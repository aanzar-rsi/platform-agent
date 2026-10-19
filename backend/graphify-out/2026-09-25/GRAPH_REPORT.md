# Graph Report - v2  (2026-09-24)

## Corpus Check
- 158 files · ~78,517 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: .jsonl 15, .example 1)

## Summary
- 1746 nodes · 4395 edges · 100 communities (82 shown, 18 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 407 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Repositories
- .mock_mode
- postgres_checkpointer.py
- chat_service.py
- TurnRenderer
- EVA Agent API — Reference & How to Use
- postgres.py
- bind_session_logger
- TestAgentNodePrompt
- tools_service.py
- test_context_memory.py
- agentnode.py
- file_io.py
- log_event
- update_context_memory
- ChatPacketQueue
- test_embeddings_quiet.py
- learner_agent/graph.py
- api_routes/auth.py
- test_experience_system.py
- TestSubagentNode
- .run_turn
- ChatRuntimeManager
- llm_client.py
- tool_node
- get_repos
- typing
- control.py
- test_endpoints.py
- vector_store.py
- embeddings.py
- now.py
- CurrentUser
- checkpoints.py
- context_selector_node
- agentnode_prompt_loader
- Tools: `tool_node`
- count_tokens
- unittest_mock
- FilePickerService
- extract_chunks.py
- bootstrap.py
- db_setup.py
- pathlib
- test_subagents_integration.py
- prompts/render.py
- web_search.py
- main.py
- truncate_value
- retrieve_experiences
- executor.py
- test_cli_repl.py
- Detailed Subsystem Reference
- Multi-User Agentic AI Platform — Database Design
- ReadFileArgs
- graphify.js
- tools/__init__.py
- decomposer.py
- opencode.json
- health.py
- .test_public_signatures_stayed_stub_compatible
- test_llm_logger.py
- route_from_agent
- get_subagents
- ws.py
- decompose_query
- llm_logger.py
- BackgroundIdleWatcher
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
- TestAgentRuntimeFanout
- WebSearchArgs
- agent_runtime.py
- learn_session
- unittest
- repl.py
- ._write_and_read
- EVA Agent Codebase Documentation
- test_db_setup.py
- prompt_change/render.py
- agent/graph.py
- require_user

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 80 edges
2. `Repositories` - 61 edges
3. `TurnRenderer` - 59 edges
4. `require_user()` - 49 edges
5. `log_event()` - 43 edges
6. `get_repos()` - 41 edges
7. `call_llm()` - 39 edges
8. `update_context_memory()` - 30 edges
9. `agent_node()` - 30 edges
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

## Communities (100 total, 18 thin omitted)

### Community 0 - "Repositories"
Cohesion: 0.10
Nodes (19): Any, Depends, get, summary(), get_prefs(), put_prefs(), Any, Depends (+11 more)

### Community 1 - ".mock_mode"
Cohesion: 0.19
Nodes (7): _Chunk, _Completion, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, TestMockModeOn, _Usage

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.05
Nodes (62): 7. PostgreSQL, Repositories, and Checkpoints, Checkpointer function map, Database troubleshooting, PostgreSQL responsibilities, contextlib, langgraph_checkpoint_postgres, object, psycopg (+54 more)

### Community 3 - "chat_service.py"
Cohesion: 0.14
Nodes (27): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get (+19 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.05
Nodes (27): _format_args(), Any, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., Draws activity + streamed output for a single agent turn. (+19 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.07
Nodes (29): Analytics, Authentication, Chats, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth) (+21 more)

### Community 6 - "postgres.py"
Cohesion: 0.06
Nodes (56): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, hash_password(), needs_rehash(), verify_password(), analytics_dir(), analytics_events_file() (+48 more)

### Community 7 - "bind_session_logger"
Cohesion: 0.18
Nodes (10): bind_session_logger(), flush_pending_logs(), get_session_logger(), Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger(), A slow/stalled write to one chat's file must not delay log() calls for the SAME…, TestAsyncWriterDoesNotBlockCaller (+2 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "tools_service.py"
Cohesion: 0.25
Nodes (11): list_tools(), Any, Depends, get, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict() (+3 more)

### Community 10 - "test_context_memory.py"
Cohesion: 0.11
Nodes (16): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+8 more)

### Community 11 - "agentnode.py"
Cohesion: 0.09
Nodes (28): BaseMessage, 1. End-to-End Turn Execution, Agent runtime event conversion, Functions to start with when tracing a turn, Main agent loop, concurrent_futures, agent_node(), _on_token() (+20 more)

### Community 12 - "file_io.py"
Cohesion: 0.25
Nodes (13): File tools, edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management., Read content from a text-based file. Supports optional line-range slicing via…, Make targeted edits to a text file by replacing an exact string match. Finds… (+5 more)

### Community 13 - "log_event"
Cohesion: 0.25
Nodes (20): json, os, log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response() (+12 more)

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "ChatPacketQueue"
Cohesion: 0.14
Nodes (10): Envelope (all messages), ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., 6. WebSocket Runtime, Queues, and Recovery, Add a WebSocket event (+2 more)

### Community 16 - "test_embeddings_quiet.py"
Cohesion: 0.15
Nodes (8): list, src_models, _FakeEncoded, _FakeModel, HfLoadIsQuiet, _install_fakes(), The HF embedding backend must load quietly: no 'Loading weights' tqdm bar, no…, Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 17 - "learner_agent/graph.py"
Cohesion: 0.19
Nodes (16): Step 3: persist and index, Standalone learner LangGraph: load_session → extract_chunks → persist., _latest_human(), load_session_node(), _message_line(), Any, Load chat trajectory from the main agent checkpointer., _slim_history() (+8 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "test_experience_system.py"
Cohesion: 0.12
Nodes (15): asyncio, datetime, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, Background idle watcher: learn from chats idle for IDLE_SECONDS. (+7 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - ".run_turn"
Cohesion: 0.13
Nodes (10): AgentRuntime, on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion. (+2 more)

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.13
Nodes (15): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+7 more)

### Community 23 - "llm_client.py"
Cohesion: 0.14
Nodes (33): Gateway behavior, LLM call logger and replay cache, OpenAI, emit_usage(), Any, _build_messages(), _cache_key(), call_llm() (+25 more)

### Community 24 - "tool_node"
Cohesion: 0.18
Nodes (10): Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, Topology, empty_context_memory(), RunnableConfig, tool_node() (+2 more)

### Community 25 - "get_repos"
Cohesion: 0.24
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "typing"
Cohesion: 0.12
Nodes (22): api_api_routes, pick_files(), post, Validate JWT for WebSocket handshake., user_from_token(), decode_access_token(), Any, FilePickRequest (+14 more)

### Community 27 - "control.py"
Cohesion: 0.20
Nodes (12): clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each…, Call at the very top of a node, before any side effects. Returns the… (+4 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "vector_store.py"
Cohesion: 0.15
Nodes (18): math, ensure_experience_dir(), Path, Learner / experience-system configuration., Safe experience retrieval for the main agent hot path., src_subagents_learner_agent_store, append_chunks(), get_chunk_by_id() (+10 more)

### Community 30 - "embeddings.py"
Cohesion: 0.15
Nodes (16): 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, Step 2: extract reusable advice, hashlib, numpy, _embed_numpy(), embed_text(), embed_texts() (+8 more)

### Community 31 - "now.py"
Cohesion: 0.22
Nodes (7): calendar, GetCurrentDatetimeInfoArgs, BaseModel, field_validator, Internal tool for getting comprehensive date and time information in the user's…, tzlocal, zoneinfo

### Community 32 - "CurrentUser"
Cohesion: 0.24
Nodes (15): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+7 more)

### Community 33 - "checkpoints.py"
Cohesion: 0.31
Nodes (11): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+3 more)

### Community 34 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "agentnode_prompt_loader"
Cohesion: 0.13
Nodes (16): 3. Prompt Rendering Deep Dive, Major prompt functions, Practical prompt-debug method, System versus user prompt, agentnode_prompt_loader(), _has_tool(), _load_module(), load_prompt() (+8 more)

### Community 36 - "Tools: `tool_node`"
Cohesion: 0.30
Nodes (12): Command execution tools, Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), Any, tool, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+4 more)

