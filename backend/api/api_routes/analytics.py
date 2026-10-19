from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from api.core.deps import CurrentUser, Repositories, get_repos, require_user
from api.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_user)],
)


@router.get("")
def summary(
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
    from_ts: Annotated[str | None, Query(alias="from")] = None,
    to_ts: Annotated[str | None, Query(alias="to")] = None,
) -> dict[str, Any]:
    return AnalyticsService(repos).summary(user, start=from_ts, end=to_ts)
