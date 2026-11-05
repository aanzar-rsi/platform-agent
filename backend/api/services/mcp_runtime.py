"""Live MCP sessions. Each session stays on its own event-loop thread.

The MCP SDK's anyio transport contexts must be entered and exited by the same
task. A persistent loop per connection keeps stdio processes and HTTP sessions
alive between API requests and agent tool calls.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import logging
import os
import re
import threading
import time
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamable_http_client
import httpx
from api.services.mcp_auth import McpBearerAuth

from api.core import deps
from src.utils.trace import emit as trace_emit, in_run


def _auth_headers(server: dict[str, Any]) -> dict[str, str]:
    metadata = server.get("metadata") if isinstance(server.get("metadata"), dict) else {}
    raw = metadata.get("auth_headers")
    if not isinstance(raw, dict):
        return {}
    headers: dict[str, str] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, str) and key.strip() and value.strip():
            headers[key.strip()] = value.strip()
    return headers

logger = logging.getLogger(__name__)
TIMEOUT = 15
RECONNECT_DELAY = 30



class McpConnection:
    def __init__(self, uid: str, server: dict[str, Any]) -> None:
        self.uid = uid
        self.server = server
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run, daemon=True, name=f"mcp-{server['id']}")
        self.stack: AsyncExitStack | None = None
        self.session: ClientSession | None = None
        self.tools: list[dict[str, Any]] = []
        self.ready: concurrent.futures.Future[None] = concurrent.futures.Future()
        self.stopping: asyncio.Event | None = None
        self.worker: concurrent.futures.Future[Any] | None = None

    def _run(self) -> None:
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()
        self.loop.close()

    def run(self, coro: Any, timeout: int = TIMEOUT) -> Any:
        if self.session is None:
            coro.close()
            raise ConnectionError("MCP session is closed")
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            future.cancel()
            raise

    async def _open_session(self, transport: Any) -> list[dict[str, Any]]:
        async with asyncio.timeout(TIMEOUT):
            streams = await self.stack.enter_async_context(transport)
            self.session = await self.stack.enter_async_context(ClientSession(
                streams[0], streams[1], read_timeout_seconds=timedelta(seconds=TIMEOUT)
            ))
        async with asyncio.timeout(TIMEOUT):
            await self.session.initialize()
            tools = []
            cursor = None
            while True:
                page = await self.session.list_tools(cursor=cursor)
                tools.extend(tool.model_dump(by_alias=True, exclude_none=True) for tool in page.tools)
                cursor = page.nextCursor
                if not cursor:
                    break
        return tools

    async def _serve(self) -> None:
        self.stack = AsyncExitStack()
        try:
            if self.server.get("command"):
                transport = stdio_client(StdioServerParameters(
                    command=self.server["command"],
                    args=self.server.get("args") or [],
                    env={**os.environ, **(self.server.get("env") or {})},
                ))
                self.tools = await self._open_session(transport)
            elif self.server.get("transport") == "sse" or (
                not self.server.get("transport") and self.server["url"].rstrip("/").endswith("/sse")
            ):
                headers = _auth_headers(self.server)
                try:
                    transport = sse_client(self.server["url"], timeout=TIMEOUT, headers=headers,
                                           auth=self._http_auth())
                except TypeError:
                    transport = sse_client(self.server["url"], timeout=TIMEOUT, headers=headers)
                self.tools = await self._open_session(transport)
            else:
                headers = _auth_headers(self.server)
                client = await self.stack.enter_async_context(
                    httpx.AsyncClient(timeout=TIMEOUT, headers=headers or None, auth=self._http_auth())
                )
                transport = streamable_http_client(self.server["url"], http_client=client)
                self.tools = await self._open_session(transport)
            self.stopping = asyncio.Event()
            self.ready.set_result(None)
            await self.stopping.wait()
        except BaseException as exc:
            if not self.ready.done():
                self.ready.set_exception(exc)
            raise
        finally:
            try:
                await self.stack.aclose()
            except BaseException as exc:
                # The handshake error is already reported to the caller. MCP's
                # background HTTP task surfaces it again while closing.
                logger.debug("MCP transport cleanup after failure: %s", exc)
            self.session = None
            self.stack = None

    def _http_auth(self) -> McpBearerAuth | None:
        if not self.server.get("_auth"):
            return None

        def save_token(auth: dict[str, Any]) -> None:
            self.server["_auth"] = auth
            from api.core.deps import get_repos
            current = get_repos().mcp.get(self.uid, self.server["id"])
            if current:
                get_repos().mcp.update(self.uid, self.server["id"], metadata={**current["metadata"], "_auth": auth})

        return McpBearerAuth(self.server, save_token)

    async def _call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if self.session is None:
            raise ConnectionError("MCP session is closed")
        result = await self.session.call_tool(name, arguments)
        return result.model_dump(by_alias=True, exclude_none=True)

    async def _details(self) -> dict[str, Any]:
        if self.session is None:
            raise ConnectionError("MCP session is closed")
        details: dict[str, Any] = {"tools": self.tools, "prompts": [], "resources": []}
        for capability, method in (("prompts", self.session.list_prompts),
                                   ("resources", self.session.list_resources)):
            try:
                cursor = None
                while True:
                    page = await method(cursor=cursor)
                    details[capability].extend(
                        item.model_dump(by_alias=True, exclude_none=True)
                        for item in getattr(page, capability)
                    )
                    cursor = page.nextCursor
                    if not cursor:
                        break
            except Exception as exc:
                details[f"{capability}_error"] = str(exc)
        return details

    def close(self) -> None:
        if not self.thread.is_alive():
            return
        try:
            if self.stopping:
                self.loop.call_soon_threadsafe(self.stopping.set)
            if self.worker:
                self.worker.result(timeout=5)
        except BaseException as exc:
            # anyio cancellation scopes may report cancellation while a stale
            # HTTP transport is shutting down; cleanup must not block reconnect.
            logger.debug("MCP session cleanup for %s: %s", self.server["id"], exc)
        finally:
            self.session = None
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.thread.join(timeout=5)


class McpRuntime:
    def __init__(self) -> None:
        self._connections: dict[tuple[str, str], McpConnection] = {}
        self._disabled: set[tuple[str, str]] = set()
        self._failures: dict[tuple[str, str], str] = {}
        self._failed_at: dict[tuple[str, str], float] = {}
        self._lock = threading.RLock()

    def get(self, uid: str, server_id: str) -> McpConnection | None:
        with self._lock:
            conn = self._connections.get((uid, server_id))
            return conn if conn and conn.session and conn.thread.is_alive() else None

    def failure(self, uid: str, server_id: str) -> str | None:
        with self._lock:
            return self._failures.get((uid, server_id))

    def connect(self, uid: str, server: dict[str, Any]) -> McpConnection:
        key = (uid, server["id"])
        with self._lock:
            existing = self.get(*key)
            if existing:
                self._disabled.discard(key)
                return existing
            stale = self._connections.pop(key, None)
            if stale:
                stale.close()
            conn = McpConnection(uid, server)
            conn.thread.start()
            conn.worker = asyncio.run_coroutine_threadsafe(conn._serve(), conn.loop)
            try:
                conn.ready.result(timeout=TIMEOUT + 2)
            except BaseException as exc:
                self._failures[key] = (
                    f"MCP endpoint returned HTTP 404: {server['url']}. Check the URL and HTTP transport."
                    if str(exc) == "Session terminated" and server.get("url")
                    else str(exc) or type(exc).__name__
                )
                self._failed_at[key] = time.monotonic()
                conn.close()
                raise
            self._connections[key] = conn
            self._disabled.discard(key)
            self._failures.pop(key, None)
            self._failed_at.pop(key, None)
            return conn

    def disconnect(self, uid: str, server_id: str, *, manual: bool = False) -> None:
        with self._lock:
            if manual:
                self._disabled.add((uid, server_id))
            self._failures.pop((uid, server_id), None)
            self._failed_at.pop((uid, server_id), None)
            conn = self._connections.pop((uid, server_id), None)
            if conn:
                conn.close()

    def can_reconnect(self, uid: str, server_id: str) -> bool:
        with self._lock:
            key = (uid, server_id)
            failed_at = self._failed_at.get(key)
            return key not in self._disabled and (failed_at is None or time.monotonic() - failed_at >= RECONNECT_DELAY)

    def mark_failure(self, uid: str, server_id: str, error: BaseException) -> None:
        with self._lock:
            self._failures[(uid, server_id)] = str(error) or type(error).__name__
            self._failed_at[(uid, server_id)] = time.monotonic()

    def close(self) -> None:
        with self._lock:
            for conn in self._connections.values():
                conn.close()
            self._connections.clear()
            self._disabled.clear()
            self._failures.clear()
            self._failed_at.clear()


mcp_runtime = McpRuntime()


@dataclass
class McpTool:
    name: str
    description: str
    server_id: str
    server_name: str
    remote_name: str
    input_schema: dict[str, Any]


def available_mcp_tools(uid: str | None, *, reconnect: bool = False) -> dict[str, McpTool]:
    if not uid:
        return {}
    result = {}
    for server in deps.get_repos().mcp.list(uid):
        if not server["enabled"]:
            continue
        conn = mcp_runtime.get(uid, server["id"])
        if not conn and reconnect and mcp_runtime.can_reconnect(uid, server["id"]):
            try:
                conn = mcp_runtime.connect(uid, server)
            except BaseException as exc:
                mcp_runtime.mark_failure(uid, server["id"], exc)
                logger.warning("MCP reconnect skipped for %s: %s", server["name"], exc)
                continue
        if not conn:
            continue
        for tool in conn.tools:
            name = "mcp_" + server["id"].replace("-", "_") + "_" + re.sub(r"\W", "_", tool["name"])
            result[name] = McpTool(
                name,
                f"{server['name']}: {tool.get('description', '')} "
                f"Pass JSON arguments using <arguments>...</arguments>. Schema: {json.dumps(tool.get('inputSchema', {}))}",
                server["id"], server["name"], tool["name"], tool.get("inputSchema", {}),
            )
    if in_run():
        trace_emit("armory.discovery.list", component="mcp_runtime", data={"returned_count": len(result)})
    return result


def call_mcp_tool(uid: str, tool: McpTool, arguments: dict[str, Any]) -> dict[str, Any]:
    def trace_outcome(success: bool, reason: str) -> None:
        if in_run():
            trace_emit("tool.call.end", component="mcp_runtime",
                       status="ok" if success else "denied",
                       data={"tool_name": tool.remote_name, "success": success, "reason_code": reason})

    server = deps.get_repos().mcp.get(uid, tool.server_id)
    conn = mcp_runtime.get(uid, tool.server_id)
    live_tool = next((item for item in conn.tools if item.get("name") == tool.remote_name), None) if conn else None
    if not server or not server["enabled"] or not conn or not live_tool:
        trace_outcome(False, "tool_unavailable")
        return {"success": False, "error": "MCP server is disconnected or tool is unavailable"}
    schema = live_tool.get("inputSchema")
    if not isinstance(schema, dict):
        trace_outcome(False, "schema_unavailable")
        return {"success": False, "error": "MCP tool schema is unavailable"}
    required = schema.get("required", [])
    if (not isinstance(required, list) or
            any(not isinstance(name, str) or not name for name in required) or
            len(required) != len(set(required))):
        trace_outcome(False, "schema_invalid")
        return {"success": False, "error": "MCP tool schema is invalid"}
    missing = sorted(name for name in required if name not in arguments)
    if missing:
        trace_outcome(False, "arguments_missing")
        return {"success": False, "error": "MCP arguments are missing required fields", "missing": missing}
    if in_run():
        trace_emit("tool.call.start", component="mcp_runtime",
                   data={"tool_name": tool.remote_name, "arg_keys": list(arguments)})
    try:
        result = conn.run(conn._call(tool.remote_name, arguments))
    except Exception as exc:
        if in_run():
            trace_emit("tool.call.error", component="mcp_runtime", status="error", error=exc,
                       data={"tool_name": tool.remote_name, "reason_code": "mcp_call_failed"})
        raise
    success = not result.get("isError", False)
    trace_outcome(success, "mcp_complete" if success else "mcp_error")
    return {"success": success, **result}
