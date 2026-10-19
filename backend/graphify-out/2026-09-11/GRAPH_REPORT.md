# Graph Report - v2  (2026-09-11)

## Corpus Check
- 175 files · ~58,550 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1400 nodes · 3385 edges · 96 communities (72 shown, 10 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 210 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- api_routes/auth.py
- subagents/registry.py
- postgres_checkpointer.py
- chat_service.py
- trace_event
- EVA Agent API — Reference & How to Use
- agent/graph.py
- llm_client.py
- update_context_memory
- db_setup.py
- to_toon
- agentnode.py
- tool_stubs.py
- test_experience_system.py
- agent/memory.py
- test_subagents_integration.py
- toolnode.py
- extract_chunks.py
- bind_session_logger
- file_io.py
- get_settings
- .run_turn
- ChatRuntimeManager
- log_event
- CurrentUser
- api_routes/memory.py
- get_repos
- agent_studio/graph.py
- sandbox/executor.py
- vector_store.py
- Repositories
- idle_watcher.py
- empty_context_memory
- checkpoints.py
- SubagentsService
- build_agent
- tools/__init__.py
- generate_code.py
- static_validate_node
- api_routes/files.py
- api_routes/preferences.py
- bootstrap.py
- trim_context_for_prompt
- call_llm_with_reasoning
- test_context_memory.py
- context_selector_node
- web_search.py
- require_user
- ChatPacketQueue
- PostgresSaver
- field_validator
- TestSubagentNode
- paths.py
- Multi-User Agentic AI Platform — Database Design
- embeddings.py
- validate_request.py
- user_memory.py
- get_current_datetime_info
- health.py
- test_main_entrypoint.py
- resolve_clarification_node
- GitHubRepoDownloader
- TestSandboxExecutor
- tools_service.py
- TestAgentRuntimeFanout
- test_endpoints.py
- ws.py
- learn_session
- system_info
- truncate_value
- WebSearchArgs
- generate_tree
- decompose_query
- TestSubagentRegistry
- write_user_profile_to_database
- TestNodeTimingInstrumentation
- db/__init__.py
- api/__init__.py
- flusher.py
- CLAUDE.md
- models/__init__.py
- subagents/__init__.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 83 edges
2. `log_event()` - 62 edges
3. `Repositories` - 61 edges
4. `require_user()` - 49 edges
5. `get_repos()` - 44 edges
6. `AgentStudioState` - 36 edges
7. `update_context_memory()` - 31 edges
8. `trace_event()` - 31 edges
9. `emit_live()` - 29 edges
10. `get_settings()` - 22 edges

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

## Communities (96 total, 10 thin omitted)

### Community 0 - "api_routes/auth.py"
Cohesion: 0.05
Nodes (56): login(), logout(), me(), Depends, get, post, cache_get_or_set(), cache_invalidate() (+48 more)

### Community 1 - "subagents/registry.py"
Cohesion: 0.09
Nodes (37): ensure_agent_studio_dirs(), Path, _coerce_kwargs(), make_studio_adapter(), Any, Chat-time invoke adapter for AgentStudio-built agents promoted to subagents., Prefer structured parameters; otherwise map a single string task to the first…, Return a (task, context) -> str adapter bound to a persisted agent. (+29 more)

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.10
Nodes (37): active_checkpoint_path(), build_config(), _ensure_branch_learn_table(), _filter_checkpoint_tree(), get_checkpointer(), _get_pool(), get_thread_state(), has_pending_interrupt() (+29 more)

### Community 3 - "chat_service.py"
Cohesion: 0.14
Nodes (26): create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get, patch (+18 more)

### Community 4 - "trace_event"
Cohesion: 0.13
Nodes (25): AgentStudio configuration., emit_live(), Any, Best-effort live progress emission for AgentStudio nodes. Nodes call…, build_agent_card(), build_test_case(), new_agent_id(), Any (+17 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.06
Nodes (31): Analytics, Authentication, Chats, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth) (+23 more)

### Community 6 - "agent/graph.py"
Cohesion: 0.12
Nodes (24): note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, Agent graph definition., Context selector node — loads a token window from execution_memory into…, human_input_node(), RunnableConfig, Human input node — the agent explicitly asks the user a question. Reached when…, _persist_from_structured() (+16 more)

### Community 7 - "llm_client.py"
Cohesion: 0.13
Nodes (26): OpenAI, _build_messages(), call_llm(), call_llm_stream(), count_tokens(), _gateway_client(), _log_llm_request(), _log_llm_response() (+18 more)

### Community 8 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 9 - "db_setup.py"
Cohesion: 0.08
Nodes (18): ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main(), Idempotent Postgres setup for this project. Creates the target database (if…, Create the target database if it doesn't exist yet. `CREATE DATABASE` can't run…, Create every table/index the app needs, skipping ones that exist., LangGraph owns `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` — let its… (+10 more)

### Community 10 - "to_toon"
Cohesion: 0.13
Nodes (20): Serialize structured context for LLM prompts as TOON (not JSON)., to_toon(), Shared helpers for trimming the sub-agent `context` dict before it goes into an…, parse_json_payload(), Any, Shared JSON-from-LLM parsing helper (mirrors learner_agent's extract_chunks…, Best-effort JSON extraction from an LLM text response., Shared streaming LLM helper for AgentStudio nodes. Nodes ask the LLM to emit a… (+12 more)

### Community 11 - "agentnode.py"
Cohesion: 0.13
Nodes (20): BaseMessage, agent_node(), _coerce_int(), _extract_tag(), _format_conversation(), _is_turn_start(), _latest_human_content(), _parse_parameters() (+12 more)

### Community 12 - "tool_stubs.py"
Cohesion: 0.12
Nodes (19): install_tool_stubs(), _normalize_executor_result(), Any, Deterministic, schema-correct tool stubs for AgentStudio sandbox tests.…, Path-aware stub so file/JSON agents can pass deterministic sandbox tests. -…, Drop-in stand-in for a LangChain StructuredTool used by generated agents., Replace src.tools callables with schema-correct stubs for sandbox grading., _stub_datetime() (+11 more)

### Community 13 - "test_experience_system.py"
Cohesion: 0.11
Nodes (15): Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., format_experiences_for_prompt(), Any, Safe experience retrieval for the main agent hot path., Return top-k experience chunks. Never raises — returns [] on any failure or… (+7 more)

### Community 14 - "agent/memory.py"
Cohesion: 0.13
Nodes (13): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+5 more)

### Community 15 - "test_subagents_integration.py"
Cohesion: 0.11
Nodes (14): WebSocket protocol helpers., emit_subagent_event(), Any, Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback (+6 more)

### Community 16 - "toolnode.py"
Cohesion: 0.14
Nodes (20): clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each…, Call at the very top of a node, before any side effects. Returns the… (+12 more)

### Community 17 - "extract_chunks.py"
Cohesion: 0.18
Nodes (18): Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks., _utc_now(), _latest_human() (+10 more)

### Community 18 - "bind_session_logger"
Cohesion: 0.15
Nodes (14): bind_session_logger(), flush_pending_logs(), get_session_logger(), Path, Append-only JSONL writer for one chat session., Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger() (+6 more)

### Community 19 - "file_io.py"
Cohesion: 0.13
Nodes (18): model_validator, edit_file(), EditFileArgs, Any, BaseModel, field_validator, Path, tool (+10 more)

### Community 20 - "get_settings"
Cohesion: 0.19
Nodes (13): create_app(), get_settings(), BaseSettings, Settings, configure_logging(), utc_now_iso(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1). (+5 more)

### Community 21 - ".run_turn"
Cohesion: 0.11
Nodes (13): AgentRuntime, _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion., Event (+5 more)

### Community 22 - "ChatRuntimeManager"
Cohesion: 0.16
Nodes (6): ChatRuntime, ChatRuntimeManager, Any, WebSocket, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 23 - "log_event"
Cohesion: 0.25
Nodes (18): _ensure_writer_started(), log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response(), log_route() (+10 more)

### Community 24 - "CurrentUser"
Cohesion: 0.24
Nodes (15): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+7 more)

### Community 25 - "api_routes/memory.py"
Cohesion: 0.24
Nodes (14): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+6 more)

