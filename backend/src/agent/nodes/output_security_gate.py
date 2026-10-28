"""Validate, sanitize, and commit all new executor output."""

from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from src.agent.memory import record_execution
from src.utils.text_truncate import truncate_for_aimessage

_REDACTED = "[REDACTED]"
_SENSITIVE_KEYS = {
    "api_key", "apikey", "authorization", "credential", "credentials", "password",
    "refresh_token", "secret", "token", "access_token",
}
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_CREDENTIAL = re.compile(
    r"(?i)\b(api[_-]?key|password|secret|access[_-]?token|refresh[_-]?token|authorization)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
_METADATA_FIELDS = {
    "armory_result": {"resource_type", "resource_name", "arguments", "structured"},
    "child_spawn": {"child_agent_id", "tool_args", "requested_policy"},
    "child_collection": {"child_agent_id"},
    "human_input": {"question", "input_kind", "resume_context"},
    "executor_error": {"executor_source"},
}


def sanitize_value(value: Any, *, _depth: int = 0, _seen: set[int] | None = None) -> Any:
    """Return deterministic, serializable data safe for checkpoints and prompts."""
    if _depth > 20:
        return "[MAX_DEPTH]"
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        text = _CONTROL_CHARS.sub("", value)
        return _CREDENTIAL.sub(lambda match: f"{match.group(1)}{match.group(2)}{_REDACTED}", text)

    seen = _seen if _seen is not None else set()
    identity = id(value)
    if identity in seen:
        return "[CYCLE]"
    seen.add(identity)
    try:
        if isinstance(value, dict):
            result = {}
            for raw_key, raw_value in value.items():
                key = str(raw_key)
                result[key] = (_REDACTED if key.strip().lower() in _SENSITIVE_KEYS
                               else sanitize_value(raw_value, _depth=_depth + 1, _seen=seen))
            return result
        if isinstance(value, (list, tuple, set, frozenset)):
            items = value if not isinstance(value, (set, frozenset)) else sorted(value, key=str)
            return [sanitize_value(item, _depth=_depth + 1, _seen=seen) for item in items]
        return sanitize_value(str(value), _depth=_depth + 1, _seen=seen)
    finally:
        seen.discard(identity)


def sanitize_executor_output(envelope: dict) -> dict:
    """Pre-sanitize an envelope before it crosses a checkpoint boundary."""
    return sanitize_value(envelope) if isinstance(envelope, dict) else {}


def _normalize_result(raw: Any, source: str) -> dict:
    if not isinstance(raw, dict):
        raise ValueError("result must be an object")
    kind = str(raw.get("kind") or "").strip()
    if kind not in _METADATA_FIELDS:
        raise ValueError(f"unsupported result kind: {kind or 'missing'}")
    if "value" not in raw:
        raise ValueError(f"{kind} result is missing value")
    if not isinstance(raw.get("success"), bool):
        raise ValueError(f"{kind} success must be a boolean")
    name = str(raw.get("name") or "").strip()
    task = str(raw.get("task") or "").strip()
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}
    metadata = {key: sanitize_value(metadata[key]) for key in _METADATA_FIELDS[kind] if key in metadata}
    if kind == "armory_result":
        if metadata.get("resource_type") not in {"tool", "subagent"} or not name:
            raise ValueError("armory result requires resource_type and name")
    if kind in {"child_spawn", "child_collection"} and raw["success"] and not metadata.get("child_agent_id"):
        raise ValueError(f"{kind} requires child_agent_id")
    return {
        "kind": kind,
        "value": sanitize_value(raw["value"]),
        "success": raw["success"],
        "status": str(raw.get("status") or ("completed" if raw["success"] else "failed")),
        "name": name,
        "task": task,
        "description": str(raw.get("description") or task or name or kind).strip(),
        "metadata": metadata,
        "source": source,
    }


def _history_upsert(history: list[dict], entry: dict) -> list[dict]:
    for index, existing in enumerate(history):
        if existing.get("key") == entry["key"]:
            history[index] = entry
            return history
    history.append(entry)
    return history


