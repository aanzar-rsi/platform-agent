"""Agent lifecycle facade and compatibility exports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from api.db.repositories.agents import AgentRepository
from src.agent.agent_models import AgentID, ChildHandle, Message, Policy
from src.agent.child_runner import ChildRunner, child_runner
from src.agent.facets import Armory, Guardrails, Memory, Observability
from src.agent.policy import default_policy, intersect_policy
from src.agent.policy_schema import (
    intersect_armory,
    intersect_memory,
    normalize_armory_policy,
    normalize_memory_policy,
)


@dataclass
class AgentCore:
    record: dict
    repository: AgentRepository = field(default_factory=AgentRepository)
    active_execution_id: str | None = None
    auto_close_on_result: bool = False

    @property
    def id(self) -> AgentID:
        r = self.record
        return AgentID(
            *(str(r[key]) for key in ("agent_id", "owner_id", "owner_type")),
            latest_session_id=r.get("latest_session_id"),
            parent_agent_id=str(r["parent_agent_id"]) if r.get("parent_agent_id") else None,
        )

    @property
    def policy(self) -> Policy:
        return Policy.from_record(self.record)

    @property
    def state(self) -> str:
        return self.record["state"]

    @property
    def memory(self) -> Memory:
        root = self.record
        while root.get("parent_agent_id"):
            root = self.repository.get(str(root["parent_agent_id"]))
        return Memory(self.policy.memory, str(root["owner_id"]))

    @property
    def armory(self) -> Armory:
        return Armory(self.policy.armory, user_id=self.id.owner_id)

    @property
    def guardrails(self) -> Guardrails:
        return Guardrails(self.policy.guardrails)

    @property
    def observability(self) -> Observability:
        return Observability(self.policy.observability)

    @property
    def conversation(self) -> list[Message]:
        return [
            Message(
                str(row["message_id"]),
                row["content"],
                str(row["sender_id"]) if row["sender_id"] else None,
                row["sender_type"],
                str(row["execution_id"]),
                row["created_at"].isoformat(),
                str(row["child_agent_id"]) if row["child_agent_id"] else None,
                row["visible_to_user"],
            )
            for row in self.repository.messages(self.id.agent_id)
        ]

    def run(self, input_message: Message | None = None, *, parent_execution_id: str | None = None,
            execution_id: str | None = None) -> str:
        if self.state == "closed":
            raise ValueError("agent_closed")
        row = self.repository.start_execution(
            self.id.agent_id,
            parent_execution_id=parent_execution_id,
            execution_id=execution_id,
        )
        self.active_execution_id = str(row["execution_id"])
        if input_message:
            self.repository.append_message(self.id.agent_id, self.active_execution_id, input_message.content,
                                           sender_type=input_message.sender_type,
                                           sender_id=input_message.sender_id)
        return self.active_execution_id

    def spawn_subagent(self, task: str, adapter: Callable[[str, dict], str],
                       context: dict | None = None, requested_policy: Policy | None = None) -> ChildHandle:
        return child_runner.spawn_child(self, task, adapter, context or {}, requested_policy=requested_policy)

    def finish(self, state: str, *, result: str | None = None, error: str | None = None) -> None:
        if not self.active_execution_id:
            raise ValueError("no_active_run")
        self.repository.finish_execution(self.active_execution_id, state, result=result, error=error)
        if state not in {"interrupted", "running"}:
            self.active_execution_id = None
            if self.auto_close_on_result:
                self.close()

    def update_armory_policy(self, new_scope: dict, *, uid: str, expected_version: int) -> None:
        from src.utils.trace import in_run, emit

        if self.state == "closed":
            raise ValueError("agent_closed")
        if not isinstance(new_scope, dict):
            raise ValueError("invalid_armory_policy")
        if any(key in new_scope for key in ("tools", "subagents")):
            raise ValueError("invalid_armory_policy")
        if "resources" in new_scope and not isinstance(new_scope["resources"], dict):
            raise ValueError("invalid_armory_policy")
        if "groups" in new_scope and not isinstance(new_scope["groups"], dict):
            raise ValueError("invalid_armory_policy")
        if "confirm_tools" in new_scope and not isinstance(new_scope["confirm_tools"], bool):
            raise ValueError("invalid_armory_policy")
        previous = normalize_armory_policy(self.policy.armory)
        effective_raw = {**previous, **new_scope}
        effective = normalize_armory_policy(effective_raw)
        ceiling = normalize_armory_policy((self.record.get("policy_ceiling") or self.record["policy"])["armory"])
        bounded = intersect_armory(ceiling, effective, ceiling)
        for group, items in effective.get("resources", {}).items():
            bounded_names = {item.get("name") for item in bounded.get("resources", {}).get(group, []) if item.get("enabled", True)}
            requested_names = {item.get("name") for item in items if item.get("enabled", True)}
            if requested_names - bounded_names:
                raise PermissionError("armory_scope_expansion_denied")
        if effective.get("groups", {}).get("mcp_servers", {}).get("enabled", False) and not bounded.get("groups", {}).get("mcp_servers", {}).get("enabled", False):
            raise PermissionError("armory_scope_expansion_denied")
        if not effective.get("confirm_tools", True) and ceiling.get("confirm_tools", True):
            raise PermissionError("confirmation_required")
        self.record = self.repository.update_policy(self.id.agent_id, "armory", effective,
                                                    uid=uid, expected_version=expected_version)
        if in_run():
            emit("policy.armory.update", data={"old_version": expected_version, "new_version": expected_version + 1,
                                               "changed_keys": list(new_scope)}, component="agent_core")

    def update_memory_policy(self, new_scope: dict, *, uid: str, expected_version: int) -> None:
        from src.utils.trace import in_run, emit

        previous = normalize_memory_policy(self.policy.memory)
        ceiling = normalize_memory_policy((self.record.get("policy_ceiling") or self.record["policy"])["memory"])
        if self.state == "closed":
            raise ValueError("agent_closed")
        if not isinstance(new_scope, dict):
            raise ValueError("invalid_memory_policy")
        if "tenant_id" in new_scope and new_scope["tenant_id"] is not None and not isinstance(new_scope["tenant_id"], str):
            raise ValueError("invalid_memory_policy")
        for key in ("read", "write", "promote", "publish"):
            if key in new_scope and (not isinstance(new_scope[key], list) or any(not isinstance(item, str) for item in new_scope[key])):
                raise ValueError("invalid_memory_policy")
        effective_raw = {**previous, **new_scope}
        effective = normalize_memory_policy(effective_raw)
        tenant_id = effective.get("tenant_id")
        if tenant_id and tenant_id != ceiling.get("tenant_id"):
            raise PermissionError("unverified_tenant")
        bounded = intersect_memory(ceiling, effective, ceiling)
        for key in ("read", "write", "promote", "publish"):
            if set(effective.get(key, [])) - set(bounded.get(key, [])):
                raise PermissionError("scope_expansion_denied")
        if effective.get("tenant_id") != bounded.get("tenant_id"):
            raise PermissionError("scope_expansion_denied")
        self.record = self.repository.update_policy(self.id.agent_id, "memory", effective,
                                                    uid=uid, expected_version=expected_version)
        if in_run():
            emit("policy.memory.update", data={"old_version": expected_version, "new_version": expected_version + 1,
                                               "changed_keys": list(new_scope)}, component="agent_core")

    def close(self) -> None:
        if self.state == "closed":
            return
        self.record = self.repository.close(self.id.agent_id)
        if self.id.parent_agent_id:
            from src.utils.trace import in_run, emit

            if in_run():
                emit("child.lifecycle.close", child_agent_id=self.id.agent_id,
                     parent_agent_id=self.id.parent_agent_id, component="agent_core")


__all__ = [
    "AgentCore",
    "AgentID",
    "Policy",
    "Message",
    "ChildHandle",
    "Memory",
    "Armory",
    "Guardrails",
    "Observability",
    "ChildRunner",
    "child_runner",
    "default_policy",
    "intersect_policy",
]