### Community 26 - "get_repos"
Cohesion: 0.18
Nodes (16): list_tools(), Any, Depends, get, get_repos(), Validate JWT for WebSocket handshake., user_from_token(), decode_access_token() (+8 more)

### Community 27 - "agent_studio/graph.py"
Cohesion: 0.23
Nodes (14): _log_route(), Conditional-edge routing functions for the AgentStudio graph., route_after_design(), route_after_evaluate(), route_after_expand(), route_after_generate_code(), route_after_generate_tests(), route_after_resolve_clarification() (+6 more)

### Community 28 - "sandbox/executor.py"
Cohesion: 0.17
Nodes (17): install_tool_stubs(), _normalize_executor_result(), Any, Deterministic, schema-correct tool stubs for AgentStudio sandbox tests.…, Path-aware stub so file/JSON agents can pass deterministic sandbox tests. -…, Drop-in stand-in for a LangChain StructuredTool used by generated agents., Replace src.tools callables with schema-correct stubs for sandbox grading., _stub_datetime() (+9 more)

### Community 29 - "vector_store.py"
Cohesion: 0.19
Nodes (17): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks() (+9 more)

### Community 30 - "Repositories"
Cohesion: 0.15
Nodes (9): Any, Depends, get, summary(), Repositories, AnalyticsService, Any, PreloadService (+1 more)

