from __future__ import annotations

import uuid as uuidlib
from typing import Any

from api.core.cache import cache_get_or_set, cache_invalidate, user_cache
from api.core.security import hash_password, needs_rehash, verify_password
from api.db.postgres import execute, fetch_all, fetch_one


def _valid_uuid(value: str) -> bool:
    try:
        uuidlib.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


def _row_to_user(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "uid": str(row["user_id"]),
        "user_name": row.get("user_name"),
        "email": row.get("email"),
        "name": row.get("display_name"),
        "role": str(row.get("role") or "user").lower(),
        "status": str(row.get("status") or "active").lower(),
        "created_at": _iso(row.get("created_at")),
        # No dedicated last_login_at column; updated_at is bumped on login.
        "last_login": _iso(row.get("updated_at")),
    }


class UserRepository:
    def list_users(self) -> list[dict[str, Any]]:
        rows = fetch_all("SELECT * FROM users ORDER BY created_at")
        return [_row_to_user(r) for r in rows]

    def get_by_uid(self, uid: str) -> dict[str, Any] | None:
        if not _valid_uuid(uid):
            return None

        def _load() -> dict[str, Any] | None:
            row = fetch_one("SELECT * FROM users WHERE user_id = %s", (uid,))
            return _row_to_user(row) if row else None

        return cache_get_or_set(user_cache, uid, _load)

    def find_login(self, identifier: str) -> dict[str, Any] | None:
        ident = identifier.strip()
        row = fetch_one(
            """
            SELECT * FROM users
            WHERE lower(email) = lower(%(ident)s)
               OR lower(user_name) = lower(%(ident)s)
               OR user_id::text = %(ident)s
            """,
            {"ident": ident},
        )
        return _row_to_user(row) if row else None

    def public_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {
            "uid": user.get("uid"),
            "user_name": user.get("user_name"),
            "email": user.get("email"),
            "name": user.get("name"),
            "role": user.get("role", "user"),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
        }

    def authenticate(self, identifier: str, password: str) -> dict[str, Any] | None:
        ident = identifier.strip()
        row = fetch_one(
            """
            SELECT u.*, c.password_hash
            FROM users u
            JOIN user_credentials c ON c.user_id = u.user_id
            WHERE (
                lower(u.email) = lower(%(ident)s)
                OR lower(u.user_name) = lower(%(ident)s)
                OR u.user_id::text = %(ident)s
            )
            AND upper(u.status) = 'ACTIVE'
            """,
            {"ident": ident},
        )
        if not row:
            return None
        hashed = row.get("password_hash")
        if not hashed or not verify_password(password, hashed):
            return None
        if needs_rehash(hashed):
            new_hash = hash_password(password)
            execute(
                "UPDATE user_credentials SET password_hash = %s, updated_at = now() WHERE user_id = %s",
                (new_hash, row["user_id"]),
            )
        return _row_to_user(row)

    def touch_last_login(self, uid: str) -> dict[str, Any] | None:
        if not _valid_uuid(uid):
            return None
        execute("UPDATE users SET updated_at = now() WHERE user_id = %s", (uid,))
        cache_invalidate(user_cache, uid)
        return self.get_by_uid(uid)
