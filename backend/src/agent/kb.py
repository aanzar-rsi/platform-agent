"""Authorized, versioned memory KB. PostgreSQL is authoritative; Chroma is an index."""

from __future__ import annotations

import hashlib
import logging
import math
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any

from psycopg.types.json import Jsonb

from api.db.postgres import get_connection
from src.config import settings
from src.models.embeddings import embed_text
from src.agent.policy_schema import memory_action_allowed, normalize_memory_policy
from src.utils.trace import emit, in_run, span

logger = logging.getLogger(__name__)
SCOPES = ("USER", "TENANT", "AGENT")
TYPES = {"resource", "user_preference", "user_details", "tenant_details", "workflow",
         "troubleshooting", "anti_pattern"}
SENSITIVITIES = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}
COLLECTIONS = {"USER": "memory-user-v1", "TENANT": "memory-tenant-v1", "AGENT": "memory-agent-v1"}
_chroma = None
_chroma_failed = False


def _chroma_available() -> bool:
    global _chroma_failed
    if _chroma_failed:
        return False
    try:
        _collection("USER")
        return True
    except Exception as exc:
        _chroma_failed = True
        logger.warning("Chroma unavailable; memory index operations skipped (%s: %s)",
                       type(exc).__name__, exc)
        return False


def chroma_status() -> bool:
    """Return whether Chroma is reachable for memory indexing."""
    return _chroma_available()


def _id(prefix: str) -> str:
    return prefix + uuid.uuid4().hex


def _iso(value: Any) -> str | None:
    return value.isoformat() if value else None


def _model() -> str:
    return f"{settings.embed_method}:{settings.embed_model_id if settings.embed_method == 'hf' else settings.embed_dimensions}"


def _vector(text: str) -> list[float]:
    vector = embed_text(text)
    if not vector or not all(math.isfinite(x) for x in vector) or not any(vector):
        raise ValueError("invalid_embedding")
    return vector


def _compatible(collection, vector: list[float]) -> None:
    metadata = collection.metadata or {}
    model, dimensions = metadata.get("embedding_model"), metadata.get("embedding_dimensions")
    if model and (model != _model() or dimensions != len(vector)):
        raise ValueError("embedding_model_mismatch")
    if not model:
        if collection.count():
            raise ValueError("embedding_model_unknown_rebuild_required")
        collection.modify(metadata={**{key: value for key, value in metadata.items() if key != "hnsw:space"},
                                    "embedding_model": _model(), "embedding_dimensions": len(vector)})


