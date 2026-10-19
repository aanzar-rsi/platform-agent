# draw.io Schematic Blueprint (v2)

Use this document as the standard blueprint when creating architecture diagrams for this repository.

Create one draw.io file with the sheets below.

---

## Sheet 1 — Agent Graph Visualisation

**Purpose:** show the LangGraph runtime flow and node routing.

### Include

- Start node (`run_turn` / runtime entry)
- Planner/agent node
- Conditional routing edges:
  - tool execution
  - subagent delegation
  - context selection
  - human input wait
  - final response / END
- Checkpointer integration (PostgreSQL)
- Loop-back edge from execution nodes to planner

### Annotation

- Label each edge with routing condition/action name.
- Mark persistent state boundaries (checkpointed vs transient).

---

## Sheet 2 — App Running Visualisation

**Purpose:** show how backend and frontend are started and interact at runtime.

### Include

- `./run_dev` launcher
- backend process (`backend/.venv/bin/python main.py`)
- frontend process (`frontend/npm run dev`)
- browser client
- REST/API channel (`/v1/...`)
- WebSocket channel (`/v1/ws/chats/{chat_id}`)

### Annotation

- Show local dev ports used by backend and frontend.
- Mark auth boundary and token usage points.

---

## Sheet 3 — Codeflow

**Purpose:** request-to-response path through code layers.

### Include

1. Frontend user action
2. API route entry
3. service/repository layer
4. agent runtime call
5. model/tool/subagent step
6. persistence/checkpoint write
7. streamed/final response to client

### Annotation

- Use directional arrows with file references where possible.
- Distinguish sync vs async paths.

---

## Sheet 4 — Logic View

**Purpose:** business logic ownership by module.

### Include

- API domain logic (auth, chats, memory, files)
- Agent policy/constraints
- Prompt/render logic
- LLM client adapter logic
- Tool selection and execution logic

### Annotation

- For each block, include:
  - owner directory
  - key inputs/outputs
  - major invariants or constraints

---

## Sheet 5 — Subroutines

**Purpose:** reusable internal flows and helpers.

### Include

- Checkpoint save/load
- context memory update/select
- tool invocation pipeline
- trace/log emission
- KB write/search/import paths

### Annotation

- Show error handling branches.
- Mark external dependencies (DB, LLM gateway, embeddings).

---

## Sheet 6 — Agent Creation

**Purpose:** lifecycle for creating and registering agents/subagents.

### Include

- prompt/module assembly
- node registration
- graph wiring (edges/routes)
- policy attachment
- tool exposure
- runtime registration and invocation constraints

### Annotation

- Identify required files to modify for a new agent/subagent.
- Include validation/testing checkpoints before release.

---

## Visual standards (all sheets)

- Use one color per subsystem:
  - frontend
  - API
  - agent runtime
  - persistence
  - external providers
- Keep labels short and file-path based.
- Prefer left-to-right flow.
- Add a legend box on every sheet.
- Add a footer with date, version (`v2`), and editor initials.
