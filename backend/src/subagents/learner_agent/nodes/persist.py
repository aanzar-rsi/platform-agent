"""Persist extracted chunks into the experience store."""

from __future__ import annotations

import logging

from src.subagents.learner_agent.state import LearnerState
from src.agent import kb
from src.agent.agent_core import AgentCore
from api.db.repositories.agents import AgentRepository
from api.db.repositories.preferences import PreferencesRepository
from src.agent.policy_schema import effective_memory_policy, memory_action_allowed
from src.utils.trace import current_ids

logger = logging.getLogger(__name__)


def persist_node(state: LearnerState) -> dict:
    if state.get("status") in ("skipped", "error"):
        _mark_request(state, request_state="SKIPPED")
        return {"stored_count": 0}

    chunks = state.get("chunks") or []
    if not chunks:
        _mark_request(state, request_state="SKIPPED")
        return {"status": "skipped", "stored_count": 0, "error": "nothing to store"}

    try:
        uid = state.get("uid") or ""
        if not uid:
            raise PermissionError("memory_identity_denied")
        agent_id = current_ids().get("agent_id")
        record = AgentRepository().get(agent_id) if agent_id else None
        policy = AgentCore(record).policy.memory if record else {"read": ["USER"], "write": ["USER"], "tenant_id": None}
        if record:
            user_ceiling = ((PreferencesRepository().get(uid).get("agent") or {}).get("memory_policy_ceiling"))
            policy = effective_memory_policy(policy, user_ceiling)
        n = 0
        for chunk in chunks:
            if (chunk.get("metadata") or {}).get("uid") != uid:
                raise PermissionError("memory_identity_denied")
            chunk_type = str(chunk.get("chunk_type") or "workflow")
            if not memory_action_allowed(policy, action="write", scope="USER", chunk_type=chunk_type):
                raise PermissionError("memory_scope_denied")
            kb.write(uid, policy, str(chunk["advice"]), search_text=chunk.get("embed_text"),
                     chunk_type=chunk_type, scope="USER", source_id=chunk.get("id"),
                     conversation_id=state.get("agent_id"), metadata={
                         "observed_tool": (chunk.get("metadata") or {}).get("observed_tool") or "",
                         "prior_tool": (chunk.get("metadata") or {}).get("prior_tool") or "",
                         "outcome": (chunk.get("metadata") or {}).get("outcome") or "unknown",
                     })
            n += 1
        if n <= 0:
            try:
                from src.utils.agent_logger import log_event

                log_event(
                    "learner.persist",
                    status="error",
                    stored_count=0,
                    error="failed to embed/store chunks",
                )
            except Exception:
                pass
            return {
                "status": "error",
                "stored_count": 0,
                "error": "failed to embed/store chunks",
            }
        try:
            from src.utils.agent_logger import log_event

            log_event("learner.persist", status="learned", stored_count=n)
        except Exception:
            pass
        _mark_request(state, request_state="COMPLETED")
        return {"status": "learned", "stored_count": n, "error": ""}
    except Exception as e:
        logger.warning("persist failed", exc_info=True)
        try:
            from src.utils.agent_logger import log_event

            log_event("learner.persist", status="error", error=str(e), stored_count=0)
        except Exception:
            pass
        _mark_request(state, request_state="SKIPPED")
        return {"status": "error", "stored_count": 0, "error": str(e)}


def _mark_request(state: LearnerState, *, request_state: str) -> None:
    request_id = state.get("extraction_request_id")
    if not request_id:
        return
    try:
        from api.db.repositories.memory_extractions import MemoryExtractionRepository

        MemoryExtractionRepository().mark_final(request_id, state=request_state)
    except Exception:
        logger.warning("failed marking extraction request state=%s id=%s", request_state, request_id, exc_info=True)
