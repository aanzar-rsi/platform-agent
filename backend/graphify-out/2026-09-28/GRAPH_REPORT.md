# Graph Report - backend  (2026-09-28)

## Corpus Check
- 156 files · ~83,023 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 27 file(s) not represented in the graph (top: .jsonl 26, .example 1)

## Summary
- 1785 nodes · 4562 edges · 117 communities (93 shown, 24 thin omitted)
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
- pydantic
- users.py
- update_context_memory
- ChatPacketQueue
- HfLoadIsQuiet
- extract_chunks.py
- api_routes/auth.py
- test_experience_system.py
- TestSubagentNode
- AgentRuntime
- ChatRuntimeManager
- llm_client.py
- api_routes/files.py
- api_routes/memory.py
- endpoint.py
- text_truncate.py
- test_endpoints.py
- CurrentUser
- log_event
- now.py
- require_user
- CheckpointService
- context_selector_node
- agentnode_prompt_loader
- executor.py
- context_manager.py
- chat_runtime_manager.py
- Platform Agent Codebase Documentation
- .run_turn
- main.py
- vector_store.py
- test_context_memory.py
- TestSubagentRegistry
- _present
- web_search.py
- SessionRepository
- truncate_value
- retrieve_experiences
- field_validator
- embeddings.py
- control.py
- Multi-User Agentic AI Platform — Database Design
- ReadFileArgs
- graphify.js
- build_embed_text
- ._commit
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- GitHubRepoDownloader
- current_session_ids
- route_from_agent
- Detailed Subsystem Reference
- subagentnode.py
- test_cli_repl.py
- ws.py
- prompt_loader.py
- Tools: `tool_node`
- llm_logger.py
- BackgroundIdleWatcher
- render
- experience.py
- load_prompt
- AGENTS.md
- fetch_all
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- sys_info.py
- fetch_one
- TestAgentRuntimeFanout
- test_prompt_render.py
- build_cache_key
- agent_runtime.py
- health.py
- Planner: `agent_node`
- paths.py
- repl.py
- ._write_and_read
- execute
- _eval_cond
- TestSchemaStatementsAreIdempotent
- WebSocket chat session
- mcp_runtime.py
- agent/graph.py
- _FakeEncoded
- Settings
- subagent_gate_node
- TestMainDispatch
- list_subagents
- generate_tree
- TestDbSetupLive
- TestTheme
- TestCreateUser

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
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Memory Model` --references--> `PlanExecuteState`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/state.py

## Import Cycles
- None detected.

## Communities (117 total, 24 thin omitted)

### Community 0 - "typing"
Cohesion: 0.14
Nodes (18): get_prefs(), put_prefs(), Any, Depends, get, put, api_db_repositories, McpUpdateRequest (+10 more)

### Community 1 - ".mock_mode"
Cohesion: 0.09
Nodes (19): _Chunk, _Completion, fake_gateway(), create(), _MockBase, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json… (+11 more)

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.07
Nodes (49): 7. PostgreSQL, Repositories, and Checkpoints, Checkpointer function map, Database troubleshooting, Persistence and Checkpoints, PostgreSQL responsibilities, langgraph_checkpoint_postgres, object, build_config() (+41 more)

### Community 3 - "chat_service.py"
Cohesion: 0.12
Nodes (32): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get (+24 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.12
Nodes (9): Console, Stop the live region (frame stays on screen) before an interrupt., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., TurnRenderer, make_console(), Console (+1 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.08
Nodes (23): Analytics, Authentication, Chats, Checkpoints & rollback, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth) (+15 more)

### Community 6 - "repositories/mcp.py"
Cohesion: 0.22
Nodes (12): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+4 more)

### Community 7 - "make_console"
Cohesion: 0.23
Nodes (8): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestPromptForInterrupt

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "Repositories"
Cohesion: 0.10
Nodes (16): Any, Depends, get, summary(), list_tools(), Any, Depends, get (+8 more)

### Community 10 - "postgres.py"
Cohesion: 0.13
Nodes (18): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute() (+10 more)

### Community 11 - "agentnode.py"
Cohesion: 0.11
Nodes (22): BaseMessage, 1. End-to-End Turn Execution, Functions to start with when tracing a turn, Main agent loop, agent_node(), _on_token(), _coerce_int(), _extract_tag() (+14 more)

### Community 12 - "pydantic"
Cohesion: 0.23
Nodes (14): File tools, pydantic, edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management., Read content from a text-based file. Supports optional line-range slicing via… (+6 more)

### Community 13 - "users.py"
Cohesion: 0.26
Nodes (11): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+3 more)

### Community 14 - "update_context_memory"
Cohesion: 0.06
Nodes (31): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, build_execution_memory_index(), count_content_tokens(), empty_context_memory(), _entry_tokens() (+23 more)

### Community 15 - "ChatPacketQueue"
Cohesion: 0.12
Nodes (13): Envelope (all messages), ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., 6. WebSocket Runtime, Queues, and Recovery, Add a WebSocket event (+5 more)

### Community 16 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 17 - "extract_chunks.py"
Cohesion: 0.18
Nodes (18): Full learner sequence, Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks., _utc_now() (+10 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "test_experience_system.py"
Cohesion: 0.09
Nodes (21): datetime, learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions() (+13 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - "AgentRuntime"
Cohesion: 0.15
Nodes (5): AgentRuntime, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, Thin re-export — stream bridging lives in agent_runtime for cohesion., Event

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.15
Nodes (12): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+4 more)

### Community 23 - "llm_client.py"
Cohesion: 0.11
Nodes (38): 8. Observability, Logs, and LLM Replay, Gateway behavior, LLM call logger and replay cache, Recommended debugging workflow, OpenAI, emit_usage(), Any, _build_messages() (+30 more)

### Community 24 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 25 - "api_routes/memory.py"
Cohesion: 0.24
Nodes (14): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+6 more)

### Community 26 - "endpoint.py"
Cohesion: 0.25
Nodes (9): api_ws, chat_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject(), WebSocket protocol helpers. (+1 more)

### Community 27 - "text_truncate.py"
Cohesion: 0.53
Nodes (5): Any, Shared stringify + truncate helpers for AIMessage previews., stringify_for_preview(), truncate_for_aimessage(), truncate_text()

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "CurrentUser"
Cohesion: 0.25
Nodes (9): CurrentUser, McpCreateRequest, model_validator, connection_log(), McpService, public_server(), Any, test_invalid_servers_remain_registered_but_never_connected() (+1 more)

### Community 30 - "log_event"
Cohesion: 0.14
Nodes (30): Agent trace logger, bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_error(), log_event(), log_llm_request() (+22 more)

### Community 31 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 32 - "require_user"
Cohesion: 0.18
Nodes (26): connect_server(), create_server(), delete_server(), disconnect_server(), import_servers(), list_servers(), Any, delete (+18 more)

### Community 33 - "CheckpointService"
Cohesion: 0.29
Nodes (11): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+3 more)

### Community 34 - "context_selector_node"
Cohesion: 0.21
Nodes (9): langchain_core_runnables, note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, _coerce_token(), context_selector_node(), RunnableConfig, Context selector node — loads a token window from execution_memory into…, log_context_select() (+1 more)

### Community 35 - "agentnode_prompt_loader"
Cohesion: 0.18
Nodes (10): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, Add a prompt block, Add an API resource, Add an internal tool, Practical prompt-debug method, System versus user prompt, agentnode_prompt_loader() (+2 more)

### Community 36 - "executor.py"
Cohesion: 0.18
Nodes (18): Command execution tools, get_python_executable(), Return the project venv Python when available, otherwise sys.executable., execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any (+10 more)

### Community 37 - "context_manager.py"
Cohesion: 0.29
Nodes (9): _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM., Check how much of a model's input context window the prompt consumes. Returns…, Check how much of a model's output context window a response consumes. Returns… (+1 more)

### Community 38 - "chat_runtime_manager.py"
Cohesion: 0.22
Nodes (7): argon2, argon2_exceptions, asyncio, dataclasses, jwt, secrets, clear_pause()

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.11
Nodes (17): CLI, Commands, Entrypoints, Environment, Flow, LLM Client, Observability, and Replay, Logging and mock replay, Main prompt contract (+9 more)

### Community 40 - ".run_turn"
Cohesion: 0.10
Nodes (22): on_subagent_event(), _emit_turn_complete(), Any, _truncate(), contextvars, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback() (+14 more)

### Community 41 - "main.py"
Cohesion: 0.23
Nodes (11): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), get_venv_python(), get_venv_site_packages(), Path (+3 more)

### Community 42 - "vector_store.py"
Cohesion: 0.15
Nodes (18): Step 3: persist and index, logging, math, ensure_experience_dir(), Path, persist_node(), Persist extracted chunks into the experience store., Safe experience retrieval for the main agent hot path. (+10 more)

### Community 43 - "test_context_memory.py"
Cohesion: 0.06
Nodes (39): dotenv, functools, json, os, pathlib, pydantic_settings, re, scripts (+31 more)

### Community 45 - "_present"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 46 - "web_search.py"
Cohesion: 0.16
Nodes (16): ddgs, ensure_venv_on_path(), Prepend the project venv site-packages directory to sys.path., _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any (+8 more)

### Community 47 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, _row_to_chat(), SessionRepository, _valid_uuid(), psycopg_types_json

### Community 48 - "truncate_value"
Cohesion: 0.47
Nodes (3): Recursively truncate oversized strings in payloads., truncate_value(), TestTruncate

### Community 49 - "retrieve_experiences"
Cohesion: 0.21
Nodes (9): Retrieval in the main agent, Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., format_experiences_for_prompt(), Any, Return top-k experience chunks. Never raises — returns [] on any failure or…, retrieve_experiences() (+1 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "embeddings.py"
Cohesion: 0.15
Nodes (16): 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, Step 2: extract reusable advice, hashlib, numpy, _embed_numpy(), embed_text(), embed_texts() (+8 more)

### Community 52 - "control.py"
Cohesion: 0.21
Nodes (11): is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each…, Call at the very top of a node, before any side effects. Returns the…, True when the graph tip has a pending interrupt raised at `node`. (+3 more)

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, model_validator, ReadFileArgs, SearchFileArgs

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "build_embed_text"
Cohesion: 0.33
Nodes (4): build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., TestEmbedKeys

### Community 57 - "._commit"
Cohesion: 0.18
Nodes (6): emit_tag(), _format_args(), Any, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short()

### Community 60 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

### Community 61 - "current_session_ids"
Cohesion: 0.50
Nodes (3): current_session_ids(), chat/run/user/core ids from the ContextVar-bound agent session logger. Falls…, TestSessionIdentity

### Community 62 - "route_from_agent"
Cohesion: 0.27
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "Detailed Subsystem Reference"
Cohesion: 0.25
Nodes (8): 4. Internal Tool Subsystem, 5. API Layer and Service Boundaries, Detailed Subsystem Reference, Information and planning tools, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

### Community 64 - "subagentnode.py"
Cohesion: 0.13
Nodes (20): Any, SubagentsService, Sub-agents: `subagent_node` and gate, _calls_this_turn(), RunnableConfig, Sub-agent node — delegates a focused task to a specialised child agent. Reads…, Count of human messages so far — increments once per new user message, so calls…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by… (+12 more)

### Community 65 - "test_cli_repl.py"
Cohesion: 0.10
Nodes (16): io, rich_console, rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, parse_command() (+8 more)

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "prompt_loader.py"
Cohesion: 0.22
Nodes (12): Major prompt functions, _has_tool(), _load_module(), _Node, _parse(), Prompt rendering and loading for every agent and sub-agent in the project. One…, Load a versioned reusable prompt module., Whether any of `names` is in the available tool list. Capability rules are… (+4 more)

### Community 68 - "Tools: `tool_node`"
Cohesion: 0.23
Nodes (11): Tools: `tool_node`, Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch() (+3 more)

### Community 69 - "llm_logger.py"
Cohesion: 0.09
Nodes (29): atexit, queue, register, _ensure_writer_started(), Path, _safe_chat_id(), _writer_loop(), _db_loop() (+21 more)

### Community 70 - "BackgroundIdleWatcher"
Cohesion: 0.14
Nodes (9): Experience API view, Idle scheduling and branch handling, Learner graph, Learning Agent and Experience System, Step 1: load trajectory, BackgroundIdleWatcher, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread. (+1 more)

### Community 71 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 72 - "experience.py"
Cohesion: 0.24
Nodes (13): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., collections (+5 more)

### Community 73 - "load_prompt"
Cohesion: 0.14
Nodes (11): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —…, These were {{ }} for str.format(); the renderer would send them literally to… (+3 more)

### Community 75 - "fetch_all"
Cohesion: 0.31
Nodes (9): fetch_all(), get_connection(), Any, Connection, _iso(), MemoryRepository, Any, _row_to_entry() (+1 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "sys_info.py"
Cohesion: 0.25
Nodes (7): langchain_core_tools, platform, Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 89 - "fetch_one"
Cohesion: 0.38
Nodes (4): fetch_one(), AuthSessionRepository, _iso(), Any

### Community 90 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 91 - "test_prompt_render.py"
Cohesion: 0.20
Nodes (11): _fmt(), PromptRenderError, Any, Exception, Serialize structured prompt context as TOON., Raised in strict mode when a template references an unknown variable., replace(), to_toon() (+3 more)

### Community 92 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 94 - "agent_runtime.py"
Cohesion: 0.21
Nodes (13): api_api_routes, create_app(), get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1). (+5 more)

### Community 96 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 97 - "Planner: `agent_node`"
Cohesion: 0.40
Nodes (3): Planner: `agent_node`, Topology, Close the live region and print the final answer exactly once.

### Community 98 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 99 - "repl.py"
Cohesion: 0.12
Nodes (33): PreferencesRepository, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, PromptSession, rich_prompt, rich_table (+25 more)

### Community 100 - "._write_and_read"
Cohesion: 0.19
Nodes (6): build_record(), _utc_now(), Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 101 - "execute"
Cohesion: 0.29
Nodes (4): execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _load(), Any

### Community 104 - "WebSocket chat session"
Cohesion: 0.33
Nodes (6): Client → server, Connect, Example messages, Minimal client flow, Server → client, WebSocket chat session

### Community 105 - "mcp_runtime.py"
Cohesion: 0.06
Nodes (23): available_mcp_tools(), call_mcp_tool(), McpConnection, McpRuntime, McpTool, Any, Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, _mcp_tools_from_metadata() (+15 more)

### Community 106 - "agent/graph.py"
Cohesion: 0.16
Nodes (17): Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, State, langchain_core_messages, langgraph_graph, langgraph_graph_message, langgraph_types (+9 more)

### Community 107 - "_FakeEncoded"
Cohesion: 0.33
Nodes (3): list, _FakeEncoded, _FakeModel

### Community 108 - "Settings"
Cohesion: 0.33
Nodes (4): get_settings(), BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 109 - "subagent_gate_node"
Cohesion: 0.40
Nodes (4): Add a planner-callable sub-agent, Current Extension Points and Limits, Subagent confirmation gate — runs unconditionally right after subagent_node,…, subagent_gate_node()

### Community 112 - "list_subagents"
Cohesion: 0.50
Nodes (4): list_subagents(), Any, Depends, get

### Community 113 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

## Knowledge Gaps
- **43 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 505 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CurrentUser` connect `CurrentUser` to `health.py`, `CheckpointService`, `require_user`, `chat_service.py`, `typing`, `experience.py`, `Repositories`, `mcp_runtime.py`, `list_subagents`, `api_routes/auth.py`, `api_routes/memory.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `get_repos()` connect `require_user` to `typing`, `CheckpointService`, `chat_service.py`, `repl.py`, `chat_runtime_manager.py`, `Repositories`, `mcp_runtime.py`, `api_routes/auth.py`, `ChatRuntimeManager`, `api_routes/memory.py`, `endpoint.py`, `agent_runtime.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `TurnRenderer` connect `TurnRenderer` to `test_cli_repl.py`, `Planner: `agent_node``, `repl.py`, `make_console`, `.run_turn`, `._commit`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 38 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._