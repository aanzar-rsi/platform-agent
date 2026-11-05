from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .admission import DEFAULT_ADMISSION_POLICY
from . import repository


@dataclass(frozen=True)
class PreflightIdentityResult:
    decision: str
    reason_code: str
    message: str
    context: dict[str, Any]


def _normalize_status(value: object, *, default: str) -> str:
    # Normalize text statuses into a stable lower-case representation.
    text = str(value or "").strip().lower()
    return text or default


def _deny(reason_code: str, message: str, *, user_id: str | None = None) -> PreflightIdentityResult:
    # Build a fail-closed resolver result with safe context metadata.
    return PreflightIdentityResult(
        decision="deny",
        reason_code=reason_code,
        message=message,
        context={
            "decision": "deny",
            "reason_code": reason_code,
            "user_id": user_id,
            "tenant_id": None,
            "role_id": None,
            "role_name": None,
            "permissions": [],
            "session_present": False,
            "membership_active": False,
            "role_active": False,
            "tenant_active": False,
            "tenant_policy": {},
            "tenant_policy_loaded": False,
            "auth_session_valid": False,
            "policy_version": None,
            "agent_id": None,
        },
    )


def _to_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _normalize_tenant_policy(policy: Any) -> dict[str, Any]:
    """Normalize admission limits while preserving governed policy fields."""

    raw = policy if isinstance(policy, dict) else {}
    normalized = dict(raw)
    normalized.update({
        "max_query_chars": _to_int(raw.get("max_query_chars"), DEFAULT_ADMISSION_POLICY["max_query_chars"]),
        "max_attachment_count": _to_int(
            raw.get("max_attachment_count"), DEFAULT_ADMISSION_POLICY["max_attachment_count"]
        ),
        "max_attachment_bytes": _to_int(
            raw.get("max_attachment_bytes"), DEFAULT_ADMISSION_POLICY["max_attachment_bytes"]
        ),
        "requests_per_minute": _to_int(
            raw.get("requests_per_minute"), DEFAULT_ADMISSION_POLICY["requests_per_minute"]
        ),
        "conversation_idle_minutes": _to_int(
            raw.get("conversation_idle_minutes"), DEFAULT_ADMISSION_POLICY["conversation_idle_minutes"]
        ),
        "max_preflight_retries": _to_int(
            raw.get("max_preflight_retries"), DEFAULT_ADMISSION_POLICY["max_preflight_retries"]
        ),
    })
    return normalized


