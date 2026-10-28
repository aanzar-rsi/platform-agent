# Platform Agent Codebase Documentation

## Purpose and Architecture

Platform is a multi-user agent platform with two front ends over the same LangGraph agent:

- An authenticated terminal interface (`python main.py --cli`).
- A FastAPI server with REST management endpoints and WebSocket turn streaming (`python main.py`).

The central agent is a planner/executor loop. Each planner visit asks an LLM for one next action. The graph then either executes an internal tool, delegates to a registered sub-agent, loads a selected portion of prior result data, waits for user input, or returns a final answer. LangGraph checkpoints every super-step in PostgreSQL, which enables history, pauses, rollback, and branch-aware experience learning.

```text
CLI or WebSocket client
        |
        v
run_turn() / AgentRuntime
        |
        v
LangGraph agent_app + PostgreSQL checkpointer
        |
        v
agent_node --conditional route--> tool | subagent | context selector | human input | END
        ^                                  |             |                 |
        +----------------------------------+-------------+-----------------+

Idle learner (separate graph): load checkpoint -> extract governed memories -> persist KB versions/index
```

## Repository Map

| Area | Responsibility | Important files |
|---|---|---|
| Entrypoints | Chooses API or terminal UI | `main.py`, `api/main.py` |
| Agent graph | LangGraph state machine and routing | `src/agent/graph.py`, `src/agent/state.py`, `src/agent/edges/routing.py` |
| Agent nodes | LLM planning, tools, delegation, context selection, questions | `src/agent/nodes/` |
| Prompt system | Template syntax, rendering, main planner prompt | `src/prompts/` |
| LLM layer | OpenAI-compatible gateway calls, streaming, logging, replay | `src/models/llm_client.py` |
| Tools | Built-in capabilities available to the planner | `src/tools/` |
| Terminal UI | Login, chat commands, Rich rendering and interrupts | `src/cli/` |
| HTTP API | Routes, services, authentication, WebSocket protocol | `api/` |
| Persistence | PostgreSQL repositories and LangGraph checkpointer | `api/db/`, `src/utils/postgres_checkpointer.py` |
| Learning agent | Derives and retrieves governed decision-aware memory | `src/subagents/learner_agent/` |
| Tests | Focused behavior and integration coverage | `tests/` |

## Startup and Configuration

### Entrypoints

`main.py` is the intended root entrypoint:

```bash
python main.py          # FastAPI server
python main.py --cli    # authenticated terminal interface
```

For direct API startup, `api/main.py` creates the FastAPI app and starts Uvicorn. It deliberately runs with `workers=1`, because `ChatRuntimeManager` and its packet queues are process-local. Multiple workers would split a chat's queue and WebSocket state across processes.

`src/bootstrap.py` can re-exec into the project virtual environment for local entrypoints. API startup sets `SKIP_VENV_REEXEC=1` because Uvicorn already owns the process.

### Environment

`src/config.py` loads `.env`, creates the required `data/` and `logs/` directories, and exposes the shared `settings` object. `api/core/config.py` holds corresponding API settings. The documented starting values are in `.env.example`.

Important settings:

| Setting | Meaning |
|---|---|
| `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD` | PostgreSQL connection details |
| `LLM_GATEWAY_URL`, `LLM_GATEWAY_API_KEY`, `LLM_MODEL_ID` | OpenAI-compatible LiteLLM gateway and default model |
| `BRAVE_SEARCH_API_KEY` | Optional primary provider for web search |
| `LLM_CALL_LOG_ENABLED`, `LLM_CALL_LOG_TO_DB` | Full LLM request/response recording |
| `MOCK_LLM_CALL` | Replay an identical prior logged LLM call when available |
| `EMBED_METHOD` | `hf` for Sentence Transformers or `numpy` for hashing embeddings |
| `MAX_LOOPS` | LangGraph recursion limit per turn |
| `MAX_SUBAGENT_CALLS_PER_TURN` | Hard cap for one named sub-agent in a user turn |
| `EXPERIENCE_*` | Enables learner, idle threshold, polling interval, and retrieval count |

## Main Agent Graph

### State

`PlanExecuteState` in `src/agent/state.py` is the durable LangGraph state. Its key fields are:

| Field | Meaning |
|---|---|
| `messages` | Conversation messages; LangGraph's `add_messages` reducer appends updates. |
| `execution_history` | Ordered tool/sub-agent metadata and results for the current scratch plan. |
| `execution_memory` | Full keyed result payloads, such as `tool_1` and `subagent_2`. |
| `context_memory` | Token-budgeted FIFO subset of result payloads visible in the next planner prompt. |
| `current_task` | Planner's current task description. |
| `next_step` | Action chosen by the planner and parsed by the router. |
| `preloaded_context` | User, preferences, memory, and MCP registry captured when the chat is created. |
| `coreid`, `sessionid` | Observability and session identifiers. |

`AgentConfig` is the stable runtime configuration injected through LangGraph's `configurable` section. It includes the user ID, chat/thread ID, loop limit, selected model, enabled capabilities, confirmation setting, and sub-agent call limit.

### Topology

`src/agent/graph.py` defines and compiles the graph:

```text
START
  |
  v
agent_node
  |-- action=tool ----------> tool_node -----------> agent_node
  |-- action=subagent ------> subagent_node -> subagent_gate -> agent_node
  |-- action=context_select -> context_selector ---> agent_node
  |-- action=ask_user ------> human_input ---------> agent_node
  `-- action=finish --------> END
