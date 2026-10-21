"""Policy defaults and intersection helpers."""

from __future__ import annotations

from src.agent.agent_models import Policy
from src.agent.policy_schema import (
    intersect_armory,
    intersect_memory,
    normalize_armory_policy,
    normalize_memory_policy,
)


def default_policy(runtime: dict | None = None) -> Policy:
    from src.tools import INTERNAL_TOOLS
    from src.subagents.registry import get_subagents

    tools = [t.name for t in INTERNAL_TOOLS]
    subagents = [s.name for s in get_subagents()]
    armory = normalize_armory_policy(
        {
            "resources": {
                "tools": [{"type": "tool", "name": name, "enabled": True} for name in tools],
                "subagents": [{"type": "subagent", "name": name, "enabled": True} for name in subagents],
                "mcp_servers": [{"type": "mcp_server", "name": "*", "enabled": True}],
            },
            "groups": {
                "tools": {"enabled": True},
                "subagents": {"enabled": True},
                "mcp_servers": {"enabled": True},
            },
            "confirm_tools": True,
        }
    )
    memory = normalize_memory_policy({"read": ["USER", "AGENT"], "write": ["USER"], "tenant_id": None})
    return Policy(
        armory=armory,
        memory=memory,
        guardrails={"confirm_tools": True},
        observability={"enabled": True},
    )


def _allowed(parent: list | None, requested: list | None, platform: list | None) -> list | None:
    lists = [items for items in (parent, requested, platform) if items is not None]
    return [item for item in lists[0] if all(item in allowed for allowed in lists[1:])] if lists else None


def intersect_policy(parent: Policy, requested: Policy | None = None, platform: Policy | None = None) -> Policy:
    """A child cannot grant capabilities, scopes or a tenant its parent lacks."""
    requested = requested or parent
    platform = platform or parent
    memory = intersect_memory(parent.memory, requested.memory, platform.memory)
    armory = intersect_armory(parent.armory, requested.armory, platform.armory)
    legacy_memory = {key: memory.get(key) for key in ("read", "write", "tenant_id")}
    return Policy(
        armory=armory,
        memory={**memory, **legacy_memory},
        guardrails=parent.guardrails,
        observability=parent.observability,
        version=parent.version,
    )
