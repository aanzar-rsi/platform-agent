from __future__ import annotations

from typing import Any

from src.utils.postgres.db_utils import fetch_all, fetch_one


def _fetch_one(sql: str, params: tuple | dict | None = None) -> dict[str, Any] | None:
    return fetch_one(sql, params)


def _fetch_all(sql: str, params: tuple | dict | None = None) -> list[dict[str, Any]]:
    return fetch_all(sql, params)


def _normalize_permission_codes(rows: list[dict[str, Any]]) -> list[str]:
    codes: set[str] = set()
    for row in rows:
        code = str(row.get("permission_code") or "").strip()
        if code:
            codes.add(code)
    return sorted(codes)

def get_tenant_user_membership(user_id: str) -> dict[str, Any] | None:
    # Load tenant membership and role linkage for a platform user.
    return _fetch_one(
        """
        SELECT user_id, tenant_id, role_id, status
        FROM tenant_users
        WHERE user_id = %s
        """,
        (user_id,),
    )


def get_tenant_record(tenant_id: str) -> dict[str, Any] | None:
    # Load tenant status for governance gating decisions.
    return _fetch_one(
        """
        SELECT tenant_id, status, policy
        FROM tenants
        WHERE tenant_id = %s
        """,
        (tenant_id,),
    )


def get_role_record(role_id: str, tenant_id: str) -> dict[str, Any] | None:
    # Resolve the role in the same tenant as the authenticated membership.
    return _fetch_one(
        """
        SELECT role_id, tenant_id, name, status
        FROM roles
        WHERE role_id = %s
          AND tenant_id = %s
        """,
        (role_id, tenant_id),
    )


def get_active_permission_codes(role_id: str, tenant_id: str | None = None) -> list[str]:
    rows = _fetch_all(
        """
        SELECT p.permission_code
        FROM roles r
        CROSS JOIN LATERAL jsonb_array_elements_text(r.permission_ids) AS role_grant(permission_id)
        JOIN permissions p ON p.permission_id = role_grant.permission_id
                          AND p.tenant_id = r.tenant_id
        WHERE r.role_id = %s
          AND (%s::text IS NULL OR r.tenant_id = %s)
          AND r.status = 'active'
          AND p.status = 'active'
        ORDER BY p.permission_code
        """,
        (role_id, tenant_id, tenant_id),
    )
    return _normalize_permission_codes(rows)


def get_tenant_permission_catalog(tenant_id: str) -> list[dict[str, str]]:
    """All active tenant capabilities, including those the user does not hold."""
    rows = _fetch_all(
        """
        SELECT p.permission_code, p.description
        FROM permissions p
        JOIN bapi_catalog b ON b.bapi_id = p.bapi_id AND b.tenant_id = p.tenant_id
        WHERE p.tenant_id = %s AND p.status = 'active' AND b.status = 'active'
        ORDER BY p.permission_code
        """,
        (tenant_id,),
    )
    return [
        {"code": str(row["permission_code"]).strip(), "description": str(row.get("description") or "").strip()}
        for row in rows if str(row.get("permission_code") or "").strip()
    ]


def get_bapi_for_permission(tenant_id: str, permission_code: str) -> dict[str, Any] | None:
    return _fetch_one(
        """
        SELECT b.bapi_id, b.provider_key, b.bapi_name, b.description, b.effect
        FROM permissions p
        JOIN bapi_catalog b ON b.bapi_id = p.bapi_id AND b.tenant_id = p.tenant_id
        WHERE p.tenant_id = %s AND p.permission_code = %s
          AND p.status = 'active' AND b.status = 'active'
        """,
        (tenant_id, permission_code),
    )


def get_bapi_for_resource(tenant_id: str, remote_name: str) -> dict[str, Any] | None:
    return _fetch_one(
        """
        SELECT b.bapi_id, b.provider_key, b.bapi_name, b.description, b.effect,
               p.permission_id, p.permission_code
        FROM bapi_catalog b
        JOIN permissions p ON p.bapi_id = b.bapi_id AND p.tenant_id = b.tenant_id
        WHERE b.tenant_id = %s AND b.bapi_name = %s
          AND b.status = 'active' AND p.status = 'active'
        """,
        (tenant_id, remote_name),
    )


