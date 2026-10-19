# Graph Report - v2  (2026-09-22)

## Corpus Check
- 156 files · ~54,648 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: .jsonl 2, .example 1)

## Summary
- 1629 nodes · 4034 edges · 112 communities (88 shown, 24 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 211 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- fetch_one
- .mock_mode
- postgres_checkpointer.py
- chat_service.py
- TurnRenderer
- EVA Agent API — Reference & How to Use
- agent/graph.py
- log_event
- update_context_memory
- typing
- renderer.py
- agentnode.py
- file_io.py
- HfLoadIsQuiet
- test_context_memory.py
- postgres.py
- subagent_node
- extract_chunks.py
- api_routes/auth.py
- idle_watcher.py
- CurrentUser
- .run_turn
- ChatRuntimeManager
- llm_client.py
- test_subagents_integration.py
- get_repos
- app.py
- ._commit
- src/config.py
- vector_store.py
- Repositories
- now.py
- TestAgentNodePrompt
- checkpoints.py
- experience.py
- set_subagent_callback
- executor.py
- test_llm_logger.py
- pathlib
- api_routes/files.py
- test_llm_mock_mode.py
- bootstrap.py
- prompts/render.py
- _fmt
- db_setup.py
- context_selector_node
- web_search.py
- render
- ChatPacketQueue
- .attach
- field_validator
- TestSubagentNode
- FastAPI
- Multi-User Agentic AI Platform — Database Design
- embeddings.py
- graphify.js
- user_memory.py
- repositories/__init__.py
- opencode.json
- TestMainDispatch
- test_cli_repl.py
- build_cache_key
- route_from_agent
- tools_service.py
- test_prompt_render.py
- test_endpoints.py
- ws.py
- learn_session
- sys_info.py
- llm_logger.py
- WebSocket chat session
- generate_tree
- _present
- test_prompt_templates.py
- AGENTS.md
- list_checkpoint_tree
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- _session_prompt
- TestAgentRuntimeFanout
- IdleWatcher
- text_truncate.py
- TestSchemaStatementsAreIdempotent
- build_config
- TestDbSetupLive
- decompose_query
- parse_command
- ._write_and_read
- api_routes/preferences.py
- count_tokens
- require_user
- json
- prompt_change/render.py
- _NotPaused
- truncate_value
- Any
- repl.py
- .test_public_signatures_stayed_stub_compatible

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 80 edges
2. `Repositories` - 61 edges
3. `TurnRenderer` - 52 edges
4. `require_user()` - 46 edges
5. `get_repos()` - 44 edges
6. `log_event()` - 42 edges
7. `call_llm()` - 37 edges
8. `update_context_memory()` - 29 edges
9. `run_cli()` - 26 edges
10. `call_llm_stream()` - 26 edges

## Surprising Connections (you probably didn't know these)
- `Operational notes` --references--> `ChatRuntimeManager`  [INFERRED]
  api/API.md → api/services/chat_runtime_manager.py
- `user_memory_fetch()` --uses--> `MemoryRepository`  [INFERRED]
  src/tools/user_memory.py → api/db/repositories/memory.py
- `user_memory_update()` --uses--> `MemoryRepository`  [INFERRED]
  src/tools/user_memory.py → api/db/repositories/memory.py
- ``GET /v1/chats` (auth)` --references--> `ChatOut`  [INFERRED]
  api/API.md → api/domain/chat.py
- ``POST /v1/chats` (auth)` --references--> `ChatOut`  [INFERRED]
  api/API.md → api/domain/chat.py

## Import Cycles
- None detected.

## Communities (112 total, 24 thin omitted)

### Community 0 - "fetch_one"
Cohesion: 0.06
Nodes (45): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, hash_password(), needs_rehash(), verify_password(), execute(), fetch_all() (+37 more)

### Community 1 - ".mock_mode"
Cohesion: 0.18
Nodes (8): _Chunk, _Completion, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, TestMockModeOn, TestStreamReplay, _Usage

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.17
Nodes (17): langgraph_checkpoint_postgres, _ensure_branch_learn_table(), get_checkpointer(), _get_pool(), initial_state_for_thread(), is_leaf_learned(), list_checkpoints(), list_leaf_checkpoints() (+9 more)

### Community 3 - "chat_service.py"
Cohesion: 0.12
Nodes (24): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `GET /v1/chats/{chat_id}` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth), patch, update_chat() (+16 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.10
Nodes (11): Console, The complete answer for this turn (authoritative copy)., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., Stop the live region (frame stays on screen) before an interrupt., End of the turn: freeze the final frame and close the region., TurnRenderer (+3 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.11
Nodes (18): Analytics, Authentication, Checkpoints & rollback, Data store (`data/`), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth), `GET /v1/auth/me` (auth), `GET /v1/chats/{chat_id}/checkpoints` (auth) (+10 more)

### Community 6 - "agent/graph.py"
Cohesion: 0.10
Nodes (33): langchain_core_messages, langchain_core_runnables, langgraph_graph, langgraph_graph_message, langgraph_types, pydantic, clear_pause(), is_pause_requested() (+25 more)

### Community 7 - "log_event"
Cohesion: 0.14
Nodes (30): bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request() (+22 more)

### Community 8 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 9 - "typing"
Cohesion: 0.17
Nodes (13): get_settings(), BaseSettings, Settings, Packet, argon2, argon2_exceptions, dataclasses, jwt (+5 more)

### Community 10 - "renderer.py"
Cohesion: 0.22
Nodes (7): io, rich_console, rich_markdown, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, CLI theme - one place for every terminal color/style used by the CLI. Keys are…, Unit tests for the live turn renderer (live rendering disabled in tests).

### Community 11 - "agentnode.py"
Cohesion: 0.11
Nodes (23): BaseMessage, concurrent_futures, agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation(), _is_turn_start() (+15 more)

### Community 12 - "file_io.py"
Cohesion: 0.13
Nodes (18): model_validator, edit_file(), EditFileArgs, Any, BaseModel, field_validator, Path, tool (+10 more)

### Community 13 - "HfLoadIsQuiet"
Cohesion: 0.15
Nodes (7): list, _FakeEncoded, _FakeModel, HfLoadIsQuiet, _install_fakes(), SentenceTransformer(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 14 - "test_context_memory.py"
Cohesion: 0.08
Nodes (23): build_execution_memory_index(), count_content_tokens(), empty_context_memory(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts. (+15 more)

### Community 15 - "postgres.py"
Cohesion: 0.11
Nodes (19): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, psycopg_types_json (+11 more)

### Community 16 - "subagent_node"
Cohesion: 0.17
Nodes (14): _calls_this_turn(), RunnableConfig, Count of human messages so far — increments once per new user message, so calls…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node(), _turn_number(), emit_subagent_event(), Any (+6 more)

### Community 17 - "extract_chunks.py"
Cohesion: 0.09
Nodes (30): Standalone learner LangGraph: load_session → extract_chunks → persist., Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., extract_chunks_node(), _normalize_chunk(), _parse_json_payload() (+22 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.22
Nodes (15): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+7 more)

### Community 19 - "idle_watcher.py"
Cohesion: 0.21
Nodes (12): asyncio, datetime, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, Background idle watcher: learn from chats idle for IDLE_SECONDS. (+4 more)

### Community 20 - "CurrentUser"
Cohesion: 0.24
Nodes (15): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+7 more)

### Community 21 - ".run_turn"
Cohesion: 0.14
Nodes (9): AgentRuntime, on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion. (+1 more)

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.16
Nodes (9): ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork(), Any, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already… (+1 more)

### Community 23 - "llm_client.py"
Cohesion: 0.16
Nodes (29): OpenAI, _build_messages(), _cache_key(), call_llm(), call_llm_stream(), _dump(), _estimated_usage(), _extract_cost() (+21 more)

### Community 24 - "test_subagents_integration.py"
Cohesion: 0.14
Nodes (8): Any, SubagentsService, tempfile, End-to-end tests for EVA subagent integration. Covers: registry catalog,…, TestCatalogAPI, TestProtocolConstants, TestRouting, TestSubagentRegistry

### Community 25 - "get_repos"
Cohesion: 0.24
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "app.py"
Cohesion: 0.16
Nodes (15): api_api_routes, configure_logging(), lifespan(), get_agent_app(), api_ws, chat_ws(), _handle_client_message(), Any (+7 more)

### Community 27 - "._commit"
Cohesion: 0.30
Nodes (5): _format_args(), Any, Record the planner's parsed decision after its streamed reasoning., _short(), Text

### Community 28 - "src/config.py"
Cohesion: 0.20
Nodes (7): dotenv, functools, pydantic_settings, BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 29 - "vector_store.py"
Cohesion: 0.14
Nodes (22): math, Soft-fail embed; returns None on any error., try_embed_text(), ensure_experience_dir(), Path, Learner / experience-system configuration., Safe experience retrieval for the main agent hot path., src_subagents_learner_agent_store (+14 more)

### Community 30 - "Repositories"
Cohesion: 0.13
Nodes (13): Any, Depends, get, summary(), Validate JWT for WebSocket handshake., Repositories, user_from_token(), decode_access_token() (+5 more)

### Community 31 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 32 - "TestAgentNodePrompt"
Cohesion: 0.25
Nodes (5): The contract lives in the system half and must not vary with turn state — that…, Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 33 - "checkpoints.py"
Cohesion: 0.26
Nodes (14): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), ChatCreateRequest, CheckpointOut (+6 more)

### Community 34 - "experience.py"
Cohesion: 0.36
Nodes (8): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., collections

### Community 35 - "set_subagent_callback"
Cohesion: 0.20
Nodes (7): contextvars, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback, TestSubagentStream

### Community 36 - "executor.py"
Cohesion: 0.21
Nodes (15): execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python…, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+7 more)