```

`route_from_agent()` in `src/agent/edges/routing.py` reads `next_step.action`. Unknown actions are intentionally treated as `finish`, preventing the graph from entering an undefined route.

The graph is compiled once as `agent_app` with the PostgreSQL checkpointer from `src/utils/postgres_checkpointer.py`.

### Planner: `agent_node`

`src/agent/nodes/agentnode.py` is the reasoning core. On every visit it:

1. Checks the cooperative pause gate before performing work.
2. Reads the latest human message and detects whether this is the first planner visit after it.
3. Loads the bounded `context_memory`, metadata-only history, and an index of all execution-memory keys.
4. Retrieves relevant learned experiences with a four-second timeout. Retrieval is advisory: errors and timeouts become `(none)`, not a failed turn.
5. Filters tools and sub-agents using runtime capability settings.
6. Renders the planner's system and user prompts.
7. Streams the LLM response through `call_llm_stream()`.
8. Exposes only tagged `<reasoning>` or `<output>` text to the UI, depending on whether the planner is exiting.
9. Parses the XML-like response into `next_step`, state updates, and an `AIMessage`.

The expected planner output is deliberately constrained. A non-final response contains `<planner_exit>False</planner_exit>` and selects one action. A final response contains `<planner_exit>True</planner_exit>` and an `<output>` block. `_parse_response()` maps planner values to graph actions:

| Planner output | State action | Next node |
|---|---|---|
| Tool call / default non-final action | `tool` | `tool_node` |
| `<action>agent_call</action>` | `subagent` | `subagent_node` |
| `<action>context_select</action>` | `context_select` | `context_selector` |
| `<action>ask_user</action>` | `ask_user` | `human_input` |
| `<planner_exit>True</planner_exit>` | `finish` | `END` |

At the start of a user turn, the prompt requires `<session_intent>continue</session_intent>` or `restart`. A `restart` clears `execution_history`, `execution_memory`, and `context_memory` so unrelated work does not contaminate a new request.

### Tools: `tool_node`

`src/agent/nodes/toolnode.py` invokes the tool named by `next_step.tool_name`.

Before execution, it:

- Rejects a tool disabled for the current session.
- Validates arguments through the tool's Pydantic schema when one is present.
- Blocks duplicate successful calls with identical arguments. `web_search` is stricter: after one success, any second successful web search in the same turn is blocked.
- Requires a LangGraph confirmation interrupt for `execute_bash`, `execute_powershell`, `execute_python_script`, and `edit_file` when `confirm_tools` is enabled.

Every result receives a sequential key such as `tool_1`, is appended to `execution_history`, stored in `execution_memory`, and automatically inserted into `context_memory`. The user-visible message is truncated, while the full result remains retrievable through `context_select`.

The built-in tool catalog is assembled in `src/tools/__init__.py`:

- Time: `get_current_datetime_info`
- Host information: `system_info`
- Files: `read_file`, `edit_file`, `search_file`
- Web: `web_search`
- Query analysis: `decompose_query`
- Execution: `execute_bash`, `execute_powershell`, `execute_python_script`

### Sub-agents: `subagent_node` and gate

`src/agent/nodes/subagentnode.py` delegates a task to a catalog entry. It emits progress callbacks, adds the outcome to the same history/memory mechanism as tools, and returns control through `subagent_gate`.

The registry shape is `SubagentSpec` in `src/subagents/registry.py`: name, display name, description, when-to-use guidance, adapter function, scope, tool metadata, source, and availability metadata. **At present, `BUILTIN_SUBAGENTS` is an empty list.** The graph and API support sub-agents, but no planner-callable built-in sub-agent is currently registered.

The one-call-per-turn guard remains active for future adapters. It prevents repeatedly invoking the same sub-agent within a user turn, including after failures. `subagent_gate_node()` is currently a no-op extension point; it exists so sub-agents that need post-result human confirmation can be added without rewiring the graph.

### Context selection and user questions

`context_selector_node` is deterministic and makes no LLM call. The planner requests a memory key and token window. The node loads that payload from `execution_memory`, slices it, and replaces any earlier window for the same key in the FIFO context buffer.

`human_input_node` always calls LangGraph `interrupt()` with a question and optional choices. On resume, the supplied text is added as a `HumanMessage`, then planning continues.

### Pause, confirmation, stop, and resume

`src/agent/control.py` implements cooperative pause flags per chat/thread. Nodes call `maybe_pause()` before side effects. A pause becomes a durable LangGraph interrupt at the next node boundary. On resume, LangGraph replays the interrupted node with the supplied resume value.

- Pause: requested through the API/WS or terminal UI; it is not an immediate hard kill.
- Tool confirmation: a special interrupt generated by `tool_node` for destructive or code-execution tools.
- Ask user: a planner-directed interrupt from `human_input_node`.
- Stop: `AgentRuntime` sets a cancellation flag checked while consuming graph updates. In-flight tools are cooperative and may finish before the run stops.

## Prompt Architecture and Rendering

### Prompt composition

`src/prompts/prompt_loader.py` is the common loader for main and sub-agent prompts. `load_prompt(name, context)` renders `<name>.txt`, then splits it around `--------------------` into:

- A small system prompt above the separator, intended for role/persona and stable cacheable text.
- A user prompt below the separator, carrying capabilities, task, dynamic context, and output contract.

The main planner calls `agentnode_prompt_loader()`, which composes:

- Reusable `persona` and `constraints` modules.
- Enabled tool and sub-agent descriptions.
- Latest user query and recent conversation.
- Turn-start flag for the `session_intent` instruction.
- Slim execution history without result bodies.
- An index of full execution-memory results.
- Budgeted context-memory entries.
- Learned experience advice.
- Preloaded user context, including preferences in a dedicated section.

### Template language

`src/prompts/prompt_loader.py` implements prompt rendering, module loading, and system/user splitting. It is not Jinja.

| Syntax | Meaning |
|---|---|
| `@block NAME` | Starts a renderable section. |
| `@block NAME if=condition` | Starts a conditional section. |
| `@end` | Closes the nearest block. |
| `@# comment` | Non-rendered comment. |
| `{variable}` | Substitutes a context value. Missing values become empty unless strict mode is enabled. |

Conditions define presence as non-empty/non-whitespace values, non-empty collections, true booleans, or numeric/object values. In `if=`, commas mean AND, pipes mean OR, and `!name` means absence. For example, `if=tools|subagents` renders when either capability list exists; `if=a,b` needs both.

Structured values use TOON serialization via the `toons` library rather than pretty JSON. This keeps prompt context more compact. The renderer removes comments/directives, omits failed blocks entirely, trims whitespace, and collapses residual blank lines.

### Main prompt contract

`src/prompts/agentnode.txt` is the operational policy for the planner. It tells the model:

- How to select one next action or finalize.
- Which tools and sub-agents are currently available.
- How context-memory and execution-memory differ.
- How to retrieve a missing result window.
- When a user question is justified.
- The exact XML-like output shape that `agent_node` parses.

`src/subagents/learner_agent/prompts/extract_memory_chunks.txt` is the learner's separate prompt. It asks for validated JSON memories from bounded conversation, Armory, child-agent, and decision-state evidence.

## Memory Model

The project has three different memory layers:

| Layer | Scope | Store | Purpose |
|---|---|---|---|
| Conversation/checkpoint state | One chat, branch-aware | PostgreSQL LangGraph tables | Resume, rollback, current graph state. |
| Execution memory | Current agent plan | `PlanExecuteState` checkpoint fields | Full results indexed by key. |
| Context memory | Current planner context | `PlanExecuteState` checkpoint fields | FIFO, token-bounded visible windows of results. |
| Learned experiences | Cross-chat, user-filtered retrieval | `data/experience/` JSON/JSONL vectors | Advisory next-action guidance learned from prior trajectories. |

`src/agent/memory.py` manages execution/context memory. `context_memory` defaults to 5,000 estimated tokens. It serializes structured data as TOON, supports approximate token windows using a four-characters-per-token estimate, evicts oldest entries first, and keeps a metadata index so the planner can request unloaded results without receiving every result body on every loop.

## LLM Client, Observability, and Replay

All LLM calls are centralized in `src/models/llm_client.py`.

### Gateway behavior

The client uses the OpenAI SDK against the configured LiteLLM/OpenAI-compatible gateway. It creates one module-level `OpenAI` client and supports:

- `call_llm()` for synchronous text, markup, or JSON results.
- `call_llm_stream()` for streamed text used by the main planner.
- Gateway token usage when available.
- LiteLLM cost information from the `x-litellm-response-cost` response header.
- Estimated usage only when the gateway does not provide usage.

For streams, it requests `stream_options={"include_usage": True}` and retries without that option only when the gateway rejects that field.

### Logging and mock replay

Each call is logged through `src/utils/llm_logger.py` and agent trace helpers. Records include the complete system prompt, prompt, model, temperature, response, usage, cost, latency, and errors. Logs are written to `logs/llm/{chat_id}.jsonl` and, when configured, the `llm_calls` PostgreSQL table.

