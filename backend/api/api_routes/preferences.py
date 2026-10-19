from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from api.core.deps import CurrentUser, Repositories, get_repos, require_user
from api.domain.memory import PreferencesUpdateRequest
from api.services.preferences_service import PreferencesService

router = APIRouter(
    prefix="/preferences",
    tags=["preferences"],
    dependencies=[Depends(require_user)],
)


@router.get("")
def get_prefs(
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> dict[str, Any]:
    return PreferencesService(repos).get(user)


@router.put("")
def put_prefs(
    body: PreferencesUpdateRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> dict[str, Any]:
    return PreferencesService(repos).put(user, body)
