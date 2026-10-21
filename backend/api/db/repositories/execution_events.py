"""Durable execution event stream persisted in PostgreSQL."""

from __future__ import annotations

import uuid
from typing import Any

from psycopg.types.json import Jsonb

from api.db.postgres import execute, get_connection


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


class ExecutionEventRepository:
    def append(
        self,
        *,
        agent_id: str,
        execution_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        current_state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event_id = str(uuid.uuid4())
        body = payload or {}
        with get_connection() as conn:
            with conn.transaction():
                execution = conn.execute(
                    """SELECT execution_id, latest_event_seq FROM agent_executions
                       WHERE execution_id = %s AND agent_id = %s FOR UPDATE""",
                    (execution_id, agent_id),
                ).fetchone()
                if not execution:
                    raise ValueError("execution_not_found")
                seq = int(execution.get("latest_event_seq") or 0) + 1
                if current_state is None:
                    conn.execute(
                        "UPDATE agent_executions SET latest_event_seq = %s WHERE execution_id = %s",
                        (seq, execution_id),
                    )
                else:
                    conn.execute(
                        """UPDATE agent_executions
                           SET latest_event_seq = %s, current_state = %s
                           WHERE execution_id = %s""",
                        (seq, Jsonb(current_state), execution_id),
                    )
                row = conn.execute(
                    """INSERT INTO agent_execution_events
                       (execution_id, sequence_number, event_id, agent_id, event_type, payload)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       RETURNING created_at""",
                    (execution_id, seq, event_id, agent_id, event_type, Jsonb(body)),
                ).fetchone()
        return {
            "v": 1,
            "type": event_type,
            "id": event_id,
            "agent_id": agent_id,
            "execution_id": execution_id,
            "seq": seq,
            "ts": _iso(row.get("created_at")) or "",
            "payload": body,
        }

    def events_after(self, execution_id: str, after_seq: int, *, limit: int = 200) -> list[dict[str, Any]]:
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT sequence_number, event_id, agent_id, event_type, payload, created_at
                   FROM agent_execution_events
                   WHERE execution_id = %s AND sequence_number > %s
                   ORDER BY sequence_number ASC
                   LIMIT %s""",
                (execution_id, max(after_seq, 0), max(1, min(limit, 2000))),
            ).fetchall()
        return [
            {
                "v": 1,
                "type": row["event_type"],
                "id": str(row["event_id"]),
                "agent_id": str(row["agent_id"]),
                "execution_id": str(execution_id),
                "seq": int(row["sequence_number"]),
                "ts": _iso(row.get("created_at")) or "",
                "payload": row.get("payload") or {},
            }
            for row in rows
        ]

    def latest_sequence(self, execution_id: str) -> int:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT latest_event_seq FROM agent_executions WHERE execution_id = %s",
                (execution_id,),
            ).fetchone()
        return int((row or {}).get("latest_event_seq") or 0)

    def cleanup_completed_older_than(self, days: int) -> int:
        return execute(
            """DELETE FROM agent_execution_events e
               USING agent_executions x
               WHERE e.execution_id = x.execution_id
                 AND x.state IN ('completed', 'failed', 'cancelled')
                 AND x.ended_at IS NOT NULL
                 AND x.ended_at < now() - (%s || ' days')::interval""",
            (max(days, 1),),
        )
