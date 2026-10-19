"""Policy endpoints use the saved AgentCore and require chat ownership."""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from api.core.deps import CurrentUser
from api.domain.chat import PolicyUpdateRequest
from api.services.chat_service import ChatService
from src.agent.agent_core import default_policy


def test_policy_read_and_update_are_owned_and_versioned():
    policy = default_policy().as_dict()
    row = {"agent_id": "chat-1", "owner_id": "owner-1", "owner_type": "user",
           "parent_agent_id": None, "state": "open", "policy": policy,
           "policy_ceiling": policy, "policy_version": 1}
    repos = Mock()
    repos.sessions.get.return_value = {"agent_id": "chat-1", "owner_id": "owner-1", "deleted": False}
    repos.agents.for_agent.return_value = row

    def update(agent_id, section, scope, *, uid, expected_version):
        assert (agent_id, uid) == ("chat-1", "owner-1")
        if expected_version != row["policy_version"]:
            raise ValueError("policy_conflict")
        row["policy"] = {**row["policy"], section: scope}
        row["policy_version"] += 1
        return row

    repos.agents.update_policy.side_effect = update
    service = ChatService(repos)
    user = CurrentUser(uid="owner-1", session_id="session", role="user", raw={})
    assert service.get_policy(user, "chat-1")["version"] == 1
    narrowed = service.update_policy(user, "chat-1", PolicyUpdateRequest(
        expected_version=1, memory={"read": ["USER"]}))
    assert narrowed["policy"]["memory"]["read"] == ["USER"]
    restored = service.update_policy(user, "chat-1", PolicyUpdateRequest(
        expected_version=2, memory={"read": ["USER", "AGENT"]}))
    assert restored["version"] == 3
    with pytest.raises(HTTPException) as exc:
        service.update_policy(user, "chat-1", PolicyUpdateRequest(
            expected_version=1, memory={"read": ["USER"]}))
    assert exc.value.status_code == 409
    with pytest.raises(HTTPException) as exc:
        service.update_policy(user, "chat-1", PolicyUpdateRequest(
            expected_version=3, guardrails={"enabled": False}))
    assert exc.value.status_code == 422
    with pytest.raises(HTTPException) as exc:
        service.get_policy(CurrentUser(uid="other", session_id="session", role="user", raw={}), "chat-1")
    assert exc.value.status_code == 403