def _memory_key(result: dict, action_id: str, index: int, history: list[dict], step_id: str = "",
                result_index: int = 0) -> str:
    child_id = result["metadata"].get("child_agent_id")
    if result["kind"] == "child_collection" and child_id:
        existing = next((row for row in history if row.get("child_agent_id") == child_id), None)
        if existing and existing.get("key"):
            return existing["key"]
    if result["kind"] == "child_spawn" and child_id:
        base = f"{action_id}:step:{step_id}" if step_id else action_id
        return f"{base}:child:{child_id}"
    if step_id:
        base = f"{action_id}:step:{step_id}"
        return base if result_index == 0 else f"{base}:result:{result_index + 1}"
    return action_id if index == 0 else f"{action_id}:result:{index + 1}"


def _trusted_message(result: dict, key: str):
    preview = truncate_for_aimessage(result["value"])
    kind = result["kind"]
    if kind == "human_input":
        return HumanMessage(content=preview, additional_kwargs={
            "ui_hidden": True,
            "ui_step": {"type": "reasoning", "content": f"User response: {preview}"},
        })
    if kind == "armory_result":
        ui_type = "subagent" if result["metadata"]["resource_type"] == "subagent" else "tool"
        return AIMessage(content=f"armory.{result['metadata']['resource_type']}.{result['name']} result: {preview}",
                         additional_kwargs={"ui_hidden": True, "ui_step": {
                             "type": ui_type, ui_type: {"id": key, "name": result["name"],
                                                        "result": preview, "success": result["success"]}}})
    if kind in {"child_spawn", "child_collection"}:
        child_id = result["metadata"].get("child_agent_id")
        return AIMessage(content=f"Child {child_id or 'spawn'}: {preview}", additional_kwargs={
            "ui_hidden": True, "ui_step": {"type": "child_agent", "child_agent": {
                "id": child_id or key, "child_agent_id": child_id, "agent_name": "child_agent",
                "result": preview, "success": result["success"], "status": result["status"], "progress": [],
            }},
        })
    return AIMessage(content=preview, additional_kwargs={"ui_hidden": True})


def _events_for(result: dict, *, action_id: str, step_id: str = "",
                sequence: int | None = None) -> list[dict]:
    kind = result["kind"]
    payload = {"task": result["task"], "result": result["value"], "success": result["success"]}
    if kind == "armory_result":
        resource_type = result["metadata"]["resource_type"]
        event = "subagent.finished" if resource_type == "subagent" else "tool.finished"
        payload.update({"agent_name" if resource_type == "subagent" else "tool_name": result["name"]})
        if resource_type == "tool":
            payload["tool_args"] = result["metadata"].get("arguments") or {}
    elif kind in {"child_spawn", "child_collection"}:
        event = "child.started" if result["status"] == "running" else "child.finished"
        payload.update(child_agent_id=result["metadata"].get("child_agent_id"), agent_name="child_agent")
    else:
        event = "human.input" if kind == "human_input" else "executor.failed"
    payload["action_id"] = action_id
    events = [{"kind": event, "payload": payload}]
    if step_id:
        events.append({"kind": "plan.step.finished", "payload": {
            "id": step_id, "sequence": sequence, "action": kind,
            "success": result["success"], "result": result["value"],
        }})
    return events


def _invalid_result(message: str, source: str) -> dict:
    return {
        "kind": "executor_error", "value": {"error": message}, "success": False,
        "status": "failed", "name": "output_security_gate", "task": "",
        "description": "Rejected malformed executor output",
        "metadata": {"executor_source": source}, "source": source,
    }