def resolve_preflight_identity(config: dict | None) -> PreflightIdentityResult:
    # Resolve trusted runtime identity into verified tenant-scoped planner context.
    configurable = (config or {}).get("configurable") or {}
    user_id = str(configurable.get("owner_id") or "").strip()
    session_id = str(configurable.get("session_id") or "").strip()
    policy_version = configurable.get("policy_version")
    agent_id = str(configurable.get("agent_id") or "").strip() or None
    if not user_id or not session_id:
        return _deny(
            "auth_context_missing",
            "Blocked preflight: authenticated runtime context missing",
            user_id=user_id or None,
        )

    membership = repository.get_tenant_user_membership(user_id)
    if not membership:
        return _deny(
            "tenant_membership_missing",
            "Blocked preflight: no tenant membership found for authenticated user",
            user_id=user_id,
        )

    membership_status = _normalize_status(membership.get("status"), default="inactive")
    tenant_id = str(membership.get("tenant_id") or "").strip() or None
    role_id = str(membership.get("role_id") or "").strip() or None
    if membership_status != "active":
        return PreflightIdentityResult(
            decision="deny",
            reason_code="tenant_user_inactive",
            message="Blocked preflight: tenant membership is inactive",
            context={
                "decision": "deny",
                "reason_code": "tenant_user_inactive",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role_id": role_id,
                "role_name": None,
                "permissions": [],
                "session_present": True,
                "membership_active": False,
                "role_active": False,
                "tenant_active": False,
                "tenant_policy": {},
                "tenant_policy_loaded": False,
                "auth_session_valid": False,
                "policy_version": policy_version,
                "agent_id": agent_id,
            },
        )

    if not tenant_id:
        return PreflightIdentityResult(
            decision="deny",
            reason_code="tenant_not_found",
            message="Blocked preflight: tenant membership is missing tenant_id",
            context={
                "decision": "deny",
                "reason_code": "tenant_not_found",
                "user_id": user_id,
                "tenant_id": None,
                "role_id": role_id,
                "role_name": None,
                "permissions": [],
                "session_present": True,
                "membership_active": True,
                "role_active": False,
                "tenant_active": False,
                "tenant_policy": {},
                "tenant_policy_loaded": False,
                "auth_session_valid": False,
                "policy_version": policy_version,
                "agent_id": agent_id,
            },
        )

    tenant = repository.get_tenant_record(tenant_id)
    if not tenant:
        return PreflightIdentityResult(
            decision="deny",
            reason_code="tenant_not_found",
            message="Blocked preflight: tenant record does not exist",
            context={
                "decision": "deny",
                "reason_code": "tenant_not_found",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role_id": role_id,
                "role_name": None,
                "permissions": [],
                "session_present": True,
                "membership_active": True,
                "role_active": False,
                "tenant_active": False,
            },
        )

    tenant_status = _normalize_status(tenant.get("status"), default="disabled")
    if tenant_status != "active":
        return PreflightIdentityResult(
            decision="deny",
            reason_code="tenant_inactive",
            message="Blocked preflight: tenant is not active",
            context={
                "decision": "deny",
                "reason_code": "tenant_inactive",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role_id": role_id,
                "role_name": None,
                "permissions": [],
                "session_present": True,
                "membership_active": True,
                "role_active": False,
                "tenant_active": False,
                "tenant_status": tenant_status,
                "tenant_policy": {},
                "tenant_policy_loaded": False,
                "auth_session_valid": False,
                "policy_version": policy_version,
                "agent_id": agent_id,
            },
        )

    if not role_id:
        return PreflightIdentityResult(
            decision="deny",
            reason_code="role_missing",
            message="Blocked preflight: tenant membership is missing role_id",
            context={
                "decision": "deny",
                "reason_code": "role_missing",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role_id": None,
                "role_name": None,
                "permissions": [],
                "session_present": True,
                "membership_active": True,
                "role_active": False,
                "tenant_active": True,
                "tenant_status": tenant_status,
                "tenant_policy": {},
                "tenant_policy_loaded": False,
                "auth_session_valid": False,
                "policy_version": policy_version,
                "agent_id": agent_id,
            },
        )

    role = repository.get_role_record(role_id, tenant_id)
    if not role:
        return PreflightIdentityResult(
            decision="deny",
            reason_code="role_not_found",
            message="Blocked preflight: role record does not exist for tenant membership",
            context={
                "decision": "deny",
                "reason_code": "role_not_found",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role_id": role_id,
                "role_name": None,
                "permissions": [],
                "session_present": True,
                "membership_active": True,
                "role_active": False,
                "tenant_active": True,
                "tenant_status": tenant_status,
                "tenant_policy": {},
                "tenant_policy_loaded": False,
                "auth_session_valid": False,
                "policy_version": policy_version,
                "agent_id": agent_id,
            },
        )

    role_status = _normalize_status(role.get("status"), default="inactive")
    role_name = str(role.get("name") or "").strip() or None
    if role_status != "active":
        return PreflightIdentityResult(
            decision="deny",
            reason_code="role_inactive",
            message="Blocked preflight: role is not active",
            context={
                "decision": "deny",
                "reason_code": "role_inactive",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role_id": role_id,
                "role_name": role_name,
                "permissions": [],
                "session_present": True,
                "membership_active": True,
                "role_active": False,
                "tenant_active": True,
                "tenant_status": tenant_status,
                "role_status": role_status,
                "tenant_policy": {},
                "tenant_policy_loaded": False,
                "auth_session_valid": False,
                "policy_version": policy_version,
                "agent_id": agent_id,
            },
        )

    permission_codes = repository.get_active_permission_codes(role_id, tenant_id)
    if not permission_codes:
        return PreflightIdentityResult(
            decision="deny",
            reason_code="permissions_missing",
            message="Blocked preflight: role has no active permissions",
            context={
                "decision": "deny",
                "reason_code": "permissions_missing",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "role_id": role_id,
                "role_name": role_name,
                "permissions": [],
                "session_present": True,
                "membership_active": True,
                "role_active": True,
                "tenant_active": True,
                "tenant_status": tenant_status,
                "role_status": role_status,
            },
        )

    return PreflightIdentityResult(
        decision="allow",
        reason_code="identity_resolved",
        message="",
        context={
            "decision": "allow",
            "reason_code": "identity_resolved",
            "user_id": user_id,
            "tenant_id": tenant_id,
            "role_id": role_id,
            "role_name": role_name,
            "permissions": permission_codes,
            "session_present": True,
            "membership_active": True,
            "role_active": True,
            "tenant_active": True,
            "tenant_status": tenant_status,
            "role_status": role_status,
            "tenant_policy": _normalize_tenant_policy(tenant.get("policy")),
            "tenant_policy_loaded": "policy" in tenant,
            "auth_session_valid": False,
            "policy_version": policy_version,
            "agent_id": agent_id,
        },
    )
