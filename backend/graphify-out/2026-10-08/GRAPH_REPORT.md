# Graph Report - backend  (2026-10-08)

## Corpus Check
- 182 files · ~118,621 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 10 file(s) not represented in the graph (top: .bin 4, .jsonl 3, .example 1)

## Summary
- 2127 nodes · 5779 edges · 120 communities (96 shown, 24 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 501 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- typing
- test_llm_mock_mode.py
- require_user
- chat_runtime_manager.py
- TurnRenderer
- EVA Agent API — Reference & How to Use
- PreferencesService
- llm_client.py
- TestAgentNodePrompt
- agent_core.py
- postgres.py
- agentnode.py
- AgentRepository
- prompt_loader.py
- update_context_memory
- pathlib
- test_llm_logger.py
- get_settings
- api_routes/auth.py
- AgentCore
- TestSubagentNode
- AgentRuntime
- bind_session_logger
- tool_node
- chat_service.py
- api_routes/memory.py
- CurrentUser
- trace.py
- test_endpoints.py
- test_agent_core.py
- SessionRepository
- Tools: `tool_node`
- web_search.py
- CheckpointService
- context_selector_node
- extract_chunks.py
- ._write_and_read
- tools/__init__.py
- repositories/mcp.py
- Platform Agent Codebase Documentation
- test_embeddings_quiet.py
- log_event
- ChatPacketQueue
- Settings
- health.py
- main.py
- token_stream.py
- emit
- agentnode_prompt_loader
- WebSocket chat session
- executor.py
- active_checkpoint_path
- paths.py
- Multi-User Agentic AI Platform — Database Design
- test_agentnode_fast_planner_handoff.py
- graphify.js
- render
- TestMainDispatch
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- repositories/memory.py
- _present
- test_context_memory.py
- agent/kb.py
- test_subagents_integration.py
- test_db_setup.py
- ws.py
- agent/memory.py
- emit_child_event
- llm_logger.py
- WebSearchArgs
- decompose_query
- subagentnode.py
- test_prompt_templates.py
- AGENTS.md
- idle_watcher.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- generate_tree
- repl.py
- test_prompt_render.py
- postgres_checkpointer.py
- agent_runtime.py
- ReadFileArgs
- TestTheme
- run_cli
- TestCreateUser
- test_phased_plan.py
- re
- file_io.py
- mcp_runtime.py
- TestAgentRuntimeFanout
- ChatRuntimeManager
- agent/graph.py
- _session_prompt
- os
- now.py
- repositories/__init__.py
- New API chat and first turn
- WebSocket protocol
- parse_command
- security.py
- _eval_cond
- src_subagents_learner_agent_store
- learn_session
- truncate_value
- toolnode.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 115 edges
2. `require_user()` - 70 edges
3. `Repositories` - 67 edges
4. `TurnRenderer` - 59 edges
5. `emit()` - 55 edges
6. `get_repos()` - 54 edges
7. `AgentCore` - 46 edges
8. `log_event()` - 44 edges
9. `agent_node()` - 41 edges
10. `get_connection()` - 40 edges

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

## Communities (120 total, 24 thin omitted)

### Community 0 - "typing"
Cohesion: 0.09
Nodes (24): api_api_routes, Any, Depends, get, summary(), Authorized view of active learned experiences., list_tools(), Any (+16 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.09
Nodes (26): Gateway behavior, LLM call logger and replay cache, call_llm(), call_llm_stream(), _Chunk, _Completion, fake_gateway(), create() (+18 more)

### Community 2 - "require_user"
Cohesion: 0.15
Nodes (37): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+29 more)

### Community 3 - "chat_runtime_manager.py"
Cohesion: 0.15
Nodes (19): utc_now_iso(), _done(), _target(), _done(), _target(), api_ws, agent_ws(), _handle_client_message() (+11 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.05
Nodes (28): emit_tag(), _format_args(), Any, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning. (+20 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.11
Nodes (18): Analytics, Authentication, Checkpoints & rollback, Data store (`data/`), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth), `GET /v1/auth/me` (auth), `GET /v1/chats/{chat_id}/checkpoints` (auth) (+10 more)

### Community 6 - "PreferencesService"
Cohesion: 0.17
Nodes (10): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, model_validator (+2 more)

### Community 7 - "llm_client.py"
Cohesion: 0.06
Nodes (46): OpenAI, emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages(), _build_provider(), _cache_key() (+38 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "agent_core.py"
Cohesion: 0.14
Nodes (14): concurrent_futures, Agent lifecycle facade and compatibility exports., ChildHandle, Policy, Core agent dataclasses shared across runtime components., ChildRunner, Process-local child execution orchestration for AgentCore., Bounded, process-local execution of durable child runs. (+6 more)

### Community 10 - "postgres.py"
Cohesion: 0.13
Nodes (17): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute() (+9 more)

### Community 11 - "agentnode.py"
Cohesion: 0.07
Nodes (32): BaseMessage, Retrieval in the main agent, agent_node(), _on_token(), run_planner_call(), _coerce_int(), _extract_tag(), _format_conversation() (+24 more)

### Community 12 - "AgentRepository"
Cohesion: 0.12
Nodes (7): fetch_all(), fetch_one(), Any, AgentRepository, Any, Durable AgentCore identities, run reservations, and child results., uuid

### Community 13 - "prompt_loader.py"
Cohesion: 0.24
Nodes (12): Major prompt functions, _armory_text(), fast_agent_prompt_loader(), _load_module(), _Node, _parse(), planner_agent_prompt_loader(), Prompt rendering and loading for every agent and sub-agent in the project. One… (+4 more)

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "pathlib"
Cohesion: 0.13
Nodes (17): Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., io, pathlib, rich_console, scripts, sys, Unit tests for the live turn renderer (live rendering disabled in tests)., Unit tests for the CLI REPL: command parsing, step handling, interrupts, and… (+9 more)

### Community 16 - "test_llm_logger.py"
Cohesion: 0.15
Nodes (12): src_utils, build_record(), current_session_ids(), lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, Agent identity from the ContextVar-bound logger. Falls back to…, _utc_now(), Tests for the LLM call recorder and its mock-replay cache key. No live Postgres… (+4 more)

### Community 17 - "get_settings"
Cohesion: 0.16
Nodes (13): get_settings(), BaseSettings, Settings, configure_logging(), execute(), Run an INSERT/UPDATE/DELETE, return affected row count., lifespan(), ensure_client_path() (+5 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "AgentCore"
Cohesion: 0.12
Nodes (6): AgentCore, AgentID, Message, Armory, Guardrails, Observability

### Community 20 - "TestSubagentNode"
Cohesion: 0.20
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - "AgentRuntime"
Cohesion: 0.15
Nodes (5): AgentRuntime, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, Thin re-export — stream bridging lives in agent_runtime for cohesion., Event

### Community 22 - "bind_session_logger"
Cohesion: 0.18
Nodes (10): bind_session_logger(), flush_pending_logs(), get_session_logger(), Bind a SessionLogger for the current context. Returns a reset token (or None if…, Block (up to `timeout`s) until all queued log lines have been written. Normal…, reset_session_logger(), A slow/stalled write to one chat's file must not delay log() calls for the SAME…, TestAsyncWriterDoesNotBlockCaller (+2 more)

### Community 23 - "tool_node"
Cohesion: 0.22
Nodes (6): empty_context_memory(), RunnableConfig, tool_node(), TestPromptLoader, TestToolAndSubagentIngest, TestToonTokenSavings

### Community 24 - "chat_service.py"
Cohesion: 0.10
Nodes (40): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `GET /v1/chats/{chat_id}` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth), create_chat(), delete_chat() (+32 more)

### Community 25 - "api_routes/memory.py"
Cohesion: 0.17
Nodes (20): get_experience(), list_experiences(), Depends, get, add_memory(), clear_memory(), get_memory(), put_memory() (+12 more)

### Community 26 - "CurrentUser"
Cohesion: 0.20
Nodes (23): connect_server(), create_server(), delete_server(), disconnect_server(), import_servers(), list_servers(), Any, delete (+15 more)

### Community 27 - "trace.py"
Cohesion: 0.16
Nodes (21): create_app(), trace_requests(), work(), bind(), bind_from_config(), context(), _persist(), Any (+13 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "test_agent_core.py"
Cohesion: 0.13
Nodes (10): FakeAgents, parent_core(), AgentCore policy and independent-child behavior without a live database., test_cancelled_running_child_cannot_commit_result(), test_child_result_requires_parent_lineage(), test_nonblocking_children_and_one_run_per_agent(), slow(), test_policy_updates_and_interrupted_close() (+2 more)

### Community 30 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "Tools: `tool_node`"
Cohesion: 0.30
Nodes (12): Command execution tools, Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), Any, tool, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+4 more)

### Community 32 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 33 - "CheckpointService"
Cohesion: 0.28
Nodes (11): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+3 more)

### Community 34 - "context_selector_node"
Cohesion: 0.39
Nodes (3): context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "extract_chunks.py"
Cohesion: 0.07
Nodes (38): Experience API view, Full learner sequence, Learner graph, Learning Agent and Experience System, Step 1: load trajectory, Step 2: extract reusable advice, Step 3: persist and index, logging (+30 more)

### Community 36 - "._write_and_read"
Cohesion: 0.18
Nodes (7): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall

### Community 37 - "tools/__init__.py"
Cohesion: 0.22
Nodes (8): langchain_core_tools, platform, Internal tools package for the agent., Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 38 - "repositories/mcp.py"
Cohesion: 0.16
Nodes (15): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+7 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.08
Nodes (25): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Current Extension Points and Limits (+17 more)

### Community 40 - "test_embeddings_quiet.py"
Cohesion: 0.15
Nodes (8): list, src_models, _FakeEncoded, _FakeModel, HfLoadIsQuiet, _install_fakes(), The HF embedding backend must load quietly: no 'Loading weights' tqdm bar, no…, Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 41 - "log_event"
Cohesion: 0.25
Nodes (20): on_subagent_event(), json, log_agent_decision(), log_context_select(), log_error(), log_event(), log_llm_request(), log_llm_response() (+12 more)

### Community 42 - "ChatPacketQueue"
Cohesion: 0.18
Nodes (7): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior

### Community 43 - "Settings"
Cohesion: 0.40
Nodes (3): BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 44 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 45 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 46 - "token_stream.py"
Cohesion: 0.22
Nodes (8): contextvars, Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_usage_callback(), set_token_callback(), set_usage_callback(), TokenCallback, UsageCallback

### Community 47 - "emit"
Cohesion: 0.21
Nodes (11): MemoryRepository, Memory, Agent policy facets: memory, armory, guardrails and observability., _record_tool_result(), current_ids(), emit(), _error(), in_run() (+3 more)

### Community 48 - "agentnode_prompt_loader"
Cohesion: 0.18
Nodes (11): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, Add a planner-callable sub-agent, Add a prompt block, Add an API resource, Add an internal tool, Practical prompt-debug method, System versus user prompt (+3 more)

### Community 49 - "WebSocket chat session"
Cohesion: 0.33
Nodes (6): Client → server, Connect, Example messages, Minimal client flow, Server → client, WebSocket chat session

### Community 50 - "executor.py"
Cohesion: 0.17
Nodes (11): BashArgs, _check_blacklist(), _find_executable(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs, Internal tools for executing Bash commands, PowerShell commands, and Python… (+3 more)

### Community 52 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "test_agentnode_fast_planner_handoff.py"
Cohesion: 0.54
Nodes (7): src_agent_nodes, _config(), object, _state(), test_fast_plan_handoff_accepts_planner_finish_without_steps_json(), test_fast_plan_handoff_missing_steps_after_retry_surfaces_clear_error(), test_fast_plan_handoff_retries_once_then_parses_plan()

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 60 - "repositories/memory.py"
Cohesion: 0.43
Nodes (4): _iso(), Any, _row_to_entry(), Durable user-memory tools

### Community 61 - "_present"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 62 - "test_context_memory.py"
Cohesion: 0.14
Nodes (10): langgraph_graph, Conditional edge out of agent_node. Reads next_step["action"] and returns the…, Conditional edge out of input_security_gate. Reuses the same…, route_from_agent(), route_from_input_gate(), Unit + edge-case tests for context memory, selector, routing, and agent parse., TestGraphWiring, TestRouting (+2 more)

### Community 63 - "agent/kb.py"
Cohesion: 0.05
Nodes (86): get_connection(), Connection, 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, fixture, hashlib, math, numpy (+78 more)

### Community 64 - "test_subagents_integration.py"
Cohesion: 0.13
Nodes (8): Any, SubagentsService, WebSocket protocol helpers., End-to-end tests for EVA subagent integration. Covers: registry catalog,…, TestCatalogAPI, TestProtocolConstants, TestSubagentRegistry, TestSubagentStream

### Community 65 - "test_db_setup.py"
Cohesion: 0.13
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "agent/memory.py"
Cohesion: 0.13
Nodes (13): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+5 more)

### Community 68 - "emit_child_event"
Cohesion: 0.60
Nodes (4): emit_child_event(), Any, test_child_events_emit_started_step_finished(), fake_run_turn()

### Community 69 - "llm_logger.py"
Cohesion: 0.14
Nodes (20): atexit, queue, _ensure_writer_started(), Path, _safe_agent_id(), _writer_loop(), _db_loop(), _db_params() (+12 more)

### Community 70 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 71 - "decompose_query"
Cohesion: 0.50
Nodes (4): decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

### Community 72 - "subagentnode.py"
Cohesion: 0.09
Nodes (31): Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, State, Sub-agents: `subagent_node` and gate, Topology, langgraph_graph_message (+23 more)

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.13
Nodes (13): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+5 more)

### Community 75 - "idle_watcher.py"
Cohesion: 0.09
Nodes (19): CLI, Commands, Flow, Idle scheduling and branch handling, BackgroundIdleWatcher, IdleWatcher, _is_run_active(), _mark_session() (+11 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 89 - "repl.py"
Cohesion: 0.12
Nodes (18): api_db_repositories, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_markdown, rich_panel, rich_prompt (+10 more)

### Community 91 - "test_prompt_render.py"
Cohesion: 0.20
Nodes (11): _fmt(), PromptRenderError, Any, Exception, Serialize structured prompt context as TOON., Raised in strict mode when a template references an unknown variable., replace(), to_toon() (+3 more)

### Community 92 - "postgres_checkpointer.py"
Cohesion: 0.06
Nodes (55): 1. End-to-End Turn Execution, 5. API Layer and Service Boundaries, 7. PostgreSQL, Repositories, and Checkpoints, 8. Observability, Logs, and LLM Replay, Checkpointer function map, Database troubleshooting, Detailed Subsystem Reference, Functions to start with when tracing a turn (+47 more)

### Community 94 - "agent_runtime.py"
Cohesion: 0.14
Nodes (18): on_child_event(), _emit_turn_complete(), Any, _truncate(), ChildEventCallback, Ask the run for this thread to pause at the next node boundary., request_pause(), Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).… (+10 more)

### Community 96 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, model_validator, ReadFileArgs, SearchFileArgs

### Community 99 - "run_cli"
Cohesion: 0.21
Nodes (20): PreferencesRepository, _choose(), get_agent_app(), _handle_settings(), _load_state(), _login(), _manage_mcp(), print_banner() (+12 more)

### Community 102 - "test_phased_plan.py"
Cohesion: 0.12
Nodes (25): pydantic, parse_plan(), Plan, PlanPhase, PlanStep, BaseModel, model_validator, Validated, checkpoint-friendly phased plans. (+17 more)

### Community 103 - "re"
Cohesion: 0.27
Nodes (4): re, requests, GitHubRepoDownloader, main()

### Community 104 - "file_io.py"
Cohesion: 0.21
Nodes (15): 4. Internal Tool Subsystem, File tools, Information and planning tools, edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management. (+7 more)

### Community 105 - "mcp_runtime.py"
Cohesion: 0.06
Nodes (27): available_mcp_tools(), call_mcp_tool(), McpConnection, McpRuntime, McpTool, Any, BaseException, Live MCP sessions. Each session stays on its own event-loop thread. The MCP… (+19 more)

### Community 106 - "TestAgentRuntimeFanout"
Cohesion: 0.33
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.26
Nodes (4): ChatRuntime, ChatRuntimeManager, WebSocket, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 108 - "agent/graph.py"
Cohesion: 0.10
Nodes (31): langchain_core_messages, langgraph_types, Agent graph definition., child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy(), _root_owner(), collect_child_node() (+23 more)

### Community 109 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 111 - "os"
Cohesion: 0.18
Nodes (12): os, ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review. (+4 more)

### Community 112 - "now.py"
Cohesion: 0.14
Nodes (12): calendar, datetime, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool (+4 more)

### Community 113 - "repositories/__init__.py"
Cohesion: 0.44
Nodes (3): AuthSessionRepository, _iso(), Any

### Community 114 - "New API chat and first turn"
Cohesion: 0.24
Nodes (5): _deferred_fork(), Any, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Any, New API chat and first turn

### Community 115 - "WebSocket protocol"
Cohesion: 0.25
Nodes (6): Envelope (all messages), 6. WebSocket Runtime, Queues, and Recovery, Agent runtime event conversion, Connection lifecycle, WebSocket debugging checklist, WebSocket protocol

### Community 117 - "security.py"
Cohesion: 0.14
Nodes (18): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+10 more)

