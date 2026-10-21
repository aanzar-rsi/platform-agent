"""
Per-chat agent session logger.

Binds via ContextVar (like token_stream) and appends structured JSONL events
to backend/logs/{agent_id}.jsonl. All public APIs soft-fail and never raise
into the agent loop.

Writes are handed off to a single background writer thread instead of being
done synchronously on the calling thread. This matters because `log()` is
called dozens of times per agent turn (every LLM request/response, every
node/tool step) from many different chats/runs concurrently — a single
shared lock around a blocking `path.open("a")` call previously meant one
slow disk write (this workspace's OneDrive-synced filesystem can stall on
individual file opens) would serialize and stall *every other* log call in
the process, including unrelated chats. Handing the formatted line to an
in-memory queue is effectively instant, so logging can never become a
bottleneck on the hot path regardless of disk speed.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import threading
import time
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

_CLIENT_ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = _CLIENT_ROOT / "logs"
DEFAULT_MAX_FIELD_CHARS = 50_000

AGENT_LOG_ENABLED = os.environ.get("EVA_AGENT_LOG_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

_session_logger: ContextVar[Optional["SessionLogger"]] = ContextVar(
    "eva_session_logger", default=None
)

# Bounded so a runaway logging burst can't grow memory unboundedly; writes are
# dropped (with a warning, never an exception) rather than blocking the caller
# if the writer thread can't keep up.
_QUEUE_MAX_SIZE = 20_000
_log_queue: "queue.Queue[tuple[Path, str]]" = queue.Queue(maxsize=_QUEUE_MAX_SIZE)
_writer_thread: threading.Thread | None = None
_writer_thread_lock = threading.Lock()


def _writer_loop() -> None:
    while True:
        path, line = _log_queue.get()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
        except Exception:
            logger.warning("Async log write failed for %s", path, exc_info=True)
        finally:
            _log_queue.task_done()


def _ensure_writer_started() -> None:
    global _writer_thread
    if _writer_thread is not None and _writer_thread.is_alive():
        return
    with _writer_thread_lock:
        if _writer_thread is not None and _writer_thread.is_alive():
            return
        _writer_thread = threading.Thread(target=_writer_loop, name="eva-log-writer", daemon=True)
        _writer_thread.start()


def flush_pending_logs(timeout: float = 2.0) -> bool:
    """Block (up to `timeout`s) until all queued log lines have been written.

    Normal logging calls never block — this is only for tests and graceful
    shutdown paths that need the on-disk file to be up to date. Returns True
    if the queue fully drained before the timeout.
    """
    deadline = time.monotonic() + timeout
    while _log_queue.unfinished_tasks > 0:
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)
    return True


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_agent_id(agent_id: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (agent_id or "").strip())
    return cleaned or "unknown"


def truncate_value(value: Any, max_chars: int = DEFAULT_MAX_FIELD_CHARS) -> Any:
    """Recursively truncate oversized strings in payloads."""
    if isinstance(value, str):
        if len(value) <= max_chars:
            return value
        omitted = len(value) - max_chars
        return value[:max_chars] + f"…[truncated {omitted} chars]"
    if isinstance(value, dict):
        return {str(k): truncate_value(v, max_chars) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [truncate_value(v, max_chars) for v in value]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return truncate_value(str(value), max_chars)


class SessionLogger:
    """Append-only JSONL writer for one agent."""

    def __init__(
        self,
        agent_id: str,
        *,
        execution_id: str | None = None,
        owner_id: str | None = None,
        session_id: str | None = None,
        logs_dir: Path | None = None,
        max_field_chars: int = DEFAULT_MAX_FIELD_CHARS,
    ) -> None:
        self.agent_id = agent_id
        self.execution_id = execution_id or ""
        self.owner_id = owner_id or ""
        self.session_id = session_id or ""
        self.logs_dir = Path(logs_dir) if logs_dir else LOGS_DIR
        self.max_field_chars = max_field_chars
        self.path = self.logs_dir / f"{_safe_agent_id(agent_id)}.jsonl"

    def log(self, event: str, payload: dict[str, Any] | None = None) -> None:
        try:
            record = {
                "ts": _utc_now(),
                "agent_id": self.agent_id,
                "execution_id": self.execution_id,
                "owner_id": self.owner_id,
                "session_id": self.session_id,
                "event": event,
                "payload": truncate_value(payload or {}, self.max_field_chars),
            }
            line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
            _ensure_writer_started()
            try:
                _log_queue.put_nowait((self.path, line))
            except queue.Full:
                logger.warning("Log queue full (%d); dropping event=%s agent_id=%s", _QUEUE_MAX_SIZE, event, self.agent_id)
        except Exception:
            logger.warning("SessionLogger.write failed agent_id=%s", self.agent_id, exc_info=True)


def bind_session_logger(
    agent_id: str,
    *,
    execution_id: str | None = None,
    owner_id: str | None = None,
    session_id: str | None = None,
    logs_dir: Path | None = None,
) -> Any:
    """
    Bind a SessionLogger for the current context.
    Returns a reset token (or None if logging disabled / bind skipped).
    """
    if not AGENT_LOG_ENABLED or not agent_id:
        return None
    try:
        session = SessionLogger(
            agent_id,
            execution_id=execution_id,
            owner_id=owner_id,
            session_id=session_id,
            logs_dir=logs_dir,
        )
        return _session_logger.set(session)
    except Exception:
        logger.warning("bind_session_logger failed", exc_info=True)
        return None


def reset_session_logger(token) -> None:
    if token is None:
        return
    try:
        _session_logger.reset(token)
    except Exception:
        logger.warning("reset_session_logger failed", exc_info=True)


def get_session_logger() -> SessionLogger | None:
    try:
        return _session_logger.get()
    except Exception:
        return None


def log_event(event_type: str, **payload: Any) -> None:
    """Log an event to the bound session logger. No-op if unbound."""
    from src.utils.trace import EVENTS, emit, in_run

    if event_type in EVENTS and in_run():
        emit(event_type, data=payload, component="agent_logger")
    try:
        session = get_session_logger()
        if session is None:
            return
        session.log(event_type, payload)
    except Exception:
        logger.warning("log_event failed event=%s", event_type, exc_info=True)


# ── Convenience helpers ───────────────────────────────────────────────────────

def log_run_start(**payload: Any) -> None:
    log_event("run.start", **payload)


def log_run_end(**payload: Any) -> None:
    log_event("run.end", **payload)


def log_error(**payload: Any) -> None:
    log_event("run.error", **payload)


def log_llm_request(**payload: Any) -> None:
    log_event("llm.request", **payload)


def log_llm_response(**payload: Any) -> None:
    log_event("llm.response", **payload)


def log_agent_decision(**payload: Any) -> None:
    log_event("agent.decision", **payload)


def log_tool(phase: str, **payload: Any) -> None:
    """phase: start | end"""
    log_event(f"tool.{phase}", **payload)


def log_route(**payload: Any) -> None:
    log_event("route", **payload)


def log_subagent(phase: str, **payload: Any) -> None:
    log_event(f"subagent.{phase}", **payload)


def log_context_select(**payload: Any) -> None:
    log_event("context_select", **payload)
