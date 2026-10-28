"""Unified graph adapter for every executable armory resource."""

from src.agent.control import clear_pause, note_text_from_resume, pause_gate_active, thread_id_from_config
from src.agent.facets import Armory
from src.agent.nodes.output_security_gate import sanitize_executor_output
from src.agent.nodes.result_collector import branch_result
from src.agent.subagent_stream import emit_subagent_event


def armory_node(state: dict, config=None) -> dict:
    next_step = state["next_step"]
    resource_type = next_step.get("resource_type", "")
    resource_name = next_step.get("resource_name", "")
    arguments = next_step.get("arguments", {})
    task = next_step.get("task") or state.get("current_task") or ""
    configurable = (config or {}).get("configurable") or {}
    policy = ((configurable.get("policy") or {}).get("armory") or {})
    armory = Armory(policy, user_id=configurable.get("owner_id"),
                    preloaded_context=state.get("preloaded_context"))

    thread_id = thread_id_from_config(config)
    paused = pause_gate_active(thread_id, "armory_node", kinds=frozenset({"paused", "confirm_resource"}))
    resource = armory.get(resource_type, resource_name, reconnect=True)
    confirm = bool(resource and resource.confirmation_required and policy.get("confirm_tools", True))
    if paused or confirm:
        from langgraph.types import interrupt

        decision = interrupt({"kind": "confirm_resource" if confirm else "paused", "node": "armory_node",
                              "resource_type": resource_type, "resource_name": resource_name,
                              "arguments": arguments, "task": task, "confirm_required": confirm})
        if paused:
            clear_pause(thread_id)
        note = note_text_from_resume(decision).strip()
        approved = not confirm or (isinstance(decision, dict) and bool(decision.get("approved")))
        if paused and not confirm:
            return _envelope(state, next_step, "armory", [{
                "kind": "human_input", "value": note or "(no answer provided)", "success": True,
                "task": task, "description": "User response at armory pause gate",
                "metadata": {"input_kind": "paused"},
            }])
        if not approved:
            result, structured = {"success": False, "error": "User declined to run this resource."}, None
            return _result_envelope(state, next_step, resource_type, resource_name, arguments, task,
                                    result, structured, note=note)

    if resource_type == "subagent":
        emit_subagent_event(resource_name, {"kind": "start", "message": "Starting",
                                             "action_id": next_step.get("action_id")})
    try:
        result, structured = armory.call(resource_type, resource_name, arguments, task=task, reconnect=True)
        success = not (isinstance(result, dict) and result.get("success") is False)
    except Exception as exc:
        result, structured, success = {"success": False, "error": str(exc)}, None, False
    if resource_type == "subagent":
        emit_subagent_event(resource_name, {"kind": "complete" if success else "error",
                                             "message": "Completed" if success else str(result),
                                             "action_id": next_step.get("action_id")})
    return _result_envelope(state, next_step, resource_type, resource_name, arguments, task, result, structured,
                            note=note if 'note' in locals() else "")


def _envelope(state, next_step, source, results):
    envelope = sanitize_executor_output({
        "version": 1, "action_id": next_step.get("action_id"), "source": source, "results": results,
    })
    return branch_result(state, envelope)


def _result_envelope(state, next_step, resource_type, resource_name, arguments, task, result, structured, *, note=""):
    success = not (isinstance(result, dict) and result.get("success") is False)
    results = []
    if note:
        results.append({"kind": "human_input", "value": note, "success": True, "task": task,
                        "description": "User response at armory approval gate",
                        "metadata": {"input_kind": "confirmation"}})
    results.append({
        "kind": "armory_result", "value": result, "success": success, "task": task,
        "name": resource_name, "description": task or f"armory.{resource_type}.{resource_name}",
        "metadata": {"resource_type": resource_type, "resource_name": resource_name,
                     "arguments": arguments, "structured": structured},
    })
    return _envelope(state, next_step, "armory", results)
