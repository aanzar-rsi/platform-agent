# Graph Report - backend  (2026-09-28)

## Corpus Check
- 156 files · ~83,175 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 28 file(s) not represented in the graph (top: .jsonl 27, .example 1)

## Summary
- 1788 nodes · 4569 edges · 105 communities (85 shown, 20 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 424 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- typing
- .mock_mode
- postgres_checkpointer.py
- chat_service.py
- TurnRenderer
- EVA Agent API — Reference & How to Use
- repositories/mcp.py
- make_console
- TestAgentNodePrompt
- Repositories
- postgres.py
- agentnode.py
- test_llm_mock_mode.py
- security.py
- update_context_memory
- ChatPacketQueue
- HfLoadIsQuiet
- learner_agent/graph.py
- api_routes/auth.py
- test_experience_system.py
- TestSubagentNode
- .run_turn
- ChatRuntimeManager
- llm_client.py
- BackgroundIdleWatcher
- api_routes/memory.py
- endpoint.py
- _session_prompt
- test_endpoints.py
- CurrentUser
- log_event
- os
- require_user
- CheckpointService
- context_selector_node
- Detailed Subsystem Reference
- executor.py
- context_manager.py
- lookup_cached_response
- Platform Agent Codebase Documentation
- run_turn_interactive
- bootstrap.py
- vector_store.py
- pathlib
- test_subagents_integration.py
- .test_resumes_after_interrupt
- web_search.py
- fetch_one
- parse_command
- retrieve.py
- field_validator
- embeddings.py
- toolnode.py
- Multi-User Agentic AI Platform — Database Design
- file_io.py
- graphify.js
- extract_chunks.py
- ._commit
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- GitHubRepoDownloader
- route_from_agent
- subagentnode.py
- renderer.py
- ws.py
- test_context_memory.py
- user_memory.py
- llm_logger.py
- IdleWatcher
- list_experiences
- test_prompt_templates.py
- AGENTS.md
- fetch_all
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- Repository map
- TestAgentRuntimeFanout
- prompt_loader.py
- build_cache_key
- agent_runtime.py
- health.py
- tool_node
- paths.py
- repl.py
- ._write_and_read
- .get
- test_db_setup.py
- mcp_runtime.py
- agent/graph.py
- _FakeEncoded
- Settings
- TestMainDispatch

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 91 edges
2. `Repositories` - 65 edges
3. `TurnRenderer` - 59 edges
4. `require_user()` - 53 edges
5. `get_repos()` - 50 edges
6. `log_event()` - 43 edges
7. `call_llm()` - 39 edges
8. `agent_node()` - 31 edges
9. `update_context_memory()` - 30 edges
10. `call_llm_stream()` - 30 edges

## Surprising Connections (you probably didn't know these)
- `Add an API resource` --references--> `require_user()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/core/deps.py
- `Entrypoints` --references--> `ChatRuntimeManager`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/services/chat_runtime_manager.py
- `Recommended debugging workflow` --references--> `_parse_response()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Main agent loop` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py

## Import Cycles
- None detected.

## Communities (105 total, 20 thin omitted)

### Community 0 - "typing"
Cohesion: 0.15
Nodes (16): get_prefs(), put_prefs(), Any, Depends, get, put, list_subagents(), Any (+8 more)

### Community 1 - ".mock_mode"
Cohesion: 0.13
Nodes (13): _Chunk, _Completion, _MockBase, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, Captures every record the client emits instead of writing it anywhere., TestMockModeOff (+5 more)

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.06
Nodes (60): _load_messages(), _message_content(), _message_role(), Any, Chat transcript from the indexed `messages` table, scoped to the active branch…, _ui_hidden(), _ui_messages(), 7. PostgreSQL, Repositories, and Checkpoints (+52 more)

### Community 3 - "chat_service.py"
Cohesion: 0.15
Nodes (24): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get (+16 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.10
Nodes (11): Topology, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., TurnRenderer (+3 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.07
Nodes (29): Analytics, Authentication, Chats, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth) (+21 more)

### Community 6 - "repositories/mcp.py"
Cohesion: 0.20
Nodes (13): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+5 more)

### Community 7 - "make_console"
Cohesion: 0.23
Nodes (8): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestPromptForInterrupt

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "Repositories"
Cohesion: 0.10
Nodes (14): Any, Depends, get, summary(), list_tools(), Any, Depends, get (+6 more)

### Community 10 - "postgres.py"
Cohesion: 0.13
Nodes (17): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute() (+9 more)

### Community 11 - "agentnode.py"
Cohesion: 0.10
Nodes (25): available_mcp_tools(), BaseMessage, Retrieval in the main agent, agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation() (+17 more)

### Community 12 - "test_llm_mock_mode.py"
Cohesion: 0.12
Nodes (11): src_models, src_utils, fake_gateway(), create(), Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Wrappers sometimes replace these with `(prompt, system_prompt=None,…, Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create. (+3 more)

### Community 13 - "security.py"
Cohesion: 0.15
Nodes (16): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+8 more)

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "ChatPacketQueue"
Cohesion: 0.15
Nodes (10): Envelope (all messages), ChatPacketQueue, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., 6. WebSocket Runtime, Queues, and Recovery, `ChatPacketQueue` behavior, Connection lifecycle (+2 more)

### Community 16 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 17 - "learner_agent/graph.py"
Cohesion: 0.19
Nodes (16): Step 3: persist and index, Standalone learner LangGraph: load_session → extract_chunks → persist., _latest_human(), load_session_node(), _message_line(), Any, Load chat trajectory from the main agent checkpointer., _slim_history() (+8 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "test_experience_system.py"
Cohesion: 0.11
Nodes (17): datetime, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+9 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - ".run_turn"
Cohesion: 0.13
Nodes (10): AgentRuntime, on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion. (+2 more)

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.14
Nodes (12): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+4 more)

### Community 23 - "llm_client.py"
Cohesion: 0.14
Nodes (33): Gateway behavior, LLM call logger and replay cache, OpenAI, emit_usage(), Any, _build_messages(), _cache_key(), call_llm() (+25 more)

### Community 24 - "BackgroundIdleWatcher"
Cohesion: 0.29
Nodes (5): CLI, Commands, Flow, BackgroundIdleWatcher, Run the async watcher in a daemon thread for non-async entrypoints.

### Community 25 - "api_routes/memory.py"
Cohesion: 0.22
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "endpoint.py"
Cohesion: 0.22
Nodes (12): Validate JWT for WebSocket handshake., user_from_token(), decode_access_token(), Any, chat_ws(), _handle_client_message(), Any, WebSocket (+4 more)

### Community 27 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (10): create_app(), fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready. (+2 more)

### Community 29 - "CurrentUser"
Cohesion: 0.14
Nodes (15): CurrentUser, McpCreateRequest, McpUpdateRequest, model_validator, connection_log(), McpService, public_server(), Any (+7 more)

### Community 30 - "log_event"
Cohesion: 0.08
Nodes (43): Agent trace logger, learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, bind_session_logger(), _ensure_writer_started(), flush_pending_logs(), get_session_logger() (+35 more)

### Community 31 - "os"
Cohesion: 0.09
Nodes (19): calendar, dotenv, json, langchain_core_tools, os, platform, pydantic, Agent environment and runtime configuration. Loads `client2.0/.env` into the… (+11 more)

### Community 32 - "require_user"
Cohesion: 0.28
Nodes (19): connect_server(), create_server(), delete_server(), disconnect_server(), import_servers(), list_servers(), Any, delete (+11 more)

### Community 33 - "CheckpointService"
Cohesion: 0.25
Nodes (12): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+4 more)