When `MOCK_LLM_CALL` is enabled, a call with the same model, system prompt, user prompt, output type, and temperature can replay a non-cached historical response. A cache miss still calls the real gateway. Replayed streaming responses are sliced into small chunks so UI behavior remains close to live streaming.

## CLI

The terminal client lives in `src/cli/repl.py` and is rendered with Rich plus `prompt_toolkit`.

### Flow

1. The user signs in with a username/email and password through `UserRepository`.
2. The CLI starts `BackgroundIdleWatcher` for experience learning.
3. It loads stored agent preferences to build runtime capabilities.
4. The first ordinary message creates a chat row and uses its ID as the LangGraph thread ID.
5. `run_turn_interactive()` installs token, usage, and sub-agent callbacks for the renderer.
6. It consumes `run_turn()` graph updates, shows node/tool/sub-agent status, and handles interrupts inline.
7. It updates the chat's last activity after the turn.

### Commands

| Command | Current behavior |
|---|---|
| `/new` | Start a fresh chat on the next message. |
| `/sessions` | Select and display a prior chat. |
| `/model` | Select from the CLI's fixed model list. |
| `/tools` | Enable or disable internal tools for subsequent turns. |
| `/agents` | Enable or disable cataloged sub-agents; currently none are registered. |
| `/mcp` | Manage the MCP registry entries. |
| `/settings` | Toggle verbosity/confirmation and adjust loop/sub-agent limits. |
| `/checkpoints` | Display checkpoint summaries. |
| `/rewind <id>` | Make the next turn run from a checkpoint. |
| `/clear` | Clear terminal output. |
| `/quit` | Exit. |

MCP management is registry management only. The current release stores endpoint metadata and connected flags but does not dynamically execute live MCP tools.

## HTTP API and WebSocket Runtime

`api/app.py` creates the FastAPI application with `/v1` as the default prefix. `api/lifespan.py` configures logging, warms repositories, initializes the agent graph, and starts the asynchronous idle learner watcher. If graph or learner initialization fails, the API logs the exception and starts in a degraded state.

### Authentication

Login returns a JWT plus a server-side auth session. REST endpoints use `Authorization: Bearer <token>`; WebSocket authentication uses a `token` query parameter. `require_user()` and `user_from_token()` both validate:

1. JWT signature and expiry.
2. Required `sub` user ID and `sid` session ID claims.
3. Active non-revoked session in the repository.
4. Existing user record.

Logout revokes the server-side session, invalidating the JWT even before it expires.

### REST resources

The dedicated reference is `documentation/backend-api.md`. The live route groups are:

| Resource | Paths | Behavior |
|---|---|---|
| Auth | `/auth/login`, `/auth/logout`, `/auth/me` | Login, session revocation, current user. |
| Health | `/live`, `/health` | Public liveness and authenticated runtime health. |
| Chats | `/chats` and `/chats/{id}` | Create/list/get/update/soft-delete chats. |
| Checkpoints | `/chats/{id}/checkpoints`, `/rollback` | List checkpoint summaries, schedule one-shot rollback. |
| Memory | `/memory`, `/memory/entries` | Manage explicit per-user durable memory. |
| Preferences | `/preferences` | Read and partially update UI/agent settings. |
| MCP | `/mcp/servers` | Manage MCP registry records, not live execution. |
| Tools/sub-agents | `/tools`, `/subagents` | Return current capability catalogs. |
| Files | `/files/pick` | Opens platform file picker through `FilePickerService`. |
| Analytics | `/analytics/summary` | Summarizes recorded events, admin-aware. |
| Experiences | `/experience`, `/experience/{chunk_id}` | List or fetch learned chunks and a visualization projection. |

When a chat is created, `PreloadService` snapshots public user data, preferences, explicit memory, and MCP registry into `preloaded_context`. This snapshot is passed into a new graph thread and becomes planner prompt context.

### WebSocket protocol

The live chat endpoint is:

```text
ws://<host>:5000/v1/ws/chats/{chat_id}?token=<jwt>&after_seq=<optional>
```

`api/ws/endpoint.py` authenticates the token, confirms chat ownership, attaches the socket to the per-chat runtime, and handles JSON messages. A `ChatPacketQueue` buffers every agent event before delivery.

The packet envelope is:

```json
{
  "v": 1,
  "type": "llm.token",
  "id": "event-id",
  "chat_id": "chat-id",
  "seq": 12,
  "ts": "ISO-8601 timestamp",
  "payload": {},
  "epoch": 0
}
```

Client messages include `run.start`, `run.stop`, `run.pause`, `run.resume`, `run.rollback`, `ack`, and `ping`. Server messages include lifecycle events such as `session.ready`, `run.started`, `node.started`, `llm.token`, `tool.started`, `run.interrupted`, `checkpoint.created`, `run.completed`, and `run.error`.

`ChatRuntimeManager` has one `ChatRuntime` per active chat in the API process. A turn runs in a daemon thread through `AgentRuntime`; it enqueues updates rather than writing directly to the socket. The socket flusher sends backlog first and then live packets. If the client disconnects, the turn continues and packets remain buffered until reconnect. `ack` trims delivered packets. A rollback fences the queue: it clears buffered packets, increments `epoch`, and resets sequence numbers so stale branch output cannot be replayed into the new branch.

Only one ordinary run is allowed per chat. Starting from a checkpoint while a run is active requests cooperative stop of the old run, waits for it, then starts the fork. A manual stop remains cooperative because a currently executing tool cannot be forcibly cancelled safely by this layer.

## Persistence and Checkpoints

The current application uses PostgreSQL for transactional data and LangGraph state. Some older prose in `documentation/backend-api.md` still describes file-backed collections; that is historical documentation, not the implementation used by the current repositories.

### PostgreSQL responsibilities

- Users, password hashes, auth sessions, preferences, memory, MCP registry, chats, analytics, and messages are accessed through `api/db/repositories/`.
- LangGraph owns `checkpoints`, `checkpoint_blobs`, and `checkpoint_writes` through `langgraph-checkpoint-postgres`.
- `PostgresSaver` in `src/utils/postgres_checkpointer.py` extends LangGraph's saver. Each checkpoint write mirrors newly appended LangChain messages into the relational `messages` table for efficient transcript reads.
- `chat_branch_learn_state` records whether an individual leaf checkpoint has already been processed by the learner.

The chat ID is the LangGraph `thread_id`. `build_config()` adds the user ID, session ID, optional checkpoint ID, runtime settings, and recursion limit. `initial_state_for_thread()` creates full initial state only for a new thread; existing threads receive only the new `HumanMessage` delta.

Rollback stores a one-shot checkpoint pointer on the chat. The next turn uses it and clears the pointer after completion. A fork is also possible by starting a run with a checkpoint ID. Chat-history readers use `active_checkpoint_path()` to filter the flat `messages` table down to the current branch, excluding messages from abandoned sibling branches.

## Learning Agent and Experience System

The learner is not a planner-callable sub-agent. It is an independent background LangGraph workflow that turns bounded conversation and execution evidence into governed advisory memory.

### Learner graph

`src/subagents/learner_agent/graph.py` defines:

```text
START -> load_session -> extract_chunks -> persist -> END
```

`learn_session(chat_id, uid, checkpoint_id)` invokes this graph and soft-fails into a status dictionary rather than raising into the watcher.

### Step 1: load trajectory