def output_security_gate_node(state: dict, config=None) -> dict:
    envelope = state.get("executor_output")
    source = str((envelope or {}).get("source") or "unknown") if isinstance(envelope, dict) else "unknown"
    action_id = str((envelope or {}).get("action_id") or "").strip() if isinstance(envelope, dict) else ""
    planned = source in {"planned_phase", "dispatch_batch"}
    phase = int((envelope or {}).get("phase") or 0) if planned else 0
    raw_items: list[tuple[Any, str, str, int]] = []

    try:
        if not isinstance(envelope, dict) or not action_id:
            raise ValueError("executor output requires an action_id")
        if planned:
            steps = envelope.get("steps")
            if not isinstance(steps, list) or not steps:
                raise ValueError("planned phase requires ordered steps")
            for step in steps:
                if not isinstance(step, dict) or not isinstance(step.get("results"), list):
                    raise ValueError("planned step requires results")
                for result_index, result in enumerate(step["results"]):
                    step_id = str(step.get("id") or "")
                    raw_items.append((result, step_id, str(step.get("action_id") or ""), result_index))
        else:
            results = envelope.get("results")
            if not isinstance(results, list) or not results:
                raise ValueError("executor output requires results")
            raw_items = [(result, "", action_id, index) for index, result in enumerate(results)]
        normalized = [(_normalize_result(raw, source), step_id, step_action_id, result_index)
                      for raw, step_id, step_action_id, result_index in raw_items]
    except (TypeError, ValueError) as exc:
        normalized = [(_invalid_result(str(exc), source), "", action_id, 0)]

    history = list(state.get("execution_history") or [])
    memory = dict(state.get("execution_memory") or {})
    context = state.get("context_memory")
    messages = []
    events = []
    failed = False
    resume_context = next((result["metadata"].get("resume_context") for result, _, _, _ in normalized
                           if result["kind"] == "human_input"), None)
    for index, (result, step_id, step_action_id, result_index) in enumerate(normalized):
        if (result["kind"] == "human_input" and not str(result["value"]).strip()
                and result["metadata"].get("input_kind") == "context_pause"):
            continue
        key = _memory_key(result, action_id or "output_gate_error", index, history, step_id, result_index)
        memory, context, entry = record_execution(
            memory, context, key=key, value=result["value"], description=result["description"],
            entry_type={"armory_result": "armory", "child_spawn": "child_agent",
                        "child_collection": "child_agent"}.get(result["kind"], result["kind"]),
            name=result["name"], task=result["task"], success=result["success"],
            metadata={**result["metadata"], "status": result["status"], "source": result["source"],
                      "action_id": action_id, **({"phase": phase, "step_id": step_id} if step_id else {})},
        )
        if result["kind"] == "armory_result":
            entry.update(resource_type=result["metadata"]["resource_type"],
                         resource_name=result["name"],
                         resource=f"armory.{result['metadata']['resource_type']}.{result['name']}",
                         arguments=result["metadata"].get("arguments") or {},
                         structured=result["metadata"].get("structured"))
            memory[key] = entry
        elif result["kind"] in {"child_spawn", "child_collection"}:
            if result["kind"] == "child_collection":
                previous = next((row for row in history if row.get("key") == key), {})
                entry.update({field: previous[field] for field in ("tool_args", "requested_policy") if field in previous})
            entry.update(agent_name="child_agent",
                          child_agent_id=result["metadata"].get("child_agent_id"),
                          **({
                              "tool_args": result["metadata"].get("tool_args") or {},
                              "requested_policy": result["metadata"].get("requested_policy") or {},
                          } if result["kind"] == "child_spawn" else {}))
            memory[key] = entry
        history = _history_upsert(history, entry)
        messages.append(_trusted_message(result, key))
        result_action_id = step_action_id or (
            f"{action_id}:step:{step_id}" if step_id and ":phase:" not in action_id else action_id
        )
        events.extend(_events_for(result, action_id=result_action_id, step_id=step_id,
                                  sequence=phase or None))
        failed = failed or not result["success"]

        if result["kind"] == "child_collection" and result["metadata"].get("child_agent_id"):
            values = (config or {}).get("configurable") or {}
            if values.get("agent_id") and values.get("execution_id"):
                from src.agent.agent_core import child_runner
                child_runner.repository.append_message(
                    values["agent_id"], values["execution_id"], str(result["value"]),
                    sender_type="agent", sender_id=result["metadata"]["child_agent_id"],
                    child_agent_id=result["metadata"]["child_agent_id"], visible_to_user=False,
                )

    update = {
        "executor_output": {}, "execution_history": history, "execution_memory": memory,
        "context_memory": context, "messages": messages, "output_events": events,
        "next_step": {}, "dispatch_target": "",
    }
    if planned:
        phase_index = int(state.get("planned_phase_index") or 0)
        events.append({"kind": "plan.phase.finished", "payload": {
            "kind": "phase.finished", "sequence": phase, "failed": failed,
            "step_ids": [str(step.get("id")) for step in envelope.get("steps", [])],
        }})
        next_phase_index = phase_index if resume_context == "context_selector" else phase_index + 1
        update.update(step_results=[], planned_phase_index=next_phase_index)
        if failed or (next_phase_index >= len(state.get("planned_phases") or [])
                      and resume_context != "context_selector"):
            update.update(planned_phases=[], current_task=(
                "collect_child" if not failed and any(row.get("status") == "running" for row in history) else ""
            ))

    if resume_context == "context_selector" and state.get("pending_context_selection"):
        update.update(next_step=state["pending_context_selection"])
    return update
