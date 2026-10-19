# Graph Report - v2  (2026-09-24)

## Corpus Check
- 158 files · ~73,835 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: .jsonl 15, .example 1)

## Summary
- 1703 nodes · 4220 edges · 109 communities (88 shown, 21 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 275 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- typing
- .mock_mode
- postgres_checkpointer.py
- get_repos
- TurnRenderer
- EVA Agent API — Reference & How to Use
- postgres.py
- bind_session_logger
- TestAgentNodePrompt
- tools_service.py
- test_context_memory.py
- agentnode.py
- edit_file
- log_event
- update_context_memory
- ChatPacketQueue
- HfLoadIsQuiet
- extract_chunks.py
- api_routes/auth.py
- idle_watcher.py
- TestSubagentNode
- .run_turn
- ChatRuntimeManager
- llm_client.py
- empty_context_memory
- api_routes/memory.py
- app.py
- toolnode.py
- test_endpoints.py
- vector_store.py
- embeddings.py
- now.py
- api_routes/mcp.py
- CurrentUser
- context_selector_node
- paths.py
- executor.py
- count_tokens
- TestMainDispatch
- api_routes/files.py
- run_turn_interactive
- bootstrap.py
- GitHubRepoDownloader
- create_user.py
- pathlib
- prompts/render.py
- web_search.py
- render
- truncate_value
- test_experience_system.py
- field_validator
- parse_command
- db_utils.py
- Multi-User Agentic AI Platform — Database Design
- src/config.py
- graphify.js
- user_memory.py
- _present
- opencode.json
- health.py
- WebSocket chat session
- build_cache_key
- route_from_agent
- security.py
- subagentnode.py
- utc_now_iso
- ws.py
- _FakeEncoded
- tools/__init__.py
- llm_logger.py
- BackgroundIdleWatcher
- _default_runtime
- generate_tree
- test_prompt_templates.py
- AGENTS.md
- test_llm_mock_mode.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- _session_prompt
- TestAgentRuntimeFanout
- WebSearchArgs
- set_subagent_callback
- agent_runtime.py
- learn_session
- TestTheme
- lookup_cached_response
- repl.py
- ._write_and_read
- TestSubagentRegistry
- Gateway behavior
- db_setup.py
- prompt_change/render.py
- agent/graph.py
- run_cli
- require_user

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 80 edges
2. `Repositories` - 61 edges
3. `TurnRenderer` - 59 edges
4. `require_user()` - 47 edges
5. `log_event()` - 42 edges
6. `get_repos()` - 41 edges
7. `call_llm()` - 38 edges
8. `update_context_memory()` - 29 edges
9. `call_llm_stream()` - 29 edges
10. `run_cli()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Entrypoints` --references--> `ChatRuntimeManager`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/services/chat_runtime_manager.py
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Step 1: load trajectory` --references--> `load_session_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/subagents/learner_agent/nodes/load_session.py
- `Authentication` --references--> `require_user()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/core/deps.py
- `Flow` --references--> `UserRepository`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/db/repositories/users.py

## Import Cycles
- None detected.

## Communities (109 total, 21 thin omitted)

### Community 0 - "typing"
Cohesion: 0.13
Nodes (19): Any, Depends, get, summary(), get_prefs(), put_prefs(), Any, Depends (+11 more)

### Community 1 - ".mock_mode"
Cohesion: 0.18
Nodes (8): _Chunk, _Completion, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, TestMockModeOn, TestStreamReplay, _Usage

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.05
Nodes (52): CLI, Commands, Entrypoints, Environment, EVA Agent Codebase Documentation, Flow, Persistence and Checkpoints, PostgreSQL responsibilities (+44 more)

### Community 3 - "get_repos"
Cohesion: 0.14
Nodes (28): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get (+20 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.05
Nodes (27): _format_args(), Any, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., Draws activity + streamed output for a single agent turn. (+19 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.08
Nodes (23): Analytics, Authentication, Chats, Checkpoints & rollback, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth) (+15 more)

### Community 6 - "postgres.py"
Cohesion: 0.06
Nodes (44): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, execute(), fetch_all(), fetch_one(), get_connection(), get_pool() (+36 more)

### Community 7 - "bind_session_logger"
Cohesion: 0.13
Nodes (16): bind_session_logger(), flush_pending_logs(), get_session_logger(), Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger(), current_session_ids(), chat/run/user/core ids from the ContextVar-bound agent session logger. Falls… (+8 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "tools_service.py"
Cohesion: 0.23
Nodes (12): list_tools(), Any, Depends, get, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict() (+4 more)

### Community 10 - "test_context_memory.py"
Cohesion: 0.12
Nodes (16): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+8 more)

### Community 11 - "agentnode.py"
Cohesion: 0.11
Nodes (22): BaseMessage, concurrent_futures, agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation(), _is_turn_start() (+14 more)

### Community 12 - "edit_file"
Cohesion: 0.25
Nodes (11): edit_file(), Any, Path, tool, Read content from a text-based file. Supports optional line-range slicing via…, Make targeted edits to a text file by replacing an exact string match. Finds…, Search a text file for lines matching a pattern or literal string. Streams the…, Resolve and validate a path points to a readable text file. Returns (path,… (+3 more)

### Community 13 - "log_event"
Cohesion: 0.33
Nodes (15): log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response(), log_route(), log_run_end() (+7 more)

### Community 14 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 15 - "ChatPacketQueue"
Cohesion: 0.19
Nodes (5): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback).

### Community 16 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 17 - "extract_chunks.py"
Cohesion: 0.18
Nodes (19): logging, Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks., _utc_now() (+11 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "idle_watcher.py"
Cohesion: 0.15
Nodes (14): asyncio, datetime, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, Background idle watcher: learn from chats idle for IDLE_SECONDS. (+6 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - ".run_turn"
Cohesion: 0.13
Nodes (12): AgentRuntime, on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Event (+4 more)

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.13
Nodes (10): ChatRuntime, ChatRuntimeManager, _deferred_fork(), Any, WebSocket, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs., HTTP API and WebSocket Runtime (+2 more)

### Community 23 - "llm_client.py"
Cohesion: 0.15
Nodes (31): OpenAI, emit_usage(), Any, _build_messages(), _cache_key(), call_llm(), call_llm_stream(), _dump() (+23 more)

### Community 24 - "empty_context_memory"
Cohesion: 0.12
Nodes (13): Main prompt contract, Prompt Architecture and Rendering, Prompt composition, Template language, empty_context_memory(), RunnableConfig, tool_node(), agentnode_prompt_loader() (+5 more)

### Community 25 - "api_routes/memory.py"
Cohesion: 0.24
Nodes (14): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+6 more)

### Community 26 - "app.py"
Cohesion: 0.17
Nodes (15): api_api_routes, create_app(), Validate JWT for WebSocket handshake., user_from_token(), api_ws, chat_ws(), _handle_client_message(), Any (+7 more)

### Community 27 - "toolnode.py"
Cohesion: 0.12
Nodes (22): langchain_core_runnables, is_pause_requested(), maybe_pause(), note_text_from_resume(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each… (+14 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "vector_store.py"
Cohesion: 0.15
Nodes (22): json, math, Soft-fail embed; returns None on any error., try_embed_text(), ensure_experience_dir(), Path, Learner / experience-system configuration., src_subagents_learner_agent_store (+14 more)

### Community 30 - "embeddings.py"
Cohesion: 0.21
Nodes (12): Step 2: extract reusable advice, hashlib, numpy, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy… (+4 more)

### Community 31 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 32 - "api_routes/mcp.py"
Cohesion: 0.19
Nodes (14): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+6 more)

### Community 33 - "CurrentUser"
Cohesion: 0.22
Nodes (13): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CurrentUser, CheckpointOut (+5 more)

### Community 34 - "context_selector_node"
Cohesion: 0.39
Nodes (3): context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 36 - "executor.py"
Cohesion: 0.22
Nodes (15): Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python… (+7 more)

### Community 37 - "count_tokens"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 39 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 40 - "run_turn_interactive"
Cohesion: 0.27
Nodes (9): Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_token_callback(), reset_usage_callback(), set_token_callback(), set_usage_callback(), run_turn_interactive(), TokenCallback (+1 more)

### Community 41 - "bootstrap.py"
Cohesion: 0.33
Nodes (9): ensure_venv_on_path(), get_python_executable(), get_venv_python(), get_venv_site_packages(), Path, Ensure the project .venv is used by the current Python process., Prepend the project venv site-packages directory to sys.path., Return the project venv Python when available, otherwise sys.executable. (+1 more)

### Community 42 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

### Community 43 - "create_user.py"
Cohesion: 0.29
Nodes (5): hash_password(), create_user(), Create one application user and their required onboarding records. Edit the…, Create the user, credentials, and preferences in one transaction., TestCreateUser

### Community 44 - "pathlib"
Cohesion: 0.09
Nodes (27): Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., Any, SubagentsService, WebSocket protocol helpers., io, langchain_core_messages, os, pathlib (+19 more)

### Community 45 - "prompts/render.py"
Cohesion: 0.11
Nodes (19): _eval_cond(), _fmt(), _Node, _parse(), PromptRenderError, Any, Exception, Generic conditional prompt renderer. Prompt templates are declarative: every… (+11 more)

### Community 46 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 47 - "render"
Cohesion: 0.23
Nodes (5): Strip trailing spaces, collapse the blank-line runs left behind by dropped…, render(), _tidy(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 48 - "truncate_value"
Cohesion: 0.24
Nodes (6): Recursively truncate oversized strings in payloads., Append-only JSONL writer for one chat session., SessionLogger, truncate_value(), _utc_now(), TestTruncate

### Community 49 - "test_experience_system.py"
Cohesion: 0.10
Nodes (16): Retrieval in the main agent, Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., format_experiences_for_prompt(), Any, Safe experience retrieval for the main agent hot path. (+8 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 52 - "db_utils.py"
Cohesion: 0.17
Nodes (14): contextlib, psycopg, psycopg_pool, psycopg_rows, execute(), fetch_all(), fetch_one(), get_connection() (+6 more)

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "src/config.py"
Cohesion: 0.11
Nodes (15): dotenv, langchain_core_tools, model_validator, pydantic, re, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, DecomposeQueryArgs, BaseModel (+7 more)

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "user_memory.py"
Cohesion: 0.24
Nodes (10): Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update() (+2 more)

### Community 57 - "_present"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 59 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 60 - "WebSocket chat session"
Cohesion: 0.25
Nodes (7): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session

### Community 61 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 62 - "route_from_agent"
Cohesion: 0.27
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "security.py"
Cohesion: 0.25
Nodes (6): needs_rehash(), verify_password(), argon2, argon2_exceptions, jwt, secrets

### Community 64 - "subagentnode.py"
Cohesion: 0.15
Nodes (18): Memory Model, _calls_this_turn(), RunnableConfig, Sub-agent node — delegates a focused task to a specialised child agent. Reads…, Count of human messages so far — increments once per new user message, so calls…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node(), _turn_number() (+10 more)

### Community 65 - "utc_now_iso"
Cohesion: 0.39
Nodes (6): utc_now_iso(), _done(), _target(), _done(), _target(), clear_pause()

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "_FakeEncoded"
Cohesion: 0.33
Nodes (3): list, _FakeEncoded, _FakeModel

### Community 68 - "tools/__init__.py"
Cohesion: 0.17
Nodes (11): platform, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…, Internal tools package for the agent., Any, tool (+3 more)

### Community 69 - "llm_logger.py"
Cohesion: 0.11
Nodes (25): atexit, queue, register, _ensure_writer_started(), Path, _safe_chat_id(), _writer_loop(), _db_loop() (+17 more)

### Community 70 - "BackgroundIdleWatcher"
Cohesion: 0.13
Nodes (10): Experience API view, Idle scheduling and branch handling, Learner graph, Learning Agent and Experience System, Step 1: load trajectory, Step 3: persist and index, BackgroundIdleWatcher, IdleWatcher (+2 more)

### Community 71 - "_default_runtime"
Cohesion: 0.29
Nodes (5): _default_runtime(), get_settings(), BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 72 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.10
Nodes (19): _has_tool(), _load_module(), load_prompt(), Any, Path, Prompt loading for every agent and sub-agent in the project. One generic entry…, Load a versioned reusable prompt module., Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the… (+11 more)

### Community 75 - "test_llm_mock_mode.py"
Cohesion: 0.10
Nodes (16): src_models, src_utils, fake_gateway(), create(), _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Wrappers sometimes replace these with `(prompt, system_prompt=None,…, Stand-in for the SDK's raw-response wrapper: headers + .parse(). (+8 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 89 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 90 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 91 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 92 - "set_subagent_callback"
Cohesion: 0.20
Nodes (7): contextvars, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback, TestSubagentStream

### Community 94 - "agent_runtime.py"
Cohesion: 0.17
Nodes (15): get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), ensure_client_path(), get_agent_app(), Thin re-export — stream bridging lives in agent_runtime for cohesion. (+7 more)

### Community 96 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 98 - "lookup_cached_response"
Cohesion: 0.47
Nodes (3): lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, TestLookupSoftFails

### Community 99 - "repl.py"
Cohesion: 0.14
Nodes (15): api_db_repositories, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_markdown, rich_panel, rich_prompt (+7 more)

### Community 100 - "._write_and_read"
Cohesion: 0.19
Nodes (6): build_record(), _utc_now(), Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 102 - "Gateway behavior"
Cohesion: 0.67
Nodes (3): Gateway behavior, LLM Client, Observability, and Replay, Logging and mock replay

### Community 103 - "db_setup.py"
Cohesion: 0.10
Nodes (14): ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main(), Idempotent Postgres setup for this project. Creates the target database (if…, Create the target database if it doesn't exist yet. `CREATE DATABASE` can't run…, Create every table/index the app needs, skipping ones that exist., LangGraph owns `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` — let its… (+6 more)

### Community 105 - "prompt_change/render.py"
Cohesion: 0.22
Nodes (13): _eval_cond(), _fmt(), _Node, _parse(), _present(), Generic conditional prompt renderer. The skeleton (prompt.txt) is fully…, Return the inline prefix used before each action template. Only meaningful at…, render() (+5 more)

### Community 106 - "agent/graph.py"
Cohesion: 0.09
Nodes (27): run(), Context selection and user questions, Current Extension Points and Limits, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, State, Sub-agents: `subagent_node` and gate (+19 more)

### Community 109 - "run_cli"
Cohesion: 0.22
Nodes (18): PreferencesRepository, _choose(), get_agent_app(), _handle_settings(), _load_state(), _login(), _manage_mcp(), print_banner() (+10 more)

### Community 112 - "require_user"
Cohesion: 0.16
Nodes (17): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., list_subagents() (+9 more)

## Knowledge Gaps
- **41 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 494 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `run_turn_interactive`, `repl.py`, `pathlib`, `run_cli`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `typing`, `api_routes/mcp.py`, `get_repos`, `tools_service.py`, `require_user`, `api_routes/auth.py`, `api_routes/memory.py`, `app.py`, `health.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `TestSubagentNode` connect `TestSubagentNode` to `pathlib`, `bind_session_logger`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._