# Graph Report - backend  (2026-10-19)

## Corpus Check
- 228 files · ~363,141 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 27 file(s) not represented in the graph (top: .jsonl 20, .bin 4, .example 1)

## Summary
- 2200 nodes · 6188 edges · 119 communities (95 shown, 24 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 534 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- typing
- test_llm_mock_mode.py
- ChatPacketQueue
- AnalyticsRepository
- TurnRenderer
- EVA Agent API — Reference & How to Use
- test_cli_repl.py
- llm_client.py
- TestAgentNodePrompt
- AgentCore
- postgres.py
- _parse_response
- retrieve_experiences
- prompt_loader.py
- update_context_memory
- test_context_memory.py
- lookup_cached_response
- agent_runtime.py
- api_routes/auth.py
- make_console
- TestSubagentNode
- postgres_checkpointer.py
- Repositories
- agentnode.py
- ChatService
- MemoryService
- CurrentUser
- emit
- agent_core.py
- run_turn_interactive
- SessionRepository
- tools/__init__.py
- armory.py
- extract_chunks.py
- context_selector_node
- load_session.py
- ._write_and_read
- embeddings.py
- execute
- Platform Agent Codebase Documentation
- BackgroundIdleWatcher
- CheckpointService
- .run_turn
- Settings
- MemoryRepository
- FastAPI
- WebSearchArgs
- re
- web_search.py
- control.py
- executor.py
- log_event
- paths.py
- Multi-User Agentic AI Platform — Database Design
- test_endpoints.py
- graphify.js
- render
- tools_service.py
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- agentnode_prompt_loader
- test_prompt_render.py
- route_from_agent
- agent/kb.py
- test_subagents_integration.py
- test_db_setup.py
- ws.py
- tool_node
- Message
- llm_logger.py
- build_cache_key
- Tools: `tool_node`
- mcp_runtime.py
- test_prompt_templates.py
- AGENTS.md
- idle_watcher.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- context_manager.py
- repl.py
- fetch_all
- main.py
- renderer.py
- policy_schema.py
- input_security_gate_node
- src/config.py
- AgentRepository
- ReadFileArgs
- Armory
- health.py
- test_phased_plan.py
- file_io.py
- McpRuntime
- ChatRuntimeManager
- TestSchemaStatementsAreIdempotent
- json_store.py
- now.py
- fetch_one
- TestMainDispatch
- security.py
- src_subagents_learner_agent_store
- test_experience_system.py
- truncate_value
- parse_command
- decompose_query
- endpoint.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 124 edges
2. `Repositories` - 75 edges
3. `require_user()` - 75 edges
4. `get_repos()` - 60 edges
5. `TurnRenderer` - 59 edges
6. `emit()` - 55 edges
7. `AgentCore` - 48 edges
8. `get_connection()` - 44 edges
9. `log_event()` - 44 edges
10. `agent_node()` - 43 edges

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

## Communities (119 total, 24 thin omitted)

### Community 0 - "typing"
Cohesion: 0.13
Nodes (18): get_experience(), list_experiences(), Depends, get, Authorized view of active learned experiences., get_prefs(), put_prefs(), Any (+10 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.06
Nodes (38): Gateway behavior, LLM call logger and replay cache, list, src_models, call_llm(), call_llm_stream(), src_utils, Summarise the given text using the LLM. (+30 more)

### Community 2 - "ChatPacketQueue"
Cohesion: 0.15
Nodes (10): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior, emit_child_event() (+2 more)

### Community 3 - "AnalyticsRepository"
Cohesion: 0.25
Nodes (4): AnalyticsRepository, Any, _TimeWindow, test_summary_can_filter_one_agent()

### Community 4 - "TurnRenderer"
Cohesion: 0.10
Nodes (13): emit_tag(), _format_args(), Any, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning. (+5 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.06
Nodes (30): Analytics, Authentication, Chats, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth) (+22 more)

### Community 6 - "test_cli_repl.py"
Cohesion: 0.15
Nodes (13): handle_step(), prompt_for_interrupt(), interrupt_step(), make_console(), Console, patch, Unit tests for the CLI REPL: command parsing, step handling, interrupts, and…, TestHandleStep (+5 more)

### Community 7 - "llm_client.py"
Cohesion: 0.09
Nodes (36): OpenAI, emit_cache_hit(), emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages(), _build_provider() (+28 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "AgentCore"
Cohesion: 0.15
Nodes (8): AgentCore, AgentID, ChildHandle, Observability, child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy(), _root_owner()

### Community 10 - "postgres.py"
Cohesion: 0.27
Nodes (6): Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, Process-wide Postgres connection pool + small query helpers for `src/`. The…

### Community 11 - "_parse_response"
Cohesion: 0.12
Nodes (10): _parse_child_calls(), _parse_parameters(), _parse_response(), Consume the LLM stream, call on_token for each visible chunk, return the full…, Parse the full LLM response into a state update dict., _run_stream(), test_parse_parameters_strips_cdata_wrapper_from_steps_json(), test_parse_response_accepts_tool_tag_as_tool_name() (+2 more)

### Community 12 - "retrieve_experiences"
Cohesion: 0.17
Nodes (10): Retrieval in the main agent, Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., format_experiences_for_prompt(), Any, Return top-k experience chunks. Never raises — returns [] on any failure or…, retrieve_experiences() (+2 more)

### Community 13 - "prompt_loader.py"
Cohesion: 0.12
Nodes (23): Major prompt functions, _armory_text(), fast_agent_prompt_loader(), _fmt(), _load_module(), _Node, _parse(), planner_agent_prompt_loader() (+15 more)

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "test_context_memory.py"
Cohesion: 0.07
Nodes (35): State, json, langchain_core_runnables, langgraph_graph, langgraph_graph_message, pathlib, pydantic, scripts (+27 more)

### Community 16 - "lookup_cached_response"
Cohesion: 0.47
Nodes (3): lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, TestLookupSoftFails

### Community 17 - "agent_runtime.py"
Cohesion: 0.14
Nodes (20): api_api_routes, create_app(), get_settings(), BaseSettings, Settings, configure_logging(), get_pool(), ConnectionPool (+12 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.20
Nodes (16): login(), logout(), me(), Depends, get, post, create_access_token(), decode_access_token() (+8 more)

### Community 19 - "make_console"
Cohesion: 0.19
Nodes (3): make_console(), Console, TestTurnRenderer

### Community 20 - "TestSubagentNode"
Cohesion: 0.12
Nodes (8): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout, TestSubagentNode, echo()

### Community 21 - "postgres_checkpointer.py"
Cohesion: 0.06
Nodes (64): _load_messages(), _message_content(), _message_role(), Any, _ui_messages(), 1. End-to-End Turn Execution, 5. API Layer and Service Boundaries, 7. PostgreSQL, Repositories, and Checkpoints (+56 more)

### Community 22 - "Repositories"
Cohesion: 0.21
Nodes (36): _armory(), checkpoint_tree(), create_agent(), delete_agent(), get_agent(), get_agent_analytics(), get_agent_mcp(), get_agent_memory() (+28 more)

### Community 23 - "agentnode.py"
Cohesion: 0.10
Nodes (35): BaseMessage, langchain_core_messages, src_agent_nodes, agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation() (+27 more)

### Community 24 - "ChatService"
Cohesion: 0.13
Nodes (20): `GET /v1/chats/{chat_id}` (auth), ChatCreateRequest, ChatDetailOut, ChatOut, ChatUpdateRequest, ExtractionDecisionRequest, PolicyUpdateRequest, BaseModel (+12 more)

### Community 25 - "MemoryService"
Cohesion: 0.21
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "CurrentUser"
Cohesion: 0.12
Nodes (18): CurrentUser, McpCreateRequest, McpUpdateRequest, model_validator, available_mcp_tools(), call_mcp_tool(), McpTool, connection_log() (+10 more)

### Community 27 - "emit"
Cohesion: 0.17
Nodes (25): trace_requests(), os, work(), bind(), bind_from_config(), emit(), _error(), _persist() (+17 more)

### Community 28 - "agent_core.py"
Cohesion: 0.21
Nodes (10): concurrent_futures, Agent lifecycle facade and compatibility exports., Policy, Core agent dataclasses shared across runtime components., Process-local child execution orchestration for AgentCore., default_policy(), intersect_policy(), Policy defaults and intersection helpers. (+2 more)

### Community 29 - "run_turn_interactive"
Cohesion: 0.07
Nodes (30): ChildEventCallback, contextvars, Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_child_callback(), reset_subagent_callback(), set_child_callback(), set_subagent_callback() (+22 more)

### Community 30 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "tools/__init__.py"
Cohesion: 0.22
Nodes (8): langchain_core_tools, platform, Internal tools package for the agent., Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 32 - "armory.py"
Cohesion: 0.32
Nodes (15): connect_mcp(), create_mcp(), disconnect_mcp(), get_armory(), get_mcp(), import_mcp(), list_mcp(), list_subagents() (+7 more)

### Community 33 - "extract_chunks.py"
Cohesion: 0.27
Nodes (10): 9. Learning Agent Detailed Flow and Diagnostics, Full learner sequence, Step 2: extract reusable advice, datetime, extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any (+2 more)

### Community 34 - "context_selector_node"
Cohesion: 0.39
Nodes (3): context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "load_session.py"
Cohesion: 0.17
Nodes (20): PreferencesRepository, logging, src_agent, effective_memory_policy(), Standalone learner LangGraph: load_session → extract_chunks → persist., _latest_human(), load_session_node(), _message_line() (+12 more)

### Community 36 - "._write_and_read"
Cohesion: 0.14
Nodes (9): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall (+1 more)

### Community 37 - "embeddings.py"
Cohesion: 0.18
Nodes (14): Learning-agent diagnostic table, hashlib, numpy, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy… (+6 more)

### Community 38 - "execute"
Cohesion: 0.15
Nodes (16): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), McpRepository, _load() (+8 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.07
Nodes (29): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Authentication (+21 more)

### Community 40 - "BackgroundIdleWatcher"
Cohesion: 0.13
Nodes (10): Experience API view, Idle scheduling and branch handling, Learner graph, Learning Agent and Experience System, Step 1: load trajectory, Step 3: persist and index, BackgroundIdleWatcher, IdleWatcher (+2 more)

### Community 41 - "CheckpointService"
Cohesion: 0.32
Nodes (6): CheckpointOut, CheckpointTreeOut, RollbackRequest, get_runtime_manager(), CheckpointService, Service function map

### Community 42 - ".run_turn"
Cohesion: 0.11
Nodes (12): AgentRuntime, on_child_event(), on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate() (+4 more)

### Community 43 - "Settings"
Cohesion: 0.33
Nodes (4): get_settings(), BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 45 - "FastAPI"
Cohesion: 0.17
Nodes (13): alias, Any, Depends, get, Query, summary(), AnalyticsService, Any (+5 more)

### Community 46 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 47 - "re"
Cohesion: 0.27
Nodes (4): re, requests, GitHubRepoDownloader, main()

### Community 48 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 49 - "control.py"
Cohesion: 0.11
Nodes (20): Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, Topology, langgraph_types, clear_pause(), is_pause_requested() (+12 more)

### Community 50 - "executor.py"
Cohesion: 0.17
Nodes (11): BashArgs, _check_blacklist(), _find_executable(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs, Internal tools for executing Bash commands, PowerShell commands, and Python… (+3 more)

### Community 51 - "log_event"
Cohesion: 0.14
Nodes (30): _record_tool_result(), bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_context_select(), log_error(), log_event() (+22 more)

### Community 52 - "paths.py"
Cohesion: 0.73
Nodes (5): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 57 - "tools_service.py"
Cohesion: 0.42
Nodes (7): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info(), ToolsService

### Community 60 - "agentnode_prompt_loader"
Cohesion: 0.15
Nodes (12): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, Add a planner-callable sub-agent, Add a prompt block, Add an API resource, Add an internal tool, Practical prompt-debug method, System versus user prompt (+4 more)

### Community 61 - "test_prompt_render.py"
Cohesion: 0.19
Nodes (6): _eval_cond(), _present(), Tests for the declarative prompt renderer in prompt_loader.py., The prototype returned True here, so `if=turn_start` always fired and the model…, TestConditions, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.22
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "agent/kb.py"
Cohesion: 0.05
Nodes (101): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+93 more)

### Community 64 - "test_subagents_integration.py"
Cohesion: 0.08
Nodes (27): Any, SubagentsService, Sub-agents: `subagent_node` and gate, note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, RunnableConfig, Sub-agent node — delegates a focused task to a configured armory sub-agent.…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by… (+19 more)

### Community 65 - "test_db_setup.py"
Cohesion: 0.22
Nodes (5): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, TestDbSetupLive

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "tool_node"
Cohesion: 0.08
Nodes (21): build_execution_memory_index(), count_content_tokens(), empty_context_memory(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts. (+13 more)

### Community 69 - "llm_logger.py"
Cohesion: 0.09
Nodes (33): atexit, queue, _ensure_writer_started(), _safe_agent_id(), _writer_loop(), build_record(), current_session_ids(), _db_loop() (+25 more)

### Community 70 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 71 - "Tools: `tool_node`"
Cohesion: 0.30
Nodes (12): Command execution tools, Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), Any, tool, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+4 more)

### Community 72 - "mcp_runtime.py"
Cohesion: 0.25
Nodes (7): Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, dataclasses, httpx, mcp, mcp_client_sse, mcp_client_stdio, mcp_client_streamable_http

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.13
Nodes (13): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+5 more)

### Community 75 - "idle_watcher.py"
Cohesion: 0.18
Nodes (11): asyncio, _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+3 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "context_manager.py"
Cohesion: 0.39
Nodes (7): _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Check how much of a model's input context window the prompt consumes. Returns…, Check how much of a model's output context window a response consumes. Returns…

### Community 89 - "repl.py"
Cohesion: 0.12
Nodes (31): prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, PromptSession, rich_prompt, rich_table, _choose() (+23 more)

### Community 90 - "fetch_all"
Cohesion: 0.29
Nodes (6): fetch_all(), Any, _iso(), Any, _row_to_entry(), Durable user-memory tools

### Community 91 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 92 - "renderer.py"
Cohesion: 0.18
Nodes (9): io, rich_console, rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, CLI theme - one place for every terminal color/style used by the CLI. Keys are… (+1 more)

### Community 94 - "policy_schema.py"
Cohesion: 0.22
Nodes (16): Durable AgentCore identities, run reservations, and child results., copy, psycopg_types_json, Agent policy facets: memory, armory, guardrails and observability., armory_resource_allowed(), _as_string_list(), _bool(), _canonical_resource() (+8 more)

### Community 96 - "input_security_gate_node"
Cohesion: 0.53
Nodes (5): _as_dict(), _coerce_int(), _deny(), input_security_gate_node(), Input security gate for executor-bound planner actions.

### Community 97 - "src/config.py"
Cohesion: 0.40
Nodes (4): dotenv, functools, pydantic_settings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…

### Community 98 - "AgentRepository"
Cohesion: 0.10
Nodes (5): AgentRepository, Any, ChildRunner, Bounded, process-local execution of durable child runs., Before a parent finishes, collect all its children by persisted lineage.

### Community 99 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, model_validator, ReadFileArgs, SearchFileArgs

### Community 101 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 102 - "test_phased_plan.py"
Cohesion: 0.09
Nodes (37): dispatch_phase(), phase_collector_node(), plan_dispatcher_node(), _escape_unescaped_quotes_in_json_strings(), parse_plan(), Plan, PlanPhase, PlanStep (+29 more)

### Community 104 - "file_io.py"
Cohesion: 0.21
Nodes (15): 4. Internal Tool Subsystem, File tools, Information and planning tools, edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management. (+7 more)

### Community 105 - "McpRuntime"
Cohesion: 0.12
Nodes (6): McpConnection, McpRuntime, Any, BaseException, test_http_404_is_reported_as_endpoint_error(), test_http_transport_connects_to_real_streamable_server()

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.12
Nodes (15): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+7 more)

### Community 111 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 112 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 113 - "fetch_one"
Cohesion: 0.22
Nodes (6): fetch_one(), AuthSessionRepository, _iso(), Any, MemoryExtractionRepository, Any

### Community 117 - "security.py"
Cohesion: 0.15
Nodes (18): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+10 more)