### Community 37 - "count_tokens"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 38 - "unittest_mock"
Cohesion: 0.24
Nodes (5): ModuleType, Tests for the main.py boot dispatch (API server vs interactive agent CLI)., TestDevPyRemoved, TestMainDispatch, unittest_mock

### Community 39 - "FilePickerService"
Cohesion: 0.36
Nodes (4): FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., HTTP API and WebSocket Runtime, REST resources

### Community 40 - "extract_chunks.py"
Cohesion: 0.22
Nodes (11): Full learner sequence, build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any (+3 more)

### Community 41 - "bootstrap.py"
Cohesion: 0.33
Nodes (9): ensure_venv_on_path(), get_python_executable(), get_venv_python(), get_venv_site_packages(), Path, Ensure the project .venv is used by the current Python process., Prepend the project venv site-packages directory to sys.path., Return the project venv Python when available, otherwise sys.executable. (+1 more)

### Community 42 - "db_setup.py"
Cohesion: 0.31
Nodes (8): ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main(), Idempotent Postgres setup for this project. Creates the target database (if…, Create the target database if it doesn't exist yet. `CREATE DATABASE` can't run…, Create every table/index the app needs, skipping ones that exist., LangGraph owns `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` — let its…

### Community 43 - "pathlib"
Cohesion: 0.16
Nodes (11): dotenv, functools, pathlib, pydantic_settings, scripts, create_user(), Create one application user and their required onboarding records. Edit the…, Create the user, credentials, and preferences in one transaction. (+3 more)

### Community 44 - "test_subagents_integration.py"
Cohesion: 0.10
Nodes (12): Any, SubagentsService, WebSocket protocol helpers., emit_subagent_event(), Any, tempfile, End-to-end tests for EVA subagent integration. Covers: registry catalog,…, TestCatalogAPI (+4 more)

### Community 45 - "prompts/render.py"
Cohesion: 0.07
Nodes (28): _eval_cond(), _fmt(), _Node, _parse(), _present(), PromptRenderError, Any, Exception (+20 more)

### Community 46 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 47 - "main.py"
Cohesion: 0.36
Nodes (7): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), Re-launch this process with the project venv Python when needed., reexec_with_venv_if_available()

