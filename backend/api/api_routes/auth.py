from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from api.core.deps import CurrentUser, Repositories, get_repos, require_user
from api.domain.auth import LoginRequest, LoginResponse, LogoutResponse, UserOut
from api.services.auth_service import AuthService

# Public login router (no auth dependency)
login_router = APIRouter(prefix="/auth", tags=["auth"])

# Protected auth routes
router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(require_user)])


@login_router.post("/login", response_model=LoginResponse)
def login(
    body: LoginRequest,
    repos: Annotated[Repositories, Depends(get_repos)],
) -> LoginResponse:
    return AuthService(repos).login(body)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    user: Annotated[CurrentUser, Depends(require_user)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> LogoutResponse:
    result = AuthService(repos).logout(user)
    return LogoutResponse(**result)


@router.get("/me", response_model=UserOut)
def me(user: Annotated[CurrentUser, Depends(require_user)]) -> UserOut:
    return UserOut(**user.raw)
