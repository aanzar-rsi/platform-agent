"""Input security gate for executor-bound planner actions."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from src.agent.plan import parse_plan


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
    if state.get("planner_response"):
        return _validate_planner_response(state, config)

    next_step = _as_dict((state or {}).get("next_step"))
    action = str(next_step.get("action") or "finish")

    if action == "armory":
        resource_type = str(next_step.get("resource_type") or "").strip()
        resource_name = str(next_step.get("resource_name") or "").strip()
        if resource_type not in {"tool", "subagent"}:
            return _deny(action, "invalid resource_type")
        if not resource_name:
            return _deny(action, "missing resource_name")
        if not isinstance(next_step.get("arguments", {}), dict):
            return _deny(action, "arguments must be an object")
        task = str(next_step.get("task") or "").strip()
        if resource_type == "subagent" and not task:
            return _deny(action, "missing task")
        return {"next_step": {**next_step, "resource_type": resource_type,
                              "resource_name": resource_name,
                              "arguments": next_step.get("arguments", {}), "task": task}}

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


def _validate_planner_response(state: dict, config=None) -> dict:
    from src.agent.nodes.agentnode import _extract_tag, _parse_response

    raw = state.get("planner_response") or ""
    response_type = state.get("planner_response_type") or "planner"
    try:
        response_action = _extract_tag(raw, "action").strip().lower()
        reasoning = _extract_tag(raw, "reasoning")
        data = _extract_tag(raw, "data")
        task = _extract_tag(raw, "task")
        allowed = {"planner", "exit"} if response_type == "classifier" else {
            "continue", "retry", "exit", "planner_exit", "plan",
        }
        if not response_action:
            raise ValueError("missing required action")
        if response_action not in allowed:
            raise ValueError(f"unsupported {response_type} action: {response_action}")
        if not reasoning:
            raise ValueError("missing required reasoning")
        if response_action in {"exit", "planner_exit"} and not data:
            raise ValueError("exit requires data")
        if response_type == "planner" and response_action in {"continue", "retry", "plan"}:
            if not task:
                raise ValueError("planning requires task")
            if not data:
                raise ValueError("planning requires data")

        update = _parse_response(raw, turn_start=False)
        next_step = update.get("next_step") or {}
        action = next_step.get("action")

        if action == "plan":
            if response_type == "classifier":
                return {
                    "planner_response": "", "planner_mode": True, "planner_error": {},
                    "next_step": {"action": "replan"},
                }
            batch = next_step.get("steps_json") or ""
            if not batch:
                raise ValueError("missing required data batch")
            configurable = (config or {}).get("configurable") or {}
            planned = parse_plan(
                batch,
                max_plan_steps=int(configurable.get("max_plan_steps") or 8),
                resources={(item["type"], item["name"]) for item in state.get("planner_resources", [])},
            )
            return {
                **update,
                "planner_response": "", "planner_mode": True, "planner_error": {},
                "planned_phases": planned, "planned_phase_index": 0,
                "plan_created": {"phases": planned, "step_count": sum(len(p["steps"]) for p in planned)},
                "next_step": {},
            }

        if action != "finish":
            raise ValueError(f"unsupported response action: {action or 'missing'}")
        return {**update, "planner_response": "", "planner_mode": False, "planner_error": {}}
    except (ValueError, TypeError) as exc:
        error = {"stage": "planner_validation", "message": str(exc)}
        return {
            "planner_response": "", "planner_mode": True, "planner_error": error,
            "planned_phases": [], "planned_phase_index": 0,
            "next_step": {"action": "replan"},
            "messages": [AIMessage(content=f"Planner response rejected: {exc}", additional_kwargs={"ui_hidden": True})],
        }
