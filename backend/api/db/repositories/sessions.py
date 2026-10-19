"""Conversation metadata lives on root AgentCore records."""

from __future__ import annotations

import uuid
from typing import Any

from psycopg.types.json import Jsonb

from api.db.postgres import fetch_all, fetch_one


def _valid_id(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "agent_id": str(row["agent_id"]),
        "owner_id": str(row["owner_id"]),
        "title": row.get("title") or "New chat",
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("updated_at")),
        "deleted": row.get("state") == "closed",
        "preloaded_context": row.get("preloaded_context") or {},
        "rollback_checkpoint_id": row.get("rollback_checkpoint_id"),
        "last_activity_at": _iso(row.get("last_activity_at")),
    }


class SessionRepository:
    def list_for_user(self, owner_id: str, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        if not _valid_id(owner_id):
            return []
        clause = "" if include_deleted else "AND state = 'open'"
        rows = fetch_all(f"SELECT * FROM agent_cores WHERE owner_id = %s AND parent_agent_id IS NULL {clause} ORDER BY updated_at DESC", (owner_id,))
        return [_row(row) for row in rows]

    def list_all(self, *, include_deleted: bool = False) -> list[dict[str, Any]]:
        clause = "" if include_deleted else "AND state = 'open'"
        rows = fetch_all(f"SELECT * FROM agent_cores WHERE parent_agent_id IS NULL {clause} ORDER BY updated_at DESC")
        return [_row(row) for row in rows]

    def get(self, agent_id: str) -> dict[str, Any] | None:
        if not _valid_id(agent_id):
            return None
        row = fetch_one("SELECT * FROM agent_cores WHERE agent_id = %s AND parent_agent_id IS NULL", (agent_id,))
        return _row(row) if row else None

    def create(self, *, owner_id: str, session_id: str | None = None,
               title: str | None = None,
               preloaded_context: dict[str, Any] | None = None) -> dict[str, Any]:
        from src.agent.agent_core import default_policy

        policy = default_policy({"owner_id": owner_id}).as_dict()
        row = fetch_one(
            """INSERT INTO agent_cores (owner_id, owner_type, latest_session_id, policy, policy_ceiling,
                   title, preloaded_context)
                VALUES (%s, 'user', %s, %s, %s, %s, %s) RETURNING *""",
            (owner_id, session_id, Jsonb(policy), Jsonb(policy), title or "New chat",
             Jsonb(preloaded_context or {})),
        )
        return _row(row)

    def update(self, agent_id: str, **fields: Any) -> dict[str, Any] | None:
        if not _valid_id(agent_id):
            return None
        columns = {"title": "title", "rollback_checkpoint_id": "rollback_checkpoint_id",
                   "last_activity_at": "last_activity_at", "preloaded_context": "preloaded_context"}
        clauses = []
        params: list[Any] = []
        if "deleted" in fields:
            clauses.append("state = %s")
            params.append("closed" if fields["deleted"] else "open")
        for key, column in columns.items():
            if key in fields:
                clauses.append(f"{column} = %s")
                params.append(Jsonb(fields[key] or {}) if key == "preloaded_context" else fields[key])
        if not clauses:
            return self.get(agent_id)
        params.append(agent_id)
        row = fetch_one(f"UPDATE agent_cores SET {', '.join(clauses)}, updated_at = now() WHERE agent_id = %s AND parent_agent_id IS NULL RETURNING *", tuple(params))
        return _row(row) if row else None

    def soft_delete(self, agent_id: str) -> bool:
        return self.update(agent_id, deleted=True) is not None

    def set_rollback(self, agent_id: str, checkpoint_id: str | None) -> dict[str, Any] | None:
        return self.update(agent_id, rollback_checkpoint_id=checkpoint_id)
