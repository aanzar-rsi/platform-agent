"""
LangGraph checkpointer backed by Postgres (`checkpoints`/`checkpoint_blobs`/
`checkpoint_writes`, managed by `langgraph-checkpoint-postgres`).

Replaces the old sharded-JSON-file checkpointer. As a side effect of every
`put()`, also mirrors newly appended messages into the relational `messages`
table so chat history can be read with a plain indexed SQL query instead of
decoding checkpoint blobs (see db_requirement.md section 3).
"""

from __future__ import annotations

import logging
import threading
import uuid as uuidlib
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres import _internal
from langgraph.checkpoint.postgres import PostgresSaver as _PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

_ROLE_MAP = {"human": "user", "ai": "assistant", "system": "system", "tool": "tool"}


def _valid_uuid(value: str) -> bool:
    try:
        uuidlib.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def _message_role(msg: Any) -> str:
    msg_type = getattr(msg, "type", None) or "unknown"
    return _ROLE_MAP.get(msg_type, msg_type)


def _message_content(msg: Any) -> str:
    content = getattr(msg, "content", "")
    return content if isinstance(content, str) else str(content)


class PostgresSaver(_PostgresSaver):
    """PostgresSaver that also mirrors new messages into the `messages` table."""

    def __init__(self, conn) -> None:
        super().__init__(conn)
        self._sync_lock = threading.Lock()

    def put(
        self,
        config: RunnableConfig,
        checkpoint: dict[str, Any],
        metadata: dict[str, Any],
        new_versions: dict[str, Any],
    ) -> RunnableConfig:
        parent_messages: list[Any] = []
        try:
            parent = self.get_tuple(config)
            if parent:
                parent_messages = parent.checkpoint.get("channel_values", {}).get("messages") or []
        except Exception:
            logger.warning("Could not load parent checkpoint before message sync", exc_info=True)
        result = super().put(config, checkpoint, metadata, new_versions)
        thread_id = None
        try:
            thread_id = config["configurable"]["thread_id"]
            values = checkpoint.get("channel_values") or {}
            messages = values.get("messages") or []
            self._sync_messages(thread_id, messages, checkpoint.get("id"), parent_messages)
        except Exception:
            logger.exception("Failed to sync messages table for thread_id=%s", thread_id)
        return result

    def _sync_messages(
        self,
        thread_id: str,
        messages: list[Any],
        checkpoint_id: str | None,
        parent_messages: list[Any] | None = None,
    ) -> None:
        if not messages or not _valid_uuid(thread_id):
            return
        parent_messages = parent_messages or []
        start = len(parent_messages)
        if messages[:start] != parent_messages:
            start = 0
        with self._sync_lock, _internal.get_connection(self.conn) as conn:
            for position, msg in enumerate(messages[start:], start=start):
                conn.execute(
                    """
                    INSERT INTO messages (agent_id, role, content, checkpoint_id, message_position)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (agent_id, checkpoint_id, message_position)
                    WHERE checkpoint_id IS NOT NULL AND message_position IS NOT NULL
                    DO NOTHING
                    """,
                    (thread_id, _message_role(msg), _message_content(msg), checkpoint_id, position),
                )


# ── Factory + conversation helpers (swap boundary) ────────────────────────────

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()
_checkpointer: PostgresSaver | None = None
_checkpointer_lock = threading.Lock()


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                from src.config import settings

                _pool = ConnectionPool(
                    conninfo=settings.database_url,
                    min_size=1,
                    max_size=10,
                    kwargs={
                        "row_factory": dict_row,
                        "autocommit": True,
                        "options": "-c timezone=Asia/Kolkata",
                    },
                    open=True,
                )
    return _pool


def get_checkpointer() -> PostgresSaver:
    """Return the process-wide Postgres checkpointer."""
    global _checkpointer
    if _checkpointer is None:
        with _checkpointer_lock:
            if _checkpointer is None:
                saver = PostgresSaver(_get_pool())
                saver.setup()
                _ensure_message_sync_schema()
                _ensure_branch_learn_table()
                _checkpointer = saver
    return _checkpointer


