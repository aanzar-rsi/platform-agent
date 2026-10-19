from __future__ import annotations

from fastapi import HTTPException, status

from api.core.deps import CurrentUser, Repositories
from api.core.security import create_access_token, new_session_id
from api.domain.auth import LoginRequest, LoginResponse, UserOut


class AuthService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    def login(self, body: LoginRequest) -> LoginResponse:
        user = self.repos.users.authenticate(body.identifier, body.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        uid = user["uid"]
        self.repos.users.touch_last_login(uid)
        refreshed = self.repos.users.get_by_uid(uid) or user
        session_id = new_session_id()
        self.repos.auth_sessions.create(session_id, uid)
        token, expires_in = create_access_token(
            uid=uid,
            session_id=session_id,
            role=str(refreshed.get("role") or "user"),
        )
        self.repos.analytics.append("login", uid=uid)
        public = self.repos.users.public_user(refreshed)
        return LoginResponse(
            access_token=token,
            expires_in=expires_in,
            session_id=session_id,
            user=UserOut(**public),
        )

    def logout(self, user: CurrentUser) -> dict:
        self.repos.auth_sessions.invalidate(user.session_id)
        self.repos.analytics.append("logout", uid=user.uid)
        return {"success": True, "message": "logged out"}

    def me(self, user: CurrentUser) -> UserOut:
        return UserOut(**user.raw)