### Community 48 - "truncate_value"
Cohesion: 0.18
Nodes (8): Agent trace logger, Path, Recursively truncate oversized strings in payloads., Append-only JSONL writer for one chat session., SessionLogger, truncate_value(), _utc_now(), TestTruncate

### Community 49 - "retrieve_experiences"
Cohesion: 0.24
Nodes (7): Retrieval in the main agent, Standalone learner agent: extract experience chunks from idle chats., format_experiences_for_prompt(), Any, Return top-k experience chunks. Never raises — returns [] on any failure or…, retrieve_experiences(), TestRetrieveSoftFail

### Community 50 - "executor.py"
Cohesion: 0.18
Nodes (10): BashArgs, _check_blacklist(), _find_executable(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs, Internal tools for executing Bash commands, PowerShell commands, and Python… (+2 more)

### Community 51 - "test_cli_repl.py"
Cohesion: 0.23
Nodes (7): io, rich_console, parse_command(), Unit tests for the live turn renderer (live rendering disabled in tests)., Unit tests for the CLI REPL: command parsing, step handling, interrupts, and…, TestParseCommand, types

### Community 52 - "Detailed Subsystem Reference"
Cohesion: 0.25
Nodes (8): 10. Safe Extension Guide, 5. API Layer and Service Boundaries, 8. Observability, Logs, and LLM Replay, Add a prompt block, Add an API resource, Add an internal tool, Detailed Subsystem Reference, Recommended debugging workflow

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): model_validator, EditFileArgs, BaseModel, field_validator, ReadFileArgs, SearchFileArgs

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "tools/__init__.py"
Cohesion: 0.13
Nodes (18): langchain_core_tools, platform, Internal tools package for the agent., Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info() (+10 more)

### Community 57 - "decomposer.py"
Cohesion: 0.50
Nodes (3): DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional…

