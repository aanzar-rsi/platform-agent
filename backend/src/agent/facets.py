"""Agent policy facets: memory, armory, guardrails and observability."""

from __future__ import annotations

from src.agent.agent_models import Message
from src.agent.policy_schema import armory_resource_allowed, memory_action_allowed, normalize_memory_policy


class Memory:
    def __init__(self, policy: dict, user_id: str, repository=None) -> None:
        self.policy = dict(policy)
        self.user_id = user_id
        self.repository = repository

    def _check(self, operation: str, scope: str, *, chunk_type: str | None = None) -> None:
        if not self.user_id or not memory_action_allowed(self.policy, action=operation, scope=scope, chunk_type=chunk_type):
            raise PermissionError("memory_scope_denied")
        effective = normalize_memory_policy(self.policy)
        if scope == "TENANT" and not effective.get("tenant_id"):
            raise PermissionError("tenant_scope_denied")

    def update_policy(self, policy: dict) -> None:
        self.policy = dict(policy)

    def retrieve(self, query: str = "", *, scope: str = "USER", chunk_type: str | None = None) -> list[dict]:
        from src.utils.trace import current_ids, emit, span

        if not current_ids().get("execution_id") or not current_ids().get("agent_id"):
            self._check("read", scope, chunk_type=chunk_type)
            return self._retrieve(query, scope)
        try:
            with span("memory", "retrieve", component="memory", data={"scope": scope}):
                self._check("read", scope, chunk_type=chunk_type)
                return self._retrieve(query, scope)
        except PermissionError as exc:
            emit("memory.retrieve.denied", status="denied", error=exc, data={"scope": scope}, component="memory")
            raise

    def _retrieve(self, query: str, scope: str) -> list[dict]:
        if scope != "USER":
            raise NotImplementedError("scoped_memory_store_requires_phase_1")
        from api.db.repositories.memory import MemoryRepository

        entries = (self.repository or MemoryRepository()).get(self.user_id)
        return [entry for entry in entries if not query or query.lower() in (entry["key"] + " " + (entry["value"] or "")).lower()]

    def write(
        self,
        key: str,
        value: str,
        category: str = "general",
        *,
        scope: str = "USER",
        chunk_type: str | None = None,
    ) -> dict:
        from src.utils.trace import current_ids, emit, span

        if not current_ids().get("execution_id") or not current_ids().get("agent_id"):
            self._check("write", scope, chunk_type=chunk_type)
            return self._write(key, value, category, scope)
        try:
            with span("memory", "write", component="memory", data={"scope": scope}):
                self._check("write", scope, chunk_type=chunk_type)
                return self._write(key, value, category, scope)
        except PermissionError as exc:
            emit("memory.write.denied", status="denied", error=exc, data={"scope": scope}, component="memory")
            raise

    def replace(self, entries: list[dict], *, scope: str = "USER") -> list[dict]:
        try:
            self._check("write", scope)
        except PermissionError as exc:
            from src.utils.trace import emit, in_run

            if in_run():
                emit("memory.write.denied", status="denied", error=exc, data={"scope": scope}, component="memory")
            raise
        if scope != "USER":
            raise NotImplementedError("scoped_memory_store_requires_phase_1")
        from api.db.repositories.memory import MemoryRepository
        from src.utils.trace import in_run, span

        if in_run():
            with span("memory", "write", component="memory", data={"scope": scope}):
                return (self.repository or MemoryRepository()).put(self.user_id, entries)
        return (self.repository or MemoryRepository()).put(self.user_id, entries)

    def clear(self, *, scope: str = "USER") -> None:
        try:
            self._check("write", scope)
        except PermissionError as exc:
            from src.utils.trace import emit, in_run

            if in_run():
                emit("memory.write.denied", status="denied", error=exc, data={"scope": scope}, component="memory")
            raise
        if scope != "USER":
            raise NotImplementedError("scoped_memory_store_requires_phase_1")
        from api.db.repositories.memory import MemoryRepository
        from src.utils.trace import in_run, span

        if in_run():
            with span("memory", "write", component="memory", data={"scope": scope}):
                (self.repository or MemoryRepository()).clear(self.user_id)
            return
        (self.repository or MemoryRepository()).clear(self.user_id)

    def _write(self, key: str, value: str, category: str, scope: str) -> dict:
        if scope != "USER":
            raise PermissionError("memory_store_unavailable")
        from api.db.repositories.memory import MemoryRepository

        return (self.repository or MemoryRepository()).add_entry(self.user_id, key, value, category)


class Armory:
    def __init__(self, policy: dict) -> None:
        self.policy = dict(policy)

    def allowed(self, name: str, kind: str = "tools") -> bool:
        return armory_resource_allowed(self.policy, group=kind, name=name)


class Guardrails:
    def __init__(self, policy: dict) -> None:
        self.policy = dict(policy)

    def check_input(self, message: Message) -> bool:
        return isinstance(message.content, str) and bool(message.content.strip())

    def check_resource_call(self, resource: str, arguments: dict) -> bool:
        return bool(resource) and isinstance(arguments, dict)

    def check_output(self, message: Message) -> bool:
        return isinstance(message.content, str)


class Observability:
    def __init__(self, policy: dict) -> None:
        self.policy = dict(policy)

    def record(self, event: str, details: dict) -> None:
        from src.utils.trace import emit

        emit(event, data=details)
