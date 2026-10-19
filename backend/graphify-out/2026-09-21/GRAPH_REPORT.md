# Graph Report - v2  (2026-09-21)

## Corpus Check
- 154 files · ~55,283 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: .jsonl 10, .example 1)

## Summary
- 1597 nodes · 3914 edges · 102 communities (80 shown, 22 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 210 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- fetch_one
- .mock_mode
- postgres_checkpointer.py
- get_repos
- TurnRenderer
- EVA Agent API — Reference & How to Use
- agent/graph.py
- bind_session_logger
- update_context_memory
- TestSchemaStatementsAreIdempotent
- pathlib
- agentnode.py
- make_console
- HfLoadIsQuiet
- test_context_memory.py
- test_subagents_integration.py
- subagentnode.py
- extract_chunks.py
- api_routes/auth.py
- edit_file
- chat_runtime_manager.py
- agent_runtime.py
- ChatRuntimeManager
- llm_client.py
- CurrentUser
- api_routes/memory.py
- typing
- renderer.py
- src/config.py
- vector_store.py
- Repositories
- idle_watcher.py
- agentnode_prompt_loader
- checkpoints.py
- require_user
- set_subagent_callback
- executor.py
- TestTemplateContracts
- test_db_setup.py
- api_routes/files.py
- _Raw
- bootstrap.py
- list_experiences
- _FakeEncoded
- parse_command
- context_selector_node
- web_search.py
- prompts/render.py
- ChatPacketQueue
- .test_resumes_after_interrupt
- field_validator
- TestSubagentNode
- paths.py
- Multi-User Agentic AI Platform — Database Design
- embeddings.py
- graphify.js
- user_memory.py
- logging
- opencode.json
- TestMainDispatch
- TestTheme
- GitHubRepoDownloader
- TestVectorStoreRoundtrip
- tools_service.py
- TestAgentRuntimeFanout
- test_endpoints.py
- ws.py
- learn_session
- system_info
- llm_logger.py
- Any
- generate_tree
- ReadFileArgs
- TestAgentNodePrompt
- AGENTS.md
- retrieve.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- current_session_ids
- main.py
- log_event
- ._write_and_read
- api_routes/preferences.py
- count_tokens
- json
- prompt_change/render.py
- truncate_value
- repl.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 80 edges
2. `Repositories` - 61 edges
3. `TurnRenderer` - 48 edges
4. `require_user()` - 46 edges
5. `get_repos()` - 44 edges
6. `log_event()` - 42 edges
7. `call_llm()` - 37 edges
8. `update_context_memory()` - 29 edges
9. `call_llm_stream()` - 26 edges
10. `agent_node()` - 23 edges

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

## Communities (102 total, 22 thin omitted)

### Community 0 - "fetch_one"
Cohesion: 0.07
Nodes (44): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, hash_password(), needs_rehash(), verify_password(), execute(), fetch_all() (+36 more)

### Community 1 - ".mock_mode"
Cohesion: 0.14
Nodes (12): _Chunk, _Completion, _MockBase, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, Captures every record the client emits instead of writing it anywhere., TestMockModeOff (+4 more)

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.13
Nodes (23): langgraph_checkpoint_postgres, build_config(), _ensure_branch_learn_table(), get_checkpointer(), _get_pool(), has_pending_interrupt(), initial_state_for_thread(), is_leaf_learned() (+15 more)

### Community 3 - "get_repos"
Cohesion: 0.11
Nodes (33): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get (+25 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.11
Nodes (11): Console, The complete answer for this turn (authoritative copy)., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., Stop the live region (frame stays on screen) before an interrupt., End of the turn: freeze the final frame and close the region., TurnRenderer (+3 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.06
Nodes (30): Analytics, Authentication, Chats, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth) (+22 more)

### Community 6 - "agent/graph.py"
Cohesion: 0.09
Nodes (35): langchain_core_messages, langchain_core_runnables, langgraph_graph, langgraph_graph_message, langgraph_types, pydantic, clear_pause(), is_pause_requested() (+27 more)

### Community 7 - "bind_session_logger"
Cohesion: 0.14
Nodes (14): bind_session_logger(), flush_pending_logs(), get_session_logger(), Path, Append-only JSONL writer for one chat session., Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger() (+6 more)

### Community 8 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 10 - "pathlib"
Cohesion: 0.11
Nodes (25): Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., io, os, pathlib, rich_console, src_models, Prompt loading for every agent and sub-agent in the project. One generic entry…, Path (+17 more)

### Community 11 - "agentnode.py"
Cohesion: 0.12
Nodes (21): BaseMessage, concurrent_futures, agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation(), _is_turn_start() (+13 more)

### Community 12 - "make_console"
Cohesion: 0.22
Nodes (8): handle_step(), _latest_answer(), Render one LangGraph step; return the interrupt payload, if any. ``step`` is a…, make_console(), Console, patch, TestHandleStep, TestPromptForInterrupt

### Community 13 - "HfLoadIsQuiet"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 14 - "test_context_memory.py"
Cohesion: 0.10
Nodes (19): build_execution_memory_index(), count_content_tokens(), empty_context_memory(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts. (+11 more)

### Community 15 - "test_subagents_integration.py"
Cohesion: 0.10
Nodes (12): Any, SubagentsService, WebSocket protocol helpers., Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), tempfile, TestRouting, End-to-end tests for EVA subagent integration. Covers: registry catalog,… (+4 more)

### Community 16 - "subagentnode.py"
Cohesion: 0.16
Nodes (18): _calls_this_turn(), RunnableConfig, Sub-agent node — delegates a focused task to a specialised child agent. Reads…, Count of human messages so far — increments once per new user message, so calls…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node(), _turn_number(), get_subagents() (+10 more)

### Community 17 - "extract_chunks.py"
Cohesion: 0.17
Nodes (19): Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks., _utc_now(), _latest_human() (+11 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (13): login(), logout(), me(), Depends, get, post, new_session_id(), LoginRequest (+5 more)

### Community 19 - "edit_file"
Cohesion: 0.25
Nodes (11): edit_file(), Any, Path, tool, Read content from a text-based file. Supports optional line-range slicing via…, Make targeted edits to a text file by replacing an exact string match. Finds…, Search a text file for lines matching a pattern or literal string. Streams the…, Resolve and validate a path points to a readable text file. Returns (path,… (+3 more)

### Community 20 - "chat_runtime_manager.py"
Cohesion: 0.14
Nodes (15): get_settings(), BaseSettings, Settings, create_access_token(), Any, get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared… (+7 more)

### Community 21 - "agent_runtime.py"
Cohesion: 0.11
Nodes (14): AgentRuntime, on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion. (+6 more)

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.15
Nodes (12): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+4 more)

### Community 23 - "llm_client.py"
Cohesion: 0.12
Nodes (34): OpenAI, _build_messages(), _cache_key(), call_llm(), call_llm_stream(), _dump(), _estimated_usage(), _extract_cost() (+26 more)

### Community 24 - "CurrentUser"
Cohesion: 0.24
Nodes (15): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+7 more)

### Community 25 - "api_routes/memory.py"
Cohesion: 0.24
Nodes (14): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+6 more)

### Community 26 - "typing"
Cohesion: 0.13
Nodes (22): api_api_routes, health(), live(), Depends, get, create_app(), HealthResponse, LiveResponse (+14 more)

### Community 27 - "renderer.py"
Cohesion: 0.17
Nodes (8): rich_markdown, rich_text, _format_args(), Any, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, _short(), CLI theme - one place for every terminal color/style used by the CLI. Keys are…, Text

### Community 28 - "src/config.py"
Cohesion: 0.11
Nodes (17): dotenv, functools, psycopg, pydantic_settings, ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main() (+9 more)

### Community 29 - "vector_store.py"
Cohesion: 0.15
Nodes (21): math, Soft-fail embed; returns None on any error., try_embed_text(), ensure_experience_dir(), Path, Learner / experience-system configuration., src_subagents_learner_agent_store, append_chunks() (+13 more)

### Community 30 - "Repositories"
Cohesion: 0.12
Nodes (14): Any, Depends, get, summary(), Validate JWT for WebSocket handshake., Repositories, user_from_token(), decode_access_token() (+6 more)

### Community 31 - "idle_watcher.py"
Cohesion: 0.08
Nodes (25): asyncio, calendar, datetime, IdleWatcher, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions() (+17 more)

### Community 32 - "agentnode_prompt_loader"
Cohesion: 0.13
Nodes (11): agentnode_prompt_loader(), _has_tool(), load_prompt(), Any, Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, Whether any of `names` is in the available tool list. Capability rules are…, Build the agent node's context and render `agentnode.txt`. (+3 more)

### Community 33 - "checkpoints.py"
Cohesion: 0.26
Nodes (13): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+5 more)

