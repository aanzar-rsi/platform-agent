# Graph Report - v2  (2026-09-23)

## Corpus Check
- 156 files · ~54,990 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 2 file(s) not represented in the graph (top: .example 1, .jsonl 1)

## Summary
- 1644 nodes · 4067 edges · 112 communities (90 shown, 22 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 211 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Repositories
- .mock_mode
- postgres_checkpointer.py
- chat_service.py
- TurnRenderer
- EVA Agent API — Reference & How to Use
- agent/graph.py
- bind_session_logger
- update_context_memory
- tools_service.py
- log_event
- agentnode.py
- edit_file
- test_embeddings_quiet.py
- test_context_memory.py
- postgres.py
- test_subagents_integration.py
- learner_agent/graph.py
- api_routes/auth.py
- test_experience_system.py
- CurrentUser
- .run_turn
- ._begin_run
- llm_client.py
- decompose_query
- api_routes/memory.py
- deps.py
- ._commit
- pathlib
- typing
- users.py
- now.py
- repositories/mcp.py
- checkpoints.py
- fetch_all
- set_subagent_callback
- executor.py
- ChatRuntimeManager
- TestMainDispatch
- api_routes/files.py
- test_llm_mock_mode.py
- bootstrap.py
- retrieve_experiences
- fetch_one
- test_llm_logger.py
- context_selector_node
- web_search.py
- prompts/render.py
- ChatPacketQueue
- GitHubRepoDownloader
- field_validator
- TestSubagentNode
- lookup_cached_response
- Multi-User Agentic AI Platform — Database Design
- ReadFileArgs
- graphify.js
- user_memory.py
- paths.py
- opencode.json
- embeddings.py
- make_console
- build_cache_key
- route_from_agent
- main.py
- subagentnode.py
- test_endpoints.py
- ws.py
- learn_session
- sys_info.py
- llm_logger.py
- generate_tree
- WebSocket chat session
- AuthSessionRepository
- test_prompt_templates.py
- AGENTS.md
- Chats
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- _session_prompt
- TestAgentRuntimeFanout
- IdleWatcher
- extract_chunks.py
- Settings
- BackgroundIdleWatcher
- WebSearchArgs
- create_user.py
- test_cli_repl.py
- ._write_and_read
- api_routes/preferences.py
- count_tokens
- _Raw
- .get
- prompt_change/render.py
- sys
- truncate_value
- repl.py
- require_user
- test_cli_theme.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 80 edges
2. `Repositories` - 61 edges
3. `TurnRenderer` - 52 edges
4. `require_user()` - 46 edges
5. `log_event()` - 42 edges
6. `get_repos()` - 41 edges
7. `call_llm()` - 37 edges
8. `update_context_memory()` - 29 edges
9. `run_cli()` - 27 edges
10. `call_llm_stream()` - 26 edges

## Surprising Connections (you probably didn't know these)
- ``GET /v1/chats` (auth)` --references--> `ChatOut`  [INFERRED]
  api/API.md → api/domain/chat.py
- ``POST /v1/chats` (auth)` --references--> `ChatOut`  [INFERRED]
  api/API.md → api/domain/chat.py
- `Operational notes` --references--> `ChatRuntimeManager`  [INFERRED]
  api/API.md → api/services/chat_runtime_manager.py
- `user_memory_fetch()` --uses--> `MemoryRepository`  [INFERRED]
  src/tools/user_memory.py → api/db/repositories/memory.py
- `user_memory_update()` --uses--> `MemoryRepository`  [INFERRED]
  src/tools/user_memory.py → api/db/repositories/memory.py

## Import Cycles
- None detected.

## Communities (112 total, 22 thin omitted)

### Community 0 - "Repositories"
Cohesion: 0.13
Nodes (9): Any, Depends, get, summary(), Repositories, AnalyticsService, Any, PreloadService (+1 more)

### Community 1 - ".mock_mode"
Cohesion: 0.14
Nodes (11): _Chunk, _Completion, fake_gateway(), create(), Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, Build a client exposing chat.completions.with_raw_response.create. (+3 more)

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.05
Nodes (52): langgraph_checkpoint_postgres, ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main(), Idempotent Postgres setup for this project. Creates the target database (if…, Create the target database if it doesn't exist yet. `CREATE DATABASE` can't run…, Create every table/index the app needs, skipping ones that exist. (+44 more)

### Community 3 - "chat_service.py"
Cohesion: 0.14
Nodes (27): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get (+19 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.10
Nodes (11): Console, The complete answer for this turn (authoritative copy)., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., Stop the live region (frame stays on screen) before an interrupt., End of the turn: freeze the final frame and close the region., TurnRenderer (+3 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.11
Nodes (18): Analytics, Authentication, Checkpoints & rollback, Data store (`data/`), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth), `GET /v1/auth/me` (auth), `GET /v1/chats/{chat_id}/checkpoints` (auth) (+10 more)

### Community 6 - "agent/graph.py"
Cohesion: 0.15
Nodes (17): langchain_core_messages, langgraph_graph, langgraph_graph_message, langgraph_types, note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, Agent graph definition., Context selector node — loads a token window from execution_memory into… (+9 more)

### Community 7 - "bind_session_logger"
Cohesion: 0.12
Nodes (17): bind_session_logger(), flush_pending_logs(), get_session_logger(), Path, Append-only JSONL writer for one chat session., Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger() (+9 more)

### Community 8 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 9 - "tools_service.py"
Cohesion: 0.42
Nodes (7): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info(), ToolsService

### Community 10 - "log_event"
Cohesion: 0.21
Nodes (22): queue, _ensure_writer_started(), log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response() (+14 more)

### Community 11 - "agentnode.py"
Cohesion: 0.11
Nodes (22): BaseMessage, concurrent_futures, langchain_core_runnables, agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation() (+14 more)

### Community 12 - "edit_file"
Cohesion: 0.25
Nodes (11): edit_file(), Any, Path, tool, Read content from a text-based file. Supports optional line-range slicing via…, Make targeted edits to a text file by replacing an exact string match. Finds…, Search a text file for lines matching a pattern or literal string. Streams the…, Resolve and validate a path points to a readable text file. Returns (path,… (+3 more)

### Community 13 - "test_embeddings_quiet.py"
Cohesion: 0.14
Nodes (9): list, src_models, _FakeEncoded, _FakeModel, HfLoadIsQuiet, _install_fakes(), SentenceTransformer(), The HF embedding backend must load quietly: no 'Loading weights' tqdm bar, no… (+1 more)

### Community 14 - "test_context_memory.py"
Cohesion: 0.10
Nodes (19): build_execution_memory_index(), count_content_tokens(), empty_context_memory(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts. (+11 more)

### Community 15 - "postgres.py"
Cohesion: 0.13
Nodes (17): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute() (+9 more)

### Community 16 - "test_subagents_integration.py"
Cohesion: 0.09
Nodes (14): Any, SubagentsService, WebSocket protocol helpers., scripts, tempfile, Tests for the main.py boot dispatch (API server vs interactive agent CLI)., TestDevPyRemoved, End-to-end tests for EVA subagent integration. Covers: registry catalog,… (+6 more)

### Community 17 - "learner_agent/graph.py"
Cohesion: 0.22
Nodes (13): Standalone learner LangGraph: load_session → extract_chunks → persist., _latest_human(), load_session_node(), _message_line(), Any, Load chat trajectory from the main agent checkpointer., _slim_history(), persist_node() (+5 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.23
Nodes (15): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+7 more)

### Community 19 - "test_experience_system.py"
Cohesion: 0.14
Nodes (15): datetime, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+7 more)

### Community 20 - "CurrentUser"
Cohesion: 0.24
Nodes (15): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+7 more)

### Community 21 - ".run_turn"
Cohesion: 0.10
Nodes (16): AgentRuntime, on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion. (+8 more)

### Community 22 - "._begin_run"
Cohesion: 0.23
Nodes (7): _done(), _target(), _done(), _target(), _deferred_fork(), Any, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…

### Community 23 - "llm_client.py"
Cohesion: 0.15
Nodes (31): OpenAI, _build_messages(), _cache_key(), call_llm(), call_llm_stream(), _dump(), _estimated_usage(), _extract_cost() (+23 more)

### Community 24 - "decompose_query"
Cohesion: 0.50
Nodes (4): decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

### Community 25 - "api_routes/memory.py"
Cohesion: 0.24
Nodes (14): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+6 more)

### Community 26 - "deps.py"
Cohesion: 0.15
Nodes (21): api_api_routes, create_app(), get_repos(), Validate JWT for WebSocket handshake., user_from_token(), configure_logging(), decode_access_token(), lifespan() (+13 more)

### Community 27 - "._commit"
Cohesion: 0.30
Nodes (5): _format_args(), Any, Record the planner's parsed decision after its streamed reasoning., _short(), Text

### Community 28 - "pathlib"
Cohesion: 0.11
Nodes (22): get_settings(), BaseSettings, Settings, utc_now_iso(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., Packet, argon2, argon2_exceptions (+14 more)

### Community 29 - "typing"
Cohesion: 0.11
Nodes (31): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., logging (+23 more)

### Community 30 - "users.py"
Cohesion: 0.24
Nodes (11): hash_password(), needs_rehash(), verify_password(), execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), Any, _row_to_user() (+3 more)

### Community 31 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 32 - "repositories/mcp.py"
Cohesion: 0.22
Nodes (12): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+4 more)

### Community 33 - "checkpoints.py"
Cohesion: 0.31
Nodes (11): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+3 more)

