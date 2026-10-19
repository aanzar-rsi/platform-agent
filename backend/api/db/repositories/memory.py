from __future__ import annotations

from typing import Any

from api.db.postgres import execute, fetch_all, get_connection


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _row_to_entry(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "key": row["key"],
        "value": row["value"],
        "category": row.get("category") or "general",
        "updated_at": _iso(row.get("updated_at")),
    }


class MemoryRepository:
    def get(self, uid: str) -> list[dict[str, Any]]:
        rows = fetch_all(
            "SELECT key, value, category, updated_at FROM user_memory_entries WHERE user_id = %s ORDER BY updated_at",
            (uid,),
        )
        return [_row_to_entry(r) for r in rows]

    def put(self, uid: str, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        with get_connection() as conn:
            conn.execute("DELETE FROM user_memory_entries WHERE user_id = %s", (uid,))
            for entry in entries:
                conn.execute(
                    """
                    INSERT INTO user_memory_entries (user_id, key, value, category, updated_at)
                    VALUES (%s, %s, %s, %s, now())
                    """,
                    (uid, entry.get("key"), entry.get("value"), entry.get("category") or "general"),
                )
        return entries

    def add_entry(self, uid: str, key: str, value: str, category: str | None = None) -> dict[str, Any]:
        row = None
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO user_memory_entries (user_id, key, value, category, updated_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (user_id, key) DO UPDATE
                SET value = excluded.value, category = excluded.category, updated_at = now()
                RETURNING key, value, category, updated_at
                """,
                (uid, key, value, category or "general"),
            )
            row = cur.fetchone()
        return _row_to_entry(row)

    def clear(self, uid: str) -> None:
        execute("DELETE FROM user_memory_entries WHERE user_id = %s", (uid,))
