from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from api.core.deps import CurrentUser, Repositories, get_repos, require_user
from api.domain.memory import McpCreateRequest, McpUpdateRequest
from api.services.mcp_service import McpService
from api.services.subagents_service import SubagentsService
from api.services.tools_service import ToolsService


router = APIRouter(prefix="/armory", tags=["armory"], dependencies=[Depends(require_user)])


@router.get("")
def get_armory() -> dict[str, list[str]]:
    return {"resources": ["tools", "mcp", "subagents"]}


@router.get("/tools")
def list_tools(user: Annotated[CurrentUser, Depends(require_user)],
               repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    return ToolsService(repos).list_catalog(user)


@router.get("/subagents")
def list_subagents(user: Annotated[CurrentUser, Depends(require_user)]) -> dict[str, Any]:
    return SubagentsService().list_catalog(uid=user.uid)


@router.get("/mcp")
def list_mcp(user: Annotated[CurrentUser, Depends(require_user)],
             repos: Annotated[Repositories, Depends(get_repos)]) -> list[dict[str, Any]]:
    return McpService(repos).list(user)


@router.post("/mcp")
def create_mcp(body: McpCreateRequest, user: Annotated[CurrentUser, Depends(require_user)],
               repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    return McpService(repos).create(user, body)


@router.post("/mcp/import")
def import_mcp(body: dict[str, Any], user: Annotated[CurrentUser, Depends(require_user)],
               repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    return McpService(repos).import_config(user, body)


@router.get("/mcp/{server_id}")
def get_mcp(server_id: str, user: Annotated[CurrentUser, Depends(require_user)],
            repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    return McpService(repos).details(user, server_id)


@router.patch("/mcp/{server_id}")
def update_mcp(server_id: str, body: McpUpdateRequest,
               user: Annotated[CurrentUser, Depends(require_user)],
               repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    return McpService(repos).update(user, server_id, body)


@router.delete("/mcp/{server_id}")
def delete_mcp(server_id: str, user: Annotated[CurrentUser, Depends(require_user)],
               repos: Annotated[Repositories, Depends(get_repos)]) -> dict:
    return McpService(repos).delete(user, server_id)


@router.post("/mcp/{server_id}/connect")
def connect_mcp(server_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    return McpService(repos).connect(user, server_id)


@router.post("/mcp/{server_id}/disconnect")
def disconnect_mcp(server_id: str, user: Annotated[CurrentUser, Depends(require_user)],
                   repos: Annotated[Repositories, Depends(get_repos)]) -> dict[str, Any]:
    return McpService(repos).disconnect(user, server_id)
