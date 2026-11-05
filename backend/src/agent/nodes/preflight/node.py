"""Preflight request gate before planner execution."""

from __future__ import annotations

import time

from langgraph.config import get_stream_writer
from langchain_core.messages import AIMessage

from src.agent.facets import Armory
from src.agent.preflight import resolve_preflight_identity
from src.agent.preflight import repository
from src.agent.preflight.admission import evaluate_admission
from src.agent.preflight.authorization import (
    AuthorizationResult,
    authorize_request,
    evaluate_request_readiness,
    parent_resource_scope,
    resource_allowed,
    verify_child_scope,
)
from src.agent.preflight.audit_repository import normalized_query_hash, write_preflight_audit
from src.agent.preflight.context import load_governed_context
from src.agent.preflight.request_contract import validate_request_fields
from src.utils.trace import context as trace_context, emit as trace_emit, in_run


def _trace_stage(stage: str, decision: str, reason_code: str, *, count: int | None = None,
                 started_at: float | None = None) -> None:
    """Record a small, correlated outcome without request or tool arguments."""
    if not in_run():
        return
    data = {"stage": stage, "decision": decision, "reason_code": reason_code}
    if count is not None:
        data["returned_count"] = count
    trace_emit("preflight.stage", component="preflight", status="denied" if decision == "deny" else "ok",
               duration_ms=(time.monotonic() - started_at) * 1000 if started_at is not None else None,
               data=data)


def _trace_decision(decision: str, reason_code: str, *, count: int = 0) -> None:
    if in_run():
        trace_emit("preflight.decision", component="preflight",
                   status="denied" if decision == "deny" else "ok",
                   data={"decision": decision, "reason_code": reason_code, "returned_count": count})


def _progress(stage: str) -> None:
    """Send a fixed, nontechnical stage name to the live run UI."""
    try:
        writer = get_stream_writer()
    except RuntimeError:
        return  # Direct node calls outside a streamed graph have no writer.
    writer({"kind": "preflight.status", "stage": stage})


def _deny(message: str, code: str = "invalid_request") -> dict:
    """Return a fail-closed malformed-request graph update."""

    _trace_decision("deny", code)
    return {
        "preflight_context": {},
        "planner_context": {},
        "planned_phases": [], "planned_phase_index": 0,
        "planner_response": "", "planner_mode": False,
        "next_step": {"action": "finish", "answer": message, "task": "preflight_denied"},
        "messages": [AIMessage(content=message)],
        "plan_event": {"kind": "preflight.denied", "reason_code": code},
    }


def _preflight_outcome(*, request_id: str, result, preflight_context: dict, retry_count: int) -> dict:
    """Map a non-planner Preflight decision into graph routing state."""

    decision = result.decision
    _trace_decision(decision, result.reason_code)
    kind = "preflight.denied"
    next_step = {"action": "finish", "answer": result.message, "task": "preflight_denied"}
    if decision == "clarify":
        kind = "preflight.clarify"
        next_step = {
            "action": "ask_user",
            "question": result.message,
            "options": ["Yes", "No"] if result.reason_code == "conversation_idle_timeout" else [],
            "task": "preflight_clarification" if result.reason_code == "conversation_idle_timeout" else "preflight_intent_clarification",
        }
    elif decision == "retry":
        kind = "preflight.retry"
        next_step = {"action": "retry", "task": "preflight_retry"}

    return {
        "preflight_context": preflight_context,
        "admission_context": getattr(result, "context", {}),
        "preflight_retry_count": retry_count,
        "planner_context": {},
        "planned_phases": [], "planned_phase_index": 0,
        "planner_response": "", "planner_mode": False,
        "next_step": next_step,
        **({"messages": [AIMessage(content=result.message)]} if decision == "deny" else {}),
        "plan_event": {
            "kind": kind,
            "reason_code": result.reason_code,
            "request_id": request_id,
            "decision": decision,
        },
    }