def get_current_authorization(user_id: str, agent_id: str) -> dict[str, Any] | None:
    """Read current membership, tenant, role, session-independent policy and agent version."""
    return _fetch_one(
        """
        SELECT tu.tenant_id, tu.role_id, tu.status AS membership_status,
               t.status AS tenant_status, t.policy AS tenant_policy,
               r.status AS role_status, a.policy_version AS agent_policy_version,
               a.policy AS agent_policy, a.state AS agent_state
        FROM tenant_users tu
        JOIN tenants t ON t.tenant_id = tu.tenant_id
        JOIN roles r ON r.role_id = tu.role_id AND r.tenant_id = tu.tenant_id
        JOIN agent_cores a ON a.agent_id = %s AND a.owner_id = tu.user_id
        WHERE tu.user_id = %s
        """,
        (agent_id, user_id),
    )


def get_child_lineage(agent_id: str, execution_id: str) -> dict[str, Any] | None:
    """Resolve the persisted child/parent execution pair and root owner."""
    return _fetch_one(
        """
        SELECT child.agent_id AS child_agent_id, child.parent_agent_id,
               child.state AS child_agent_state, child.policy_version AS child_policy_version,
               child.policy AS child_policy, child_run.parent_execution_id,
               child_run.state AS child_execution_state,
               child_run.policy_version AS child_execution_policy_version,
               parent_run.state AS parent_execution_state,
               parent_run.policy_version AS parent_execution_policy_version,
               parent.policy_version AS parent_policy_version,
               parent.state AS parent_agent_state, parent.owner_id AS root_user_id
        FROM agent_cores child
        JOIN agent_executions child_run ON child_run.agent_id = child.agent_id
        JOIN agent_cores parent ON parent.agent_id = child.parent_agent_id
        JOIN agent_executions parent_run
          ON parent_run.execution_id = child_run.parent_execution_id
         AND parent_run.agent_id = parent.agent_id
        WHERE child.agent_id = %s AND child_run.execution_id = %s
          AND parent.owner_type = 'user' AND parent.parent_agent_id IS NULL
        """,
        (agent_id, execution_id),
    )


def get_execution_authorization(execution_id: str, agent_id: str) -> dict[str, Any] | None:
    return _fetch_one(
        "SELECT state, policy_version FROM agent_executions WHERE execution_id = %s AND agent_id = %s",
        (execution_id, agent_id),
    )


def get_parent_decision(execution_id: str, agent_id: str, user_id: str) -> dict[str, Any] | None:
    """The parent run's last successful Preflight decision, not a client claim."""
    return _fetch_one(
        """
        SELECT tenant_id, role_id, decision, details, candidate_tools
        FROM preflight_audit
        WHERE execution_id = %s AND agent_id = %s AND user_id = %s
          AND decision IN ('allow', 'degrade')
        ORDER BY created_at DESC, audit_id DESC LIMIT 1
        """,
        (execution_id, agent_id, user_id),
    )


def get_active_auth_session(session_id: str, user_id: str) -> dict[str, Any] | None:
    # Validate that the authenticated session is active for the same user.
    return _fetch_one(
        """
        SELECT session_id, user_id, expires_at, revoked_at
        FROM auth_sessions
        WHERE session_id = %s
          AND user_id = %s
          AND revoked_at IS NULL
          AND expires_at > now()
        """,
        (session_id, user_id),
    )


def get_open_conversation_activity(agent_id: str, owner_id: str) -> dict[str, Any] | None:
    # Load last known activity for an open conversation owned by the user.
    return _fetch_one(
        """
        SELECT last_activity_at, updated_at
        FROM agent_cores
        WHERE agent_id = %s
          AND owner_id = %s
          AND state = 'open'
        """,
        (agent_id, owner_id),
    )


def count_recent_user_requests_per_minute(user_id: str) -> int:
    # Request-rate estimate based on top-level execution reservations in the last minute.
    row = _fetch_one(
        """
        SELECT count(*)::int AS request_count
        FROM agent_executions e
        JOIN agent_cores a ON a.agent_id = e.agent_id
        WHERE a.owner_id = %s
          AND a.owner_type = 'user'
          AND a.parent_agent_id IS NULL
          AND e.started_at >= now() - interval '1 minute'
        """,
        (user_id,),
    )
    return int((row or {}).get("request_count") or 0)


def count_recent_tenant_requests_per_minute(tenant_id: str) -> int:
    # Request-rate estimate for all top-level requests by users in the same tenant.
    row = _fetch_one(
        """
        SELECT count(*)::int AS request_count
        FROM agent_executions e
        JOIN agent_cores a ON a.agent_id = e.agent_id
        JOIN tenant_users tu ON tu.user_id = a.owner_id
        WHERE tu.tenant_id = %s
          AND a.owner_type = 'user'
          AND a.parent_agent_id IS NULL
          AND e.started_at >= now() - interval '1 minute'
        """,
        (tenant_id,),
    )
    return int((row or {}).get("request_count") or 0)
