from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .admission_repository import AdmissionRepository

DEFAULT_ADMISSION_POLICY: dict[str, int] = {
    "max_query_chars": 10_000,
    "max_attachment_count": 10,
    "max_attachment_bytes": 52_428_800,
    "requests_per_minute": 30,
    "conversation_idle_minutes": 60,
    "max_preflight_retries": 2,
}

IDENTITY_OVERRIDE_FIELDS = frozenset({
    "user_id",
    "tenant_id",
    "role_id",
    "permissions",
    "session_id",
})
IDENTITY_BYPASS_PHRASES = ("ignore authorization", "bypass authorization", "ignore access controls")


@dataclass(frozen=True)
class AdmissionResult:
    decision: str
    reason_code: str
    message: str
    context: dict[str, Any]


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _to_int(value: Any, default: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number >= 0 else default


def _normalized_policy_snapshot(raw_policy: Any) -> dict[str, int]:
    policy = raw_policy if isinstance(raw_policy, dict) else {}
    return {
        "max_query_chars": _to_int(policy.get("max_query_chars"), DEFAULT_ADMISSION_POLICY["max_query_chars"]),
        "max_attachment_count": _to_int(
            policy.get("max_attachment_count"), DEFAULT_ADMISSION_POLICY["max_attachment_count"]
        ),
        "max_attachment_bytes": _to_int(
            policy.get("max_attachment_bytes"), DEFAULT_ADMISSION_POLICY["max_attachment_bytes"]
        ),
        "requests_per_minute": _to_int(
            policy.get("requests_per_minute"), DEFAULT_ADMISSION_POLICY["requests_per_minute"]
        ),
        "conversation_idle_minutes": _to_int(
            policy.get("conversation_idle_minutes"), DEFAULT_ADMISSION_POLICY["conversation_idle_minutes"]
        ),
        "max_preflight_retries": _to_int(
            policy.get("max_preflight_retries"), DEFAULT_ADMISSION_POLICY["max_preflight_retries"]
        ),
    }


def _base_context(
    *,
    decision: str,
    reason_code: str,
    policy: dict[str, int],
    query_char_count: int,
    attachment_count: int,
    retry_count: int,
    checks: dict[str, Any],
) -> dict[str, Any]:
    return {
        "decision": decision,
        "reason_code": reason_code,
        "checks": checks,
        "query_char_count": query_char_count,
        "attachment_count": attachment_count,
        "retry_count": retry_count,
        "policy": policy,
    }


def _result(
    *,
    decision: str,
    reason_code: str,
    message: str,
    policy: dict[str, int],
    query_char_count: int,
    attachment_count: int,
    retry_count: int,
    checks: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> AdmissionResult:
    payload = _base_context(
        decision=decision,
        reason_code=reason_code,
        policy=policy,
        query_char_count=query_char_count,
        attachment_count=attachment_count,
        retry_count=retry_count,
        checks=checks,
    )
    if context:
        payload.update(context)
    return AdmissionResult(decision=decision, reason_code=reason_code, message=message, context=payload)


def _has_structured_identity_override(request: dict[str, Any]) -> bool:
    """Detect structured or explicit attempts to override trusted identity."""

    query = str(request.get("query") or "").lower()
    return any(field in request for field in IDENTITY_OVERRIDE_FIELDS) or any(
        phrase in query for phrase in IDENTITY_BYPASS_PHRASES
    )


def _extract_attachments(request: dict[str, Any]) -> list[dict[str, Any]]:
    raw = request.get("attachments")
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("attachment_metadata_invalid")
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("attachment_metadata_invalid")
        attachment_id = str(item.get("attachment_id") or item.get("id") or "").strip()
        size = item.get("size_bytes", item.get("bytes"))
        try:
            size_int = int(size)
        except (TypeError, ValueError):
            raise ValueError("attachment_metadata_invalid") from None
        if size_int < 0:
            raise ValueError("attachment_metadata_invalid")
        out.append({"attachment_id": attachment_id, "size_bytes": size_int})
    return out


def evaluate_admission(
    *,
    request: dict[str, Any],
    identity_context: dict[str, Any],
    config: dict | None,
    preflight_retry_count: int,
    repository: AdmissionRepository | None = None,
) -> AdmissionResult:
    repo = repository or AdmissionRepository()
    configurable = (config or {}).get("configurable") or {}

    policy = _normalized_policy_snapshot(identity_context.get("tenant_policy") or {})
    query = str(request.get("query") or "").strip()
    query_char_count = len(query)
    checks: dict[str, Any] = {}

    if _has_structured_identity_override(request):
        return _result(
            decision="deny",
            reason_code="identity_override_attempt",
            message="Blocked request: identity override fields are not allowed",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=0,
            retry_count=preflight_retry_count,
            checks=checks,
        )

    if query_char_count > policy["max_query_chars"]:
        return _result(
            decision="deny",
            reason_code="query_too_large",
            message=f"Blocked request: query exceeds max length ({policy['max_query_chars']})",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=0,
            retry_count=preflight_retry_count,
            checks=checks,
        )

    try:
        attachments = _extract_attachments(request)
    except ValueError:
        return _result(
            decision="deny",
            reason_code="attachment_metadata_invalid",
            message="Blocked request: attachment metadata is invalid",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=0,
            retry_count=preflight_retry_count,
            checks=checks,
        )

    attachment_count = len(attachments)
    if attachment_count > policy["max_attachment_count"]:
        return _result(
            decision="deny",
            reason_code="attachment_count_exceeded",
            message="Blocked request: attachment count exceeds policy",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=attachment_count,
            retry_count=preflight_retry_count,
            checks=checks,
        )

    total_attachment_bytes = sum(item["size_bytes"] for item in attachments)
    if total_attachment_bytes > policy["max_attachment_bytes"]:
        return _result(
            decision="deny",
            reason_code="attachment_size_exceeded",
            message="Blocked request: total attachment size exceeds policy",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=attachment_count,
            retry_count=preflight_retry_count,
            checks=checks,
        )
    checks["attachment_total_bytes"] = total_attachment_bytes

    user_id = str(identity_context.get("user_id") or "").strip()
    tenant_id = str(identity_context.get("tenant_id") or "").strip()
    session_id = str(configurable.get("session_id") or "").strip()
    auth_session = repo.get_active_auth_session(session_id, user_id) if user_id and session_id else None
    if not auth_session:
        return _result(
            decision="deny",
            reason_code="auth_session_invalid",
            message="Blocked request: active authenticated session is required",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=attachment_count,
            retry_count=preflight_retry_count,
            checks=checks,
        )
    checks["auth_session_valid"] = True

    policy_version = configurable.get("policy_version")
    if policy_version in (None, ""):
        return _result(
            decision="deny",
            reason_code="policy_version_unavailable",
            message="Blocked request: policy version unavailable",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=attachment_count,
            retry_count=preflight_retry_count,
            checks=checks,
        )

    if not identity_context.get("tenant_policy_loaded", True):
        return _result(
            decision="deny",
            reason_code="tenant_policy_unavailable",
            message="Blocked request: tenant policy unavailable",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=attachment_count,
            retry_count=preflight_retry_count,
            checks=checks,
        )

    user_request_count = repo.count_recent_user_requests_per_minute(user_id) if user_id else 0
    tenant_request_count = repo.count_recent_tenant_requests_per_minute(tenant_id) if tenant_id else 0
    checks["requests_per_minute"] = {
        "user": user_request_count,
        "tenant": tenant_request_count,
        "limit": policy["requests_per_minute"],
    }

    over_user_limit = user_request_count > policy["requests_per_minute"]
    over_tenant_limit = tenant_request_count > policy["requests_per_minute"]
    if over_user_limit or over_tenant_limit:
        max_retries = policy["max_preflight_retries"]
        if preflight_retry_count < max_retries:
            return _result(
                decision="retry",
                reason_code=("user_rate_limit_exceeded" if over_user_limit else "tenant_rate_limit_exceeded"),
                message="Temporarily rate-limited. Please retry shortly.",
                policy=policy,
                query_char_count=query_char_count,
                attachment_count=attachment_count,
                retry_count=preflight_retry_count,
                checks=checks,
            )
        return _result(
            decision="deny",
            reason_code="preflight_retry_limit_exceeded",
            message="Blocked request: preflight retry limit exceeded",
            policy=policy,
            query_char_count=query_char_count,
            attachment_count=attachment_count,
            retry_count=preflight_retry_count,
            checks=checks,
        )

    agent_id = str(configurable.get("agent_id") or "").strip()
    owner_id = str(configurable.get("owner_id") or "").strip()
    if agent_id and owner_id:
        activity = repo.get_open_conversation_activity(agent_id, owner_id)
    else:
        activity = None

    if activity:
        last_activity_at = _parse_dt(activity.get("last_activity_at")) or _parse_dt(activity.get("updated_at"))
        checks["conversation_activity"] = {"has_activity": bool(last_activity_at)}
        if last_activity_at:
            idle_window = timedelta(minutes=policy["conversation_idle_minutes"])
            if _now_utc() - last_activity_at > idle_window:
                confirmation = bool(configurable.get("preflight_idle_confirmed"))
                checks["conversation_activity"]["idle_timeout"] = True
                if not confirmation:
                    return _result(
                        decision="clarify",
                        reason_code="conversation_idle_timeout",
                        message="This conversation has been inactive for a while. Do you want to continue it?",
                        policy=policy,
                        query_char_count=query_char_count,
                        attachment_count=attachment_count,
                        retry_count=preflight_retry_count,
                        checks=checks,
                        context={"clarification_task": "preflight_clarification"},
                    )

    return _result(
        decision="allow",
        reason_code="admission_passed",
        message="",
        policy=policy,
        query_char_count=query_char_count,
        attachment_count=attachment_count,
        retry_count=preflight_retry_count,
        checks=checks,
    )