`load_session_node()` loads a checkpoint branch tip from `agent_app.get_state()`. It extracts:

- The latest user query.
- A compact recent message summary.
- Structured recent conversation messages.
- A slimmed Armory/child execution history with result previews and preserved child spawn parameters.
- Entry, transition, and recovery decision snapshots.
- Effective per-type write and confirmation state.

Chats with no checkpoint state or no conversation/execution evidence are skipped. Conversation-only sessions can produce durable preferences or professional context when evidence is explicit and reusable.

### Step 2: extract reusable advice

`extract_chunks_node()` renders `extract_memory_chunks.txt` and calls the shared `src/models/llm_client.py` once at low temperature. It can produce resource, user preference, user details, tenant details, workflow, troubleshooting, and anti-pattern chunks.

A normalized experience chunk includes:

- A deterministic evidence ID and stable semantic key.
- Bounded search text and reusable content.
- Sensitivity and memory weight.
- Validated type metadata, retrieval cues, preconditions, and decision stage.

Deterministic validation rejects secrets, protected-trait profiling, unknown metadata values, unsupported resource names, and invalid candidates. The learner can produce no chunks when evidence has no durable lesson.

### Step 3: persist and index

`persist_node()` revalidates USER/type write policy and uses the shared governed KB. PostgreSQL stores append-only versions and is authoritative; Chroma indexes active versions. Replayed evidence is skipped, equivalent content reinforces weight, changed content appends a version, and direct unresolved contradictions are kept separate.

Broader publication is a separate admin-reviewed lifecycle. Request and review revalidate target scope, chunk type, publish permission, and `allow_admin_promotion`; AGENT publication rejects deterministic private identifiers and configurations. Validation failures become terminal `PROMOTION_FAILED` records while the source remains active. Published targets support revocation/demotion, timezone-aware expiry, and validated retention classes.

### Idle scheduling and branch handling

`IdleWatcher` polls eligible non-deleted chats. A chat is eligible after `EXPERIENCE_IDLE_SECONDS` and only when it is not currently active in the CLI or API runtime. It enumerates every leaf checkpoint, skips leaves already marked `learned` or `skipped`, and invokes the learner per unprocessed branch.

This is branch-aware: a rollback/fork can leave a non-active branch that still represents a useful completed trajectory. The watcher learns from each leaf rather than only the active chat head. It runs as an asyncio task in API lifespan and as `BackgroundIdleWatcher` in the synchronous CLI.

### Retrieval in the main agent

Before each fast-classifier or planner LLM call, `agent_node` retrieves up to `EXPERIENCE_TOP_K` memories using entry, transition, or recovery query lanes. Results are deduplicated, authorized by scope and type, revalidated against PostgreSQL, stage-adjusted, and filtered against currently available resources. `format_experiences_for_prompt()` groups them by governed type.

Retrieval has a hard four-second wait bound in a small thread pool. A disabled system, empty store, embedding failure, timeout, or any exception simply produces no advice. Learned memory is explicitly framed as untrusted advisory context that cannot grant resources or policy and is overridden by current instructions.

### Experience API view

`GET /v1/experience` returns the current user's chunks by default, or all chunks when `scope=all` is requested. It also constructs a visualization-friendly graph:

- Tool nodes count observed tool usage.
- Experience nodes represent advice chunks.
- Transition links connect `prior_tool -> observed_tool`.
- Membership links connect each experience to its observed tool.

`GET /v1/experience/{chunk_id}` enforces owner access for user-owned chunks.

## Current Extension Points and Limits

- The agent graph already has tool, sub-agent, context selection, user-question, pause, and confirmation routes.
- The sub-agent registry is currently empty, so sub-agent delegation is not active until `BUILTIN_SUBAGENTS` receives adapter specifications.
- `subagent_gate_node` is intentionally a no-op placeholder for future sub-agent-specific confirmation.
- MCP server records can be created and preloaded, but no live MCP tool execution is implemented.
- Packet queues and active chat runtime state are in-memory and require a single API worker.
- Experience vectors/chunks are file-backed JSON/JSONL, not stored in PostgreSQL or a vector database.
- Token accounting for context slicing and any gateway response without usage is approximate at roughly four characters per token.
- API startup can continue when graph/learner initialization fails, but `/health` should be used to identify degraded graph readiness.

## Testing and Operational Checks

The repository keeps focused tests in `tests/`. Relevant areas include:

| Test area | Examples |
|---|---|
| Prompt syntax and planner contract | `tests/test_prompt_render.py`, `tests/test_prompt_templates.py` |
| Context/execution memory and routing | `tests/test_context_memory.py` |
| CLI commands, interrupts, rendering | `tests/test_cli_repl.py`, `tests/test_cli_renderer.py`, `tests/test_cli_runtime_controls.py` |
| API, WebSocket, auth, checkpoints | `backend/tests/` + root `tests/` |
| Learner extraction, retrieval, idle scheduling | `tests/test_experience_system.py` |
| Sub-agent integration infrastructure | `tests/test_subagents_integration.py` |
| LLM logs/replay behavior | `tests/test_llm_logger.py`, `tests/test_llm_mock_mode.py` |

For setup and schema creation, see `scripts/db_setup.py`. Operationally, verify PostgreSQL availability, `.env` LLM credentials, and a single API worker before testing real turns.

## Detailed Subsystem Reference

This section is an implementation-level companion to the architecture sections above. It describes where a request enters, the functions that handle it, the state it changes, and where to look when the behavior is unexpected.

### 1. End-to-End Turn Execution

There are two ways to initiate a turn, but both arrive at the same LangGraph entrypoint:

```text
CLI input
  -> src.cli.repl.run_turn_interactive()
  -> src.utils.postgres_checkpointer.run_turn()
  -> agent_app.stream(...)

WebSocket run.start
  -> api.ws.endpoint._handle_client_message()
  -> ChatRuntimeManager.start_run()
  -> AgentRuntime.run_turn() in a worker thread
  -> src.utils.postgres_checkpointer.run_turn()
  -> agent_app.stream(...)
```

#### New API chat and first turn

The REST chat-create route and the WebSocket turn are intentionally separate. Creating a chat does not call the LLM.

1. `POST /v1/chats` reaches `api/api_routes/chats.py:create_chat()`.
2. FastAPI resolves `require_user()` from `api/core/deps.py`.
3. `require_user()` decodes the bearer JWT, verifies its `sub` and `sid` claims, checks that `AuthSessionRepository.is_active()` accepts the server-side session, and loads the user.
4. `ChatService.create()` calls `PreloadService.build(uid)`.
5. `PreloadService.build()` reads the public user profile, preferences, durable user-memory entries, and MCP registry records.
6. `SessionRepository.create()` inserts a row in `chats`, storing this initial `preloaded_context` JSONB snapshot.
7. The client opens `/v1/ws/chats/{chat_id}` and sends `run.start` with the user query.
8. `ChatRuntimeManager._begin_run()` reads the stored snapshot and saved agent preferences, updates chat activity/title, and starts an `AgentRuntime` thread.
9. `AgentRuntime.run_turn()` calls `src.utils.postgres_checkpointer.run_turn()` with the chat ID as the LangGraph thread ID.
10. Since this is a new thread, `initial_state_for_thread()` creates all durable agent fields. On later turns it adds only a new `HumanMessage`; prior state is restored by the checkpointer.

