from __future__ import annotations

from api.core.deps import CurrentUser, Repositories
from api.domain.memory import MemoryAddRequest, MemoryEntry, MemoryPutRequest
from src.agent.agent_core import Memory, default_policy
from src.agent.policy_schema import effective_memory_policy


class MemoryService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    def get(self, user: CurrentUser) -> list[MemoryEntry]:
        policy = self._policy(user.uid)
        return [MemoryEntry(**e) for e in Memory(policy, user.uid, self.repos.memory).retrieve(scope="USER")]

    def put(self, user: CurrentUser, body: MemoryPutRequest) -> list[MemoryEntry]:
        entries = [e.model_dump() for e in body.entries]
        saved = Memory(self._policy(user.uid), user.uid, self.repos.memory).replace(entries, scope="USER")
        return [MemoryEntry(**e) for e in saved]

    def add(self, user: CurrentUser, body: MemoryAddRequest) -> MemoryEntry:
        entry = Memory(self._policy(user.uid), user.uid, self.repos.memory).write(
            body.key, body.value, body.category, scope="USER")
        return MemoryEntry(**entry)

    def clear(self, user: CurrentUser) -> dict:
        Memory(self._policy(user.uid), user.uid, self.repos.memory).clear(scope="USER")
        return {"success": True}

    def _policy(self, uid: str) -> dict:
        ceiling = ((self.repos.preferences.get(uid).get("agent") or {}).get("memory_policy_ceiling"))
        return effective_memory_policy(default_policy().memory, ceiling)
