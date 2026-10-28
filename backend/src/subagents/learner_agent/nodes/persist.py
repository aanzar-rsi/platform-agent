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


def _contradicts(left: str, right: str) -> bool:
    def normalized(text: str) -> tuple[bool, str]:
        value = " ".join(text.strip().casefold().split()).rstrip(".")
        negated = value.startswith("do not ")
        return negated, value[7:] if negated else value

    left_negated, left_body = normalized(left)
    right_negated, right_body = normalized(right)
    return bool(left_body and left_body == right_body and left_negated != right_negated)


def _has_pending_requests(state: LearnerState) -> bool:
    return any(request.get("state") == "APPROVAL_PENDING"
               for request in (state.get("extraction_requests") or {}).values())


def _result(state: LearnerState, *, stored_count: int, fallback_status: str,
            fallback_error: str = "") -> dict:
    if _has_pending_requests(state):
        return {"status": "pending_confirmation", "stored_count": stored_count,
                "error": "awaiting_extraction_confirmation"}
    return {"status": fallback_status, "stored_count": stored_count, "error": fallback_error}


def persist_node(state: LearnerState) -> dict:
    if state.get("status") in ("skipped", "error"):
        _mark_requests(state, request_state="SKIPPED")
        return _result(state, stored_count=0, fallback_status=state.get("status") or "skipped",
                       fallback_error=state.get("error") or "")

    chunks = state.get("chunks") or []
    if not chunks:
        _mark_requests(state, request_state="SKIPPED")
        return _result(state, stored_count=0, fallback_status="skipped", fallback_error="nothing to store")

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
            metadata = dict(chunk.get("metadata") or {})
            metadata["evidence_id"] = chunk.get("id")
            evidence_id = str(chunk.get("id") or "")
            if kb.evidence_exists(uid, policy, evidence_id):
                continue
            existing = kb.find_user_memory(
                uid, policy, chunk_type=chunk_type,
                semantic_key=str(chunk.get("semantic_key") or metadata.get("semantic_key") or ""),
            )
            content = str(chunk["advice"])
            if existing and existing.get("content", "").strip().casefold() == content.strip().casefold():
                kb.reinforce(uid, policy, existing["chunk_id"], evidence_id=evidence_id)
            else:
                kb.write(
                    uid, policy, content, search_text=chunk.get("embed_text"),
                    chunk_type=chunk_type, scope="USER",
                    chunk_id=(existing.get("chunk_id") if existing and not _contradicts(existing["content"], content)
                              else None),
                    conversation_id=state.get("agent_id"), metadata=metadata,
                    memory_weight=float(chunk.get("memory_weight", 0.5)),
                    sensitivity=str(chunk.get("sensitivity") or "INTERNAL"),
                )
            n += 1
        already_processed = bool(chunks) and n == 0
        if n <= 0:
            _mark_requests(state, request_state="COMPLETED")
            return _result(state, stored_count=0,
                           fallback_status="learned" if already_processed else "skipped")
        try:
            from src.utils.agent_logger import log_event

            log_event("learner.persist", status="learned", stored_count=n)
        except Exception:
            pass
        _mark_requests(state, request_state="COMPLETED")
        return _result(state, stored_count=n, fallback_status="learned")
    except Exception as e:
        logger.warning("persist failed", exc_info=True)
        try:
            from src.utils.agent_logger import log_event

            log_event("learner.persist", status="error", error=str(e), stored_count=0)
        except Exception:
            pass
        _mark_requests(state, request_state="SKIPPED")
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


def _mark_requests(state: LearnerState, *, request_state: str) -> None:
    requests = state.get("extraction_requests") or {}
    if not requests:
        _mark_request(state, request_state=request_state)
        return
    for chunk_type, request in requests.items():
        if request.get("state") != "APPROVED" or chunk_type not in (state.get("allowed_chunk_types") or []):
            continue
        try:
            from api.db.repositories.memory_extractions import MemoryExtractionRepository

            MemoryExtractionRepository().mark_final(request.get("request_id") or "", state=request_state)
        except Exception:
            logger.warning("failed marking extraction request type=%s", chunk_type, exc_info=True)
