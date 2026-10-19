# Graph Report - backend  (2026-10-05)

## Corpus Check
- 166 files · ~103,690 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 31 file(s) not represented in the graph (top: .jsonl 30, .example 1)

## Summary
- 2015 nodes · 5422 edges · 123 communities (97 shown, 26 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 444 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Repositories
- test_llm_mock_mode.py
- postgres_checkpointer.py
- chat_service.py
- TurnRenderer
- EVA Agent API — Reference & How to Use
- repositories/mcp.py
- TestSubagentRegistry
- TestAgentNodePrompt
- BackgroundIdleWatcher
- typing
- agentnode.py
- _Raw
- users.py
- slice_by_tokens
- ChatPacketQueue
- src/config.py
- extract_chunks.py
- api_routes/auth.py
- test_experience_system.py
- TestSubagentNode
- AgentRuntime
- agent/kb.py
- llm_client.py
- ChatService
- default_policy
- endpoint.py
- trace.py
- test_endpoints.py
- CurrentUser
- file_io.py
- emit
- require_user
- checkpoint_service.py
- context_selector_node
- agentnode_prompt_loader
- Tools: `tool_node`
- count_tokens
- AgentRepository
- Platform Agent Codebase Documentation
- AgentCore
- log_event
- json_store.py
- generate_tree
- run_turn_interactive
- _eval_cond
- web_search.py
- SessionRepository
- tools_service.py
- retrieve.py
- field_validator
- Full learner sequence
- make_console
- Multi-User Agentic AI Platform — Database Design
- edit_file
- graphify.js
- render
- test_prompt_render.py
- opencode.json
- mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_src_models_version_py
- re
- _present
- route_from_agent
- PreferencesRepository
- test_subagents_integration.py
- test_cli_repl.py
- ws.py
- agent/memory.py
- user_memory_fetch
- llm_logger.py
- main.py
- agent_core.py
- ._commit
- test_prompt_templates.py
- AGENTS.md
- WebSearchArgs
- db/__init__.py
- api/__init__.py
- flusher.py
- cli/__init__.py
- models/__init__.py
- subagents/__init__.py
- now.py
- AuthSessionRepository
- TestAgentRuntimeFanout
- prompt_loader.py
- build_cache_key
- mcp_runtime.py
- health.py
- empty_context_memory
- Observability
- repl.py
- test_llm_logger.py
- tools/__init__.py
- test_agent_core.py
- ._write_and_read
- update_context_memory
- McpRuntime
- test_context_memory.py
- ChatRuntimeManager
- ChildRunner
- repositories/memory.py
- paths.py
- MemoryRepo
- TestEmptyAndSerialize
- truncate_value
- Detailed Subsystem Reference
- list_subagents
- Memory
- Armory
- TestVectorStoreRoundtrip
- src_subagents_learner_agent_store
- TestMainDispatch
- test_db_setup.py

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 105 edges
2. `Repositories` - 65 edges
3. `require_user()` - 65 edges
4. `TurnRenderer` - 59 edges
5. `emit()` - 51 edges
6. `get_repos()` - 50 edges
7. `log_event()` - 46 edges
8. `call_llm()` - 39 edges
9. `in_run()` - 38 edges
10. `get_connection()` - 35 edges

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

## Communities (123 total, 26 thin omitted)

### Community 0 - "Repositories"
Cohesion: 0.12
Nodes (11): Any, Depends, get, summary(), Repositories, AnalyticsService, Any, PreloadService (+3 more)

### Community 1 - "test_llm_mock_mode.py"
Cohesion: 0.13
Nodes (14): _Chunk, _Completion, _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, Captures every record the client emits instead of writing it anywhere. (+6 more)

### Community 2 - "postgres_checkpointer.py"
Cohesion: 0.07
Nodes (44): 7. PostgreSQL, Repositories, and Checkpoints, Checkpointer function map, Database troubleshooting, Persistence and Checkpoints, PostgreSQL responsibilities, langgraph_checkpoint_postgres, _ensure_branch_learn_table(), _ensure_message_sync_schema() (+36 more)

### Community 3 - "chat_service.py"
Cohesion: 0.20
Nodes (17): is_placeholder_title(), Derive a short default chat title from the first human message., True for empty / New chat / legacy `Chat <locale datetime>` titles., title_from_first_message(), _first_human_content(), _load_execution_history(), _load_messages(), _message_content() (+9 more)

### Community 4 - "TurnRenderer"
Cohesion: 0.11
Nodes (10): Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., TurnRenderer, make_console() (+2 more)

### Community 5 - "EVA Agent API — Reference & How to Use"
Cohesion: 0.08
Nodes (24): Analytics, Authentication, Checkpoints & rollback, Client → server, Connect, Data store (`data/`), EVA Agent API — Reference & How to Use, Example messages (+16 more)

### Community 6 - "repositories/mcp.py"
Cohesion: 0.20
Nodes (13): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, _iso(), McpRepository, _load(), Any, _row_to_server() (+5 more)

### Community 8 - "TestAgentNodePrompt"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Community 9 - "BackgroundIdleWatcher"
Cohesion: 0.15
Nodes (8): CLI, Commands, Flow, Idle scheduling and branch handling, BackgroundIdleWatcher, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread., Run the async watcher in a daemon thread for non-async entrypoints.

### Community 10 - "typing"
Cohesion: 0.14
Nodes (16): Process-wide Postgres connection pool + small query helpers. This is the shared…, contextlib, psycopg, psycopg_pool, psycopg_rows, execute(), fetch_all(), fetch_one() (+8 more)

### Community 11 - "agentnode.py"
Cohesion: 0.07
Nodes (37): BaseMessage, 1. End-to-End Turn Execution, 8. Observability, Logs, and LLM Replay, Agent runtime event conversion, Context selection and user questions, Debugging planner problems, Functions to start with when tracing a turn, Main Agent Graph (+29 more)

### Community 12 - "_Raw"
Cohesion: 0.20
Nodes (6): fake_gateway(), create(), Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create., _Raw, create()

### Community 13 - "users.py"
Cohesion: 0.22
Nodes (13): hash_password(), needs_rehash(), verify_password(), execute(), Run an INSERT/UPDATE/DELETE, return affected row count., _iso(), Any, _row_to_user() (+5 more)

### Community 14 - "slice_by_tokens"
Cohesion: 0.28
Nodes (5): Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, _tokens_of_chars()

### Community 15 - "ChatPacketQueue"
Cohesion: 0.15
Nodes (9): Envelope (all messages), ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback)., Add a WebSocket event, `ChatPacketQueue` behavior (+1 more)