The preload snapshot is not dynamically refreshed during a chat. The explicit `user_memory_fetch` tool exists for cases where the planner needs the current durable-memory source of truth after the chat begins.

#### Main agent loop

For one user question, the agent may loop through graph nodes until the planner returns a final answer or raises an interrupt.

```text
HumanMessage added to checkpoint state
  -> agent_node calls LLM
  -> parsed next_step
  -> selected executor node updates state
  -> agent_node sees the updated state and calls LLM again
  -> finish or interrupt
```

`agent_node()` is the only node that makes the main planner LLM call. Executor nodes do not decide the next action themselves; they update state and return to `agent_node()`.

The `max_loops` runtime value becomes LangGraph's `recursion_limit`. If an agent appears to keep planning without ending, inspect the `next_step` sequence in logs and compare it with this limit. A low limit causes LangGraph to stop before the task completes; a high limit does not solve a planner repeatedly choosing a non-progressing action.

#### Functions to start with when tracing a turn

| Function | File | Why it matters |
|---|---|---|
| `run_turn()` | `src/utils/postgres_checkpointer.py` | Common wrapper that binds logs, chooses new-state vs resume input, builds config, and yields graph updates. |
| `initial_state_for_thread()` | `src/utils/postgres_checkpointer.py` | Defines what exists on a brand-new chat. |
| `build_config()` | `src/utils/postgres_checkpointer.py` | Merges user/thread/checkpoint/runtime settings into LangGraph configuration. |
| `agent_node()` | `src/agent/nodes/agentnode.py` | Builds the prompt, calls the LLM, and creates `next_step`. |
| `_parse_response()` | `src/agent/nodes/agentnode.py` | Converts planner XML-like output into graph state. |
| `route_from_agent()` | `src/agent/edges/routing.py` | Maps `next_step.action` to the next graph node. |
| `tool_node()` | `src/agent/nodes/toolnode.py` | Validates, confirms, invokes, and records a tool. |
| `context_selector_node()` | `src/agent/nodes/context_selector.py` | Loads an execution-memory window for the next planner call. |
| `human_input_node()` | `src/agent/nodes/human_input.py` | Creates a durable LangGraph interrupt for a user answer. |

### 2. Agent State, Memory, and Planner Decisions

The planner receives a deliberately incomplete view of previous results. This is a key design constraint, not an accidental omission.

#### Why execution memory is split

Tool output can be large. Supplying every historical result in every planner prompt would grow cost and degrade tool selection. Instead, the system has three representations:

| Representation | Full result bodies? | Planner sees it every loop? | Main producer |
|---|---:|---:|---|
| `execution_history` | No, only slim metadata in prompt | Yes | Tool and sub-agent nodes |
| `execution_memory` | Yes | No, index only | Tool and sub-agent nodes |
| `context_memory` | Selected complete/sliced result windows | Yes, under budget | Auto-ingest plus context selector |

`build_execution_memory_index()` supplies every stored key with type, name, task, size, and `in_context` status. The planner can then choose `context_select` for a key without guessing whether data still exists.

`update_context_memory()` enforces the context budget. It removes an existing window for the same key, evicts oldest different entries until the new slice fits, then appends the new entry. This makes it a FIFO cache with replacement semantics per key.

`slice_by_tokens()` uses approximate offsets based on four characters per token. It preserves the original structured object when the full value fits, retaining compact TOON serialization. Partial slices become TOON text, so an exact token boundary should not be assumed.

#### Planner response parsing details

The planner template requests XML-like tags, but this is parsed with regular expressions rather than XML parsing. The important helpers are:

| Function | Role |
|---|---|
| `_extract_tag(text, tag)` | Finds the first `<tag>...</tag>` body. |
| `_parse_parameters(params_xml)` | Converts immediate nested parameter tags into a dictionary. |
| `_coerce_int(value, default)` | Safely converts context-window offsets. |
| `_run_stream(stream, on_token)` | Buffers full output while exposing only visible reasoning/output text. |
| `_parse_response(buffer, turn_start)` | Creates `messages`, `current_task`, `next_step`, and restart reset updates. |

The parser treats any non-final action other than `agent_call`, `context_select`, or `ask_user` as a tool action. This means a malformed or unexpected action name can cause the `name` field to be looked up as a tool. The resulting `Unknown tool` result is returned to the planner so it can recover on the next loop.

#### Debugging planner problems

| Symptom | Inspect first | Likely cause or next check |
|---|---|---|
| Agent ends immediately | `agent.decision` event and raw planner buffer | Planner emitted `<planner_exit>True</planner_exit>` or parsing missed required tags. |
| Agent calls an unknown tool | `agent.decision` and `tool.end` events | Prompt/tool catalog mismatch, malformed `<name>`, or a tool disabled at runtime. |
| Agent repeats work | `execution_history`, duplicate guard result, prompt context | The planner did not use a prior result; inspect whether it was in `context_memory`. |
| Agent says it lacks a prior result | `execution_memory_index` and `context_memory` prompt sections | It may need `context_select`, or the user turn was classified as `restart`. |
| Agent stops at a recursion error | Runtime preferences and `build_config()` | Increase `max_loops` only after checking repeated routing. |
| No streamed tokens but final answer appears | `_run_stream()` tags and raw LLM response | The response may omit/delay `<planner_exit>` or visible `<output>`/`<reasoning>` tags. |

### 3. Prompt Rendering Deep Dive

Prompt behavior is controlled by template data and `@block` conditions, not by conditional Python string concatenation. The main entrypoints are:

```text
agent_node()
  -> agentnode_prompt_loader(...)
  -> load_prompt("agentnode", context)
  -> render_file(agentnode.txt, context)
  -> render(template, context)
  -> system prompt + user prompt
```

#### Major prompt functions

| Function | What it does | Debugging value |
|---|---|---|
| `agentnode_prompt_loader()` | Builds all main planner context fields and loads reusable modules. | Start here if a prompt section is missing or a tool is absent. |
| `_load_module()` | Reads reusable persona/constraint text. | Check when stable policy is unexpectedly different. |
| `_has_tool()` | Gates user-memory policy text on actual capability availability. | Confirms why a capability rule does or does not render. |
| `load_prompt()` | Renders a template and partitions it into system/user prompts. | Ensures the separator is present and correctly placed. |
| `_parse()` | Converts directive text into an internal tree. | Useful only when renderer syntax itself is suspect. |
| `_eval_cond()` / `_present()` | Evaluates `if=` rules. | Diagnose a conditional section being dropped. |
| `_subst()` | Replaces `{variables}` and optionally raises in strict mode. | Diagnose typoed or missing variables. |
| `to_toon()` / `_fmt()` | Serializes structured values compactly. | Explain why context does not look like JSON. |
| `_tidy()` | Removes blank lines after omitted blocks. | Explains final prompt whitespace. |

#### System versus user prompt

Everything above the separator in `agentnode.txt` is static system content: the base autonomous-agent instruction and persona. Most changing data is below the separator to avoid mixing volatile task data with persona policy. The tests verify this separation because it improves prompt-cache behavior and makes prompt changes easier to reason about.

The system prompt is expected to remain identical across ordinary planner iterations. If it changes from turn to turn, look for dynamic variables accidentally placed above `--------------------`.

#### Practical prompt-debug method

