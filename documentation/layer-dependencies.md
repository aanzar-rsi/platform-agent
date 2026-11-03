# Cross-layer dependencies

This is the dependency policy for the current `frontend/` and `backend/` implementation. An arrow `A → B` means A may call or import B; an HTTP/WebSocket arrow is a network call, not a source import. See [component and dependency diagram](component-dependency-diagram.md) for the connected view.

## Permitted dependencies

| Caller | May depend on | Boundary and examples |
|---|---|---|
| `frontend/src/pages`, `components`, `hooks` | Frontend UI, auth hook, `lib/api.ts`, `lib/websocket.ts`, frontend types | Render state and issue API requests; `EnhancedChatView.tsx` consumes both API and WebSocket clients. |
| `frontend/src/lib/api.ts`, `lib/websocket.ts` | Backend `/v1` HTTP and `/v1/ws/agents/{agent_id}` WebSocket contracts | `VITE_API_URL` and `VITE_WS_URL` select the hosts. `lib/api.ts` supplies the bearer token; `lib/websocket.ts` uses it for the connection. |
| `backend/api/api_routes`, `api/ws/endpoint.py` | `api/core` auth/dependencies, `api/domain` request/response models, `api/services` | Validate the transport, authenticate the user and delegate operations. The WebSocket endpoint checks agent ownership before attaching to the runtime manager. |
| `backend/api/services` | `api/db/repositories`, other services, and specific `src/` runtime/policy entrypoints | Coordinate ownership, preloading, preferences and runs. `agent_runtime.py` invokes the graph through `src.agent.graph`; `tools_service.py` reads the tool catalog. |
| `backend/src/cli` | Shared agent runtime plus API authentication, repository and MCP integration | The CLI is a second entrypoint; `src/cli/repl.py` calls the common `run_turn()` and uses API repositories. |
| `backend/src/agent/graph.py` and nodes | Agent state, policy, prompts, model client, Armory, checkpointer | `graph.py` wires planner → input security → execution dispatcher → executors → result collector → output security. `agentnode.py` calls `src/models/llm_client.py`. |
| `backend/src/agent`, learner, and repository implementations | Narrow cross-package persistence/resource integration | Existing exceptions to a strictly one-way dependency: `src/agent/kb.py` and learner code use `api.db` repositories; `src/agent/facets.py` uses `api.services.mcp_runtime`; `api/db/repositories/agents.py` imports `src.agent.policy_schema`. Keep these dependencies confined to integration points. |
| `backend/api/db/repositories` and `src/utils/postgres_checkpointer.py` | PostgreSQL | Repositories own application records; the checkpointer owns LangGraph checkpoint persistence and mirrors messages. `api/services/chat_runtime_manager.py` persists execution events through a repository. |
| `backend/src/agent/facets.py` | `src/tools`, `src/subagents/registry.py`, API MCP runtime | Armory discovers and invokes authorized tools, subagents and MCP resources; tool implementations may call the shared LLM client where required. |

## Prohibited dependencies

- Do not import Python `backend/api` or `backend/src` modules into frontend code, or expose database credentials to the browser. Cross this boundary through the authenticated HTTP/WebSocket contracts.
- Do not let UI components query PostgreSQL, invoke the graph/checkpointer, or call the LLM gateway directly. Use frontend API clients and backend routes/runtime respectively.
- Do not move authentication, ownership checks or policy enforcement into frontend-only logic. REST uses `api/core/deps.py`; WebSocket validates token and ownership in `api/ws/endpoint.py`; execution authorization belongs to agent policy/Armory.
- Do not let transport routes implement planner decisions or directly write checkpoint tables. Delegate to services/runtime and the LangGraph checkpointer.
- Do not add unrelated `src.agent` → `api.api_routes` or `api.ws` imports. The existing reverse dependencies serve persistence and resource integration; new agent behavior belongs in the runtime, with transport adapters at the API edge.
- Do not bypass `src/models/llm_client.py` for new LLM calls, or bypass Armory authorization and the graph's input/output gates for executable actions.

## Scope of the rules

These are conventions for new work, not an assertion that the backend packages are acyclic: API services call the agent, while parts of the agent/learner call API repositories and MCP services. Shared PostgreSQL and the external LLM gateway are infrastructure, not an invitation for UI or route-level direct access. Consult [`backend-codebase.md`](backend-codebase.md) for runtime detail and [`backend-api.md`](backend-api.md) for transport contracts; older descriptions of file-backed data or `/ws/chats/` there are historical.
