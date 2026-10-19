"""Safe experience retrieval for the main agent hot path."""

from __future__ import annotations

import logging
from typing import Any

from src.subagents.learner_agent.config import EXPERIENCE_ENABLED, TOP_K
from src.subagents.learner_agent.keys import build_embed_text
from src.agent import kb
from src.agent.policy_schema import effective_memory_policy, memory_action_allowed

logger = logging.getLogger(__name__)


def retrieve_experiences(
    user_query: str,
    *,
    prior_task: str = "",
    prior_tool: str = "",
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
            if not memory_action_allowed(memory_policy, action="read", scope="USER", chunk_type="workflow"):
                return []
            policy = {**memory_policy, "version": agent.policy.version}
        else:
            policy = {"read": ["USER", "AGENT"], "write": ["USER"], "tenant_id": None}
        key = build_embed_text(
            user_query,
            prior_task=prior_task or "",
            prior_tool=prior_tool or "",
        )
        return kb.search(uid or "", policy, key, top_k=top_k if top_k is not None else TOP_K)
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
    lines: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        advice = (chunk.get("content") or chunk.get("advice") or "").strip()
        meta = chunk.get("metadata") or {}
        outcome = meta.get("outcome") or ""
        tool = meta.get("observed_tool") or ""
        score = chunk.get("score")
        header = f"{i}."
        if tool:
            header += f" [tool={tool}"
            if outcome:
                header += f", outcome={outcome}"
            header += "]"
        if isinstance(score, (int, float)):
            header += f" (sim={score:.3f})"
        lines.append(f"{header}\n{advice}")
    return "\n\n".join(lines)
