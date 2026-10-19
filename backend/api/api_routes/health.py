from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.core.deps import CurrentUser, require_user
from api.domain.common import HealthResponse, LiveResponse
from api.services.agent_runtime import get_agent_app
from api.services.chat_runtime_manager import get_runtime_manager

live_router = APIRouter(tags=["health"])
router = APIRouter(tags=["health"], dependencies=[Depends(require_user)])


@live_router.get("/live", response_model=LiveResponse)
def live() -> LiveResponse:
    return LiveResponse(ok=True)


@router.get("/health", response_model=HealthResponse)
def health(_user: Annotated[CurrentUser, Depends(require_user)]) -> HealthResponse:
    agent_ready = False
    try:
        get_agent_app()
        agent_ready = True
    except Exception:
        agent_ready = False
    mgr = get_runtime_manager()
    return HealthResponse(
        status="ok" if agent_ready else "degraded",
        agent_ready=agent_ready,
        active_ws=mgr.active_ws_count(),
        active_runs=mgr.active_run_count(),
    )
