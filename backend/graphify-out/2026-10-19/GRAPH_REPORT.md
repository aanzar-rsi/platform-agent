# Graph Report - backend  (2026-10-15)

## Corpus Check
- 229 files · ~363,214 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 27 file(s) not represented in the graph (top: .jsonl 20, .bin 4, .example 1)

## Summary
- 2204 nodes · 6193 edges · 129 communities (101 shown, 28 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 534 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Repositories
- test_llm_mock_mode.py
- ChatPacketQueue
- fetch_all
- TurnRenderer
- EVA Agent API — Reference & How to Use
- text_truncate.py
- llm_client.py
- TestAgentNodePrompt
- test_kb.py
- postgres.py
- agentnode.py
- in_run
- prompt_loader.py
- update_context_memory
- agent/graph.py
- lookup_cached_response
- agent_runtime.py
- api_routes/auth.py
- api_routes/kb.py
- TestSubagentNode
- postgres_checkpointer.py
- require_user
- plan_dispatcher.py
- ChatService
- MemoryService
- CurrentUser
- emit
- test_llm_logger.py
- run_turn_interactive
- SessionRepository
- tools/__init__.py
- bind_session_logger
- extract_chunks.py
- context_selector_node
- load_session.py
- ._write_and_read
- embed_text
- fetch_one
- Platform Agent Codebase Documentation
- BackgroundIdleWatcher
- llm_logger.py
- .run_turn
- src/config.py
- TestRuntimeControls
- deps.py
- WebSearchArgs
- HfLoadIsQuiet
- web_search.py
- control.py
- field_validator
- log_event
- paths.py
- Multi-User Agentic AI Platform — Database Design
- api_routes/files.py
- graphify.js
- render
- available_mcp_tools
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- agentnode_prompt_loader
- test_prompt_render.py
- route_from_agent
- agent/kb.py
- subagent_node
- test_db_setup.py
- ws.py
- test_context_memory.py
- token_stream.py
- record_llm_call
- sync_index
- executor.py
- test_agentnode_fast_planner_handoff.py
- test_prompt_templates.py
- AGENTS.md
- test_experience_system.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- _fmt
- repl.py
- MemoryExtractionRepository
- main.py
- renderer.py
- AgentCore
- .attach
- subagent_stream.py
- get_connection
- ReadFileArgs
- _FakeEncoded
- health.py
- test_phased_plan.py
- import_memory_kb.py
- file_io.py
- McpRuntime
- TestAgentRuntimeFanout
- ChatRuntimeManager
- WebSocket chat session
- TestSchemaStatementsAreIdempotent
- json_store.py
- datetime
- typing
- ._begin_reserved_run
- generate_tree
- TestMainDispatch
- security.py
- TestSubagentRegistry
- _session_prompt
- src_subagents_learner_agent_store
- learn_session
- truncate_value
- TestTheme
- TestCreateUser
- parse_command
- decompose_query
- 6. WebSocket Runtime, Queues, and Recovery
- set_chat_active

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

## Communities (129 total, 28 thin omitted)

### Community 0 - "Repositories"
Cohesion: 0.11
Nodes (13): get_prefs(), put_prefs(), Any, Depends, get, put, Repositories, PreferencesUpdateRequest (+5 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.09
Nodes (27): Gateway behavior, LLM call logger and replay cache, src_models, call_llm(), call_llm_stream(), _Chunk, _Completion, fake_gateway() (+19 more)

### Community 2 - "ChatPacketQueue"
Cohesion: 0.18
Nodes (7): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior

### Community 3 - "fetch_all"
Cohesion: 0.27
Nodes (5): fetch_all(), AnalyticsRepository, Any, _TimeWindow, test_summary_can_filter_one_agent()

### Community 4 - "TurnRenderer"
Cohesion: 0.05
Nodes (28): emit_tag(), _format_args(), Any, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning. (+20 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.11
Nodes (18): Analytics, Authentication, Checkpoints & rollback, Data store (`data/`), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth), `GET /v1/auth/me` (auth), `GET /v1/chats/{chat_id}/checkpoints` (auth) (+10 more)

### Community 6 - "text_truncate.py"
Cohesion: 0.43
Nodes (6): _record_tool_result(), Any, Shared stringify + truncate helpers for AIMessage previews., stringify_for_preview(), truncate_for_aimessage(), truncate_text()

### Community 7 - "llm_client.py"
Cohesion: 0.06
Nodes (50): collections, OpenAI, emit_cache_hit(), emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages() (+42 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "test_kb.py"
Cohesion: 0.10
Nodes (21): fixture, pytest, search(), update(), Collection, Conn, Cursor, Memory authorization, post-index revalidation, and governance gates. (+13 more)

### Community 10 - "postgres.py"
Cohesion: 0.13
Nodes (17): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute() (+9 more)

### Community 11 - "agentnode.py"
Cohesion: 0.08
Nodes (28): BaseMessage, agent_node(), _on_token(), run_planner_call(), _extract_tag(), _format_conversation(), _is_turn_start(), _latest_human_content() (+20 more)

### Community 12 - "in_run"
Cohesion: 0.17
Nodes (14): PreferencesRepository, Retrieval in the main agent, Standalone learner agent: extract experience chunks from idle chats., _mark_request(), persist_node(), Persist extracted chunks into the experience store., format_experiences_for_prompt(), Any (+6 more)

### Community 13 - "prompt_loader.py"
Cohesion: 0.18
Nodes (16): Major prompt functions, _armory_text(), fast_agent_prompt_loader(), _load_module(), _Node, _parse(), planner_agent_prompt_loader(), PromptRenderError (+8 more)

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "agent/graph.py"
Cohesion: 0.07
Nodes (41): State, io, langchain_core_messages, langchain_core_runnables, langgraph_graph, langgraph_graph_message, pathlib, pydantic (+33 more)

### Community 16 - "lookup_cached_response"
Cohesion: 0.47
Nodes (3): lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, TestLookupSoftFails

### Community 17 - "agent_runtime.py"
Cohesion: 0.13
Nodes (22): get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., ensure_client_path(), get_agent_app() (+14 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "api_routes/kb.py"
Cohesion: 0.20
Nodes (29): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+21 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.20
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - "postgres_checkpointer.py"
Cohesion: 0.06
Nodes (55): 1. End-to-End Turn Execution, 5. API Layer and Service Boundaries, 7. PostgreSQL, Repositories, and Checkpoints, 8. Observability, Logs, and LLM Replay, Checkpointer function map, Database troubleshooting, Detailed Subsystem Reference, Functions to start with when tracing a turn (+47 more)

### Community 22 - "require_user"
Cohesion: 0.18
Nodes (34): _armory(), checkpoint_tree(), create_agent(), delete_agent(), get_agent(), get_agent_analytics(), get_agent_mcp(), get_agent_memory() (+26 more)

### Community 23 - "plan_dispatcher.py"
Cohesion: 0.13
Nodes (20): langgraph_types, _coerce_int(), _map_plan_step_to_next_step(), child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy(), _root_owner(), collect_child_node() (+12 more)

### Community 24 - "ChatService"
Cohesion: 0.09
Nodes (37): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `GET /v1/chats/{chat_id}` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth), _services(), ChatCreateRequest (+29 more)

### Community 25 - "MemoryService"
Cohesion: 0.22
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "CurrentUser"
Cohesion: 0.16
Nodes (30): connect_mcp(), create_mcp(), delete_mcp(), disconnect_mcp(), get_armory(), get_mcp(), import_mcp(), list_mcp() (+22 more)

### Community 27 - "emit"
Cohesion: 0.06
Nodes (52): api_api_routes, create_app(), trace_requests(), _iso(), MemoryRepository, Any, _row_to_entry(), api_ws (+44 more)

### Community 28 - "test_llm_logger.py"
Cohesion: 0.13
Nodes (15): json, os, DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional…, src_utils, build_record(), current_session_ids() (+7 more)

### Community 29 - "run_turn_interactive"
Cohesion: 0.11
Nodes (16): ChildEventCallback, reset_child_callback(), set_child_callback(), reset_token_callback(), run_turn_interactive(), FakeAgents, parent_core(), AgentCore policy and independent-child behavior without a live database. (+8 more)

### Community 30 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "tools/__init__.py"
Cohesion: 0.22
Nodes (8): langchain_core_tools, platform, Internal tools package for the agent., Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 32 - "bind_session_logger"
Cohesion: 0.18
Nodes (10): bind_session_logger(), flush_pending_logs(), get_session_logger(), Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger(), A slow/stalled write to one chat's file must not delay log() calls for the SAME…, TestAsyncWriterDoesNotBlockCaller (+2 more)

### Community 33 - "extract_chunks.py"
Cohesion: 0.21
Nodes (11): Full learner sequence, build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any (+3 more)

### Community 34 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "load_session.py"
Cohesion: 0.25
Nodes (11): Standalone learner LangGraph: load_session → extract_chunks → persist., _latest_human(), load_session_node(), _message_line(), Any, Load chat trajectory from the main agent checkpointer., _slim_history(), LearnerState (+3 more)

### Community 36 - "._write_and_read"
Cohesion: 0.18
Nodes (7): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall

### Community 37 - "embed_text"
Cohesion: 0.17
Nodes (13): 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, Step 2: extract reusable advice, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Deterministic hashing bag-of-words vectorizer (no ML dependencies). (+5 more)

### Community 38 - "fetch_one"
Cohesion: 0.16
Nodes (17): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, fetch_one(), Any, _iso(), McpRepository, _load() (+9 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.10
Nodes (19): CLI, Commands, Current Extension Points and Limits, Entrypoints, Environment, Flow, LLM Client, Observability, and Replay, Logging and mock replay (+11 more)

### Community 40 - "BackgroundIdleWatcher"
Cohesion: 0.13
Nodes (10): Experience API view, Idle scheduling and branch handling, Learner graph, Learning Agent and Experience System, Step 1: load trajectory, Step 3: persist and index, BackgroundIdleWatcher, IdleWatcher (+2 more)

### Community 41 - "llm_logger.py"
Cohesion: 0.21
Nodes (10): atexit, hashlib, numpy, queue, Local text embeddings: sentence-transformers model, or a dependency-free numpy…, _db_loop(), _ensure_db_writer_started(), _ensure_table() (+2 more)

### Community 42 - ".run_turn"
Cohesion: 0.12
Nodes (11): AgentRuntime, on_child_event(), on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate() (+3 more)

### Community 43 - "src/config.py"
Cohesion: 0.20
Nodes (7): dotenv, functools, pydantic_settings, BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 45 - "deps.py"
Cohesion: 0.10
Nodes (24): alias, Any, Depends, get, Query, summary(), get_experience(), list_experiences() (+16 more)

### Community 46 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 47 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 48 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 49 - "control.py"
Cohesion: 0.20
Nodes (12): clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each…, Call at the very top of a node, before any side effects. Returns the… (+4 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "log_event"
Cohesion: 0.26
Nodes (18): log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response(), log_route(), log_run_end() (+10 more)

### Community 52 - "paths.py"
Cohesion: 0.73
Nodes (5): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 57 - "available_mcp_tools"
Cohesion: 0.16
Nodes (11): available_mcp_tools(), McpTool, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info() (+3 more)

### Community 60 - "agentnode_prompt_loader"
Cohesion: 0.18
Nodes (11): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, Add a planner-callable sub-agent, Add a prompt block, Add an API resource, Add an internal tool, Practical prompt-debug method, System versus user prompt (+3 more)

### Community 61 - "test_prompt_render.py"
Cohesion: 0.19
Nodes (6): _eval_cond(), _present(), Tests for the declarative prompt renderer in prompt_loader.py., The prototype returned True here, so `if=turn_start` always fired and the model…, TestConditions, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.19
Nodes (6): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, Conditional edge out of input_security_gate. Reuses the same…, route_from_agent(), route_from_input_gate(), TestRouting, TestRouting

### Community 63 - "agent/kb.py"
Cohesion: 0.17
Nodes (37): math, _active_for_uid(), _audit(), audit_log(), _authorized(), cancel_promotion(), _conflicts(), demote() (+29 more)

### Community 64 - "subagent_node"
Cohesion: 0.15
Nodes (16): Any, Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, Sub-agents: `subagent_node` and gate, Topology, RunnableConfig (+8 more)

### Community 65 - "test_db_setup.py"
Cohesion: 0.22
Nodes (5): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, TestDbSetupLive

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "test_context_memory.py"
Cohesion: 0.09
Nodes (22): build_execution_memory_index(), count_content_tokens(), empty_context_memory(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts. (+14 more)

### Community 68 - "token_stream.py"
Cohesion: 0.18
Nodes (10): CacheHitCallback, Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_cache_hit_callback(), reset_usage_callback(), set_cache_hit_callback(), set_token_callback(), set_usage_callback() (+2 more)

### Community 69 - "record_llm_call"
Cohesion: 0.12
Nodes (17): Agent trace logger, _ensure_writer_started(), Path, Append-only JSONL writer for one agent., _safe_agent_id(), SessionLogger, _utc_now(), _writer_loop() (+9 more)

### Community 70 - "sync_index"
Cohesion: 0.24
Nodes (10): _chroma_available(), _collection(), _compatible(), _model(), Replay PostgreSQL projection tasks. A failed task stays queued for retry., Periodic reconciliation for expired versions and indexing retries., rebuild_index(), refresh_index() (+2 more)

### Community 71 - "executor.py"
Cohesion: 0.21
Nodes (16): Command execution tools, Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool (+8 more)

### Community 72 - "test_agentnode_fast_planner_handoff.py"
Cohesion: 0.53
Nodes (8): src_agent_nodes, _config(), object, _state(), test_fast_plan_handoff_accepts_planner_finish_without_steps_json(), test_fast_plan_handoff_missing_steps_after_retry_surfaces_clear_error(), test_fast_plan_handoff_retries_once_then_parses_plan(), test_plan_parse_failure_retries_once_then_returns_graceful_message()

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.13
Nodes (13): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+5 more)

### Community 75 - "test_experience_system.py"
Cohesion: 0.13
Nodes (14): _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+6 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "_fmt"
Cohesion: 0.33
Nodes (6): _fmt(), Any, Serialize structured prompt context as TOON., to_toon(), json.dumps(indent=2) was 2.6x more tokens for the same data., TestFormatting

### Community 89 - "repl.py"
Cohesion: 0.16
Nodes (27): api_db_repositories, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_prompt, rich_table, _choose() (+19 more)

### Community 91 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 92 - "renderer.py"
Cohesion: 0.25
Nodes (6): rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, CLI theme - one place for every terminal color/style used by the CLI. Keys are…

### Community 94 - "AgentCore"
Cohesion: 0.07
Nodes (36): Durable AgentCore identities, run reservations, and child results., concurrent_futures, copy, AgentCore, Agent lifecycle facade and compatibility exports., AgentID, ChildHandle, Message (+28 more)

### Community 97 - "subagent_stream.py"
Cohesion: 0.18
Nodes (10): contextvars, emit_child_event(), Any, Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback (+2 more)

### Community 98 - "get_connection"
Cohesion: 0.15
Nodes (4): get_connection(), Connection, AgentRepository, Any

### Community 99 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, model_validator, ReadFileArgs, SearchFileArgs

### Community 100 - "_FakeEncoded"
Cohesion: 0.33
Nodes (3): list, _FakeEncoded, _FakeModel

### Community 101 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 102 - "test_phased_plan.py"
Cohesion: 0.07
Nodes (41): re, requests, dispatch_phase(), phase_collector_node(), plan_dispatcher_node(), _escape_unescaped_quotes_in_json_strings(), parse_plan(), Plan (+33 more)

### Community 103 - "import_memory_kb.py"
Cohesion: 0.29
Nodes (6): argparse, main(), Opt-in backfill of owner-provenanced legacy learner chunks into the KB. Run…, src_agent, import_legacy(), Opt-in, resumable import; ownerless and mismatched records are quarantined.

### Community 104 - "file_io.py"
Cohesion: 0.21
Nodes (15): 4. Internal Tool Subsystem, File tools, Information and planning tools, edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management. (+7 more)

### Community 105 - "McpRuntime"
Cohesion: 0.12
Nodes (6): McpConnection, McpRuntime, Any, BaseException, test_http_404_is_reported_as_endpoint_error(), test_http_transport_connects_to_real_streamable_server()

### Community 106 - "TestAgentRuntimeFanout"
Cohesion: 0.33
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.20
Nodes (5): ChatRuntimeManager, _deferred_fork(), Any, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 108 - "WebSocket chat session"
Cohesion: 0.18
Nodes (10): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session, HTTP API and WebSocket Runtime (+2 more)

### Community 111 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 112 - "datetime"
Cohesion: 0.14
Nodes (12): calendar, datetime, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool (+4 more)

### Community 113 - "typing"
Cohesion: 0.32
Nodes (4): AuthSessionRepository, _iso(), Any, typing

### Community 114 - "._begin_reserved_run"
Cohesion: 0.42
Nodes (7): utc_now_iso(), _done(), _target(), _done(), _target(), context(), set_trace_parent()

### Community 115 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 117 - "security.py"
Cohesion: 0.15
Nodes (17): hash_password(), needs_rehash(), verify_password(), execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), Any, _row_to_user() (+9 more)

### Community 119 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 121 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 122 - "truncate_value"
Cohesion: 0.47
Nodes (3): Recursively truncate oversized strings in payloads., truncate_value(), TestTruncate

### Community 126 - "decompose_query"
Cohesion: 0.50
Nodes (4): decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

### Community 127 - "6. WebSocket Runtime, Queues, and Recovery"
Cohesion: 0.40
Nodes (4): 6. WebSocket Runtime, Queues, and Recovery, Agent runtime event conversion, Connection lifecycle, WebSocket debugging checklist

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 556 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `repl.py`, `renderer.py`, `run_turn_interactive`, `agent/graph.py`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `AgentCore` connect `AgentCore` to `get_connection`, `load_session.py`, `ChatRuntimeManager`, `in_run`, `agent_runtime.py`, `._begin_reserved_run`, `plan_dispatcher.py`, `ChatService`, `repl.py`, `emit`, `run_turn_interactive`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `.attach`, `ChatPacketQueue`, `EVA Agent API — Reference & How to Use`, `Platform Agent Codebase Documentation`, `.run_turn`, `WebSocket chat session`, `agent_runtime.py`, `._begin_reserved_run`, `ChatService`, `AgentCore`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 64 inferred relationships involving `CurrentUser` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`CurrentUser` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Repositories` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`Repositories` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._