### Community 37 - "test_llm_logger.py"
Cohesion: 0.20
Nodes (8): src_utils, current_session_ids(), lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, chat/run/user/core ids from the ContextVar-bound agent session logger. Falls…, Tests for the LLM call recorder and its mock-replay cache key. No live Postgres…, TestLookupSoftFails, TestSessionIdentity

### Community 38 - "pathlib"
Cohesion: 0.09
Nodes (20): os, pathlib, scripts, socket, src_agent_nodes, sys, Focused checks for CLI-configurable agent runtime controls., Unit tests for the CLI theme definition. (+12 more)

### Community 39 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 40 - "test_llm_mock_mode.py"
Cohesion: 0.12
Nodes (13): src_models, fake_gateway(), create(), _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create., Captures every record the client emits instead of writing it anywhere. (+5 more)

### Community 41 - "bootstrap.py"
Cohesion: 0.18
Nodes (16): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), ensure_venv_on_path(), get_python_executable(), get_venv_python() (+8 more)

### Community 42 - "prompts/render.py"
Cohesion: 0.25
Nodes (9): _Node, _parse(), PromptRenderError, Exception, Generic conditional prompt renderer. Prompt templates are declarative: every…, Raised in strict mode when a template references an unknown variable., _render_node(), _subst() (+1 more)

