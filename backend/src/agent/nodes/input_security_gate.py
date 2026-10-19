"""Input security gate for executor-bound planner actions."""

from __future__ import annotations


def _coerce_int(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _deny(action: str, reason: str) -> dict:
    return {
        "next_step": {
            "action": "finish",
            "answer": f"Blocked invalid planner action '{action}': {reason}",
            "task": "security_gate_denied",
        }
    }


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def input_security_gate_node(state: dict, config=None) -> dict:
    next_step = _as_dict((state or {}).get("next_step"))
    action = str(next_step.get("action") or "finish")

    if action == "tool":
        tool_name = str(next_step.get("tool_name") or "").strip()
        tool_args = _as_dict(next_step.get("tool_args"))
        if not tool_name:
            return _deny(action, "missing tool_name")
        return {"next_step": {**next_step, "tool_name": tool_name, "tool_args": tool_args}}

    if action == "subagent":
        agent_name = str(next_step.get("agent_name") or "").strip()
        task = str(next_step.get("task") or "").strip()
        if not agent_name:
            return _deny(action, "missing agent_name")
        if not task:
            return _deny(action, "missing task")
        return {"next_step": {**next_step, "agent_name": agent_name, "task": task}}

    if action == "child_agent":
        calls = next_step.get("child_calls") if isinstance(next_step.get("child_calls"), list) else []
        normalized = []
        for call in calls[:10]:
            if not isinstance(call, dict):
                continue
            task = str(call.get("task") or "").strip()
            if not task:
                continue
            entry = {
                "task": task,
                "parameters": call.get("parameters") if isinstance(call.get("parameters"), dict) else {},
            }
            if isinstance(call.get("requested_policy"), dict):
                entry["requested_policy"] = call["requested_policy"]
            normalized.append(entry)
        if not normalized:
            return _deny(action, "missing valid child_calls")
        return {"next_step": {**next_step, "child_calls": normalized}}

    if action == "collect_child":
        child_id = str(next_step.get("child_agent_id") or "").strip()
        if not child_id:
            return _deny(action, "missing child_agent_id")
        return {"next_step": {**next_step, "child_agent_id": child_id}}

    if action == "context_select":
        key = str(next_step.get("key") or "").strip()
        from_token = _coerce_int(next_step.get("from_token"), 0)
        to_token = _coerce_int(next_step.get("to_token"), None)
        if not key:
            return _deny(action, "missing key")
        if from_token is None or from_token < 0:
            from_token = 0
        if to_token is not None and to_token < from_token:
            to_token = None
        return {"next_step": {**next_step, "key": key, "from_token": from_token, "to_token": to_token}}

    if action == "ask_user":
        question = str(next_step.get("question") or "").strip() or "The agent needs more information to continue."
        options = [str(o).strip() for o in (next_step.get("options") or []) if str(o).strip()]
        return {"next_step": {**next_step, "question": question, "options": options[:10]}}

    if action == "finish":
        answer = next_step.get("answer")
        if answer is not None and not isinstance(answer, str):
            return _deny(action, "answer must be a string")
        return {}

    return _deny(action, "unknown action")
