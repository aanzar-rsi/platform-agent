from __future__ import annotations

import asyncio
from typing import Any

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException

from api.core.config import get_settings


def _fernet() -> Fernet:
    key = get_settings().mcp_credentials_key
    if not key:
        raise HTTPException(status_code=422, detail="MCP_CREDENTIALS_KEY is required for login-authenticated servers")
    try:
        return Fernet(key.encode())
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="MCP_CREDENTIALS_KEY must be a valid Fernet key") from exc


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken as exc:
        raise ConnectionError("Saved MCP credentials cannot be decrypted") from exc


def public_auth(auth: dict[str, Any] | None) -> dict[str, Any] | None:
    if not auth:
        return None
    return {
        "login_url": auth["login_url"],
        "username": auth["username"],
        "use_agent_credentials": auth.get("use_agent_credentials", False),
        "username_field": auth.get("username_field", "username"),
        "password_field": auth.get("password_field", "password"),
        "token_field": auth.get("token_field", "access_token"),
        "password_configured": bool(auth.get("password")),
    }


class McpBearerAuth(httpx.Auth):
    """Logs in before the first request and refreshes once after a 401."""

    requires_response_body = True

    def __init__(self, server: dict[str, Any], save_token) -> None:
        self.server = server
        self.save_token = save_token
        self._token = decrypt(server["_auth"].get("token", "")) if server["_auth"].get("token") else None
        self._lock = asyncio.Lock()

    async def _login(self, *, force: bool = False) -> str:
        async with self._lock:
            if self._token and not force:
                return self._token
            auth = self.server["_auth"]
            password = decrypt(auth["password"])
            payload = {
                auth.get("username_field", "username"): auth["username"],
                auth.get("password_field", "password"): password,
            }
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(auth["login_url"], json=payload)
                response.raise_for_status()
                body = response.json()
            token = body.get(auth.get("token_field", "access_token")) if isinstance(body, dict) else None
            if not isinstance(token, str) or not token:
                raise ConnectionError("MCP login response did not include the configured token field")
            self._token = token
            auth["token"] = encrypt(token)
            self.save_token(auth)
            return token

    async def async_auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {await self._login()}"
        response = yield request
        if response.status_code != 401:
            return
        await response.aclose()
        request.headers["Authorization"] = f"Bearer {await self._login(force=True)}"
        yield request
