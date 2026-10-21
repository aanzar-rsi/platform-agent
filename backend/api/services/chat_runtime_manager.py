from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from api.core.deps import get_repos
from api.core.security import utc_now_iso
from api.services.agent_runtime import AgentRuntime

logger = logging.getLogger(__name__)


class ExecutionEventWriter:
    """Execution-bound event writer persisted in PostgreSQL."""

    def __init__(self, *, agent_id: str, execution_id: str, event_repo) -> None:
        self.agent_id = agent_id
        self.execution_id = execution_id
        self._events = event_repo

    def enqueue(self, type_: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._events.append(
            agent_id=self.agent_id,
            execution_id=self.execution_id,
            event_type=type_,
            payload=payload or {},
        )


@dataclass
class ChatRuntime:
    agent_id: str
    owner_id: str
    run_active: bool = False
    run_thread: threading.Thread | None = None
    execution_id: str | None = None
    sockets: dict[int, WebSocket] = field(default_factory=dict)
    flusher_tasks: dict[int, asyncio.Task] = field(default_factory=dict)
    flush_cursors: dict[int, int] = field(default_factory=dict)
    flush_execution_ids: dict[int, str | None] = field(default_factory=dict)


class ChatRuntimeManager:
    """Process-local orchestrator for runs + DB-backed websocket replay/live delivery."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runtimes: dict[str, ChatRuntime] = {}
        self._agent = AgentRuntime()

    def get_or_create(self, agent_id: str, owner_id: str) -> ChatRuntime:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if rt is None:
                rt = ChatRuntime(agent_id=agent_id, owner_id=owner_id)
                self._runtimes[agent_id] = rt
            elif rt.owner_id != owner_id:
                raise PermissionError("Agent belongs to another owner")
            return rt

    def _socket_key(self, websocket: WebSocket) -> int:
        return id(websocket)

    def active_ws_count(self) -> int:
        with self._lock:
            return sum(len(r.sockets) for r in self._runtimes.values())

    def active_run_count(self) -> int:
        with self._lock:
            return sum(1 for r in self._runtimes.values() if r.run_active)

    def _follow_execution(self, rt: ChatRuntime, execution_id: str) -> None:
        with self._lock:
            rt.execution_id = execution_id
            for key in rt.sockets:
                if rt.flush_execution_ids.get(key) != execution_id:
                    rt.flush_execution_ids[key] = execution_id
                    rt.flush_cursors[key] = 0

    async def attach(
        self,
        agent_id: str,
        owner_id: str,
        websocket: WebSocket,
        *,
        execution_id: str | None = None,
        after_seq: int = 0,
    ) -> ChatRuntime:
        rt = self.get_or_create(agent_id, owner_id)
        repos = get_repos()
        active = repos.agents.active_execution(agent_id)
        latest = repos.agents.latest_execution(agent_id)
        chosen = execution_id or str((active or latest or {}).get("execution_id") or "") or None
        selected = None
        if chosen:
            selected = repos.agents.execution(chosen)
            if not selected or str(selected.get("agent_id")) != str(agent_id):
                raise PermissionError("execution_not_found")
        else:
            selected = active or latest

        latest_seq = repos.execution_events.latest_sequence(chosen) if chosen else 0
        status = str((selected or {}).get("state") or "idle")
        current_state = (selected or {}).get("current_state") or {}
        ready = {
            "execution_id": chosen,
            "status": status,
            "run_active": status in {"running", "interrupted"},
            "latest_sequence": latest_seq,
            "last_seq": latest_seq,
            "backlog_count": max(latest_seq - max(after_seq, 0), 0),
            "current_state": current_state,
            "epoch": 0,
        }
        await websocket.send_json(
            {
                "v": 1,
                "type": "session.ready",
                "id": "session-ready",
                "agent_id": agent_id,
                "seq": None,
                "execution_id": chosen,
                "ts": utc_now_iso(),
                "payload": ready,
            }
        )

        key = self._socket_key(websocket)
        with self._lock:
            rt.sockets[key] = websocket
            rt.flush_cursors[key] = max(after_seq, 0)
            rt.flush_execution_ids[key] = chosen
            old = rt.flusher_tasks.get(key)
            if old and not old.done():
                old.cancel()
            rt.flusher_tasks[key] = asyncio.create_task(self._flush_loop(agent_id, key))
        return rt

    async def detach(self, agent_id: str, websocket: WebSocket | None = None) -> None:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if not rt:
                return
            keys = [self._socket_key(websocket)] if websocket is not None else list(rt.sockets.keys())
            tasks = []
            for key in keys:
                task = rt.flusher_tasks.pop(key, None)
                rt.sockets.pop(key, None)
                rt.flush_cursors.pop(key, None)
                rt.flush_execution_ids.pop(key, None)
                if task is not None:
                    tasks.append(task)
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def _flush_loop(self, agent_id: str, socket_key: int) -> None:
        try:
            while True:
                with self._lock:
                    rt = self._runtimes.get(agent_id)
                    if not rt:
                        return
                    ws = rt.sockets.get(socket_key)
                    if ws is None:
                        return
                    cursor = int(rt.flush_cursors.get(socket_key, 0))
                    execution_id = rt.flush_execution_ids.get(socket_key)
                if not execution_id:
                    await asyncio.sleep(0.5)
                    continue
                events = await asyncio.to_thread(
                    get_repos().execution_events.events_after,
                    execution_id,
                    cursor,
                    limit=200,
                )
                if not events:
                    await asyncio.sleep(0.5)
                    continue
                for envelope in events:
                    with self._lock:
                        rt2 = self._runtimes.get(agent_id)
                        if not rt2 or rt2.sockets.get(socket_key) is not ws:
                            return
                    try:
                        await ws.send_json(envelope)
                    except Exception:
                        logger.info("WS send failed; detaching agent_id=%s", agent_id)
                        await self.detach(agent_id, ws)
                        return
                    with self._lock:
                        if rt2:
                            rt2.flush_cursors[socket_key] = max(
                                int(rt2.flush_cursors.get(socket_key, 0)),
                                int(envelope.get("seq") or 0),
                            )
        except asyncio.CancelledError:
            return

    def start_run(
        self,
        *,
        agent_id: str,
        owner_id: str,
        query: str,
        checkpoint_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        doc = get_repos().sessions.get(agent_id)
        if not doc or doc["deleted"] or doc["owner_id"] != owner_id:
            return {"ok": False, "error": "Agent not found or not owned"}
        rt = self.get_or_create(agent_id, owner_id)
        with self._lock:
            already_running = rt.run_active
            prev_thread = rt.run_thread if already_running else None
            if already_running:
                if checkpoint_id is None:
                    return {"ok": False, "error": "Run already active for this chat"}
                rt.run_active = True
            else:
                rt.run_active = True

        if not already_running:
            return self._begin_run(
                agent_id=agent_id,
                owner_id=owner_id,
                query=query,
                checkpoint_id=checkpoint_id,
                session_id=session_id,
            )

        self._agent.request_stop(agent_id, superseded=True)

        def _deferred_fork() -> None:
            if prev_thread is not None:
                prev_thread.join(timeout=120)
                if prev_thread.is_alive():
                    logger.warning("Fork wait timed out; previous execution still active agent_id=%s", agent_id)
                    self.enqueue_control(
                        agent_id,
                        "error",
                        {"message": "Couldn't switch branches — the previous run is still active. Try again in a moment."},
                    )
                    with self._lock:
                        rt.run_active = False
                    return
            try:
                result = self._begin_run(
                    agent_id=agent_id,
                    owner_id=owner_id,
                    query=query,
                    checkpoint_id=checkpoint_id,
                    session_id=session_id,
                )
                if not result.get("ok"):
                    self.enqueue_control(agent_id, "error", {"message": result["error"]})
            except Exception:
                logger.exception("Fork start failed agent_id=%s", agent_id)
                self.enqueue_control(agent_id, "error", {"message": "Couldn't start fork"})

        threading.Thread(target=_deferred_fork, name=f"fork-wait-{agent_id}", daemon=True).start()
        return {"ok": True, "forking": True}

    def _begin_run(
        self,
        *,
        agent_id: str,
        owner_id: str,
        query: str,
        checkpoint_id: str | None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        rt = self.get_or_create(agent_id, owner_id)
        try:
            doc = get_repos().sessions.get(agent_id)
            if not doc or doc["deleted"] or doc["owner_id"] != owner_id:
                with self._lock:
                    rt.run_active = False
                return {"ok": False, "error": "Agent not found or not owned"}
            return self._begin_reserved_run(
                rt,
                agent_id=agent_id,
                owner_id=owner_id,
                query=query,
                checkpoint_id=checkpoint_id,
                session_id=session_id,
            )
        except Exception:
            with self._lock:
                rt.run_active = False
                rt.run_thread = None
            raise

    def _begin_reserved_run(
        self,
        rt: ChatRuntime,
        *,
        agent_id: str,
        owner_id: str,
        query: str,
        checkpoint_id: str | None,
        session_id: str | None,
    ) -> dict[str, Any]:
        repos = get_repos()
        session = repos.sessions.get(agent_id)
        preloaded = (session or {}).get("preloaded_context") or {}
        runtime = dict(repos.preferences.get(owner_id).get("agent") or {})
        from src.agent.agent_core import AgentCore
        from src.utils.trace import bind, context, reset

        agent_record = repos.agents.for_agent(agent_id, owner_id, session_id)
        agent = AgentCore(agent_record, repos.agents)
        existing = repos.agents.active_execution(agent.id.agent_id)
        if existing and existing["state"] == "interrupted":
            with self._lock:
                rt.run_active = False
            return {"ok": False, "error": "already_running"}
        try:
            execution_id = agent.run()
        except ValueError as exc:
            with self._lock:
                rt.run_active = False
            return {"ok": False, "error": str(exc)}
        self._follow_execution(rt, execution_id)

        runtime = {
            **runtime,
            "agent_id": agent.id.agent_id,
            "owner_id": owner_id,
            "policy": agent.policy.as_dict(),
            "policy_version": agent.policy.version,
            "session_id": agent.id.latest_session_id,
        }
        runtime.update({key: value for key, value in context().items() if value})
        if checkpoint_id is None and session:
            checkpoint_id = session.get("rollback_checkpoint_id")

        update_fields: dict[str, Any] = {"last_activity_at": utc_now_iso()}
        if session and session.get("last_activity_at") is None:
            from api.domain.chat_title import title_from_first_message

            update_fields["title"] = title_from_first_message(query)
        repos.sessions.update(agent_id, **update_fields)

        writer = ExecutionEventWriter(
            agent_id=agent_id,
            execution_id=execution_id,
            event_repo=repos.execution_events,
        )

        def _done(outcome: str = "completed", result: str | None = None, error: str | None = None) -> None:
            try:
                agent.finish(outcome, result=result, error=error)
            finally:
                with self._lock:
                    rt.run_active = False
                    rt.run_thread = None
                    rt.execution_id = None
            if session and session.get("rollback_checkpoint_id"):
                repos.sessions.set_rollback(agent_id, None)
            repos.sessions.update(agent_id, last_activity_at=utc_now_iso())
            repos.analytics.append("run_complete", uid=owner_id, payload={"agent_id": agent_id})

        def _target() -> None:
            trace_token = bind(agent_id=agent_id, execution_id=execution_id, owner_id=owner_id, session_id=session_id)
            from src.utils.trace import set_trace_parent

            parent_token = set_trace_parent(runtime.get("trace_id"), runtime.get("span_id"))
            try:
                self._agent.run_turn(
                    agent_id=agent_id,
                    owner_id=owner_id,
                    query=query,
                    event_writer=writer,
                    checkpoint_id=checkpoint_id,
                    preloaded_context=preloaded,
                    runtime=runtime,
                    on_complete=_done,
                    execution_id=execution_id,
                )
            except Exception as exc:
                logger.exception("Execution worker failed before completion agent_id=%s", agent_id)
                if rt.execution_id == execution_id:
                    _done("failed", error=type(exc).__name__)
            finally:
                if parent_token is not None:
                    reset(parent_token)
                reset(trace_token)

        repos.analytics.append("run_start", uid=owner_id, payload={"agent_id": agent_id})
        thread = threading.Thread(target=_target, name=f"run-{agent_id}", daemon=True)
        with self._lock:
            rt.run_thread = thread
        thread.start()
        return {"ok": True}

    def stop_run(self, agent_id: str) -> dict[str, Any]:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if not rt or not rt.run_active:
                return {"ok": False, "error": "No active run"}
        self._agent.request_stop(agent_id)
        return {"ok": True, "message": "Stop requested (cooperative)"}

    def pause_run(self, agent_id: str) -> dict[str, Any]:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if not rt or not rt.run_active:
                return {"ok": False, "error": "No active run"}
        self._agent.request_pause(agent_id)
        return {"ok": True, "message": "Pause requested (cooperative)"}

    def resume_run(
        self,
        *,
        agent_id: str,
        owner_id: str,
        resume_value: Any = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        doc = get_repos().sessions.get(agent_id)
        if not doc or doc["deleted"] or doc["owner_id"] != owner_id:
            return {"ok": False, "error": "Agent not found or not owned"}
        rt = self.get_or_create(agent_id, owner_id)
        with self._lock:
            prev_thread = rt.run_thread if rt.run_active else None

        if prev_thread is not None:
            prev_thread.join(timeout=120)
            with self._lock:
                if rt.run_thread is prev_thread and prev_thread.is_alive():
                    return {"ok": False, "error": "Run still winding down — try again in a moment"}

        with self._lock:
            if rt.run_active:
                return {"ok": False, "error": "Run already active for this chat"}
            rt.run_active = True

        repos = get_repos()
        runtime = dict(repos.preferences.get(owner_id).get("agent") or {})
        from src.agent.agent_core import AgentCore
        from src.utils.trace import bind, context, reset
        from src.agent.control import clear_pause
        from src.utils.postgres_checkpointer import has_pending_interrupt

        agent_record = repos.agents.for_agent(agent_id, owner_id, session_id)
        agent = AgentCore(agent_record, repos.agents)

        if not has_pending_interrupt(agent_id):
            with self._lock:
                rt.run_active = False
            return {"ok": False, "error": "no_interrupted_run"}
        interrupted = repos.agents.active_execution(agent.id.agent_id)
        if interrupted and interrupted["state"] != "interrupted":
            with self._lock:
                rt.run_active = False
            return {"ok": False, "error": "already_running"}
        if interrupted and interrupted["state"] == "interrupted":
            execution_id = str(interrupted["execution_id"])
            repos.agents.finish_execution(execution_id, "running")
            agent.active_execution_id = execution_id
        else:
            try:
                execution_id = agent.run()
            except ValueError as exc:
                with self._lock:
                    rt.run_active = False
                return {"ok": False, "error": str(exc)}
        clear_pause(agent_id)
        self._follow_execution(rt, execution_id)

        runtime = {
            **runtime,
            "agent_id": agent.id.agent_id,
            "owner_id": owner_id,
            "policy": agent.policy.as_dict(),
            "policy_version": agent.policy.version,
            "session_id": agent.id.latest_session_id,
        }
        runtime.update({key: value for key, value in context().items() if value})

        writer = ExecutionEventWriter(
            agent_id=agent_id,
            execution_id=execution_id,
            event_repo=repos.execution_events,
        )

        def _done(outcome: str = "completed", result: str | None = None, error: str | None = None) -> None:
            try:
                agent.finish(outcome, result=result, error=error)
            finally:
                with self._lock:
                    rt.run_active = False
                    rt.run_thread = None
                    rt.execution_id = None
            repos.sessions.update(agent_id, last_activity_at=utc_now_iso())
            repos.analytics.append("run_complete", uid=owner_id, payload={"agent_id": agent_id})

        def _target() -> None:
            trace_token = bind(agent_id=agent_id, execution_id=execution_id, owner_id=owner_id, session_id=session_id)
            from src.utils.trace import set_trace_parent

            parent_token = set_trace_parent(runtime.get("trace_id"), runtime.get("span_id"))
            try:
                self._agent.run_turn(
                    agent_id=agent_id,
                    owner_id=owner_id,
                    event_writer=writer,
                    on_complete=_done,
                    resume_value=resume_value,
                    is_resume=True,
                    runtime=runtime,
                    execution_id=execution_id,
                )
            except Exception as exc:
                logger.exception("Resume worker failed before completion agent_id=%s", agent_id)
                if rt.execution_id == execution_id:
                    _done("failed", error=type(exc).__name__)
            finally:
                if parent_token is not None:
                    reset(parent_token)
                reset(trace_token)

        repos.analytics.append("run_resume", uid=owner_id, payload={"agent_id": agent_id})
        thread = threading.Thread(target=_target, name=f"resume-{agent_id}", daemon=True)
        with self._lock:
            rt.run_thread = thread
        thread.start()
        return {"ok": True}

    def enqueue_control(self, agent_id: str, type_: str, payload: dict[str, Any] | None = None) -> None:
        repos = get_repos()
        execution = repos.agents.active_execution(agent_id) or repos.agents.latest_execution(agent_id)
        if not execution:
            return
        try:
            repos.execution_events.append(
                agent_id=agent_id,
                execution_id=str(execution["execution_id"]),
                event_type=type_,
                payload=payload or {},
            )
        except Exception:
            logger.exception("enqueue_control failed agent_id=%s type=%s", agent_id, type_)


_manager: ChatRuntimeManager | None = None


def get_runtime_manager() -> ChatRuntimeManager:
    global _manager
    if _manager is None:
        _manager = ChatRuntimeManager()
    return _manager
