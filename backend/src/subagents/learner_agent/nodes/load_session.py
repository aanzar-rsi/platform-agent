"""Load chat trajectory from the main agent checkpointer."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import BaseMessage

from src.subagents.learner_agent.state import LearnerState
from api.db.repositories.agents import AgentRepository
from api.db.repositories.preferences import PreferencesRepository
from src.agent.agent_core import AgentCore
from src.agent.policy_schema import effective_memory_policy, memory_requires_extract_confirmation

logger = logging.getLogger(__name__)


def _message_line(msg: Any) -> str:
    role = getattr(msg, "type", None) or "unknown"
    content = getattr(msg, "content", "")
    if not isinstance(content, str):
        content = str(content)
    if len(content) > 500:
        content = content[:500] + "…"
    return f"{role}: {content}"


def _latest_human(messages: list[Any]) -> str:
    for msg in reversed(messages):
        if getattr(msg, "type", None) == "human":
            content = getattr(msg, "content", "")
            return content if isinstance(content, str) else str(content)
    return ""


def _slim_history(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slim: list[dict[str, Any]] = []
    for entry in history:
        result = entry.get("result")
        result_preview = result
        if isinstance(result, str) and len(result) > 800:
            result_preview = result[:800] + "…"
        elif isinstance(result, dict):
            # keep structure but cap error/body strings
            result_preview = {}
            for k, v in list(result.items())[:12]:
                if isinstance(v, str) and len(v) > 400:
                    result_preview[k] = v[:400] + "…"
                else:
                    result_preview[k] = v
        slim.append(
            {
                "type": entry.get("type"),
                "tool_name": entry.get("tool_name") or entry.get("agent_name"),
                "tool_args": entry.get("tool_args") or {},
                "task": entry.get("task") or "",
                "key": entry.get("key"),
                "result": result_preview,
            }
        )
    return slim


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
        requires_confirm = memory_requires_extract_confirmation(memory_policy, chunk_type="workflow")
        extraction_request_id = ""
        if requires_confirm and checkpoint:
            from api.db.repositories.memory_extractions import MemoryExtractionRepository

            repo = MemoryExtractionRepository()
            pending = repo.create_pending(owner_id=owner_id, agent_id=agent_id,
                                          checkpoint_id=checkpoint, chunk_type="workflow")
            if pending.get("state") == "APPROVAL_PENDING":
                return {
                    "status": "skipped",
                    "error": "awaiting_extraction_confirmation",
                    "chunks": [],
                    "execution_history": _slim_history(history) if isinstance(history, list) else [],
                    "user_query": _latest_human(messages) if messages else "",
                    "messages_summary": "\n".join(_message_line(m) for m in messages[-20:]),
                    "policy": memory_policy,
                    "extraction_request_id": pending.get("request_id") or "",
                }
            if pending.get("state") == "REJECTED":
                return {
                    "status": "skipped",
                    "error": "extraction_rejected",
                    "chunks": [],
                    "policy": memory_policy,
                    "extraction_request_id": pending.get("request_id") or "",
                }
            extraction_request_id = pending.get("request_id") or ""
        if not isinstance(history, list):
            history = []
        if not history:
            return {
                "status": "skipped",
                "error": "no tool steps to learn from",
                "chunks": [],
                "execution_history": [],
                "user_query": _latest_human(messages) if messages else "",
                "messages_summary": "\n".join(_message_line(m) for m in messages[-20:]),
            }

        msg_lines = [_message_line(m) for m in messages[-20:] if isinstance(m, BaseMessage) or hasattr(m, "content")]
        out = {
            "status": "pending",
            "user_query": _latest_human(messages),
            "messages_summary": "\n".join(msg_lines) or "(none)",
            "execution_history": _slim_history(history),
            "policy": memory_policy,
            "extraction_request_id": extraction_request_id,
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