### Community 16 - "src/config.py"
Cohesion: 0.06
Nodes (26): dotenv, functools, hashlib, list, numpy, pydantic_settings, get_settings(), BaseSettings (+18 more)

### Community 17 - "extract_chunks.py"
Cohesion: 0.17
Nodes (19): Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks., _utc_now(), _latest_human() (+11 more)

### Community 18 - "api_routes/auth.py"
Cohesion: 0.27
Nodes (13): login(), logout(), me(), Depends, get, post, new_session_id(), LoginRequest (+5 more)

### Community 19 - "test_experience_system.py"
Cohesion: 0.13
Nodes (16): datetime, _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of… (+8 more)

### Community 20 - "TestSubagentNode"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Community 21 - "AgentRuntime"
Cohesion: 0.15
Nodes (5): AgentRuntime, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, Thin re-export — stream bridging lives in agent_runtime for cohesion., Event

### Community 22 - "agent/kb.py"
Cohesion: 0.06
Nodes (89): get_experience(), list_experiences(), Depends, get, Authorized view of active learned experiences., append_version(), cancel(), chunks() (+81 more)

### Community 23 - "llm_client.py"
Cohesion: 0.10
Nodes (38): Gateway behavior, LLM call logger and replay cache, OpenAI, emit_usage(), Any, _build_messages(), _cache_key(), call_llm() (+30 more)