def _audit_decision(
    *,
    request: dict,
    identity: dict,
    config: dict | None,
    decision: str,
    reason_code: str,
    retry_count: int,
    memory_references: list[dict] | None = None,
    details: dict | None = None,
    resolved_intent: str | None = None,
    domain: str | None = None,
    candidate_tools: list[dict] | None = None,
) -> str | None:
    """Audit correlated runtime decisions without persisting request content."""

    configurable = (config or {}).get("configurable") or {}
    if not configurable.get("agent_id") or not configurable.get("execution_id"):
        return None
    return write_preflight_audit({
        "request_id": str(request.get("request_id") or ""),
        "trace_id": trace_context().get("trace_id"),
        "user_id": identity.get("user_id"),
        "tenant_id": identity.get("tenant_id"),
        "role_id": identity.get("role_id"),
        "agent_id": configurable.get("agent_id"),
        "execution_id": configurable.get("execution_id"),
        "query_hash": normalized_query_hash(str(request.get("query") or "")),
        "permissions": list(identity.get("permissions") or []),
        "resolved_intent": resolved_intent,
        "domain": domain,
        "decision": decision,
        "reason_code": reason_code,
        "memory_references": memory_references or [],
        "candidate_tools": candidate_tools or [],
        "details": details or {},
        "retry_count": retry_count,
    })


def _audit_or_deny(**kwargs) -> tuple[str | None, dict | None]:
    """Fail closed when a correlated production decision cannot be audited."""

    try:
        return _audit_decision(**kwargs), None
    except Exception:
        configurable = (kwargs.get("config") or {}).get("configurable") or {}
        if not configurable.get("agent_id") or not configurable.get("execution_id"):
            return None, None
        return None, _deny("Blocked request: Preflight audit is unavailable", code="preflight_audit_unavailable")


def _audit_validation_failure(*, request: dict, config: dict | None, reason_code: str, details: dict) -> str | None:
    """Audit malformed graph requests when trusted runtime correlation is available."""

    configurable = (config or {}).get("configurable") or {}
    if not configurable.get("agent_id") or not configurable.get("execution_id"):
        return None
    return write_preflight_audit({
        "request_id": str(request.get("request_id") or configurable.get("request_id") or "invalid-request"),
        "trace_id": trace_context().get("trace_id"),
        "user_id": configurable.get("owner_id"),
        "agent_id": configurable.get("agent_id"),
        "execution_id": configurable.get("execution_id"),
        "query_hash": normalized_query_hash(str(request.get("query") or "")),
        "permissions": [],
        "decision": "deny",
        "reason_code": reason_code,
        "details": details,
    })