### Community 34 - "require_user"
Cohesion: 0.17
Nodes (12): list_subagents(), Any, Depends, get, list_tools(), Any, Depends, get (+4 more)

### Community 35 - "set_subagent_callback"
Cohesion: 0.19
Nodes (9): contextvars, emit_subagent_event(), Any, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback (+1 more)

### Community 36 - "executor.py"
Cohesion: 0.21
Nodes (15): execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python…, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+7 more)

### Community 37 - "TestTemplateContracts"
Cohesion: 0.18
Nodes (7): _all_template_files(), @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —…, These were {{ }} for str.format(); the renderer would send them literally to…, _strip_comments(), TestEveryTemplateFileIsRegistered, TestTemplateContracts

### Community 38 - "test_db_setup.py"
Cohesion: 0.25
Nodes (4): skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, TestDbSetupLive

### Community 39 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 40 - "_Raw"
Cohesion: 0.15
Nodes (7): fake_gateway(), create(), Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create., _Raw, TestErrorsAreRecorded, create()

### Community 41 - "bootstrap.py"
Cohesion: 0.27
Nodes (11): ensure_venv_on_path(), get_python_executable(), get_venv_python(), get_venv_site_packages(), Path, Ensure the project .venv is used by the current Python process., Prepend the project venv site-packages directory to sys.path., Return the project venv Python when available, otherwise sys.executable. (+3 more)

