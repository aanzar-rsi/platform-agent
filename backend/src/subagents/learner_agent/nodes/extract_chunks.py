"""LLM extraction of tool-based experience chunks."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.subagents.learner_agent.keys import build_embed_text
from src.subagents.learner_agent.state import LearnerState
from src.models.llm_client import call_llm
from src.prompts.prompt_loader import load_prompt
from src.agent.nodes.output_security_gate import sanitize_value

logger = logging.getLogger(__name__)

_PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


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


def _normalize_chunk(
    raw: dict[str, Any],
    *,
    uid: str,
    agent_id: str,
    user_query: str,
    step_index: int = 0,
    history: list[dict[str, Any]] | None = None,
    checkpoint_id: str = "",
    allowed_types: set[str] | None = None,
    observed_resources: set[tuple[str, str]] | None = None,
) -> dict[str, Any] | None:
    history = history or []
    if raw.get("content"):
        content = str(raw["content"]).strip()
        if not content or sanitize_value(content) != content:
            return None
        chunk_type = str(raw.get("chunk_type") or "")
        if allowed_types is not None and chunk_type not in allowed_types:
            return None
        metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
        resource_type = str(metadata.get("resource_type") or "")
        resource_name = str(metadata.get("resource_name") or "")
        if chunk_type == "resource":
            observed = observed_resources or set()
            if resource_type == "mcp_server":
                allowed = ("tool", resource_name) in observed and resource_name.startswith("mcp_")
            else:
                allowed = (resource_type, resource_name) in observed
            if not allowed:
                return None
        return {"id": f"exp_{uuid.uuid4().hex[:16]}", "chunk_type": chunk_type,
                "advice": content, "embed_text": build_embed_text(user_query),
                "metadata": {**metadata, "uid": uid, "source_agent_id": agent_id,
                             "checkpoint_id": checkpoint_id, "semantic_key": raw.get("semantic_key")}}

    advice = (raw.get("advice") or "").strip()
    if not advice:
        return None

    prior_task = (raw.get("prior_task") or "").strip()
    prior_tool = (raw.get("prior_tool") or "").strip()
    observed_tool = (raw.get("observed_tool") or "").strip()

    # Prefer structured prior from trajectory when LLM omits them
    if step_index == 0:
        prior_task = ""
        prior_tool = ""
    elif (not prior_task and not prior_tool) and step_index > 0 and step_index - 1 < len(history):
        prev = history[step_index - 1]
        prior_task = (prev.get("task") or "").strip()
        prior_tool = (prev.get("tool_name") or "").strip()

    if not observed_tool and step_index < len(history):
        observed_tool = (history[step_index].get("tool_name") or "").strip()

    embed_text = build_embed_text(
        user_query,
        prior_task=prior_task,
        prior_tool=prior_tool,
    )
    return {
        "id": f"exp_{uuid.uuid4().hex[:16]}",
        "type": "tool",
        "chunk_type": "workflow",
        "embed_text": embed_text,
        "advice": advice,
        "metadata": {
            "uid": uid,
            "source_agent_id": agent_id,
            "user_query": user_query,
            "prior_task": prior_task,
            "prior_tool": prior_tool,
            "observed_tool": observed_tool,
            "tool_args": raw.get("tool_args") if isinstance(raw.get("tool_args"), dict) else {},
            "result_summary": (raw.get("result_summary") or "")[:1000],
            "outcome": (raw.get("outcome") or "success").strip().lower(),
            "learning": (raw.get("learning") or "")[:1000],
            "created_at": _utc_now(),
        },
    }


def extract_chunks_node(state: LearnerState) -> dict:
    if state.get("status") in ("skipped", "error"):
        return {"chunks": state.get("chunks") or []}

    history = state.get("execution_history") or []
    if not history:
        return {"status": "skipped", "chunks": [], "error": "empty execution_history"}

    try:
        system_prompt, user_prompt = load_prompt(
            "extract_tool_chunks",
            {
                "user_query": state.get("user_query") or "",
                "messages_summary": state.get("messages_summary") or "",
                "execution_history": history,
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
        observed = {(str(item.get("resource_type") or ""), str(item.get("resource_name") or ""))
                    for item in history if isinstance(item, dict) and item.get("resource_name")}
        for i, raw in enumerate(raw_chunks):
            if not isinstance(raw, dict):
                continue
            # Map by order when possible; fall back to sequential index
            step_index = i if i < len(history) else min(i, len(history) - 1)
            # If observed_tool matches a history entry, prefer that index
            obs = (raw.get("observed_tool") or "").strip()
            if obs:
                for j, step in enumerate(history):
                    if (step.get("tool_name") or "") == obs:
                        step_index = j
                        break
            normalized = _normalize_chunk(
                raw,
                uid=uid,
                agent_id=agent_id,
                user_query=user_query,
                step_index=step_index,
                history=history,
                checkpoint_id=str(state.get("branch_checkpoint_id") or ""),
                allowed_types=set(state.get("allowed_chunk_types") or ["workflow"]),
                observed_resources=observed,
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
