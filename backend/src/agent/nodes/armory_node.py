"""Unified graph adapter for every executable armory resource."""

import hashlib
import json

from langgraph import types as langgraph_types
from src.agent.control import clear_pause, note_text_from_resume, pause_gate_active, thread_id_from_config
from src.agent.facets import Armory
from src.agent.nodes.output_security_gate import sanitize_executor_output
from src.agent.nodes.result_collector import branch_result
from src.agent.subagent_stream import emit_subagent_event
from src.agent.preflight import authorization as preflight_authorization
from src.agent.preflight import repository as preflight_repository
from src.utils.trace import emit as trace_emit, in_run


def _tool_trace(event: str, name: str, *, decision: str, reason_code: str) -> None:
    if in_run():
        trace_emit(event, component="armory_node", status="denied" if decision == "deny" else "ok",
                   data={"tool_name": name, "decision": decision, "reason_code": reason_code})


def armory_node(state: dict, config=None) -> dict:
    """Authorize, invoke, and record one planner-selected resource."""

    next_step = state["next_step"]
    resource_type = next_step.get("resource_type", "")
    resource_name = next_step.get("resource_name", "")
    arguments = next_step.get("arguments", {})
    task = next_step.get("task") or state.get("current_task") or ""
    configurable = (config or {}).get("configurable") or {}
    trusted_context = state.get("planner_context") or {}
    if (state.get("preflight_context") or {}).get("decision") not in {"allow", "degrade"}:
        return _result_envelope(state, next_step, resource_type, resource_name, arguments, task,
                                {"success": False, "error": "Preflight approval is required."}, None)
    policy = ((configurable.get("policy") or {}).get("armory") or {})
    approved_resources = {
        (str(item.get("type") or ""), str(item.get("name") or ""))
        for item in trusted_context.get("resources") or []
        if isinstance(item, dict)
    }
    if (resource_type, resource_name) not in approved_resources:
        _tool_trace("armory.authz.deny", resource_name, decision="deny", reason_code="resource_not_approved")
        return _result_envelope(state, next_step, resource_type, resource_name, arguments, task,
                                {"success": False, "error": "Resource was not approved by Preflight."}, None)

    armory = Armory(policy, user_id=configurable.get("owner_id"),
                    preloaded_context=state.get("preloaded_context"))
    identity = trusted_context.get("identity") or {}
    authorization = trusted_context.get("authorization") or {}

    def authorize(remote_name: str | None = None) -> None:
        preflight_authorization.check_resource_execution(
            user_id=str(configurable.get("owner_id") or ""),
            agent_id=str(configurable.get("agent_id") or ""),
            session_id=str(configurable.get("session_id") or ""),
            resource_type=resource_type, resource_name=resource_name,
            remote_name=remote_name,
            required=authorization.get("permissions_needed") or [],
            tenant_id=str(identity.get("tenant_id") or ""),
            role_id=str(identity.get("role_id") or ""),
            policy_version=configurable.get("policy_version"),
            config=config,
        )

    thread_id = thread_id_from_config(config)
    paused = pause_gate_active(thread_id, "armory_node", kinds=frozenset({"paused", "confirm_tool"}))
    try:
        resource = armory.get(resource_type, resource_name, reconnect=True)
    except Exception:
        _tool_trace("armory.authz.deny", resource_name, decision="deny", reason_code="resource_unavailable")
        return _result_envelope(state, next_step, resource_type, resource_name, arguments, task,
                                {"success": False, "error": "Resource is unavailable."}, None)
    remote_name = getattr(resource.target, "remote_name", None)
    try:
        authorize(remote_name)
    except Exception:
        _tool_trace("armory.authz.deny", resource_name, decision="deny", reason_code="authorization_revoked")
        return _result_envelope(state, next_step, resource_type, resource_name, arguments, task,
                                {"success": False, "error": "Resource authorization is unavailable or revoked."}, None)
    tenant_policy = (state.get("preflight_context") or {}).get("tenant_policy") or {}
    # A request can expose all granted BAPIs, so confirmation follows the
    # selected tool's trusted catalog effect rather than the request's intent.
    mapped_write = False
    if resource_type == "tool" and isinstance(remote_name, str) and remote_name:
        try:
            mapping = preflight_repository.get_bapi_for_resource(str(identity.get("tenant_id") or ""), remote_name)
            if not mapping:
                raise PermissionError("business_mapping_unavailable")
            mapped_write = mapping.get("effect") == "write"
        except Exception:
            _tool_trace("armory.authz.deny", resource_name, decision="deny", reason_code="business_mapping_unavailable")
            return _result_envelope(state, next_step, resource_type, resource_name, arguments, task,
                                    {"success": False, "error": "Resource authorization is unavailable or revoked."}, None)
    confirm = bool(resource and (
        (policy.get("confirm_tools", True) and resource.confirmation_required) or
        (mapped_write and tenant_policy.get("confirm_writes", False))
    ))
    proposal = {"resource_type": resource_type, "resource_name": resource_name, "arguments": arguments}
    confirmation_id = hashlib.sha256(
        json.dumps(proposal, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()
    if paused or confirm:
        if confirm:
            _tool_trace("guardrail.decision.approval_required", resource_name,
                        decision="clarify", reason_code="write_confirmation_required")
        decision = langgraph_types.interrupt({"kind": "confirm_tool" if confirm else "paused", "node": "armory_node",
                               "resource_type": resource_type, "resource_name": resource_name,
                               "arguments": arguments, "tool_name": resource_name, "tool_args": arguments,
                               "confirmation_id": confirmation_id, "task": task, "confirm_required": confirm})
        if paused:
            clear_pause(thread_id)
        note = note_text_from_resume(decision).strip()
        approved = not confirm or (
            isinstance(decision, dict) and decision.get("approved") is True and
            decision.get("confirmation_id") == confirmation_id
        )
        if paused and not confirm:
            return _envelope(state, next_step, "armory", [{
                "kind": "human_input", "value": note or "(no answer provided)", "success": True,
                "task": task, "description": "User response at armory pause gate",
                "metadata": {"input_kind": "paused"},
            }])
        if not approved:
            result, structured = {"success": False, "error": "User declined to run this resource."}, None
            return _result_envelope(state, next_step, resource_type, resource_name, arguments, task,
                                    result, structured, note=note,
                                    child_agent_id=configurable.get("child_agent_id"))

    try:
        authorize(remote_name)
        _tool_trace("armory.authz.allow", resource_name, decision="allow", reason_code="execution_rechecked")
        if resource_type == "subagent":
            emit_subagent_event(resource_name, {"kind": "start", "message": "Starting"})
        result, structured = armory.call(resource_type, resource_name, arguments, task=task, reconnect=True)
        success = not (isinstance(result, dict) and result.get("success") is False)
    except Exception as exc:
        result, structured, success = {"success": False, "error": str(exc)}, None, False
    if resource_type == "subagent":
        emit_subagent_event(resource_name, {"kind": "complete" if success else "error",
                                              "message": "Completed" if success else str(result),
                                             "action_id": next_step.get("action_id")})
    return _result_envelope(state, next_step, resource_type, resource_name, arguments, task, result, structured,
                            note=note if 'note' in locals() else "",
                            child_agent_id=configurable.get("child_agent_id"))


def _envelope(state, next_step, source, results):
    envelope = sanitize_executor_output({
        "version": 1, "action_id": next_step.get("action_id"), "source": source, "results": results,
    })
    return branch_result(state, envelope)


def _result_envelope(state, next_step, resource_type, resource_name, arguments, task, result, structured, *, note="",
                     child_agent_id=None):
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
                     "arguments": arguments, "structured": structured,
                     **({"child_agent_id": child_agent_id} if child_agent_id else {})},
    })
    return _envelope(state, next_step, "armory", results)
