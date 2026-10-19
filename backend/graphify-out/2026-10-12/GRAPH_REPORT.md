# Graph Report - backend  (2026-10-09)

## Corpus Check
- 223 files · ~221,657 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: .jsonl 10, .bin 4, .example 1)

## Summary
- 2168 nodes · 6017 edges · 112 communities (91 shown, 21 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 506 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Repositories
- test_llm_mock_mode.py
- ChatPacketQueue
- typing
- TurnRenderer
- EVA Agent API — Reference & How to Use
- WebSocket chat session
- llm_client.py
- TestAgentNodePrompt
- utc_now_iso
- db_utils.py
- agentnode.py
- in_run
- prompt_loader.py
- update_context_memory
- sys
- test_llm_logger.py
- agent_runtime.py
- api_routes/auth.py
- AgentCore
- TestSubagentNode
- .run_turn
- require_user
- make_console
- CurrentUser
- api_routes/memory.py
- McpService
- emit
- test_endpoints.py
- test_agent_core.py
- SessionRepository
- Tools: `tool_node`
- web_search.py
- CheckpointService
- context_selector_node
- load_session.py
- ._write_and_read
- embeddings.py
- execute
- Platform Agent Codebase Documentation
- test_embeddings_quiet.py
- unittest_mock
- AgentRuntime
- pathlib
- test_create_user.py
- Settings
- WebSearchArgs
- MemoryRepository
- agentnode_prompt_loader
- field_validator
- log_event
- security.py
- Multi-User Agentic AI Platform — Database Design
- test_agentnode_fast_planner_handoff.py
- graphify.js
- render
- tools_service.py
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- test_prompt_render.py
- route_from_agent
- agent/kb.py
- toolnode.py
- test_db_setup.py
- ws.py
- test_context_memory.py
- ._commit
- llm_logger.py
- executor.py
- Main Agent Graph
- test_prompt_templates.py
- AGENTS.md
- test_experience_system.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- repl.py
- postgres_checkpointer.py
- agent_core.py
- test_subagents_integration.py
- fetch_one
- ReadFileArgs
- health.py
- test_phased_plan.py
- re
- tools/__init__.py
- McpRuntime
- TestAgentRuntimeFanout
- ChatRuntimeManager
- postgres.py
- json_store.py
- now.py
- repositories/__init__.py
- TestMainDispatch
- test_cli_repl.py
- users.py
- src_subagents_learner_agent_store
- learn_session
- truncate_value
- agent/graph.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 119 edges
2. `require_user()` - 72 edges
3. `Repositories` - 69 edges
4. `TurnRenderer` - 59 edges
5. `get_repos()` - 56 edges
6. `emit()` - 55 edges
7. `AgentCore` - 48 edges
8. `get_connection()` - 44 edges
9. `log_event()` - 44 edges
10. `agent_node()` - 43 edges

## Surprising Connections (you probably didn't know these)
- `Add an API resource` --references--> `require_user()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/core/deps.py
- `Entrypoints` --references--> `ChatRuntimeManager`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → api/services/chat_runtime_manager.py
- `Topology` --references--> `route_from_agent()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/edges/routing.py
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Memory Model` --references--> `PlanExecuteState`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/state.py

## Import Cycles
- None detected.

## Communities (112 total, 21 thin omitted)

### Community 0 - "Repositories"
Cohesion: 0.12
Nodes (16): get_prefs(), put_prefs(), Any, Depends, get, put, Repositories, PreferencesUpdateRequest (+8 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.09
Nodes (26): Gateway behavior, LLM call logger and replay cache, call_llm(), call_llm_stream(), _Chunk, _Completion, fake_gateway(), create() (+18 more)

### Community 2 - "ChatPacketQueue"
Cohesion: 0.18
Nodes (7): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior

### Community 3 - "typing"
Cohesion: 0.10
Nodes (28): api_api_routes, Authorized view of active learned experiences., pick_files(), post, list_subagents(), Any, Depends, get (+20 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.11
Nodes (10): Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., TurnRenderer, make_console() (+2 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.08
Nodes (23): Analytics, Authentication, Chats, Checkpoints & rollback, Data store (`data/`), `DELETE /v1/chats/{chat_id}` (auth), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth) (+15 more)

### Community 6 - "WebSocket chat session"
Cohesion: 0.15
Nodes (12): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session, 6. WebSocket Runtime, Queues, and Recovery (+4 more)

### Community 7 - "llm_client.py"
Cohesion: 0.07
Nodes (44): collections, OpenAI, emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages(), _build_provider() (+36 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "utc_now_iso"
Cohesion: 0.39
Nodes (6): utc_now_iso(), _done(), _target(), _done(), _target(), set_trace_parent()

### Community 10 - "db_utils.py"
Cohesion: 0.17
Nodes (14): contextlib, psycopg, psycopg_pool, psycopg_rows, execute(), fetch_all(), fetch_one(), get_connection() (+6 more)

### Community 11 - "agentnode.py"
Cohesion: 0.08
Nodes (29): BaseMessage, Main agent loop, Recommended debugging workflow, agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation() (+21 more)

### Community 12 - "in_run"
Cohesion: 0.13
Nodes (21): AgentRepository, available_mcp_tools(), call_mcp_tool(), McpTool, Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, Retrieval in the main agent, httpx, mcp (+13 more)

### Community 13 - "prompt_loader.py"
Cohesion: 0.13
Nodes (22): Major prompt functions, _armory_text(), fast_agent_prompt_loader(), _fmt(), _load_module(), _Node, _parse(), planner_agent_prompt_loader() (+14 more)

### Community 14 - "update_context_memory"
Cohesion: 0.12
Nodes (12): 2. Agent State, Memory, and Planner Decisions, Debugging planner problems, Planner response parsing details, Why execution memory is split, Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory() (+4 more)

### Community 15 - "sys"
Cohesion: 0.14
Nodes (11): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), sys, Unit tests for the CLI theme definition., TestTheme (+3 more)

### Community 16 - "test_llm_logger.py"
Cohesion: 0.11
Nodes (14): src_utils, build_cache_key(), current_session_ids(), lookup_cached_response(), Stable hash of everything that can change the answer. Fields are length-…, Most recent successful, non-replayed call with this exact key. Global across…, Agent identity from the ContextVar-bound logger. Falls back to…, Tests for the LLM call recorder and its mock-replay cache key. No live Postgres… (+6 more)

### Community 17 - "agent_runtime.py"
Cohesion: 0.22
Nodes (13): get_settings(), configure_logging(), get_pool(), ConnectionPool, lifespan(), ensure_client_path(), get_agent_app(), asyncio (+5 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "AgentCore"
Cohesion: 0.11
Nodes (7): AgentCore, AgentID, Message, Armory, Guardrails, Observability, Agent policy facets: memory, armory, guardrails and observability.

### Community 20 - "TestSubagentNode"
Cohesion: 0.20
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - ".run_turn"
Cohesion: 0.47
Nodes (4): on_child_event(), on_subagent_event(), Any, _truncate()

### Community 22 - "require_user"
Cohesion: 0.14
Nodes (31): Any, Depends, get, summary(), get_experience(), list_experiences(), Depends, get (+23 more)

### Community 23 - "make_console"
Cohesion: 0.23
Nodes (8): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestPromptForInterrupt

### Community 24 - "CurrentUser"
Cohesion: 0.13
Nodes (38): `GET /v1/chats/{chat_id}` (auth), create_chat(), delete_chat(), get_chat(), get_policy(), list_chats(), list_memory_extraction_requests(), delete (+30 more)

### Community 25 - "api_routes/memory.py"
Cohesion: 0.22
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "McpService"
Cohesion: 0.12
Nodes (13): McpCreateRequest, McpUpdateRequest, model_validator, connection_log(), McpService, public_server(), Any, mcp_server_fastmcp (+5 more)

### Community 27 - "emit"
Cohesion: 0.18
Nodes (25): create_app(), trace_requests(), work(), bind(), bind_from_config(), emit(), _error(), _persist() (+17 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "test_agent_core.py"
Cohesion: 0.08
Nodes (20): ChildEventCallback, ChildRunner, Bounded, process-local execution of durable child runs., Before a parent finishes, collect all its children by persisted lineage., reset_child_callback(), set_child_callback(), Bind a token callback for the current context; returns a reset token., set_token_callback() (+12 more)

### Community 30 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "Tools: `tool_node`"
Cohesion: 0.13
Nodes (16): 4. Internal Tool Subsystem, Durable user-memory tools, Information and planning tools, Tools: `tool_node`, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces… (+8 more)

### Community 32 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 33 - "CheckpointService"
Cohesion: 0.23
Nodes (14): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+6 more)

### Community 34 - "context_selector_node"
Cohesion: 0.39
Nodes (3): context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "load_session.py"
Cohesion: 0.10
Nodes (33): PreferencesRepository, Experience API view, Full learner sequence, Learner graph, Learning Agent and Experience System, Step 1: load trajectory, Step 3: persist and index, memory_action_allowed() (+25 more)

### Community 36 - "._write_and_read"
Cohesion: 0.18
Nodes (7): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall

### Community 37 - "embeddings.py"
Cohesion: 0.15
Nodes (16): 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, Step 2: extract reusable advice, hashlib, numpy, _embed_numpy(), embed_text(), embed_texts() (+8 more)

### Community 38 - "execute"
Cohesion: 0.15
Nodes (17): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), McpRepository, _load() (+9 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.09
Nodes (20): FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Current Extension Points and Limits, Entrypoints, Environment, HTTP API and WebSocket Runtime, LLM Client, Observability, and Replay, Logging and mock replay (+12 more)

### Community 40 - "test_embeddings_quiet.py"
Cohesion: 0.15
Nodes (8): list, src_models, _FakeEncoded, _FakeModel, HfLoadIsQuiet, _install_fakes(), The HF embedding backend must load quietly: no 'Loading weights' tqdm bar, no…, Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 41 - "unittest_mock"
Cohesion: 0.25
Nodes (4): object, Focused checks for CLI-configurable agent runtime controls., TestRuntimeControls, unittest_mock

### Community 42 - "AgentRuntime"
Cohesion: 0.13
Nodes (9): AgentRuntime, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, Thin re-export — stream bridging lives in agent_runtime for cohesion., Event, emit_child_event(), Any, test_child_events_emit_started_step_finished() (+1 more)

### Community 43 - "pathlib"
Cohesion: 0.15
Nodes (11): BaseSettings, Settings, Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., dotenv, generate_tree(), Path, Recursively generates a string representation of a directory tree., functools (+3 more)

### Community 45 - "Settings"
Cohesion: 0.40
Nodes (3): BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 46 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 48 - "agentnode_prompt_loader"
Cohesion: 0.18
Nodes (11): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, Add a planner-callable sub-agent, Add a prompt block, Add an API resource, Add an internal tool, Practical prompt-debug method, System versus user prompt (+3 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "log_event"
Cohesion: 0.12
Nodes (34): Agent trace logger, json, os, DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional…, bind_session_logger(), flush_pending_logs() (+26 more)

### Community 52 - "security.py"
Cohesion: 0.24
Nodes (9): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, argon2, argon2_exceptions, jwt (+1 more)

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "test_agentnode_fast_planner_handoff.py"
Cohesion: 0.53
Nodes (8): src_agent_nodes, _config(), object, _state(), test_fast_plan_handoff_accepts_planner_finish_without_steps_json(), test_fast_plan_handoff_missing_steps_after_retry_surfaces_clear_error(), test_fast_plan_handoff_retries_once_then_parses_plan(), test_plan_parse_failure_retries_once_then_returns_graceful_message()

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 57 - "tools_service.py"
Cohesion: 0.47
Nodes (7): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info(), src_tools

### Community 61 - "test_prompt_render.py"
Cohesion: 0.19
Nodes (6): _eval_cond(), _present(), Tests for the declarative prompt renderer in prompt_loader.py., The prototype returned True here, so `if=turn_start` always fired and the model…, TestConditions, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.19
Nodes (6): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, Conditional edge out of input_security_gate. Reuses the same…, route_from_agent(), route_from_input_gate(), TestRouting, TestRouting

### Community 63 - "agent/kb.py"
Cohesion: 0.05
Nodes (100): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+92 more)

### Community 64 - "toolnode.py"
Cohesion: 0.07
Nodes (41): Any, SubagentsService, Sub-agents: `subagent_node` and gate, langchain_core_runnables, langgraph_graph_message, pydantic, clear_pause(), is_pause_requested() (+33 more)

### Community 65 - "test_db_setup.py"
Cohesion: 0.13
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "test_context_memory.py"
Cohesion: 0.09
Nodes (23): langgraph_graph, build_execution_memory_index(), count_content_tokens(), empty_context_memory(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context. (+15 more)

### Community 68 - "._commit"
Cohesion: 0.18
Nodes (6): emit_tag(), _format_args(), Any, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short()

### Community 69 - "llm_logger.py"
Cohesion: 0.13
Nodes (22): atexit, queue, _ensure_writer_started(), Path, _safe_agent_id(), _writer_loop(), build_record(), _db_loop() (+14 more)

### Community 71 - "executor.py"
Cohesion: 0.22
Nodes (15): Command execution tools, execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python… (+7 more)

### Community 72 - "Main Agent Graph"
Cohesion: 0.22
Nodes (9): Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, State, Topology, AgentConfig, BaseModel (+1 more)

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.13
Nodes (13): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+5 more)

### Community 75 - "test_experience_system.py"
Cohesion: 0.07
Nodes (25): CLI, Commands, Flow, Idle scheduling and branch handling, BackgroundIdleWatcher, IdleWatcher, _is_run_active(), _mark_session() (+17 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 89 - "repl.py"
Cohesion: 0.10
Nodes (39): api_db_repositories, contextvars, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, PromptSession, rich_prompt (+31 more)

### Community 92 - "postgres_checkpointer.py"
Cohesion: 0.07
Nodes (56): 1. End-to-End Turn Execution, 7. PostgreSQL, Repositories, and Checkpoints, 8. Observability, Logs, and LLM Replay, Checkpointer function map, Database troubleshooting, Detailed Subsystem Reference, Functions to start with when tracing a turn, New API chat and first turn (+48 more)

### Community 94 - "agent_core.py"
Cohesion: 0.14
Nodes (26): Durable AgentCore identities, run reservations, and child results., concurrent_futures, copy, dataclasses, Agent lifecycle facade and compatibility exports., ChildHandle, Policy, Core agent dataclasses shared across runtime components. (+18 more)

### Community 97 - "test_subagents_integration.py"
Cohesion: 0.12
Nodes (12): WebSocket protocol helpers., emit_subagent_event(), Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), SubagentEventCallback, tempfile (+4 more)

### Community 98 - "fetch_one"
Cohesion: 0.18
Nodes (4): fetch_one(), Any, MemoryExtractionRepository, Any

### Community 99 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, model_validator, ReadFileArgs, SearchFileArgs

### Community 101 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 102 - "test_phased_plan.py"
Cohesion: 0.10
Nodes (29): _escape_unescaped_quotes_in_json_strings(), parse_plan(), Plan, PlanPhase, PlanStep, BaseModel, model_validator, Validated, checkpoint-friendly phased plans. (+21 more)

### Community 103 - "re"
Cohesion: 0.27
Nodes (4): re, requests, GitHubRepoDownloader, main()

### Community 104 - "tools/__init__.py"
Cohesion: 0.23
Nodes (14): File tools, edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management., Read content from a text-based file. Supports optional line-range slicing via…, Make targeted edits to a text file by replacing an exact string match. Finds… (+6 more)

### Community 105 - "McpRuntime"
Cohesion: 0.12
Nodes (6): McpConnection, McpRuntime, Any, BaseException, test_http_404_is_reported_as_endpoint_error(), test_http_transport_connects_to_real_streamable_server()

### Community 106 - "TestAgentRuntimeFanout"
Cohesion: 0.33
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.18
Nodes (7): ChatRuntime, ChatRuntimeManager, _deferred_fork(), Any, WebSocket, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs.

### Community 109 - "postgres.py"
Cohesion: 0.20
Nodes (7): fetch_all(), Any, Process-wide Postgres connection pool + small query helpers. This is the shared…, _iso(), Any, _row_to_entry(), uuid

### Community 111 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 112 - "now.py"
Cohesion: 0.14
Nodes (11): calendar, datetime, langchain_core_tools, platform, GetCurrentDatetimeInfoArgs, BaseModel, field_validator, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 113 - "repositories/__init__.py"
Cohesion: 0.27
Nodes (6): AnalyticsRepository, Any, AuthSessionRepository, _iso(), Any, Repository map

### Community 115 - "test_cli_repl.py"
Cohesion: 0.09
Nodes (18): io, rich_console, rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, parse_command() (+10 more)

### Community 117 - "users.py"
Cohesion: 0.18
Nodes (14): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+6 more)

### Community 121 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 122 - "truncate_value"
Cohesion: 0.32
Nodes (4): Recursively truncate oversized strings in payloads., truncate_value(), _utc_now(), TestTruncate

### Community 127 - "agent/graph.py"
Cohesion: 0.10
Nodes (34): langchain_core_messages, langgraph_types, Agent graph definition., _map_plan_step_to_next_step(), child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy(), _root_owner() (+26 more)

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 557 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `repl.py`, `test_cli_repl.py`, `._commit`, `make_console`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `CheckpointService`, `ChatPacketQueue`, `EVA Agent API — Reference & How to Use`, `WebSocket chat session`, `Platform Agent Codebase Documentation`, `utc_now_iso`, `AgentRuntime`, `agent_runtime.py`, `AgentCore`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `AgentCore` connect `AgentCore` to `load_session.py`, `utc_now_iso`, `ChatRuntimeManager`, `in_run`, `MemoryRepository`, `agent_runtime.py`, `CurrentUser`, `repl.py`, `test_agent_core.py`, `agent_core.py`, `agent/graph.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 57 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 57 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 39 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 39 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._