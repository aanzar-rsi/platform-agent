from __future__ import annotations

import logging
import sys
import threading
import uuid
import time
from pathlib import Path
from typing import Any, Callable

from api.core.config import get_settings
from api.services.packet_queue import ChatPacketQueue

logger = logging.getLogger(__name__)

_agent_app = None
_agent_lock = threading.Lock()


def ensure_client_path() -> None:
    settings = get_settings()
    root = str(settings.client_root)
    if root not in sys.path:
        sys.path.insert(0, root)


def get_agent_app():
    global _agent_app
    with _agent_lock:
        if _agent_app is not None:
            return _agent_app
        ensure_client_path()
        import os

        os.environ["EVA_SKIP_VENV_REEXEC"] = "1"
        from src.agent.graph import agent_app

        _agent_app = agent_app
        return _agent_app


class AgentRuntime:
    """Runs one LangGraph turn and fans events into a packet queue."""

    def __init__(self) -> None:
        self._cancel_flags: dict[str, threading.Event] = {}
        self._supersede_flags: dict[str, bool] = {}
        self._flag_lock = threading.Lock()

    def request_stop(self, agent_id: str, *, superseded: bool = False) -> None:
        """Cooperatively cancel the active run for this chat.

        `superseded=True` marks this as a fork preempting its own parent run
        (as opposed to a manual user Stop) — the resulting `run.completed`
        gets a `superseded` flag so the frontend knows to silently drop it
        instead of finalizing/showing it as the turn's answer.
        """
        with self._flag_lock:
            flag = self._cancel_flags.get(agent_id)
            if flag:
                flag.set()
            if superseded:
                self._supersede_flags[agent_id] = True

    def request_pause(self, agent_id: str) -> None:
        from src.agent.control import request_pause

        request_pause(agent_id)

    def _flag_for(self, agent_id: str) -> threading.Event:
        with self._flag_lock:
            flag = threading.Event()
            self._cancel_flags[agent_id] = flag
            return flag

    def _pop_supersede(self, agent_id: str) -> bool:
        with self._flag_lock:
            return self._supersede_flags.pop(agent_id, False)

    def _clear_flag(self, agent_id: str) -> None:
        with self._flag_lock:
            self._cancel_flags.pop(agent_id, None)
            self._supersede_flags.pop(agent_id, None)

    def run_turn(
        self,
        *,
        agent_id: str,
        owner_id: str,
        query: str | None = None,
        queue: ChatPacketQueue,
        checkpoint_id: str | None = None,
        preloaded_context: dict[str, Any] | None = None,
        on_complete: Callable[..., None] | None = None,
        resume_value: Any = None,
        is_resume: bool = False,
        runtime: dict[str, Any] | None = None,
        execution_id: str | None = None,
    ) -> None:
        from src.utils.trace import emit as trace_emit

        run_started_at = time.monotonic()
        cancel = self._flag_for(agent_id)
        execution_id = execution_id or str(uuid.uuid4())
        if (runtime or {}).get("agent_id"):
            trace_emit("run.lifecycle.start", component="agent_runtime", execution_id=execution_id,
                       agent_id=agent_id, owner_id=owner_id,
                       session_id=runtime.get("session_id"))
        outcome = "completed"
        outcome_error = None
        final_answer = None
        if is_resume:
            queue.enqueue("run.started", {"execution_id": execution_id, "resumed": True})
        else:
            queue.enqueue(
                "run.started",
                {"execution_id": execution_id, "query": query, "checkpoint_id": checkpoint_id},
            )
        # Immediate UI signal — LangGraph only emits node.started after the node
        # finishes, which left the client stuck on "Thinking…" during checkpoint
        # load / prompt prep / first LLM tokens.
        queue.enqueue("node.started", {"node": "agent_node"})

        try:
            from src.agent.subagent_stream import (
                reset_child_callback,
                reset_subagent_callback,
                set_child_callback,
                set_subagent_callback,
            )
            from src.agent.token_stream import (
                reset_cache_hit_callback,
                reset_token_callback,
                set_cache_hit_callback,
                set_token_callback,
            )
            from src.utils.agent_logger import log_event
            from src.utils.postgres_checkpointer import run_turn

            streamed_output: list[str] = []

            def on_token(text: str, channel: str, source: dict[str, Any] | None = None) -> None:
                if cancel.is_set():
                    return
                if channel == "output" and text:
                    streamed_output.append(text)
                payload = {"text": text, "channel": channel}
                if isinstance(source, dict):
                    if source.get("agent_id"):
                        payload["agent_id"] = source.get("agent_id")
                    if source.get("child_agent_id"):
                        payload["child_agent_id"] = source.get("child_agent_id")
                queue.enqueue("llm.token", payload)

            def on_subagent_event(agent_name: str, event: dict) -> None:
                if cancel.is_set():
                    return
                # Reasoning deltas are small, high-frequency chunks used purely for
                # live UI streaming — skip the structured log to avoid spamming it.
                if event.get("kind") != "reasoning_delta":
                    try:
                        log_event(
                            "subagent.step",
                            agent_name=agent_name,
                            step=event.get("step"),
                            status=event.get("status"),
                            kind=event.get("kind"),
                            message=event.get("message"),
                        )
                    except Exception:
                        pass
                queue.enqueue(
                    "subagent.step",
                    {"agent_name": agent_name, "child_agent_id": event.get("child_agent_id"), "event": event},
                )

            def on_cache_hit(payload: dict[str, Any]) -> None:
                if cancel.is_set():
                    return
                queue.enqueue("llm.cache_hit", payload)

            def on_child_event(agent_name: str, event: dict) -> None:
                if cancel.is_set():
                    return
                kind = event.get("kind")
                child_agent_id = event.get("child_agent_id")
                if kind == "start":
                    queue.enqueue(
                        "child.started",
                        {
                            "agent_name": agent_name,
                            "child_agent_id": child_agent_id,
                            "task": event.get("task"),
                        },
                    )
                    return

                if kind in {"complete", "error"}:
                    queue.enqueue(
                        "child.finished",
                        {
                            "agent_name": agent_name,
                            "child_agent_id": child_agent_id,
                            "task": event.get("task"),
                            "result": _truncate(event.get("result") or event.get("message")),
                            "success": bool(event.get("success", kind != "error")),
                        },
                    )
                    return

                if kind != "reasoning_delta":
                    try:
                        log_event(
                            "child.step",
                            agent_name=agent_name,
                            step=event.get("step"),
                            status=event.get("status"),
                            kind=event.get("kind"),
                            message=event.get("message"),
                        )
                    except Exception:
                        pass
                queue.enqueue(
                    "child.step",
                    {"agent_name": agent_name, "child_agent_id": child_agent_id, "event": event},
                )

            token = set_token_callback(on_token)
            cache_hit_token = set_cache_hit_callback(on_cache_hit)
            subagent_token = set_subagent_callback(on_subagent_event)
            child_token = set_child_callback(on_child_event)
            try:
                graph = get_agent_app()
                stream = run_turn(
                    graph,
                    agent_id,
                    query,
                    owner_id=owner_id,
                    checkpoint_id=checkpoint_id,
                    execution_id=execution_id,
                    preloaded_context=preloaded_context,
                    stream_mode=["updates", "custom"],
                    resume_value=resume_value,
                    is_resume=is_resume,
                    runtime=runtime,
                )
                final_answer = None
                turn_completed = False
                finished = False
                for item in stream:
                    if cancel.is_set():
                        stopped_answer = final_answer or "".join(streamed_output) or None
                        superseded = self._pop_supersede(agent_id)
                        log_event(
                            "run.stopped",
                            execution_id=execution_id,
                            answer=stopped_answer,
                            superseded=superseded,
                        )
                        queue.enqueue(
                            "run.completed",
                            {
                                "execution_id": execution_id,
                                "stopped": True,
                                "answer": stopped_answer,
                                "superseded": superseded,
                            },
                        )
                        outcome = "cancelled"
                        if (runtime or {}).get("agent_id"):
                            trace_emit("run.lifecycle.cancel", status="cancelled", component="agent_runtime",
                                       duration_ms=(time.monotonic() - run_started_at) * 1000)
                        break

                    # stream_mode list yields (mode, data) tuples
                    if isinstance(item, tuple) and len(item) == 2:
                        mode, data = item
                    else:
                        mode, data = "updates", item

                    if mode == "custom" and isinstance(data, dict):
                        # llm.token / subagent.step are already enqueued via ContextVar
                        # callbacks; skip stream-writer duplicates.
                        continue

                    if mode != "updates" or not isinstance(data, dict):
                        continue

                    if "__interrupt__" in data:
                        interrupts = data.get("__interrupt__") or ()
                        intr = interrupts[0] if interrupts else None
                        payload = getattr(intr, "value", None) if intr is not None else None
                        payload = payload if isinstance(payload, dict) else {"value": payload}
                        tip = None
                        try:
                            from src.utils.postgres_checkpointer import list_checkpoints

                            cps = list_checkpoints(agent_id)
                            tip = cps[0]["checkpoint_id"] if cps else None
                        except Exception:
                            pass
                        log_event(
                            "run.interrupted",
                            execution_id=execution_id,
                            kind=payload.get("kind"),
                            checkpoint_id=tip,
                        )
                        queue.enqueue(
                            "run.interrupted",
                            {
                                "execution_id": execution_id,
                                "interrupt_id": getattr(intr, "id", None) if intr is not None else None,
                                "kind": payload.get("kind"),
                                "payload": payload,
                                "checkpoint_id": tip,
                            },
                        )
                        turn_completed = True
                        outcome = "interrupted"
                        if (runtime or {}).get("agent_id"):
                            trace_emit("run.lifecycle.interrupt", component="agent_runtime",
                                       duration_ms=(time.monotonic() - run_started_at) * 1000,
                                       data={"checkpoint_id": tip})
                        break

                    for node_name, updates in data.items():
                        queue.enqueue(
                            "node.started",
                            {"node": node_name},
                        )
                        if not isinstance(updates, dict):
                            queue.enqueue("node.finished", {"node": node_name})
                            continue

                        next_step = updates.get("next_step") or {}
                        action = next_step.get("action")

                        if node_name == "agent_node" and updates.get("plan_created"):
                            queue.enqueue("plan.created", updates["plan_created"])
                        if node_name == "plan_dispatcher" and updates.get("plan_event", {}).get("kind") == "phase.started":
                            queue.enqueue("plan.phase.started", updates["plan_event"])
                            for planned in updates["plan_event"]["steps"]:
                                queue.enqueue("plan.step.started", {"sequence": updates["plan_event"]["sequence"], **planned})
                        if node_name == "phase_collector":
                            for result in updates.get("step_events") or []:
                                queue.enqueue("plan.step.finished", {**result, "result": _truncate(result.get("result"))})
                            if updates.get("plan_event", {}).get("kind") == "phase.finished":
                                queue.enqueue("plan.phase.finished", updates["plan_event"])

                        # Emit *.started only from agent_node's next_step decision.
                        # Emitting on the executor node name would duplicate the event
                        # when tool_node / subagent_node finish (they don't return next_step).
                        if node_name == "agent_node" and action == "tool":
                            queue.enqueue(
                                "tool.started",
                                {
                                    "tool_name": next_step.get("tool_name"),
                                    "tool_args": next_step.get("tool_args"),
                                    "task": next_step.get("task"),
                                },
                            )
                        if node_name == "agent_node" and action == "subagent":
                            queue.enqueue(
                                "subagent.started",
                                {
                                    "agent_name": next_step.get("agent_name"),
                                    "tool_args": next_step.get("tool_args"),
                                    "task": next_step.get("task"),
                                },
                            )
                        if "execution_history" in updates and node_name != "phase_collector":
                            hist = updates.get("execution_history") or []
                            if hist:
                                last = (next((entry for entry in hist if entry.get("child_agent_id") ==
                                              (updates.get("next_step") or {}).get("child_agent_id")), None)
                                        if node_name == "collect_child" else hist[-1])
                                if last is None:
                                    pass
                                elif last.get("type") == "tool":
                                    queue.enqueue(
                                        "tool.finished",
                                        {
                                            "tool_name": last.get("tool_name"),
                                            "tool_args": last.get("tool_args"),
                                            "task": last.get("task"),
                                            "result": _truncate(last.get("result")),
                                            "success": bool(
                                                isinstance(last.get("result"), dict)
                                                and last["result"].get("success", True)
                                            ),
                                        },
                                    )
                                elif last.get("type") == "subagent":
                                    if node_name != "collect_child" or last.get("status") != "running":
                                        queue.enqueue(
                                            "subagent.started" if last.get("status") == "running" else "subagent.finished",
                                            {"child_agent_id": last.get("child_agent_id"),
                                             "agent_name": last.get("agent_name"), "task": last.get("task"),
                                             "result": _truncate(last.get("result")),
                                             "success": bool(last.get("success", True))},
                                        )
                                elif last.get("type") == "child_agent":
                                    if node_name != "child_agent_node" and (
                                        node_name != "collect_child" or last.get("status") != "running"
                                    ):
                                        queue.enqueue(
                                            "child.started" if last.get("status") == "running" else "child.finished",
                                            {"child_agent_id": last.get("child_agent_id"),
                                             "agent_name": last.get("agent_name") or "child_agent",
                                             "task": last.get("task"),
                                             "result": _truncate(last.get("result")),
                                             "success": bool(last.get("success", True))},
                                        )

                        if action == "finish":
                            final_answer = next_step.get("answer")
                            log_event("run.answer", answer=final_answer)
                            queue.enqueue("llm.done", {"channel": "output"})

                        queue.enqueue(
                            "node.finished",
                            {
                                "node": node_name,
                                "next_step": {
                                    "action": action,
                                    "tool_name": next_step.get("tool_name"),
                                    "agent_name": next_step.get("agent_name"),
                                }
                                if next_step
                                else {},
                            },
                        )

                        if action == "finish" and not turn_completed:
                            turn_completed = True
                            finished = True
                            break
                else:
                    if not turn_completed:
                        finished = True
                if finished:
                    if cancel.is_set():
                        outcome = "cancelled"
                    elif runtime and runtime.get("agent_id"):
                        from src.agent.agent_core import child_runner

                        child_runner.join(execution_id)
                    if outcome == "completed":
                        _emit_turn_complete(queue, agent_id=agent_id, execution_id=execution_id,
                                            final_answer=final_answer)
                    elif outcome == "cancelled":
                        queue.enqueue("run.completed", {"execution_id": execution_id, "stopped": True,
                                                        "answer": None, "superseded": self._pop_supersede(agent_id)})
            finally:
                reset_token_callback(token)
                reset_cache_hit_callback(cache_hit_token)
                reset_subagent_callback(subagent_token)
                reset_child_callback(child_token)
        except Exception as exc:
            outcome = "failed"
            outcome_error = type(exc).__name__
            if (runtime or {}).get("agent_id"):
                trace_emit("run.lifecycle.error", status="error", error=exc, component="agent_runtime",
                           duration_ms=(time.monotonic() - run_started_at) * 1000)
            logger.exception("Agent execution failed agent_id=%s", agent_id)
            try:
                from src.utils.agent_logger import log_error

                log_error(execution_id=execution_id, message=str(exc))
            except Exception:
                pass
            queue.enqueue(
                "run.error",
                {"execution_id": execution_id, "message": str(exc)},
            )
        finally:
            self._clear_flag(agent_id)
            try:
                if outcome in {"failed", "cancelled"} and runtime and runtime.get("agent_id"):
                    from src.agent.agent_core import child_runner

                    child_runner.join(execution_id, cancel=True)
            except Exception as exc:
                outcome, outcome_error = "failed", type(exc).__name__
                queue.enqueue("run.error", {"execution_id": execution_id, "message": "Child collection failed"})
            if (runtime or {}).get("agent_id") and outcome in {"completed", "failed"}:
                trace_emit("run.lifecycle.end" if outcome == "completed" else "run.lifecycle.error",
                           status="ok" if outcome == "completed" else "error",
                           error=RuntimeError(outcome_error or "run_failed") if outcome == "failed" else None,
                           component="agent_runtime", duration_ms=(time.monotonic() - run_started_at) * 1000,
                           data={"run_state": outcome})
            if on_complete:
                on_complete(outcome, final_answer, outcome_error)


def _truncate(value: Any, limit: int = 2000) -> Any:
    text = str(value)
    if len(text) <= limit:
        return value if not isinstance(value, str) else text
    return text[:limit] + "…"


def _emit_turn_complete(
    queue: ChatPacketQueue,
    *,
    agent_id: str,
    execution_id: str,
    final_answer: str | None,
    stopped: bool = False,
) -> None:
    tip = None
    try:
        from src.utils.postgres_checkpointer import list_checkpoints

        cps = list_checkpoints(agent_id)
        tip = cps[0]["checkpoint_id"] if cps else None
    except Exception:
        tip = None
    queue.enqueue("checkpoint.created", {"checkpoint_id": tip})
    queue.enqueue(
        "run.completed",
        {
            "execution_id": execution_id,
            "stopped": stopped,
            "answer": final_answer,
            "checkpoint_id": tip,
        },
    )
