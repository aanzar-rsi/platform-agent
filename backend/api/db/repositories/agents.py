"""Durable AgentCore identities, run reservations, and child results."""

from __future__ import annotations

import uuid
from typing import Any

from psycopg.types.json import Jsonb

from api.db.postgres import fetch_all, fetch_one, get_connection
from src.agent.policy_schema import intersect_armory, intersect_memory, normalize_armory_policy, normalize_memory_policy


class AgentRepository:
    def get(self, agent_id: str) -> dict[str, Any] | None:
        return fetch_one("SELECT * FROM agent_cores WHERE agent_id = %s", (agent_id,))

    def for_agent(self, agent_id: str, owner_id: str, session_id: str | None = None) -> dict:
        with get_connection() as conn:
            with conn.transaction():
                row = conn.execute(
                    """UPDATE agent_cores SET latest_session_id = COALESCE(%s, latest_session_id)
                       WHERE agent_id = %s AND owner_id = %s AND owner_type = 'user'
                       AND parent_agent_id IS NULL AND state = 'open' RETURNING *""",
                    (session_id, agent_id, owner_id),
                ).fetchone()
                if row is None:
                    raise PermissionError("Agent not found or not owned")
                return row

    def child(self, parent_id: str, policy: dict, *, max_depth: int,
              parent_execution_id: str | None = None, max_children: int | None = None) -> dict:
        with get_connection() as conn:
            with conn.transaction():
                parent = conn.execute(
                    "SELECT * FROM agent_cores WHERE agent_id = %s FOR UPDATE", (parent_id,)
                ).fetchone()
                if not parent or parent["state"] != "open" or parent["depth"] >= max_depth:
                    raise ValueError("child_not_allowed")
                if parent_execution_id is not None:
                    running = conn.execute(
                        "SELECT 1 FROM agent_executions WHERE execution_id = %s AND agent_id = %s AND state = 'running'",
                        (parent_execution_id, parent_id),
                    ).fetchone()
                    if not running:
                        raise ValueError("parent_not_running")
                    if max_children is not None:
                        count = conn.execute(
                            "SELECT count(*) AS n FROM agent_executions WHERE parent_execution_id = %s", (parent_execution_id,)
                        ).fetchone()["n"]
                        if count >= max_children:
                            raise ValueError("child_limit")
                inherited = parent["policy"]
                inherited_armory = normalize_armory_policy((inherited or {}).get("armory") or {})
                inherited_memory = normalize_memory_policy((inherited or {}).get("memory") or {})
                requested_armory = normalize_armory_policy((policy or {}).get("armory") or {})
                requested_memory = normalize_memory_policy((policy or {}).get("memory") or {})
                if intersect_armory(inherited_armory, requested_armory, inherited_armory) != requested_armory:
                    raise PermissionError("child_policy_expansion_denied")
                if intersect_memory(inherited_memory, requested_memory, inherited_memory) != requested_memory:
                    raise PermissionError("child_tenant_denied")
                if policy.get("guardrails") != inherited["guardrails"] or policy.get("observability") != inherited["observability"]:
                    raise PermissionError("child_immutable_policy_denied")
                child = conn.execute(
                    """INSERT INTO agent_cores
                       (owner_id, owner_type, parent_agent_id, latest_session_id, policy, depth)
                       VALUES (%s, 'agent', %s, %s, %s, %s) RETURNING *""",
                    (parent_id, parent_id, parent["latest_session_id"],
                      Jsonb(policy), parent["depth"] + 1),
                ).fetchone()
                return child

    def start_execution(self, agent_id: str, *, execution_id: str | None = None,
                        parent_execution_id: str | None = None) -> dict:
        execution_id = execution_id or str(uuid.uuid4())
        with get_connection() as conn:
            with conn.transaction():
                agent = conn.execute(
                    "SELECT * FROM agent_cores WHERE agent_id = %s FOR UPDATE", (agent_id,)
                ).fetchone()
                if not agent or agent["state"] != "open":
                    raise ValueError("agent_closed")
                active = conn.execute(
                    "SELECT 1 FROM agent_executions WHERE agent_id = %s AND state IN ('running', 'interrupted')",
                    (agent_id,),
                ).fetchone()
                if active:
                    raise ValueError("already_running")
                return conn.execute(
                    """INSERT INTO agent_executions (execution_id, agent_id, parent_execution_id, state, policy_version)
                       VALUES (%s, %s, %s, 'running', %s) RETURNING *""",
                    (execution_id, agent_id, parent_execution_id, agent["policy_version"]),
                ).fetchone()

    def execution(self, execution_id: str) -> dict | None:
        return fetch_one("SELECT * FROM agent_executions WHERE execution_id = %s", (execution_id,))

    def active_execution(self, agent_id: str) -> dict | None:
        return fetch_one(
            "SELECT * FROM agent_executions WHERE agent_id = %s AND state IN ('running', 'interrupted')",
            (agent_id,),
        )

    def finish_execution(self, execution_id: str, state: str, *, result: str | None = None,
                         error: str | None = None) -> dict:
        if state not in {"interrupted", "running", "completed", "failed", "cancelled"}:
            raise ValueError("invalid_run_state")
        with get_connection() as conn:
            with conn.transaction():
                row = conn.execute("SELECT * FROM agent_executions WHERE execution_id = %s FOR UPDATE", (execution_id,)).fetchone()
                allowed = {"running": {"running", "interrupted", "completed", "failed", "cancelled"},
                           "interrupted": {"running", "cancelled", "failed"}}
                if not row or state not in allowed.get(row["state"], set()):
                    raise ValueError("invalid_run_transition")
                return conn.execute(
                    """UPDATE agent_executions SET state = %s, result = COALESCE(%s, result),
                        error = COALESCE(%s, error), ended_at = CASE WHEN %s IN ('running', 'interrupted')
                        THEN NULL ELSE now() END WHERE execution_id = %s RETURNING *""",
                    (state, result, error, state, execution_id),
                ).fetchone()

    def update_policy(self, agent_id: str, field: str, scope: dict, *, uid: str,
                      expected_version: int) -> dict:
        if field not in {"armory", "memory"}:
            raise ValueError("immutable_policy")
        with get_connection() as conn:
            with conn.transaction():
                agent = conn.execute(
                    "SELECT * FROM agent_cores WHERE agent_id = %s FOR UPDATE", (agent_id,)
                ).fetchone()
                if not agent or agent["state"] != "open":
                    raise ValueError("agent_closed")
                if agent["policy_version"] != expected_version:
                    raise ValueError("policy_conflict")
                if str(agent["owner_id"]) != str(uid) or agent["owner_type"] != "user":
                    raise PermissionError("policy_update_denied")
                ceiling = (agent.get("policy_ceiling") or agent["policy"])[field]
                if field == "memory":
                    if intersect_memory(ceiling, scope, ceiling) != normalize_memory_policy(scope):
                        raise PermissionError("memory_scope_expansion_denied")
                if field == "armory":
                    if intersect_armory(ceiling, scope, ceiling) != normalize_armory_policy(scope):
                        raise PermissionError("armory_scope_expansion_denied")
                    if normalize_armory_policy(ceiling).get("confirm_tools", True) and not normalize_armory_policy(scope).get("confirm_tools", True):
                        raise PermissionError("confirmation_required")
                policy = dict(agent["policy"])
                policy[field] = scope
                return conn.execute(
                    """UPDATE agent_cores SET policy = %s,
                        policy_ceiling = COALESCE(policy_ceiling, policy), policy_version = policy_version + 1
                       WHERE agent_id = %s RETURNING *""",
                    (Jsonb(policy), agent_id),
                ).fetchone()

    def close(self, agent_id: str) -> dict:
        with get_connection() as conn:
            with conn.transaction():
                agent = conn.execute(
                    "SELECT * FROM agent_cores WHERE agent_id = %s FOR UPDATE", (agent_id,)
                ).fetchone()
                if not agent:
                    raise ValueError("agent_not_found")
                if agent["state"] == "closed":
                    return agent
                busy = conn.execute(
                    "SELECT 1 FROM agent_executions WHERE agent_id = %s AND state IN ('running', 'interrupted')",
                    (agent_id,),
                ).fetchone()
                if busy:
                    raise ValueError("agent_busy")
                return conn.execute(
                    "UPDATE agent_cores SET state = 'closed', closed_at = now() WHERE agent_id = %s RETURNING *",
                    (agent_id,),
                ).fetchone()

    def append_message(self, agent_id: str, execution_id: str, content: str, *,
                       sender_type: str, sender_id: str | None = None,
                       child_agent_id: str | None = None, visible_to_user: bool = True) -> dict:
        with get_connection() as conn:
            with conn.transaction():
                agent = conn.execute(
                    "SELECT state FROM agent_cores WHERE agent_id = %s FOR UPDATE", (agent_id,)
                ).fetchone()
                if not agent or agent["state"] != "open":
                    raise ValueError("agent_closed")
                return conn.execute(
                    """INSERT INTO agent_messages
                       (agent_id, execution_id, sender_type, sender_id, content, child_agent_id, visible_to_user)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING *""",
                    (agent_id, execution_id, sender_type, sender_id, content, child_agent_id, visible_to_user),
                ).fetchone()

    def messages(self, agent_id: str) -> list[dict]:
        return fetch_all(
            "SELECT * FROM agent_messages WHERE agent_id = %s ORDER BY created_at, message_id",
            (agent_id,),
        )

    def children(self, parent_execution_id: str) -> list[dict]:
        return fetch_all(
            """SELECT a.*, r.execution_id, r.state AS execution_state, r.result, r.error FROM agent_cores a
               JOIN agent_executions r ON r.agent_id = a.agent_id WHERE r.parent_execution_id = %s""",
            (parent_execution_id,),
        )

    def child_outcome(self, parent_id: str, parent_execution_id: str, child_id: str) -> dict | None:
        return fetch_one(
            """SELECT r.* FROM agent_executions r JOIN agent_cores a ON a.agent_id = r.agent_id
               WHERE r.agent_id = %s AND r.parent_execution_id = %s AND a.parent_agent_id = %s""",
            (child_id, parent_execution_id, parent_id),
        )

    def latest_execution(self, agent_id: str) -> dict | None:
        return fetch_one(
            "SELECT * FROM agent_executions WHERE agent_id = %s ORDER BY started_at DESC LIMIT 1",
            (agent_id,),
        )