### Community 42 - "list_experiences"
Cohesion: 0.43
Nodes (7): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization.

### Community 43 - "_FakeEncoded"
Cohesion: 0.33
Nodes (3): list, _FakeEncoded, _FakeModel

### Community 44 - "parse_command"
Cohesion: 0.47
Nodes (3): parse_command(), Map a typed line to a (command, arg) pair, or None for a query., TestParseCommand

### Community 45 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 46 - "web_search.py"
Cohesion: 0.17
Nodes (14): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, BaseModel, field_validator (+6 more)

### Community 47 - "prompts/render.py"
Cohesion: 0.07
Nodes (26): Exception, _eval_cond(), _fmt(), _Node, _parse(), _present(), PromptRenderError, Any (+18 more)

### Community 48 - "ChatPacketQueue"
Cohesion: 0.19
Nodes (5): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback).

### Community 49 - ".test_resumes_after_interrupt"
Cohesion: 0.33
Nodes (4): interrupt_step(), TestRunTurnInteractive, fake_run_turn(), first()

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 52 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "embeddings.py"
Cohesion: 0.23
Nodes (11): hashlib, numpy, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy…, Deterministic hashing bag-of-words vectorizer (no ML dependencies). (+3 more)

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "user_memory.py"
Cohesion: 0.24
Nodes (10): Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update() (+2 more)

### Community 61 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

### Community 63 - "tools_service.py"
Cohesion: 0.42
Nodes (7): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info(), ToolsService

### Community 64 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 65 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 68 - "system_info"
Cohesion: 0.50
Nodes (4): Any, tool, Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 69 - "llm_logger.py"
Cohesion: 0.06
Nodes (41): atexit, contextlib, psycopg_pool, psycopg_rows, queue, register, build_cache_key(), _db_loop() (+33 more)

### Community 70 - "Any"
Cohesion: 0.16
Nodes (13): _filter_checkpoint_tree(), _infer_node(), _is_redundant_checkpoint(), _message_content(), _message_role(), _node_from_metadata(), PostgresSaver, Any (+5 more)

### Community 71 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 72 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): model_validator, EditFileArgs, BaseModel, field_validator, ReadFileArgs, SearchFileArgs

### Community 73 - "TestAgentNodePrompt"
Cohesion: 0.25
Nodes (5): The contract lives in the system half and must not vary with turn state — that…, Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 75 - "retrieve.py"
Cohesion: 0.12
Nodes (14): Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., format_experiences_for_prompt(), Any (+6 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 96 - "current_session_ids"
Cohesion: 0.50
Nodes (3): current_session_ids(), chat/run/user/core ids from the ContextVar-bound agent session logger. Falls…, TestSessionIdentity

### Community 97 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 99 - "log_event"
Cohesion: 0.32
Nodes (16): log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response(), log_route(), log_run_end() (+8 more)

### Community 100 - "._write_and_read"
Cohesion: 0.21
Nodes (4): Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 101 - "api_routes/preferences.py"
Cohesion: 0.25
Nodes (9): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, PreferencesService (+1 more)

### Community 102 - "count_tokens"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 104 - "json"
Cohesion: 0.13
Nodes (13): json, langchain_core_tools, platform, re, decompose_query(), DecomposeQueryArgs, Any, BaseModel (+5 more)

### Community 105 - "prompt_change/render.py"
Cohesion: 0.22
Nodes (13): _eval_cond(), _fmt(), _Node, _parse(), _present(), Generic conditional prompt renderer. The skeleton (prompt.txt) is fully…, Return the inline prefix used before each action template. Only meaningful at…, render() (+5 more)

### Community 107 - "truncate_value"
Cohesion: 0.24
Nodes (6): _ensure_writer_started(), Recursively truncate oversized strings in payloads., truncate_value(), _utc_now(), _writer_loop(), TestTruncate

### Community 109 - "repl.py"
Cohesion: 0.12
Nodes (28): rich_panel, rich_prompt, rich_table, Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_token_callback(), set_token_callback(), get_agent_app() (+20 more)

## Knowledge Gaps
- **32 isolated node(s):** `$schema`, `plugin`, `graphify`, `Layout`, ``POST /v1/auth/login` (public)` (+27 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 473 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `pathlib`, `make_console`, `repl.py`, `.test_resumes_after_interrupt`, `renderer.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `TestSubagentNode` connect `TestSubagentNode` to `bind_session_logger`, `test_subagents_integration.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `log_event()` connect `log_event` to `learn_session`, `agent/graph.py`, `bind_session_logger`, `retrieve.py`, `agentnode.py`, `subagentnode.py`, `extract_chunks.py`, `agent_runtime.py`, `llm_client.py`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _32 weakly-connected nodes found - possible documentation gaps or missing edges._