def _ensure_branch_learn_table() -> None:
    """Idempotent setup for per-branch experience-learning bookkeeping — tracks
    which leaf checkpoints (branch tips) have already been learned from, so the
    idle learner can cover every fork of a thread instead of only the current
    tip (see src/subagents/learner_agent/idle_watcher.py)."""
    with _get_pool().connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS agent_branch_learn_state (
                agent_id TEXT NOT NULL,
                leaf_checkpoint_id TEXT NOT NULL,
                learned_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                status TEXT,
                PRIMARY KEY (agent_id, leaf_checkpoint_id)
            )
            """
        )


def _ensure_message_sync_schema() -> None:
    """Add the idempotency key needed by the checkpoint message mirror."""
    with _get_pool().connection() as conn:
        conn.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_position INTEGER")
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_checkpoint_position
            ON messages (agent_id, checkpoint_id, message_position)
            WHERE checkpoint_id IS NOT NULL AND message_position IS NOT NULL
            """
        )


def reconcile_thread_messages(thread_id: str) -> list[Any]:
    """Sync an agent's active transcript from its checkpoint tip."""
    saver = get_checkpointer()
    tup = saver.get_tuple(build_config(thread_id))
    if tup is None:
        return []
    messages = tup.checkpoint.get("channel_values", {}).get("messages") or []
    checkpoint_id = tup.config["configurable"].get("checkpoint_id")
    saver._sync_messages(thread_id, messages, checkpoint_id)
    return messages


def is_leaf_learned(agent_id: str, leaf_checkpoint_id: str) -> bool:
    with _get_pool().connection() as conn:
        row = conn.execute(
            """
            SELECT 1 FROM agent_branch_learn_state
            WHERE agent_id = %s AND leaf_checkpoint_id = %s
              AND status IN ('learned', 'skipped')
            """,
            (agent_id, leaf_checkpoint_id),
        ).fetchone()
        return row is not None


def mark_leaf_learned(agent_id: str, leaf_checkpoint_id: str, *, status: str = "learned") -> None:
    with _get_pool().connection() as conn:
        conn.execute(
            """
            INSERT INTO agent_branch_learn_state (agent_id, leaf_checkpoint_id, learned_at, status)
            VALUES (%s, %s, now(), %s)
            ON CONFLICT (agent_id, leaf_checkpoint_id)
            DO UPDATE SET learned_at = now(), status = EXCLUDED.status
            """,
            (agent_id, leaf_checkpoint_id, status),
        )


def build_config(
    agent_id: str,
    *,
    owner_id: str = "local-user",
    checkpoint_id: str | None = None,
    execution_id: str | None = None,
    runtime: dict[str, Any] | None = None,
) -> RunnableConfig:
    from src.config import settings

    max_loops = settings.resolve_max_loops(runtime)
    configurable: dict[str, Any] = {
        "thread_id": agent_id,
        "checkpoint_ns": "",
        "agent_id": agent_id,
        "owner_id": owner_id,
        "max_loops": max_loops,
    }
    if checkpoint_id:
        configurable["checkpoint_id"] = checkpoint_id
    configurable.update(runtime or {})
    # User preferences may alter model/UI settings, never identity or checkpoint scope.
    configurable.update({"thread_id": agent_id, "agent_id": agent_id, "owner_id": owner_id,
                         "session_id": (runtime or {}).get("session_id")})
    if execution_id:
        configurable["execution_id"] = execution_id
    from src.utils.trace import context

    current_trace = context()
    if current_trace["trace_id"]:
        configurable.update(current_trace)
    return {"configurable": configurable, "recursion_limit": max_loops}


def rewind_config(
    agent_id: str,
    checkpoint_id: str,
    *,
    owner_id: str = "local-user",
) -> RunnableConfig:
    """Config that resumes / time-travels from a specific checkpoint."""
    return build_config(agent_id, owner_id=owner_id, checkpoint_id=checkpoint_id)


def list_checkpoints(thread_id: str) -> list[dict[str, Any]]:
    """Return readable checkpoint summaries for a thread (newest first)."""
    saver = get_checkpointer()
    out: list[dict[str, Any]] = []
    for tup in saver.list({"configurable": {"thread_id": thread_id}}):
        values = tup.checkpoint.get("channel_values", {})
        messages = values.get("messages") or []
        snippet = ""
        if messages:
            last = messages[-1]
            content = getattr(last, "content", last)
            snippet = str(content)[:120]
        out.append(
            {
                "checkpoint_id": tup.config["configurable"]["checkpoint_id"],
                "timestamp": tup.checkpoint.get("ts"),
                "current_task": values.get("current_task", ""),
                "message_snippet": snippet,
                "parent_checkpoint_id": (
                    tup.parent_config["configurable"]["checkpoint_id"]
                    if tup.parent_config
                    else None
                ),
            }
        )
    return out