1. Start with `tests/test_prompt_templates.py` and `tests/test_prompt_render.py`; they encode intended rendering contracts.
2. Call `agentnode_prompt_loader()` in a focused test or REPL with a controlled context.
3. Print system and user halves separately, not the original template source.
4. Check each missing block's `if=` condition using `_present()` rules. `False`, `None`, empty text, and empty collections all suppress a block.
5. For state-related issues, inspect `execution_memory_index` and `context_memory`, not only `execution_history`.
6. Use strict mode through `load_prompt(..., strict=True)` when developing a template to surface unknown placeholder names rather than silently rendering them empty.

### 4. Internal Tool Subsystem

The tool registry is a fixed list in `src/tools/__init__.py`. Each tool is a LangChain `@tool` with a Pydantic argument schema. The execution path is:

```text
planner <name> and <parameters>
  -> tool_node validates selected tool and arguments
  -> StructuredTool.invoke() or direct user-memory function call
  -> normalized result dict
  -> execution_history + execution_memory + context_memory
```

The direct call for user-memory tools is intentional: `tool_node()` injects a server-derived `uid` after validation and bypasses StructuredTool filtering so this trusted field reaches the implementation. The planner cannot choose another user's ID.

#### File tools

`src/tools/file_io.py` restricts operations to known text extensions and enforces size limits.

| Function | Main behavior | Guardrails |
|---|---|---|
| `read_file()` | Reads a whole text file or selected 1-based line range. | 50 MB cap, allowed encodings/extensions, replacement decoding on bad bytes. |
| `edit_file()` | Replaces one exact old string, or all occurrences when opted in. | 50 MB cap, ambiguity failure for repeated matches, temporary-file replacement for atomic write. |
| `search_file()` | Searches regex or literal text with nearby lines. | 100 MB cap, regex validation, max 500 results, maximum line length clipping. |

There is no project-root sandbox in `_resolve_text_file()`: any readable allowed-extension path can be targeted. Confirmation at the agent graph level protects `edit_file`, but direct use of these Python functions bypasses that graph-level confirmation.

Tips:

- Use `search_file` before `read_file` for large source files.
- When `edit_file` reports multiple occurrences, include more surrounding lines in `old_string`; this is safer than setting `replace_all`.
- `read_file` line windows are inclusive at `end_line`, while Python slicing is internally end-exclusive.

#### Command execution tools

`src/tools/executor.py` runs commands in child processes. They are destructive-capability tools, so `tool_node()` normally interrupts for approval before invoking them.

| Function | Execution model | Important limits |
|---|---|---|
| `execute_bash()` | `bash -c <command>` | 1-300 second timeout, 10 MB stdout/stderr cap, small blacklist. |
| `execute_powershell()` | Prefers `pwsh`, falls back to `powershell`. | Same timeout/output cap and PowerShell blacklist. |
| `execute_python_script()` | Writes script to temp file and uses project Python when available. | Optional dependencies install into a temporary target directory, not the project environment. |

`_run()` centralizes subprocess output, timeout, missing executable, and return-code normalization. A successful process means only `return_code == 0`; callers should inspect stderr when `success` is false.

The blacklist is a narrow safety net, not a general sandbox. Confirmation, least-privilege runtime settings, and controlled deployment permissions remain necessary.

#### Information and planning tools

| Function | Purpose | Notes |
|---|---|---|
| `get_current_datetime_info()` | Supplies local/current date-time information. | Useful when an answer depends on time. |
| `system_info()` | Reports host/system details. | Diagnose environment assumptions before shell commands. |
| `web_search()` | Uses Brave when configured, otherwise `ddgs` DuckDuckGo. | Tool node allows one successful web search per user turn. |
| `decompose_query()` | Calls the shared LLM client for structured task analysis. | It is an LLM-backed tool, so its request is logged/replayable independently. |

`web_search()` returns normalized title/URL/description rows. `provider="auto"` selects Brave only when `BRAVE_SEARCH_API_KEY` is set; otherwise it uses DuckDuckGo. A forced Brave request fails rather than silently changing provider when the key is missing.

`decompose_query()` asks the LLM for intent, subtasks, assumptions, ambiguity, constraints, needed context, complexity, and an approach. It catches LLM failures and returns `{success: false}` rather than raising into `tool_node()`.

#### Durable user-memory tools

`user_memory_update()` upserts an entry by `(user_id, key)`. `user_memory_fetch()` returns all entries or filters by key/category. The planner template advises use only for durable facts and preferences, not temporary task details.

The corresponding REST memory API has a separate bulk-replace operation. `MemoryRepository.put()` deletes all current entries then inserts the supplied set in one connection context; `add_entry()` is the safer single-entry upsert path.

### 5. API Layer and Service Boundaries

The API follows a thin route -> service -> repository pattern:

```text
FastAPI route
  -> dependency authentication and request schema validation
  -> service for ownership/business behavior
  -> repository or runtime manager
  -> PostgreSQL, file analytics, or agent graph
```

Routes should not directly make planner decisions. The notable exception is the WebSocket endpoint, which validates protocol messages and delegates long-running work to the runtime manager.

#### Service function map

| Service | Important methods | Responsibility |
|---|---|---|
| `AuthService` | `login()`, `logout()`, `me()` | Authenticates, creates/revokes server sessions, creates JWT response. |
| `ChatService` | `create()`, `list()`, `get()`, `update()`, `delete()` | Ownership checks, preloading, transcript/history projection, soft deletion. |
| `CheckpointService` | `list()`, `tree()`, `rollback()` | Ownership checks around checkpoint helpers and queue fencing. |
| `MemoryService` | `get()`, `put()`, `add()`, `clear()` | Per-user durable memory operations. |
| `PreferencesService` | `get()`, `put()` | UI and agent runtime preferences. |
| `McpService` | `list()`, `create()`, `update()`, `delete()` | Registry CRUD only. |
| `ToolsService` | `list_catalog()` | Converts internal tool schemas and MCP metadata into client catalog data. |
| `AnalyticsService` | `summary()` | Applies admin/user visibility when reading analytics. |
| `PreloadService` | `build()` | Creates the initial prompt context snapshot for a chat. |

`ChatService._owned()` is the common ownership guard for chat management. It returns `404` for missing/deleted chats and `403` for another user's chat. Any new chat-specific REST operation should use this or an equivalent ownership check before accessing checkpoint data.

#### Authentication implementation detail

`UserRepository.authenticate()` joins `users` and `user_credentials`, verifies the password hash, and opportunistically rehashes when `needs_rehash()` says the stored hash should be upgraded. `AuthSessionRepository.create()` stores a server-side session expiration. JWT validation alone is insufficient: both REST and WebSocket paths check that this record remains active.

This server-side check is why logout can revoke an otherwise unexpired JWT.

### 6. WebSocket Runtime, Queues, and Recovery

The WebSocket protocol is defined as string constants in `api/ws/protocol.py`. The protocol separates control commands from durable event delivery.

#### Connection lifecycle

1. `chat_ws()` reads `token` and optional `after_seq`.
2. `user_from_token()` validates the JWT and server session.
3. The chat is loaded and checked for ownership/deletion.
4. `ChatRuntimeManager.attach()` obtains the process-local runtime for the chat.
5. A previously attached socket for that chat is detached; the newest connection wins.
6. The server sends `session.ready` directly.
7. It sends all queued events with sequence greater than `max(after_seq, ack_seq)`.
8. A flusher task waits for new queue events and sends them until disconnected.

