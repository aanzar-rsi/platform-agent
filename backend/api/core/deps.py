from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWTError

from api.core.security import decode_access_token
from api.db.repositories import (
    AgentRepository,
    AnalyticsRepository,
    AuthSessionRepository,
    ExecutionEventRepository,
    McpRepository,
    MemoryRepository,
    MemoryExtractionRepository,
    PreferencesRepository,
    SessionRepository,
    UserRepository,
)

_bearer = HTTPBearer(auto_error=False)


@dataclass
class Repositories:
    agents: AgentRepository = field(default_factory=AgentRepository)
    users: UserRepository = field(default_factory=UserRepository)
    auth_sessions: AuthSessionRepository = field(default_factory=AuthSessionRepository)
    sessions: SessionRepository = field(default_factory=SessionRepository)
    memory: MemoryRepository = field(default_factory=MemoryRepository)
    memory_extractions: MemoryExtractionRepository = field(default_factory=MemoryExtractionRepository)
    preferences: PreferencesRepository = field(default_factory=PreferencesRepository)
    mcp: McpRepository = field(default_factory=McpRepository)
    analytics: AnalyticsRepository = field(default_factory=AnalyticsRepository)
    execution_events: ExecutionEventRepository = field(default_factory=ExecutionEventRepository)


_repos: Repositories | None = None


def get_repos() -> Repositories:
    global _repos
    if _repos is None:
        _repos = Repositories()
    return _repos


@dataclass
class CurrentUser:
    uid: str
    session_id: str
    role: str
    raw: dict[str, Any]


def require_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    repos: Annotated[Repositories, Depends(get_repos)],
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    uid = payload.get("sub")
    sid = payload.get("sid")
    if not uid or not sid:
        raise HTTPException(status_code=401, detail="Malformed token")
    if not repos.auth_sessions.is_active(sid, uid):
        raise HTTPException(status_code=401, detail="Session revoked or expired")

    user = repos.users.get_by_uid(uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return CurrentUser(
        uid=uid,
        session_id=sid,
        role=str(user.get("role") or "user").lower(),
        raw=repos.users.public_user(user),
    )


def user_from_token(token: str, repos: Repositories | None = None) -> CurrentUser:
    """Validate JWT for WebSocket handshake."""
    repos = repos or get_repos()
    try:
        payload = decode_access_token(token)
    except PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc
    uid = payload.get("sub")
    sid = payload.get("sid")
    if not uid or not sid:
        raise HTTPException(status_code=401, detail="Malformed token")
    if not repos.auth_sessions.is_active(sid, uid):
        raise HTTPException(status_code=401, detail="Session revoked or expired")
    user = repos.users.get_by_uid(uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return CurrentUser(
        uid=uid,
        session_id=sid,
        role=str(user.get("role") or "user").lower(),
        raw=repos.users.public_user(user),
    )
