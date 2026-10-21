"""Cooperative "pause anywhere" registry for user-initiated mid-run pauses.

Each thread (chat) can have a pending pause flag. Nodes call `maybe_pause`
at the very top, before any side-effecting work. If a pause was requested,
it raises a LangGraph `interrupt()` so the run cleanly stops at this
super-step boundary and can be resumed exactly where it left off.

On resume, LangGraph replays the interrupted node from the top. The pause
flag may still be set because the first `interrupt()` raised before
`clear_pause` could run. Nodes therefore also consult the graph's pending
interrupt list (`pause_gate_active`) so the `interrupt()` call site is still
hit after `clear_pause` is called in `resume_run`.
"""

from __future__ import annotations

import threading

_flags: dict[str, threading.Event] = {}
_lock = threading.Lock()


def request_pause(thread_id: str) -> None:
    """Ask the run for this thread to pause at the next node boundary."""
    with _lock:
        _flags.setdefault(thread_id, threading.Event()).set()


def is_pause_requested(thread_id: str) -> bool:
    with _lock:
        flag = _flags.get(thread_id)
        return bool(flag and flag.is_set())


def clear_pause(thread_id: str) -> None:
    with _lock:
        flag = _flags.get(thread_id)
        if flag:
            flag.clear()


def thread_id_from_config(config) -> str | None:
    return ((config or {}).get("configurable") or {}).get("thread_id")


def _pending_interrupt_at_node(
    thread_id: str,
    node: str,
    kinds: frozenset[str] | None = None,
) -> bool:
    """True when the graph tip has a pending interrupt raised at `node`."""
    try:
        from src.agent.graph import agent_app
        from src.utils.postgres_checkpointer import build_config

        snap = agent_app.get_state(build_config(thread_id))
    except Exception:
        return False

    allowed = kinds or frozenset({"paused"})
    for task in getattr(snap, "tasks", None) or ():
        for intr in getattr(task, "interrupts", None) or ():
            val = getattr(intr, "value", None)
            if not isinstance(val, dict):
                continue
            if val.get("node") != node:
                continue
            kind = val.get("kind") or "paused"
            if kind in allowed:
                return True
    return False


def pause_gate_active(
    thread_id: str | None,
    node: str,
    *,
    kinds: frozenset[str] | None = None,
) -> bool:
    """Whether this node should enter its pause/confirm interrupt gate."""
    if not thread_id:
        return False
    if is_pause_requested(thread_id):
        return True
    return _pending_interrupt_at_node(thread_id, node, kinds)


class _NotPaused:
    """Sentinel distinct from any real resume value (which may itself be
    `None`/falsy), so callers can reliably tell "wasn't paused" apart from
    "was paused and resumed with an empty/no-op value"."""

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return "NOT_PAUSED"


NOT_PAUSED = _NotPaused()


def maybe_pause(config, *, node: str, extra: dict | None = None):
    """Call at the very top of a node, before any side effects.

    Returns the `NOT_PAUSED` sentinel immediately if no pause gate applies.
    Otherwise raises a LangGraph interrupt; once resumed, clears the flag and
    returns the resume payload (whatever the client sent — typically `None`/`{}`
    for a plain "resume", or free text / a dict with a "note").
    """
    thread_id = thread_id_from_config(config)
    if not thread_id or not pause_gate_active(thread_id, node):
        return NOT_PAUSED

    from langgraph.types import interrupt

    payload: dict = {"kind": "paused", "node": node}
    if extra:
        payload.update(extra)
    resume_value = interrupt(payload)
    clear_pause(thread_id)
    return resume_value


def note_text_from_resume(value) -> str:
    """Best-effort extraction of free-text the user typed while paused/asked,
    regardless of whether the client sent a raw string or a small dict."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("note", "text", "answer", "message"):
            v = value.get(key)
            if isinstance(v, str):
                return v
    return ""