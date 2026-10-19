from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket

from api.core.config import get_settings
from api.core.deps import get_repos
from api.core.security import utc_now_iso
from api.domain.chat_title import title_from_first_message
from api.services.agent_runtime import AgentRuntime
from api.services.packet_queue import ChatPacketQueue

logger = logging.getLogger(__name__)


@dataclass
class ChatRuntime:
    agent_id: str
    owner_id: str
    queue: ChatPacketQueue
    run_active: bool = False
    run_thread: threading.Thread | None = None
    execution_id: str | None = None
    websocket: WebSocket | None = None
    flusher_task: asyncio.Task | None = None
    flush_cursor: int = 0


class ChatRuntimeManager:
    """Process-local orchestrator: queues, attach/detach, parallel runs."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._runtimes: dict[str, ChatRuntime] = {}
        self._agent = AgentRuntime()

    def get_or_create(self, agent_id: str, owner_id: str) -> ChatRuntime:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if rt is None:
                rt = ChatRuntime(
                    agent_id=agent_id,
                    owner_id=owner_id,
                    queue=ChatPacketQueue(agent_id),
                )
                self._runtimes[agent_id] = rt
            elif rt.owner_id != owner_id:
                raise PermissionError("Agent belongs to another owner")
            return rt

    def fence_queue(self, agent_id: str) -> None:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if rt:
                rt.queue.fence()
                rt.flush_cursor = 0

    def active_ws_count(self) -> int:
        with self._lock:
            return sum(1 for r in self._runtimes.values() if r.websocket is not None)

    def active_run_count(self) -> int:
        with self._lock:
            return sum(1 for r in self._runtimes.values() if r.run_active)

    async def attach(self, agent_id: str, owner_id: str, websocket: WebSocket, after_seq: int = 0) -> ChatRuntime:
        rt = self.get_or_create(agent_id, owner_id)
        # Detach previous socket if any
        if rt.websocket is not None and rt.websocket is not websocket:
            await self._detach_socket(rt)
        rt.websocket = websocket
        stats = rt.queue.stats()
        ready = {
            "last_seq": stats["last_seq"],
            "run_active": rt.run_active,
            "backlog_count": stats["backlog_count"],
            "epoch": stats["epoch"],
        }
        # Direct send for session.ready (control), then catch-up from queue
        await websocket.send_json(
            {
                "v": 1,
                "type": "session.ready",
                "id": "session-ready",
                "agent_id": agent_id,
                "seq": None,
                "ts": utc_now_iso(),
                "payload": ready,
            }
        )
        backlog = rt.queue.snapshot_undelivered(after_seq)
        for envelope in backlog:
            await websocket.send_json(envelope)
            rt.flush_cursor = max(rt.flush_cursor, envelope.get("seq") or 0)
        if rt.flusher_task is None or rt.flusher_task.done():
            rt.flusher_task = asyncio.create_task(self._flush_loop(agent_id))
        return rt

    async def detach(self, agent_id: str, websocket: WebSocket | None = None) -> None:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if not rt:
                return
            if websocket is not None and rt.websocket is not websocket:
                return
        await self._detach_socket(rt)

    async def _detach_socket(self, rt: ChatRuntime) -> None:
        task = rt.flusher_task
        rt.websocket = None
        rt.flusher_task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    async def _flush_loop(self, agent_id: str) -> None:
        try:
            while True:
                with self._lock:
                    rt = self._runtimes.get(agent_id)
                    if not rt or rt.websocket is None:
                        return
                    ws = rt.websocket
                    cursor = rt.flush_cursor
                packets = await asyncio.to_thread(rt.queue.wait_new, cursor, 0.5)
                if not packets:
                    continue
                for envelope in packets:
                    with self._lock:
                        if rt.websocket is not ws:
                            return
                    try:
                        await ws.send_json(envelope)
                        with self._lock:
                            rt.flush_cursor = max(rt.flush_cursor, envelope.get("seq") or 0)
                    except Exception:
                        logger.info("WS send failed; detaching agent_id=%s", agent_id)
                        await self.detach(agent_id, ws)
                        return
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
        """Start a new turn. If a `checkpoint_id` is given (a fork) while a
        run is already active for this chat, the in-flight run is preempted:
        it's asked to stop cooperatively (which only takes effect *between*
        node/tool executions, so any tool call currently running is allowed
        to finish first), and the fork starts the instant it fully stops."""
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
                # Keep the chat marked busy through the stop→fork handoff so no
                # third concurrent run can sneak in while we wait.
                rt.run_active = True
            else:
                # Reserve the slot before releasing the lock; starting the thread
                # below must not admit a competing run.
                rt.run_active = True

        if not already_running:
            return self._begin_run(agent_id=agent_id, owner_id=owner_id, query=query, checkpoint_id=checkpoint_id, session_id=session_id)

        self._agent.request_stop(agent_id, superseded=True)

        def _deferred_fork() -> None:
            if prev_thread is not None:
                prev_thread.join(timeout=120)
                if prev_thread.is_alive():
                    logger.warning(
                        "Fork wait timed out; previous execution still active agent_id=%s", agent_id
                    )
                    self.enqueue_control(
                        agent_id,
                        "error",
                        {"message": "Couldn't switch branches — the previous run is still active. Try again in a moment."},
                    )
                    with self._lock:
                        rt.run_active = False
                    return
            try:
                result = self._begin_run(agent_id=agent_id, owner_id=owner_id, query=query,
                                         checkpoint_id=checkpoint_id, session_id=session_id)
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
            return self._begin_reserved_run(rt, agent_id=agent_id, owner_id=owner_id, query=query,
                                            checkpoint_id=checkpoint_id, session_id=session_id)
        except Exception:
            with self._lock:
                rt.run_active = False
                rt.run_thread = None
            raise

    def _begin_reserved_run(self, rt: ChatRuntime, *, agent_id: str, owner_id: str, query: str,
                             checkpoint_id: str | None, session_id: str | None) -> dict[str, Any]:
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
        with self._lock:
            rt.execution_id = execution_id
        runtime = {**runtime, "agent_id": agent.id.agent_id, "owner_id": owner_id,
                   "policy": agent.policy.as_dict(), "policy_version": agent.policy.version,
                   "session_id": agent.id.latest_session_id}
        runtime.update({key: value for key, value in context().items() if value})
        runtime["enabled_tools"] = agent.policy.armory["tools"]
        runtime["enabled_subagents"] = agent.policy.armory["subagents"]
        if checkpoint_id is None and session:
            checkpoint_id = session.get("rollback_checkpoint_id")

        # First activity on a chat → default title from the first human message.
        update_fields: dict[str, Any] = {"last_activity_at": utc_now_iso()}
        if session and session.get("last_activity_at") is None:
            update_fields["title"] = title_from_first_message(query)
        repos.sessions.update(agent_id, **update_fields)

        def _done(outcome: str = "completed", result: str | None = None, error: str | None = None) -> None:
            try:
                agent.finish(outcome, result=result, error=error)
            finally:
                with self._lock:
                    rt.run_active = False
                    rt.run_thread = None
                    rt.execution_id = None
            # clear one-shot rollback tip after a turn
            if session and session.get("rollback_checkpoint_id"):
                repos.sessions.set_rollback(agent_id, None)
            repos.sessions.update(agent_id, last_activity_at=utc_now_iso())
            repos.analytics.append(
                "run_complete",
                uid=owner_id,
                payload={"agent_id": agent_id},
            )

        def _target() -> None:
            trace_token = bind(agent_id=agent_id, execution_id=execution_id,
                               owner_id=owner_id, session_id=session_id)
            from src.utils.trace import set_trace_parent

            parent_token = set_trace_parent(runtime.get("trace_id"), runtime.get("span_id"))
            try:
                self._agent.run_turn(
                    agent_id=agent_id, owner_id=owner_id, query=query, queue=rt.queue,
                    checkpoint_id=checkpoint_id, preloaded_context=preloaded,
                    runtime=runtime, on_complete=_done, execution_id=execution_id,
                )
            except Exception as exc:
                logger.exception("Execution worker failed before completion agent_id=%s", agent_id)
                if rt.execution_id == execution_id:
                    _done("failed", error=type(exc).__name__)
            finally:
                if parent_token is not None:
                    reset(parent_token)
                reset(trace_token)

        repos.analytics.append(
            "run_start",
            uid=owner_id,
            payload={"agent_id": agent_id},
        )
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

    def resume_run(self, *, agent_id: str, owner_id: str, resume_value: Any = None,
                   session_id: str | None = None) -> dict[str, Any]:
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

        agent_record = repos.agents.for_agent(agent_id, owner_id, session_id)
        agent = AgentCore(agent_record, repos.agents)
        from src.utils.postgres_checkpointer import has_pending_interrupt

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
        from src.agent.control import clear_pause

        clear_pause(agent_id)
        with self._lock:
            rt.execution_id = execution_id
        runtime = {**runtime, "agent_id": agent.id.agent_id, "owner_id": owner_id,
                   "policy": agent.policy.as_dict(), "policy_version": agent.policy.version,
                   "session_id": agent.id.latest_session_id}
        runtime.update({key: value for key, value in context().items() if value})
        runtime["enabled_tools"] = agent.policy.armory["tools"]
        runtime["enabled_subagents"] = agent.policy.armory["subagents"]

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
            trace_token = bind(agent_id=agent_id, execution_id=execution_id,
                               owner_id=owner_id, session_id=session_id)
            from src.utils.trace import set_trace_parent

            parent_token = set_trace_parent(runtime.get("trace_id"), runtime.get("span_id"))
            try:
                self._agent.run_turn(
                    agent_id=agent_id, owner_id=owner_id, queue=rt.queue, on_complete=_done,
                    resume_value=resume_value, is_resume=True, runtime=runtime, execution_id=execution_id,
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

    def ack(self, agent_id: str, seq: int) -> None:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if rt:
                rt.queue.ack(seq)

    def enqueue_control(self, agent_id: str, type_: str, payload: dict[str, Any] | None = None) -> None:
        with self._lock:
            rt = self._runtimes.get(agent_id)
            if rt:
                rt.queue.enqueue(type_, payload)


_manager: ChatRuntimeManager | None = None


def get_runtime_manager() -> ChatRuntimeManager:
    global _manager
    if _manager is None:
        _manager = ChatRuntimeManager()
    return _manager
