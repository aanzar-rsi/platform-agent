from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from api.core.deps import CurrentUser, Repositories, get_repos, require_user
from api.domain.chat import (
    ChatCreateRequest,
    ChatDetailOut,
    ChatOut,
    ChatUpdateRequest,
    CheckpointOut,
    CheckpointTreeOut,
    ExtractionDecisionRequest,
    PolicyUpdateRequest,
    RollbackRequest,
)
from api.services.analytics_service import AnalyticsService
from api.services.chat_service import ChatService
from api.services.checkpoint_service import CheckpointService
from api.services.mcp_service import McpService
from api.services.memory_service import MemoryService
from api.services.subagents_service import SubagentsService
from api.services.tools_service import ToolsService
from src.agent.policy_schema import armory_resource_allowed


router = APIRouter(prefix="/agents", tags=["agents"], dependencies=[Depends(require_user)])


def _services(repos: Repositories) -> tuple[ChatService, CheckpointService]:
    return ChatService(repos), CheckpointService(repos)


def _armory(user: CurrentUser, repos: Repositories, agent_id: str) -> dict[str, Any]:
    return ChatService(repos).get_policy(user, agent_id)


@router.post("", response_model=ChatOut)
def create_agent(body: ChatCreateRequest, user: Annotated[CurrentUser, Depends(require_user)],
                 repos: Annotated[Repositories, Depends(get_repos)]) -> ChatOut:
    return ChatService(repos).create(user, body)


@router.get("", response_model=list[ChatOut])
def list_agents(user: Annotated[CurrentUser, Depends(require_user)],
                repos: Annotated[Repositories, Depends(get_repos)]) -> list[ChatOut]:
    return ChatService(repos).list(user)


@router.get("/{agent_id}", response_model=ChatDetailOut)
def get_agent(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
              repos: Annotated[Repositories, Depends(get_repos)]) -> ChatDetailOut:
    return ChatService(repos).get(user, agent_id)


@router.patch("/{agent_id}", response_model=ChatOut)
def update_agent(agent_id: str, body: ChatUpdateRequest,
                 user: Annotated[CurrentUser, Depends(require_user)],
                 repos: Annotated[Repositories, Depends(get_repos)]) -> ChatOut:
    return ChatService(repos).update(user, agent_id, body)


@router.delete("/{agent_id}")
def delete_agent(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                 repos: Annotated[Repositories, Depends(get_repos)]) -> dict:
    return ChatService(repos).delete(user, agent_id)