def active_checkpoint_path(thread_id: str) -> set[str] | None:
    """Checkpoint ids on the path from the current graph tip back to the root.

    Used to filter the flat `messages` table down to the active branch after
    forks — sibling/abandoned branch rows are excluded."""
    checkpoints = list_checkpoints(thread_id)
    if not checkpoints:
        return None

    by_id = {c["checkpoint_id"]: c for c in checkpoints}
    path: set[str] = set()
    cur: str | None = checkpoints[0]["checkpoint_id"]
    while cur:
        path.add(cur)
        entry = by_id.get(cur)
        if not entry:
            break
        cur = entry.get("parent_checkpoint_id")
    return path


def _infer_node(values: dict[str, Any], parent_values: dict[str, Any] | None) -> str:
    """Best-effort label for "which node just wrote this checkpoint" — there is
    no direct node name on a checkpoint, so this compares channel shapes
    against the parent checkpoint. Good enough for UI display, not authoritative."""
    parent_values = parent_values or {}
    messages = values.get("messages") or []
    parent_messages = parent_values.get("messages") or []
    history = values.get("execution_history") or []
    parent_history = parent_values.get("execution_history") or []

    if len(messages) > len(parent_messages) and messages:
        last_type = getattr(messages[-1], "type", None)
        if last_type == "human":
            return "start"

    if len(history) > len(parent_history) and history:
        last = history[-1] or {}
        if last.get("type") == "tool":
            return "armory_node"
        if last.get("type") == "subagent":
            if "human_rounds" in last or "awaiting_persist_confirmation" in (last.get("structured") or {}):
                return "output_security_gate"
            return "armory_node"

    if values.get("context_memory") != parent_values.get("context_memory"):
        if len(history) == len(parent_history):
            return "context_selector"

    if len(messages) > len(parent_messages) and messages:
        last_type = getattr(messages[-1], "type", None)
        if last_type == "ai":
            return "agent_node"

    return "unknown"


def _node_from_metadata(
    metadata: dict[str, Any] | None,
    values: dict[str, Any],
    parent_values: dict[str, Any] | None,
) -> str:
    """Prefer LangGraph checkpoint metadata (authoritative node writes)."""
    writes = (metadata or {}).get("writes") or {}
    if isinstance(writes, dict) and writes:
        for key in writes:
            if key not in ("__start__", "__end__"):
                return key
        return next(iter(writes.keys()))
    return _infer_node(values, parent_values)


def _is_redundant_checkpoint(
    values: dict[str, Any],
    parent_values: dict[str, Any] | None,
    node: str,
) -> bool:
    """Drop no-op rows LangGraph adds when interrupt() fires without changing
    messages or execution_history (shows up as a blank duplicate in the tree)."""
    parent_values = parent_values or {}
    if node != "unknown":
        return False
    if values.get("current_task"):
        return False
    msgs = values.get("messages") or []
    parent_msgs = parent_values.get("messages") or []
    if len(msgs) != len(parent_msgs):
        return False
    hist = values.get("execution_history") or []
    parent_hist = parent_values.get("execution_history") or []
    if len(hist) != len(parent_hist):
        return False
    return True


