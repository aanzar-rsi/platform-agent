from __future__ import annotations

from typing import Any

from api.core.deps import Repositories


class PreloadService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    def build(self, uid: str) -> dict[str, Any]:
        user = self.repos.users.get_by_uid(uid)
        public = self.repos.users.public_user(user) if user else {"uid": uid}
        return {
            "user": public,
            "preferences": self.repos.preferences.get(uid),
            "memory": self.repos.memory.get(uid),
            "mcp_servers": self.repos.mcp.list(uid),
        }
