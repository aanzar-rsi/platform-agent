from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    identifier: str = Field(..., description="email, user_name, or uid")
    password: str


class UserOut(BaseModel):
    uid: str
    user_name: str | None = None
    email: str | None = None
    name: str | None = None
    role: str = "user"
    created_at: str | None = None
    last_login: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: str
    user: UserOut


class LogoutResponse(BaseModel):
    success: bool = True
    message: str = "logged out"