### Community 31 - "idle_watcher.py"
Cohesion: 0.15
Nodes (13): IdleWatcher, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS. (+5 more)

### Community 32 - "empty_context_memory"
Cohesion: 0.17
Nodes (8): empty_context_memory(), agentnode_prompt_loader(), Any, T, TestPromptLoader, TestToolAndSubagentIngest, TestToonTokenSavings, TestPromptWiring

### Community 33 - "checkpoints.py"
Cohesion: 0.31
Nodes (11): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+3 more)

### Community 34 - "SubagentsService"
Cohesion: 0.24
Nodes (11): disable_studio_agent(), enable_studio_agent(), list_studio_agents(), list_subagents(), Any, Depends, get, post (+3 more)

### Community 35 - "build_agent"
Cohesion: 0.20
Nodes (12): agent_studio(), build_agent(), _format_report(), _parse_ts(), Any, datetime, AgentStudio: a subagent specialised in building single-function agents from a…, Adapter matching the `(task, context) -> str` shape used by… (+4 more)

### Community 36 - "tools/__init__.py"
Cohesion: 0.23
Nodes (14): execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python…, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+6 more)

### Community 37 - "generate_code.py"
Cohesion: 0.21
Nodes (11): _allowed_imports(), _extract_code(), generate_code_node(), Generate the single-function agent source code., _repair_feedback(), format_tool_contracts(), format_tool_contracts_for_repair(), Concrete arg/return contracts for whitelisted tools used by AgentStudio.… (+3 more)

### Community 38 - "static_validate_node"
Cohesion: 0.30
Nodes (5): _allowed_modules(), _module_root(), static_validate_node(), Regression: the syntax-error early-return must bump repair_attempts the same as…, TestStaticValidate

### Community 39 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 40 - "api_routes/preferences.py"
Cohesion: 0.25
Nodes (9): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, PreferencesService (+1 more)

### Community 41 - "bootstrap.py"
Cohesion: 0.23
Nodes (12): run(), main(), Boot the EVA agent. Usage (from the v2 project root): python main.py # start…, get_python_executable(), get_venv_python(), get_venv_site_packages(), Path, Ensure the project .venv is used by the current Python process. (+4 more)

### Community 42 - "trim_context_for_prompt"
Cohesion: 0.21
Nodes (6): Any, trim_context_for_prompt(), route_after_static_validate(), Tests for AgentStudio latency fixes: reusing tests across code-only repairs…, TestReuseTestsOnRepair, TestTrimContextForPrompt

