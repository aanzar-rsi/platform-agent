"""Process-local child execution orchestration for AgentCore."""

from __future__ import annotations

import threading
import time
from concurrent.futures import TimeoutError as FutureTimeout
from contextvars import copy_context
from typing import Callable

from api.db.repositories.agents import AgentRepository
from src.agent.agent_models import ChildHandle, Policy
from src.agent.policy import intersect_policy
from src.agent.policy_schema import normalize_armory_policy, normalize_memory_policy


class ChildRunner:
    """Bounded, process-local execution of durable child runs."""

    def __init__(self, repository: AgentRepository | None = None, *, workers: int = 8,
                 max_children: int = 5, max_depth: int = 3, timeout: float = 600) -> None:
        from concurrent.futures import ThreadPoolExecutor

        self.repository = repository or AgentRepository()
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="agent-child")
        self.max_children = max_children
        self.max_depth = max_depth
        self.timeout = timeout
        self._handles: dict[str, ChildHandle] = {}
        self._lock = threading.Lock()

    def spawn_child(self, parent: "AgentCore", task: str, adapter: Callable[[str, dict], str],
                    context: dict, *, requested_policy: Policy | None = None,
                    platform_policy: Policy | None = None) -> ChildHandle:
        from src.agent.agent_core import AgentCore

        if not parent.active_execution_id or parent.state != "open":
            raise ValueError("parent_not_running")
        if len(self.repository.children(parent.active_execution_id)) >= self.max_children:
            raise ValueError("child_limit")
        if requested_policy:
            requested_policy = Policy(
                armory=normalize_armory_policy({**parent.policy.armory, **requested_policy.armory}),
                memory=normalize_memory_policy({**parent.policy.memory, **requested_policy.memory}),
                guardrails=parent.policy.guardrails,
                observability=parent.policy.observability,
                version=parent.policy.version,
            )
        policy = intersect_policy(parent.policy, requested_policy, platform_policy)
        child_record = self.repository.child(parent.id.agent_id, policy.as_dict(), max_depth=self.max_depth,
                                             parent_execution_id=parent.active_execution_id, max_children=self.max_children)
        child = AgentCore(child_record, self.repository, auto_close_on_result=True)
        try:
            execution_id = child.run(parent_execution_id=parent.active_execution_id)
        except Exception:
            child.close()
            raise
        from src.agent.subagent_stream import emit_child_event
        from src.agent.token_stream import reset_token_callback, set_token_callback
        from src.utils.trace import bind, emit, in_run, reset

        if in_run():
            emit(
                "child.lifecycle.spawn",
                child_agent_id=child.id.agent_id,
                parent_agent_id=parent.id.agent_id,
                data={
                    "task_size": len(task),
                    "requested_policy_version": (requested_policy or parent.policy).version,
                    "effective_policy_version": policy.version,
                },
                component="child_runner",
            )
        try:
            self.repository.append_message(parent.id.agent_id, parent.active_execution_id, task,
                                           sender_type="agent", sender_id=parent.id.agent_id,
                                           child_agent_id=child.id.agent_id, visible_to_user=False)
            self.repository.append_message(child.id.agent_id, execution_id, task,
                                           sender_type="agent", sender_id=parent.id.agent_id)
        except Exception:
            child.finish("failed", error="spawn_failed")
            child.close()
            raise

        cancel_event = threading.Event()
        deadline = time.monotonic() + self.timeout

        emit_child_event(context.get("agent_name", "child_agent"), {
            "kind": "start",
            "step": "spawn",
            "status": "in_progress",
            "message": "Starting",
            "task": task,
            "child_agent_id": child.id.agent_id,
        })

        def work() -> str:
            token = bind(agent_id=child.id.agent_id, execution_id=execution_id,
                         owner_id=parent.memory.user_id, session_id=child.id.latest_session_id,
                         parent_agent_id=parent.id.agent_id, child_agent_id=child.id.agent_id)
            token_callback = set_token_callback(
                lambda text, channel: emit_child_event(
                    context.get("agent_name", "child_agent"),
                    {
                        "kind": "reasoning",
                        "step": "reasoning",
                        "status": "in_progress",
                        "message": text,
                        "reasoningDone": False,
                        "child_agent_id": child.id.agent_id,
                    },
                )
                if channel == "reasoning" and text
                else None
            )
            try:
                if in_run():
                    emit("child.lifecycle.start", component="child_runner")
                if cancel_event.is_set():
                    raise InterruptedError("child_cancelled")
                child_context = {
                    **dict(context or {}),
                    "runtime": {
                        **(dict((context or {}).get("runtime") or {})),
                        "agent_id": child.id.agent_id,
                        "owner_id": parent.memory.user_id,
                        "session_id": child.id.latest_session_id,
                        "execution_id": execution_id,
                        "child_agent_id": child.id.agent_id,
                        "policy": child.policy.as_dict(),
                        "policy_version": child.policy.version,
                    },
                    "child_agent_id": child.id.agent_id,
                }
                result = adapter(task, child_context)
                if cancel_event.is_set() or time.monotonic() >= deadline:
                    raise TimeoutError("child_timeout") if time.monotonic() >= deadline else InterruptedError("child_cancelled")
                self.repository.append_message(child.id.agent_id, execution_id, str(result),
                                               sender_type="agent", sender_id=child.id.agent_id)
                child.finish("completed", result=str(result))
                if in_run():
                    emit("child.lifecycle.end", data={"success": True, "result_size": len(str(result))},
                         component="child_runner")
                emit_child_event(context.get("agent_name", "child_agent"), {
                    "kind": "complete",
                    "step": "collect",
                    "status": "completed",
                    "message": "Completed",
                    "result": str(result),
                    "success": True,
                    "child_agent_id": child.id.agent_id,
                })
                return result
            except Exception as exc:
                status = "timeout" if isinstance(exc, TimeoutError) else "cancelled" if isinstance(exc, InterruptedError) else "error"
                if in_run():
                    emit("child.lifecycle.error", status=status, error=exc, component="child_runner")
                child.finish("cancelled" if status == "cancelled" else "failed", error=type(exc).__name__)
                emit_child_event(context.get("agent_name", "child_agent"), {
                    "kind": "error",
                    "step": "collect",
                    "status": "error",
                    "message": status,
                    "result": type(exc).__name__,
                    "success": False,
                    "child_agent_id": child.id.agent_id,
                })
                raise
            finally:
                reset_token_callback(token_callback)
                reset(token)

        ctx = copy_context()
        try:
            future = self.pool.submit(ctx.run, work)
        except Exception:
            child.finish("failed", error="worker_unavailable")
            raise
        handle = ChildHandle(child.id.agent_id, execution_id, future, cancel_event, deadline)
        with self._lock:
            self._handles[handle.child_agent_id] = handle
        return handle

    def spawn_subagent(self, parent: "AgentCore", task: str, adapter: Callable[[str, dict], str],
                       context: dict, *, requested_policy: Policy | None = None,
                       platform_policy: Policy | None = None) -> ChildHandle:
        return self.spawn_child(parent, task, adapter, context, requested_policy=requested_policy,
                                platform_policy=platform_policy)

    def await_child(self, child_agent_id: str, *, parent_agent_id: str | None = None,
                    parent_execution_id: str | None = None, timeout: float | None = None) -> str:
        if parent_agent_id and parent_execution_id and not self.repository.child_outcome(
            parent_agent_id, parent_execution_id, child_agent_id
        ):
            raise PermissionError("child_not_owned")
        with self._lock:
            handle = self._handles.get(child_agent_id)
        if handle:
            try:
                return handle.future.result(timeout=self.timeout if timeout is None else timeout)
            except FutureTimeout:
                raise TimeoutError("child_still_running") from None
            except Exception:
                row = self.repository.latest_execution(child_agent_id)
                if row and row["state"] != "completed":
                    raise RuntimeError(row["error"] or row["state"]) from None
                raise
        child = self.repository.get(child_agent_id)
        if not child:
            raise ValueError("child_not_found")
        run = self.repository.active_execution(child_agent_id)
        if run:
            raise ValueError("child_still_running")
        row = self.repository.latest_execution(child_agent_id)
        if row is None:
            raise ValueError("child_execution_not_found")
        if row["state"] != "completed":
            raise RuntimeError(row["error"] or row["state"])
        return row["result"] or ""

    def join(self, parent_execution_id: str, *, cancel: bool = False) -> None:
        """Before a parent finishes, collect all its children by persisted lineage."""
        rows = self.repository.children(parent_execution_id)
        if cancel:
            for row in rows:
                if row["execution_state"] in {"running", "interrupted"}:
                    self.cancel(str(row["agent_id"]))
        for row in rows:
            if row["execution_state"] in {"running", "interrupted"}:
                child_id = str(row["agent_id"])
                if not self.repository.active_execution(child_id):
                    continue
                try:
                    self.await_child(child_id, timeout=self.timeout)
                except TimeoutError:
                    if self.repository.active_execution(child_id) and not cancel:
                        raise
                except Exception:
                    if not cancel:
                        continue
                if not cancel and self.repository.active_execution(child_id):
                    raise TimeoutError("child_still_running")

    def shutdown(self) -> None:
        self.pool.shutdown(wait=False, cancel_futures=True)

    def cancel(self, child_agent_id: str) -> bool:
        with self._lock:
            handle = self._handles.get(child_agent_id)
        if not handle:
            return False
        handle.cancel_event.set()
        queued = handle.future.cancel()
        from src.utils.trace import in_run, emit

        if in_run():
            emit("child.lifecycle.error", status="cancelled", child_agent_id=child_agent_id,
                 component="child_runner")
        if queued:
            self.repository.finish_execution(handle.execution_id, "cancelled")
            self.repository.close(child_agent_id)
        return True

    @staticmethod
    def run_child_graph(task: str, context: dict) -> str:
        from src.agent.graph import agent_app
        from src.utils.postgres_checkpointer import run_turn

        values = dict(context or {})
        runtime = values.get("runtime") or {}
        agent_id = runtime.get("agent_id")
        owner_id = values.get("uid") or runtime.get("owner_id") or "local-user"
        execution_id = runtime.get("execution_id")
        if not agent_id:
            raise ValueError("child_runtime_missing_agent_id")
        stream = run_turn(
            agent_app,
            agent_id,
            task,
            owner_id=owner_id,
            execution_id=execution_id,
            runtime=runtime,
            bind_logger=False,
        )
        final = ""
        for item in stream:
            if isinstance(item, dict) and "agent_node" in item:
                step = item.get("agent_node") or {}
                ns = step.get("next_step") or {}
                if ns.get("action") == "finish":
                    final = str(ns.get("answer") or "")
        return final


child_runner = ChildRunner()
