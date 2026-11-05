# Component and dependency diagram

Arrows point from a caller to the component it uses. Solid arrows are in-process dependencies; labels `HTTP`, `WS`, `SQL` and `gateway` mark external calls. This is the current high-level component map, not the individual LangGraph node transition diagram.

```mermaid
flowchart LR
    subgraph browser["Browser - frontend/src"]
        UI["Routes, pages and components"]
        AUTH["AuthProvider / useAuth"]
        HTTP["lib/api.ts"]
        WSCLIENT["lib/websocket.ts"]
        UI --> AUTH
        UI --> HTTP
        UI --> WSCLIENT
        AUTH --> HTTP
        WSCLIENT -->|token| HTTP
    end

    subgraph server["Python backend"]
        ROUTES["api/api_routes - REST"]
        WS["api/ws/endpoint.py"]
        SEC["api/core - JWT and session validation"]
        SERVICES["api/services - chat, memory, MCP, etc."]
        MANAGER["ChatRuntimeManager / AgentRuntime"]
        REPOS["api/db/repositories"]
        CLI["src/cli"]
        GRAPH["src/agent/graph.py - LangGraph"]
        NODES["src/agent/nodes - planner, gates, dispatcher, executors, collector"]
        ARMORY["src/agent/facets.py - Armory / Memory"]
        RESOURCES["src/tools and src/subagents"]
        MCP["api/services/mcp_runtime.py"]
        LEARNER["src/subagents/learner_agent and src/agent/kb.py"]
        PROMPTS["src/prompts"]
        LLM["src/models/llm_client.py"]
        CP["src/utils/postgres_checkpointer.py"]

        ROUTES --> SEC
        WS --> SEC
        ROUTES --> SERVICES
        WS --> MANAGER
        SERVICES --> REPOS
        SERVICES --> MANAGER
        SERVICES --> GRAPH
        MANAGER --> REPOS
        MANAGER --> GRAPH
        CLI --> GRAPH
        CLI --> REPOS
        GRAPH --> NODES
        GRAPH --> CP
        NODES --> ARMORY
        NODES --> PROMPTS
        NODES --> LLM
        ARMORY --> RESOURCES
        ARMORY --> MCP
        ARMORY --> REPOS
        LEARNER --> GRAPH
        LEARNER --> REPOS
        LEARNER --> LLM
        MCP --> REPOS
    end

    DB["PostgreSQL"]
    GATEWAY["OpenAI-compatible LLM gateway"]
    EXT["External MCP servers"]

    HTTP -->|HTTP /v1| ROUTES
    WSCLIENT -->|WS /v1/ws/agents/:agent_id| WS
    REPOS -->|SQL| DB
    CP -->|SQL checkpoints and messages| DB
    LLM -->|gateway| GATEWAY
    MCP -->|MCP| EXT
```

**Reading the execution path:** the WebSocket endpoint validates the user/agent, then the runtime manager starts `AgentRuntime`. It runs the compiled graph; the planner uses prompts and the shared LLM client, and the graph routes validated actions through Armory/child/human executors, result collection and the output security gate. Checkpoints and execution events persist to PostgreSQL. The CLI enters the same graph without the HTTP/WebSocket transport. The learner runs separately and consumes saved trajectory data.

**Cross-package exception:** the graph and API do not form a strict dependency pyramid. Runtime/learner code uses API repositories and MCP services, and repository policy code imports `src.agent.policy_schema`. See [cross-layer dependencies](layer-dependencies.md) for the permitted and prohibited boundaries.