### Community 24 - "ChatService"
Cohesion: 0.16
Nodes (22): Chats, `DELETE /v1/chats/{chat_id}` (auth), `GET /v1/chats` (auth), `GET /v1/chats/{chat_id}` (auth), `PATCH /v1/chats/{chat_id}` (auth), `POST /v1/chats` (auth), create_chat(), delete_chat() (+14 more)

### Community 25 - "default_policy"
Cohesion: 0.24
Nodes (15): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+7 more)

### Community 26 - "endpoint.py"
Cohesion: 0.18
Nodes (13): Validate JWT for WebSocket handshake., user_from_token(), chat_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject() (+5 more)

### Community 27 - "trace.py"
Cohesion: 0.19
Nodes (19): api_api_routes, create_app(), trace_requests(), api_ws, fastapi_middleware_cors, work(), bind(), bind_from_config() (+11 more)

### Community 28 - "test_endpoints.py"
Cohesion: 0.24
Nodes (9): fastapi_testclient, starlette_websockets, TestClient, check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected() (+1 more)

### Community 29 - "CurrentUser"
Cohesion: 0.12
Nodes (24): get_prefs(), put_prefs(), Any, Depends, get, put, CurrentUser, McpCreateRequest (+16 more)

### Community 30 - "file_io.py"
Cohesion: 0.23
Nodes (7): EditFileArgs, BaseModel, field_validator, model_validator, Internal tools for file I/O operations, file search, and directory management., ReadFileArgs, SearchFileArgs

### Community 31 - "emit"
Cohesion: 0.10
Nodes (28): available_mcp_tools(), call_mcp_tool(), McpTool, Pause, confirmation, stop, and resume, object, clear_pause(), is_pause_requested(), maybe_pause() (+20 more)

### Community 32 - "require_user"
Cohesion: 0.28
Nodes (19): connect_server(), create_server(), delete_server(), disconnect_server(), import_servers(), list_servers(), Any, delete (+11 more)

### Community 33 - "checkpoint_service.py"
Cohesion: 0.28
Nodes (11): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+3 more)

### Community 34 - "context_selector_node"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Community 35 - "agentnode_prompt_loader"
Cohesion: 0.22
Nodes (7): 10. Safe Extension Guide, Add a prompt block, Add an API resource, Add an internal tool, agentnode_prompt_loader(), Build the agent node's context and render `agentnode.txt`., TestPromptWiring

### Community 36 - "Tools: `tool_node`"
Cohesion: 0.20
Nodes (16): Command execution tools, Tools: `tool_node`, get_python_executable(), Return the project venv Python when available, otherwise sys.executable., execute_bash(), execute_powershell(), execute_python_script(), _find_executable() (+8 more)

### Community 37 - "count_tokens"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Community 38 - "AgentRepository"
Cohesion: 0.13
Nodes (7): fetch_all(), fetch_one(), Any, AgentRepository, Any, Durable AgentCore identities, run reservations, and child results., uuid

### Community 39 - "Platform Agent Codebase Documentation"
Cohesion: 0.08
Nodes (24): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools., Authentication (+16 more)

### Community 40 - "AgentCore"
Cohesion: 0.17
Nodes (4): AgentCore, AgentID, Guardrails, Message

### Community 41 - "log_event"
Cohesion: 0.10
Nodes (37): Agent trace logger, learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, bind_session_logger(), flush_pending_logs(), get_session_logger(), log_agent_decision() (+29 more)

### Community 42 - "json_store.py"
Cohesion: 0.31
Nodes (8): ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any, Plain-text JSONL mirror of experience chunks for human review., read_all_chunks()

