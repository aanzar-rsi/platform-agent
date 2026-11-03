"""Canonical, redacted JSON trace events for API and agent operations."""

from __future__ import annotations

import json
import logging
import os
import re
import socket
import threading
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("agent.trace")
_persist_logger = logging.getLogger(__name__)
_context: ContextVar[dict[str, Any]] = ContextVar("agent_trace_context", default={})
_CLIENT_ROOT = Path(__file__).resolve().parents[2]
_TRACE_DIR = Path(os.environ.get("EVA_TRACE_LOG_DIR") or (_CLIENT_ROOT / "logs" / "traces"))
_TRACE_LOCK = threading.Lock()
_TRACE_FILES: dict[str, Path] = {}
_TRACE_STDOUT = {"1", "true", "yes", "on"}
_ids = ("request_id", "agent_id", "execution_id", "session_id", "owner_id",
        "owner_type", "tenant_id", "parent_agent_id", "child_agent_id")
_safe_data = {"method", "path", "http_status", "client_type", "reason", "checkpoint_id", "resumed",
              "node", "action", "tool_name", "agent_name", "arg_keys", "success", "scope",
              "scope_counts", "top_k", "returned_count", "policy_version", "old_version", "new_version",
              "changed_keys", "guardrail_type", "decision", "reason_code", "child_agent_id",
              "requested_policy_version", "effective_policy_version", "result_size", "query_hash",
               "attempt", "task_size", "run_state"}
_safe_data.update({"promotion_request_id", "source_chunk_id", "target_chunk_id", "from_scope", "to_scope"})

# Only schema-listed names are emitted. Extend requirements/02_TRACE_SCHEMA.md first.
EVENTS = frozenset({
    "api.request.start", "api.request.end", "api.request.error",
    "session.websocket.attach", "session.websocket.detach",
    "run.lifecycle.start", "run.lifecycle.interrupt", "run.lifecycle.cancel",
    "run.lifecycle.end", "run.lifecycle.error", "node.execution.start", "node.execution.end",
    "node.routing.decision", "armory.discovery.list", "armory.authz.allow", "armory.authz.deny",
    "tool.call.start", "tool.call.end", "tool.call.error", "armory.call.start", "armory.call.end",
    "armory.call.error", "memory.retrieve.start",
    "memory.retrieve.end", "memory.retrieve.denied", "memory.write.start", "memory.write.end",
    "memory.write.denied", "subagent.lifecycle.spawn", "subagent.lifecycle.start",
    "subagent.lifecycle.progress", "subagent.lifecycle.end", "subagent.lifecycle.error",
    "subagent.lifecycle.close", "child.lifecycle.spawn", "child.lifecycle.start",
    "child.lifecycle.progress", "child.lifecycle.end", "child.lifecycle.error",
    "child.lifecycle.close", "guardrail.input.check", "guardrail.resource.check",
    "guardrail.output.check", "guardrail.decision.allow", "guardrail.decision.deny",
    "guardrail.decision.approval_required", "policy.armory.update", "policy.memory.update",
    "checkpoint.create", "checkpoint.list", "checkpoint.resume", "checkpoint.error",
    "node.execution.error",
    "memory.promotion.requested", "memory.promotion.validated", "memory.promotion.approved",
    "memory.promotion.rejected", "memory.promotion.activated", "memory.promotion.failed",
    "memory.promotion.cancelled",
    "memory.revoke", "memory.demote", "memory.revalidate",
})


def bind(**fields: Any):
    current = _context.get()
    ids = dict(current.get("ids") or {})
    ids.update({key: str(value) if value is not None else None for key, value in fields.items() if key in _ids})
    return _context.set({**current, "ids": ids,
                         "trace_id": current.get("trace_id") or "trc_" + uuid.uuid4().hex,
                         "span_id": current.get("span_id")})


def context() -> dict[str, Any]:
    return {"trace_id": _context.get().get("trace_id"), "span_id": _context.get().get("span_id")}


def set_trace_parent(trace_id: str | None, span_id: str | None):
    if trace_id:
        return _context.set({**_context.get(), "trace_id": trace_id, "span_id": span_id})
    return None


def reset(token) -> None:
    _context.reset(token)


def current_ids() -> dict[str, Any]:
    return dict(_context.get().get("ids") or {})


def in_run() -> bool:
    return all(current_ids().get(key) for key in ("agent_id", "execution_id"))


def bind_from_config(config: dict | None):
    values = (config or {}).get("configurable") or {}
    if not values.get("agent_id") or not values.get("execution_id"):
        return None
    current = _context.get()
    ids = {**(current.get("ids") or {}),
           **{key: str(values[key]) for key in _ids if values.get(key) is not None}}
    return _context.set({**current, "ids": ids,
                         "trace_id": values.get("trace_id") or current.get("trace_id") or "trc_" + uuid.uuid4().hex,
                         "span_id": values.get("span_id") or current.get("span_id")})


def _error(exc: BaseException | None, status: str) -> dict | None:
    if status not in {"error", "timeout", "denied"}:
        return None
    name = type(exc).__name__ if exc else "Denied"
    return {"code": name.upper(), "type": name, "message": name, "retryable": status == "timeout",
            "stack": None}


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip()) or "unbound"


def _filename_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _trace_path(ids: dict[str, Any]) -> Path:
    key = _safe_id(str(ids.get("agent_id") or "unbound"))
    path = _TRACE_FILES.get(key)
    if path is None:
        path = _TRACE_DIR / f"{_filename_timestamp()}_{key}.json"
        _TRACE_FILES[key] = path
    return path


