# Graph Report - backend  (2026-10-13)

## Corpus Check
- 226 files · ~310,929 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 21 file(s) not represented in the graph (top: .jsonl 14, .bin 4, .example 1)

## Summary
- 2197 nodes · 6174 edges · 128 communities (107 shown, 21 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 533 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- api_routes/preferences.py
- test_llm_mock_mode.py
- ChatPacketQueue
- AnalyticsRepository
- TurnRenderer
- EVA Agent API — Reference & How to Use
- mcp_runtime.py
- llm_client.py
- TestAgentNodePrompt
- Repositories
- typing
- agentnode.py
- test_experience_system.py
- prompt_loader.py
- slice_by_tokens
- agent/graph.py
- lookup_cached_response
- agent_runtime.py
- api_routes/auth.py
- AgentCore
- TestSubagentNode
- chat_service.py
- require_user
- make_console
- ChatService
- MemoryService
- CurrentUser
- emit
- endpoint.py
- test_agent_core.py
- SessionRepository
- web_search
- make_console
- CheckpointService
- context_selector_node
- load_session.py
- ._write_and_read
- embeddings.py
- mcp.py
- Platform Agent Codebase Documentation
- BackgroundIdleWatcher
- in_run
- .run_turn
- src/config.py
- tool_node
- AnalyticsService
- WebSearchArgs
- test_embeddings_quiet.py
- _parse_response
- control.py
- executor.py
- log_event
- paths.py
- Multi-User Agentic AI Platform — Database Design
- api_routes/files.py
- graphify.js
- render
- tools_service.py
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- agentnode_prompt_loader
- _present
- route_from_agent
- agent/kb.py
- test_subagents_integration.py
- test_db_setup.py
- ws.py
- test_context_memory.py
- update_context_memory
- llm_logger.py
- AgentRuntime
- Tools: `tool_node`
- ChildRunner
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
- fetch_one
- main.py
- postgres_checkpointer.py
- agent_core.py
- plan.py
- run_turn_interactive
- AgentRepository
- ReadFileArgs
- execute
- health.py
- test_phased_plan.py
- GitHubRepoDownloader
- tools/__init__.py
- McpRuntime
- TestAgentRuntimeFanout
- ChatRuntimeManager
- WebSocket chat session
- .add_entry
- json_store.py
- json
- Repository map
- ._begin_reserved_run
- pathlib
- context_manager.py
- security.py
- Learning Agent and Experience System
- _session_prompt
- src_subagents_learner_agent_store
- learn_session
- truncate_value
- .test_resumes_after_interrupt
- user_from_token
- parse_command
- decompose_query
- 6. WebSocket Runtime, Queues, and Recovery

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
- `Main agent loop` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Main prompt contract` --references--> `agent_node()`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/nodes/agentnode.py
- `Memory Model` --references--> `PlanExecuteState`  [INFERRED]
  CODEBASE_DOCUMENTATION.md → src/agent/state.py

## Import Cycles
- None detected.

## Communities (128 total, 21 thin omitted)

### Community 0 - "api_routes/preferences.py"
Cohesion: 0.18
Nodes (10): get_prefs(), put_prefs(), Any, Depends, get, put, PreferencesUpdateRequest, model_validator (+2 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.09
Nodes (28): Gateway behavior, LLM call logger and replay cache, call_llm(), call_llm_stream(), Summarise the given text using the LLM., summarise(), _Chunk, _Completion (+20 more)

### Community 2 - "ChatPacketQueue"
Cohesion: 0.18
Nodes (7): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior

### Community 3 - "AnalyticsRepository"
Cohesion: 0.29
Nodes (4): AnalyticsRepository, Any, _TimeWindow, test_summary_can_filter_one_agent()

### Community 4 - "TurnRenderer"
Cohesion: 0.10
Nodes (13): emit_tag(), _format_args(), Any, Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning. (+5 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.11
Nodes (18): Analytics, Authentication, Checkpoints & rollback, Data store (`data/`), EVA Agent API — Reference & How to Use, `GET /v1/analytics/summary` (auth), `GET /v1/auth/me` (auth), `GET /v1/chats/{chat_id}/checkpoints` (auth) (+10 more)

### Community 6 - "mcp_runtime.py"
Cohesion: 0.18
Nodes (14): available_mcp_tools(), call_mcp_tool(), McpTool, Live MCP sessions. Each session stays on its own event-loop thread. The MCP…, asyncio, httpx, langchain_core_runnables, mcp (+6 more)

### Community 7 - "llm_client.py"
Cohesion: 0.08
Nodes (37): OpenAI, emit_usage(), Any, _apply_output_type_instruction(), BaseLLMProvider, _build_messages(), _build_provider(), _cache_key() (+29 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "Repositories"
Cohesion: 0.15
Nodes (22): connect_mcp(), create_mcp(), delete_mcp(), disconnect_mcp(), get_armory(), get_mcp(), import_mcp(), list_mcp() (+14 more)

### Community 10 - "typing"
Cohesion: 0.12
Nodes (19): fetch_all(), get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, psycopg, psycopg_pool, psycopg_rows, psycopg_types_json (+11 more)

### Community 11 - "agentnode.py"
Cohesion: 0.11
Nodes (32): BaseMessage, src_agent_nodes, agent_node(), _on_token(), run_planner_call(), _coerce_int(), _extract_tag(), _format_conversation() (+24 more)

### Community 12 - "test_experience_system.py"
Cohesion: 0.11
Nodes (18): Full learner sequence, Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., format_experiences_for_prompt() (+10 more)

### Community 13 - "prompt_loader.py"
Cohesion: 0.13
Nodes (20): Major prompt functions, _armory_text(), _fmt(), _Node, _parse(), PromptRenderError, Any, Exception (+12 more)

### Community 14 - "slice_by_tokens"
Cohesion: 0.28
Nodes (5): Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, _tokens_of_chars()

### Community 15 - "agent/graph.py"
Cohesion: 0.08
Nodes (38): State, langchain_core_messages, langgraph_graph, langgraph_graph_message, langgraph_types, note_text_from_resume(), Best-effort extraction of free-text the user typed while paused/asked,…, Conditional edge out of input_security_gate. Reuses the same… (+30 more)

### Community 16 - "lookup_cached_response"
Cohesion: 0.47
Nodes (3): lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, TestLookupSoftFails

### Community 17 - "agent_runtime.py"
Cohesion: 0.16
Nodes (18): api_api_routes, create_app(), get_settings(), BaseSettings, Settings, configure_logging(), lifespan(), Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1). (+10 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.25
Nodes (14): login(), logout(), me(), Depends, get, post, create_access_token(), new_session_id() (+6 more)

### Community 19 - "AgentCore"
Cohesion: 0.11
Nodes (6): AgentCore, AgentID, Message, Armory, Guardrails, Observability

### Community 20 - "TestSubagentNode"
Cohesion: 0.20
Nodes (4): Extra <parameters> on an agent_call reach the sub-agent as…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - "chat_service.py"
Cohesion: 0.07
Nodes (49): is_placeholder_title(), Derive a short default chat title from the first human message., True for empty / New chat / legacy `Chat <locale datetime>` titles., title_from_first_message(), _first_human_content(), _load_execution_history(), _load_messages(), _message_content() (+41 more)

### Community 22 - "require_user"
Cohesion: 0.21
Nodes (32): _armory(), checkpoint_tree(), create_agent(), delete_agent(), get_agent(), get_agent_analytics(), get_agent_mcp(), get_agent_memory() (+24 more)

### Community 23 - "make_console"
Cohesion: 0.20
Nodes (9): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestHumanInputNode (+1 more)

### Community 24 - "ChatService"
Cohesion: 0.17
Nodes (16): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `GET /v1/chats/{chat_id}` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth), ChatCreateRequest, ChatDetailOut (+8 more)

### Community 25 - "MemoryService"
Cohesion: 0.17
Nodes (17): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+9 more)

### Community 26 - "CurrentUser"
Cohesion: 0.12
Nodes (20): get_experience(), list_experiences(), Depends, get, Authorized view of active learned experiences., CurrentUser, McpCreateRequest, McpUpdateRequest (+12 more)

### Community 27 - "emit"
Cohesion: 0.17
Nodes (23): trace_requests(), contextlib, work(), bind(), bind_from_config(), emit(), _error(), _persist() (+15 more)

### Community 28 - "endpoint.py"
Cohesion: 0.15
Nodes (17): get_runtime_manager(), agent_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject(), fastapi_exceptions (+9 more)

### Community 29 - "test_agent_core.py"
Cohesion: 0.12
Nodes (14): ChildEventCallback, set_child_callback(), reset_token_callback(), FakeAgents, parent_core(), AgentCore policy and independent-child behavior without a live database., test_cancelled_running_child_cannot_commit_result(), test_child_reasoning_stays_in_child_stream() (+6 more)

### Community 30 - "SessionRepository"
Cohesion: 0.35
Nodes (6): _iso(), Any, Conversation metadata lives on root AgentCore records., _row(), SessionRepository, _valid_id()

### Community 31 - "web_search"
Cohesion: 0.15
Nodes (13): 4. Internal Tool Subsystem, Information and planning tools, get_current_datetime_info(), Any, tool, Get comprehensive date and time information for the user's current timezone.…, Any, tool (+5 more)

### Community 32 - "make_console"
Cohesion: 0.19
Nodes (3): make_console(), Console, TestTurnRenderer

### Community 33 - "CheckpointService"
Cohesion: 0.29
Nodes (7): _services(), CheckpointOut, CheckpointTreeOut, RollbackRequest, CheckpointService, list_checkpoints(), Return readable checkpoint summaries for a thread (newest first).

### Community 34 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "load_session.py"
Cohesion: 0.16
Nodes (22): effective_memory_policy(), memory_requires_extract_confirmation(), Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks. (+14 more)

### Community 36 - "._write_and_read"
Cohesion: 0.14
Nodes (9): register, _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall (+1 more)

### Community 37 - "embeddings.py"
Cohesion: 0.18
Nodes (14): Step 2: extract reusable advice, hashlib, numpy, _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy… (+6 more)

### Community 38 - "mcp.py"
Cohesion: 0.22
Nodes (12): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+4 more)

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.11
Nodes (17): Current Extension Points and Limits, Entrypoints, Environment, HTTP API and WebSocket Runtime, LLM Client, Observability, and Replay, Logging and mock replay, Main prompt contract, Memory Model (+9 more)

### Community 40 - "BackgroundIdleWatcher"
Cohesion: 0.15
Nodes (8): CLI, Commands, Flow, Idle scheduling and branch handling, BackgroundIdleWatcher, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread., Run the async watcher in a daemon thread for non-async entrypoints.

### Community 41 - "in_run"
Cohesion: 0.25
Nodes (7): MemoryRepository, Memory, Agent policy facets: memory, armory, guardrails and observability., current_ids(), in_run(), span(), wrapped()

### Community 42 - ".run_turn"
Cohesion: 0.22
Nodes (6): on_child_event(), on_subagent_event(), _emit_turn_complete(), Any, _truncate(), Event

### Community 43 - "src/config.py"
Cohesion: 0.20
Nodes (7): dotenv, functools, pydantic_settings, BaseSettings, Agent environment and runtime configuration. Loads `client2.0/.env` into the…, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Community 44 - "tool_node"
Cohesion: 0.22
Nodes (6): empty_context_memory(), RunnableConfig, tool_node(), object, TestRuntimeControls, TestToolAndSubagentIngest

### Community 45 - "AnalyticsService"
Cohesion: 0.18
Nodes (12): alias, Any, Depends, get, Query, summary(), AnalyticsService, Any (+4 more)

### Community 46 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 47 - "test_embeddings_quiet.py"
Cohesion: 0.15
Nodes (8): list, src_models, _FakeEncoded, _FakeModel, HfLoadIsQuiet, _install_fakes(), The HF embedding backend must load quietly: no 'Loading weights' tqdm bar, no…, Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Community 48 - "_parse_response"
Cohesion: 0.09
Nodes (18): 1. End-to-End Turn Execution, 2. Agent State, Memory, and Planner Decisions, 5. API Layer and Service Boundaries, 8. Observability, Logs, and LLM Replay, Debugging planner problems, Detailed Subsystem Reference, Functions to start with when tracing a turn, Main agent loop (+10 more)

### Community 49 - "control.py"
Cohesion: 0.17
Nodes (14): clear_pause(), is_pause_requested(), maybe_pause(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each…, Call at the very top of a node, before any side effects. Returns the… (+6 more)

### Community 50 - "executor.py"
Cohesion: 0.17
Nodes (11): BashArgs, _check_blacklist(), _find_executable(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs, Internal tools for executing Bash commands, PowerShell commands, and Python… (+3 more)

### Community 51 - "log_event"
Cohesion: 0.14
Nodes (31): Agent trace logger, bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_context_select(), log_error(), log_event() (+23 more)

### Community 52 - "paths.py"
Cohesion: 0.73
Nodes (5): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "api_routes/files.py"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 57 - "tools_service.py"
Cohesion: 0.47
Nodes (7): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info(), src_tools

### Community 60 - "agentnode_prompt_loader"
Cohesion: 0.16
Nodes (10): 10. Safe Extension Guide, 3. Prompt Rendering Deep Dive, Add a prompt block, Add an API resource, Add an internal tool, Practical prompt-debug method, System versus user prompt, agentnode_prompt_loader() (+2 more)

### Community 61 - "_present"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.15
Nodes (9): Context selection and user questions, Main Agent Graph, Pause, confirmation, stop, and resume, Planner: `agent_node`, Topology, Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting (+1 more)

### Community 63 - "agent/kb.py"
Cohesion: 0.05
Nodes (104): append_version(), audit(), cancel(), chunks(), create_chunk(), demote(), expiry(), ExpiryBody (+96 more)

### Community 64 - "test_subagents_integration.py"
Cohesion: 0.08
Nodes (24): Any, WebSocket protocol helpers., Add a planner-callable sub-agent, Sub-agents: `subagent_node` and gate, RunnableConfig, Sub-agent node — delegates a focused task to a configured armory sub-agent.…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node() (+16 more)

### Community 65 - "test_db_setup.py"
Cohesion: 0.13
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "test_context_memory.py"
Cohesion: 0.11
Nodes (16): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+8 more)

### Community 68 - "update_context_memory"
Cohesion: 0.25
Nodes (3): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, update_context_memory(), TestUpdateContextMemory

### Community 69 - "llm_logger.py"
Cohesion: 0.11
Nodes (26): atexit, queue, _record(), _ensure_writer_started(), Path, _safe_agent_id(), _writer_loop(), build_record() (+18 more)

### Community 70 - "AgentRuntime"
Cohesion: 0.18
Nodes (8): AgentRuntime, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, Thin re-export — stream bridging lives in agent_runtime for cohesion., emit_child_event(), Any, test_child_events_emit_started_step_finished(), fake_run_turn()

### Community 71 - "Tools: `tool_node`"
Cohesion: 0.30
Nodes (12): Command execution tools, Tools: `tool_node`, execute_bash(), execute_powershell(), execute_python_script(), Any, tool, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+4 more)

### Community 72 - "ChildRunner"
Cohesion: 0.23
Nodes (4): ChildHandle, ChildRunner, Bounded, process-local execution of durable child runs., Before a parent finishes, collect all its children by persisted lineage.

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.13
Nodes (13): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+5 more)

### Community 75 - "idle_watcher.py"
Cohesion: 0.15
Nodes (13): 9. Learning Agent Detailed Flow and Diagnostics, Learning-agent diagnostic table, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, datetime (+5 more)

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 89 - "repl.py"
Cohesion: 0.11
Nodes (34): api_db_repositories, PreferencesRepository, prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, rich_markdown, rich_panel (+26 more)

### Community 90 - "fetch_one"
Cohesion: 0.31
Nodes (4): fetch_one(), Any, MemoryExtractionRepository, Any

### Community 91 - "main.py"
Cohesion: 0.24
Nodes (7): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, ModuleType, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), TestMainDispatch

### Community 92 - "postgres_checkpointer.py"
Cohesion: 0.21
Nodes (12): langgraph_checkpoint_postgres, _ensure_branch_learn_table(), _ensure_message_sync_schema(), _get_pool(), has_pending_interrupt(), is_leaf_learned(), mark_leaf_learned(), ConnectionPool (+4 more)

### Community 94 - "agent_core.py"
Cohesion: 0.16
Nodes (22): Durable AgentCore identities, run reservations, and child results., concurrent_futures, copy, Agent lifecycle facade and compatibility exports., Policy, Core agent dataclasses shared across runtime components., Process-local child execution orchestration for AgentCore., default_policy() (+14 more)

### Community 96 - "plan.py"
Cohesion: 0.24
Nodes (8): _escape_unescaped_quotes_in_json_strings(), Plan, PlanPhase, PlanStep, BaseModel, model_validator, Validated, checkpoint-friendly phased plans., Best-effort repair for planner JSON with raw quotes inside string values.

### Community 97 - "run_turn_interactive"
Cohesion: 0.13
Nodes (17): contextvars, Per-run sub-agent and child-agent progress callback plumbing (API / CLI safe).…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_child_callback(), reset_subagent_callback(), set_subagent_callback(), Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token. (+9 more)

### Community 99 - "ReadFileArgs"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, model_validator, ReadFileArgs, SearchFileArgs

### Community 100 - "execute"
Cohesion: 0.28
Nodes (4): execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _load(), Any

### Community 101 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 102 - "test_phased_plan.py"
Cohesion: 0.13
Nodes (29): dispatch_phase(), phase_collector_node(), plan_dispatcher_node(), parse_plan(), Reject the entire plan if any step is invalid or exceeds the runtime limit., A plan must be safe to dispatch and parallel phases must merge once., step(), test_dispatcher_runs_sequential_phases_without_reinvoking_agent() (+21 more)

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
Cohesion: 0.16
Nodes (8): ChatRuntime, ChatRuntimeManager, _deferred_fork(), Any, WebSocket, Start a new turn. If a `checkpoint_id` is given (a fork) while a run is already…, Process-local orchestrator: queues, attach/detach, parallel runs., New API chat and first turn

### Community 108 - "WebSocket chat session"
Cohesion: 0.22
Nodes (8): Client → server, Connect, Envelope (all messages), Example messages, Minimal client flow, Server → client, WebSocket chat session, WebSocket protocol

### Community 109 - ".add_entry"
Cohesion: 0.48
Nodes (4): _iso(), Any, _row_to_entry(), Durable user-memory tools

### Community 111 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 112 - "json"
Cohesion: 0.09
Nodes (25): calendar, datetime, ddgs, json, langchain_core_tools, os, platform, pydantic (+17 more)

### Community 113 - "Repository map"
Cohesion: 0.44
Nodes (4): AuthSessionRepository, _iso(), Any, Repository map

### Community 114 - "._begin_reserved_run"
Cohesion: 0.42
Nodes (7): utc_now_iso(), _done(), _target(), _done(), _target(), context(), set_trace_parent()

### Community 115 - "pathlib"
Cohesion: 0.09
Nodes (21): generate_tree(), Path, Recursively generates a string representation of a directory tree., io, pathlib, rich_console, scripts, src_utils (+13 more)

### Community 116 - "context_manager.py"
Cohesion: 0.39
Nodes (7): _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Check how much of a model's input context window the prompt consumes. Returns…, Check how much of a model's output context window a response consumes. Returns…

### Community 117 - "security.py"
Cohesion: 0.16
Nodes (15): hash_password(), needs_rehash(), verify_password(), _iso(), Any, _row_to_user(), UserRepository, _load() (+7 more)

### Community 118 - "Learning Agent and Experience System"
Cohesion: 0.33
Nodes (6): Experience API view, Learner graph, Learning Agent and Experience System, Retrieval in the main agent, Step 1: load trajectory, Step 3: persist and index

### Community 119 - "_session_prompt"
Cohesion: 0.33
Nodes (5): PromptSession, OpenSessions, Exception, _session_prompt(), open_sessions()

### Community 121 - "learn_session"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Community 122 - "truncate_value"
Cohesion: 0.32
Nodes (4): Recursively truncate oversized strings in payloads., truncate_value(), _utc_now(), TestTruncate

### Community 123 - ".test_resumes_after_interrupt"
Cohesion: 0.33
Nodes (4): interrupt_step(), TestRunTurnInteractive, fake_run_turn(), first()

### Community 124 - "user_from_token"
Cohesion: 0.40
Nodes (5): Validate JWT for WebSocket handshake., user_from_token(), decode_access_token(), Any, Authentication

### Community 126 - "decompose_query"
Cohesion: 0.50
Nodes (4): decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…

### Community 127 - "6. WebSocket Runtime, Queues, and Recovery"
Cohesion: 0.40
Nodes (4): 6. WebSocket Runtime, Queues, and Recovery, Agent runtime event conversion, Connection lifecycle, WebSocket debugging checklist

## Knowledge Gaps
- **44 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+39 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 555 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `make_console`, `run_turn_interactive`, `pathlib`, `make_console`, `repl.py`, `.test_resumes_after_interrupt`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `AgentCore` connect `AgentCore` to `run_turn_interactive`, `AgentRepository`, `load_session.py`, `ChildRunner`, `in_run`, `ChatRuntimeManager`, `test_experience_system.py`, `agent/graph.py`, `agent_runtime.py`, `._begin_reserved_run`, `chat_service.py`, `ChatService`, `repl.py`, `test_agent_core.py`, `agent_core.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `ChatRuntimeManager` connect `ChatRuntimeManager` to `ChatPacketQueue`, `EVA Agent API — Reference & How to Use`, `AgentRuntime`, `Platform Agent Codebase Documentation`, `WebSocket chat session`, `agent_runtime.py`, `._begin_reserved_run`, `AgentCore`, `endpoint.py`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 64 inferred relationships involving `CurrentUser` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`CurrentUser` has 64 INFERRED edges - model-reasoned connections that need verification._
- **Are the 47 inferred relationships involving `Repositories` (e.g. with `_armory()` and `checkpoint_tree()`) actually correct?**
  _`Repositories` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `graphify` to the rest of the system?**
  _44 weakly-connected nodes found - possible documentation gaps or missing edges._