def _uuid(value: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (ValueError, TypeError, AttributeError) as exc:
        raise PermissionError("memory_identity_denied") from exc


def _collection(scope: str):
    global _chroma
    if _chroma is None:
        import chromadb

        import os

        server = os.environ.get("MEMORY_CHROMA_HOST")
        if server:
            _chroma = chromadb.HttpClient(host=server, port=int(os.environ.get("MEMORY_CHROMA_PORT", "8000")))
        else:
            path = settings.data_root / "memory-chroma"
            path.mkdir(parents=True, exist_ok=True)
            _chroma = chromadb.PersistentClient(path=str(path))
    return _chroma.get_or_create_collection(COLLECTIONS[scope], metadata={"hnsw:space": "cosine"})


@contextmanager
def _trace(action: str, scope: str, **data):
    if in_run():
        trace_data = {"scope": scope, **data}
        with span("memory", action, component="kb", data=trace_data):
            yield trace_data
    else:
        yield data


def _deny(action: str, scope: str, reason: str) -> None:
    if in_run():
        emit(f"memory.{action}.denied", status="denied", error=PermissionError(reason),
             component="kb", data={"scope": scope})
    raise PermissionError(reason)


def _authorized(
    uid: str,
    policy: dict,
    scope: str,
    action: str,
    *,
    role: str = "user",
    chunk_type: str | None = None,
    promote_target: str | None = None,
) -> str | None:
    if (not isinstance(uid, str) or not uid.strip() or scope not in SCOPES or
            not memory_action_allowed(policy, action=action, scope=scope, chunk_type=chunk_type,
                                      promote_target=promote_target)):
        _deny("retrieve" if action == "read" else "write", scope, "memory_scope_denied")
    try:
        _uuid(uid)
    except PermissionError:
        _deny("retrieve" if action == "read" else "write", scope, "memory_identity_denied")
    tenant = policy.get("tenant_id")
    if scope == "TENANT" and (not isinstance(tenant, str) or not tenant.strip()):
        _deny("retrieve" if action == "read" else "write", scope, "tenant_scope_denied")
    if action == "write" and scope != "USER" and role != "admin":
        _deny("write", scope, "publisher_required")
    return tenant if scope == "TENANT" else None


def _audit(conn, action: str, uid: str | None, chunk_id: str | None = None,
           version_id: str | None = None, request_id: str | None = None, details: dict | None = None):
    conn.execute("""INSERT INTO memory_audit (action, actor_user_id, chunk_id, version_id, request_id, details)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                 (action, uid, chunk_id, version_id, request_id, Jsonb(details or {})))


def _queue(conn, version_id: str, operation: str):
    conn.execute("""INSERT INTO memory_index_outbox (version_id, operation) VALUES (%s, %s)
                    ON CONFLICT (version_id) DO UPDATE SET operation = EXCLUDED.operation,
                    attempts = 0, last_error = NULL""", (version_id, operation))


def _row(conn, chunk_id: str, *, lock: bool = False):
    return conn.execute("""SELECT c.*, v.content, v.search_text, v.version_id, v.status AS version_status,
        v.expires_at, v.created_at AS version_created_at, v.embedding_model, v.embedding_dimensions,
        v.metadata, v.sensitivity FROM memory_chunks c JOIN memory_versions v
        ON v.version_id = c.active_version_id WHERE c.chunk_id = %s""" + (" FOR UPDATE OF c" if lock else ""),
        (chunk_id,)).fetchone()


def _visible(row: dict | None, uid: str, policy: dict) -> bool:
    if not row or row["status"] != "ACTIVE" or row["version_status"] != "ACTIVE":
        return False
    if row["expires_at"] and row["expires_at"] <= datetime.now(timezone.utc):
        return False
    scope = row["scope"]
    if scope not in SCOPES or not memory_action_allowed(
        policy, action="read", scope=scope, chunk_type=row.get("chunk_type")
    ):
        return False
    if scope == "USER":
        return str(row["owner_user_id"]) == uid
    if scope == "TENANT":
        return bool(policy.get("tenant_id")) and row["tenant_id"] == policy["tenant_id"]
    return True


def _public(row: dict) -> dict:
    metadata = row["metadata"] or {}
    safe_metadata = {key: metadata[key] for key in (
        "semantic_key", "evidence_kind", "decision_stage", "intent", "current_subgoal",
        "resource_domain", "resource_type", "resource_name", "guidance_kind", "workflow_kind",
        "failure_kind", "anti_pattern_kind", "preference_kind", "detail_kind", "preconditions",
        "next_action", "retrieval_cues", "outcome",
    ) if key in metadata}
    return {"chunk_id": row["chunk_id"], "chunk_type": row["chunk_type"], "scope": row["scope"],
            "memory_weight": row["memory_weight"], "status": row["status"],
            "active_version_id": row["version_id"], "content": row["content"],
            "updated_at": _iso(row["updated_at"]), "created_at": _iso(row["created_at"]),
            "metadata": safe_metadata}


def _conflicts(conn, scope: str, tenant: str | None, content: str) -> bool:
    """Exact contradictions in the same publication scope require human resolution."""
    negated = content.removeprefix("Do not ") if content.startswith("Do not ") else "Do not " + content
    return bool(conn.execute("""SELECT 1 FROM memory_chunks c JOIN memory_versions v
        ON c.active_version_id = v.version_id WHERE c.scope = %s AND c.tenant_id IS NOT DISTINCT FROM %s
        AND c.status = 'ACTIVE' AND v.status = 'ACTIVE' AND lower(v.content) = lower(%s)
        LIMIT 1""", (scope, tenant, negated)).fetchone())


def _publication_allowed(policy: dict, *, chunk_type: str, target_scope: str) -> bool:
    normalized = normalize_memory_policy(policy)
    chunk = normalized.get("chunks", {}).get(chunk_type) or {}
    return bool(
        target_scope in normalized.get("publish", [])
        and target_scope in normalized.get("promote", [])
        and target_scope in chunk.get("promote", [])
        and chunk.get("allow_admin_promotion", False)
    )


def _active_for_uid(conn, uid: str, source_id: str) -> dict | None:
    found = conn.execute("SELECT chunk_id FROM memory_chunks WHERE source_id = %s AND owner_user_id = %s",
                         (source_id, uid)).fetchone()
    return _row(conn, found["chunk_id"]) if found else None


def write(uid: str, policy: dict, content: str, *, chunk_type: str = "workflow", scope: str = "USER",
          search_text: str | None = None, sensitivity: str = "INTERNAL", memory_weight: float = 0.5,
          chunk_id: str | None = None, source_id: str | None = None, conversation_id: str | None = None,
          message_ids: list[str] | None = None, metadata: dict | None = None, role: str = "user") -> dict:
    if scope != "USER":
        _deny("write", scope, "promotion_required")
    tenant = _authorized(uid, policy, scope, "write", role=role, chunk_type=chunk_type)
    if chunk_type not in TYPES or sensitivity not in SENSITIVITIES or not isinstance(content, str) or not content.strip():
        raise ValueError("invalid_memory_chunk")
    if not isinstance(memory_weight, (int, float)) or not 0 <= memory_weight <= 1:
        raise ValueError("invalid_memory_weight")
    if scope == "AGENT" and sensitivity != "PUBLIC":
        raise ValueError("global_memory_must_be_public")
    if not isinstance(message_ids or [], list):
        raise ValueError("invalid_message_ids")
    if source_id and (not isinstance(source_id, str) or not source_id.strip()):
        raise ValueError("invalid_source_id")
    text = (search_text or content).strip()
    vector = _vector(text)
    version_id = _id("v_")
    with _trace("write", scope, policy_version=policy.get("version")):
        with get_connection() as conn, conn.transaction():
            if source_id:
                occupied = conn.execute("SELECT owner_user_id FROM memory_chunks WHERE source_id = %s", (source_id,)).fetchone()
                if occupied and str(occupied["owner_user_id"]) != uid:
                    _deny("write", scope, "memory_scope_denied")
                row = _active_for_uid(conn, uid, source_id)
                if row:
                    if not _visible(row, uid, {"read": [scope], "tenant_id": tenant}):
                        _deny("write", scope, "memory_scope_denied")
                    return _public(row)
            previous = _row(conn, chunk_id, lock=True) if chunk_id else None
            if chunk_id and (not previous or previous["status"] != "ACTIVE" or
                             previous["scope"] != scope or previous["chunk_type"] != chunk_type or
                             (scope == "USER" and str(previous["owner_user_id"]) != uid) or
                             (scope == "TENANT" and previous["tenant_id"] != tenant)):
                _deny("write", scope, "memory_scope_denied")
            if previous and previous["embedding_model"] != _model():
                raise ValueError("embedding_model_mismatch")
            chunk_id = chunk_id or _id("chk_")
            if not previous:
                conn.execute("""INSERT INTO memory_chunks
                    (chunk_id, chunk_type, scope, owner_user_id, tenant_id, memory_weight, source_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (chunk_id, chunk_type, scope, uid if scope == "USER" else None, tenant, memory_weight, source_id))
            conn.execute("""INSERT INTO memory_versions
                (version_id, chunk_id, content, search_text, content_hash, embedding, embedding_model,
                  embedding_dimensions, created_by, source_agent_id, source_message_ids, sensitivity, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (version_id, chunk_id, content, text, "sha256:" + hashlib.sha256(content.encode()).hexdigest(),
                 Jsonb(vector), _model(), len(vector), uid, conversation_id, Jsonb(message_ids or []),
                 sensitivity, Jsonb(metadata or {})))
            if previous:
                conn.execute("UPDATE memory_versions SET status = 'SUPERSEDED' WHERE version_id = %s",
                             (previous["version_id"],))
                _queue(conn, previous["version_id"], "DELETE")
            conn.execute("""UPDATE memory_chunks SET active_version_id = %s, memory_weight = %s,
                updated_at = now() WHERE chunk_id = %s""", (version_id, memory_weight, chunk_id))
            _queue(conn, version_id, "UPSERT")
            _audit(conn, "memory.write", uid, chunk_id, version_id)
            result = _public(_row(conn, chunk_id))
    sync_index()
    return result


def sync_index(limit: int = 100) -> int:
    """Replay PostgreSQL projection tasks. A failed task stays queued for retry."""
    if not _chroma_available():
        return 0
    completed = 0
    with get_connection() as conn:
        tasks = conn.execute("""SELECT o.version_id, o.operation, c.scope, c.chunk_type, c.owner_user_id, c.tenant_id,
            c.active_version_id, c.status, v.search_text, v.embedding, v.embedding_model,
            v.embedding_dimensions, v.status AS version_status, v.expires_at, v.chunk_id
            FROM memory_index_outbox o JOIN memory_versions v ON v.version_id = o.version_id
            JOIN memory_chunks c ON c.chunk_id = v.chunk_id ORDER BY o.created_at LIMIT %s""", (limit,)).fetchall()
    for task in tasks:
        try:
            collection = _collection(task["scope"])
            if (task["operation"] == "DELETE" or task["status"] != "ACTIVE" or
                    task["version_status"] != "ACTIVE" or task["active_version_id"] != task["version_id"] or
                    (task["expires_at"] and task["expires_at"] <= datetime.now(timezone.utc))):
                collection.delete(ids=[task["version_id"]])
            else:
                if task["embedding_model"] != _model() or task["embedding_dimensions"] != len(task["embedding"]):
                    raise ValueError("embedding_model_mismatch")
                meta = {"chunk_id": task["chunk_id"], "scope": task["scope"], "status": "ACTIVE",
                        "embedding_model": task["embedding_model"], "chunk_type": task["chunk_type"]}
                _compatible(collection, task["embedding"])
                if task["scope"] == "USER":
                    meta["owner_user_id"] = str(task["owner_user_id"])
                if task["scope"] == "TENANT":
                    meta["tenant_id"] = task["tenant_id"]
                collection.upsert(ids=[task["version_id"]], documents=[task["search_text"]],
                                  embeddings=[task["embedding"]], metadatas=[meta])
            with get_connection() as conn:
                conn.execute("DELETE FROM memory_index_outbox WHERE version_id = %s AND operation = %s",
                             (task["version_id"], task["operation"]))
            completed += 1
        except Exception as exc:
            logger.warning("KB index retry pending for %s", task["version_id"], exc_info=True)
            with get_connection() as conn:
                conn.execute("""UPDATE memory_index_outbox SET attempts = attempts + 1,
                    last_error = %s WHERE version_id = %s""", (type(exc).__name__, task["version_id"]))
    return completed


def refresh_index() -> int:
    """Periodic reconciliation for expired versions and indexing retries."""
    with get_connection() as conn, conn.transaction():
        conn.execute("""INSERT INTO memory_index_outbox (version_id, operation)
            SELECT v.version_id, 'DELETE' FROM memory_versions v
            JOIN memory_chunks c ON c.chunk_id = v.chunk_id
            WHERE c.active_version_id = v.version_id AND
            (v.expires_at <= now() OR c.status != 'ACTIVE' OR v.status != 'ACTIVE')
            ON CONFLICT (version_id) DO UPDATE SET operation = 'DELETE'""")
    return sync_index()


def audit_log(uid: str, role: str, limit: int = 100) -> list[dict]:
    if role != "admin":
        raise PermissionError("admin_required")
    _uuid(uid)
    with get_connection() as conn:
        rows = conn.execute("""SELECT action, actor_user_id, chunk_id, version_id, request_id,
            created_at FROM memory_audit ORDER BY audit_id DESC LIMIT %s""", (min(max(limit, 1), 200),)).fetchall()
    return [{**row, "actor_user_id": str(row["actor_user_id"]) if row["actor_user_id"] else None,
             "created_at": _iso(row["created_at"])} for row in rows]


def rebuild_index() -> int:
    with get_connection() as conn, conn.transaction():
        conn.execute("""INSERT INTO memory_index_outbox (version_id, operation)
            SELECT v.version_id, CASE WHEN c.active_version_id = v.version_id AND c.status = 'ACTIVE'
                AND v.status = 'ACTIVE' AND (v.expires_at IS NULL OR v.expires_at > now())
                THEN 'UPSERT' ELSE 'DELETE' END
            FROM memory_versions v JOIN memory_chunks c ON c.chunk_id = v.chunk_id
            ON CONFLICT (version_id) DO UPDATE SET operation = EXCLUDED.operation""")
    return sync_index(limit=100000)


def search(uid: str, policy: dict, query: str, *, top_k: int = 5,
           chunk_types: set[str] | None = None) -> list[dict]:
    if not isinstance(uid, str) or not uid.strip():
        _deny("retrieve", "USER", "memory_identity_denied")
    try:
        _uuid(uid)
    except PermissionError:
        _deny("retrieve", "USER", "memory_identity_denied")
    if not isinstance(query, str) or not query.strip() or top_k < 1 or top_k > 100:
        raise ValueError("invalid_memory_query")
    allowed_types = {
        chunk_type for chunk_type in (chunk_types or TYPES)
        if chunk_type in TYPES and any(memory_action_allowed(policy, action="read", scope=scope,
                                                               chunk_type=chunk_type)
                                   for scope in SCOPES)
    }
    if not allowed_types:
        return []
    scopes = [s for s in SCOPES if s in policy.get("read", []) and (s != "TENANT" or policy.get("tenant_id"))]
    if not scopes:
        return []
    if not _chroma_available():
        return []
    with _trace(
        "retrieve", ",".join(scopes), top_k=top_k,
        query_hash=hashlib.sha256(query.encode()).hexdigest(),
        policy_version=policy.get("version"), scope_count=len(scopes), returned_count=0,
    ) as trace_data:
        vector = _vector(query)
        candidates: list[tuple[str, float, str]] = []
        for scope in scopes:
            filters = ([{"owner_user_id": uid}] if scope == "USER" else
                       [{"tenant_id": policy["tenant_id"]}] if scope == "TENANT" else [])
            filters.append({"chunk_type": {"$in": sorted(allowed_types)}})
            where = filters[0] if len(filters) == 1 else {"$and": filters}
            collection = _collection(scope)
            _compatible(collection, vector)
            result = collection.query(query_embeddings=[vector], n_results=top_k,
                                               where=where, include=["distances"])
            for version_id, distance in zip(result["ids"][0], result["distances"][0]):
                candidates.append((version_id, 1 - distance, scope))
        hits = []
        with get_connection() as conn:
            for version_id, similarity, scope in candidates:
                row = conn.execute("""SELECT c.*, v.version_id, v.content, v.metadata,
                    v.status AS version_status, v.expires_at, v.created_at AS version_created_at
                    FROM memory_versions v JOIN memory_chunks c ON c.chunk_id = v.chunk_id
                    WHERE v.version_id = %s AND c.active_version_id = v.version_id""", (version_id,)).fetchone()
                if not _visible(row, uid, policy) or row["scope"] != scope or row["version_id"] != version_id:
                    continue
                if row["chunk_type"] not in allowed_types:
                    continue
                hit = _public(row)
                age = max(0, (datetime.now(timezone.utc) - row["updated_at"]).days)
                hit["score"] = similarity + {"USER": 0.15, "TENANT": 0.08, "AGENT": 0}[scope] + (
                    0.1 / (1 + age / 30)) + row["memory_weight"] * 0.1
                hits.append(hit)
        hits.sort(key=lambda x: x["score"], reverse=True)
        selected = hits[:top_k]
        trace_data["returned_count"] = len(selected)
        return selected


def find_user_memory(uid: str, policy: dict, *, chunk_type: str,
                     semantic_key: str) -> dict | None:
    """Find one authorized active USER chunk by its normalized semantic key."""
    _authorized(uid, policy, "USER", "read", chunk_type=chunk_type)
    with get_connection() as conn:
        row = conn.execute("""SELECT c.*, v.version_id, v.content, v.metadata,
            v.status AS version_status, v.expires_at FROM memory_chunks c JOIN memory_versions v
            ON c.active_version_id = v.version_id WHERE c.scope = 'USER' AND c.owner_user_id = %s
            AND c.chunk_type = %s AND c.status = 'ACTIVE' AND v.status = 'ACTIVE'
            AND v.metadata->>'semantic_key' = %s ORDER BY c.updated_at DESC LIMIT 1""",
            (uid, chunk_type, semantic_key)).fetchone()
    return _public(row) if row and _visible(row, uid, policy) else None


def evidence_exists(uid: str, policy: dict, evidence_id: str) -> bool:
    """Check append-only version provenance so branch retries are idempotent."""
    _authorized(uid, policy, "USER", "read")
    with get_connection() as conn:
        return bool(conn.execute("""SELECT 1 FROM memory_versions v JOIN memory_chunks c
            ON c.chunk_id = v.chunk_id WHERE c.owner_user_id = %s
            AND v.metadata->>'evidence_id' = %s
            UNION ALL
            SELECT 1 FROM memory_audit WHERE actor_user_id = %s
            AND details->>'evidence_id' = %s LIMIT 1""",
            (uid, evidence_id, uid, evidence_id)).fetchone())


def reinforce(uid: str, policy: dict, chunk_id: str, *, amount: float = 0.05,
              evidence_id: str | None = None) -> dict:
    """Increase confidence without creating a duplicate content version."""
    _authorized(uid, policy, "USER", "write")
    with get_connection() as conn, conn.transaction():
        row = _row(conn, chunk_id, lock=True)
        if not row or not _visible(row, uid, {**policy, "read": list(set(policy.get("read", [])) | {"USER"})}):
            _deny("write", "USER", "memory_scope_denied")
        weight = min(1.0, float(row["memory_weight"]) + max(0.0, amount))
        conn.execute("UPDATE memory_chunks SET memory_weight = %s, updated_at = now() WHERE chunk_id = %s",
                     (weight, chunk_id))
        details = {"memory_weight": weight}
        if evidence_id:
            details["evidence_id"] = evidence_id
        _audit(conn, "memory.reinforce", uid, chunk_id, row["version_id"], details=details)
        result = _public(_row(conn, chunk_id))
    return result


def list_chunks(uid: str, policy: dict, *, limit: int = 100, scope: str | None = None) -> list[dict]:
    if scope is not None:
        _authorized(uid, policy, scope, "read")
    if not isinstance(uid, str) or not uid.strip():
        _deny("retrieve", scope or "USER", "memory_identity_denied")
    try:
        _uuid(uid)
    except PermissionError:
        _deny("retrieve", scope or "USER", "memory_identity_denied")
    if not 1 <= limit <= 200:
        raise ValueError("invalid_limit")
    scopes = [scope] if scope else [s for s in SCOPES if s in policy.get("read", []) and
                                   (s != "TENANT" or policy.get("tenant_id"))]
    if not scopes:
        return []
    with _trace("retrieve", ",".join(scopes), top_k=limit, policy_version=policy.get("version")):
        with get_connection() as conn:
            rows = conn.execute("""SELECT c.*, v.version_id, v.content, v.metadata,
                v.status AS version_status, v.expires_at FROM memory_chunks c JOIN memory_versions v
                ON c.active_version_id = v.version_id WHERE c.scope = ANY(%s)
                AND c.status = 'ACTIVE' AND v.status = 'ACTIVE'
                AND (v.expires_at IS NULL OR v.expires_at > now())
                AND ((c.scope = 'USER' AND c.owner_user_id = %s) OR
                     (c.scope = 'TENANT' AND c.tenant_id = %s) OR c.scope = 'AGENT')
                ORDER BY c.updated_at DESC LIMIT %s""", (scopes, uid, policy.get("tenant_id"), limit)).fetchall()
        return [_public(row) for row in rows if _visible(row, uid, policy)]


def get_chunk(uid: str, policy: dict, chunk_id: str) -> dict:
    if not isinstance(uid, str) or not uid.strip():
        _deny("retrieve", "USER", "memory_identity_denied")
    _uuid(uid)
    with _trace("retrieve", "USER", policy_version=policy.get("version")):
        with get_connection() as conn:
            row = _row(conn, chunk_id)
        if not row or not _visible(row, uid, policy):
            raise KeyError("chunk_not_found")
        return _public(row)


def history(uid: str, policy: dict, chunk_id: str) -> dict:
    with _trace("retrieve", "USER", policy_version=policy.get("version")):
        with get_connection() as conn:
            row = _row(conn, chunk_id)
            if not row:
                raise KeyError("chunk_not_found")
            _authorized(uid, policy, row["scope"], "read")
            if not _visible(row, uid, policy):
                _deny("retrieve", row["scope"], "memory_scope_denied")
            versions = conn.execute("SELECT * FROM memory_versions WHERE chunk_id = %s ORDER BY created_at, version_id",
                                    (chunk_id,)).fetchall()
            versions.sort(key=lambda version: (version["version_id"] == row["version_id"], version["created_at"]))
        result = {**_public(row), "owner_user_id": str(row["owner_user_id"]) if row["owner_user_id"] else None,
                  "tenant_id": row["tenant_id"], "schema_version": 1, "versions": []}
        if row["scope"] == "AGENT":
            result["owner_user_id"] = None
        for version in versions:
            entry = {key: _iso(value) if key in {"created_at", "expires_at", "revalidated_at"} else value
                     for key, value in version.items() if key != "embedding" and
                     (row["scope"] == "USER" or key not in {"source_agent_id", "source_message_ids",
                                                              "created_by", "promoted_from_version_id", "metadata"})}
            if row["scope"] == "USER":
                entry["created_by"] = str(version["created_by"]) if version["created_by"] else None
            result["versions"].append(entry)
        result["active_version_index"] = next(i for i, v in enumerate(versions)
                                               if v["version_id"] == row["version_id"])
        return result


def request_promotion(uid: str, policy: dict, source_chunk_id: str, target_scope: str, *,
                      idempotency_key: str, proposed_content: str | None = None) -> dict:
    _uuid(uid)
    if target_scope not in {"TENANT", "AGENT"} or not idempotency_key or len(idempotency_key) > 160:
        raise ValueError("invalid_promotion_request")
    with get_connection() as conn, conn.transaction():
        existing = conn.execute("""SELECT * FROM memory_promotion_requests WHERE requested_by = %s
            AND idempotency_key = %s""", (uid, idempotency_key)).fetchone()
        if existing:
            if (existing["source_chunk_id"] != source_chunk_id or existing["to_scope"] != target_scope or
                    (proposed_content is not None and existing["proposed_content"] != proposed_content)):
                raise ValueError("idempotency_conflict")
            return _request_view(existing)
        row = _row(conn, source_chunk_id, lock=True)
        if not row or not _visible(row, uid, policy):
            raise PermissionError("memory_scope_denied")
        if not memory_action_allowed(
            policy, action="promote", scope=row["scope"], chunk_type=row["chunk_type"],
            promote_target=target_scope,
        ):
            raise PermissionError("promotion_policy_denied")
        if (row["scope"], target_scope) not in {("USER", "TENANT"), ("USER", "AGENT"), ("TENANT", "AGENT")}:
            raise ValueError("invalid_promotion_transition")
        if target_scope == "TENANT" and (not policy.get("tenant_id") or "TENANT" not in policy.get("read", [])):
            raise PermissionError("tenant_scope_denied")
        tenant = policy.get("tenant_id") if target_scope == "TENANT" else None
        if row["scope"] == "TENANT" and row["tenant_id"] != policy.get("tenant_id"):
            raise PermissionError("tenant_scope_denied")
        content = proposed_content if proposed_content is not None else row["content"]
        if not isinstance(content, str) or not content.strip():
            raise ValueError("invalid_promotion_content")
        request_id = _id("pr_")
        request = conn.execute("""INSERT INTO memory_promotion_requests
            (request_id, idempotency_key, requested_by, source_chunk_id, source_version_id,
             from_scope, to_scope, target_tenant_id, proposed_content, state)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'APPROVAL_PENDING') RETURNING *""",
            (request_id, idempotency_key, uid, source_chunk_id, row["version_id"], row["scope"],
             target_scope, tenant, content)).fetchone()
        _audit(conn, "memory.promotion.requested", uid, source_chunk_id, row["version_id"], request_id)
    _governance_trace("memory.promotion.requested", uid, {**request, "policy_version": policy.get("version")})
    return _request_view(request)


def _request_view(row: dict) -> dict:
    return {key: (str(row[key]) if key in {"requested_by", "reviewed_by"} and row.get(key) else
                  _iso(row[key]) if key in {"created_at", "updated_at"} else row[key])
            for key in ("request_id", "requested_by", "source_chunk_id", "source_version_id",
                        "from_scope", "to_scope", "target_tenant_id", "proposed_content", "state",
                        "target_chunk_id", "reviewed_by", "reason", "created_at", "updated_at")
            if key in row}


def promotion_detail(uid: str, role: str, request_id: str) -> dict:
    _uuid(uid)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM memory_promotion_requests WHERE request_id = %s", (request_id,)).fetchone()
        if not row:
            raise KeyError("promotion_not_found")
        if role != "admin" and str(row["requested_by"]) != uid:
            raise PermissionError("promotion_not_owned")
        return _request_view(row)


def cancel_promotion(uid: str, role: str, request_id: str) -> dict:
    _uuid(uid)
    with get_connection() as conn, conn.transaction():
        request = conn.execute("SELECT * FROM memory_promotion_requests WHERE request_id = %s FOR UPDATE",
                               (request_id,)).fetchone()
        if not request:
            raise KeyError("promotion_not_found")
        if role != "admin" and str(request["requested_by"]) != uid:
            raise PermissionError("promotion_not_owned")
        if request["state"] == "PROMOTION_CANCELLED":
            return _request_view(request)
        if request["state"] != "APPROVAL_PENDING":
            raise ValueError("promotion_not_pending")
        request = conn.execute("""UPDATE memory_promotion_requests SET state = 'PROMOTION_CANCELLED',
            updated_at = now() WHERE request_id = %s RETURNING *""", (request_id,)).fetchone()
        _audit(conn, "memory.promotion.cancelled", uid, request["source_chunk_id"],
               request["source_version_id"], request_id)
    _governance_trace("memory.promotion.cancelled", uid, request)
    return _request_view(request)


def _governance_trace(event: str, uid: str, request: dict | None = None, *, status: str = "ok"):
    if in_run():
        emit(event, status=status, error=RuntimeError(event) if status == "error" else None,
             component="kb", owner_id=uid,
             data={key: value for key, value in {
                 "promotion_request_id": request.get("request_id") if request else None,
                 "source_chunk_id": request.get("source_chunk_id") if request else None,
                 "target_chunk_id": request.get("target_chunk_id") if request else None,
                 "from_scope": request.get("from_scope") if request else None,
                 "to_scope": request.get("to_scope") if request else None,
                 "policy_version": request.get("policy_version") if request else None,
             }.items() if value is not None})


_PRIVATE = re.compile(
    r"[\w.+-]+@[\w.-]+\.[a-zA-Z]{2,}|https?://\S+|\b(?:\d{1,3}\.){3}\d{1,3}\b|"
    r"\b(?:api[_-]?key|password|token|secret|credential)\s*[:=]\s*\S+|"
    r"\b(?:customer|client|tenant|account|organization)[_-]?(?:id|name|code)\s*[:=]\s*\S+|"
    r"\b(?:host|hostname|server|database|schema)\s*[:=]\s*[\w.-]+",
    re.I,
)


def _fail_promotion(uid: str, request_id: str, reason: str) -> None:
    """Record a terminal review failure without altering the source memory."""
    with get_connection() as conn, conn.transaction():
        request = conn.execute(
            "SELECT * FROM memory_promotion_requests WHERE request_id = %s FOR UPDATE", (request_id,)
        ).fetchone()
        if not request or request["state"] != "APPROVAL_PENDING":
            return
        failed = conn.execute("""UPDATE memory_promotion_requests SET state = 'PROMOTION_FAILED',
            reviewed_by = %s, reason = %s, updated_at = now() WHERE request_id = %s RETURNING *""",
            (uid, reason[:500], request_id)).fetchone()
        request = failed or {**request, "state": "PROMOTION_FAILED", "reviewed_by": uid,
                             "reason": reason[:500]}
        _audit(conn, "memory.promotion.failed", uid, request["source_chunk_id"],
               request["source_version_id"], request_id, {"reason_code": reason[:120]})
    _governance_trace("memory.promotion.failed", uid, request, status="error")


def review_promotion(uid: str, role: str, request_id: str, *, approve: bool,
                     policy: dict, reason: str = "") -> dict:
    if role != "admin":
        raise PermissionError("admin_required")
    try:
        return _review_promotion(uid, request_id, approve=approve, policy=policy, reason=reason)
    except (PermissionError, ValueError, KeyError) as exc:
        if approve:
            try:
                _fail_promotion(uid, request_id, str(exc))
            except Exception:
                logger.warning("failed recording terminal promotion failure request=%s", request_id, exc_info=True)
        raise
    except Exception as exc:
        if approve:
            try:
                _fail_promotion(uid, request_id, type(exc).__name__)
            except Exception:
                logger.warning("failed recording terminal promotion failure request=%s", request_id, exc_info=True)
        _governance_trace("memory.promotion.failed", uid, {"request_id": request_id}, status="error")
        raise


def _review_promotion(uid: str, request_id: str, *, approve: bool, policy: dict, reason: str) -> dict:
    with get_connection() as conn, conn.transaction():
        request = conn.execute("SELECT * FROM memory_promotion_requests WHERE request_id = %s FOR UPDATE",
                               (request_id,)).fetchone()
        if not request:
            raise KeyError("promotion_not_found")
        if request["state"] != "APPROVAL_PENDING":
            return _request_view(request)
        if not approve:
            request = conn.execute("""UPDATE memory_promotion_requests SET state = 'PROMOTION_REJECTED',
                reviewed_by = %s, reason = %s, updated_at = now() WHERE request_id = %s RETURNING *""",
                (uid, reason, request_id)).fetchone()
            _audit(conn, "memory.promotion.rejected", uid, request["source_chunk_id"],
                   request["source_version_id"], request_id)
        else:
            source = _row(conn, request["source_chunk_id"], lock=True)
            if (not source or source["status"] != "ACTIVE" or source["version_status"] != "ACTIVE" or
                    source["version_id"] != request["source_version_id"] or
                    (source["expires_at"] and source["expires_at"] <= datetime.now(timezone.utc))):
                raise ValueError("source_stale")
            if not _publication_allowed(
                policy, chunk_type=source["chunk_type"], target_scope=request["to_scope"]
            ):
                raise PermissionError("publisher_policy_denied")
            tenant = _authorized(uid, policy, request["to_scope"], "write", role="admin")
            if request["to_scope"] == "TENANT" and tenant != request["target_tenant_id"]:
                raise PermissionError("tenant_scope_denied")
            if source["scope"] == "TENANT" and source["tenant_id"] != policy.get("tenant_id"):
                raise PermissionError("tenant_scope_denied")
            content = request["proposed_content"].strip()
            if request["to_scope"] == "AGENT":
                if _PRIVATE.search(content):
                    raise ValueError("generalization_required")
                # An admin supplies and reviews the generalized text; no untrusted auto-redaction.
                if source["scope"] != "AGENT" and content == source["content"] and source["sensitivity"] != "PUBLIC":
                    raise ValueError("generalization_required")
            if _conflicts(conn, request["to_scope"], tenant, content):
                raise ValueError("conflicting_memory_requires_review")
            vector = _vector(content)
            chunk_id, version_id = _id("chk_"), _id("v_")
            conn.execute("""INSERT INTO memory_chunks (chunk_id, chunk_type, scope, tenant_id, memory_weight,
                active_version_id) VALUES (%s, %s, %s, %s, %s, %s)""",
                (chunk_id, source["chunk_type"], request["to_scope"], tenant, source["memory_weight"], version_id))
            conn.execute("""INSERT INTO memory_versions (version_id, chunk_id, content, search_text, content_hash,
                embedding, embedding_model, embedding_dimensions, created_by, sensitivity, promoted_from_version_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'PUBLIC', %s)""",
                (version_id, chunk_id, content, content, "sha256:" + hashlib.sha256(content.encode()).hexdigest(),
                 Jsonb(vector), _model(), len(vector), uid, source["version_id"]))
            _queue(conn, version_id, "UPSERT")
            request = conn.execute("""UPDATE memory_promotion_requests SET state = 'TARGET_ACTIVE',
                target_chunk_id = %s, reviewed_by = %s, reason = %s, updated_at = now()
                WHERE request_id = %s RETURNING *""", (chunk_id, uid, reason, request_id)).fetchone()
            _audit(conn, "memory.promotion.activated", uid, chunk_id, version_id, request_id,
                   {"source_version_id": source["version_id"]})
    _governance_trace("memory.promotion.rejected" if not approve else "memory.promotion.validated", uid, request)
    if approve:
        _governance_trace("memory.promotion.approved", uid, request)
        _governance_trace("memory.promotion.activated", uid, request)
        sync_index()
    return _request_view(request)


def promotions(uid: str, role: str) -> list[dict]:
    _uuid(uid)
    with get_connection() as conn:
        rows = conn.execute("""SELECT * FROM memory_promotion_requests
            WHERE (%s = 'admin' OR requested_by = %s) ORDER BY created_at DESC LIMIT 200""",
            (role, uid)).fetchall()
    return [{**_request_view(row), "proposed_content": "[open review details]",
             "requested_by": None, "source_chunk_id": None, "source_version_id": None}
            for row in rows]


def revoke(uid: str, role: str, chunk_id: str, policy: dict) -> dict:
    _uuid(uid)
    if role != "admin":
        raise PermissionError("admin_required")
    with get_connection() as conn, conn.transaction():
        row = _row(conn, chunk_id, lock=True)
        if not row or row["scope"] not in {"TENANT", "AGENT"}:
            raise KeyError("chunk_not_found")
        _authorized(uid, policy, row["scope"], "write", role=role)
        if row["scope"] == "TENANT" and row["tenant_id"] != policy.get("tenant_id"):
            raise PermissionError("tenant_scope_denied")
        conn.execute("UPDATE memory_chunks SET status = 'REVOKED', updated_at = now() WHERE chunk_id = %s", (chunk_id,))
        conn.execute("UPDATE memory_versions SET status = 'REVOKED' WHERE version_id = %s", (row["version_id"],))
        _queue(conn, row["version_id"], "DELETE")
        _audit(conn, "memory.revoke", uid, chunk_id, row["version_id"])
    _governance_trace("memory.revoke", uid)
    sync_index()
    return {"chunk_id": chunk_id, "status": "REVOKED"}


def demote(uid: str, role: str, chunk_id: str, policy: dict) -> dict:
    """Controlled demotion: revoke a published target, preserving its source and history."""
    with get_connection() as conn:
        linked = conn.execute("""SELECT 1 FROM memory_versions WHERE chunk_id = %s
            AND promoted_from_version_id IS NOT NULL""", (chunk_id,)).fetchone()
    if not linked:
        raise ValueError("not_a_promotion")
    result = revoke(uid, role, chunk_id, policy)
    _governance_trace("memory.demote", uid)
    return result


def import_legacy(uid: str, policy: dict, *, dry_run: bool = False) -> dict[str, int]:
    """Opt-in, resumable import; ownerless and mismatched records are quarantined."""
    from src.subagents.learner_agent.store.json_store import read_all_chunks

    _authorized(uid, policy, "USER", "write")
    counts = {"imported": 0, "already_imported": 0, "quarantined": 0}
    for record in read_all_chunks():
        if not isinstance(record, dict):
            counts["quarantined"] += 1
            continue
        meta = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        source_id = record.get("id")
        if (not isinstance(source_id, str) or not source_id or not isinstance(meta, dict) or meta.get("uid") != uid or
                not isinstance(record.get("advice"), str) or not record["advice"].strip()):
            counts["quarantined"] += 1
            continue
        if _PRIVATE.search(record["advice"]) or _PRIVATE.search(str(record.get("embed_text") or "")):
            counts["quarantined"] += 1
            continue
        with get_connection() as conn:
            existing = _active_for_uid(conn, uid, source_id)
        if existing:
            counts["already_imported"] += 1
        elif not dry_run:
            write(uid, policy, record["advice"], source_id=source_id, chunk_type="workflow",
                   search_text=record.get("embed_text"), conversation_id=meta.get("source_agent_id"),
                  metadata={"observed_tool": meta.get("observed_tool") or "",
                            "prior_tool": meta.get("prior_tool") or "",
                            "outcome": meta.get("outcome") or "unknown"})
            counts["imported"] += 1
    return counts


def set_expiry(uid: str, role: str, chunk_id: str, policy: dict, expires_at: datetime | None,
               retention_class: str | None = None) -> dict:
    if role != "admin":
        raise PermissionError("admin_required")
    if expires_at is not None and expires_at.tzinfo is None:
        raise ValueError("expiry_requires_timezone")
    if retention_class not in {None, "TRANSIENT", "STANDARD", "LONG_TERM", "LEGAL_HOLD"}:
        raise ValueError("invalid_retention_class")
    with get_connection() as conn, conn.transaction():
        row = _row(conn, chunk_id, lock=True)
        if not row or row["scope"] not in {"TENANT", "AGENT"}:
            raise KeyError("chunk_not_found")
        _authorized(uid, policy, row["scope"], "write", role=role)
        if row["scope"] == "TENANT" and row["tenant_id"] != policy.get("tenant_id"):
            raise PermissionError("tenant_scope_denied")
        conn.execute("""UPDATE memory_versions SET expires_at = %s, retention_class = %s,
            revalidated_at = now() WHERE version_id = %s""",
            (expires_at, retention_class, row["version_id"]))
        if row["status"] == "ACTIVE" and row["version_status"] == "ACTIVE":
            _queue(conn, row["version_id"], "UPSERT" if expires_at is None or expires_at > datetime.now(timezone.utc) else "DELETE")
        _audit(conn, "memory.revalidate", uid, chunk_id, row["version_id"],
               details={"has_expiry": bool(expires_at), "retention_class": retention_class})
    _governance_trace("memory.revalidate", uid)
    sync_index()
    return {"chunk_id": chunk_id, "expires_at": _iso(expires_at), "retention_class": retention_class}
