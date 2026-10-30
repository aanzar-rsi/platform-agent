from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.core.deps import CurrentUser, require_user
from api.domain.common import HealthResponse, LiveResponse
from api.db.postgres import fetch_one
from api.services.agent_runtime import get_agent_app
from api.services.chat_runtime_manager import get_runtime_manager
from src.agent.kb import chroma_status

live_router = APIRouter(tags=["health"])
router = APIRouter(tags=["health"], dependencies=[Depends(require_user)])


def _dependency_snapshot() -> tuple[dict[str, bool], list[str]]:
    deps = {
        "postgres": False,
        "chroma": False,
    }
    warnings: list[str] = []
    try:
        fetch_one("SELECT 1")
        deps["postgres"] = True
    except Exception:
        warnings.append("postgres_unavailable")
    deps["chroma"] = chroma_status()
    if not deps["chroma"]:
        warnings.append("chroma_unavailable")
    return deps, warnings


@live_router.get("/live", response_model=LiveResponse)
def live() -> LiveResponse:
    deps, warnings = _dependency_snapshot()
    status = "ok" if deps["postgres"] else "degraded"
    return LiveResponse(ok=True, status=status, dependencies=deps, warnings=warnings)


@router.get("/health", response_model=HealthResponse)
def health(_user: Annotated[CurrentUser, Depends(require_user)]) -> HealthResponse:
    agent_ready = False
    deps, warnings = _dependency_snapshot()

    try:
        get_agent_app()
        agent_ready = True
    except Exception:
        agent_ready = False

    mgr = get_runtime_manager()
    status = "ok" if agent_ready and deps["postgres"] else "degraded"
    return HealthResponse(
        status=status,
        agent_ready=agent_ready,
        active_ws=mgr.active_ws_count(),
        active_runs=mgr.active_run_count(),
        dependencies=deps,
        warnings=warnings,
    )
