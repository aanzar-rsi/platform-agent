# Graph Report - v2  (2026-09-16)

## Corpus Check
- 182 files · ~65,103 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1544 nodes · 3751 edges · 107 communities (84 shown, 9 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 205 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- security.py
- .mock_mode
- postgres_checkpointer.py
- chat_service.py
- log_event
- EVA Agent API — Reference & How to Use
- agent/graph.py
- bind_session_logger
- update_context_memory
- test_db_setup.py
- to_toon
- agentnode.py
- tool_stubs.py
- test_embeddings_quiet.py
- agent/memory.py
- set_subagent_callback
- toolnode.py
- extract_chunks.py
- api_routes/auth.py
- tools/__init__.py
- get_settings
- .run_turn
- ChatRuntimeManager
- llm_client.py
- CurrentUser
- get_repos
- endpoint.py
- agent_studio/graph.py
- get_checkpointer
- vector_store.py
- Repositories
- idle_watcher.py
- test_context_memory.py
- checkpoints.py
- require_user
- build_agent
- tools/executor.py
- generate_code.py
- static_validate_node
- api_routes/files.py
- test_llm_mock_mode.py
- bootstrap.py
- trim_context_for_prompt
- call_llm_with_reasoning
- route_from_agent
- context_selector_node
- web_search.py
- subagentnode.py
- ChatPacketQueue
- PostgresSaver
- field_validator
- TestSubagentNode
- paths.py
- Multi-User Agentic AI Platform — Database Design
- embeddings.py
- test_agent_studio.py
- user_memory.py
- get_current_datetime_info
- health.py
- test_main_entrypoint.py
- resolve_clarification_node
- GitHubRepoDownloader
- run_function_against_cases
- FastAPI
- TestAgentRuntimeFanout
- test_endpoints.py
- ws.py
- learn_session
- system_info
- llm_logger.py
- Any
- generate_tree
- ReadFileArgs
- test_subagents_integration.py
- write_user_profile_to_database
- test_experience_system.py
- db/__init__.py
- api/__init__.py
- flusher.py
- CLAUDE.md
- models/__init__.py
- subagents/__init__.py
- flush_pending_llm_calls
- test_llm_logger.py
- list_checkpoints
- src/config.py
- agent_logger.py
- ._write_and_read
- api_routes/preferences.py
- count_tokens
- build_cache_key
- decomposer.py
- TestNodeTimingInstrumentation

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 83 edges
2. `log_event()` - 63 edges
3. `Repositories` - 61 edges
4. `require_user()` - 49 edges
5. `get_repos()` - 44 edges
6. `call_llm()` - 37 edges
7. `AgentStudioState` - 36 edges
8. `update_context_memory()` - 31 edges
9. `trace_event()` - 31 edges
10. `emit_live()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `user_memory_fetch()` --uses--> `MemoryRepository`  [INFERRED]
  src/tools/user_memory.py → api/db/repositories/memory.py
- `user_memory_update()` --uses--> `MemoryRepository`  [INFERRED]
  src/tools/user_memory.py → api/db/repositories/memory.py
- `lifespan()` --uses--> `IdleWatcher`  [INFERRED]
  api/lifespan.py → src/subagents/learner_agent/idle_watcher.py
- `_is_run_active()` --calls--> `get_runtime_manager()`  [EXTRACTED]
  src/subagents/learner_agent/idle_watcher.py → api/services/chat_runtime_manager.py
- `list_experiences()` --calls--> `read_all_chunks()`  [EXTRACTED]
  api/api_routes/experience.py → src/subagents/learner_agent/store/json_store.py

## Import Cycles
- None detected.

## Communities (107 total, 9 thin omitted)

### Community 0 - "security.py"
Cohesion: 0.07
Nodes (41): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, hash_password(), needs_rehash(), verify_password(), execute(), fetch_all() (+33 more)

### Community 1 - ".mock_mode"
Cohesion: 0.18
Nodes (8): _Chunk, _Completion, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, TestMockModeOn, TestStreamReplay, _Usage

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.16
Nodes (18): build_config(), _ensure_branch_learn_table(), _get_pool(), get_thread_state(), has_pending_interrupt(), initial_state_for_thread(), is_leaf_learned(), mark_leaf_learned() (+10 more)

### Community 3 - "chat_service.py"
Cohesion: 0.13
Nodes (28): create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get, patch (+20 more)

### Community 4 - "log_event"
Cohesion: 0.13
Nodes (25): emit_live(), Any, Best-effort live progress emission for AgentStudio nodes. Nodes call…, build_agent_card(), build_test_case(), new_agent_id(), Any, Plain-dict shapes for AgentCard / TestCase / TestResult, plus builders. Kept as… (+17 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.06
Nodes (31): Analytics, Authentication, Chats, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth) (+23 more)

### Community 6 - "agent/graph.py"
Cohesion: 0.16
Nodes (17): note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, Agent graph definition., Context selector node — loads a token window from execution_memory into…, human_input_node(), RunnableConfig, Human input node — the agent explicitly asks the user a question. Reached when…, _persist_from_structured() (+9 more)

### Community 7 - "bind_session_logger"
Cohesion: 0.18
Nodes (12): bind_session_logger(), flush_pending_logs(), get_session_logger(), Append-only JSONL writer for one chat session., Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger(), SessionLogger (+4 more)

### Community 8 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 9 - "test_db_setup.py"
Cohesion: 0.18
Nodes (5): skipUnless, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 10 - "to_toon"
Cohesion: 0.12
Nodes (22): Serialize structured context for LLM prompts as TOON (not JSON)., to_toon(), AgentStudio configuration., Shared helpers for trimming the sub-agent `context` dict before it goes into an…, parse_json_payload(), Any, Shared JSON-from-LLM parsing helper (mirrors learner_agent's extract_chunks…, Best-effort JSON extraction from an LLM text response. (+14 more)

### Community 11 - "agentnode.py"
Cohesion: 0.14
Nodes (18): BaseMessage, agent_node(), _coerce_int(), _extract_tag(), _format_conversation(), _is_turn_start(), _latest_human_content(), _parse_parameters() (+10 more)

### Community 12 - "tool_stubs.py"
Cohesion: 0.17
Nodes (17): install_tool_stubs(), _normalize_executor_result(), Any, Deterministic, schema-correct tool stubs for AgentStudio sandbox tests.…, Path-aware stub so file/JSON agents can pass deterministic sandbox tests. -…, Drop-in stand-in for a LangChain StructuredTool used by generated agents., Replace src.tools callables with schema-correct stubs for sandbox grading., _stub_datetime() (+9 more)

### Community 13 - "test_embeddings_quiet.py"
Cohesion: 0.16
Nodes (7): list, _FakeEncoded, _FakeModel, HfLoadIsQuiet, _install_fakes(), The HF embedding backend must load quietly: no 'Loading weights' tqdm bar, no…, Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 14 - "agent/memory.py"
Cohesion: 0.13
Nodes (13): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+5 more)

### Community 15 - "set_subagent_callback"
Cohesion: 0.18
Nodes (9): emit_subagent_event(), Any, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback, TestBuildAgentStreaming (+1 more)

### Community 16 - "toolnode.py"
Cohesion: 0.19
Nodes (15): clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each…, Call at the very top of a node, before any side effects. Returns the… (+7 more)

### Community 17 - "extract_chunks.py"
Cohesion: 0.18
Nodes (18): Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks., _utc_now(), _latest_human() (+10 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.26
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "tools/__init__.py"
Cohesion: 0.23
Nodes (13): edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management., Read content from a text-based file. Supports optional line-range slicing via…, Make targeted edits to a text file by replacing an exact string match. Finds…, Search a text file for lines matching a pattern or literal string. Streams the… (+5 more)

### Community 20 - "get_settings"
Cohesion: 0.24
Nodes (11): create_app(), get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., ensure_client_path() (+3 more)

### Community 21 - ".run_turn"
Cohesion: 0.11
Nodes (13): AgentRuntime, _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion., Event (+5 more)

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.18
Nodes (6): ChatRuntime, ChatRuntimeManager, Any, WebSocket, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 23 - "llm_client.py"
Cohesion: 0.16
Nodes (29): OpenAI, _build_messages(), _cache_key(), call_llm(), call_llm_stream(), _dump(), _estimated_usage(), _extract_cost() (+21 more)

### Community 24 - "CurrentUser"
Cohesion: 0.24
Nodes (15): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+7 more)

### Community 25 - "get_repos"
Cohesion: 0.24
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "endpoint.py"
Cohesion: 0.43
Nodes (7): utc_now_iso(), chat_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject()

### Community 27 - "agent_studio/graph.py"
Cohesion: 0.23
Nodes (14): _log_route(), Conditional-edge routing functions for the AgentStudio graph., route_after_design(), route_after_evaluate(), route_after_expand(), route_after_generate_code(), route_after_generate_tests(), route_after_resolve_clarification() (+6 more)

### Community 28 - "get_checkpointer"
Cohesion: 0.21
Nodes (12): ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main(), Idempotent Postgres setup for this project. Creates the target database (if…, Create the target database if it doesn't exist yet. `CREATE DATABASE` can't run…, Create every table/index the app needs, skipping ones that exist., LangGraph owns `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` — let its… (+4 more)

### Community 29 - "vector_store.py"
Cohesion: 0.17
Nodes (19): Soft-fail embed; returns None on any error., try_embed_text(), ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any (+11 more)

### Community 30 - "Repositories"
Cohesion: 0.12
Nodes (13): Any, Depends, get, summary(), Validate JWT for WebSocket handshake., Repositories, user_from_token(), decode_access_token() (+5 more)

### Community 31 - "idle_watcher.py"
Cohesion: 0.15
Nodes (13): IdleWatcher, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS. (+5 more)

### Community 32 - "test_context_memory.py"
Cohesion: 0.14
Nodes (10): empty_context_memory(), agentnode_prompt_loader(), Any, T, Unit + edge-case tests for context memory, selector, routing, and agent parse., TestGraphWiring, TestPromptLoader, TestToolAndSubagentIngest (+2 more)

### Community 33 - "checkpoints.py"
Cohesion: 0.31
Nodes (11): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+3 more)

### Community 34 - "require_user"
Cohesion: 0.17
Nodes (21): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., disable_studio_agent() (+13 more)

### Community 35 - "build_agent"
Cohesion: 0.20
Nodes (12): agent_studio(), build_agent(), _format_report(), _parse_ts(), Any, datetime, AgentStudio: a subagent specialised in building single-function agents from a…, Adapter matching the `(task, context) -> str` shape used by… (+4 more)

### Community 36 - "tools/executor.py"
Cohesion: 0.24
Nodes (13): execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python…, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+5 more)

### Community 37 - "generate_code.py"
Cohesion: 0.21
Nodes (11): _allowed_imports(), _extract_code(), generate_code_node(), Generate the single-function agent source code., _repair_feedback(), format_tool_contracts(), format_tool_contracts_for_repair(), Concrete arg/return contracts for whitelisted tools used by AgentStudio.… (+3 more)

### Community 38 - "static_validate_node"
Cohesion: 0.26
Nodes (6): _allowed_modules(), _module_root(), AST-based static validation: syntax, single-function shape, import/call…, static_validate_node(), Regression: the syntax-error early-return must bump repair_attempts the same as…, TestStaticValidate

### Community 39 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 40 - "test_llm_mock_mode.py"
Cohesion: 0.11
Nodes (12): fake_gateway(), _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, src/subagents/agent_studio/sandbox/tool_stubs.py replaces these with `(prompt,…, Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create., Captures every record the client emits instead of writing it anywhere., _Raw (+4 more)

### Community 41 - "bootstrap.py"
Cohesion: 0.29
Nodes (11): ensure_venv_on_path(), get_python_executable(), get_venv_python(), get_venv_site_packages(), Path, Ensure the project .venv is used by the current Python process., Prepend the project venv site-packages directory to sys.path., Return the project venv Python when available, otherwise sys.executable. (+3 more)

### Community 42 - "trim_context_for_prompt"
Cohesion: 0.21
Nodes (6): Any, trim_context_for_prompt(), route_after_static_validate(), Tests for AgentStudio latency fixes: reusing tests across code-only repairs…, TestReuseTestsOnRepair, TestTrimContextForPrompt

### Community 43 - "call_llm_with_reasoning"
Cohesion: 0.19
Nodes (7): call_llm_with_reasoning(), Stream an LLM call, live-emitting `<reasoning>` content as it arrives. Any…, Tests for the richer AgentStudio live-progress plumbing: trace_event kinds, the…, on_subagent_event should not call log_event for reasoning_delta kind, but…, TestAgentRuntimeLogSpamGuard, TestCallLlmWithReasoning, TestEmitLive

### Community 44 - "route_from_agent"
Cohesion: 0.36
Nodes (3): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting

### Community 45 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 46 - "web_search.py"
Cohesion: 0.18
Nodes (13): _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, BaseModel, field_validator, tool (+5 more)

### Community 47 - "subagentnode.py"
Cohesion: 0.22
Nodes (12): _calls_this_turn(), RunnableConfig, Sub-agent node — delegates a focused task to a specialised child agent. Reads…, Count of human messages so far — increments once per new user message, so calls…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node(), _turn_number(), Any (+4 more)

### Community 48 - "ChatPacketQueue"
Cohesion: 0.18
Nodes (5): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback).

### Community 49 - "PostgresSaver"
Cohesion: 0.32
Nodes (5): _message_content(), _message_role(), PostgresSaver, PostgresSaver that also mirrors new messages into the `messages` table., _valid_uuid()

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "TestSubagentNode"
Cohesion: 0.27
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode

### Community 52 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "embeddings.py"
Cohesion: 0.33
Nodes (8): _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy…, Deterministic hashing bag-of-words vectorizer (no ML dependencies)., Embed a single string using the configured local method., Embed multiple strings, batching when possible.

### Community 55 - "test_agent_studio.py"
Cohesion: 0.29
Nodes (5): _looks_like_gibberish(), First-pass structural validity gate for an incoming build request.…, validate_request_node(), Tests for the AgentStudio subagent: node units, AST whitelist enforcement,…, TestValidateRequest

### Community 56 - "user_memory.py"
Cohesion: 0.24
Nodes (10): Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update() (+2 more)

### Community 57 - "get_current_datetime_info"
Cohesion: 0.20
Nodes (8): get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's…, Get comprehensive date and time information for the user's current timezone.…

### Community 58 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 59 - "test_main_entrypoint.py"
Cohesion: 0.28
Nodes (4): ModuleType, Tests for the main.py boot dispatch (API server vs interactive agent CLI)., TestDevPyRemoved, TestMainDispatch

### Community 60 - "resolve_clarification_node"
Cohesion: 0.44
Nodes (3): resolve_clarification_node(), Tests for AgentStudio's bounded, in-call clarification-resolution loop. Covers:…, TestResolveClarificationNode

### Community 62 - "run_function_against_cases"
Cohesion: 0.05
Nodes (53): Any, ensure_agent_studio_dirs(), Path, _coerce_kwargs(), make_studio_adapter(), Any, Chat-time invoke adapter for AgentStudio-built agents promoted to subagents., Prefer structured parameters; otherwise map a single string task to the first… (+45 more)

### Community 63 - "FastAPI"
Cohesion: 0.23
Nodes (12): list_tools(), Any, Depends, get, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict() (+4 more)

### Community 64 - "TestAgentRuntimeFanout"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 65 - "test_endpoints.py"
Cohesion: 0.43
Nodes (6): TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected()

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 68 - "system_info"
Cohesion: 0.33
Nodes (5): Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 69 - "llm_logger.py"
Cohesion: 0.11
Nodes (26): Path, _safe_chat_id(), _db_loop(), _db_params(), _ensure_db_writer_started(), _ensure_table(), _logs_dir(), Any (+18 more)

### Community 70 - "Any"
Cohesion: 0.29
Nodes (10): _filter_checkpoint_tree(), _infer_node(), _is_redundant_checkpoint(), list_checkpoint_tree(), _node_from_metadata(), Any, Best-effort label for "which node just wrote this checkpoint" — there is no…, Prefer LangGraph checkpoint metadata (authoritative node writes). (+2 more)

### Community 71 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 72 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): model_validator, EditFileArgs, BaseModel, field_validator, ReadFileArgs, SearchFileArgs

### Community 73 - "test_subagents_integration.py"
Cohesion: 0.17
Nodes (5): WebSocket protocol helpers., End-to-end tests for EVA subagent integration. Covers: registry catalog,…, TestProtocolConstants, TestRouting, TestSubagentRegistry

### Community 75 - "test_experience_system.py"
Cohesion: 0.11
Nodes (17): Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., format_experiences_for_prompt(), Any (+9 more)

### Community 94 - "flush_pending_llm_calls"
Cohesion: 0.40
Nodes (5): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…

### Community 96 - "test_llm_logger.py"
Cohesion: 0.22
Nodes (7): current_session_ids(), lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, chat/run/user/core ids from the ContextVar-bound agent session logger. Falls…, Tests for the LLM call recorder and its mock-replay cache key. No live Postgres…, TestLookupSoftFails, TestSessionIdentity

### Community 97 - "list_checkpoints"
Cohesion: 0.28
Nodes (8): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, _print_checkpoints(), Interactive multi-turn agent CLI loop., run_cli(), list_checkpoints(), Return readable checkpoint summaries for a thread (newest first).

### Community 98 - "src/config.py"
Cohesion: 0.29
Nodes (5): get_settings(), BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 99 - "agent_logger.py"
Cohesion: 0.16
Nodes (21): _ensure_writer_started(), log_agent_decision(), log_context_select(), log_error(), log_llm_request(), log_llm_response(), log_route(), log_run_end() (+13 more)

### Community 100 - "._write_and_read"
Cohesion: 0.21
Nodes (6): build_record(), _utc_now(), Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 101 - "api_routes/preferences.py"
Cohesion: 0.25
Nodes (9): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, PreferencesService (+1 more)

### Community 102 - "count_tokens"
Cohesion: 0.26
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 103 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 104 - "decomposer.py"
Cohesion: 0.25
Nodes (7): decompose_query(), DecomposeQueryArgs, Any, BaseModel, tool, Tool for decomposing a user query into a structured, multi-dimensional…, Decompose a user query into a structured multi-dimensional breakdown. Produces…

## Knowledge Gaps
- **35 isolated node(s):** `graphify`, `Layout`, ``POST /v1/auth/login` (public)`, ``POST /v1/auth/logout` (auth)`, ``GET /v1/auth/me` (auth)` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 443 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `log_event()` connect `log_event` to `build_agent`, `learn_session`, `generate_code.py`, `agent/graph.py`, `static_validate_node`, `agent_logger.py`, `bind_session_logger`, `to_toon`, `test_experience_system.py`, `agentnode.py`, `subagentnode.py`, `extract_chunks.py`, `get_settings`, `.run_turn`, `llm_client.py`, `agent_studio/graph.py`, `resolve_clarification_node`?**
  _High betweenness centrality (0.221) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `checkpoints.py`, `require_user`, `chat_service.py`, `api_routes/preferences.py`, `api_routes/auth.py`, `get_repos`, `health.py`, `Repositories`, `FastAPI`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `get_repos()` connect `get_repos` to `checkpoints.py`, `require_user`, `chat_service.py`, `api_routes/preferences.py`, `api_routes/auth.py`, `get_settings`, `ChatRuntimeManager`, `CurrentUser`, `endpoint.py`, `idle_watcher.py`, `Repositories`, `FastAPI`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify`, `Layout`, ``POST /v1/auth/login` (public)` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `security.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06604938271604938 - nodes in this community are weakly interconnected._