### Community 59 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 61 - "test_llm_logger.py"
Cohesion: 0.11
Nodes (14): src_utils, build_cache_key(), current_session_ids(), lookup_cached_response(), Stable hash of everything that can change the answer. Fields are length-…, Most recent successful, non-replayed call with this exact key. Global across…, chat/run/user/core ids from the ContextVar-bound agent session logger. Falls…, Tests for the LLM call recorder and its mock-replay cache key. No live Postgres… (+6 more)

### Community 62 - "route_from_agent"
Cohesion: 0.36
Nodes (3): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting

### Community 64 - "get_subagents"
Cohesion: 0.20
Nodes (11): Add a planner-callable sub-agent, Current Extension Points and Limits, Sub-agents: `subagent_node` and gate, Subagent confirmation gate — runs unconditionally right after subagent_node,…, subagent_gate_node(), get_subagents(), Catalog of sub-agents that meta agents main planner can delegate a task to.…, Describes one planner-callable sub-agent. (+3 more)

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 68 - "decompose_query"
Cohesion: 0.20
Nodes (10): 4. Internal Tool Subsystem, Information and planning tools, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…, get_current_datetime_info(), Any (+2 more)

### Community 69 - "llm_logger.py"
Cohesion: 0.15
Nodes (21): atexit, queue, _ensure_writer_started(), _safe_chat_id(), _writer_loop(), build_record(), _db_loop(), _db_params() (+13 more)

### Community 70 - "BackgroundIdleWatcher"
Cohesion: 0.12
Nodes (12): CLI, Commands, Experience API view, Flow, Idle scheduling and branch handling, Learner graph, Learning Agent and Experience System, Step 1: load trajectory (+4 more)

### Community 72 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.15
Nodes (10): Path, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —…, These were {{ }} for str.format(); the renderer would send them literally to…, _strip_comments() (+2 more)

### Community 75 - "test_llm_mock_mode.py"
Cohesion: 0.12
Nodes (13): fake_gateway(), create(), _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create., Captures every record the client emits instead of writing it anywhere., _Raw (+5 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 90 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 91 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 94 - "agent_runtime.py"
Cohesion: 0.14
Nodes (20): create_app(), get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., ensure_client_path() (+12 more)

### Community 96 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 97 - "unittest"
Cohesion: 0.33
Nodes (3): Unit tests for the CLI theme definition., TestTheme, unittest

### Community 99 - "repl.py"
Cohesion: 0.05
Nodes (60): api_db_repositories, PreferencesRepository, contextvars, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, PromptSession (+52 more)

### Community 100 - "._write_and_read"
Cohesion: 0.18
Nodes (7): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall

### Community 102 - "EVA Agent Codebase Documentation"
Cohesion: 0.12
Nodes (15): Entrypoints, Environment, EVA Agent Codebase Documentation, LLM Client, Observability, and Replay, Logging and mock replay, Main prompt contract, Memory Model, Persistence and Checkpoints (+7 more)

### Community 103 - "test_db_setup.py"
Cohesion: 0.15
Nodes (6): skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 105 - "prompt_change/render.py"
Cohesion: 0.11
Nodes (18): argparse, re, requests, _eval_cond(), _fmt(), _Node, _parse(), _present() (+10 more)

### Community 106 - "agent/graph.py"
Cohesion: 0.10
Nodes (33): State, langchain_core_messages, langchain_core_runnables, langgraph_graph, langgraph_graph_message, langgraph_types, pydantic, note_text_from_resume() (+25 more)

### Community 112 - "require_user"
Cohesion: 0.17
Nodes (15): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., list_subagents() (+7 more)

## Knowledge Gaps
- **43 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 496 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **18 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `test_cli_repl.py`, `repl.py`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `agentnode_prompt_loader()` connect `agentnode_prompt_loader` to `EVA Agent Codebase Documentation`, `TestAgentNodePrompt`, `test_prompt_templates.py`, `test_context_memory.py`, `agentnode.py`, `test_subagents_integration.py`, `test_experience_system.py`, `Detailed Subsystem Reference`, `tool_node`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `Repositories`, `checkpoints.py`, `chat_service.py`, `tools_service.py`, `require_user`, `api_routes/auth.py`, `get_repos`, `typing`, `health.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._