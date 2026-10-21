from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator
from urllib.parse import urlparse


class MemoryEntry(BaseModel):
    key: str
    value: str
    category: str = "general"
    updated_at: str | None = None


class MemoryPutRequest(BaseModel):
    entries: list[MemoryEntry]


class MemoryAddRequest(BaseModel):
    key: str
    value: str
    category: str = "general"


class PreferencesUpdateRequest(BaseModel):
    theme: str | None = None
    console_mode: str | None = None
    agent: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_agent_preferences(self):
        allowed = {"model_id", "confirm_tools",
                   "max_loops", "max_plan_steps", "verbose", "memory_policy_ceiling"}
        if self.agent is not None and set(self.agent) - allowed:
            raise ValueError("Agent policy must be updated through AgentCore")
        return self


class McpCreateRequest(BaseModel):
    name: str
    url: str | None = None
    command: str | None = None
    transport: str | None = None
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)
    enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_transport(self):
        if not self.name.strip() or bool(self.url) == bool(self.command):
            raise ValueError("Provide a name and exactly one of url or command")
        if self.url and (urlparse(self.url).scheme not in ("http", "https") or not urlparse(self.url).netloc):
            raise ValueError("MCP URL must use http or https")
        if self.command is not None and not self.command.strip():
            raise ValueError("Command cannot be blank")
        if self.transport not in (None, "stdio", "streamable_http", "sse"):
            raise ValueError("Transport must be stdio, streamable_http, or sse")
        if self.transport == "stdio" and not self.command:
            raise ValueError("Stdio transport requires a command")
        if self.transport in ("sse", "streamable_http") and not self.url:
            raise ValueError("HTTP transport requires a URL")
        if self.command and (not all(isinstance(arg, str) for arg in self.args) or not all(isinstance(value, str) for value in self.env.values())):
            raise ValueError("Stdio arguments and environment values must be strings")
        return self


class McpUpdateRequest(BaseModel):
    name: str | None = None
    url: str | None = None
    command: str | None = None
    transport: str | None = None
    args: list[str] | None = None
    env: dict[str, str] | None = None
    enabled: bool | None = None
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_url(self):
        if self.url is not None and self.url and (urlparse(self.url).scheme not in ("http", "https") or not urlparse(self.url).netloc):
            raise ValueError("MCP URL must use http or https")
        return self
