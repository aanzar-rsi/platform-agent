from __future__ import annotations

import uuid
from typing import Any

from api.db.postgres import fetch_all, fetch_one, get_connection


class MemoryExtractionRepository:
    def get_pending(self, *, agent_id: str, checkpoint_id: str, chunk_type: str) -> dict[str, Any] | None:
        return fetch_one(
            """SELECT * FROM memory_extraction_requests
               WHERE agent_id = %s AND checkpoint_id = %s AND chunk_type = %s
               AND state = 'APPROVAL_PENDING'""",
            (agent_id, checkpoint_id, chunk_type),
        )

    def latest(self, *, agent_id: str, checkpoint_id: str, chunk_type: str) -> dict[str, Any] | None:
        return fetch_one(
            """SELECT * FROM memory_extraction_requests
               WHERE agent_id = %s AND checkpoint_id = %s AND chunk_type = %s
               ORDER BY created_at DESC LIMIT 1""",
            (agent_id, checkpoint_id, chunk_type),
        )

    def create_pending(self, *, owner_id: str, agent_id: str, checkpoint_id: str, chunk_type: str) -> dict[str, Any]:
        with get_connection() as conn, conn.transaction():
            existing = conn.execute(
                """SELECT * FROM memory_extraction_requests
                   WHERE owner_id = %s AND agent_id = %s AND checkpoint_id = %s AND chunk_type = %s
                   AND state = 'APPROVAL_PENDING'""",
                (owner_id, agent_id, checkpoint_id, chunk_type),
            ).fetchone()
            if existing:
                return existing
            request_id = "er_" + uuid.uuid4().hex
            return conn.execute(
                """INSERT INTO memory_extraction_requests
                   (request_id, owner_id, agent_id, checkpoint_id, chunk_type, state)
                   VALUES (%s, %s, %s, %s, %s, 'APPROVAL_PENDING') RETURNING *""",
                (request_id, owner_id, agent_id, checkpoint_id, chunk_type),
            ).fetchone()

    def list_for_user(self, owner_id: str, *, state: str | None = None) -> list[dict[str, Any]]:
        if state:
            return fetch_all(
                """SELECT * FROM memory_extraction_requests
                   WHERE owner_id = %s AND state = %s ORDER BY created_at DESC LIMIT 200""",
                (owner_id, state),
            )
        return fetch_all(
            """SELECT * FROM memory_extraction_requests
               WHERE owner_id = %s ORDER BY created_at DESC LIMIT 200""",
            (owner_id,),
        )

    def get_for_user(self, owner_id: str, request_id: str) -> dict[str, Any] | None:
        return fetch_one(
            "SELECT * FROM memory_extraction_requests WHERE request_id = %s AND owner_id = %s",
            (request_id, owner_id),
        )

    def decide(self, *, owner_id: str, request_id: str, approve: bool, reason: str = "") -> dict[str, Any]:
        state = "APPROVED" if approve else "REJECTED"
        with get_connection() as conn, conn.transaction():
            request = conn.execute(
                "SELECT * FROM memory_extraction_requests WHERE request_id = %s FOR UPDATE",
                (request_id,),
            ).fetchone()
            if not request or str(request["owner_id"]) != owner_id:
                raise PermissionError("extraction_request_not_found")
            if request["state"] in {"COMPLETED", "SKIPPED"}:
                return request
            if request["state"] in {"APPROVED", "REJECTED"}:
                return request
            return conn.execute(
                """UPDATE memory_extraction_requests
                   SET state = %s, reviewed_by = %s, reason = %s, updated_at = now()
                   WHERE request_id = %s RETURNING *""",
                (state, owner_id, reason, request_id),
            ).fetchone()

    def mark_final(self, request_id: str, *, state: str) -> None:
        if state not in {"COMPLETED", "SKIPPED"}:
            raise ValueError("invalid_extraction_request_state")
        with get_connection() as conn:
            conn.execute(
                "UPDATE memory_extraction_requests SET state = %s, updated_at = now() WHERE request_id = %s",
                (state, request_id),
            )
