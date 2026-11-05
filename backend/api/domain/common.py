from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    agent_ready: bool
    active_ws: int
    active_runs: int
    dependencies: dict[str, bool]
    warnings: list[str] = Field(default_factory=list)


class LiveResponse(BaseModel):
    ok: bool = True
    status: str = "ok"
    dependencies: dict[str, bool] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