### Community 43 - "_fmt"
Cohesion: 0.29
Nodes (7): _fmt(), Any, Serialize structured context for LLM prompts as TOON (not JSON)., Structured values are serialized as TOON, not JSON — measurably fewer tokens…, to_toon(), json.dumps(indent=2) was 2.6x more tokens for the same data., TestFormatting

### Community 44 - "db_setup.py"
Cohesion: 0.31
Nodes (8): ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main(), Idempotent Postgres setup for this project. Creates the target database (if…, Create the target database if it doesn't exist yet. `CREATE DATABASE` can't run…, Create every table/index the app needs, skipping ones that exist., LangGraph owns `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` — let its…

### Community 45 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 46 - "web_search.py"
Cohesion: 0.17
Nodes (14): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, BaseModel, field_validator (+6 more)

### Community 47 - "render"
Cohesion: 0.23
Nodes (5): Strip trailing spaces, collapse the blank-line runs left behind by dropped…, render(), _tidy(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 48 - "ChatPacketQueue"
Cohesion: 0.22
Nodes (4): ChatPacketQueue, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback).

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 52 - "FastAPI"
Cohesion: 0.33
Nodes (8): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel, FastAPI

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "embeddings.py"
Cohesion: 0.25
Nodes (10): hashlib, numpy, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy…, Deterministic hashing bag-of-words vectorizer (no ML dependencies). (+2 more)

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "user_memory.py"
Cohesion: 0.24
Nodes (10): Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update() (+2 more)

### Community 57 - "repositories/__init__.py"
Cohesion: 0.31
Nodes (8): utc_now_iso(), analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 60 - "test_cli_repl.py"
Cohesion: 0.22
Nodes (9): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, Unit tests for the CLI REPL: command parsing, step handling, interrupts, and…, TestHandleStep (+1 more)

### Community 61 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 62 - "route_from_agent"
Cohesion: 0.36
Nodes (3): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting

### Community 63 - "tools_service.py"
Cohesion: 0.23
Nodes (12): list_tools(), Any, Depends, get, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict() (+4 more)

### Community 64 - "test_prompt_render.py"
Cohesion: 0.36
Nodes (3): _eval_cond(), Tests for the declarative prompt renderer (src/prompts/render.py)., TestConditions

### Community 65 - "test_endpoints.py"
Cohesion: 0.19
Nodes (11): create_app(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API. (+3 more)

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 68 - "sys_info.py"
Cohesion: 0.25
Nodes (7): langchain_core_tools, platform, Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 69 - "llm_logger.py"
Cohesion: 0.11
Nodes (26): atexit, queue, register, _ensure_writer_started(), Path, _safe_chat_id(), _writer_loop(), _db_loop() (+18 more)

### Community 70 - "WebSocket chat session"
Cohesion: 0.25
Nodes (7): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session

### Community 71 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 72 - "_present"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.11
Nodes (17): _has_tool(), load_prompt(), Any, Path, Prompt loading for every agent and sub-agent in the project. One generic entry…, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, Whether any of `names` is in the available tool list. Capability rules are…, Path (+9 more)

### Community 75 - "list_checkpoint_tree"
Cohesion: 0.25
Nodes (8): has_pending_interrupt(), _infer_node(), list_checkpoint_tree(), _node_from_metadata(), Best-effort label for "which node just wrote this checkpoint" — there is no…, Prefer LangGraph checkpoint metadata (authoritative node writes)., Like `list_checkpoints`, plus `node`, `is_leaf`, and whether the tip checkpoint…, Return the pending `Interrupt` for this thread's current tip, or None.

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 89 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 90 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 92 - "text_truncate.py"
Cohesion: 0.43
Nodes (6): _record_tool_result(), Any, Shared stringify + truncate helpers for AIMessage previews., stringify_for_preview(), truncate_for_aimessage(), truncate_text()

### Community 96 - "build_config"
Cohesion: 0.20
Nodes (8): object, build_config(), get_thread_state(), RunnableConfig, Config that resumes / time-travels from a specific checkpoint., Return channel_values for the tip checkpoint, or None., rewind_config(), TestRuntimeControls

### Community 98 - "decompose_query"
Cohesion: 0.50
Nodes (4): decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

### Community 99 - "parse_command"
Cohesion: 0.20
Nodes (6): parse_command(), interrupt_step(), TestParseCommand, TestRunTurnInteractive, fake_run_turn(), first()

### Community 100 - "._write_and_read"
Cohesion: 0.19
Nodes (6): build_record(), _utc_now(), Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 101 - "api_routes/preferences.py"
Cohesion: 0.25
Nodes (9): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, PreferencesService (+1 more)

### Community 102 - "count_tokens"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 103 - "require_user"
Cohesion: 0.15
Nodes (16): create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get, post (+8 more)

### Community 104 - "json"
Cohesion: 0.40
Nodes (4): json, DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional…

### Community 105 - "prompt_change/render.py"
Cohesion: 0.11
Nodes (18): argparse, re, requests, _eval_cond(), _fmt(), _Node, _parse(), _present() (+10 more)

### Community 107 - "truncate_value"
Cohesion: 0.32
Nodes (4): Recursively truncate oversized strings in payloads., truncate_value(), _utc_now(), TestTruncate

### Community 108 - "Any"
Cohesion: 0.22
Nodes (9): _filter_checkpoint_tree(), _is_redundant_checkpoint(), _message_content(), _message_role(), PostgresSaver, Any, Drop no-op rows LangGraph adds when interrupt() fires without changing messages…, PostgresSaver that also mirrors new messages into the `messages` table. (+1 more)

### Community 109 - "repl.py"
Cohesion: 0.12
Nodes (34): api_db_repositories, PreferencesRepository, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_panel, rich_prompt (+26 more)

## Knowledge Gaps
- **32 isolated node(s):** `$schema`, `plugin`, `graphify`, `Layout`, ``POST /v1/auth/login` (public)` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 479 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `parse_command`, `renderer.py`, `repl.py`, `._commit`, `test_cli_repl.py`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `checkpoints.py`, `EVA Agent API — Reference & How to Use`, `typing`, `ChatPacketQueue`, `.attach`, `.run_turn`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `checkpoints.py`, `experience.py`, `chat_service.py`, `api_routes/preferences.py`, `require_user`, `api_routes/auth.py`, `FastAPI`, `get_repos`, `Repositories`, `tools_service.py`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._