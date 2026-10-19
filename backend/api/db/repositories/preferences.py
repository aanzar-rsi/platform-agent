from __future__ import annotations

from typing import Any

from psycopg.types.json import Jsonb

from api.core.cache import cache_get_or_set, cache_invalidate, preferences_cache
from api.db.postgres import execute, fetch_one

_DEFAULT_APP_PREFS: dict[str, Any] = {
    "theme": "system",
    "console_mode": "basic",
    "memory_policy_ceiling": {
        "version": 2,
        "enabled": True,
        "read": ["USER", "AGENT"],
        "write": ["USER"],
        "promote": ["TENANT", "AGENT"],
        "publish": [],
        "tenant_id": None,
        "confirm_before_extracting": False,
        "allow_admin_promotion": True,
        "chunks": {},
    },
}


class PreferencesRepository:
    def get(self, uid: str) -> dict[str, Any]:
        def _load() -> dict[str, Any]:
            row = fetch_one(
                "SELECT app_preferences, agent_preferences FROM user_preferences WHERE user_id = %s",
                (uid,),
            )
            app_prefs = dict(_DEFAULT_APP_PREFS)
            agent_prefs: dict[str, Any] = {}
            if row:
                app_prefs.update(row.get("app_preferences") or {})
                agent_prefs = row.get("agent_preferences") or {}
            return {**app_prefs, "agent": agent_prefs}

        return cache_get_or_set(preferences_cache, uid, _load)

    def put(self, uid: str, prefs: dict[str, Any]) -> dict[str, Any]:
        current = self.get(uid)
        current.update(prefs)
        agent_prefs = current.pop("agent", {})
        app_prefs = current

        execute(
            """
            INSERT INTO user_preferences (user_id, app_preferences, agent_preferences, updated_at)
            VALUES (%s, %s, %s, now())
            ON CONFLICT (user_id) DO UPDATE
            SET app_preferences = excluded.app_preferences,
                agent_preferences = excluded.agent_preferences,
                updated_at = now()
            """,
            (uid, Jsonb(app_prefs), Jsonb(agent_prefs)),
        )
        cache_invalidate(preferences_cache, uid)
        return {**app_prefs, "agent": agent_prefs}
