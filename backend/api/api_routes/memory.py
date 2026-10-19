from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.core.deps import CurrentUser, Repositories, get_repos, require_user
from api.domain.memory import MemoryAddRequest, MemoryEntry, MemoryPutRequest
from api.services.memory_service import MemoryService

router = APIRouter(
    prefix="/memory",
    tags=["memory"],
    dependencies=[Depends(require_user)],
)


@router.get("", response_model=list[MemoryEntry])
def get_memory(
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> list[MemoryEntry]:
    return MemoryService(repos).get(user)


@router.put("", response_model=list[MemoryEntry])
def put_memory(
    body: MemoryPutRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> list[MemoryEntry]:
    return MemoryService(repos).put(user, body)


@router.post("/entries", response_model=MemoryEntry)
def add_memory(
    body: MemoryAddRequest,
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> MemoryEntry:
    return MemoryService(repos).add(user, body)


@router.delete("")
def clear_memory(
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> dict:
    return MemoryService(repos).clear(user)