### Community 34 - "context_selector_node"
Cohesion: 0.39
Nodes (3): context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "Detailed Subsystem Reference"
Cohesion: 0.17
Nodes (11): Packet, 10. Safe Extension Guide, 1. End-to-End Turn Execution, 8. Observability, Logs, and LLM Replay, Add a prompt block, Add a WebSocket event, Add an API resource, Add an internal tool (+3 more)

### Community 36 - "executor.py"
Cohesion: 0.08
Nodes (43): 4. Internal Tool Subsystem, Command execution tools, File tools, Information and planning tools, Tools: `tool_node`, decompose_query(), Any, tool (+35 more)

### Community 37 - "context_manager.py"
Cohesion: 0.29
Nodes (9): _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM., Check how much of a model's input context window the prompt consumes. Returns…, Check how much of a model's output context window a response consumes. Returns… (+1 more)

### Community 38 - "lookup_cached_response"
Cohesion: 0.47
Nodes (3): lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, TestLookupSoftFails

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.08
Nodes (24): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Entrypoints (+16 more)

### Community 40 - "run_turn_interactive"
Cohesion: 0.12
Nodes (16): contextvars, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_token_callback() (+8 more)

### Community 41 - "bootstrap.py"
Cohesion: 0.18
Nodes (16): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), ensure_venv_on_path(), get_python_executable(), get_venv_python() (+8 more)

