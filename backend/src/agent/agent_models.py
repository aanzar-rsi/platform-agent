"""Core agent dataclasses shared across runtime components."""

from __future__ import annotations

import threading
from concurrent.futures import Future
from dataclasses import dataclass
from typing import Literal

from src.agent.policy_schema import normalize_armory_policy, normalize_memory_policy


@dataclass(frozen=True)
class AgentID:
    agent_id: str
    owner_id: str
    owner_type: Literal["user", "agent"]
    latest_session_id: str | None = None
    parent_agent_id: str | None = None


@dataclass(frozen=True)
class Policy:
    armory: dict
    memory: dict
    guardrails: dict
    observability: dict
    version: int = 1

    @classmethod
    def from_record(cls, record: dict) -> "Policy":
        raw = record["policy"]
        armory = normalize_armory_policy(raw.get("armory"))
        memory = normalize_memory_policy(raw.get("memory"))
        return cls(
            armory,
            memory,
            raw.get("guardrails") or {},
            raw.get("observability") or {},
            version=record["policy_version"],
        )

    def as_dict(self) -> dict:
        return {key: getattr(self, key) for key in ("armory", "memory", "guardrails", "observability")}


@dataclass(frozen=True)
class Message:
    message_id: str
    content: str
    sender_id: str | None
    sender_type: Literal["user", "agent", "tool", "system"]
    execution_id: str
    created_at: str
    child_agent_id: str | None = None
    visible_to_user: bool = True


@dataclass(frozen=True)
class ChildHandle:
    child_agent_id: str
    execution_id: str
    future: Future
    cancel_event: threading.Event
    deadline: float
