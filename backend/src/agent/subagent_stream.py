"""Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).

Mirrors `token_stream.py`: a sub-agent implementation
calls `emit_subagent_event(...)` as it makes internal progress; whoever is
running the outer graph turn binds a callback via `set_subagent_callback`
to forward those events (e.g. onto a websocket queue).
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Callable, Optional

SubagentEventCallback = Callable[[str, dict[str, Any]], None]  # (agent_name, event)
ChildEventCallback = Callable[[str, dict[str, Any]], None]  # (agent_name, event)

_subagent_callback: ContextVar[Optional[SubagentEventCallback]] = ContextVar(
    "eva_subagent_callback", default=None
)
_child_callback: ContextVar[Optional[ChildEventCallback]] = ContextVar(
    "eva_child_callback", default=None
)


def set_subagent_callback(callback: Optional[SubagentEventCallback]):
    """Bind a sub-agent progress callback for the current context; returns a reset token."""
    return _subagent_callback.set(callback)


def reset_subagent_callback(token) -> None:
    _subagent_callback.reset(token)


def emit_subagent_event(agent_name: str, event: dict[str, Any]) -> None:
    from src.utils.trace import emit, in_run

    if in_run() and event.get("kind") != "reasoning_delta":
        emit("subagent.lifecycle.progress", component="subagent_stream",
             child_agent_id=event.get("child_agent_id"),
             data={"agent_name": agent_name})
    callback = _subagent_callback.get()
    if callback is not None:
        callback(agent_name, event)
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        writer({"type": "subagent.step", "agent_name": agent_name, "event": event})
    except Exception:
        pass


def set_child_callback(callback: Optional[ChildEventCallback]):
    return _child_callback.set(callback)


def reset_child_callback(token) -> None:
    _child_callback.reset(token)


def emit_child_event(agent_name: str, event: dict[str, Any]) -> None:
    from src.utils.trace import emit, in_run

    if in_run() and event.get("kind") != "reasoning_delta":
        emit("child.lifecycle.progress", component="subagent_stream",
             child_agent_id=event.get("child_agent_id"), data={"agent_name": agent_name})
    callback = _child_callback.get()
    if callback is not None:
        callback(agent_name, event)
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        writer({"type": "child.step", "agent_name": agent_name, "event": event})
    except Exception:
        pass
