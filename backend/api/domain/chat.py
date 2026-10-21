from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatCreateRequest(BaseModel):
    title: str | None = None


class ChatUpdateRequest(BaseModel):
    title: str | None = None


class PolicyUpdateRequest(BaseModel):
    expected_version: int = Field(ge=1)
    armory: dict[str, Any] | None = None
    memory: dict[str, Any] | None = None


class ExtractionDecisionRequest(BaseModel):
    approve: bool
    reason: str = ""


class ChatOut(BaseModel):
    agent_id: str
    owner_id: str
    title: str
    created_at: str
    updated_at: str
    deleted: bool = False
    rollback_checkpoint_id: str | None = None


class ChatDetailOut(ChatOut):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    execution_history: list[dict[str, Any]] = Field(default_factory=list)
    preloaded_context: dict[str, Any] = Field(default_factory=dict)
    latest_execution: dict[str, Any] | None = None


class RollbackRequest(BaseModel):
    checkpoint_id: str


class CheckpointOut(BaseModel):
    checkpoint_id: str
    timestamp: str | None = None
    current_task: str | None = None
    message_snippet: str | None = None
    parent_checkpoint_id: str | None = None


class CheckpointTreeOut(CheckpointOut):
    node: str | None = None
    is_leaf: bool = False
    is_active_tip: bool = False
    has_pending_interrupt: bool = False
