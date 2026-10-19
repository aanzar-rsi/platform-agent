# Graph Report - backend  (2026-10-07)

## Corpus Check
- 260 files · ~230,704 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .jsonl 7, .bin 4, .example 1)

## Summary
- 2068 nodes · 5593 edges · 129 communities (102 shown, 27 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 478 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- api_routes/preferences.py
- call_llm
- require_user
- make_console
- TurnRenderer
- EVA Agent API — Reference & How to Use
- endpoint.py
- llm_client.py
- TestAgentNodePrompt
- emit
- postgres.py
- agentnode.py
- tools/__init__.py
- prompt_loader.py
- update_context_memory
- pathlib
- Any
- mcp_runtime.py
- api_routes/auth.py
- agent_core.py
- TestSubagentNode
- .run_turn
- ._commit
- app.py
- typing
- Repositories
- get_repos
- trace.py
- test_endpoints.py
- FakeAgents
- fetch_one
- edit_file
- web_search.py
- CurrentUser
- context_selector_node
- extract_chunks.py
- ._write_and_read
- BackgroundIdleWatcher
- repositories/mcp.py
- Platform Agent Codebase Documentation
- HfLoadIsQuiet
- log_event
- ChatPacketQueue
- core/config.py
- health.py
- main.py
- _FakeEncoded
- AgentCore
- agentnode_prompt_loader
- WebSocket chat session
- field_validator
- get_checkpointer
- paths.py
- Multi-User Agentic AI Platform — Database Design
- input_security_gate.py
- graphify.js
- render
- TestMainDispatch
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- fetch_all
- _present
- route_from_agent
- agent/kb.py
- subagent_node
- test_db_setup.py
- ws.py
- test_context_memory.py
- retrieve_experiences
- llm_logger.py
- list_subagents
- embeddings.py
- truncate_for_aimessage
- test_prompt_templates.py
- AGENTS.md
- idle_watcher.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- generate_tree
- test_cli_repl.py
- build_config
- _fmt
- postgres_checkpointer.py
- run_turn_interactive
- pydantic
- TestSubagentRegistry
- TestTheme
- repl.py
- TestCreateUser
- tools_service.py
- tool_node
- re
- executor.py
- McpRuntime
- TestAgentRuntimeFanout
- ChatRuntimeManager
- agent/graph.py
- child_agent_node.py
- json_store.py
- now.py
- repositories/__init__.py
- security.py
- SubagentsService
- utc_now_iso
- users.py
- _eval_cond
- execute
- src_subagents_learner_agent_store
- learn_session
- truncate_value
- output_security_gate.py
- TestRuntimeControls
- TestSchemaStatementsAreIdempotent
- Chats
- _NotPaused
- PostgresSaver

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 115 edges
2. `require_user()` - 70 edges
3. `Repositories` - 67 edges
4. `TurnRenderer` - 59 edges
5. `emit()` - 55 edges
6. `get_repos()` - 54 edges
7. `AgentCore` - 46 edges
8. `log_event()` - 44 edges
9. `get_connection()` - 40 edges
10. `in_run()` - 40 edges

## Surprising Connections (you probably didn't know these)
- `Add an API resource` --references--> `require_user()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/core/deps.py
- `Entrypoints` --references--> `ChatRuntimeManager`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/services/chat_runtime_manager.py
- `Topology` --references--> `route_from_agent()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/edges/routing.py
- `Recommended debugging workflow` --references--> `_parse_response()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Main agent loop` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py

## Import Cycles
- None detected.

## Communities (129 total, 27 thin omitted)

### Community 0 - "api_routes/preferences.py"
Cohesion: 0.18
Nodes (10): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, model_validator (+2 more)

### Community 1 - "call_llm"
Cohesion: 0.08
Nodes (29): 8. Observability, Logs, and LLM Replay, Gateway behavior, LLM call logger and replay cache, LLM Client, Observability, and Replay, Logging and mock replay, Recommended debugging workflow, call_llm(), call_llm_stream() (+21 more)

### Community 2 - "require_user"
Cohesion: 0.14
Nodes (39): get_experience(), list_experiences(), Depends, get, Authorized view of active learned experiences., append_version(), audit(), cancel() (+31 more)

### Community 3 - "make_console"
Cohesion: 0.20
Nodes (9): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestHumanInputNode (+1 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.11
Nodes (10): Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., TurnRenderer, make_console() (+2 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.11
Nodes (18): Analytics, Authentication, Checkpoints & rollback, Data store (`data/`), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth), `GET /v1/auth/me` (auth), `GET /v1/chats/{chat_id}/checkpoints` (auth) (+10 more)

### Community 6 - "endpoint.py"
Cohesion: 0.24
Nodes (10): Validate JWT for WebSocket handshake., user_from_token(), agent_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject() (+2 more)

### Community 7 - "llm_client.py"
Cohesion: 0.06
Nodes (44): OpenAI, emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages(), _build_provider(), _cache_key() (+36 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "emit"
Cohesion: 0.18
Nodes (12): MemoryRepository, Memory, Agent policy facets: memory, armory, guardrails and observability., _record_tool_result(), Safe experience retrieval for the main agent hot path., current_ids(), emit(), _error() (+4 more)

### Community 10 - "postgres.py"
Cohesion: 0.15
Nodes (15): Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute(), fetch_all(), fetch_one() (+7 more)

### Community 11 - "agentnode.py"
Cohesion: 0.08
Nodes (28): BaseMessage, agent_node(), _on_token(), _coerce_int(), _dispatch_planned_step(), _extract_tag(), _format_conversation(), _is_turn_start() (+20 more)

### Community 12 - "tools/__init__.py"
Cohesion: 0.15
Nodes (12): langchain_core_tools, platform, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…, Internal tools package for the agent., Any (+4 more)

### Community 13 - "prompt_loader.py"
Cohesion: 0.18
Nodes (16): Major prompt functions, _armory_text(), fast_agent_prompt_loader(), _load_module(), _Node, _parse(), planner_agent_prompt_loader(), PromptRenderError (+8 more)

### Community 14 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 15 - "pathlib"
Cohesion: 0.10
Nodes (25): os, pathlib, scripts, src_agent_nodes, src_models, DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional… (+17 more)

### Community 16 - "Any"
Cohesion: 0.18
Nodes (13): _filter_checkpoint_tree(), _infer_node(), _is_redundant_checkpoint(), list_checkpoint_tree(), _message_content(), _message_role(), _node_from_metadata(), Any (+5 more)

### Community 17 - "mcp_runtime.py"
Cohesion: 0.17
Nodes (14): Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, asyncio, collections, httpx, logging, mcp, mcp_client_sse, mcp_client_stdio (+6 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "agent_core.py"
Cohesion: 0.12
Nodes (17): Durable AgentCore identities, run reservations, and child results., concurrent_futures, dataclasses, Agent lifecycle facade and compatibility exports., ChildHandle, Policy, Core agent dataclasses shared across runtime components., ChildRunner (+9 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.20
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - ".run_turn"
Cohesion: 0.10
Nodes (14): AgentRuntime, on_child_event(), on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate() (+6 more)

### Community 22 - "._commit"
Cohesion: 0.18
Nodes (6): emit_tag(), _format_args(), Any, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short()

### Community 23 - "app.py"
Cohesion: 0.21
Nodes (12): api_api_routes, create_app(), get_settings(), configure_logging(), get_pool(), ConnectionPool, lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1). (+4 more)

### Community 24 - "typing"
Cohesion: 0.10
Nodes (38): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), get_policy(), list_chats(), delete, Depends (+30 more)

### Community 25 - "Repositories"
Cohesion: 0.12
Nodes (23): Any, Depends, get, summary(), add_memory(), clear_memory(), get_memory(), put_memory() (+15 more)

### Community 26 - "get_repos"
Cohesion: 0.11
Nodes (30): connect_server(), create_server(), delete_server(), disconnect_server(), import_servers(), list_servers(), Any, delete (+22 more)

### Community 27 - "trace.py"
Cohesion: 0.17
Nodes (19): trace_requests(), work(), bind(), context(), _persist(), Any, Path, Canonical, redacted JSON trace events for API and agent operations. (+11 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "FakeAgents"
Cohesion: 0.13
Nodes (11): pytest, FakeAgents, parent_core(), AgentCore policy and independent-child behavior without a live database., test_cancelled_running_child_cannot_commit_result(), test_child_result_requires_parent_lineage(), test_nonblocking_children_and_one_run_per_agent(), slow() (+3 more)

### Community 30 - "fetch_one"
Cohesion: 0.34
Nodes (7): fetch_one(), _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "edit_file"
Cohesion: 0.22
Nodes (14): 4. Internal Tool Subsystem, File tools, Information and planning tools, edit_file(), Any, Path, tool, Read content from a text-based file. Supports optional line-range slicing via… (+6 more)

### Community 32 - "web_search.py"
Cohesion: 0.17
Nodes (14): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, BaseModel, field_validator (+6 more)

### Community 33 - "CurrentUser"
Cohesion: 0.24
Nodes (13): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CurrentUser, CheckpointOut (+5 more)

### Community 34 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "extract_chunks.py"
Cohesion: 0.08
Nodes (36): 9. Learning Agent Detailed Flow and Diagnostics, Experience API view, Full learner sequence, Learner graph, Learning Agent and Experience System, Learning-agent diagnostic table, Step 1: load trajectory, Step 2: extract reusable advice (+28 more)

### Community 36 - "._write_and_read"
Cohesion: 0.14
Nodes (9): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall (+1 more)

### Community 37 - "BackgroundIdleWatcher"
Cohesion: 0.15
Nodes (8): CLI, Commands, Flow, Idle scheduling and branch handling, BackgroundIdleWatcher, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread., Run the async watcher in a daemon thread for non-async entrypoints.

### Community 38 - "repositories/mcp.py"
Cohesion: 0.20
Nodes (13): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+5 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.08
Nodes (24): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Authentication (+16 more)

### Community 40 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 41 - "log_event"
Cohesion: 0.14
Nodes (30): json, bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_context_select(), log_error(), log_event() (+22 more)

### Community 42 - "ChatPacketQueue"
Cohesion: 0.18
Nodes (7): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior

### Community 43 - "core/config.py"
Cohesion: 0.15
Nodes (9): BaseSettings, Settings, dotenv, functools, pydantic_settings, BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints… (+1 more)

### Community 44 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 45 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 46 - "_FakeEncoded"
Cohesion: 0.33
Nodes (3): list, _FakeEncoded, _FakeModel

### Community 47 - "AgentCore"
Cohesion: 0.12
Nodes (6): AgentCore, AgentID, Message, Armory, Guardrails, Observability

### Community 48 - "agentnode_prompt_loader"
Cohesion: 0.16
Nodes (13): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, 5. API Layer and Service Boundaries, Add a planner-callable sub-agent, Add a prompt block, Add an API resource, Add an internal tool, Detailed Subsystem Reference (+5 more)

### Community 49 - "WebSocket chat session"
Cohesion: 0.14
Nodes (12): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session, 6. WebSocket Runtime, Queues, and Recovery (+4 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "get_checkpointer"
Cohesion: 0.22
Nodes (13): 7. PostgreSQL, Repositories, and Checkpoints, Checkpointer function map, Database troubleshooting, active_checkpoint_path(), get_checkpointer(), get_thread_state(), list_checkpoints(), list_leaf_checkpoints() (+5 more)

### Community 52 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "input_security_gate.py"
Cohesion: 0.53
Nodes (5): _as_dict(), _coerce_int(), _deny(), input_security_gate_node(), Input security gate for executor-bound planner actions.

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 60 - "fetch_all"
Cohesion: 0.26
Nodes (6): fetch_all(), Any, _iso(), Any, _row_to_entry(), Durable user-memory tools

### Community 61 - "_present"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.22
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "agent/kb.py"
Cohesion: 0.06
Nodes (72): get_connection(), Connection, AgentRepository, Any, fixture, math, _active_for_uid(), _audit() (+64 more)

### Community 64 - "subagent_node"
Cohesion: 0.16
Nodes (16): Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, Sub-agents: `subagent_node` and gate, Topology, RunnableConfig, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by… (+8 more)

### Community 65 - "test_db_setup.py"
Cohesion: 0.22
Nodes (5): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, TestDbSetupLive

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "test_context_memory.py"
Cohesion: 0.10
Nodes (18): Why execution memory is split, build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts. (+10 more)

### Community 68 - "retrieve_experiences"
Cohesion: 0.24
Nodes (7): Retrieval in the main agent, Standalone learner agent: extract experience chunks from idle chats., format_experiences_for_prompt(), Any, Return top-k experience chunks. Never raises — returns [] on any failure or…, retrieve_experiences(), TestRetrieveSoftFail

### Community 69 - "llm_logger.py"
Cohesion: 0.09
Nodes (29): atexit, datetime, queue, _record(), _replay(), _ensure_writer_started(), _writer_loop(), build_record() (+21 more)

### Community 70 - "list_subagents"
Cohesion: 0.50
Nodes (4): list_subagents(), Any, Depends, get

### Community 71 - "embeddings.py"
Cohesion: 0.24
Nodes (9): hashlib, numpy, _embed_numpy(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy…, Deterministic hashing bag-of-words vectorizer (no ML dependencies)., Embed multiple strings, batching when possible. (+1 more)

### Community 72 - "truncate_for_aimessage"
Cohesion: 0.36
Nodes (7): collect_child_node(), Explicitly collect a selected child without importing its full transcript., Any, Shared stringify + truncate helpers for AIMessage previews., stringify_for_preview(), truncate_for_aimessage(), truncate_text()

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.15
Nodes (12): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+4 more)

### Community 75 - "idle_watcher.py"
Cohesion: 0.18
Nodes (11): _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+3 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 89 - "test_cli_repl.py"
Cohesion: 0.10
Nodes (16): io, rich_console, rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, parse_command() (+8 more)

### Community 90 - "build_config"
Cohesion: 0.15
Nodes (16): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Functions to start with when tracing a turn, Planner response parsing details, PostgreSQL responsibilities, build_config(), has_pending_interrupt(), initial_state_for_thread() (+8 more)

### Community 91 - "_fmt"
Cohesion: 0.33
Nodes (6): _fmt(), Any, Serialize structured prompt context as TOON., to_toon(), json.dumps(indent=2) was 2.6x more tokens for the same data., TestFormatting

### Community 92 - "postgres_checkpointer.py"
Cohesion: 0.25
Nodes (10): langgraph_checkpoint_postgres, _ensure_branch_learn_table(), _ensure_message_sync_schema(), _get_pool(), is_leaf_learned(), mark_leaf_learned(), ConnectionPool, LangGraph checkpointer backed by Postgres (`checkpoints`/`checkpoint_blobs`/… (+2 more)

### Community 94 - "run_turn_interactive"
Cohesion: 0.10
Nodes (21): ChildEventCallback, contextvars, Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_child_callback(), reset_subagent_callback(), set_child_callback(), set_subagent_callback() (+13 more)

### Community 96 - "pydantic"
Cohesion: 0.21
Nodes (8): pydantic, EditFileArgs, BaseModel, field_validator, model_validator, Internal tools for file I/O operations, file search, and directory management., ReadFileArgs, SearchFileArgs

### Community 99 - "repl.py"
Cohesion: 0.12
Nodes (32): PreferencesRepository, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, PromptSession, rich_prompt, rich_table (+24 more)

### Community 101 - "tools_service.py"
Cohesion: 0.23
Nodes (12): list_tools(), Any, Depends, get, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict() (+4 more)

### Community 102 - "tool_node"
Cohesion: 0.28
Nodes (5): empty_context_memory(), RunnableConfig, tool_node(), TestPromptLoader, TestToolAndSubagentIngest

### Community 103 - "re"
Cohesion: 0.27
Nodes (4): re, requests, GitHubRepoDownloader, main()

### Community 104 - "executor.py"
Cohesion: 0.21
Nodes (16): Command execution tools, Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool (+8 more)

### Community 105 - "McpRuntime"
Cohesion: 0.12
Nodes (6): McpConnection, McpRuntime, Any, BaseException, test_http_404_is_reported_as_endpoint_error(), test_http_transport_connects_to_real_streamable_server()

### Community 106 - "TestAgentRuntimeFanout"
Cohesion: 0.33
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.18
Nodes (7): ChatRuntime, ChatRuntimeManager, _deferred_fork(), Any, WebSocket, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 108 - "agent/graph.py"
Cohesion: 0.11
Nodes (31): State, langchain_core_messages, langchain_core_runnables, langgraph_graph, langgraph_graph_message, langgraph_types, clear_pause(), is_pause_requested() (+23 more)

### Community 109 - "child_agent_node.py"
Cohesion: 0.43
Nodes (6): child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy(), _root_owner(), emit_child_event(), Any

### Community 111 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 112 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 113 - "repositories/__init__.py"
Cohesion: 0.44
Nodes (3): AuthSessionRepository, _iso(), Any

### Community 114 - "security.py"
Cohesion: 0.25
Nodes (6): decode_access_token(), Any, argon2, argon2_exceptions, jwt, secrets

### Community 115 - "SubagentsService"
Cohesion: 0.50
Nodes (3): Any, SubagentsService, TestCatalogAPI

### Community 116 - "utc_now_iso"
Cohesion: 0.46
Nodes (6): utc_now_iso(), _done(), _target(), _done(), _target(), set_trace_parent()

### Community 117 - "users.py"
Cohesion: 0.20
Nodes (14): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+6 more)

### Community 119 - "execute"
Cohesion: 0.29
Nodes (4): execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _load(), Any

### Community 121 - "learn_session"
Cohesion: 0.18
Nodes (9): Agent trace logger, learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, Path, Append-only JSONL writer for one agent., _safe_agent_id(), SessionLogger (+1 more)

### Community 122 - "truncate_value"
Cohesion: 0.32
Nodes (4): Recursively truncate oversized strings in payloads., truncate_value(), _utc_now(), TestTruncate

### Community 123 - "output_security_gate.py"
Cohesion: 0.53
Nodes (5): output_security_gate_node(), Output security gate for executor node updates before re-planning., _sanitize_history(), _sanitize_memory(), _sanitize_messages()

### Community 126 - "Chats"
Cohesion: 0.40
Nodes (5): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth)

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 548 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `make_console`, `repl.py`, `._commit`, `test_cli_repl.py`, `run_turn_interactive`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `api_routes/preferences.py`, `require_user`, `tools_service.py`, `list_subagents`, `endpoint.py`, `health.py`, `api_routes/auth.py`, `typing`, `Repositories`, `get_repos`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `emit()` connect `emit` to `endpoint.py`, `agentnode.py`, `mcp_runtime.py`, `agent_core.py`, `get_repos`, `trace.py`, `CurrentUser`, `log_event`, `AgentCore`, `route_from_agent`, `agent/kb.py`, `subagent_node`, `retrieve_experiences`, `postgres_checkpointer.py`, `run_turn_interactive`, `repl.py`, `tool_node`, `agent/graph.py`, `child_agent_node.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._