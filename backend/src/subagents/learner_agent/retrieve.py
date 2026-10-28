"""Safe experience retrieval for the main agent hot path."""

from __future__ import annotations

import logging
from typing import Any

from src.subagents.learner_agent.config import EXPERIENCE_ENABLED, TOP_K
from src.subagents.learner_agent.keys import build_decision_state, build_retrieval_queries
from src.agent import kb
from src.agent.policy_schema import effective_memory_policy, memory_action_allowed

logger = logging.getLogger(__name__)


def retrieve_experiences(
    user_query: str,
    *,
    prior_task: str = "",
    prior_tool: str = "",
    execution_history: list[dict[str, Any]] | None = None,
    available_resources: set[tuple[str, str]] | None = None,
    uid: str | None = None,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """
    Return top-k experience chunks. Never raises — returns [] on any failure
    or when the experience system is disabled / empty.
    """
    if not EXPERIENCE_ENABLED:
        return []
    try:
        from src.utils.trace import current_ids, in_run, emit
        from src.agent.agent_core import AgentCore
        from api.db.repositories.agents import AgentRepository
        from api.db.repositories.preferences import PreferencesRepository

        if in_run():
            record = AgentRepository().get(current_ids()["agent_id"])
            agent = AgentCore(record) if record else None
            if not agent or agent.memory.user_id != uid:
                emit("memory.retrieve.denied", status="denied", error=PermissionError("memory_scope_denied"),
                      data={"scope": "USER"}, component="learner_retrieve")
                return []
            ceiling = ((PreferencesRepository().get(uid or "").get("agent") or {}).get("memory_policy_ceiling"))
            memory_policy = effective_memory_policy(agent.policy.memory, ceiling)
            policy = {**memory_policy, "version": agent.policy.version}
        else:
            policy = {"read": ["USER", "AGENT"], "write": ["USER"], "tenant_id": None}
        history = list(execution_history or [])
        if not history and (prior_task or prior_tool):
            history = [{"task": prior_task, "tool_name": prior_tool, "success": True}]
        decision = build_decision_state(user_query, history)
        stage = decision["decision_stage"]
        lane_types = {
            "entry": {"user_preference", "user_details", "tenant_details", "workflow", "resource", "anti_pattern"},
            "transition": {"user_preference", "user_details", "workflow", "resource", "anti_pattern"},
            "recovery": {"user_preference", "troubleshooting", "anti_pattern", "workflow", "resource"},
        }[stage]
        limit = top_k if top_k is not None else TOP_K
        merged: dict[str, dict[str, Any]] = {}
        for query in build_retrieval_queries(decision):
            for chunk in kb.search(uid or "", policy, query, top_k=limit, chunk_types=lane_types):
                metadata = chunk.get("metadata") or {}
                resource_name = str(metadata.get("resource_name") or "")
                resource_type = str(metadata.get("resource_type") or "")
                if resource_name and available_resources is not None and (resource_type, resource_name) not in available_resources:
                    continue
                chunk_stage = metadata.get("decision_stage") or "general"
                chunk["score"] = float(chunk.get("score") or 0) + (0.15 if chunk_stage in {stage, "general"} else -0.1)
                chunk_id = str(chunk.get("chunk_id") or "")
                if chunk_id not in merged or chunk["score"] > merged[chunk_id]["score"]:
                    merged[chunk_id] = chunk
        return sorted(merged.values(), key=lambda item: item["score"], reverse=True)[:limit]
    except Exception as exc:
        from src.utils.trace import in_run, emit

        if in_run():
            emit("memory.retrieve.end", status="error", error=exc, duration_ms=0,
                  data={"scope": "USER"}, component="learner_retrieve")
        logger.warning("retrieve_experiences failed (%s: %s)", type(exc).__name__, exc)
        return []


def format_experiences_for_prompt(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(none)"
    grouped: dict[str, list[str]] = {}
    for chunk in chunks:
        advice = (chunk.get("content") or chunk.get("advice") or "").strip()
        meta = chunk.get("metadata") or {}
        label = str(chunk.get("chunk_type") or "memory").replace("_", " ").title()
        stage = meta.get("decision_stage")
        grouped.setdefault(label, []).append(f"- {advice}" + (f" [stage={stage}]" if stage else ""))
    return "\n\n".join(f"{label}:\n" + "\n".join(items) for label, items in grouped.items())