### Community 121 - "learn_session"
Cohesion: 0.25
Nodes (7): Agent trace logger, learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, Append-only JSONL writer for one agent., SessionLogger, TestLearnSessionSoftFail

### Community 122 - "truncate_value"
Cohesion: 0.32
Nodes (4): Recursively truncate oversized strings in payloads., truncate_value(), _utc_now(), TestTruncate

### Community 127 - "toolnode.py"
Cohesion: 0.15
Nodes (17): langchain_core_runnables, clear_pause(), is_pause_requested(), maybe_pause(), note_text_from_resume(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node() (+9 more)

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 555 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `CurrentUser` connect `CurrentUser` to `typing`, `CheckpointService`, `require_user`, `PreferencesService`, `mcp_runtime.py`, `health.py`, `api_routes/auth.py`, `chat_service.py`, `api_routes/memory.py`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._
- **Why does `emit()` connect `emit` to `chat_runtime_manager.py`, `agent_core.py`, `agentnode.py`, `AgentCore`, `tool_node`, `trace.py`, `CheckpointService`, `extract_chunks.py`, `log_event`, `test_context_memory.py`, `agent/kb.py`, `emit_child_event`, `subagentnode.py`, `repl.py`, `postgres_checkpointer.py`, `agent_runtime.py`, `run_cli`, `mcp_runtime.py`, `toolnode.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `TurnRenderer` connect `TurnRenderer` to `repl.py`, `run_cli`, `pathlib`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 37 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 37 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._