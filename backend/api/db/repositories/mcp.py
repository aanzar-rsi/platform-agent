from __future__ import annotations

import uuid as uuidlib
from typing import Any

from psycopg.types.json import Jsonb

from api.core.cache import cache_get_or_set, cache_invalidate, mcp_cache
from api.db.postgres import execute, fetch_all, fetch_one


def _valid_uuid(value: str) -> bool:
    try:
        uuidlib.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _row_to_server(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata") or {}
    auth = metadata.get("_auth")
    return {
        "id": str(row["server_id"]),
        "name": row["name"],
        "url": row["server_url"],
        "connected": False,
        "command": metadata.get("command"),
        "transport": metadata.get("transport"),
        "args": metadata.get("args", []),
        "env": metadata.get("env", {}),
        "enabled": metadata.get("enabled", True),
        "metadata": {key: value for key, value in metadata.items() if key != "_auth"},
        "_auth": auth,
        "created_at": _iso(row.get("created_at")),
        "updated_at": _iso(row.get("created_at")),
    }


_LIST_SQL = """
    SELECT c.*, conn.connection_status
    FROM mcp_servers_catalog c
    LEFT JOIN user_mcp_connections conn
        ON conn.server_id = c.server_id AND conn.user_id = %(uid)s
    WHERE c.owner_user_id = %(uid)s
    ORDER BY c.created_at
"""

_GET_ONE_SQL = """
    SELECT c.*, conn.connection_status
    FROM mcp_servers_catalog c
    LEFT JOIN user_mcp_connections conn
        ON conn.server_id = c.server_id AND conn.user_id = %(uid)s
    WHERE c.owner_user_id = %(uid)s AND c.server_id = %(sid)s
"""


class McpRepository:
    def list(self, uid: str) -> list[dict[str, Any]]:
        def _load() -> list[dict[str, Any]]:
            rows = fetch_all(_LIST_SQL, {"uid": uid})
            return [_row_to_server(r) for r in rows]

        return cache_get_or_set(mcp_cache, uid, _load)

    def get(self, uid: str, server_id: str) -> dict[str, Any] | None:
        if not _valid_uuid(server_id):
            return None
        row = fetch_one(_GET_ONE_SQL, {"uid": uid, "sid": server_id})
        return _row_to_server(row) if row else None

    def create(self, uid: str, *, name: str, url: str = "", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        row = fetch_one(
            """
            INSERT INTO mcp_servers_catalog
                (name, server_url, auth_type, is_global, status, owner_user_id, metadata)
            VALUES (%s, %s, 'none', false, 'active', %s, %s)
            RETURNING *
            """,
            (name, url, uid, Jsonb(metadata or {})),
        )
        cache_invalidate(mcp_cache, uid)
        return _row_to_server({**row, "connection_status": None})

    def update(self, uid: str, server_id: str, **fields: Any) -> dict[str, Any] | None:
        if not _valid_uuid(server_id):
            return None

        set_clauses: list[str] = []
        params: list[Any] = []
        if "name" in fields:
            set_clauses.append("name = %s")
            params.append(fields["name"])
        if "url" in fields:
            set_clauses.append("server_url = %s")
            params.append(fields["url"])
        if "metadata" in fields:
            set_clauses.append("metadata = %s")
            params.append(Jsonb(fields["metadata"]))

        if set_clauses:
            params.extend([server_id, uid])
            n = execute(
                f"UPDATE mcp_servers_catalog SET {', '.join(set_clauses)} "
                "WHERE server_id = %s AND owner_user_id = %s",
                tuple(params),
            )
            if n == 0:
                return None
        else:
            owner_row = fetch_one(
                "SELECT 1 FROM mcp_servers_catalog WHERE server_id = %s AND owner_user_id = %s",
                (server_id, uid),
            )
            if not owner_row:
                return None

        cache_invalidate(mcp_cache, uid)
        row = fetch_one(_GET_ONE_SQL, {"uid": uid, "sid": server_id})
        return _row_to_server(row) if row else None

    def delete(self, uid: str, server_id: str) -> bool:
        if not _valid_uuid(server_id):
            return False
        # user_mcp_connections.server_id has no ON DELETE CASCADE — clear it first.
        execute(
            "DELETE FROM user_mcp_connections WHERE server_id = %s AND user_id = %s",
            (server_id, uid),
        )
        n = execute(
            "DELETE FROM mcp_servers_catalog WHERE server_id = %s AND owner_user_id = %s",
            (server_id, uid),
        )
        if n > 0:
            cache_invalidate(mcp_cache, uid)
        return n > 0