### Community 42 - "vector_store.py"
Cohesion: 0.14
Nodes (20): 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, math, Soft-fail embed; returns None on any error., try_embed_text(), ensure_experience_dir(), Path, src_subagents_learner_agent_store (+12 more)

### Community 43 - "pathlib"
Cohesion: 0.09
Nodes (23): generate_tree(), Path, Recursively generates a string representation of a directory tree., io, pathlib, rich_console, scripts, src_agent_nodes (+15 more)

### Community 44 - "test_subagents_integration.py"
Cohesion: 0.13
Nodes (8): Any, SubagentsService, WebSocket protocol helpers., End-to-end tests for EVA subagent integration. Covers: registry catalog,…, TestCatalogAPI, TestProtocolConstants, TestRouting, TestSubagentRegistry

### Community 45 - ".test_resumes_after_interrupt"
Cohesion: 0.33
Nodes (4): interrupt_step(), TestRunTurnInteractive, fake_run_turn(), first()

### Community 46 - "web_search.py"
Cohesion: 0.17
Nodes (14): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, BaseModel, field_validator (+6 more)

### Community 47 - "fetch_one"
Cohesion: 0.38
Nodes (6): fetch_one(), _iso(), Any, _row_to_chat(), SessionRepository, _valid_uuid()

### Community 49 - "retrieve.py"
Cohesion: 0.22
Nodes (6): Standalone learner agent: extract experience chunks from idle chats., Any, Safe experience retrieval for the main agent hot path., Return top-k experience chunks. Never raises — returns [] on any failure or…, retrieve_experiences(), TestRetrieveSoftFail

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "embeddings.py"
Cohesion: 0.21
Nodes (12): Step 2: extract reusable advice, hashlib, numpy, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy… (+4 more)

### Community 52 - "toolnode.py"
Cohesion: 0.15
Nodes (18): clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each…, Call at the very top of a node, before any side effects. Returns the… (+10 more)

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "file_io.py"
Cohesion: 0.23
Nodes (7): EditFileArgs, BaseModel, field_validator, model_validator, Internal tools for file I/O operations, file search, and directory management., ReadFileArgs, SearchFileArgs

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "extract_chunks.py"
Cohesion: 0.17
Nodes (15): Full learner sequence, load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval. (+7 more)

### Community 57 - "._commit"
Cohesion: 0.18
Nodes (6): emit_tag(), _format_args(), Any, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short()

### Community 60 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

### Community 62 - "route_from_agent"
Cohesion: 0.36
Nodes (3): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting

### Community 64 - "subagentnode.py"
Cohesion: 0.13
Nodes (21): Add a planner-callable sub-agent, Current Extension Points and Limits, Sub-agents: `subagent_node` and gate, note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, subagent_gate_node(), _calls_this_turn(), RunnableConfig (+13 more)