def _persist(record: dict[str, Any]) -> None:
    ids = record.get("ids") or {}
    path = _trace_path(ids)
    meta = {
        "session_id": ids.get("session_id"),
        "agent_id": ids.get("agent_id"),
        "owner_id": ids.get("owner_id"),
    }
    try:
        with _TRACE_LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(payload, dict):
                    payload = {**meta, "events": []}
            else:
                payload = {**meta, "events": []}
            events = payload.get("events")
            if not isinstance(events, list):
                events = []
            events.append(record)
            payload["events"] = events
            path.write_text(json.dumps(payload, ensure_ascii=False, default=str), encoding="utf-8")
    except Exception:
        _persist_logger.warning("Trace file write failed path=%s", path, exc_info=True)


def emit(event: str, *, status: str = "ok", data: dict | None = None,
         duration_ms: float | None = None, error: BaseException | None = None,
         component: str = "backend", span_id: str | None = None,
         parent_span_id: str | None = None, **ids: Any) -> dict:
    if event not in EVENTS:
        raise ValueError("unknown_trace_event")
    if status not in {"ok", "error", "cancelled", "timeout", "denied"}:
        raise ValueError("invalid_trace_status")
    if (event.endswith((".end", ".error")) or status in {"error", "timeout", "denied"}) and duration_ms is None:
        duration_ms = 0
    context = _context.get()
    merged = {key: None for key in _ids}
    merged.update(context.get("ids") or {})
    merged.update({key: str(value) if value is not None else None for key, value in ids.items() if key in _ids})
    if event.startswith(("run.", "node.", "tool.", "subagent.", "child.", "memory.", "policy.",
                          "guardrail.", "checkpoint.", "armory.")):
        keys = ("agent_id",) if event.startswith("checkpoint.") and not merged["execution_id"] else (
            "agent_id", "execution_id")
        if not all(merged.get(key) for key in keys):
            raise ValueError("missing_trace_correlation")
    given = data or {}
    safe = {key: value for key, value in given.items() if key in _safe_data}
    for key in ("tool_name", "agent_name", "checkpoint_id"):
        if key in safe:
            safe[key] = re.sub(r"[^A-Za-z0-9_.*:-]", "_", str(safe[key]))[:120]
    redacted_reason = "reason" in safe
    if redacted_reason:
        safe["reason"] = "redacted"
    if "arg_keys" in safe:
        safe["arg_keys"] = [str(key)[:40] for key in safe["arg_keys"]][:40]
    if "path" in safe:
        safe["path"] = re.sub(r"(/agents)/[^/]+", r"\1/:id", str(safe["path"]))
        safe["path"] = re.sub(r"/[0-9a-fA-F-]{32,36}(?=/|$)", "/:id", safe["path"])
    record = {
        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "event": event, "status": status,
        "level": "error" if status in {"error", "timeout"} else "warn" if status == "denied" else "info",
        "message": event, "trace": {"trace_id": context.get("trace_id") or "trc_" + uuid.uuid4().hex,
                                    "span_id": span_id or "spn_" + uuid.uuid4().hex,
                                    "parent_span_id": (parent_span_id if span_id else context.get("span_id"))},
        "ids": merged,
        "runtime": {"service": "backend", "component": component, "environment": "dev",
                    "host": socket.gethostname(), "thread": threading.current_thread().name,
                    "process": os.getpid(), "version": "local"},
        "metrics": {"duration_ms": duration_ms, "attempt": 1}, "data": safe,
        "error": _error(error, status),
        "security": {"contains_redacted": len(safe) != len(given) or redacted_reason,
                     "redaction_tags": ["data"] if len(safe) != len(given) or redacted_reason else []},
    }
    _persist(record)
    if os.environ.get("EVA_TRACE_LOGGER_ENABLED", "").strip().lower() in _TRACE_STDOUT:
        logger.info(json.dumps(record, default=str))
    return record


@contextmanager
def span(domain: str, entity: str, *, component: str, data: dict | None = None):
    name = f"{domain}.{entity}"
    parent = _context.get()
    span_id = "spn_" + uuid.uuid4().hex
    parent_span_id = parent.get("span_id")
    token = _context.set({**parent, "span_id": span_id,
                          "trace_id": parent.get("trace_id") or "trc_" + uuid.uuid4().hex})
    start = time.monotonic()
    try:
        emit(name + ".start", component=component, data=data, span_id=span_id,
             parent_span_id=parent_span_id)
        yield data
    except BaseException as exc:
        error_event = name + ".error" if name + ".error" in EVENTS else name + ".end"
        emit(error_event, status="timeout" if isinstance(exc, TimeoutError) else "error",
             duration_ms=(time.monotonic() - start) * 1000, error=exc, component=component,
              data=data, span_id=span_id, parent_span_id=parent_span_id)
        raise
    else:
        status = "error" if name == "api.request" and (data or {}).get("http_status", 200) >= 400 else "ok"
        emit(name + ".end", status=status,
             error=RuntimeError("http_error") if status == "error" else None,
             duration_ms=(time.monotonic() - start) * 1000,
             component=component, data=data, span_id=span_id,
             parent_span_id=parent_span_id)
    finally:
        _context.reset(token)


def traced_node(name: str, fn):
    """Wrap LangGraph nodes once so every exit (including caught failures) is traced."""
    def wrapped(state, config=None):
        token = bind_from_config(config) if not in_run() else None
        try:
            if not in_run():
                return fn(state, config)
            with span("node", "execution", component=name, data={"node": name}):
                return fn(state, config)
        finally:
            if token is not None:
                reset(token)
    return wrapped
