"""Persist safe immutable snapshots of Preflight decisions."""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

from psycopg.types.json import Jsonb

from src.utils.postgres import db_utils


def normalized_query_hash(query: str) -> str:
    """Hash normalized query text without retaining the original content."""

    normalized = " ".join(str(query or "").split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def write_preflight_audit(record: dict[str, Any]) -> str:
    """Insert one safe Preflight decision snapshot and return its audit ID."""

    audit_id = secrets.token_hex(12)
    db_utils.execute(
        """
        INSERT INTO preflight_audit (
            audit_id, request_id, trace_id, user_id, tenant_id, role_id, agent_id,
            execution_id, query_hash, resolved_intent, domain, permissions,
            decision, reason_code, memory_references, candidate_tools, details, retry_count
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """,
        (
            audit_id,
            record["request_id"],
            record.get("trace_id"),
            record.get("user_id"),
            record.get("tenant_id"),
            record.get("role_id"),
            record.get("agent_id"),
            record.get("execution_id"),
            record["query_hash"],
            record.get("resolved_intent"),
            record.get("domain"),
            Jsonb(list(record.get("permissions") or [])),
            record["decision"],
            record["reason_code"],
            Jsonb(list(record.get("memory_references") or [])),
            Jsonb(list(record.get("candidate_tools") or [])),
            Jsonb(dict(record.get("details") or {})),
            int(record.get("retry_count") or 0),
        ),
    )
    return audit_id