### Community 43 - "generate_tree"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Community 44 - "run_turn_interactive"
Cohesion: 0.13
Nodes (19): on_child_event(), on_subagent_event(), Any, _truncate(), ChildEventCallback, Bind a sub-agent progress callback for the current context; returns a reset…, reset_child_callback(), set_child_callback() (+11 more)

### Community 46 - "web_search.py"
Cohesion: 0.18
Nodes (17): ddgs, ensure_venv_on_path(), get_venv_python(), get_venv_site_packages(), Path, Prepend the project venv site-packages directory to sys.path., _venv_bin_dir(), _brave_search() (+9 more)

### Community 47 - "SessionRepository"
Cohesion: 0.36
Nodes (5): _iso(), Any, _row_to_chat(), SessionRepository, _valid_uuid()

### Community 48 - "tools_service.py"
Cohesion: 0.25
Nodes (11): list_tools(), Any, Depends, get, _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict() (+3 more)

### Community 49 - "retrieve.py"
Cohesion: 0.14
Nodes (12): Retrieval in the main agent, Standalone learner agent: extract experience chunks from idle chats., build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., format_experiences_for_prompt(), Any, Safe experience retrieval for the main agent hot path. (+4 more)

### Community 50 - "field_validator"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Community 51 - "Full learner sequence"
Cohesion: 0.17
Nodes (13): 9. Learning Agent Detailed Flow and Diagnostics, Experience API view, Full learner sequence, Learner graph, Learning Agent and Experience System, Learning-agent diagnostic table, Step 1: load trajectory, Step 2: extract reusable advice (+5 more)

### Community 52 - "make_console"
Cohesion: 0.23
Nodes (8): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestPromptForInterrupt

### Community 53 - "Multi-User Agentic AI Platform — Database Design"
Cohesion: 0.18
Nodes (10): 1. Users, credentials, preferences, 2. User activity & sessions, 3. Chats & agent activity, 4. Checkpoints & execution details (LangGraph), 5. Long-term memory (per user), 6. MCP server details (global + per-user), 7. Analytics, 8. Entity relationship summary (+2 more)

### Community 54 - "edit_file"
Cohesion: 0.20
Nodes (14): 4. Internal Tool Subsystem, Durable user-memory tools, File tools, edit_file(), Any, Path, tool, Read content from a text-based file. Supports optional line-range slicing via… (+6 more)

### Community 55 - "graphify.js"
Cohesion: 0.40
Nodes (3): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path

### Community 56 - "render"
Cohesion: 0.29
Nodes (3): render(), str.format() required {{ }} escaping; this renderer does not., TestRendering

### Community 57 - "test_prompt_render.py"
Cohesion: 0.20
Nodes (11): _fmt(), PromptRenderError, Any, Exception, Serialize structured prompt context as TOON., Raised in strict mode when a template references an unknown variable., replace(), to_toon() (+3 more)

### Community 60 - "re"
Cohesion: 0.24
Nodes (5): argparse, re, requests, GitHubRepoDownloader, main()

### Community 61 - "_present"
Cohesion: 0.24
Nodes (6): 3. Prompt Rendering Deep Dive, Practical prompt-debug method, System versus user prompt, _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Community 62 - "route_from_agent"
Cohesion: 0.24
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Community 63 - "PreferencesRepository"
Cohesion: 0.60
Nodes (3): PreferencesRepository, _load(), Any

### Community 64 - "test_subagents_integration.py"
Cohesion: 0.08
Nodes (29): Any, SubagentsService, Add a planner-callable sub-agent, Current Extension Points and Limits, Sub-agents: `subagent_node` and gate, contextvars, Subagent confirmation gate — runs unconditionally right after subagent_node,…, subagent_gate_node() (+21 more)

### Community 65 - "test_cli_repl.py"
Cohesion: 0.10
Nodes (16): io, rich_console, rich_markdown, rich_panel, rich_rule, rich_text, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, parse_command() (+8 more)

### Community 66 - "ws.py"
Cohesion: 0.53
Nodes (5): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope

### Community 67 - "agent/memory.py"
Cohesion: 0.17
Nodes (13): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+5 more)

### Community 68 - "user_memory_fetch"
Cohesion: 0.40
Nodes (6): Any, tool, Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update()

### Community 69 - "llm_logger.py"
Cohesion: 0.10
Nodes (26): atexit, queue, register, _ensure_writer_started(), _writer_loop(), _db_loop(), _db_params(), _drain_on_exit() (+18 more)

### Community 70 - "main.py"
Cohesion: 0.36
Nodes (7): run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), Re-launch this process with the project venv Python when needed., reexec_with_venv_if_available()

### Community 71 - "agent_core.py"
Cohesion: 0.18
Nodes (11): _allowed(), intersect_policy(), Policy, Agent identity, effective policy and durable lifecycle facade., A child cannot grant capabilities, scopes or a tenant its parent lacks., child_agent_node(), Spawn one or more child AgentCore runs from a single planner action., _requested_policy() (+3 more)

### Community 72 - "._commit"
Cohesion: 0.18
Nodes (6): emit_tag(), _format_args(), Any, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short()

### Community 73 - "test_prompt_templates.py"
Cohesion: 0.15
Nodes (12): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+4 more)

### Community 75 - "WebSearchArgs"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Community 80 - "models/__init__.py"
Cohesion: 0.40
Nodes (4): importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil, Top-level package for models. This package automatically imports submodules in…

### Community 87 - "now.py"
Cohesion: 0.15
Nodes (11): calendar, get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's… (+3 more)

### Community 89 - "AuthSessionRepository"
Cohesion: 0.57
Nodes (3): AuthSessionRepository, _iso(), Any

### Community 90 - "TestAgentRuntimeFanout"
Cohesion: 0.33
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Community 91 - "prompt_loader.py"
Cohesion: 0.24
Nodes (11): Major prompt functions, _has_tool(), _load_module(), _Node, _parse(), Prompt rendering and loading for every agent and sub-agent in the project. One…, Load a versioned reusable prompt module., Whether any of `names` is in the available tool list. Capability rules are… (+3 more)

### Community 92 - "build_cache_key"
Cohesion: 0.33
Nodes (4): build_cache_key(), Stable hash of everything that can change the answer. Fields are length-…, A newline inside one field must not be able to impersonate the boundary between…, TestCacheKey

### Community 94 - "mcp_runtime.py"
Cohesion: 0.10
Nodes (29): get_settings(), BaseSettings, Settings, configure_logging(), create_access_token(), decode_access_token(), Any, lifespan() (+21 more)

### Community 96 - "health.py"
Cohesion: 0.39
Nodes (7): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel

### Community 97 - "empty_context_memory"
Cohesion: 0.22
Nodes (4): empty_context_memory(), TestPromptLoader, TestToolAndSubagentIngest, TestToonTokenSavings

### Community 99 - "repl.py"
Cohesion: 0.11
Nodes (36): api_db_repositories, _emit_turn_complete(), prompt_toolkit, prompt_toolkit_completion, prompt_toolkit_key_binding, prompt_toolkit_shortcuts, PromptSession, rich_prompt (+28 more)

### Community 100 - "test_llm_logger.py"
Cohesion: 0.12
Nodes (18): json, os, pydantic, collect_child_node(), Explicitly collect a selected child without importing its full transcript., Internal tools for executing Bash commands, PowerShell commands, and Python…, src_utils, current_session_ids() (+10 more)

### Community 101 - "tools/__init__.py"
Cohesion: 0.15
Nodes (13): Information and planning tools, langchain_core_tools, platform, decompose_query(), Any, tool, Decompose a user query into a structured multi-dimensional breakdown. Produces…, Internal tools package for the agent. (+5 more)

### Community 102 - "test_agent_core.py"
Cohesion: 0.13
Nodes (9): pytest, FakeAgents, parent_core(), AgentCore policy and independent-child behavior without a live database., test_cancelled_running_child_cannot_commit_result(), test_child_result_requires_parent_lineage(), test_nonblocking_children_and_one_run_per_agent(), slow() (+1 more)

