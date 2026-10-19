# Graph Report - backend  (2026-10-09)

## Corpus Check
- 216 files · ~176,312 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 13 file(s) not represented in the graph (top: .jsonl 6, .bin 4, .example 1)

## Summary
- 2165 nodes · 6012 edges · 123 communities (102 shown, 21 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 506 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- api_routes/preferences.py
- test_llm_mock_mode.py
- api_routes/kb.py
- typing
- TurnRenderer
- EVA Agent API — Reference & How to Use
- test_kb.py
- llm_client.py
- TestAgentNodePrompt
- Policy
- db_utils.py
- agentnode.py
- test_experience_system.py
- prompt_loader.py
- update_context_memory
- pathlib
- test_llm_logger.py
- mcp_runtime.py
- api_routes/auth.py
- AgentCore
- TestSubagentNode
- .run_turn
- require_user
- make_console
- chat_service.py
- api_routes/memory.py
- McpService
- emit
- test_endpoints.py
- run_turn_interactive
- fetch_all
- tools/__init__.py
- web_search.py
- CheckpointService
- context_selector_node
- load_session.py
- ._write_and_read
- embeddings.py
- repositories/__init__.py
- Platform Agent Codebase Documentation
- HfLoadIsQuiet
- log_event
- ChatPacketQueue
- src/config.py
- BackgroundIdleWatcher
- main.py
- AgentRepository
- MemoryRepository
- agentnode_prompt_loader
- write
- field_validator
- bind_session_logger
- paths.py
- Multi-User Agentic AI Platform — Database Design
- test_agentnode_fast_planner_handoff.py
- graphify.js
- render
- tools_service.py
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- CurrentUser
- _present
- route_from_agent
- agent/kb.py
- test_subagents_integration.py
- test_db_setup.py
- ws.py
- test_context_memory.py
- ._commit
- llm_logger.py
- build_cache_key
- executor.py
- human_input_node
- test_prompt_templates.py
- AGENTS.md
- idle_watcher.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- plan.py
- repl.py
- in_run
- test_prompt_render.py
- postgres_checkpointer.py
- agent_core.py
- extract_chunks.py
- app.py
- fetch_one
- pydantic
- .finish
- health.py
- test_phased_plan.py
- GitHubRepoDownloader
- edit_file
- McpRuntime
- TestAgentRuntimeFanout
- ChatRuntimeManager
- _session_prompt
- postgres.py
- json_store.py
- json
- AuthSessionRepository
- TestMainDispatch
- parse_command
- generate_tree
- users.py
- _eval_cond
- src_subagents_learner_agent_store
- learn_session
- truncate_value
- agent/graph.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 119 edges
2. `require_user()` - 72 edges
3. `Repositories` - 69 edges
4. `TurnRenderer` - 59 edges
5. `get_repos()` - 56 edges
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
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py

## Import Cycles
- None detected.

## Communities (123 total, 21 thin omitted)

### Community 0 - "api_routes/preferences.py"
Cohesion: 0.25
Nodes (9): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, PreferencesService (+1 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.09
Nodes (28): Gateway behavior, LLM Client, Observability, and Replay, Logging and mock replay, src_models, call_llm(), call_llm_stream(), _Chunk, _Completion (+20 more)

### Community 2 - "api_routes/kb.py"
Cohesion: 0.20
Nodes (29): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+21 more)

### Community 3 - "typing"
Cohesion: 0.11
Nodes (19): Any, Depends, get, summary(), Authorized view of active learned experiences., list_subagents(), Any, Depends (+11 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.14
Nodes (10): io, rich_console, Console, Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., TurnRenderer, make_console(), Console (+2 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.08
Nodes (24): Analytics, Authentication, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), EVA Agent API — Reference & How to Use, Example messages (+16 more)

### Community 6 - "test_kb.py"
Cohesion: 0.11
Nodes (19): fixture, search(), update(), Collection, Conn, Cursor, Memory authorization, post-index revalidation, and governance gates., Use rollback-only database writes and an ephemeral in-memory Chroma index. (+11 more)

### Community 7 - "llm_client.py"
Cohesion: 0.07
Nodes (44): collections, OpenAI, emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages(), _build_provider() (+36 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "Policy"
Cohesion: 0.29
Nodes (5): ChildHandle, Policy, intersect_policy(), A child cannot grant capabilities, scopes or a tenant its parent lacks., test_policy_intersection_and_memory_identity()

### Community 10 - "db_utils.py"
Cohesion: 0.17
Nodes (14): contextlib, psycopg, psycopg_pool, psycopg_rows, execute(), fetch_all(), fetch_one(), get_connection() (+6 more)

### Community 11 - "agentnode.py"
Cohesion: 0.08
Nodes (29): BaseMessage, 1. End-to-End Turn Execution, Functions to start with when tracing a turn, Main agent loop, note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, agent_node(), _on_token() (+21 more)

### Community 12 - "test_experience_system.py"
Cohesion: 0.11
Nodes (18): Retrieval in the main agent, src_agent, Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval. (+10 more)

### Community 13 - "prompt_loader.py"
Cohesion: 0.24
Nodes (12): Major prompt functions, _armory_text(), fast_agent_prompt_loader(), _load_module(), _Node, _parse(), planner_agent_prompt_loader(), Prompt rendering and loading for every agent and sub-agent in the project. One… (+4 more)

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "pathlib"
Cohesion: 0.10
Nodes (17): pathlib, scripts, src_agent_nodes, sys, Unit tests for the CLI REPL: command parsing, step handling, interrupts, and…, object, Focused checks for CLI-configurable agent runtime controls., TestRuntimeControls (+9 more)

### Community 16 - "test_llm_logger.py"
Cohesion: 0.18
Nodes (9): src_utils, current_session_ids(), lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, Agent identity from the ContextVar-bound logger. Falls back to…, tempfile, Tests for the LLM call recorder and its mock-replay cache key. No live Postgres…, TestLookupSoftFails (+1 more)

### Community 17 - "mcp_runtime.py"
Cohesion: 0.10
Nodes (24): get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., ensure_client_path(), get_agent_app() (+16 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.23
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "AgentCore"
Cohesion: 0.13
Nodes (6): AgentCore, AgentID, Message, Armory, Guardrails, Observability

### Community 20 - "TestSubagentNode"
Cohesion: 0.20
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - ".run_turn"
Cohesion: 0.32
Nodes (5): on_child_event(), on_subagent_event(), Any, _truncate(), Event

### Community 22 - "require_user"
Cohesion: 0.18
Nodes (36): create_chat(), delete_chat(), get_chat(), get_policy(), list_chats(), list_memory_extraction_requests(), delete, Depends (+28 more)

### Community 23 - "make_console"
Cohesion: 0.16
Nodes (12): handle_step(), _latest_answer(), prompt_for_interrupt(), interrupt_step(), make_console(), Console, patch, TestHandleStep (+4 more)

### Community 24 - "chat_service.py"
Cohesion: 0.12
Nodes (23): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `GET /v1/chats/{chat_id}` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth), ChatDetailOut, ChatOut (+15 more)

### Community 25 - "api_routes/memory.py"
Cohesion: 0.22
Nodes (14): add_memory(), get_memory(), put_memory(), Depends, get, post, put, MemoryAddRequest (+6 more)

### Community 26 - "McpService"
Cohesion: 0.11
Nodes (14): McpCreateRequest, McpUpdateRequest, model_validator, connection_log(), McpService, public_server(), Any, mcp_server_fastmcp (+6 more)

### Community 27 - "emit"
Cohesion: 0.18
Nodes (25): create_app(), trace_requests(), work(), bind(), bind_from_config(), emit(), _error(), _persist() (+17 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "run_turn_interactive"
Cohesion: 0.09
Nodes (24): ChildEventCallback, reset_child_callback(), set_child_callback(), emit_token(), Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_token_callback(), reset_usage_callback() (+16 more)

### Community 30 - "fetch_all"
Cohesion: 0.33
Nodes (7): fetch_all(), _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "tools/__init__.py"
Cohesion: 0.15
Nodes (14): Information and planning tools, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…, Internal tools package for the agent., get_current_datetime_info(), Any (+6 more)

### Community 32 - "web_search.py"
Cohesion: 0.17
Nodes (14): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, BaseModel, field_validator (+6 more)

### Community 33 - "CheckpointService"
Cohesion: 0.18
Nodes (18): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), ChatCreateRequest, ChatUpdateRequest (+10 more)

### Community 34 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "load_session.py"
Cohesion: 0.20
Nodes (18): PreferencesRepository, logging, effective_memory_policy(), Standalone learner LangGraph: load_session → extract_chunks → persist., _latest_human(), load_session_node(), _message_line(), Any (+10 more)

### Community 36 - "._write_and_read"
Cohesion: 0.19
Nodes (6): build_record(), _utc_now(), Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 37 - "embeddings.py"
Cohesion: 0.12
Nodes (17): hashlib, list, numpy, _vector(), _embed_numpy(), embed_text(), embed_texts(), _get_hf_model() (+9 more)

### Community 38 - "repositories/__init__.py"
Cohesion: 0.15
Nodes (17): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), McpRepository, _load() (+9 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.09
Nodes (23): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Current Extension Points and Limits (+15 more)

### Community 40 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 41 - "log_event"
Cohesion: 0.28
Nodes (18): log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response(), log_route(), log_run_end() (+10 more)

### Community 42 - "ChatPacketQueue"
Cohesion: 0.09
Nodes (15): AgentRuntime, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback). (+7 more)

### Community 43 - "src/config.py"
Cohesion: 0.20
Nodes (8): dotenv, functools, pydantic_settings, get_settings(), BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 44 - "BackgroundIdleWatcher"
Cohesion: 0.11
Nodes (13): CLI, Commands, Experience API view, Flow, Idle scheduling and branch handling, Learner graph, Learning Agent and Experience System, Step 1: load trajectory (+5 more)

### Community 45 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 46 - "AgentRepository"
Cohesion: 0.11
Nodes (4): AgentRepository, ChildRunner, Bounded, process-local execution of durable child runs., Before a parent finishes, collect all its children by persisted lineage.

### Community 47 - "MemoryRepository"
Cohesion: 0.18
Nodes (6): _iso(), MemoryRepository, Any, _row_to_entry(), Durable user-memory tools, Memory

### Community 48 - "agentnode_prompt_loader"
Cohesion: 0.14
Nodes (14): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, 5. API Layer and Service Boundaries, Add a planner-callable sub-agent, Add a prompt block, Add an API resource, Add an internal tool, Detailed Subsystem Reference (+6 more)

### Community 49 - "write"
Cohesion: 0.34
Nodes (14): _active_for_uid(), _authorized(), _deny(), get_chunk(), history(), import_legacy(), list_chunks(), _public() (+6 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "bind_session_logger"
Cohesion: 0.18
Nodes (10): bind_session_logger(), flush_pending_logs(), get_session_logger(), Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger(), A slow/stalled write to one chat's file must not delay log() calls for the SAME…, TestAsyncWriterDoesNotBlockCaller (+2 more)

### Community 52 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "test_agentnode_fast_planner_handoff.py"
Cohesion: 0.64
Nodes (7): _config(), object, _state(), test_fast_plan_handoff_accepts_planner_finish_without_steps_json(), test_fast_plan_handoff_missing_steps_after_retry_surfaces_clear_error(), test_fast_plan_handoff_retries_once_then_parses_plan(), test_plan_parse_failure_retries_once_then_returns_graceful_message()

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 57 - "tools_service.py"
Cohesion: 0.25
Nodes (11): list_tools(), Any, Depends, get, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict() (+3 more)

### Community 60 - "CurrentUser"
Cohesion: 0.25
Nodes (9): get_experience(), list_experiences(), Depends, get, CurrentUser, PolicyUpdateRequest, ChatService, Policy endpoints use the saved AgentCore and require chat ownership. (+1 more)

### Community 61 - "_present"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.22
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "agent/kb.py"
Cohesion: 0.14
Nodes (37): get_connection(), Connection, math, _audit(), audit_log(), cancel_promotion(), _chroma_available(), _collection() (+29 more)

### Community 64 - "test_subagents_integration.py"
Cohesion: 0.07
Nodes (30): Any, SubagentsService, Sub-agents: `subagent_node` and gate, contextvars, RunnableConfig, Sub-agent node — delegates a focused task to a configured armory sub-agent.…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node() (+22 more)

### Community 65 - "test_db_setup.py"
Cohesion: 0.13
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "test_context_memory.py"
Cohesion: 0.11
Nodes (17): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+9 more)

### Community 68 - "._commit"
Cohesion: 0.18
Nodes (6): emit_tag(), _format_args(), Any, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short()

### Community 69 - "llm_logger.py"
Cohesion: 0.11
Nodes (25): atexit, queue, register, _ensure_writer_started(), Path, _safe_agent_id(), _writer_loop(), _db_loop() (+17 more)

### Community 70 - "build_cache_key"
Cohesion: 0.21
Nodes (8): 8. Observability, Logs, and LLM Replay, Agent trace logger, LLM call logger and replay cache, Recommended debugging workflow, build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 71 - "executor.py"
Cohesion: 0.22
Nodes (15): Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python… (+7 more)

### Community 72 - "human_input_node"
Cohesion: 0.25
Nodes (8): Agent runtime event conversion, Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, Topology, human_input_node(), TestHumanInputNode

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.13
Nodes (14): re, load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables. (+6 more)

### Community 75 - "idle_watcher.py"
Cohesion: 0.16
Nodes (13): _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+5 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "plan.py"
Cohesion: 0.32
Nodes (6): Plan, PlanPhase, PlanStep, BaseModel, model_validator, Validated, checkpoint-friendly phased plans.

### Community 89 - "repl.py"
Cohesion: 0.12
Nodes (32): api_db_repositories, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_markdown, rich_panel, rich_prompt (+24 more)

### Community 90 - "in_run"
Cohesion: 0.12
Nodes (24): available_mcp_tools(), call_mcp_tool(), McpTool, langchain_core_runnables, clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused (+16 more)

### Community 91 - "test_prompt_render.py"
Cohesion: 0.20
Nodes (11): _fmt(), PromptRenderError, Any, Exception, Serialize structured prompt context as TOON., Raised in strict mode when a template references an unknown variable., replace(), to_toon() (+3 more)

### Community 92 - "postgres_checkpointer.py"
Cohesion: 0.08
Nodes (49): 7. PostgreSQL, Repositories, and Checkpoints, Checkpointer function map, Database troubleshooting, PostgreSQL responsibilities, langgraph_checkpoint_postgres, active_checkpoint_path(), build_config(), _ensure_branch_learn_table() (+41 more)

### Community 94 - "agent_core.py"
Cohesion: 0.17
Nodes (20): Durable AgentCore identities, run reservations, and child results., concurrent_futures, copy, Agent lifecycle facade and compatibility exports., Core agent dataclasses shared across runtime components., Process-local child execution orchestration for AgentCore., Agent policy facets: memory, armory, guardrails and observability., default_policy() (+12 more)

### Community 96 - "extract_chunks.py"
Cohesion: 0.24
Nodes (11): 9. Learning Agent Detailed Flow and Diagnostics, Full learner sequence, Learning-agent diagnostic table, Step 2: extract reusable advice, datetime, extract_chunks_node(), _normalize_chunk(), _parse_json_payload() (+3 more)

### Community 97 - "app.py"
Cohesion: 0.20
Nodes (11): api_api_routes, api_ws, agent_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject() (+3 more)

### Community 98 - "fetch_one"
Cohesion: 0.23
Nodes (5): fetch_one(), Any, Any, MemoryExtractionRepository, Any

### Community 99 - "pydantic"
Cohesion: 0.21
Nodes (8): pydantic, EditFileArgs, BaseModel, field_validator, model_validator, Internal tools for file I/O operations, file search, and directory management., ReadFileArgs, SearchFileArgs

### Community 100 - ".finish"
Cohesion: 0.18
Nodes (3): Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., Restart the live region after an interrupt prompt.

### Community 101 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 102 - "test_phased_plan.py"
Cohesion: 0.13
Nodes (29): dispatch_phase(), phase_collector_node(), plan_dispatcher_node(), Fan out independent phase steps; commit their results once in plan order., parse_plan(), Reject the entire plan if any step is invalid or exceeds the runtime limit., A plan must be safe to dispatch and parallel phases must merge once., step() (+21 more)

### Community 103 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

### Community 104 - "edit_file"
Cohesion: 0.22
Nodes (14): 4. Internal Tool Subsystem, Command execution tools, File tools, edit_file(), Any, Path, tool, Read content from a text-based file. Supports optional line-range slicing via… (+6 more)

### Community 105 - "McpRuntime"
Cohesion: 0.12
Nodes (6): McpConnection, McpRuntime, Any, BaseException, test_http_404_is_reported_as_endpoint_error(), test_http_transport_connects_to_real_streamable_server()

### Community 106 - "TestAgentRuntimeFanout"
Cohesion: 0.33
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.11
Nodes (18): Envelope (all messages), utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target() (+10 more)

### Community 108 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 109 - "postgres.py"
Cohesion: 0.40
Nodes (3): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…

### Community 111 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 112 - "json"
Cohesion: 0.12
Nodes (15): calendar, json, langchain_core_tools, os, platform, DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional… (+7 more)

### Community 113 - "AuthSessionRepository"
Cohesion: 0.46
Nodes (3): AuthSessionRepository, _iso(), Any

### Community 116 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 117 - "users.py"
Cohesion: 0.20
Nodes (14): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+6 more)

### Community 121 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 122 - "truncate_value"
Cohesion: 0.24
Nodes (6): Recursively truncate oversized strings in payloads., Append-only JSONL writer for one agent., SessionLogger, truncate_value(), _utc_now(), TestTruncate

### Community 127 - "agent/graph.py"
Cohesion: 0.08
Nodes (36): State, langchain_core_messages, langgraph_graph, langgraph_graph_message, langgraph_types, Conditional edge out of input_security_gate. Reuses the same…, route_from_input_gate(), Agent graph definition. (+28 more)

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 556 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `.finish`, `._commit`, `pathlib`, `make_console`, `repl.py`, `run_turn_interactive`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `AgentCore` connect `AgentCore` to `load_session.py`, `Policy`, `ChatRuntimeManager`, `test_experience_system.py`, `AgentRepository`, `MemoryRepository`, `mcp_runtime.py`, `chat_service.py`, `repl.py`, `CurrentUser`, `run_turn_interactive`, `agent_core.py`, `agent/graph.py`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `CheckpointService`, `EVA Agent API — Reference & How to Use`, `Platform Agent Codebase Documentation`, `ChatPacketQueue`, `mcp_runtime.py`, `AgentCore`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 57 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 57 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._