### Community 121 - "test_experience_system.py"
Cohesion: 0.12
Nodes (13): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, _is_run_active(), Expose synchronous CLI turns to the background idle watcher., set_chat_active(), build_embed_text(), Build retrieval / embed keys shared by learner and main agent. (+5 more)

### Community 122 - "truncate_value"
Cohesion: 0.18
Nodes (8): Agent trace logger, Path, Recursively truncate oversized strings in payloads., Append-only JSONL writer for one agent., SessionLogger, truncate_value(), _utc_now(), TestTruncate

### Community 126 - "decompose_query"
Cohesion: 0.50
Nodes (4): decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

### Community 127 - "endpoint.py"
Cohesion: 0.18
Nodes (13): Validate JWT for WebSocket handshake., user_from_token(), agent_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject() (+5 more)

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 554 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `test_cli_repl.py`, `make_console`, `repl.py`, `renderer.py`, `run_turn_interactive`?**
  _High betweenness centrality (0.084) - this node is a cross-community bridge._
- **Why does `AgentCore` connect `AgentCore` to `AgentRepository`, `load_session.py`, `Armory`, `Message`, `ChatRuntimeManager`, `MemoryRepository`, `retrieve_experiences`, `agent_runtime.py`, `postgres_checkpointer.py`, `ChatService`, `repl.py`, `agent_core.py`, `run_turn_interactive`, `policy_schema.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `ChatPacketQueue`, `EVA Agent API — Reference & How to Use`, `Platform Agent Codebase Documentation`, `AgentCore`, `.run_turn`, `CheckpointService`, `agent_runtime.py`, `postgres_checkpointer.py`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 64 inferred relationships involving `CurrentUser` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`CurrentUser` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Repositories` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`Repositories` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._