"""Per-run token callback plumbing for agent_node (API / CLI safe)."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Callable, Optional

TokenCallback = Callable[[str, str], None]  # (text, channel)
UsageCallback = Callable[[dict[str, Any]], None]
CacheHitCallback = Callable[[dict[str, Any]], None]

_token_callback: ContextVar[Optional[TokenCallback]] = ContextVar(
    "eva_token_callback", default=None
)
_usage_callback: ContextVar[Optional[UsageCallback]] = ContextVar(
    "eva_usage_callback", default=None
)
_cache_hit_callback: ContextVar[Optional[CacheHitCallback]] = ContextVar(
    "eva_cache_hit_callback", default=None
)


def set_token_callback(callback: Optional[TokenCallback]):
    """Bind a token callback for the current context; returns a reset token."""
    return _token_callback.set(callback)


def reset_token_callback(token) -> None:
    _token_callback.reset(token)


def set_usage_callback(callback: Optional[UsageCallback]):
    return _usage_callback.set(callback)


def reset_usage_callback(token) -> None:
    _usage_callback.reset(token)


def set_cache_hit_callback(callback: Optional[CacheHitCallback]):
    return _cache_hit_callback.set(callback)


def reset_cache_hit_callback(token) -> None:
    _cache_hit_callback.reset(token)


def emit_token(text: str, channel: str = "output") -> None:
    callback = _token_callback.get()
    if callback is not None:
        callback(text, channel)
    try:
        from langgraph.config import get_stream_writer

        writer = get_stream_writer()
        writer({"type": "llm.token", "text": text, "channel": channel})
    except Exception:
        pass


def emit_usage(usage: dict[str, Any]) -> None:
    callback = _usage_callback.get()
    if callback is not None:
        callback(usage)
    try:
        from langgraph.config import get_stream_writer

        get_stream_writer()({"type": "llm.usage", "usage": usage})
    except Exception:
        pass


def emit_cache_hit(payload: dict[str, Any]) -> None:
    callback = _cache_hit_callback.get()
    if callback is not None:
        callback(payload)
    try:
        from langgraph.config import get_stream_writer

        get_stream_writer()({"type": "llm.cache_hit", **payload})
    except Exception:
        pass