def _filter_checkpoint_tree(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not raw:
        return raw

    by_id = {row["checkpoint_id"]: row for row in raw}
    skip: set[str] = set()
    for row in raw:
        parent_values = None
        parent_id = row.get("parent_checkpoint_id")
        if parent_id and parent_id in by_id:
            parent_values = by_id[parent_id].get("_values")
        if _is_redundant_checkpoint(row.get("_values") or {}, parent_values, row.get("node") or "unknown"):
            skip.add(row["checkpoint_id"])

    def resolve_parent(parent_id: str | None) -> str | None:
        seen: set[str] = set()
        while parent_id and parent_id in skip and parent_id not in seen:
            seen.add(parent_id)
            parent_id = by_id.get(parent_id, {}).get("parent_checkpoint_id")
        return parent_id

    kept: list[dict[str, Any]] = []
    for row in raw:
        if row["checkpoint_id"] in skip:
            continue
        entry = {k: v for k, v in row.items() if not k.startswith("_")}
        entry["parent_checkpoint_id"] = resolve_parent(row.get("parent_checkpoint_id"))
        kept.append(entry)

    child_parents = {row["parent_checkpoint_id"] for row in kept if row.get("parent_checkpoint_id")}
    for row in kept:
        row["is_leaf"] = row["checkpoint_id"] not in child_parents

    for row in raw:
        if row["checkpoint_id"] in skip and row.get("has_pending_interrupt"):
            parent_id = resolve_parent(row.get("parent_checkpoint_id"))
            if parent_id:
                for kept_row in kept:
                    if kept_row["checkpoint_id"] == parent_id:
                        kept_row["has_pending_interrupt"] = True
                        break

    for row in raw:
        if row["checkpoint_id"] in skip and row.get("is_active_tip"):
            parent_id = resolve_parent(row.get("parent_checkpoint_id"))
            if parent_id:
                for kept_row in kept:
                    if kept_row["checkpoint_id"] == parent_id:
                        kept_row["is_active_tip"] = True
                        break

    return kept


def list_checkpoint_tree(thread_id: str) -> list[dict[str, Any]]:
    """Like `list_checkpoints`, plus `node`, `is_leaf`, and whether the tip
    checkpoint has a pending interrupt — powers the frontend branch tree."""
    saver = get_checkpointer()
    tuples = list(saver.list({"configurable": {"thread_id": thread_id}}))

    by_id: dict[str, Any] = {}
    for tup in tuples:
        cp_id = tup.config["configurable"]["checkpoint_id"]
        by_id[cp_id] = tup

    tip_id = tuples[0].config["configurable"]["checkpoint_id"] if tuples else None
    interrupt_tip = has_pending_interrupt(thread_id) if tip_id else None

    raw: list[dict[str, Any]] = []
    for tup in tuples:
        cp_id = tup.config["configurable"]["checkpoint_id"]
        values = tup.checkpoint.get("channel_values", {})
        parent_id = (
            tup.parent_config["configurable"]["checkpoint_id"] if tup.parent_config else None
        )
        parent_tup = by_id.get(parent_id) if parent_id else None
        parent_values = parent_tup.checkpoint.get("channel_values", {}) if parent_tup else None

        messages = values.get("messages") or []
        snippet = ""
        if messages:
            last = messages[-1]
            content = getattr(last, "content", last)
            snippet = str(content)[:160]

        node = _node_from_metadata(getattr(tup, "metadata", None), values, parent_values)

        raw.append(
            {
                "checkpoint_id": cp_id,
                "timestamp": tup.checkpoint.get("ts"),
                "current_task": values.get("current_task", ""),
                "message_snippet": snippet,
                "parent_checkpoint_id": parent_id,
                "node": node,
                "is_leaf": False,
                "is_active_tip": cp_id == tip_id,
                "has_pending_interrupt": bool(cp_id == tip_id and interrupt_tip is not None),
                "_values": values,
            }
        )

    return _filter_checkpoint_tree(raw)


def list_leaf_checkpoints(thread_id: str) -> list[str]:
    """checkpoint_ids that are branch tips (no other checkpoint has them as a
    parent) — used to make experience learning cover every forked branch,
    not just the current head."""
    saver = get_checkpointer()
    tuples = list(saver.list({"configurable": {"thread_id": thread_id}}))
    if not tuples:
        return []
    parent_ids = {
        tup.parent_config["configurable"]["checkpoint_id"]
        for tup in tuples
        if tup.parent_config
    }
    return [
        tup.config["configurable"]["checkpoint_id"]
        for tup in tuples
        if tup.config["configurable"]["checkpoint_id"] not in parent_ids
    ]


def has_pending_interrupt(thread_id: str):
    """Return the pending `Interrupt` for this thread's current tip, or None."""
    try:
        from src.agent.graph import agent_app
    except Exception:
        return None
    snap = agent_app.get_state(build_config(thread_id))
    for task in getattr(snap, "tasks", None) or ():
        interrupts = getattr(task, "interrupts", None)
        if interrupts:
            return interrupts[0]
    return None


def thread_has_state(thread_id: str) -> bool:
    saver = get_checkpointer()
    return saver.get_tuple(build_config(thread_id)) is not None


def get_thread_state(thread_id: str) -> dict[str, Any] | None:
    """Return channel_values for the tip checkpoint, or None."""
    saver = get_checkpointer()
    tup = saver.get_tuple(build_config(thread_id))
    if tup is None:
        return None
    return tup.checkpoint.get("channel_values", {})


def initial_state_for_thread(
    thread_id: str,
    query: str,
    *,
    preloaded_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full state for a brand-new thread; message-only delta for existing ones."""
    from langchain_core.messages import HumanMessage

    human = HumanMessage(content=query)
    if thread_has_state(thread_id):
        return {"messages": [human], "planned_phases": [], "planned_phase_index": 0,
                "plan_created": {}, "plan_event": {}, "step_events": [], "step_results": [],
                "executor_output": {}, "output_events": [], "dispatch_target": ""}
    return {
        "messages": [human],
        "execution_history": [],
        "execution_memory": {},
        "context_memory": {
            "budget_tokens": 5000,
            "used_tokens": 0,
            "truncated": False,
            "entries": [],
        },
        "context_selection_history": [],
        "context_selection_summary": {},
        "current_task": "",
        "next_step": {},
        "preloaded_context": preloaded_context or {},
        "agent_id": thread_id,
        "planned_phases": [],
        "planned_phase_index": 0,
        "plan_created": {},
        "plan_event": {},
        "step_events": [],
        "step_results": [],
        "action_sequence": 0,
        "executor_output": {},
        "output_events": [],
        "dispatch_target": "",
        "dispatch_step": {},
        "pending_context_selection": {},
        "human_request_kind": "",
    }


def run_turn(
    graph,
    agent_id: str,
    query: str | None,
    *,
    owner_id: str = "local-user",
    checkpoint_id: str | None = None,
    execution_id: str | None = None,
    preloaded_context: dict[str, Any] | None = None,
    stream_mode: str | list[str] = "updates",
    bind_logger: bool = True,
    resume_value: Any = None,
    is_resume: bool = False,
    runtime: dict[str, Any] | None = None,
):
    """
    Run one user turn against the compiled graph.
    Yields the same step dicts as `graph.stream(...)`.

    When bind_logger=True (default), binds a per-chat session logger for the
    duration of the stream iteration and emits run.start / run.end.

    When `is_resume=True`, this continues a run that's paused on a pending
    `interrupt()` for `thread_id` instead of starting a fresh turn: no new
    message is added and `query` is ignored — `resume_value` is delivered to
    the waiting `interrupt()` call via `Command(resume=...)`.
    """
    import uuid

    from langgraph.types import Command
    from src.utils.trace import current_ids, emit as trace_emit

    from src.utils.agent_logger import (
        bind_session_logger,
        log_error,
        log_run_end,
        log_run_start,
        reset_session_logger,
    )

    resolved_execution_id = execution_id or str(uuid.uuid4())
    config = build_config(
        agent_id,
        owner_id=owner_id,
        checkpoint_id=None if is_resume else checkpoint_id,
        execution_id=resolved_execution_id,
        runtime=runtime,
    )
    if is_resume:
        stream_input: Any = Command(resume=resume_value)
    else:
        stream_input = initial_state_for_thread(
            agent_id,
            query or "",
            preloaded_context=preloaded_context,
        )

    def _stream():
        from src.utils.trace import bind_from_config, reset as reset_trace

        trace_token = bind_from_config(config) if not current_ids().get("execution_id") else None
        from src.utils.trace import in_run

        traced = in_run()
        if traced:
            trace_emit("checkpoint.resume" if is_resume else "checkpoint.list", component="checkpointer",
                       data={"checkpoint_id": checkpoint_id} if checkpoint_id else {})
        token = None
        if bind_logger:
            token = bind_session_logger(
                agent_id,
                execution_id=resolved_execution_id,
                owner_id=owner_id,
                session_id=(runtime or {}).get("session_id"),
            )
            log_run_start(
                query=query or "(resume)",
                checkpoint_id=checkpoint_id,
                stream_mode=stream_mode
                if isinstance(stream_mode, str)
                else list(stream_mode),
            )
        try:
            try:
                for item in graph.stream(stream_input, config=config, stream_mode=stream_mode):
                    yield item
                if traced:
                    trace_emit("checkpoint.create", component="checkpointer")
                if bind_logger:
                    log_run_end(stopped=False)
            except Exception as exc:
                if traced:
                    trace_emit("checkpoint.error", status="error", error=exc, component="checkpointer")
                if bind_logger:
                    log_error(message=str(exc))
                    log_run_end(stopped=True, error=str(exc))
                raise
        finally:
            if bind_logger:
                reset_session_logger(token)
            if trace_token is not None:
                reset_trace(trace_token)

    return _stream()
