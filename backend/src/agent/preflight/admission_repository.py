from __future__ import annotations

from typing import Any

from . import repository


class AdmissionRepository:
    """Data access helpers for admission decisions."""

    def get_active_auth_session(self, session_id: str, user_id: str) -> dict[str, Any] | None:
        return repository.get_active_auth_session(session_id, user_id)

    def count_recent_user_requests_per_minute(self, user_id: str) -> int:
        return repository.count_recent_user_requests_per_minute(user_id)

    def count_recent_tenant_requests_per_minute(self, tenant_id: str) -> int:
        return repository.count_recent_tenant_requests_per_minute(tenant_id)

    def get_open_conversation_activity(self, agent_id: str, owner_id: str) -> dict[str, Any] | None:
        return repository.get_open_conversation_activity(agent_id, owner_id)
