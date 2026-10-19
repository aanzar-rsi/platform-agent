from __future__ import annotations

import logging
from typing import Any

from fastapi import HTTPException

from api.core.deps import CurrentUser, Repositories
from api.domain.memory import McpCreateRequest, McpUpdateRequest
from api.services.mcp_runtime import mcp_runtime

logger = logging.getLogger(__name__)


def connection_log(level: str, message: str) -> dict[str, str]:
    from datetime import datetime, timezone

    return {"timestamp": datetime.now(timezone.utc).isoformat(), "level": level, "message": message}


def public_server(uid: str, server: dict[str, Any]) -> dict[str, Any]:
    conn = mcp_runtime.get(uid, server["id"])
    return {**server, "connected": conn is not None, "tools_count": len(conn.tools) if conn else 0,
            "connection_error": mcp_runtime.failure(uid, server["id"])}


class McpService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    def list(self, user: CurrentUser) -> list[dict[str, Any]]:
        return [public_server(user.uid, server) for server in self.repos.mcp.list(user.uid)]

    def create(self, user: CurrentUser, body: McpCreateRequest) -> dict[str, Any]:
        server = self.repos.mcp.create(
            user.uid, name=body.name.strip(), url=body.url or "",
            metadata={**body.metadata, "command": body.command, "transport": body.transport,
                      "args": body.args,
                      "env": body.env, "enabled": body.enabled},
        )
        try:
            result = self.connect(user, server["id"])
            return {**public_server(user.uid, server), "connection_logs": result["logs"]}
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, dict) else {"message": exc.detail, "logs": []}
            return {**public_server(user.uid, server), "connection_error": detail["message"], "connection_logs": detail["logs"]}

    def update(self, user: CurrentUser, server_id: str, body: McpUpdateRequest) -> dict[str, Any]:
        existing = self.repos.mcp.get(user.uid, server_id)
        if not existing:
            raise HTTPException(status_code=404, detail="MCP server not found")
        fields = body.model_dump(exclude_unset=True)
        if "name" in fields and not (fields["name"] or "").strip():
            raise HTTPException(status_code=422, detail="Name cannot be blank")
        metadata_fields = {key: fields.pop(key) for key in ("command", "transport", "args", "env", "enabled") if key in fields}
        if metadata_fields or "metadata" in fields:
            fields["metadata"] = {**existing["metadata"], **(fields.get("metadata") or {}), **metadata_fields}
        if "url" in fields and fields["url"] is None:
            fields["url"] = ""
        if "url" in fields or any(key in metadata_fields for key in ("command", "transport", "args", "env")):
            candidate = {**existing, **fields, **metadata_fields}
            if fields.get("url") and metadata_fields.get("command"):
                raise HTTPException(status_code=422, detail="Choose either URL or command")
            if fields.get("url") and not metadata_fields.get("command"):
                candidate["command"] = None
                fields["metadata"] = {**candidate["metadata"], "command": None}
            elif metadata_fields.get("command"):
                candidate["url"] = ""
                fields["url"] = ""
            candidate.update({key: candidate["metadata"].get(key) for key in ("command", "transport", "args", "env")})
            McpCreateRequest.model_validate(candidate)
        doc = self.repos.mcp.update(
            user.uid, server_id, **fields
        )
        if "url" in fields or any(key in metadata_fields for key in ("command", "transport", "args", "env")):
            mcp_runtime.disconnect(user.uid, server_id)
        if metadata_fields.get("enabled") is False:
            mcp_runtime.disconnect(user.uid, server_id)
        return public_server(user.uid, doc)

    def connect(self, user: CurrentUser, server_id: str) -> dict[str, Any]:
        server = self.repos.mcp.get(user.uid, server_id)
        if not server:
            raise HTTPException(status_code=404, detail="MCP server not found")
        if not server["enabled"]:
            raise HTTPException(status_code=400, detail="Enable the MCP server before connecting")
        target = server["command"] or server["url"]
        transport = "stdio" if server["command"] else server.get("transport") or "streamable_http"
        logs = [connection_log("INFO", f"Connecting via {transport}: {target}")]
        try:
            conn = mcp_runtime.connect(user.uid, server)
        except BaseException as exc:
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            logger.warning("MCP connection failed for %s (transport=%s, url=%s, command=%s): %s",
                           server_id, server.get("transport"), server.get("url"), server.get("command"), exc)
            reason = str(exc) or type(exc).__name__
            if reason == "Session terminated":
                reason = (f"The MCP server returned HTTP 404 during the handshake at {server['url']}. "
                          "Check the MCP endpoint path and select the correct HTTP transport (Streamable HTTP or Legacy SSE).")
            logs.append(connection_log("ERROR", reason))
            raise HTTPException(status_code=502, detail={"message": f"MCP connection failed: {reason}", "logs": logs}) from exc
        logs.append(connection_log("INFO", f"Handshake complete; discovered {len(conn.tools)} tool(s)."))
        return {"success": True, "message": "Connected", "server_id": server_id,
                "tools_count": len(conn.tools), "tools": [tool["name"] for tool in conn.tools], "logs": logs}

    def disconnect(self, user: CurrentUser, server_id: str) -> dict[str, Any]:
        if not self.repos.mcp.get(user.uid, server_id):
            raise HTTPException(status_code=404, detail="MCP server not found")
        mcp_runtime.disconnect(user.uid, server_id, manual=True)
        return {"success": True, "message": "Disconnected"}

    def details(self, user: CurrentUser, server_id: str) -> dict[str, Any]:
        server = self.repos.mcp.get(user.uid, server_id)
        if not server:
            raise HTTPException(status_code=404, detail="MCP server not found")
        conn = mcp_runtime.get(user.uid, server_id)
        failure = mcp_runtime.failure(user.uid, server_id)
        logs = [connection_log("ERROR", failure)] if failure else []
        try:
            discovered = conn.run(conn._details()) if conn else {"tools": [], "prompts": [], "resources": []}
        except Exception as exc:
            discovered = {"tools": [], "prompts": [], "resources": [], "tools_error": str(exc)}
            logs.append(connection_log("ERROR", str(exc)))
            conn = None
        return {"server_id": server_id, "server_name": server["name"],
                "server_url": server["url"] or server.get("command") or "",
                "connected": conn is not None, "logs": logs, **discovered}

    def import_config(self, user: CurrentUser, config: dict[str, Any]) -> dict[str, Any]:
        entries = config.get("mcpServers")
        if not isinstance(entries, dict):
            raise HTTPException(status_code=422, detail="Expected an mcpServers object")
        validated = []
        for name, value in entries.items():
            if not isinstance(value, dict):
                raise HTTPException(status_code=422, detail=f"Invalid server: {name}")
            try:
                body = McpCreateRequest.model_validate({**value, "name": name})
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            validated.append(body)
        created = [self.create(user, body) for body in validated]
        return {"success": True, "count": len(created), "created": created}

    def delete(self, user: CurrentUser, server_id: str) -> dict:
        if not self.repos.mcp.get(user.uid, server_id):
            raise HTTPException(status_code=404, detail="MCP server not found")
        mcp_runtime.disconnect(user.uid, server_id)
        if not self.repos.mcp.delete(user.uid, server_id):
            raise HTTPException(status_code=404, detail="MCP server not found")
        return {"success": True, "id": server_id}
