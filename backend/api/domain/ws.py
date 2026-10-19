from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WsEnvelope(BaseModel):
    v: int = 1
    type: str
    id: str
    agent_id: str
    seq: int | None = None
    ts: str
    payload: dict[str, Any] = Field(default_factory=dict)


class ClientRunStart(BaseModel):
    query: str
    checkpoint_id: str | None = None


class ClientAck(BaseModel):
    seq: int


class ClientRollback(BaseModel):
    checkpoint_id: str
