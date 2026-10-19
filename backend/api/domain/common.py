from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    agent_ready: bool
    active_ws: int
    active_runs: int


class LiveResponse(BaseModel):
    ok: bool = True
