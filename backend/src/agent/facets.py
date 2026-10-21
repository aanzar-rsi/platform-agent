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
    """The only discovery and invocation boundary for executable resources."""

    def __init__(self, policy: dict, *, user_id: str | None = None,
                 preloaded_context: dict | None = None) -> None:
        self.policy = dict(policy)
        self.user_id = user_id
        self.preloaded_context = dict(preloaded_context or {})

    def list(self, resource_type: str | None = None, *, reconnect: bool = False) -> list:
        from dataclasses import dataclass
        from src.subagents.registry import get_subagents
        from src.tools import INTERNAL_TOOLS

        @dataclass(frozen=True)
        class Resource:
            type: str
            name: str
            description: str
            target: object
            confirmation_required: bool = False

        resources = []
        if resource_type in (None, "tool"):
            confirm = {"edit_file", "execute_bash", "execute_powershell", "execute_python_script"}
            resources.extend(
                Resource("tool", tool.name, tool.description, tool, tool.name in confirm)
                for tool in INTERNAL_TOOLS
                if armory_resource_allowed(self.policy, group="tools", name=tool.name)
            )
            if self.user_id:
                from api.services.mcp_runtime import available_mcp_tools

                resources.extend(
                    Resource("tool", name, tool.description, tool)
                    for name, tool in available_mcp_tools(self.user_id, reconnect=reconnect).items()
                    if armory_resource_allowed(self.policy, group="tools", name=name)
                )
        if resource_type in (None, "subagent"):
            resources.extend(
                Resource("subagent", spec.name, spec.description, spec)
                for spec in get_subagents(self.user_id)
                if armory_resource_allowed(self.policy, group="subagents", name=spec.name)
            )
        return resources

    def get(self, resource_type: str, resource_name: str, *, reconnect: bool = False):
        if resource_type not in {"tool", "subagent"}:
            raise ValueError(f"Unknown armory resource type: {resource_type}")
        return next(
            (resource for resource in self.list(resource_type, reconnect=reconnect)
             if resource.name == resource_name),
            None,
        )

    def call(self, resource_type: str, resource_name: str, arguments: dict,
             *, task: str = "", reconnect: bool = False):
        """Authorize, resolve, validate, and invoke one resource."""
        if not isinstance(arguments, dict):
            raise ValueError("Armory arguments must be an object")
        resource = self.get(resource_type, resource_name, reconnect=reconnect)
        if resource is None:
            group = "tools" if resource_type == "tool" else "subagents"
            if not armory_resource_allowed(self.policy, group=group, name=resource_name):
                from src.utils.trace import emit, in_run
                if in_run():
                    emit("armory.authz.deny", component="armory", status="denied",
                         error=PermissionError("armory_resource_denied"),
                         data={"resource_type": resource_type, "resource_name": resource_name})
                raise PermissionError(f"Armory resource denied: {resource_type}.{resource_name}")
            raise LookupError(f"Unknown armory resource: {resource_type}.{resource_name}")

        from src.utils.trace import emit, in_run
        if in_run():
            emit("armory.authz.allow", component="armory",
                 data={"resource_type": resource_type, "resource_name": resource_name})

        if resource_type == "subagent":
            context = {**self.preloaded_context, "parameters": arguments}
            if self.user_id:
                context["uid"] = self.user_id
            result = resource.target.adapter(task, context)
            return result, context.pop("_subagent_structured_result", None)

        from api.services.mcp_runtime import McpTool, call_mcp_tool
        if isinstance(resource.target, McpTool):
            return call_mcp_tool(self.user_id or "", resource.target, arguments), None
        schema = getattr(resource.target, "args_schema", None)
        invoke_args = schema.model_validate(arguments).model_dump() if schema else arguments
        return resource.target.invoke(invoke_args), None


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