### Community 65 - "renderer.py"
Cohesion: 0.25
Nodes (6): rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, CLI theme - one place for every terminal color/style used by the CLI. Keys are…

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "test_context_memory.py"
Cohesion: 0.10
Nodes (19): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+11 more)

### Community 68 - "user_memory.py"
Cohesion: 0.24
Nodes (10): Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update() (+2 more)

### Community 69 - "llm_logger.py"
Cohesion: 0.11
Nodes (27): atexit, queue, register, _safe_chat_id(), build_record(), current_session_ids(), _db_loop(), _db_params() (+19 more)

### Community 70 - "IdleWatcher"
Cohesion: 0.18
Nodes (7): Experience API view, Idle scheduling and branch handling, Learner graph, Learning Agent and Experience System, Step 1: load trajectory, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread.

### Community 72 - "list_experiences"
Cohesion: 0.43
Nodes (7): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization.

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.15
Nodes (9): re, _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —…, These were {{ }} for str.format(); the renderer would send them literally to…, _strip_comments(), TestEveryTemplateFileIsRegistered (+1 more)

### Community 75 - "fetch_all"
Cohesion: 0.22
Nodes (11): execute(), fetch_all(), get_connection(), Any, Connection, Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), MemoryRepository (+3 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 89 - "Repository map"
Cohesion: 0.27
Nodes (6): AnalyticsRepository, Any, AuthSessionRepository, _iso(), Any, Repository map

### Community 90 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 91 - "prompt_loader.py"
Cohesion: 0.06
Nodes (36): 3. Prompt Rendering Deep Dive, Major prompt functions, Practical prompt-debug method, System versus user prompt, agentnode_prompt_loader(), _eval_cond(), _fmt(), _has_tool() (+28 more)

### Community 92 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 94 - "agent_runtime.py"
Cohesion: 0.15
Nodes (19): api_api_routes, get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., ensure_client_path() (+11 more)

### Community 96 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 97 - "tool_node"
Cohesion: 0.17
Nodes (12): Agent runtime event conversion, Context selection and user questions, Functions to start with when tracing a turn, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, empty_context_memory(), human_input_node() (+4 more)

### Community 98 - "paths.py"
Cohesion: 0.62
Nodes (5): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path

### Community 99 - "repl.py"
Cohesion: 0.16
Nodes (27): api_db_repositories, PreferencesRepository, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_prompt, rich_table (+19 more)

### Community 100 - "._write_and_read"
Cohesion: 0.21
Nodes (4): Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 103 - "test_db_setup.py"
Cohesion: 0.14
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 105 - "mcp_runtime.py"
Cohesion: 0.07
Nodes (22): call_mcp_tool(), McpConnection, McpRuntime, McpTool, Any, Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, _mcp_tools_from_metadata(), _parameters_from_mcp_item() (+14 more)

### Community 106 - "agent/graph.py"
Cohesion: 0.14
Nodes (16): State, langchain_core_messages, langchain_core_runnables, langgraph_graph, langgraph_graph_message, langgraph_types, Agent graph definition., _coerce_token() (+8 more)

### Community 107 - "_FakeEncoded"
Cohesion: 0.33
Nodes (3): list, _FakeEncoded, _FakeModel

### Community 108 - "Settings"
Cohesion: 0.33
Nodes (4): get_settings(), BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

## Knowledge Gaps
- **43 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 506 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_repos()` connect `require_user` to `typing`, `CheckpointService`, `chat_service.py`, `repl.py`, `Repositories`, `mcp_runtime.py`, `agentnode.py`, `api_routes/auth.py`, `ChatRuntimeManager`, `api_routes/memory.py`, `endpoint.py`, `agent_runtime.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `CheckpointService`, `Detailed Subsystem Reference`, `EVA Agent API — Reference & How to Use`, `Platform Agent Codebase Documentation`, `ChatPacketQueue`, `.run_turn`, `agent_runtime.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `typing`, `CheckpointService`, `health.py`, `chat_service.py`, `require_user`, `list_experiences`, `Repositories`, `mcp_runtime.py`, `api_routes/auth.py`, `api_routes/memory.py`, `endpoint.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._