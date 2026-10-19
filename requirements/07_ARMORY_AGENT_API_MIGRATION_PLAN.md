# Armory and Agent API Migration Plan

## Decisions

- "Global" resources are scoped to the authenticated user, except built-in tools and subagents, which are platform catalogs visible to authenticated users.
- The canonical armory resource groups are `tools`, `mcp`, and `subagents`.
- Old `/v1/chats`, `/v1/tools`, `/v1/mcp`, and `/v1/subagents` endpoints are removed without compatibility aliases.
- Agent memory returns its effective policy, visible memory entries, and extraction requests in one response.
- `/v1/ws/agents/{agent_id}` remains unchanged.

## Target API

### Global Armory

- `GET /v1/armory`
- `GET /v1/armory/tools`
- `GET /v1/armory/mcp`
- `POST /v1/armory/mcp`
- `POST /v1/armory/mcp/import`
- `GET /v1/armory/mcp/{server_id}`
- `PATCH /v1/armory/mcp/{server_id}`
- `DELETE /v1/armory/mcp/{server_id}`
- `POST /v1/armory/mcp/{server_id}/connect`
- `POST /v1/armory/mcp/{server_id}/disconnect`
- `GET /v1/armory/subagents`

### Agents

- `POST /v1/agents`
- `GET /v1/agents`
- `GET /v1/agents/{agent_id}`
- `PATCH /v1/agents/{agent_id}`
- `DELETE /v1/agents/{agent_id}`
- `GET /v1/agents/{agent_id}/armory`
- `PATCH /v1/agents/{agent_id}/armory`
- `GET /v1/agents/{agent_id}/armory/tools`
- `GET /v1/agents/{agent_id}/armory/mcp`
- `GET /v1/agents/{agent_id}/armory/subagents`
- `GET /v1/agents/{agent_id}/memory`
- `PATCH /v1/agents/{agent_id}/memory`
- `GET /v1/agents/{agent_id}/memory/extraction-requests`
- `POST /v1/agents/{agent_id}/memory/extraction-requests/{request_id}`
- `GET /v1/agents/{agent_id}/analytics`
- `GET /v1/agents/{agent_id}/checkpoints`
- `GET /v1/agents/{agent_id}/checkpoints/tree`
- `POST /v1/agents/{agent_id}/rollback`

### Global Resources

- `GET|PUT|DELETE /v1/memory`
- `POST /v1/memory/entries`
- `GET /v1/analytics`

## Implementation Steps

1. Replace the chats router with an agents router and move checkpoint routes under it.
2. Add a global armory router backed by the existing tools, MCP, and subagent services.
3. Add agent-scoped armory catalogs filtered by the agent's effective policy.
4. Add combined agent memory and agent-filtered analytics endpoints.
5. Remove the unused Agent Studio frontend API and UI behavior.
6. Migrate all frontend HTTP calls to the new hierarchy.
7. Add route and frontend/backend contract checks, then run focused backend tests and the frontend build.
