# Graph Report - backend  (2026-10-13)

## Corpus Check
- 224 files · ~289,744 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 19 file(s) not represented in the graph (top: .jsonl 12, .bin 4, .example 1)

## Summary
- 2170 nodes · 6090 edges · 121 communities (98 shown, 23 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 529 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- typing
- test_llm_mock_mode.py
- ChatPacketQueue
- endpoint.py
- TurnRenderer
- EVA Agent API — Reference & How to Use
- in_run
- llm_client.py
- TestAgentNodePrompt
- armory.py
- postgres.py
- agentnode.py
- test_experience_system.py
- test_prompt_render.py
- update_context_memory
- test_context_memory.py
- test_llm_logger.py
- agent_runtime.py
- api_routes/auth.py
- AgentCore
- TestSubagentNode
- build_config
- require_user
- make_console
- ChatService
- api_routes/memory.py
- CurrentUser
- emit
- test_endpoints.py
- test_agent_core.py
- SessionRepository
- decompose_query
- web_search.py
- CheckpointService
- context_selector_node
- load_session.py
- ._write_and_read
- embeddings.py
- mcp.py
- Platform Agent Codebase Documentation
- BackgroundIdleWatcher
- TestRuntimeControls
- .run_turn
- src/config.py
- tool_node
- list_checkpoint_tree
- WebSearchArgs
- active_checkpoint_path
- agentnode_prompt_loader
- prompt_loader.py
- field_validator
- log_event
- repositories/analytics.py
- Multi-User Agentic AI Platform — Database Design
- test_agentnode_fast_planner_handoff.py
- graphify.js
- render
- tools_service.py
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- test_dispatcher_runs_sequential_phases_without_reinvoking_agent
- _present
- route_from_agent
- agent/kb.py
- subagentnode.py
- test_db_setup.py
- ws.py
- agent/memory.py
- ._commit
- llm_logger.py
- subagent_stream.py
- executor.py
- sys_info.py
- test_prompt_templates.py
- AGENTS.md
- idle_watcher.py
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- _eval_cond
- repl.py
- security.py
- main.py
- postgres_checkpointer.py
- policy_schema.py
- get_experience
- run_turn_interactive
- AgentRepository
- ReadFileArgs
- .get
- health.py
- test_phased_plan.py
- GitHubRepoDownloader
- tools/__init__.py
- McpRuntime
- TestAgentRuntimeFanout
- ChatRuntimeManager
- generate_tree
- repositories/memory.py
- json_store.py
- pydantic
- execute
- TestMainDispatch
- test_cli_repl.py
- TestSubagentRegistry
- users.py
- src_subagents_learner_agent_store
- truncate_value
- plan_dispatcher.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 123 edges
2. `Repositories` - 75 edges
3. `require_user()` - 75 edges
4. `get_repos()` - 60 edges
5. `TurnRenderer` - 59 edges
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
- `Recommended debugging workflow` --references--> `_parse_response()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py

## Import Cycles
- None detected.

## Communities (121 total, 23 thin omitted)

### Community 0 - "typing"
Cohesion: 0.09
Nodes (26): Any, Depends, get, summary(), Authorized view of active learned experiences., get_prefs(), put_prefs(), Any (+18 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.09
Nodes (27): Gateway behavior, LLM call logger and replay cache, src_models, call_llm(), call_llm_stream(), _Chunk, _Completion, fake_gateway() (+19 more)

### Community 2 - "ChatPacketQueue"
Cohesion: 0.12
Nodes (12): Envelope (all messages), ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., 6. WebSocket Runtime, Queues, and Recovery, Add a WebSocket event (+4 more)

### Community 3 - "endpoint.py"
Cohesion: 0.23
Nodes (10): api_ws, agent_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject(), WebSocket protocol helpers. (+2 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.11
Nodes (10): Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., TurnRenderer, make_console() (+2 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.08
Nodes (24): Analytics, Authentication, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), EVA Agent API — Reference & How to Use, Example messages (+16 more)

### Community 6 - "in_run"
Cohesion: 0.13
Nodes (25): available_mcp_tools(), call_mcp_tool(), McpTool, Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, datetime, httpx, mcp, mcp_client_sse (+17 more)

### Community 7 - "llm_client.py"
Cohesion: 0.06
Nodes (48): collections, OpenAI, emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages(), _build_provider() (+40 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "armory.py"
Cohesion: 0.21
Nodes (19): connect_mcp(), create_mcp(), delete_mcp(), disconnect_mcp(), get_armory(), get_mcp(), import_mcp(), list_mcp() (+11 more)

### Community 10 - "postgres.py"
Cohesion: 0.18
Nodes (10): Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute(), get_pool(), ConnectionPool (+2 more)

### Community 11 - "agentnode.py"
Cohesion: 0.09
Nodes (32): BaseMessage, 1. End-to-End Turn Execution, Functions to start with when tracing a turn, Main agent loop, agent_node(), _on_token(), run_planner_call(), _extract_tag() (+24 more)

### Community 12 - "test_experience_system.py"
Cohesion: 0.10
Nodes (21): Full learner sequence, Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, Standalone learner agent: extract experience chunks from idle chats., build_embed_text() (+13 more)

### Community 13 - "test_prompt_render.py"
Cohesion: 0.20
Nodes (11): _fmt(), PromptRenderError, Any, Exception, Serialize structured prompt context as TOON., Raised in strict mode when a template references an unknown variable., replace(), to_toon() (+3 more)

### Community 14 - "update_context_memory"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Community 15 - "test_context_memory.py"
Cohesion: 0.07
Nodes (35): State, langchain_core_messages, langchain_core_runnables, langgraph_graph, langgraph_graph_message, pathlib, scripts, Conditional edge out of input_security_gate. Reuses the same… (+27 more)

### Community 16 - "test_llm_logger.py"
Cohesion: 0.11
Nodes (16): json, os, DecomposeQueryArgs, BaseModel, Tool for decomposing a user query into a structured, multi-dimensional…, src_utils, current_session_ids(), lookup_cached_response() (+8 more)

### Community 17 - "agent_runtime.py"
Cohesion: 0.15
Nodes (18): api_api_routes, get_settings(), BaseSettings, Settings, configure_logging(), get_pool(), ConnectionPool, lifespan() (+10 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "AgentCore"
Cohesion: 0.09
Nodes (16): concurrent_futures, AgentCore, Agent lifecycle facade and compatibility exports., AgentID, ChildHandle, Message, Policy, Core agent dataclasses shared across runtime components. (+8 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.20
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - "build_config"
Cohesion: 0.21
Nodes (14): Checkpointer function map, build_config(), get_thread_state(), _message_content(), _message_role(), Any, RunnableConfig, Sync an agent's active transcript from its checkpoint tip. (+6 more)

### Community 22 - "require_user"
Cohesion: 0.24
Nodes (30): _armory(), checkpoint_tree(), create_agent(), delete_agent(), get_agent(), get_agent_analytics(), get_agent_mcp(), get_agent_memory() (+22 more)

### Community 23 - "make_console"
Cohesion: 0.20
Nodes (9): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestHumanInputNode (+1 more)

### Community 24 - "ChatService"
Cohesion: 0.10
Nodes (33): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `GET /v1/chats/{chat_id}` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth), ChatCreateRequest, ChatDetailOut (+25 more)

### Community 25 - "api_routes/memory.py"
Cohesion: 0.22
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "CurrentUser"
Cohesion: 0.14
Nodes (14): CurrentUser, McpCreateRequest, McpUpdateRequest, model_validator, connection_log(), McpService, public_server(), Any (+6 more)

### Community 27 - "emit"
Cohesion: 0.13
Nodes (21): create_app(), trace_requests(), MemoryRepository, work(), Memory, bind(), emit(), _error() (+13 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "test_agent_core.py"
Cohesion: 0.10
Nodes (17): ChildEventCallback, ChildRunner, Bounded, process-local execution of durable child runs., Before a parent finishes, collect all its children by persisted lineage., reset_child_callback(), set_child_callback(), FakeAgents, parent_core() (+9 more)

### Community 30 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "decompose_query"
Cohesion: 0.17
Nodes (11): 4. Internal Tool Subsystem, Durable user-memory tools, Information and planning tools, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…, get_current_datetime_info() (+3 more)

### Community 32 - "web_search.py"
Cohesion: 0.26
Nodes (11): ddgs, _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set… (+3 more)

### Community 33 - "CheckpointService"
Cohesion: 0.38
Nodes (3): _services(), CheckpointService, Service function map

### Community 34 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "load_session.py"
Cohesion: 0.10
Nodes (30): PreferencesRepository, Experience API view, Learner graph, Learning Agent and Experience System, Retrieval in the main agent, Step 1: load trajectory, Step 3: persist and index, psycopg_types_json (+22 more)

### Community 36 - "._write_and_read"
Cohesion: 0.18
Nodes (7): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall

### Community 37 - "embeddings.py"
Cohesion: 0.08
Nodes (22): 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, Step 2: extract reusable advice, hashlib, list, numpy, _embed_numpy(), embed_text() (+14 more)

### Community 38 - "mcp.py"
Cohesion: 0.22
Nodes (12): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+4 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.08
Nodes (25): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Current Extension Points and Limits (+17 more)

### Community 40 - "BackgroundIdleWatcher"
Cohesion: 0.15
Nodes (8): CLI, Commands, Flow, Idle scheduling and branch handling, BackgroundIdleWatcher, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread., Run the async watcher in a daemon thread for non-async entrypoints.

### Community 42 - ".run_turn"
Cohesion: 0.12
Nodes (12): AgentRuntime, on_child_event(), on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate() (+4 more)

### Community 43 - "src/config.py"
Cohesion: 0.20
Nodes (8): dotenv, functools, pydantic_settings, get_settings(), BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 44 - "tool_node"
Cohesion: 0.28
Nodes (5): empty_context_memory(), RunnableConfig, tool_node(), TestToolAndSubagentIngest, TestToonTokenSavings

### Community 45 - "list_checkpoint_tree"
Cohesion: 0.17
Nodes (11): _filter_checkpoint_tree(), has_pending_interrupt(), _infer_node(), _is_redundant_checkpoint(), list_checkpoint_tree(), _node_from_metadata(), Best-effort label for "which node just wrote this checkpoint" — there is no…, Prefer LangGraph checkpoint metadata (authoritative node writes). (+3 more)

### Community 46 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 47 - "active_checkpoint_path"
Cohesion: 0.20
Nodes (9): 7. PostgreSQL, Repositories, and Checkpoints, Database troubleshooting, PostgreSQL responsibilities, active_checkpoint_path(), initial_state_for_thread(), PostgresSaver, Checkpoint ids on the path from the current graph tip back to the root. Used to…, PostgresSaver that also mirrors new messages into the `messages` table. (+1 more)

### Community 48 - "agentnode_prompt_loader"
Cohesion: 0.09
Nodes (17): 10. Safe Extension Guide, 2. Agent State, Memory, and Planner Decisions, 5. API Layer and Service Boundaries, 8. Observability, Logs, and LLM Replay, Add a planner-callable sub-agent, Add a prompt block, Add an API resource, Add an internal tool (+9 more)

### Community 49 - "prompt_loader.py"
Cohesion: 0.31
Nodes (8): Major prompt functions, _armory_text(), _Node, _parse(), Prompt rendering and loading for every agent and sub-agent in the project. One…, _render_node(), _subst(), _tidy()

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "log_event"
Cohesion: 0.13
Nodes (29): Agent trace logger, bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_context_select(), log_event(), log_llm_request() (+21 more)

### Community 52 - "repositories/analytics.py"
Cohesion: 0.31
Nodes (8): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any, test_summary_can_filter_one_agent()

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
Cohesion: 0.42
Nodes (7): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info(), ToolsService

### Community 60 - "test_dispatcher_runs_sequential_phases_without_reinvoking_agent"
Cohesion: 0.38
Nodes (8): dispatch_phase(), phase_collector_node(), plan_dispatcher_node(), step(), test_dispatcher_runs_sequential_phases_without_reinvoking_agent(), test_parallel_failure_replans_and_does_not_run_later_phase(), test_parallel_phase_fanout_and_ordered_merge(), fake_tool()

### Community 61 - "_present"
Cohesion: 0.24
Nodes (6): 3. Prompt Rendering Deep Dive, Practical prompt-debug method, System versus user prompt, _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.22
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "agent/kb.py"
Cohesion: 0.05
Nodes (102): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+94 more)

### Community 64 - "subagentnode.py"
Cohesion: 0.07
Nodes (38): Any, Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, Sub-agents: `subagent_node` and gate, Topology, clear_pause() (+30 more)

### Community 65 - "test_db_setup.py"
Cohesion: 0.13
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "agent/memory.py"
Cohesion: 0.12
Nodes (14): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+6 more)

### Community 68 - "._commit"
Cohesion: 0.18
Nodes (6): emit_tag(), _format_args(), Any, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short()

### Community 69 - "llm_logger.py"
Cohesion: 0.12
Nodes (26): atexit, queue, _ensure_writer_started(), _safe_agent_id(), _writer_loop(), build_record(), _db_loop(), _db_params() (+18 more)

### Community 70 - "subagent_stream.py"
Cohesion: 0.31
Nodes (7): contextvars, emit_child_event(), emit_subagent_event(), Any, Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).…, test_child_events_emit_started_step_finished(), fake_run_turn()

### Community 71 - "executor.py"
Cohesion: 0.21
Nodes (16): Command execution tools, Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool (+8 more)

### Community 72 - "sys_info.py"
Cohesion: 0.25
Nodes (7): langchain_core_tools, platform, Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info()

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.13
Nodes (13): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+5 more)

### Community 75 - "idle_watcher.py"
Cohesion: 0.18
Nodes (11): _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+3 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 89 - "repl.py"
Cohesion: 0.12
Nodes (31): api_db_repositories, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, PromptSession, rich_prompt, rich_table (+23 more)

### Community 90 - "security.py"
Cohesion: 0.33
Nodes (4): argon2, argon2_exceptions, jwt, secrets

### Community 91 - "main.py"
Cohesion: 0.47
Nodes (5): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli()

### Community 92 - "postgres_checkpointer.py"
Cohesion: 0.18
Nodes (17): langgraph_checkpoint_postgres, _ensure_branch_learn_table(), _ensure_message_sync_schema(), get_checkpointer(), _get_pool(), is_leaf_learned(), list_checkpoints(), list_leaf_checkpoints() (+9 more)

### Community 94 - "policy_schema.py"
Cohesion: 0.21
Nodes (16): Durable AgentCore identities, run reservations, and child results., copy, default_policy(), Policy defaults and intersection helpers., _as_string_list(), _bool(), _canonical_resource(), effective_memory_policy() (+8 more)

### Community 96 - "get_experience"
Cohesion: 0.67
Nodes (4): get_experience(), list_experiences(), Depends, get

### Community 97 - "run_turn_interactive"
Cohesion: 0.12
Nodes (16): Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_token_callback(), reset_usage_callback(), set_token_callback() (+8 more)

### Community 98 - "AgentRepository"
Cohesion: 0.11
Nodes (7): fetch_all(), fetch_one(), Any, AgentRepository, Any, MemoryExtractionRepository, Any

### Community 99 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, model_validator, ReadFileArgs, SearchFileArgs

### Community 101 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 102 - "test_phased_plan.py"
Cohesion: 0.10
Nodes (29): _escape_unescaped_quotes_in_json_strings(), parse_plan(), Plan, PlanPhase, PlanStep, BaseModel, model_validator, Validated, checkpoint-friendly phased plans. (+21 more)

### Community 103 - "GitHubRepoDownloader"
Cohesion: 0.27
Nodes (4): argparse, requests, GitHubRepoDownloader, main()

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
Cohesion: 0.14
Nodes (13): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+5 more)

### Community 108 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 109 - "repositories/memory.py"
Cohesion: 0.60
Nodes (3): _iso(), Any, _row_to_entry()

### Community 111 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 112 - "pydantic"
Cohesion: 0.20
Nodes (8): calendar, pydantic, GetCurrentDatetimeInfoArgs, BaseModel, field_validator, Internal tool for getting comprehensive date and time information in the user's…, tzlocal, zoneinfo

### Community 113 - "execute"
Cohesion: 0.33
Nodes (5): execute(), Run an INSERT/UPDATE/DELETE, return affected row count., AuthSessionRepository, _iso(), Any

### Community 115 - "test_cli_repl.py"
Cohesion: 0.10
Nodes (16): io, rich_console, rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, parse_command() (+8 more)

### Community 117 - "users.py"
Cohesion: 0.26
Nodes (11): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+3 more)

### Community 122 - "truncate_value"
Cohesion: 0.47
Nodes (3): Recursively truncate oversized strings in payloads., truncate_value(), TestTruncate

### Community 127 - "plan_dispatcher.py"
Cohesion: 0.12
Nodes (22): Agent runtime event conversion, langgraph_types, _coerce_int(), _map_plan_step_to_next_step(), child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy(), _root_owner() (+14 more)

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 550 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `run_turn_interactive`, `._commit`, `test_cli_repl.py`, `make_console`, `repl.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `AgentCore` connect `AgentCore` to `run_turn_interactive`, `AgentRepository`, `load_session.py`, `ChatRuntimeManager`, `test_experience_system.py`, `agent_runtime.py`, `ChatService`, `repl.py`, `emit`, `test_agent_core.py`, `policy_schema.py`, `plan_dispatcher.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `ChatPacketQueue`, `EVA Agent API — Reference & How to Use`, `Platform Agent Codebase Documentation`, `.run_turn`, `agent_runtime.py`, `AgentCore`, `ChatService`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 64 inferred relationships involving `CurrentUser` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`CurrentUser` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Repositories` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`Repositories` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._