#### `ChatPacketQueue` behavior

`ChatPacketQueue` is the in-memory delivery buffer, not the source of truth for chat state.

| Method | Effect |
|---|---|
| `enqueue(type, payload)` | Adds a versioned envelope, assigns monotonic sequence number, bounds packet count. |
| `snapshot_undelivered(after_seq)` | Returns retained packets after client cursor/acknowledgement. |
| `wait_new(after_seq, timeout)` | Blocks the flusher thread briefly until new packets are available. |
| `ack(seq)` | Advances acknowledged cursor and removes packets at or before it. |
| `fence()` | Clears backlog, increments epoch, resets sequence/ack counters after rollback. |
| `stats()` | Reports last sequence, acknowledged sequence, backlog count, and epoch. |

The queue retains at most `packet_queue_max_packets` events. If a disconnected client misses more data than this cap retains, oldest undelivered packets are dropped. The client should acknowledge frequently and use REST chat/checkpoint data for durable recovery rather than treating packet backlog as permanent history.

#### Agent runtime event conversion

`AgentRuntime.run_turn()` bridges graph updates to queue packets. It installs ContextVar callbacks for token and sub-agent events, then examines LangGraph update events for node lifecycle, planner decisions, tool/sub-agent completion, interrupts, and final answers.

Important behavior:

- It immediately emits `node.started` for `agent_node` before the graph produces an update, so the UI is not blank during initial prompt preparation.
- `llm.token` events are emitted from `agent_node` streaming callbacks, not duplicated from LangGraph custom events.
- When `human_input_node` or a confirmation gate interrupts, it emits `run.interrupted` with the interrupt payload and best-effort checkpoint tip.
- A final planner action emits `llm.done`, then `checkpoint.created`, then `run.completed`.
- A stopped run may contain a partial answer reconstructed from already streamed output text.
- A fork can mark an interrupted prior run as `superseded`; clients should not treat that run as the current answer.

#### WebSocket debugging checklist

| Symptom | What to inspect |
|---|---|
| Connection closes with 4401 | Token missing, expired, malformed, revoked, or user deleted. Inspect `user_from_token()`. |
| Connection closes with 4403 | Chat is owned by another user. |
| Connection closes with 4404 | Chat missing or soft-deleted. |
| No events after `session.ready` | Check `run.start` payload has non-empty `query`, then `active_runs` in `/health`. |
| Duplicate UI stream | Client may be rendering both callback events and its own persisted data; server already suppresses custom-event duplicates. |
| Reconnect repeats old packets | Send `ack` and/or correct `after_seq`; compare event `epoch`. |
| Events disappear after rollback | Expected: rollback fences the queue and starts a new epoch. |
| Run never stops immediately | Stop is cooperative. Check an active tool or LLM call before the next update boundary. |

### 7. PostgreSQL, Repositories, and Checkpoints

There are two pools in the codebase:

- `api/db/postgres.py:get_pool()` is the repository pool used for application tables.
- `src/utils/postgres_checkpointer.py:_get_pool()` is the LangGraph checkpointer pool.

Both use psycopg connection pools with `dict_row`, autocommit, and an Asia/Kolkata timezone option. They are separate module-level singletons, so pool diagnostics should distinguish normal API repository traffic from checkpoint traffic.

#### Repository map

| Repository | Key methods | Storage role |
|---|---|---|
| `UserRepository` | `authenticate`, `get_by_uid`, `find_login`, `touch_last_login` | Users, credentials, cached public profile. |
| `AuthSessionRepository` | `create`, `is_active`, `invalidate` | Server-side JWT revocation/expiry control. |
| `SessionRepository` | `create`, `get`, `list_for_user`, `update`, `soft_delete`, `set_rollback` | Chat rows and preloaded context. |
| `MemoryRepository` | `get`, `put`, `add_entry`, `clear` | Durable per-user facts/preferences. |
| `PreferencesRepository` | `get`, `put` | UI preferences and agent runtime settings. |
| `McpRepository` | `list`, `create`, `update`, `delete` | MCP registry metadata. |
| `AnalyticsRepository` | `append`, `summary` | JSONL analytics event log. |

Despite most transactional state being in PostgreSQL, `AnalyticsRepository` writes `data/analytics/events.jsonl`; learned experiences also remain file-backed. Do not assume every repository is a SQL-backed repository solely from its package location.

#### Checkpointer function map

| Function/class | Purpose |
|---|---|
| `PostgresSaver.put()` | Delegates checkpoint write then mirrors newly appended messages to SQL `messages`. |
| `get_checkpointer()` | Creates/configures the process-wide LangGraph Postgres saver and branch-learning table. |
| `build_config()` | Supplies `thread_id`, user, checkpoint ID, run ID, runtime settings, recursion limit. |
| `list_checkpoints()` | Produces readable newest-first checkpoint summaries. |
| `list_checkpoint_tree()` | Adds node inference, parent relationships, leaf status, active tip, interrupt status. |
| `active_checkpoint_path()` | Computes the active tip-to-root set for filtering transcript rows after branches. |
| `list_leaf_checkpoints()` | Returns every branch tip for idle learning. |
| `get_thread_state()` | Reads current checkpoint channel values. |
| `run_turn()` | Binds trace logging and streams new/resumed graph execution. |

The message-table mirror is append-oriented. `PostgresSaver._sync_messages()` counts existing SQL message rows and inserts messages beyond that count. Branch-aware readers subsequently use checkpoint ancestry to hide sibling-branch rows; the raw table itself can contain messages from abandoned branches.

#### Database troubleshooting

1. Run `scripts/db_setup.py` to create application/checkpointer-related schema before real use.
2. Confirm the connection parameters in `.env` are shared by `src/config.py` and `api/core/config.py`.
3. If REST works but graph initialization fails, test the checkpointer tables/pool separately; agent graph compilation calls `get_checkpointer()`.
4. If chat detail has no transcript but checkpoints exist, inspect message mirroring and `active_checkpoint_path()` filtering.
5. If rollback appears ineffective, confirm the selected checkpoint ID belongs to the chat and observe the next run. Rollback is a one-shot pointer, not an immediate mutation of the current checkpoint tip.
6. If an idle branch is repeatedly relearned, inspect `chat_branch_learn_state` status for that leaf. Only `learned` and `skipped` suppress future attempts; `error` remains eligible.

### 8. Observability, Logs, and LLM Replay

The system has three observability streams with different purposes:

| Stream | Location | Best for |
|---|---|---|
| Agent trace | `logs/{chat_id}.jsonl` | Node decisions, tools, routing, learner events, high-level run trace. |
| Full LLM log | `logs/llm/{chat_id}.jsonl` and `llm_calls` | Exact prompts, responses, cost, provider usage, replay debugging. |
| Analytics | `data/analytics/events.jsonl` | Product-level counts such as login/run/chat creation. |

#### Agent trace logger

`src/utils/agent_logger.py` binds a `SessionLogger` through a `ContextVar`. `run_turn()` binds it before graph iteration and resets it afterward; `learn_session()` binds the same logger around learner execution.

`log_event()` is intentionally a no-op without a bound session. Logging calls should therefore be safe in helpers that can run from a test, background worker, or API code path.