### Community 103 - "._write_and_read"
Cohesion: 0.19
Nodes (6): build_record(), _utc_now(), Record one call under a temp logs dir and return the parsed JSONL rows., _record_kwargs(), TestRecordLlmCall, TestRecordShape

### Community 104 - "update_context_memory"
Cohesion: 0.25
Nodes (3): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, update_context_memory(), TestUpdateContextMemory

### Community 105 - "McpRuntime"
Cohesion: 0.12
Nodes (6): McpConnection, McpRuntime, Any, BaseException, test_http_404_is_reported_as_endpoint_error(), test_http_transport_connects_to_real_streamable_server()

### Community 106 - "test_context_memory.py"
Cohesion: 0.07
Nodes (28): State, langchain_core_messages, langgraph_graph, langgraph_graph_message, langgraph_types, pathlib, scripts, Agent graph definition. (+20 more)

### Community 107 - "ChatRuntimeManager"
Cohesion: 0.13
Nodes (15): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+7 more)

### Community 108 - "ChildRunner"
Cohesion: 0.23
Nodes (4): ChildHandle, ChildRunner, Bounded, process-local execution of durable child runs., Before a parent finishes, collect all its children by persisted lineage.

### Community 109 - "repositories/memory.py"
Cohesion: 0.60
Nodes (3): _iso(), Any, _row_to_entry()

### Community 111 - "paths.py"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Community 114 - "truncate_value"
Cohesion: 0.47
Nodes (3): Recursively truncate oversized strings in payloads., truncate_value(), TestTruncate

### Community 115 - "Detailed Subsystem Reference"
Cohesion: 0.40
Nodes (5): 2. Agent State, Memory, and Planner Decisions, 5. API Layer and Service Boundaries, Detailed Subsystem Reference, Planner response parsing details, Why execution memory is split

### Community 116 - "list_subagents"
Cohesion: 0.50
Nodes (4): list_subagents(), Any, Depends, get

### Community 117 - "Memory"
Cohesion: 0.18
Nodes (8): MemoryRepository, Memory, _memory(), BaseModel, Tools for reading and writing per-user long-term memory / preferences., UserMemoryFetchArgs, UserMemoryUpdateArgs, current_ids()

### Community 123 - "test_db_setup.py"
Cohesion: 0.14
Nodes (7): scripts_db_setup, skipUnless, socket, Tests for scripts/db_setup.py. Static checks always run. The live integration…, A REFERENCES users(...) statement must not appear before `users` is created,…, TestDbSetupLive, TestSchemaStatementsAreIdempotent

## Knowledge Gaps
- **43 isolated node(s):** `$schema`, `plugin`, `graphify`, `Purpose and Architecture`, `Repository Map` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 552 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `TurnRenderer` to `test_cli_repl.py`, `repl.py`, `._commit`, `run_turn_interactive`, `make_console`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `CurrentUser` connect `CurrentUser` to `Repositories`, `checkpoint_service.py`, `health.py`, `require_user`, `chat_service.py`, `tools_service.py`, `api_routes/auth.py`, `list_subagents`, `agent/kb.py`, `ChatService`, `default_policy`, `endpoint.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Why does `emit()` connect `emit` to `postgres_checkpointer.py`, `agentnode.py`, `agent/kb.py`, `endpoint.py`, `trace.py`, `checkpoint_service.py`, `AgentCore`, `log_event`, `run_turn_interactive`, `retrieve.py`, `route_from_agent`, `test_subagents_integration.py`, `agent_core.py`, `mcp_runtime.py`, `Observability`, `repl.py`, `test_context_memory.py`, `ChatRuntimeManager`, `ChildRunner`, `Memory`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `require_user()` (e.g. with `Add an API resource` and `Authentication`) actually correct?**
  _`require_user()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._