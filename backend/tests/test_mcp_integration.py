"""MCP handshake, persistence boundary and agent tool execution."""

import asyncio
import sys
import uuid
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from mcp.server.fastmcp import FastMCP

from api.core.deps import CurrentUser
from api.domain.memory import McpCreateRequest, McpUpdateRequest
from api.services.mcp_auth import decrypt, encrypt
from api.services.mcp_runtime import McpConnection, McpRuntime, available_mcp_tools, call_mcp_tool, mcp_runtime
from api.services.mcp_service import McpService


class MemoryRepo:
    def __init__(self):
        self.servers = {}

    def create(self, uid, *, name, url, metadata):
        server = {"id": str(uuid.uuid4()), "name": name, "url": url, "metadata": metadata,
                  "command": metadata.get("command"), "args": metadata.get("args", []),
                  "env": metadata.get("env", {}), "enabled": metadata.get("enabled", True)}
        self.servers[(uid, server["id"])] = server
        return server

    def get(self, uid, server_id):
        return self.servers.get((uid, server_id))

    def list(self, uid):
        return [server for (owner, _), server in self.servers.items() if owner == uid]

    def delete(self, uid, server_id):
        return self.servers.pop((uid, server_id), None) is not None

    def update(self, uid, server_id, **fields):
        server = self.get(uid, server_id)
        if server:
            server.update(fields)
            server["command"] = server["metadata"].get("command")
            server["args"] = server["metadata"].get("args", [])
            server["env"] = server["metadata"].get("env", {})
            server["enabled"] = server["metadata"].get("enabled", True)
        return server


def test_mcp_login_credentials_are_encrypted_and_not_public(monkeypatch):
    monkeypatch.setenv("MCP_CREDENTIALS_KEY", "")
    from api.core.config import get_settings
    get_settings.cache_clear()
    key = __import__("cryptography.fernet", fromlist=["Fernet"]).Fernet.generate_key().decode()
    monkeypatch.setenv("MCP_CREDENTIALS_KEY", key)
    get_settings.cache_clear()
    try:
        repo = MemoryRepo()
        service = McpService(type("Repos", (), {"mcp": repo})())
        user = CurrentUser(uid="alice", session_id="s", role="user", raw={})
        with patch.object(service, "connect", return_value={"logs": []}):
            server = service.create(user, McpCreateRequest(
                name="secure", url="https://mcp.example/mcp",
                auth={"login_url": "https://mcp.example/login", "username": "alice", "password": "secret"},
            ))
        stored = repo.get(user.uid, server["id"])["metadata"]["_auth"]
        assert stored["password"] != "secret"
        assert decrypt(stored["password"]) == "secret"
        assert "password" not in server["auth"]
        assert server["auth"]["password_configured"] is True
    finally:
        get_settings.cache_clear()


def test_agent_credentials_use_current_user_id(monkeypatch):
    from api.core.config import get_settings
    key = __import__("cryptography.fernet", fromlist=["Fernet"]).Fernet.generate_key().decode()
    monkeypatch.setenv("MCP_CREDENTIALS_KEY", key)
    get_settings.cache_clear()
    try:
        repo = MemoryRepo()
        service = McpService(type("Repos", (), {"mcp": repo})())
        user = CurrentUser(uid="agent-user-id", session_id="s", role="user", raw={})
        with patch.object(service, "connect", return_value={"logs": []}):
            server = service.create(user, McpCreateRequest(
                name="secure", url="https://mcp.example/mcp",
                auth={"login_url": "https://mcp.example/auth/login", "username": "", "password": "secret",
                      "use_agent_credentials": True},
            ))
        stored = repo.get(user.uid, server["id"])["metadata"]["_auth"]
        assert stored["username"] == user.uid
        assert server["auth"]["use_agent_credentials"] is True
    finally:
        get_settings.cache_clear()


def test_stdio_import_connect_discover_and_agent_call():
    repo = MemoryRepo()
    repos = type("Repos", (), {"mcp": repo})()
    user = CurrentUser(uid="alice", session_id="s", role="user", raw={})
    with patch("api.core.deps.get_repos", return_value=repos):
        imported = McpService(repos).import_config(user, {"mcpServers": {
            "search": {"command": sys.executable, "args": ["-c", "from mcp.server.fastmcp import FastMCP\nm=FastMCP('test')\n@m.tool()\ndef greet(name: str) -> str:\n    return 'Hello ' + name\nm.run()"]}
        }})
        server = imported["created"][0]
        try:
            assert server["connected"] is True
            assert McpService(repos).details(user, server["id"])["tools"][0]["name"] == "greet"
            tool = next(iter(available_mcp_tools(user.uid).values()))
            assert "Hello Alice" in str(call_mcp_tool(user.uid, tool, {"name": "Alice"}))
            with pytest.raises(HTTPException) as exc:
                McpService(repos).connect(CurrentUser(uid="bob", session_id="s", role="user", raw={}), server["id"])
            assert exc.value.status_code == 404
            McpService(repos).disconnect(user, server["id"])
            assert not McpService(repos).list(user)[0]["connected"]
            assert McpService(repos).connect(user, server["id"])["success"]
            McpService(repos).update(user, server["id"], McpUpdateRequest(enabled=False))
            assert not McpService(repos).list(user)[0]["connected"]
        finally:
            mcp_runtime.close()


