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
    return _single_step_batch({
        "action": "finish",
        "answer": f"Blocked invalid planner action '{action}': {reason}",
        "task": "security_gate_denied",
    })


def _as_dict(value) -> dict:
    return value if isinstance(value, dict) else {}


def _require_tag(raw: str, tag: str, *, required: bool = True) -> str:
    open_tag = f"<{tag}>"
    close_tag = f"</{tag}>"
    open_pos = raw.find(open_tag)
    close_pos = raw.find(close_tag)

    if open_pos == -1 and close_pos == -1:
        if required:
            raise ValueError(f"missing required {tag}")
        return ""
    if open_pos == -1:
        raise ValueError(f"malformed <{tag}>: missing opening tag")
    if close_pos == -1:
        raise ValueError(f"malformed <{tag}>: missing closing tag {close_tag}")
    if close_pos < open_pos:
        raise ValueError(f"malformed <{tag}>: closing tag appears before opening tag")

    value = raw[open_pos + len(open_tag):close_pos].strip()
    if required and not value:
        raise ValueError(f"missing required {tag}")
    return value


def _single_step_batch(next_step: dict, *, action_id: str = "action:1") -> dict:
    return {
        "planned_phases": [{"sequence": 1, "steps": [{
            "id": action_id, "action": "command", "command": next_step,
            "name": next_step.get("resource_name", ""), "task": next_step.get("task", ""),
            "uses": [],
        }]}],
        "planned_phase_index": 0,
        "next_step": {},
    }


def _accept_action(state: dict, next_step: dict, config=None) -> dict:
    """Normalize a validated direct action into the universal batch contract."""
    sequence = int(state.get("action_sequence") or 0) + 1
    execution_id = str(((config or {}).get("configurable") or {}).get("execution_id") or "execution")
    action_id = str(next_step.get("action_id") or f"{execution_id}:action:{sequence}")
    return {
        "action_sequence": sequence,
        **_single_step_batch({**next_step, "action_id": action_id}, action_id=action_id),
    }


def input_security_gate_node(state: dict, config=None) -> dict:
    if state.get("executor_output"):
        envelope = state["executor_output"]
        action_id = str(envelope.get("action_id") or "precomputed")
        return {
            **_single_step_batch({"action": "precomputed"}, action_id=action_id),
            "step_results": [{"id": action_id, "sequence": 1, "action": "precomputed",
                              "task": "", "name": "", "results": envelope.get("results") or []}],
            "executor_output": {},
        }
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
        return _accept_action(state, {**next_step, "resource_type": resource_type,
                                      "resource_name": resource_name,
                                      "arguments": next_step.get("arguments", {}), "task": task}, config)

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
        return _accept_action(state, {**next_step, "child_calls": normalized}, config)

    if action == "collect_child":
        child_id = str(next_step.get("child_agent_id") or "").strip()
        if not child_id:
            return _deny(action, "missing child_agent_id")
        return _accept_action(state, {**next_step, "child_agent_id": child_id}, config)

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
        return _accept_action(state, {**next_step, "key": key, "from_token": from_token,
                                      "to_token": to_token}, config)

    if action == "ask_user":
        question = str(next_step.get("question") or "").strip() or "The agent needs more information to continue."
        options = [str(o).strip() for o in (next_step.get("options") or []) if str(o).strip()]
        return _accept_action(state, {**next_step, "question": question, "options": options[:10]}, config)

    if action == "finish":
        answer = next_step.get("answer")
        if answer is not None and not isinstance(answer, str):
            return _deny(action, "answer must be a string")
        return _accept_action(state, next_step, config)

    return _deny(action, "unknown action")


def _validate_planner_response(state: dict, config=None) -> dict:
    from src.agent.nodes.agentnode import _parse_response

    raw = state.get("planner_response") or ""
    response_type = state.get("planner_response_type") or "planner"
    try:
        response_action = _require_tag(raw, "action").lower()
        allowed = {"planner", "exit"} if response_type == "classifier" else {
            "continue", "retry", "exit", "planner_exit", "plan",
        }
        if response_action not in allowed:
            raise ValueError(f"unsupported {response_type} action: {response_action}")

        _require_tag(raw, "reasoning")
        if response_action in {"exit", "planner_exit"}:
            _require_tag(raw, "data")
        if response_type == "planner" and response_action in {"continue", "retry", "plan"}:
            _require_tag(raw, "task")
            _require_tag(raw, "data")

        update = _parse_response(raw, turn_start=False)
        next_step = update.get("next_step") or {}
        action = next_step.get("action")

        if action == "plan":
            if response_type == "classifier":
                return {
                    "planner_response": "", "planner_mode": True, "planner_error": {},
                    **_single_step_batch({"action": "replan"}, action_id="replan"),
                }
            batch = next_step.get("steps_json") or ""
            if not batch:
                raise ValueError("missing required data batch")
            configurable = (config or {}).get("configurable") or {}
            planned = parse_plan(
                batch,
                max_plan_steps=int(configurable.get("max_plan_steps") or 8),
                resources={(item["type"], item["name"]) for item in state.get("planner_resources", [])},
                context_selection_summary=state.get("context_selection_summary") or {},
            )
            execution_id = str(configurable.get("execution_id") or "execution")
            for phase in planned:
                for step in phase["steps"]:
                    step["action_id"] = f"{execution_id}:phase:{phase['sequence']}:step:{step['id']}"
            return {
                **update,
                "planner_response": "", "planner_mode": True, "planner_error": {},
                "planned_phases": planned, "planned_phase_index": 0,
                "plan_created": {"phases": planned, "step_count": sum(len(p["steps"]) for p in planned)},
                "next_step": {},
            }

        if action != "finish":
            raise ValueError(f"unsupported response action: {action or 'missing'}")
        accepted = _accept_action(state, next_step, config)
        return {**update, **accepted, "planner_response": "", "planner_mode": False, "planner_error": {}}
    except (ValueError, TypeError) as exc:
        if "context_select loop detected" in str(exc):
            message = (
                "Planner requested a repeated context window after loop detection. "
                "Stopping to prevent another context-selection loop."
            )
            accepted = _accept_action(state, {"action": "finish", "answer": message}, config)
            return {
                "planner_response": "",
                "planner_mode": False,
                "planner_error": {"stage": "planner_validation", "message": str(exc)},
                **accepted,
            }
        prior_attempt = 0
        if isinstance(state.get("planner_error"), dict):
            try:
                prior_attempt = int(state["planner_error"].get("attempt") or 0)
            except Exception:
                prior_attempt = 0
        error = {
            "stage": "planner_validation",
            "message": str(exc),
            "attempt": prior_attempt + 1,
            "instruction": "Rebuild the full response from scratch and include all required tags.",
        }
        return {
            "planner_response": "", "planner_mode": True, "planner_error": error,
            **_single_step_batch({"action": "replan"}, action_id="replan"),
            "messages": [AIMessage(content=f"Planner response rejected: {exc}", additional_kwargs={"ui_hidden": True})],
        }