Writes are queued to one daemon thread. This prevents slow OneDrive/network filesystem writes from blocking the agent. It also means log lines may not be immediately visible on disk. `flush_pending_logs()` is the deliberate synchronization point for tests or graceful shutdown.

Useful event names include:

- `run.start`, `run.end`, `run.error`
- `llm.request`, `llm.response`, `llm.error`, `llm.cache_hit`
- `agent.decision`, `route`
- `tool.start`, `tool.end`
- `subagent.start`, `subagent.end`, `subagent.call_blocked`
- `context_select`
- `learner.start`, `learner.load`, `learner.extract`, `learner.persist`, `learner.end`

Large payload strings are truncated recursively before trace logging. If the full tool result or complete prompt is required, use the execution memory/checkpoint or LLM log rather than assuming the agent trace contains the full value.

#### LLM call logger and replay cache

`src/utils/llm_logger.py` records each success, error, and replay. `build_cache_key()` hashes all answer-affecting fields: model, system prompt, user prompt, output type, and temperature. It length-prefixes fields before hashing so different field boundaries cannot collide through embedded newlines.

`lookup_cached_response()` deliberately finds the most recent successful non-replayed result across sessions/users. This is appropriate only as a development replay feature. Do not enable `MOCK_LLM_CALL` in production where cross-session replay semantics would be inappropriate.

Both file and database LLM logging are asynchronous and soft-failing. A database outage should produce logger warnings but should not cause `call_llm()` or `call_llm_stream()` to fail.

#### Recommended debugging workflow

1. Obtain the chat ID and approximate turn time.
2. Inspect `logs/{chat_id}.jsonl` in chronological order for `run.start`, `agent.decision`, routing, and tool events.
3. Inspect `logs/llm/{chat_id}.jsonl` for the exact rendered system prompt, user prompt, raw output, model, latency, usage, and gateway cost.
4. Compare the raw planner output with `_parse_response()` expectations when routing looks wrong.
5. Inspect checkpoint state with `get_thread_state(chat_id)` or checkpoint-list APIs when state/memory differs from the trace.
6. Inspect WebSocket envelope sequence and epoch when the backend behavior is correct but the UI rendering is stale or duplicated.
7. Use `GET /v1/health` to distinguish an unavailable agent graph from an ordinary failed turn.

### 9. Learning Agent Detailed Flow and Diagnostics

The learner runs after inactivity, not in the user-facing turn critical path. It avoids adding LLM extraction latency to the live answer.

#### Full learner sequence

```text
IdleWatcher tick
  -> SessionRepository.list_all()
  -> sessions_ready_to_learn()
  -> skip active chats
  -> list_leaf_checkpoints(chat_id)
  -> skip leaves recorded as learned/skipped
  -> learn_session(chat_id, leaf)
       -> load_session_node()
       -> extract_chunks_node()
       -> persist_node()
  -> mark_leaf_learned(chat_id, leaf, status)
```

`load_session_node()` accepts conversation-only evidence as well as Armory and child-agent trajectories, while requiring explicit durable evidence for preferences and user details.

`extract_chunks_node()` asks for high-signal memories across the seven governed types. `_normalize_chunk()` validates metadata, sensitivity, weight, semantic/evidence identity, profiling boundaries, secrets, and observed resources.

`persist_node()` writes through `src/agent/kb.py`. PostgreSQL and an outbox provide the durable boundary; Chroma can be rebuilt from active PostgreSQL versions.

`retrieve_experiences()` derives current decision state, searches stage-specific type lanes, deduplicates candidates, and filters unavailable resources. `agent_node()` wraps this in `_safe_learned_experiences()` so retrieval cannot stall either fast or planner decisions longer than four seconds.

#### Learning-agent diagnostic table

| Symptom | Where to look | Explanation |
|---|---|---|
| No experiences ever appear | `EXPERIENCE_ENABLED`, idle duration, `sessions_ready_to_learn()` | The chat must be idle and contain durable conversation or execution evidence. |
| A chat never becomes eligible | `last_activity_at`, active runtime/CLI markers | Active chats are intentionally skipped. |
| Learner runs but stores zero chunks | `learner.extract` event and extraction prompt/output | The LLM may have found no high-signal tool lesson. |
| `stored_count=0` after chunks extracted | KB traces/outbox and embedding logs | Evidence may already be processed, or KB/indexing may have soft-failed. |
| Experiences retrieved for wrong user | chunk metadata and retrieval `uid` | User filtering happens only when the caller supplies a UID. Main agent does. |
| Same branch keeps processing | `chat_branch_learn_state` | Error status intentionally retries; learned/skipped do not. |
| Planner is slow before LLM call | learner retrieval timeout logs | Retrieval uses a four-second cap; inspect embedding startup/availability. |

### 10. Safe Extension Guide

#### Add an internal tool

1. Create a Pydantic argument schema and `@tool` function under `src/tools/`.
2. Return a consistent result dictionary with `success` and a useful `error` on ordinary failures.
3. Add it to `INTERNAL_TOOLS` in `src/tools/__init__.py`.
4. Decide whether it is destructive or arbitrary execution. If so, add its name to `CONFIRM_REQUIRED_TOOLS` in `toolnode.py`.
5. Add focused tests for schema validation, ordinary errors, and state ingestion if behavior is non-trivial.
6. The planner receives the tool name and description automatically through `agentnode_prompt_loader()`.

#### Add a planner-callable sub-agent

1. Implement an adapter matching `Callable[[str, dict[str, Any]], str]`.
2. Add a `SubagentSpec` to `BUILTIN_SUBAGENTS` in `src/subagents/registry.py`.
3. Provide concise `description` and `when_to_use`; these are what the planner sees.
4. Ensure one adapter invocation is self-contained, because the graph enforces one call per named agent per user turn by default.
5. Put structured escalation data in `_subagent_structured_result` within the supplied context only if a future `subagent_gate_node` needs to inspect it.
6. Update integration tests and verify `/v1/subagents`, CLI `/agents`, and prompt rendering list the new entry.

#### Add a prompt block

1. Add `@block` syntax to the relevant `.txt` template.
2. Add the context key in the loader, usually `agentnode_prompt_loader()`.
3. Use `if=` so absent optional data consumes no tokens.
4. Keep stable role/policy content above the separator and volatile data below it.
5. Add a focused render test before changing parser logic. The renderer is generic and normally should not require modification.

#### Add an API resource

1. Define Pydantic request/response models under `api/domain/`.
2. Create a route module under `api/api_routes/` with `require_user` unless explicitly public.
3. Put ownership and business policy in a service, not route functions.
4. Put persistence in a repository and use parameterized SQL helpers.
5. Include the router in `api/app.py`.
6. Add endpoint tests for authentication, ownership, success, and validation failure.

#### Add a WebSocket event

1. Add a constant in `api/ws/protocol.py`.
2. Choose whether the event must be durable/reconnectable. Durable events should go through `ChatPacketQueue.enqueue()`.
3. Emit it from `AgentRuntime` or `ChatRuntimeManager`, not directly from arbitrary graph nodes.
4. Document payload shape and client handling in `documentation/backend-api.md` and this document.
5. Test delivery, reconnect catch-up, acknowledgement trimming, and rollback fencing if it is branch-sensitive.