def test_invalid_servers_remain_registered_but_never_connected():
    repo = MemoryRepo()
    repos = type("Repos", (), {"mcp": repo})()
    user = CurrentUser(uid="alice", session_id="s", role="user", raw={})
    service = McpService(repos)
    server = service.create(user, McpCreateRequest(name="invalid", command=sys.executable, args=["-c", "import sys;sys.exit(1)"]))
    assert server["connected"] is False
    assert "connection_error" in server
    assert service.list(user)[0]["id"] == server["id"]
    with pytest.raises(HTTPException) as exc:
        service.connect(user, server["id"])
    assert exc.value.status_code == 502
    assert exc.value.detail["logs"][-1]["level"] == "ERROR"
    assert service.list(user)[0]["connection_error"]


def test_connect_cancellation_returns_http_502_instead_of_escaping():
    repo = MemoryRepo()
    repos = type("Repos", (), {"mcp": repo})()
    user = CurrentUser(uid="alice", session_id="s", role="user", raw={})
    service = McpService(repos)
    server = repo.create(
        user.uid,
        name="cancelled",
        url="http://127.0.0.1:1/mcp",
        metadata={"command": None, "transport": "streamable_http", "args": [], "env": {}, "enabled": True},
    )
    with patch("api.services.mcp_service.mcp_runtime.connect", side_effect=asyncio.CancelledError("transport cancelled")):
        with pytest.raises(HTTPException) as exc:
            service.connect(user, server["id"])
    assert exc.value.status_code == 502
    assert "transport cancelled" in exc.value.detail["message"]
    assert exc.value.detail["logs"][-1]["level"] == "ERROR"


def test_stale_connection_cleanup_cancellation_does_not_block_reconnect():
    connection = McpConnection.__new__(McpConnection)
    connection.server = {"id": "server"}
    connection.thread = type("Thread", (), {"is_alive": lambda self: True, "join": lambda self, timeout: None})()
    connection.stopping = None
    connection.worker = type("Worker", (), {"result": lambda self, timeout: (_ for _ in ()).throw(asyncio.CancelledError("cancel scope"))})()
    connection.loop = type("Loop", (), {"call_soon_threadsafe": lambda self, callback: None, "stop": lambda self: None})()
    connection.session = object()

    connection.close()

    assert connection.session is None


def test_http_transport_connects_to_real_streamable_server():
    server_app = FastMCP("http-example", streamable_http_path="/mcp")

    @server_app.tool()
    def double(value: int) -> int:
        return value * 2

    # Run the ASGI server on a real loop in a different thread from the client.
    import socket
    import threading
    import uvicorn

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    config = uvicorn.Config(server_app.streamable_http_app(), log_level="error", lifespan="on")
    http_server = uvicorn.Server(config)
    thread = threading.Thread(target=http_server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if http_server.started:
                break
            thread.join(0.05)
        assert http_server.started
        conn = McpRuntime()
        try:
            session = conn.connect("alice", {"id": "http-test", "url": f"http://127.0.0.1:{port}/mcp", "command": None,
                                             "transport": "streamable_http"})
            assert session.tools[0]["name"] == "double"
            assert session.run(session._call("double", {"value": 4}))["structuredContent"] == {"result": 8}
        finally:
            conn.close()
    finally:
        http_server.should_exit = True
        thread.join(timeout=5)


def test_http_404_is_reported_as_endpoint_error():
    from fastapi import FastAPI
    import socket
    import threading
    import uvicorn

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(FastAPI(), log_level="error"))
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    try:
        for _ in range(100):
            if server.started:
                break
            thread.join(0.05)
        assert server.started
        runtime = McpRuntime()
        try:
            with pytest.raises(Exception):
                runtime.connect("alice", {"id": "missing", "url": f"http://127.0.0.1:{port}/wrong", "command": None,
                                          "transport": "streamable_http"})
            assert "HTTP 404" in runtime.failure("alice", "missing")
        finally:
            runtime.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)


def test_reconnect_cancellation_does_not_escape_tool_catalog():
    repo = MemoryRepo()
    repo.servers[("alice", "unavailable")] = {
        "id": "unavailable", "name": "unavailable", "url": "http://127.0.0.1:1/mcp",
        "command": None, "transport": "streamable_http", "args": [], "env": {}, "enabled": True,
        "metadata": {},
    }
    with patch("api.core.deps.get_repos", return_value=type("Repos", (), {"mcp": repo})()), \
         patch.object(mcp_runtime, "can_reconnect", return_value=True), \
         patch.object(mcp_runtime, "connect", side_effect=asyncio.CancelledError("MCP transport cancelled")):
        assert available_mcp_tools("alice", reconnect=True) == {}
    assert mcp_runtime.failure("alice", "unavailable") == "MCP transport cancelled"