### Community 43 - "call_llm_with_reasoning"
Cohesion: 0.18
Nodes (7): call_llm_with_reasoning(), Stream an LLM call, live-emitting `<reasoning>` content as it arrives. Any…, Tests for the richer AgentStudio live-progress plumbing: trace_event kinds, the…, on_subagent_event should not call log_event for reasoning_delta kind, but…, TestAgentRuntimeLogSpamGuard, TestCallLlmWithReasoning, TestTraceEventKinds

### Community 44 - "test_context_memory.py"
Cohesion: 0.23
Nodes (5): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), Unit + edge-case tests for context memory, selector, routing, and agent parse., TestGraphWiring, TestRouting

### Community 45 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 46 - "web_search.py"
Cohesion: 0.26
Nodes (12): ensure_venv_on_path(), Prepend the project venv site-packages directory to sys.path., _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool (+4 more)

### Community 47 - "require_user"
Cohesion: 0.27
Nodes (11): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., Depends (+3 more)

### Community 48 - "ChatPacketQueue"
Cohesion: 0.20
Nodes (4): ChatPacketQueue, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback).

### Community 49 - "PostgresSaver"
Cohesion: 0.20
Nodes (9): _print_checkpoints(), Interactive multi-turn agent CLI loop., run_cli(), PostgresSaver, RunnableConfig, Config that resumes / time-travels from a specific checkpoint., PostgresSaver that also mirrors new messages into the `messages` table., rewind_config() (+1 more)

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
Cohesion: 0.27
Nodes (10): _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy…, Deterministic hashing bag-of-words vectorizer (no ML dependencies)., Embed a single string using the configured local method., Embed multiple strings, batching when possible. (+2 more)

### Community 55 - "validate_request.py"
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

### Community 62 - "TestSandboxExecutor"
Cohesion: 0.22
Nodes (4): A single stuck case (e.g. a hung live web_search) must time out on its own…, Once the overall time budget is exhausted, remaining cases are marked as…, Regression: previously a subprocess.TimeoutExpired on the *outer* sandbox…, TestSandboxExecutor

### Community 63 - "tools_service.py"
Cohesion: 0.57
Nodes (6): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info()

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

### Community 69 - "truncate_value"
Cohesion: 0.47
Nodes (3): Recursively truncate oversized strings in payloads., truncate_value(), TestTruncate

### Community 70 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 71 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 72 - "decompose_query"
Cohesion: 0.50
Nodes (4): decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

## Knowledge Gaps
- **35 isolated node(s):** `graphify`, `Layout`, ``POST /v1/auth/login` (public)`, ``POST /v1/auth/logout` (auth)`, ``GET /v1/auth/me` (auth)` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 401 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `log_event()` connect `log_event` to `build_agent`, `trace_event`, `generate_code.py`, `agent/graph.py`, `llm_client.py`, `static_validate_node`, `learn_session`, `to_toon`, `agentnode.py`, `extract_chunks.py`, `bind_session_logger`, `get_settings`, `.run_turn`, `agent_studio/graph.py`, `resolve_clarification_node`?**
  _High betweenness centrality (0.209) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `api_routes/auth.py`, `checkpoints.py`, `SubagentsService`, `chat_service.py`, `get_repos`, `api_routes/preferences.py`, `require_user`, `api_routes/memory.py`, `health.py`, `Repositories`, `tools_service.py`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Why does `get_repos()` connect `get_repos` to `api_routes/auth.py`, `checkpoints.py`, `chat_service.py`, `api_routes/preferences.py`, `require_user`, `get_settings`, `ChatRuntimeManager`, `CurrentUser`, `api_routes/memory.py`, `Repositories`, `idle_watcher.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 37 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **What connects `graphify`, `Layout`, ``POST /v1/auth/login` (public)` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api_routes/auth.py` be split into smaller, more focused modules?**
  _Cohesion score 0.051018465638682654 - nodes in this community are weakly interconnected._