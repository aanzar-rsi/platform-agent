# Graph Report - backend  (2026-10-06)

## Corpus Check
- 229 files · ~165,752 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 9 file(s) not represented in the graph (top: .bin 4, .jsonl 3, .example 1)

## Summary
- 2052 nodes · 5567 edges · 126 communities (102 shown, 24 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 457 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- api_routes/preferences.py
- .mock_mode
- require_user
- Repositories
- TurnRenderer
- EVA Agent API — Reference & How to Use
- users.py
- agentnode_prompt_loader
- TestAgentNodePrompt
- idle_watcher.py
- typing
- agentnode.py
- test_llm_mock_mode.py
- AgentRepository
- update_context_memory
- ChatPacketQueue
- postgres_checkpointer.py
- agent_runtime.py
- api_routes/auth.py
- Policy
- TestSubagentNode
- .run_turn
- agent/kb.py
- llm_client.py
- chat_service.py
- Memory
- CurrentUser
- trace.py
- test_endpoints.py
- FakeAgents
- Tools: `tool_node`
- executor.py
- web_search.py
- CheckpointService
- context_selector_node
- learner_agent/graph.py
- ._write_and_read
- count_tokens
- execute
- Platform Agent Codebase Documentation
- mcp_runtime.py
- log_event
- build_config
- src/config.py
- WebSocket chat session
- default_policy
- list_checkpoint_tree
- agent_core.py
- security.py
- test_experience_system.py
- field_validator
- in_run
- PostgresSaver
- Multi-User Agentic AI Platform — Database Design
- SessionRepository
- graphify.js
- render
- _fmt
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- GitHubRepoDownloader
- test_prompt_render.py
- route_from_agent
- health.py
- agent/graph.py
- pathlib
- ws.py
- test_context_memory.py
- emit
- llm_logger.py
- json_store.py
- AgentCore
- repositories/memory.py
- test_prompt_templates.py
- AGENTS.md
- BackgroundIdleWatcher
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- test_db_setup.py
- renderer.py
- utc_now_iso
- prompt_loader.py
- build_cache_key
- learn_session
- pydantic
- tool_node
- paths.py
- repl.py
- Repository map
- tools_service.py
- test_agent_core.py
- HfLoadIsQuiet
- deps.py
- McpRuntime
- test_subagents_integration.py
- ChatRuntimeManager
- child_agent_node.py
- list_checkpoints
- truncate_value
- now.py
- TestMainDispatch
- PreferencesRepository
- _session_prompt
- _FakeEncoded
- bootstrap.py
- generate_tree
- json
- src_subagents_learner_agent_store
- TestRuntimeControls
- sys_info.py
- Observability
- user_memory_fetch
- .test_public_signatures_stayed_stub_compatible

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 115 edges
2. `require_user()` - 70 edges
3. `Repositories` - 67 edges
4. `TurnRenderer` - 59 edges
5. `get_repos()` - 54 edges
6. `emit()` - 53 edges
7. `log_event()` - 44 edges
8. `get_connection()` - 40 edges
9. `AgentCore` - 39 edges
10. `call_llm()` - 39 edges

## Surprising Connections (you probably didn't know these)
- `Add an API resource` --references--> `require_user()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/core/deps.py
- `Entrypoints` --references--> `ChatRuntimeManager`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/services/chat_runtime_manager.py
- `Topology` --references--> `route_from_agent()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/edges/routing.py
- `Recommended debugging workflow` --references--> `_parse_response()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py

## Import Cycles
- None detected.

## Communities (126 total, 24 thin omitted)

### Community 0 - "api_routes/preferences.py"
Cohesion: 0.25
Nodes (9): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, PreferencesService (+1 more)

### Community 1 - ".mock_mode"
Cohesion: 0.18
Nodes (8): _Chunk, _Completion, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, TestMockModeOn, TestStreamReplay, _Usage

### Community 2 - "require_user"
Cohesion: 0.18
Nodes (33): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+25 more)

### Community 3 - "Repositories"
Cohesion: 0.15
Nodes (22): connect_server(), create_server(), delete_server(), disconnect_server(), import_servers(), list_servers(), Any, delete (+14 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.05
Nodes (29): emit_tag(), _format_args(), Any, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning. (+21 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.08
Nodes (23): Analytics, Authentication, Chats, Checkpoints & rollback, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth) (+15 more)

### Community 6 - "users.py"
Cohesion: 0.26
Nodes (10): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+2 more)

### Community 7 - "agentnode_prompt_loader"
Cohesion: 0.12
Nodes (15): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, 5. API Layer and Service Boundaries, 8. Observability, Logs, and LLM Replay, Add a prompt block, Add an API resource, Add an internal tool, Detailed Subsystem Reference (+7 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "idle_watcher.py"
Cohesion: 0.16
Nodes (13): _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+5 more)

### Community 10 - "typing"
Cohesion: 0.14
Nodes (16): Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute(), fetch_all(), fetch_one() (+8 more)

### Community 11 - "agentnode.py"
Cohesion: 0.10
Nodes (25): BaseMessage, 1. End-to-End Turn Execution, Functions to start with when tracing a turn, Main agent loop, agent_node(), _on_token(), _coerce_int(), _extract_tag() (+17 more)

### Community 12 - "test_llm_mock_mode.py"
Cohesion: 0.13
Nodes (12): fake_gateway(), create(), _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create., Captures every record the client emits instead of writing it anywhere., _Raw (+4 more)

### Community 13 - "AgentRepository"
Cohesion: 0.12
Nodes (7): fetch_all(), fetch_one(), Any, AgentRepository, Any, Durable AgentCore identities, run reservations, and child results., uuid

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "ChatPacketQueue"
Cohesion: 0.18
Nodes (7): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior

### Community 16 - "postgres_checkpointer.py"
Cohesion: 0.18
Nodes (17): langgraph_checkpoint_postgres, _ensure_branch_learn_table(), _ensure_message_sync_schema(), get_checkpointer(), _get_pool(), is_leaf_learned(), list_leaf_checkpoints(), mark_leaf_learned() (+9 more)

### Community 17 - "agent_runtime.py"
Cohesion: 0.18
Nodes (15): api_api_routes, get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., ensure_client_path() (+7 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.12
Nodes (8): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout, TestSubagentNode, echo()

### Community 21 - ".run_turn"
Cohesion: 0.11
Nodes (12): AgentRuntime, on_child_event(), on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate() (+4 more)

### Community 22 - "agent/kb.py"
Cohesion: 0.05
Nodes (89): get_connection(), get_pool(), Connection, ConnectionPool, 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, Step 2: extract reusable advice, fixture (+81 more)

### Community 23 - "llm_client.py"
Cohesion: 0.14
Nodes (33): Gateway behavior, LLM call logger and replay cache, OpenAI, emit_usage(), Any, _build_messages(), _cache_key(), call_llm() (+25 more)

### Community 24 - "chat_service.py"
Cohesion: 0.12
Nodes (34): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), get_policy(), list_chats(), delete, Depends (+26 more)

### Community 25 - "Memory"
Cohesion: 0.18
Nodes (16): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+8 more)

### Community 26 - "CurrentUser"
Cohesion: 0.14
Nodes (14): CurrentUser, McpCreateRequest, McpUpdateRequest, model_validator, connection_log(), McpService, public_server(), Any (+6 more)

### Community 27 - "trace.py"
Cohesion: 0.20
Nodes (12): bind_from_config(), context(), _persist(), Any, Path, Canonical, redacted JSON trace events for API and agent operations., Wrap LangGraph nodes once so every exit (including caught failures) is traced., _safe_id() (+4 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 30 - "Tools: `tool_node`"
Cohesion: 0.16
Nodes (19): 4. Internal Tool Subsystem, File tools, Information and planning tools, Tools: `tool_node`, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces… (+11 more)

### Community 31 - "executor.py"
Cohesion: 0.20
Nodes (16): Command execution tools, execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python… (+8 more)

### Community 32 - "web_search.py"
Cohesion: 0.17
Nodes (14): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, BaseModel, field_validator (+6 more)

### Community 33 - "CheckpointService"
Cohesion: 0.24
Nodes (12): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+4 more)

### Community 34 - "context_selector_node"
Cohesion: 0.39
Nodes (3): context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "learner_agent/graph.py"
Cohesion: 0.13
Nodes (21): Experience API view, Learner graph, Learning Agent and Experience System, Retrieval in the main agent, Step 1: load trajectory, Step 3: persist and index, src_agent, Standalone learner LangGraph: load_session → extract_chunks → persist. (+13 more)

### Community 36 - "._write_and_read"
Cohesion: 0.18
Nodes (7): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall

### Community 37 - "count_tokens"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 38 - "execute"
Cohesion: 0.19
Nodes (15): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), McpRepository, _load() (+7 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.08
Nodes (25): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Authentication (+17 more)

### Community 40 - "mcp_runtime.py"
Cohesion: 0.11
Nodes (20): Validate JWT for WebSocket handshake., user_from_token(), Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, api_ws, agent_ws(), _handle_client_message(), Any, WebSocket (+12 more)

### Community 41 - "log_event"
Cohesion: 0.14
Nodes (30): os, bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_context_select(), log_error(), log_event() (+22 more)

### Community 42 - "build_config"
Cohesion: 0.27
Nodes (11): Checkpointer function map, build_config(), get_thread_state(), _message_content(), _message_role(), Any, RunnableConfig, Config that resumes / time-travels from a specific checkpoint. (+3 more)

### Community 43 - "src/config.py"
Cohesion: 0.20
Nodes (8): dotenv, functools, pydantic_settings, get_settings(), BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 44 - "WebSocket chat session"
Cohesion: 0.15
Nodes (11): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session, 6. WebSocket Runtime, Queues, and Recovery (+3 more)

### Community 45 - "default_policy"
Cohesion: 0.24
Nodes (9): main(), Opt-in backfill of owner-provenanced legacy learner chunks into the KB. Run…, default_policy(), _memory(), BaseModel, Tools for reading and writing per-user long-term memory / preferences., UserMemoryFetchArgs, UserMemoryUpdateArgs (+1 more)

### Community 46 - "list_checkpoint_tree"
Cohesion: 0.17
Nodes (11): _filter_checkpoint_tree(), has_pending_interrupt(), _infer_node(), _is_redundant_checkpoint(), list_checkpoint_tree(), _node_from_metadata(), Best-effort label for "which node just wrote this checkpoint" — there is no…, Prefer LangGraph checkpoint metadata (authoritative node writes). (+3 more)

### Community 47 - "agent_core.py"
Cohesion: 0.20
Nodes (6): AgentID, _allowed(), Armory, intersect_policy(), Agent identity, effective policy and durable lifecycle facade., A child cannot grant capabilities, scopes or a tenant its parent lacks.

### Community 48 - "security.py"
Cohesion: 0.25
Nodes (6): decode_access_token(), Any, argon2, argon2_exceptions, jwt, secrets

### Community 49 - "test_experience_system.py"
Cohesion: 0.11
Nodes (23): Full learner sequence, datetime, Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval. (+15 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "in_run"
Cohesion: 0.13
Nodes (22): available_mcp_tools(), call_mcp_tool(), McpTool, clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active() (+14 more)

### Community 52 - "PostgresSaver"
Cohesion: 0.33
Nodes (5): PostgreSQL responsibilities, initial_state_for_thread(), PostgresSaver, PostgresSaver that also mirrors new messages into the `messages` table., Full state for a brand-new thread; message-only delta for existing ones.

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 57 - "_fmt"
Cohesion: 0.33
Nodes (6): _fmt(), Any, Serialize structured prompt context as TOON., to_toon(), json.dumps(indent=2) was 2.6x more tokens for the same data., TestFormatting

### Community 60 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

### Community 61 - "test_prompt_render.py"
Cohesion: 0.19
Nodes (6): _eval_cond(), _present(), Tests for the declarative prompt renderer in prompt_loader.py., The prototype returned True here, so `if=turn_start` always fired and the model…, TestConditions, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.24
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 64 - "agent/graph.py"
Cohesion: 0.07
Nodes (40): Add a planner-callable sub-agent, Agent runtime event conversion, Context selection and user questions, Current Extension Points and Limits, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, State (+32 more)

### Community 65 - "pathlib"
Cohesion: 0.11
Nodes (19): io, pathlib, rich_console, scripts, src_agent_nodes, src_models, sys, Unit tests for the live turn renderer (live rendering disabled in tests). (+11 more)

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "test_context_memory.py"
Cohesion: 0.10
Nodes (18): langgraph_graph, build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts. (+10 more)

### Community 68 - "emit"
Cohesion: 0.18
Nodes (15): create_app(), trace_requests(), MemoryRepository, work(), bind(), emit(), _error(), BaseException (+7 more)

### Community 69 - "llm_logger.py"
Cohesion: 0.08
Nodes (32): atexit, queue, src_utils, _ensure_writer_started(), _safe_agent_id(), _writer_loop(), build_record(), current_session_ids() (+24 more)

### Community 70 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 71 - "AgentCore"
Cohesion: 0.21
Nodes (3): AgentCore, Guardrails, Message

### Community 72 - "repositories/memory.py"
Cohesion: 0.48
Nodes (3): _iso(), Any, _row_to_entry()

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.14
Nodes (13): re, load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables. (+5 more)

### Community 75 - "BackgroundIdleWatcher"
Cohesion: 0.15
Nodes (8): CLI, Commands, Flow, Idle scheduling and branch handling, BackgroundIdleWatcher, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread., Run the async watcher in a daemon thread for non-async entrypoints.

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "test_db_setup.py"
Cohesion: 0.13
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 89 - "renderer.py"
Cohesion: 0.17
Nodes (8): rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, parse_command(), CLI theme - one place for every terminal color/style used by the CLI. Keys are…, TestParseCommand

### Community 90 - "utc_now_iso"
Cohesion: 0.46
Nodes (6): utc_now_iso(), _done(), _target(), _done(), _target(), set_trace_parent()

### Community 91 - "prompt_loader.py"
Cohesion: 0.18
Nodes (15): Major prompt functions, _has_tool(), _load_module(), _Node, _parse(), PromptRenderError, Exception, Prompt rendering and loading for every agent and sub-agent in the project. One… (+7 more)

### Community 92 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 94 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 96 - "pydantic"
Cohesion: 0.21
Nodes (8): pydantic, EditFileArgs, BaseModel, field_validator, model_validator, Internal tools for file I/O operations, file search, and directory management., ReadFileArgs, SearchFileArgs

### Community 97 - "tool_node"
Cohesion: 0.28
Nodes (5): empty_context_memory(), RunnableConfig, tool_node(), TestPromptLoader, TestToolAndSubagentIngest

### Community 98 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 99 - "repl.py"
Cohesion: 0.10
Nodes (40): api_db_repositories, ChildEventCallback, contextvars, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_prompt (+32 more)

### Community 100 - "Repository map"
Cohesion: 0.44
Nodes (4): AuthSessionRepository, _iso(), Any, Repository map

### Community 101 - "tools_service.py"
Cohesion: 0.57
Nodes (6): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info()

### Community 102 - "test_agent_core.py"
Cohesion: 0.18
Nodes (12): ChildRunner, Bounded, process-local execution of durable child runs., Before a parent finishes, collect all its children by persisted lineage., parent_core(), AgentCore policy and independent-child behavior without a live database., test_cancelled_running_child_cannot_commit_result(), test_child_result_requires_parent_lineage(), test_nonblocking_children_and_one_run_per_agent() (+4 more)

### Community 103 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 104 - "deps.py"
Cohesion: 0.11
Nodes (18): Any, Depends, get, summary(), get_experience(), list_experiences(), Depends, get (+10 more)

### Community 105 - "McpRuntime"
Cohesion: 0.12
Nodes (6): McpConnection, McpRuntime, Any, BaseException, test_http_404_is_reported_as_endpoint_error(), test_http_transport_connects_to_real_streamable_server()

### Community 106 - "test_subagents_integration.py"
Cohesion: 0.12
Nodes (11): Any, SubagentsService, emit_subagent_event(), Bind a sub-agent progress callback for the current context; returns a reset…, set_subagent_callback(), SubagentEventCallback, End-to-end tests for EVA subagent integration. Covers: registry catalog,…, TestCatalogAPI (+3 more)

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.18
Nodes (7): ChatRuntime, ChatRuntimeManager, _deferred_fork(), Any, WebSocket, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 108 - "child_agent_node.py"
Cohesion: 0.43
Nodes (6): child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy(), _root_owner(), emit_child_event(), Any

### Community 109 - "list_checkpoints"
Cohesion: 0.33
Nodes (6): 7. PostgreSQL, Repositories, and Checkpoints, Database troubleshooting, active_checkpoint_path(), list_checkpoints(), Return readable checkpoint summaries for a thread (newest first)., Checkpoint ids on the path from the current graph tip back to the root. Used to…

### Community 111 - "truncate_value"
Cohesion: 0.18
Nodes (8): Agent trace logger, Path, Recursively truncate oversized strings in payloads., Append-only JSONL writer for one agent., SessionLogger, truncate_value(), _utc_now(), TestTruncate

### Community 112 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 114 - "PreferencesRepository"
Cohesion: 0.47
Nodes (4): PreferencesRepository, _load(), Any, _save_runtime()

### Community 115 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 116 - "_FakeEncoded"
Cohesion: 0.33
Nodes (3): list, _FakeEncoded, _FakeModel

### Community 117 - "bootstrap.py"
Cohesion: 0.18
Nodes (16): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), ensure_venv_on_path(), get_python_executable(), get_venv_python() (+8 more)

### Community 118 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 119 - "json"
Cohesion: 0.40
Nodes (4): json, DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional…

### Community 122 - "sys_info.py"
Cohesion: 0.25
Nodes (7): langchain_core_tools, platform, Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 124 - "user_memory_fetch"
Cohesion: 0.38
Nodes (7): Durable user-memory tools, Any, tool, Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update()

## Knowledge Gaps
- **43 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 555 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AgentCore` connect `AgentCore` to `repl.py`, `emit`, `learner_agent/graph.py`, `test_agent_core.py`, `ChatRuntimeManager`, `child_agent_node.py`, `AgentRepository`, `default_policy`, `agent_core.py`, `agent_runtime.py`, `test_experience_system.py`, `Policy`, `chat_service.py`, `Memory`, `utc_now_iso`, `Observability`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `TurnRenderer` connect `TurnRenderer` to `pathlib`, `renderer.py`, `repl.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `api_routes/preferences.py`, `CheckpointService`, `require_user`, `Repositories`, `tools_service.py`, `deps.py`, `mcp_runtime.py`, `api_routes/auth.py`, `chat_service.py`, `Memory`, `health.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._