### Community 34 - "fetch_all"
Cohesion: 0.27
Nodes (8): fetch_all(), get_connection(), Any, Connection, _iso(), MemoryRepository, Any, _row_to_entry()

### Community 35 - "set_subagent_callback"
Cohesion: 0.20
Nodes (7): contextvars, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback, TestSubagentStream

### Community 36 - "executor.py"
Cohesion: 0.21
Nodes (15): execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python…, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+7 more)

### Community 37 - "ChatRuntimeManager"
Cohesion: 0.23
Nodes (4): ChatRuntime, ChatRuntimeManager, WebSocket, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 39 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 40 - "test_llm_mock_mode.py"
Cohesion: 0.16
Nodes (8): _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Wrappers sometimes replace these with `(prompt, system_prompt=None,…, Captures every record the client emits instead of writing it anywhere., TestErrorsAreRecorded, TestMockModeOff, TestSandboxStubCompatibility, TestStreamReplay

### Community 41 - "bootstrap.py"
Cohesion: 0.27
Nodes (11): ensure_venv_on_path(), get_python_executable(), get_venv_python(), get_venv_site_packages(), Path, Ensure the project .venv is used by the current Python process., Prepend the project venv site-packages directory to sys.path., Return the project venv Python when available, otherwise sys.executable. (+3 more)

### Community 42 - "retrieve_experiences"
Cohesion: 0.21
Nodes (8): Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), format_experiences_for_prompt(), Any, Return top-k experience chunks. Never raises — returns [] on any failure or…, retrieve_experiences(), TestAgentNodeHelper, TestRetrieveSoftFail

### Community 43 - "fetch_one"
Cohesion: 0.38
Nodes (6): fetch_one(), _iso(), Any, _row_to_chat(), SessionRepository, _valid_uuid()

### Community 44 - "test_llm_logger.py"
Cohesion: 0.21
Nodes (8): os, src_utils, current_session_ids(), chat/run/user/core ids from the ContextVar-bound agent session logger. Falls…, Tests for the LLM call recorder and its mock-replay cache key. No live Postgres…, _record_kwargs(), TestRecordShape, TestSessionIdentity

### Community 45 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 46 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 47 - "prompts/render.py"
Cohesion: 0.07
Nodes (27): _eval_cond(), _fmt(), _Node, _parse(), _present(), PromptRenderError, Any, Exception (+19 more)

### Community 48 - "ChatPacketQueue"
Cohesion: 0.22
Nodes (4): ChatPacketQueue, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback).

### Community 49 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 52 - "lookup_cached_response"
Cohesion: 0.25
Nodes (8): lookup_cached_response(), Any, Most recent successful, non-replayed call with this exact key. Global across…, Fan a completed call out to the JSONL file and the Postgres table. Both sinks…, record_llm_call(), _write_db(), _write_file(), TestLookupSoftFails

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): model_validator, EditFileArgs, BaseModel, field_validator, ReadFileArgs, SearchFileArgs

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "user_memory.py"
Cohesion: 0.24
Nodes (10): Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update() (+2 more)

### Community 57 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 59 - "embeddings.py"
Cohesion: 0.25
Nodes (10): hashlib, numpy, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy…, Deterministic hashing bag-of-words vectorizer (no ML dependencies). (+2 more)

### Community 60 - "make_console"
Cohesion: 0.23
Nodes (8): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestPromptForInterrupt

### Community 61 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 62 - "route_from_agent"
Cohesion: 0.36
Nodes (3): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting

### Community 63 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 64 - "subagentnode.py"
Cohesion: 0.14
Nodes (20): _calls_this_turn(), RunnableConfig, Sub-agent node — delegates a focused task to a specialised child agent. Reads…, Count of human messages so far — increments once per new user message, so calls…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node(), _turn_number(), emit_subagent_event() (+12 more)

### Community 65 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "learn_session"
Cohesion: 0.29
Nodes (5): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, Standalone learner agent: extract experience chunks from idle chats., TestLearnSessionSoftFail

### Community 68 - "sys_info.py"
Cohesion: 0.25
Nodes (7): langchain_core_tools, platform, Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 69 - "llm_logger.py"
Cohesion: 0.31
Nodes (8): atexit, _db_loop(), _db_params(), _ensure_db_writer_started(), _ensure_table(), Full-fidelity recording of every LLM call, plus the mock-replay cache. Two…, Record -> INSERT params. JSONB columns need real JSON strings., time

### Community 70 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 71 - "WebSocket chat session"
Cohesion: 0.25
Nodes (7): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session

### Community 72 - "AuthSessionRepository"
Cohesion: 0.46
Nodes (3): AuthSessionRepository, _iso(), Any

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.06
Nodes (28): agentnode_prompt_loader(), _has_tool(), _load_module(), load_prompt(), Any, Path, Load a versioned reusable prompt module., Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the… (+20 more)

### Community 75 - "Chats"
Cohesion: 0.40
Nodes (5): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 89 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 90 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 92 - "extract_chunks.py"
Cohesion: 0.14
Nodes (14): json, re, Prompt loading for every agent and sub-agent in the project. One generic entry…, build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., extract_chunks_node(), _normalize_chunk() (+6 more)

### Community 94 - "Settings"
Cohesion: 0.40
Nodes (3): BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 97 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 98 - "create_user.py"
Cohesion: 0.25
Nodes (5): psycopg_types_json, create_user(), Create one application user and their required onboarding records. Edit the…, Create the user, credentials, and preferences in one transaction., TestCreateUser

### Community 99 - "test_cli_repl.py"
Cohesion: 0.11
Nodes (15): io, rich_console, rich_markdown, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, parse_command(), CLI theme - one place for every terminal color/style used by the CLI. Keys are…, Unit tests for the live turn renderer (live rendering disabled in tests). (+7 more)

### Community 100 - "._write_and_read"
Cohesion: 0.18
Nodes (7): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall

### Community 101 - "api_routes/preferences.py"
Cohesion: 0.25
Nodes (9): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, PreferencesService (+1 more)

### Community 102 - "count_tokens"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 103 - "_Raw"
Cohesion: 0.40
Nodes (3): Stand-in for the SDK's raw-response wrapper: headers + .parse()., _Raw, create()

### Community 105 - "prompt_change/render.py"
Cohesion: 0.22
Nodes (13): _eval_cond(), _fmt(), _Node, _parse(), _present(), Generic conditional prompt renderer. The skeleton (prompt.txt) is fully…, Return the inline prefix used before each action template. Only meaningful at…, render() (+5 more)

### Community 106 - "sys"
Cohesion: 0.09
Nodes (24): object, pydantic, clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node() (+16 more)

### Community 107 - "truncate_value"
Cohesion: 0.47
Nodes (3): Recursively truncate oversized strings in payloads., truncate_value(), TestTruncate

### Community 109 - "repl.py"
Cohesion: 0.13
Nodes (32): api_db_repositories, PreferencesRepository, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_panel, rich_prompt (+24 more)

### Community 112 - "require_user"
Cohesion: 0.13
Nodes (19): health(), live(), Depends, get, list_subagents(), Any, Depends, get (+11 more)

## Knowledge Gaps
- **32 isolated node(s):** `$schema`, `plugin`, `graphify`, `Layout`, ``POST /v1/auth/login` (public)` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 483 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `._commit`, `test_cli_repl.py`, `make_console`, `repl.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `checkpoints.py`, `EVA Agent API — Reference & How to Use`, `ChatPacketQueue`, `.run_turn`, `._begin_run`, `pathlib`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `Repositories`, `checkpoints.py`, `chat_service.py`, `api_routes/preferences.py`, `tools_service.py`, `require_user`, `api_routes/auth.py`, `api_routes/memory.py`, `deps.py`, `typing`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._