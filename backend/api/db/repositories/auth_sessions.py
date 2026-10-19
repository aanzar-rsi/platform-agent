from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from api.core.config import get_settings
from api.db.postgres import execute, fetch_one


def _iso(value: Any) -> str | None:
    return value.isoformat() if value is not None else None


class AuthSessionRepository:
    def create(self, session_id: str, uid: str) -> dict[str, Any]:
        settings = get_settings()
        expires = datetime.now(timezone.utc) + timedelta(
            hours=settings.auth_session_expire_hours
        )
        row = fetch_one(
            """
            INSERT INTO auth_sessions (session_id, user_id, expires_at)
            VALUES (%s, %s, %s)
            RETURNING session_id, user_id, created_at, expires_at, revoked_at
            """,
            (session_id, uid, expires),
        )
        return self._to_doc(row)

    def get(self, session_id: str) -> dict[str, Any] | None:
        row = fetch_one(
            "SELECT * FROM auth_sessions WHERE session_id = %s", (session_id,)
        )
        return self._to_doc(row) if row else None

    def is_active(self, session_id: str, uid: str) -> bool:
        doc = self.get(session_id)
        if not doc or not doc.get("active"):
            return False
        if doc.get("uid") != uid:
            return False
        expires_at = doc.get("expires_at")
        if expires_at:
            try:
                exp = datetime.fromisoformat(expires_at)
                if exp.tzinfo is None:
                    exp = exp.replace(tzinfo=timezone.utc)
                if exp < datetime.now(timezone.utc):
                    return False
            except ValueError:
                return False
        return True

    def invalidate(self, session_id: str) -> bool:
        n = execute(
            "UPDATE auth_sessions SET revoked_at = now() WHERE session_id = %s AND revoked_at IS NULL",
            (session_id,),
        )
        return n > 0

    @staticmethod
    def _to_doc(row: dict[str, Any] | None) -> dict[str, Any]:
        if not row:
            return {}
        return {
            "session_id": row["session_id"],
            "uid": str(row["user_id"]),
            "created_at": _iso(row.get("created_at")),
            "expires_at": _iso(row.get("expires_at")),
            "active": row.get("revoked_at") is None,
        }