def preflight_node(state: dict, config=None) -> dict:
    """Run request, identity, admission, context, and audit gates before planning."""

    request = state.get("planner_request") if isinstance(state.get("planner_request"), dict) else {}
    request_id = str(request.get("request_id") or "").strip()
    query = str(request.get("query") or "").strip()
    query_type = str(request.get("query_type") or "chat").strip().lower()
    stage_started = time.monotonic()
    _progress("checking")
    validation_error = validate_request_fields(request_id=request_id, query=query, query_type=query_type)
    if validation_error is not None:
        code, message, _details = validation_error
        _trace_stage("request", "deny", code, started_at=stage_started)
        try:
            _audit_validation_failure(request=request, config=config, reason_code=code, details=_details or {})
        except Exception:
            return _deny("Blocked request: Preflight audit is unavailable", code="preflight_audit_unavailable")
        return _deny(f"Blocked malformed request: {message}", code=code)

    _trace_stage("request", "allow", "request_valid", started_at=stage_started)
    stage_started = time.monotonic()
    _progress("access")
    try:
        identity = resolve_preflight_identity(config if isinstance(config, dict) else {})
    except Exception:
        _trace_stage("identity", "deny", "identity_unavailable", started_at=stage_started)
        return _deny("Blocked request: identity verification is unavailable", code="identity_unavailable")
    _trace_stage("identity", identity.decision, identity.reason_code, started_at=stage_started)
    if identity.decision != "allow":
        audit_id, audit_failure = _audit_or_deny(
            request=request,
            identity=identity.context,
            config=config,
            decision="deny",
            reason_code=identity.reason_code,
            retry_count=int(state.get("preflight_retry_count") or 0),
        )
        if audit_failure:
            return audit_failure
        _trace_decision("deny", identity.reason_code)
        return {
            "preflight_context": identity.context,
            "admission_context": {},
            "planner_context": {},
            "preflight_retry_count": int(state.get("preflight_retry_count") or 0),
            "next_step": {
                "action": "finish",
                "answer": identity.message,
                "task": "preflight_denied",
            },
            "messages": [AIMessage(content=identity.message)],
            "plan_event": {
                "kind": "preflight.denied",
                "reason_code": identity.reason_code,
                "request_id": request_id,
                "audit_id": audit_id,
            },
        }

    retry_count = int(state.get("preflight_retry_count") or 0)
    cfg = config if isinstance(config, dict) else {}
    if bool(state.get("preflight_resume")):
        cfg = {
            **cfg,
            "configurable": {**((cfg.get("configurable") or {})), "preflight_idle_confirmed": True},
        }

    stage_started = time.monotonic()
    try:
        admission = evaluate_admission(
            request=request,
            identity_context=identity.context,
            config=cfg,
            preflight_retry_count=retry_count,
        )
    except Exception:
        _trace_stage("admission", "deny", "admission_unavailable", started_at=stage_started)
        audit_id, audit_failure = _audit_or_deny(
            request=request, identity=identity.context, config=cfg,
            decision="deny", reason_code="admission_unavailable", retry_count=retry_count,
        )
        if audit_failure:
            return audit_failure
        outcome = _preflight_outcome(
            request_id=request_id,
            result=AuthorizationResult("deny", "admission_unavailable", "Admission checks are unavailable"),
            preflight_context={**identity.context, "decision": "deny", "reason_code": "admission_unavailable"},
            retry_count=retry_count,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome
    _trace_stage("admission", admission.decision, admission.reason_code, started_at=stage_started)

    preflight_context = {**identity.context, **admission.context}
    preflight_context["decision"] = admission.decision
    preflight_context["reason_code"] = admission.reason_code

    if admission.decision in {"deny", "clarify", "retry"}:
        next_retry = retry_count + 1 if admission.decision == "retry" else retry_count
        audit_id, audit_failure = _audit_or_deny(
            request=request,
            identity=identity.context,
            config=cfg,
            decision=admission.decision,
            reason_code=admission.reason_code,
            retry_count=next_retry,
            details={"stage": "admission"},
        )
        if audit_failure:
            return audit_failure
        outcome = _preflight_outcome(
            request_id=request_id,
            result=admission,
            preflight_context=preflight_context,
            retry_count=next_retry,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome

    _progress("actions")
    configurable = cfg.get("configurable") or {}
    parent_scope = None
    stage_started = time.monotonic()
    try:
        if configurable.get("child_agent_id") or configurable.get("parent_agent_id"):
            parent_scope = verify_child_scope(
                cfg, user_id=identity.context["user_id"],
                tenant_id=identity.context["tenant_id"], role_id=identity.context["role_id"],
            )
    except Exception:
        _trace_stage("permissions", "deny", "child_scope_invalid", started_at=stage_started)
        audit_id, audit_failure = _audit_or_deny(
            request=request, identity=identity.context, config=cfg,
            decision="deny", reason_code="child_scope_invalid", retry_count=retry_count,
            details={"stage": "business_authorization"},
        )
        if audit_failure:
            return audit_failure
        preflight_context.update(decision="deny", reason_code="child_scope_invalid")
        outcome = _preflight_outcome(
            request_id=request_id,
            result=AuthorizationResult("deny", "child_scope_invalid", "Unable to verify child permissions"),
            preflight_context=preflight_context, retry_count=retry_count,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome

    stage_started = time.monotonic()
    try:
        authorization = authorize_request(query, identity.context, cfg, parent_scope=parent_scope)
    except Exception:
        authorization = AuthorizationResult("deny", "intent_unavailable", "Unable to verify the requested action")
    if authorization.decision != "allow":
        _trace_stage("intent", authorization.decision, authorization.reason_code, started_at=stage_started)
        audit_id, audit_failure = _audit_or_deny(
            request=request, identity=identity.context, config=cfg,
            decision=authorization.decision, reason_code=authorization.reason_code,
            retry_count=retry_count, resolved_intent=",".join(authorization.required) or None,
            details={"stage": "business_intent"},
        )
        if audit_failure:
            return audit_failure
        preflight_context.update(decision=authorization.decision, reason_code=authorization.reason_code)
        outcome = _preflight_outcome(
            request_id=request_id, result=authorization,
            preflight_context=preflight_context, retry_count=retry_count,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome
    _trace_stage("intent", "allow", authorization.reason_code, count=len(authorization.required),
                 started_at=stage_started)
    _trace_stage("permissions", "allow", authorization.reason_code, count=len(authorization.held))
    stage_started = time.monotonic()
    try:
        readiness = evaluate_request_readiness(query, authorization.required, identity.context["tenant_policy"])
    except Exception:
        readiness = AuthorizationResult("deny", "readiness_unavailable", "Unable to verify request readiness")
    if readiness.decision != "allow":
        _trace_stage("readiness", readiness.decision, readiness.reason_code, started_at=stage_started)
        audit_id, audit_failure = _audit_or_deny(
            request=request, identity=identity.context, config=cfg,
            decision=readiness.decision, reason_code=readiness.reason_code,
            retry_count=retry_count, resolved_intent=",".join(authorization.required) or None,
            domain=getattr(readiness, "domain", None), details={"stage": "request_readiness"},
        )
        if audit_failure:
            return audit_failure
        preflight_context.update(decision=readiness.decision, reason_code=readiness.reason_code)
        outcome = _preflight_outcome(
            request_id=request_id, result=readiness,
            preflight_context=preflight_context, retry_count=retry_count,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome
    _trace_stage("readiness", "allow", readiness.reason_code, started_at=stage_started)
    stage_started = time.monotonic()
    try:
        resources = Armory(
            (configurable.get("policy") or {}).get("armory") or {},
            user_id=configurable.get("owner_id"), preloaded_context=state.get("preloaded_context"),
        ).list(reconnect=True)
    except Exception:
        _trace_stage("resources", "deny", "resource_catalog_unavailable", started_at=stage_started)
        audit_id, audit_failure = _audit_or_deny(
            request=request, identity=identity.context, config=cfg, decision="deny",
            reason_code="resource_catalog_unavailable", retry_count=retry_count,
        )
        if audit_failure:
            return audit_failure
        preflight_context.update(decision="deny", reason_code="resource_catalog_unavailable")
        outcome = _preflight_outcome(
            request_id=request_id,
            result=AuthorizationResult("deny", "resource_catalog_unavailable", "Tool catalog is unavailable"),
            preflight_context=preflight_context, retry_count=retry_count,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome
    held_permissions = set(authorization.held)
    parent_resources = None
    if parent_scope is not None:
        try:
            parent_resources = parent_resource_scope(
                str(configurable["parent_execution_id"]), str(configurable["parent_agent_id"]),
                str(identity.context["user_id"]),
            )
        except Exception:
            _trace_stage("resources", "deny", "child_resource_scope_invalid", started_at=stage_started)
            audit_id, audit_failure = _audit_or_deny(
                request=request, identity=identity.context, config=cfg, decision="deny",
                reason_code="child_resource_scope_invalid", retry_count=retry_count,
            )
            if audit_failure:
                return audit_failure
            preflight_context.update(decision="deny", reason_code="child_resource_scope_invalid")
            outcome = _preflight_outcome(
                request_id=request_id,
                result=AuthorizationResult("deny", "child_resource_scope_invalid", "Child resources are unavailable"),
                preflight_context=preflight_context, retry_count=retry_count,
            )
            outcome["plan_event"]["audit_id"] = audit_id
            return outcome
    approved = []
    try:
        for resource in resources:
            if parent_resources is not None and (resource.type, resource.name) not in parent_resources:
                continue
            remote_name = getattr(resource.target, "remote_name", None)
            if resource_allowed(resource.type, resource.name,
                                tenant_id=str(identity.context.get("tenant_id") or ""),
                                remote_name=remote_name,
                                tenant_policy=identity.context.get("tenant_policy") or {},
                                held=held_permissions, required=set(authorization.required)):
                approved.append({"type": resource.type, "name": resource.name,
                                 "remote_name": remote_name, "rank": len(approved) + 1})
    except Exception:
        _trace_stage("resources", "deny", "resource_mapping_unavailable", started_at=stage_started)
        audit_id, audit_failure = _audit_or_deny(
            request=request, identity=identity.context, config=cfg, decision="deny",
            reason_code="resource_mapping_unavailable", retry_count=retry_count,
        )
        if audit_failure:
            return audit_failure
        preflight_context.update(decision="deny", reason_code="resource_mapping_unavailable")
        outcome = _preflight_outcome(
            request_id=request_id,
            result=AuthorizationResult("deny", "resource_mapping_unavailable", "Tool authorization is unavailable"),
            preflight_context=preflight_context, retry_count=retry_count,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome

    _trace_stage("resources", "allow", "resources_filtered", count=len(approved), started_at=stage_started)
    stage_started = time.monotonic()
    _progress("context")
    try:
        governed = load_governed_context(
            request=request, state=state, identity_context=identity.context, config=cfg,
        )
    except Exception:
        _trace_stage("context", "deny", "context_unavailable", started_at=stage_started)
        audit_id, audit_failure = _audit_or_deny(
            request=request, identity=identity.context, config=cfg, decision="deny",
            reason_code="context_unavailable", retry_count=retry_count,
        )
        if audit_failure:
            return audit_failure
        preflight_context.update(decision="deny", reason_code="context_unavailable")
        outcome = _preflight_outcome(
            request_id=request_id,
            result=AuthorizationResult("deny", "context_unavailable", "Request context is unavailable"),
            preflight_context=preflight_context, retry_count=retry_count,
        )
        outcome["plan_event"]["audit_id"] = audit_id
        return outcome
    _trace_stage("context", governed.decision, governed.reason_code,
                 count=len(governed.items) if isinstance(getattr(governed, "items", None), tuple) else 0,
                 started_at=stage_started)
    preflight_context["decision"] = governed.decision
    preflight_context["reason_code"] = governed.reason_code
    governed_planner_context = governed.planner_context()
    maximum_sensitivity = governed.details.get("maximum_sensitivity")
    if maximum_sensitivity:
        governed_planner_context["maximum_sensitivity"] = maximum_sensitivity
    governed_planner_context["token_budget"] = max(100, min(5000, int(
        (identity.context.get("tenant_policy") or {}).get("memory_context_tokens") or 1500
    )))
    memory_references = governed_planner_context["memory_references"]
    if governed.decision in {"deny", "clarify", "retry"}:
        approved = []
    audit_id, audit_failure = _audit_or_deny(
        request=request,
        identity=identity.context,
        config=cfg,
        decision=governed.decision,
        reason_code=governed.reason_code,
        retry_count=retry_count,
        memory_references=memory_references,
        details={
            **governed.details,
            "permissions_needed": list(authorization.required),
            "required_fields": list(readiness.required_fields),
            "missing_fields": list(readiness.missing_fields),
            "write_requires_confirmation": readiness.write_requires_confirmation,
        },
        resolved_intent=",".join(authorization.required) or None,
        domain=readiness.domain,
        candidate_tools=approved,
    )
    if audit_failure:
        return audit_failure
    if governed.decision in {"deny", "clarify", "retry"}:
        return _preflight_outcome(
            request_id=request_id,
            result=governed,
            preflight_context=preflight_context,
            retry_count=retry_count + 1 if governed.decision == "retry" else retry_count,
        ) | {"plan_event": {
            "kind": f"preflight.{governed.decision if governed.decision != 'deny' else 'denied'}",
            "reason_code": governed.reason_code,
            "request_id": request_id,
            "decision": governed.decision,
            "audit_id": audit_id,
        }}

    _trace_decision(governed.decision, governed.reason_code, count=len(approved))
    update = {
        "preflight_context": preflight_context,
        "admission_context": admission.context,
        "preflight_retry_count": retry_count,
        "preflight_resume": False,
        "planned_phases": [],
        "planned_phase_index": 0,
        "planner_response": "",
        "planner_mode": False,
        "planner_error": {},
        "step_results": [],
        "executor_output": {},
        "pending_context_selection": {},
        "human_request_kind": "",
        "next_step": {"action": "replan"},
        "planner_context": {
            "version": 3,
            "identity": {
                "user_id": preflight_context.get("user_id"),
                "tenant_id": preflight_context.get("tenant_id"),
                "role_id": preflight_context.get("role_id"),
            },
            "authorization": {
                "permissions": list(authorization.held),
                "permissions_held": list(authorization.held),
                "permissions_needed": list(authorization.required),
                "policy_version": identity.context.get("policy_version"),
            },
            "intent": list(authorization.required),
            "domain": readiness.domain,
            "readiness": {
                "required_fields": list(readiness.required_fields),
                "missing_fields": list(readiness.missing_fields),
                "write_requires_confirmation": readiness.write_requires_confirmation,
            },
            "resources": approved,
            "admission": {
                "decision": admission.decision,
                "reason_code": admission.reason_code,
                "checks": admission.context.get("checks") or {},
                "query_char_count": int(admission.context.get("query_char_count") or 0),
                "attachment_count": int(admission.context.get("attachment_count") or 0),
                "retry_count": int(admission.context.get("retry_count") or 0),
            },
            "context": governed_planner_context,
            "decision": {
                "value": governed.decision,
                "reason_code": governed.reason_code,
            },
        },
        "plan_event": {
            "kind": "preflight.ready",
            "request_id": request_id,
            "reason_code": governed.reason_code,
            "role_id": preflight_context.get("role_id"),
            "permission_count": len(preflight_context.get("permissions") or []),
            "decision": governed.decision,
            "audit_id": audit_id,
        },
    }
    return update
