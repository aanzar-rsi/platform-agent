"""Governed LLM extraction of durable memory candidates."""

from __future__ import annotations

import json
import logging
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.subagents.learner_agent.state import LearnerState
from src.models.llm_client import call_llm
from src.prompts.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"
_CHUNK_TYPES = {
    "resource", "user_preference", "user_details", "tenant_details", "workflow",
    "troubleshooting", "anti_pattern",
}
_DECISION_STAGES = {"entry", "transition", "recovery", "general"}
_SENSITIVITIES = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}
_EVIDENCE_KINDS = {"explicit_statement", "user_correction", "observed_success", "observed_failure", "repeated_pattern"}
_SCALAR_VALUES = {
    "preference_kind": {"response_style", "communication", "workflow", "technology", "constraint"},
    "detail_kind": {"interest", "project", "skill", "experience", "recurring_topic", "organization", "process"},
    "resource_domain": {"armory", "child_agent"},
    "resource_type": {"tool", "subagent", "mcp_server", "child_agent"},
    "guidance_kind": {"selection", "usage", "sequencing", "limitation"},
    "workflow_kind": {"overview", "transition", "orchestration", "checklist"},
    "failure_kind": {"empty_result", "timeout", "validation", "dependency", "permission", "unexpected_result"},
    "anti_pattern_kind": {"user_correction", "failed_approach", "security", "duplication", "overengineering"},
}
_SECRET = re.compile(
    r"(?i)(?:api[_-]?key|password|secret|access[_-]?token|refresh[_-]?token|authorization)\s*[:=]\s*\S+"
)
_PROTECTED = re.compile(
    r"(?i)\b(race|ethnicity|religion|sexual orientation|medical diagnosis|disability|political affiliation)\b"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json_payload(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {"chunks": []}
    # strip optional markdown fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if fence:
        raw = fence.group(1).strip()
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {"chunks": data}
    except json.JSONDecodeError:
        # try first {...} blob
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            try:
                data = json.loads(raw[start : end + 1])
                if isinstance(data, dict):
                    return data
            except json.JSONDecodeError:
                pass
    return {"chunks": []}


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:24]
    return f"{prefix}_{digest}"


def _clean_metadata(raw: dict[str, Any], chunk_type: str) -> dict[str, Any]:
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    stage = str(metadata.get("decision_stage") or "general").strip().lower()
    cleaned: dict[str, Any] = {
        "semantic_key": str(raw.get("semantic_key") or metadata.get("semantic_key") or "").strip().lower()[:200],
        "evidence_kind": str(raw.get("evidence_kind") or metadata.get("evidence_kind") or "observed_success").strip().lower()[:60],
        "decision_stage": stage if stage in _DECISION_STAGES else "general",
        "intent": str(metadata.get("intent") or "").strip()[:120],
        "current_subgoal": str(metadata.get("current_subgoal") or "").strip()[:300],
    }
    scalar_fields = {
        "user_preference": ("preference_kind",),
        "user_details": ("detail_kind",),
        "tenant_details": ("detail_kind",),
        "resource": ("resource_domain", "resource_type", "resource_name", "guidance_kind"),
        "workflow": ("workflow_kind",),
        "troubleshooting": ("failure_kind", "resource_type", "resource_name"),
        "anti_pattern": ("anti_pattern_kind",),
    }
    for field in scalar_fields.get(chunk_type, ()):
        value = str(metadata.get(field) or "").strip().lower()[:120]
        if value and field in _SCALAR_VALUES and value not in _SCALAR_VALUES[field]:
            return {}
        cleaned[field] = value
    for field in ("preconditions", "next_action", "retrieval_cues"):
        value = metadata.get(field)
        if isinstance(value, list):
            cleaned[field] = value[:8]
        elif isinstance(value, dict):
            cleaned[field] = value
    return {key: value for key, value in cleaned.items() if value not in ("", [], {})}


def _normalize_chunk(
    raw: dict[str, Any],
    *,
    uid: str,
    agent_id: str,
    user_query: str,
    checkpoint_id: str,
    allowed_types: set[str],
    observed_resources: set[tuple[str, str]],
) -> dict[str, Any] | None:
    chunk_type = str(raw.get("chunk_type") or raw.get("type") or "").strip().lower()
    content = str(raw.get("content") or raw.get("advice") or "").strip()
    if chunk_type not in _CHUNK_TYPES or chunk_type not in allowed_types or not content:
        return None
    if _SECRET.search(content) or _PROTECTED.search(content):
        return None
    metadata = _clean_metadata(raw, chunk_type)
    semantic_key = str(metadata.get("semantic_key") or "").strip()
    if not semantic_key or not re.fullmatch(r"[a-z0-9]+(?:[._-][a-z0-9]+)*", semantic_key):
        return None
    if metadata.get("evidence_kind") not in _EVIDENCE_KINDS:
        return None
    serialized = json.dumps(raw, sort_keys=True, default=str)
    if _SECRET.search(serialized) or _PROTECTED.search(serialized):
        return None
    if chunk_type == "resource":
        resource_type = str(metadata.get("resource_type") or "")
        resource_name = str(metadata.get("resource_name") or "")
        if not resource_type or not resource_name or (resource_type, resource_name) not in observed_resources:
            return None
    try:
        weight = float(raw.get("memory_weight", 0.5))
    except (TypeError, ValueError):
        return None
    if not 0 <= weight <= 1:
        return None
    sensitivity = str(raw.get("sensitivity") or "INTERNAL").strip().upper()
    if sensitivity not in _SENSITIVITIES:
        return None
    cues = metadata.get("retrieval_cues") if isinstance(metadata.get("retrieval_cues"), list) else []
    search_text = str(raw.get("search_text") or "").strip()
    if not search_text:
        search_text = " | ".join([user_query, semantic_key, *[str(cue) for cue in cues]])
    evidence_id = _stable_id("evidence", uid, agent_id, checkpoint_id, semantic_key)
    return {
        "id": evidence_id,
        "type": chunk_type,
        "chunk_type": chunk_type,
        "semantic_key": semantic_key,
        "embed_text": search_text[:3000],
        "advice": content[:4000],
        "memory_weight": weight,
        "sensitivity": sensitivity,
        "metadata": {
            **metadata,
            "uid": uid,
            "source_agent_id": agent_id,
            "user_query": user_query,
            "source_checkpoint_id": checkpoint_id,
            "outcome": str(raw.get("outcome") or "success").strip().lower()[:40],
            "created_at": _utc_now(),
        },
    }


def extract_chunks_node(state: LearnerState) -> dict:
    if state.get("status") in ("skipped", "error"):
        return {"chunks": state.get("chunks") or []}

    history = state.get("execution_history") or []
    messages = state.get("conversation_messages") or []
    if not history and not messages:
        return {"status": "skipped", "chunks": [], "error": "empty learning evidence"}

    try:
        system_prompt, user_prompt = load_prompt(
            "extract_memory_chunks",
            {
                "user_query": state.get("user_query") or "",
                "messages_summary": state.get("messages_summary") or "",
                "conversation_messages": messages,
                "execution_history": history,
                "decision_snapshots": state.get("decision_snapshots") or [],
                "allowed_chunk_types": state.get("allowed_chunk_types") or [],
            },
            prompts_dir=_PROMPTS_DIR,
        )
        response = call_llm(
            user_prompt.strip(),
            system_prompt=system_prompt.strip() or None,
            temperature=0.2,
            output_type="text",
        )
        if not isinstance(response, str):
            response = json.dumps(response)

        payload = _parse_json_payload(response)
        raw_chunks = payload.get("chunks") or []
        if not isinstance(raw_chunks, list):
            raw_chunks = []

        uid = state.get("uid") or ""
        agent_id = state.get("agent_id") or ""
        user_query = state.get("user_query") or ""
        chunks: list[dict[str, Any]] = []
        allowed_types = set(state.get("allowed_chunk_types") or [])
        observed_resources = {
            (str(step.get("resource_type") or ""), str(step.get("resource_name") or step.get("tool_name") or ""))
            for step in history if step.get("resource_name") or step.get("tool_name")
        }
        observed_resources |= {
            ("mcp_server", name) for resource_type, name in observed_resources
            if resource_type == "tool" and name.startswith("mcp_")
        }
        for raw in raw_chunks:
            if not isinstance(raw, dict):
                continue
            normalized = _normalize_chunk(
                raw,
                uid=uid,
                agent_id=agent_id,
                user_query=user_query,
                checkpoint_id=state.get("branch_checkpoint_id") or agent_id,
                allowed_types=allowed_types,
                observed_resources=observed_resources,
            )
            if normalized:
                chunks.append(normalized)

        if not chunks:
            try:
                from src.utils.agent_logger import log_event

                log_event("learner.extract", status="skipped", chunk_count=0)
            except Exception:
                pass
            return {"status": "skipped", "chunks": [], "error": "no chunks extracted"}
        try:
            from src.utils.agent_logger import log_event

            log_event(
                "learner.extract",
                status="pending",
                chunk_count=len(chunks),
                chunk_ids=[c.get("id") for c in chunks],
            )
        except Exception:
            pass
        return {"chunks": chunks, "status": "pending", "error": ""}
    except Exception as e:
        logger.warning("extract_chunks failed", exc_info=True)
        try:
            from src.utils.agent_logger import log_event

            log_event("learner.extract", status="error", error=str(e))
        except Exception:
            pass
        return {"status": "error", "error": str(e), "chunks": []}