@router.get("/{agent_id}/armory")
def get_armory(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
               repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    policy = _armory(user, repos, agent_id)
    return {"agent_id": agent_id, "version": policy["version"],
            "armory": policy["policy"]["armory"], **policy}


@router.patch("/{agent_id}/armory")
def update_armory(agent_id: str, body: PolicyUpdateRequest,
                  user: Annotated[CurrentUser, Depends(require_user)],
                  repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    if body.armory is None or body.memory is not None:
        raise HTTPException(status_code=422, detail="Provide only armory")
    updated = ChatService(repos).update_policy(user, agent_id, body)
    return {"agent_id": agent_id, "version": updated["version"],
            "armory": updated["policy"]["armory"], **updated}


@router.get("/{agent_id}/armory/tools")
def get_agent_tools(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                    repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    armory = _armory(user, repos, agent_id)["policy"]["armory"]
    catalog = ToolsService(repos).list_catalog(user)
    internal = [tool for tool in catalog["internal"]
                if armory_resource_allowed(armory, group="tools", name=tool["name"])]
    mcp = [tool for tool in catalog["mcp"]
           if armory_resource_allowed(armory, group="tools", name=tool["name"])]
    return {"internal": internal, "mcp": mcp,
            "counts": {"internal": len(internal), "mcp": len(mcp)}}


@router.get("/{agent_id}/armory/mcp")
def get_agent_mcp(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                  repos: Annotated[Repositories, Depends(get_repos)]) -> list[dict[str, Any]]:
    armory = _armory(user, repos, agent_id)["policy"]["armory"]
    configured = armory.get("resources", {}).get("mcp_servers", [])
    enabled = {item.get("name") for item in configured if item.get("enabled", True)}
    if not armory.get("groups", {}).get("mcp_servers", {}).get("enabled", False):
        return []
    return [server for server in McpService(repos).list(user)
            if "*" in enabled or server.get("name") in enabled or server.get("id") in enabled]


@router.get("/{agent_id}/armory/subagents")
def get_agent_subagents(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                        repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    armory = _armory(user, repos, agent_id)["policy"]["armory"]
    entries = SubagentsService().list_catalog(uid=user.uid)["subagents"]
    entries = [entry for entry in entries
               if armory_resource_allowed(armory, group="subagents", name=entry["name"])]
    return {"subagents": entries, "counts": {"subagents": len(entries)}}


@router.get("/{agent_id}/memory")
def get_agent_memory(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                     repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    policy = ChatService(repos).get_policy(user, agent_id)
    return {
        "agent_id": agent_id,
        "version": policy["version"],
        "policy": policy["policy"]["memory"],
        "ceiling": policy["ceiling"]["memory"],
        "entries": [entry.model_dump() for entry in MemoryService(repos).get(user)],
        "extraction_requests": ChatService(repos).list_extraction_requests(user, agent_id),
    }


@router.patch("/{agent_id}/memory")
def update_agent_memory(agent_id: str, body: PolicyUpdateRequest,
                        user: Annotated[CurrentUser, Depends(require_user)],
                        repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    if body.memory is None or body.armory is not None:
        raise HTTPException(status_code=422, detail="Provide only memory")
    updated = ChatService(repos).update_policy(user, agent_id, body)
    return {"agent_id": agent_id, "version": updated["version"],
            "memory": updated["policy"]["memory"], **updated}


@router.get("/{agent_id}/memory/extraction-requests")
def list_memory_extraction_requests(agent_id: str, state: str | None = None,
                                    user: Annotated[CurrentUser, Depends(require_user)] = None,
                                    repos: Annotated[Repositories, Depends(get_repos)] = None) -> list[dict]:
    return ChatService(repos).list_extraction_requests(user, agent_id, state=state)


@router.post("/{agent_id}/memory/extraction-requests/{request_id}")
def review_memory_extraction_request(agent_id: str, request_id: str, body: ExtractionDecisionRequest,
                                     user: Annotated[CurrentUser, Depends(require_user)],
                                     repos: Annotated[Repositories, Depends(get_repos)]) -> dict:
    return ChatService(repos).review_extraction_request(user, agent_id, request_id, body)


@router.get("/{agent_id}/analytics")
def get_agent_analytics(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                        repos: Annotated[Repositories, Depends(get_repos)],
                        from_ts: Annotated[str | None, Query(alias="from")] = None,
                        to_ts: Annotated[str | None, Query(alias="to")] = None) -> dict[str, Any]:
    ChatService(repos)._owned(agent_id, user)
    return AnalyticsService(repos).summary(user, agent_id=agent_id, start=from_ts, end=to_ts)


@router.get("/{agent_id}/checkpoints", response_model=list[CheckpointOut])
def list_checkpoints(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                     repos: Annotated[Repositories, Depends(get_repos)]) -> list[CheckpointOut]:
    return CheckpointService(repos).list(user, agent_id)


@router.get("/{agent_id}/checkpoints/tree", response_model=list[CheckpointTreeOut])
def checkpoint_tree(agent_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                    repos: Annotated[Repositories, Depends(get_repos)]) -> list[CheckpointTreeOut]:
    return CheckpointService(repos).tree(user, agent_id)


@router.post("/{agent_id}/rollback")
def rollback(agent_id: str, body: RollbackRequest,
             user: Annotated[CurrentUser, Depends(require_user)],
             repos: Annotated[Repositories, Depends(get_repos)]) -> dict:
    result = CheckpointService(repos).rollback(user, agent_id, body)
    from api.services.chat_runtime_manager import get_runtime_manager
    get_runtime_manager().fence_queue(agent_id)
    get_runtime_manager().enqueue_control(agent_id, "checkpoint.created",
                                          {"checkpoint_id": body.checkpoint_id, "rollback": True})
    return result
