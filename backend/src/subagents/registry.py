"""Catalog of sub-agents that meta agents main planner can delegate a task to.


Mirrors the `INTERNAL_TOOLS` convention in `src/tools/__init__.py`: builtins

are an explicit list.

"""



from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

@dataclass(frozen=True)

class SubagentSpec:
    """Describes one planner-callable sub-agent."""
    name: str
    display_name: str
    description: str
    when_to_use: str
    adapter: Callable[[str, dict[str, Any]], str]
    scope: str = ""
    availability: str = "On demand when the planner delegates"
    tools: tuple[str, ...] = ()
    source: str = "builtin"
    agent_id: str | None = None
    status: str | None = None
    enabled: bool = True

BUILTIN_SUBAGENTS: list[SubagentSpec] = []

# Back-compat aliases used by older imports/tests.
SUBAGENTS: list[SubagentSpec] = BUILTIN_SUBAGENTS
SUBAGENT_MAP: dict[str, SubagentSpec] = {spec.name: spec for spec in BUILTIN_SUBAGENTS}


def get_subagents(uid: str | None = None) -> list[SubagentSpec]:
    """Builtin sub-agents (uid accepted for back-compat, currently unused)."""

    return list(BUILTIN_SUBAGENTS)

def resolve_subagent(name: str, uid: str | None = None) -> SubagentSpec | None:
    for spec in get_subagents(uid):
        if spec.name == name:
            return spec

    return None

__all__ = [
    "SubagentSpec",
    "BUILTIN_SUBAGENTS",
    "SUBAGENTS",
    "SUBAGENT_MAP",
    "get_subagents",
    "resolve_subagent",
]
