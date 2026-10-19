from __future__ import annotations

from typing import Any

from api.core.deps import CurrentUser, Repositories
from api.domain.memory import PreferencesUpdateRequest


class PreferencesService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    def get(self, user: CurrentUser) -> dict[str, Any]:
        return self.repos.preferences.get(user.uid)

    def put(self, user: CurrentUser, body: PreferencesUpdateRequest) -> dict[str, Any]:
        prefs = body.model_dump(exclude_none=True)
        agent = prefs.get("agent")
        if agent is not None:
            permitted = {"model_id", "enabled_tools", "enabled_subagents", "confirm_tools",
                          "max_loops", "max_plan_steps", "verbose", "memory_policy_ceiling"}
            if any(key not in permitted for key in agent):
                raise ValueError("Agent policy must be updated through AgentCore")
        return self.repos.preferences.put(user.uid, prefs)
