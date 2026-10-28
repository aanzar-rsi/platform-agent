"""Load chat trajectory from the main agent checkpointer."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import BaseMessage

from src.subagents.learner_agent.state import LearnerState
from api.db.repositories.agents import AgentRepository
from api.db.repositories.preferences import PreferencesRepository
from src.agent.agent_core import AgentCore
from src.agent.policy_schema import (
    DEFAULT_CHUNK_TYPES,
    effective_memory_policy,
    memory_action_allowed,
    memory_requires_extract_confirmation,
)
from src.subagents.learner_agent.keys import build_decision_state
from src.agent.nodes.output_security_gate import sanitize_value

logger = logging.getLogger(__name__)


def _message_line(msg: Any) -> str:
    role = getattr(msg, "type", None) or "unknown"
    content = sanitize_value(getattr(msg, "content", ""))
    if not isinstance(content, str):
        content = str(content)
    if len(content) > 500:
        content = content[:500] + "…"
    return f"{role}: {content}"


def _latest_human(messages: list[Any]) -> str:
    for msg in reversed(messages):
        if getattr(msg, "type", None) == "human":
            content = sanitize_value(getattr(msg, "content", ""))
            return content if isinstance(content, str) else str(content)
    return ""


def _slim_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slim: list[dict[str, Any]] = []
    for entry in history:
        result = entry.get("result")
        result_preview = sanitize_value(result)
        if isinstance(result_preview, str) and len(result_preview) > 800:
            result_preview = result_preview[:800] + "…"
        elif isinstance(result_preview, dict):
            # keep structure but cap error/body strings
            bounded = {}
            for k, v in list(result_preview.items())[:12]:
                if isinstance(v, str) and len(v) > 400:
                    bounded[k] = v[:400] + "…"
                else:
                    bounded[k] = v
            result_preview = bounded
        slim.append(
            {
                "type": entry.get("type"),
                "tool_name": entry.get("tool_name") or entry.get("agent_name"),
                "resource_type": entry.get("resource_type") or ("child_agent" if entry.get("type") == "child_agent" else ""),
                "resource_name": entry.get("resource_name") or entry.get("tool_name") or entry.get("agent_name") or "",
                "tool_args": sanitize_value(entry.get("tool_args") or entry.get("arguments") or {}),
                "task": entry.get("task") or "",
                "key": entry.get("key"),
                "success": entry.get("success", True),
                "status": entry.get("status") or "completed",
                "child_agent_id": entry.get("child_agent_id") or "",
                "requested_policy": sanitize_value(entry.get("requested_policy") or {}),
                "result": result_preview,
            }
        )
    return slim


def _conversation_messages(messages: list[Any]) -> list[dict[str, Any]]:
    out = []
    for index, message in enumerate(messages[-30:]):
        role = getattr(message, "type", None) or "unknown"
        content = sanitize_value(getattr(message, "content", ""))
        content = content if isinstance(content, str) else str(content)
        out.append({"sequence": index, "role": role, "content": content[:2000]})
    return out


def _decision_snapshots(user_query: str, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snapshots = [build_decision_state(user_query, [])]
    for index in range(len(history)):
        snapshot = build_decision_state(user_query, history[: index + 1])
        snapshot["boundary_index"] = index + 1
        snapshots.append(snapshot)
    return snapshots[-10:]


def load_session_node(state: LearnerState) -> dict:
    agent_id = state.get("agent_id") or ""
    if not agent_id:
        return {"status": "error", "error": "missing agent_id", "chunks": []}

    try:
        from src.agent.graph import agent_app
        from src.utils.postgres_checkpointer import build_config

        uid = state.get("uid") or "local-user"
        checkpoint_id = state.get("branch_checkpoint_id") or None
        config = build_config(agent_id, owner_id=uid, checkpoint_id=checkpoint_id)
        snap = agent_app.get_state(config)
        values = getattr(snap, "values", None) or {}
        if not values:
            return {
                "status": "skipped",
                "error": "no checkpoint state",
                "chunks": [],
                "execution_history": [],
                "user_query": "",
                "messages_summary": "",
            }

        messages = values.get("messages") or []
        history = values.get("execution_history") or []
        record = AgentRepository().get(agent_id)
        if not record:
            return {"status": "error", "error": "agent_not_found", "chunks": []}
        owner_id = state.get("uid") or str(record.get("owner_id") or "")
        user_ceiling = ((PreferencesRepository().get(owner_id).get("agent") or {}).get("memory_policy_ceiling"))
        memory_policy = effective_memory_policy(AgentCore(record).policy.memory, user_ceiling)
        checkpoint = state.get("branch_checkpoint_id") or ""
        allowed_types: list[str] = []
        extraction_requests: dict[str, dict[str, Any]] = {}
        for chunk_type in DEFAULT_CHUNK_TYPES:
            if not memory_action_allowed(memory_policy, action="write", scope="USER", chunk_type=chunk_type):
                continue
            if not (checkpoint and memory_requires_extract_confirmation(memory_policy, chunk_type=chunk_type)):
                allowed_types.append(chunk_type)
                continue
            from api.db.repositories.memory_extractions import MemoryExtractionRepository

            repo = MemoryExtractionRepository()
            request = repo.latest(agent_id=agent_id, checkpoint_id=checkpoint, chunk_type=chunk_type)
            if not request:
                request = repo.create_pending(owner_id=owner_id, agent_id=agent_id,
                                              checkpoint_id=checkpoint, chunk_type=chunk_type)
            extraction_requests[chunk_type] = {
                "request_id": request.get("request_id") or "",
                "state": request.get("state") or "APPROVAL_PENDING",
            }
            if request.get("state") == "APPROVED":
                allowed_types.append(chunk_type)
        if not isinstance(history, list):
            history = []
        user_query = _latest_human(messages) if messages else ""
        if not history and not user_query:
            return {
                "status": "skipped",
                "error": "no conversation evidence to learn from",
                "chunks": [],
                "execution_history": [],
                "user_query": _latest_human(messages) if messages else "",
                "messages_summary": "\n".join(_message_line(m) for m in messages[-20:]),
            }

        msg_lines = [_message_line(m) for m in messages[-20:] if isinstance(m, BaseMessage) or hasattr(m, "content")]
        slim_history = _slim_history(history)
        pending_types = [kind for kind, request in extraction_requests.items()
                         if request.get("state") == "APPROVAL_PENDING"]
        if not allowed_types:
            return {
                "status": "pending_confirmation" if pending_types else "skipped",
                "error": "awaiting_extraction_confirmation" if pending_types else "no writable chunk types",
                "chunks": [], "execution_history": slim_history, "user_query": user_query,
                "messages_summary": "\n".join(_message_line(m) for m in messages[-20:]),
                "conversation_messages": _conversation_messages(messages), "policy": memory_policy,
                "extraction_requests": extraction_requests, "allowed_chunk_types": [],
            }
        out = {
            "status": "pending",
            "user_query": user_query,
            "messages_summary": "\n".join(msg_lines) or "(none)",
            "conversation_messages": _conversation_messages(messages),
            "execution_history": slim_history,
            "decision_snapshots": _decision_snapshots(user_query, slim_history),
            "allowed_chunk_types": allowed_types,
            "policy": memory_policy,
            "extraction_requests": extraction_requests,
            "error": "",
        }
        try:
            from src.utils.agent_logger import log_event

            log_event(
                "learner.load",
                status="pending",
                history_steps=len(out["execution_history"]),
                user_query=out["user_query"],
            )
        except Exception:
            pass
        return out
    except Exception as e:
        logger.warning("load_session failed agent_id=%s", agent_id, exc_info=True)
        try:
            from src.utils.agent_logger import log_event

            log_event("learner.load", status="error", error=str(e))
        except Exception:
            pass
        return {"status": "error", "error": str(e), "chunks": []}
