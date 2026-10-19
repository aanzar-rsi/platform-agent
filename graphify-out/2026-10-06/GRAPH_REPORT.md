# Graph Report - v2  (2026-09-28)

## Corpus Check
- 264 files · ~157,817 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 28 file(s) not represented in the graph (top: .jsonl 22, .example 2, .tsbuildinfo 2)

## Summary
- 2549 nodes · 5393 edges · 159 communities (125 shown, 34 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 210 edges (avg confidence: 0.93)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Backend Api Db
- Frontend Src Pages
- Frontend Package Json
- Frontend Package Json
- Backend Src Utils
- Backend Src Agent
- Frontend Src Components
- Frontend Src Lib
- Backend Api Api Routes
- Backend Src Cli
- Frontend Src Components
- Backend Api Services
- Backend Src Utils
- Backend Src Cli
- Backend Api Services
- Frontend Src Components
- Backend Src Agent
- Backend Src Models
- Backend Src Subagents
- Backend Tests Test Llm Mock Mode Py
- Frontend Src Components
- Backend Src Agent
- Frontend Src Hooks
- Frontend Src Lib
- Backend Tests Test Context Memory Py
- Backend Api Services
- Backend Src Subagents
- Frontend Src Components
- Backend Tests Test Context Memory Py
- Frontend Package Json
- Backend Src Cli
- Backend Tests Test Experience System Py
- Backend Tests Test Llm Logger Py
- Backend Api Core
- Backend Tests Test Llm Mock Mode Py
- Frontend Src Components
- Frontend Tsconfig App Json
- Backend Src Utils
- Backend Api Services
- Backend Src Subagents
- Backend Tests Test Subagents Integration Py
- Backend Src Subagents
- Backend Tests Test Prompt Templates Py
- Backend Src Utils
- Backend Tests Test Main Entrypoint Py
- Frontend Components Json
- Frontend Src Components
- Frontend Src Types
- Backend Api Services
- Backend Api Domain
- Backend Api Api Routes
- Backend Api Services
- Backend Src Agent
- Backend Tests Test Cli Repl Py
- Backend Tests Test Cli Repl Py
- Backend Tests Test Prompt Templates Py
- Frontend Tsconfig Convex Json
- Backend Tests Test Subagents Integration Py
- Backend Api Domain
- Backend Tests Test Prompt Render Py
- Backend Src Tools
- Scripts Db Setup Py
- Frontend Src Instrumentation Tsx
- Frontend Tsconfig Node Json
- Backend Tests Test Llm Logger Py
- Backend Src Prompts
- Backend Api Services
- Backend Api Services
- Frontend Src Components
- Frontend Src Lib
- Frontend Src Pages
- Backend Tests Test Context Memory Py
- Backend Tests Test Context Memory Py
- Backend Src Utils
- Backend Src Tools
- Backend Src Tools
- Tests Test Backend Correctness Py
- Backend Tests Test Py
- Backend Api Ws
- Backend Src Models
- Backend Src Tools
- Backend Src Tools
- Frontend Src Components
- Frontend Readme Md
- Backend Api Db
- Backend Tests Test Context Memory Py
- Backend Src Subagents
- Backend Src Tools
- Frontend Src Components
- Frontend Src Components
- Backend Api Domain
- Backend Api Services
- Backend Src Bootstrap Py
- Backend Src Prompts
- Backend Src Tools
- Backend Src Utils
- Backend Tests Test Endpoints Py
- Frontend Src Components
- Frontend Src Components
- Backend Opencode Plugins
- Backend Tests Test Prompt Render Py
- Backend Tests Test Prompt Render Py
- Backend Src Tools
- Frontend Package Json
- Frontend Src Components
- Frontend Src Components
- Backend Src Tools
- Backend Tests Test Embeddings Quiet Py
- Backend Tests Test Subagents Integration Py
- Frontend Src Components
- Frontend Src Components
- Frontend Src Components
- Frontend Src Hooks
- Backend Src Utils
- Backend Tests Test Prompt Render Py
- Backend Src Subagents
- Frontend Package Json
- Backend Src Config Py
- Backend Tests Test Experience System Py
- Backend Tests Test Llm Logger Py
- Frontend Src Lib
- Backend Src Models
- Backend Src Tools
- Backend Tests Test Db Setup Py
- Frontend Src Lib
- Frontend Src Lib
- Backend File Structure Py
- Frontend Src Lib
- Backend Opencode Opencode Json
- Backend Tests Test Llm Mock Mode Py
- Frontend Tsconfig Json
- Run Dev
- Backend Requirements Txt
- Backend Api Db
- Backend Api Init Py
- Backend Api Ws
- Backend Src Cli
- Backend Src Cli
- Backend Src Subagents
- Frontend Package Json
- Frontend Src Components
- Frontend Src Lib
- Frontend Src Vite Env D Ts
-  Github Workflows Ci Yml
- Git Ignore Rules
- Backend Pyproject Toml
- Container Orchestration
- Frontend Gitignore
- Frontend Index Html
- Frontend Vite Config Js
- Graphify Out Gitkeep

## God Nodes (most connected - your core abstractions)
1. `CurrentUser` - 80 edges
2. `Repositories` - 61 edges
3. `TurnRenderer` - 59 edges
4. `react` - 54 edges
5. `require_user()` - 46 edges
6. `log_event()` - 42 edges
7. `get_repos()` - 41 edges
8. `call_llm()` - 37 edges
9. `lucide-react` - 32 edges
10. `update_context_memory()` - 29 edges

## Surprising Connections (you probably didn't know these)
- `check_atomic_admission()` --uses--> `ChatRuntimeManager`  [INFERRED]
  tests/test_backend_correctness.py → backend/api/services/chat_runtime_manager.py
- `check_rollback_ownership()` --uses--> `CheckpointService`  [INFERRED]
  tests/test_backend_correctness.py → backend/api/services/checkpoint_service.py
- `check_message_sync()` --uses--> `PostgresSaver`  [INFERRED]
  tests/test_backend_correctness.py → backend/src/utils/postgres_checkpointer.py
- `ensure_checkpointer_tables()` --calls--> `get_checkpointer()`  [INFERRED]
  scripts/db_setup.py → backend/src/utils/postgres_checkpointer.py
- `create_user()` --calls--> `hash_password()`  [EXTRACTED]
  scripts/create_user.py → backend/api/core/security.py

## Import Cycles
- None detected.

## Communities (159 total, 34 thin omitted)

### Backend Api Db - "Backend Api Db"
Cohesion: 0.07
Nodes (42): cache_get_or_set(), cache_invalidate(), Small in-process TTL caches for hot Postgres lookups. Not a distributed cache —…, hash_password(), needs_rehash(), verify_password(), execute(), fetch_all() (+34 more)

### Frontend Src Pages - "Frontend Src Pages"
Cohesion: 0.05
Nodes (57): HeaderNavbar, NavigationProps, LogoutButton(), ProtectedRoute(), ProtectedRouteProps, ToasterProps, frontend_src_index, RouteSyncer() (+49 more)

### Frontend Package Json - "Frontend Package Json"
Cohesion: 0.03
Nodes (72): dependencies, axios, class-variance-authority, clsx, cmdk, convex, @convex-dev/auth, convex-helpers (+64 more)

### Frontend Package Json - "Frontend Package Json"
Cohesion: 0.03
Nodes (61): name, private, type, version, autoprefixer, baseline-browser-mapping, cmdk, convex (+53 more)

### Backend Src Utils - "Backend Src Utils"
Cohesion: 0.07
Nodes (44): build_config(), _ensure_branch_learn_table(), _ensure_message_sync_schema(), _filter_checkpoint_tree(), get_checkpointer(), _get_pool(), get_thread_state(), has_pending_interrupt() (+36 more)

### Backend Src Agent - "Backend Src Agent"
Cohesion: 0.06
Nodes (35): Uvicorn entrypoint: from client2.0 run python -m api.main (workers=1)., run(), main(), Boot the agent. Usage (from the v2 project root): python main.py # start the…, Agent graph definition., Interactive multi-turn agent CLI loop (rendered by src.cli.repl)., run_cli(), Subagent confirmation gate — runs unconditionally right after subagent_node,… (+27 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.05
Nodes (36): Alert, AlertDescription, AlertTitle, alertVariants, Badge(), BadgeProps, badgeVariants, Button (+28 more)

### Frontend Src Lib - "Frontend Src Lib"
Cohesion: 0.04
Nodes (40): analyticsAPI, AnalyticsSummary, apiClient, authAPI, CatalogSubagent, CatalogTool, chatAPI, ChatCreateRequest (+32 more)

### Backend Api Api Routes - "Backend Api Api Routes"
Cohesion: 0.11
Nodes (24): create_server(), delete_server(), list_servers(), Any, delete, Depends, get, patch (+16 more)

### Backend Src Cli - "Backend Src Cli"
Cohesion: 0.11
Nodes (10): Console, Stop the live region (frame stays on screen) before an interrupt., Close the live region and print the final answer exactly once., Draws activity + streamed output for a single agent turn., Plain text of the activity rows shown so far., Restart the live region after an interrupt prompt., TurnRenderer, make_console() (+2 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.06
Nodes (29): ChatInterface(), ChatSidebar(), AGENT_STUDIO_PHASES, ChatTuneSettings, ChatViewProps, EnhancedChatView, EnhancedChatViewHandle, extractStudioAgentId() (+21 more)

### Backend Api Services - "Backend Api Services"
Cohesion: 0.13
Nodes (28): create_chat(), delete_chat(), get_chat(), list_chats(), delete, Depends, get, patch (+20 more)

### Backend Src Utils - "Backend Src Utils"
Cohesion: 0.15
Nodes (28): bind_session_logger(), _ensure_writer_started(), flush_pending_logs(), get_session_logger(), log_agent_decision(), log_context_select(), log_error(), log_event() (+20 more)

### Backend Src Cli - "Backend Src Cli"
Cohesion: 0.11
Nodes (35): PreferencesRepository, _choose(), _default_runtime(), get_agent_app(), _handle_settings(), _load_state(), _login(), _manage_mcp() (+27 more)

### Backend Api Services - "Backend Api Services"
Cohesion: 0.16
Nodes (24): add_memory(), clear_memory(), get_memory(), put_memory(), delete, Depends, get, post (+16 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.06
Nodes (23): BreadcrumbItem, BreadcrumbProps, MCPWarningWidgetProps, Checkbox, MultiUIResourceRendererProps, UIResource, UIResourceRendererProps, Feature (+15 more)

### Backend Src Agent - "Backend Src Agent"
Cohesion: 0.11
Nodes (27): clear_pause(), is_pause_requested(), maybe_pause(), note_text_from_resume(), _NotPaused, pause_gate_active(), _pending_interrupt_at_node(), Cooperative "pause anywhere" registry for user-initiated mid-run pauses. Each… (+19 more)

### Backend Src Models - "Backend Src Models"
Cohesion: 0.14
Nodes (32): emit_usage(), Any, _build_messages(), _cache_key(), call_llm(), call_llm_stream(), _dump(), _estimated_usage() (+24 more)

### Backend Src Subagents - "Backend Src Subagents"
Cohesion: 0.13
Nodes (25): Standalone learner LangGraph: load_session → extract_chunks → persist., extract_chunks_node(), _normalize_chunk(), _parse_json_payload(), Any, LLM extraction of tool-based experience chunks., _utc_now(), _latest_human() (+17 more)

### Backend Tests Test Llm Mock Mode Py - "Backend Tests Test Llm Mock Mode Py"
Cohesion: 0.18
Nodes (8): _Chunk, _Completion, Patch the cache lookup; `hit` may be a dict, None, or a callable., Same prompt at a different temperature must miss., A text call and a json call with the same prompt must not collide — the json…, TestMockModeOn, TestStreamReplay, _Usage

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.09
Nodes (25): ArchivedPlanDisplay(), BatchMeta, BatchSection(), BatchType, buildPlanTileGroups(), CriticFeedbackSummary, CriticStatus, DecisionInfo (+17 more)

### Backend Src Agent - "Backend Src Agent"
Cohesion: 0.11
Nodes (22): agent_node(), _on_token(), _coerce_int(), _extract_tag(), _format_conversation(), _is_turn_start(), _latest_human_content(), _parse_parameters() (+14 more)

### Frontend Src Hooks - "Frontend Src Hooks"
Cohesion: 0.11
Nodes (18): ChatSidebarProps, SidebarExecutionLoaderWrap, SidebarSection, AnimatedBackgroundProps, AuthContext, AuthContextValue, AuthProvider(), AuthState (+10 more)

### Frontend Src Lib - "Frontend Src Lib"
Cohesion: 0.11
Nodes (6): AgentWebSocketClient, AgentWebSocketHandlers, createWebSocketClient(), ServerEventType, WS_HOST, WsEnvelope

### Backend Tests Test Context Memory Py - "Backend Tests Test Context Memory Py"
Cohesion: 0.15
Nodes (8): Insert/replace a sliced window for `key` under a FIFO token budget. 1. Slice…, Slice content by approximate token offsets. Returns (slice_value, actual_from,…, slice_by_tokens(), update_context_memory(), Build a string that is approximately n tokens (~4 chars/token)., TestSliceByTokens, TestUpdateContextMemory, _tokens_of_chars()

### Backend Api Services - "Backend Api Services"
Cohesion: 0.15
Nodes (12): utc_now_iso(), ChatRuntime, ChatRuntimeManager, _done(), _target(), _done(), _target(), _deferred_fork() (+4 more)

### Backend Src Subagents - "Backend Src Subagents"
Cohesion: 0.13
Nodes (23): Soft-fail embed; returns None on any error., try_embed_text(), ensure_experience_dir(), Path, Learner / experience-system configuration., append_chunks(), get_chunk_by_id(), Any (+15 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.09
Nodes (22): connectMock, createMock, disconnectMock, getMock, listCheckpointsMock, preferencesGetMock, preferencesUpdateMock, rollbackMock (+14 more)

### Backend Tests Test Context Memory Py - "Backend Tests Test Context Memory Py"
Cohesion: 0.13
Nodes (13): build_execution_memory_index(), count_content_tokens(), _entry_tokens(), Any, Context memory helpers — FIFO budget, token slicing, execution_memory index.…, keys + short meta: name, task, total_tokens, in_context., History rows without result bodies, for agent prompts., Encode content as TOON text for token counting / window slicing. (+5 more)

### Frontend Package Json - "Frontend Package Json"
Cohesion: 0.08
Nodes (25): devDependencies, autoprefixer, baseline-browser-mapping, eslint, eslint-config-prettier, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh (+17 more)

### Backend Src Cli - "Backend Src Cli"
Cohesion: 0.13
Nodes (11): _format_args(), Any, Live terminal renderer for one agent turn. The renderer is fed two kinds of…, The complete answer for this turn (authoritative copy)., Record the planner's parsed decision after its streamed reasoning., _short(), rich_markdown, rich_panel (+3 more)

### Backend Tests Test Experience System Py - "Backend Tests Test Experience System Py"
Cohesion: 0.13
Nodes (14): _is_run_active(), _mark_session(), _parse_iso(), process_idle_sessions(), Any, Background idle watcher: learn from chats idle for IDLE_SECONDS., Scan sessions and run learn_session for every not-yet-learned branch leaf of…, Pure helper: sessions idle long enough to consider for learning. Per-branch… (+6 more)

### Backend Tests Test Llm Logger Py - "Backend Tests Test Llm Logger Py"
Cohesion: 0.13
Nodes (13): build_cache_key(), build_record(), current_session_ids(), Stable hash of everything that can change the answer. Fields are length-…, chat/run/user/core ids from the ContextVar-bound agent session logger. Falls…, _utc_now(), Tests for the LLM call recorder and its mock-replay cache key. No live Postgres…, A newline inside one field must not be able to impersonate the boundary between… (+5 more)

### Backend Api Core - "Backend Api Core"
Cohesion: 0.16
Nodes (15): argon2, argon2_exceptions, get_settings(), BaseSettings, Settings, create_access_token(), decode_access_token(), Any (+7 more)

### Backend Tests Test Llm Mock Mode Py - "Backend Tests Test Llm Mock Mode Py"
Cohesion: 0.13
Nodes (12): fake_gateway(), create(), _MockBase, Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay. The gateway is…, Stand-in for the SDK's raw-response wrapper: headers + .parse()., Build a client exposing chat.completions.with_raw_response.create., Captures every record the client emits instead of writing it anywhere., _Raw (+4 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.11
Nodes (17): computeTipLayout(), entriesToPanelMemory(), formatToolParameters(), InfoPanel(), InfoPanelProps, parseMemoryValue(), TipLayout, ToolDetail (+9 more)

### Frontend Tsconfig App Json - "Frontend Tsconfig App Json"
Cohesion: 0.09
Nodes (21): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, jsx, lib, module, moduleDetection (+13 more)

### Backend Src Utils - "Backend Src Utils"
Cohesion: 0.15
Nodes (19): atexit, Path, _safe_chat_id(), _db_loop(), _db_params(), _ensure_db_writer_started(), _ensure_table(), _logs_dir() (+11 more)

### Backend Api Services - "Backend Api Services"
Cohesion: 0.25
Nodes (14): checkpoint_tree(), list_checkpoints(), Depends, get, post, rollback(), CheckpointOut, CheckpointTreeOut (+6 more)

### Backend Src Subagents - "Backend Src Subagents"
Cohesion: 0.12
Nodes (16): Any, _calls_this_turn(), RunnableConfig, Count of human messages so far — increments once per new user message, so calls…, Responsibilities: - Read next_step["agent_name"] and next_step["task"] set by…, subagent_node(), _turn_number(), emit_subagent_event() (+8 more)

### Backend Tests Test Subagents Integration Py - "Backend Tests Test Subagents Integration Py"
Cohesion: 0.12
Nodes (12): SubagentsService, Smoke tests for per-chat agent session logger., TestAsyncWriterDoesNotBlockCaller, TestHelpersNeverRaise, End-to-end tests for EVA subagent integration. Covers: registry catalog,…, TestCatalogAPI, TestProtocolConstants, TestSubagentRegistry (+4 more)

### Backend Src Subagents - "Backend Src Subagents"
Cohesion: 0.12
Nodes (15): Retrieve experience chunks; never raise into the agent loop and never block it…, _safe_learned_experiences(), Standalone learner agent: extract experience chunks from idle chats., format_experiences_for_prompt(), Any, Safe experience retrieval for the main agent hot path., Return top-k experience chunks. Never raises — returns [] on any failure or…, retrieve_experiences() (+7 more)

### Backend Tests Test Prompt Templates Py - "Backend Tests Test Prompt Templates Py"
Cohesion: 0.14
Nodes (13): load_prompt(), Path, Render `<name>.txt` and split it into (system_prompt, user_prompt). This is the…, render_file(), _all_template_files(), Contract tests for every prompt template in the project. Guards the three…, @# lines never render, so their contents are not template variables., strict=True turns a typo'd {var} into a failure instead of an empty string —… (+5 more)

### Backend Src Utils - "Backend Src Utils"
Cohesion: 0.14
Nodes (16): get_pool(), ConnectionPool, Process-wide Postgres connection pool + small query helpers. This is the shared…, execute(), fetch_all(), fetch_one(), get_connection(), get_pool() (+8 more)

### Backend Tests Test Main Entrypoint Py - "Backend Tests Test Main Entrypoint Py"
Cohesion: 0.12
Nodes (11): _FakeEncoded, _FakeModel, The HF embedding backend must load quietly: no 'Loading weights' tqdm bar, no…, Tests for the main.py boot dispatch (API server vs interactive agent CLI)., TestDevPyRemoved, TestMainDispatch, list, main (+3 more)

### Frontend Components Json - "Frontend Components Json"
Cohesion: 0.10
Nodes (19): aliases, components, hooks, lib, ui, utils, iconLibrary, registries (+11 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.11
Nodes (11): AdvancedConsolePanelProps, AdvancedEventData, ContextMemoryEntry, ExecutionMemoryEntry, humanLabel(), LLM_LABEL_NAMES, LLMCallEntry, LLMCallsTab() (+3 more)

### Frontend Src Types - "Frontend Src Types"
Cohesion: 0.11
Nodes (19): AgentCardPayload, AgentCardPermissions, AgentStep, AgentTestCasePayload, AgentTestResultPayload, Chat, CheckpointInfo, CheckpointTreeNode (+11 more)

### Backend Api Services - "Backend Api Services"
Cohesion: 0.13
Nodes (9): Any, Depends, get, summary(), Repositories, AnalyticsService, Any, PreloadService (+1 more)

### Backend Api Domain - "Backend Api Domain"
Cohesion: 0.27
Nodes (13): login(), logout(), me(), Depends, get, post, new_session_id(), LoginRequest (+5 more)

### Backend Api Api Routes - "Backend Api Api Routes"
Cohesion: 0.13
Nodes (19): _build_graph(), get_experience(), list_experiences(), Any, Depends, get, Return experience chunks and a graph projection for visualization., list_subagents() (+11 more)

### Backend Api Services - "Backend Api Services"
Cohesion: 0.13
Nodes (9): AgentRuntime, on_subagent_event(), _emit_turn_complete(), Any, Runs one LangGraph turn and fans events into a packet queue., Cooperatively cancel the active run for this chat. `superseded=True` marks this…, _truncate(), Thin re-export — stream bridging lives in agent_runtime for cohesion. (+1 more)

### Backend Src Agent - "Backend Src Agent"
Cohesion: 0.13
Nodes (17): Per-run sub-agent progress callback plumbing (API / CLI safe). Mirrors…, Bind a sub-agent progress callback for the current context; returns a reset…, reset_subagent_callback(), set_subagent_callback(), Per-run token callback plumbing for agent_node (API / CLI safe)., Bind a token callback for the current context; returns a reset token., reset_token_callback(), reset_usage_callback() (+9 more)

### Backend Tests Test Cli Repl Py - "Backend Tests Test Cli Repl Py"
Cohesion: 0.23
Nodes (8): handle_step(), _latest_answer(), prompt_for_interrupt(), make_console(), Console, patch, TestHandleStep, TestPromptForInterrupt

### Backend Tests Test Cli Repl Py - "Backend Tests Test Cli Repl Py"
Cohesion: 0.14
Nodes (12): parse_command(), Unit tests for the live turn renderer (live rendering disabled in tests)., interrupt_step(), Unit tests for the CLI REPL: command parsing, step handling, interrupts, and…, TestParseCommand, TestRunTurnInteractive, fake_run_turn(), first() (+4 more)

### Backend Tests Test Prompt Templates Py - "Backend Tests Test Prompt Templates Py"
Cohesion: 0.22
Nodes (5): The role and persona stay stable regardless of volatile context., Baseline before this migration was ~1887 tok of scaffolding on every call, re-…, _Sub, TestAgentNodePrompt, _tools()

### Frontend Tsconfig Convex Json - "Frontend Tsconfig Convex Json"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, baseUrl, isolatedModules, lib, module, moduleDetection, moduleResolution (+10 more)

### Backend Tests Test Subagents Integration Py - "Backend Tests Test Subagents Integration Py"
Cohesion: 0.18
Nodes (5): Extra <parameters> on an agent_call reach the sub-agent as…, A sub-agent call is a single, self-contained best-effort attempt — a repeat…, A follow-up human message starts a new turn, so a retry is allowed again., TestSubagentNode, echo()

### Backend Api Domain - "Backend Api Domain"
Cohesion: 0.14
Nodes (14): ClientAck, ClientRollback, ClientRunStart, BaseModel, WsEnvelope, AgentConfig, BaseModel, Defines the external configuration parameters for the graph run. These… (+6 more)

### Backend Tests Test Prompt Render Py - "Backend Tests Test Prompt Render Py"
Cohesion: 0.19
Nodes (7): PromptRenderError, Exception, Raised in strict mode when a template references an unknown variable., render(), Tests for the declarative prompt renderer in prompt_loader.py., str.format() required {{ }} escaping; this renderer does not., TestRendering

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.21
Nodes (15): execute_bash(), execute_powershell(), execute_python_script(), _find_executable(), Any, tool, Internal tools for executing Bash commands, PowerShell commands, and Python…, Execute a Bash command and return stdout, stderr, and the return code. Runs via… (+7 more)

### Scripts Db Setup Py - "Scripts Db Setup Py"
Cohesion: 0.14
Nodes (12): Tests for scripts/db_setup.py. Static checks always run. The live integration…, TestDbSetupLive, ensure_checkpointer_tables(), ensure_database(), ensure_schema(), main(), Idempotent Postgres setup for this project. Creates the target database (if…, Create the target database if it doesn't exist yet. `CREATE DATABASE` can't run… (+4 more)

### Frontend Src Instrumentation Tsx - "Frontend Src Instrumentation Tsx"
Cohesion: 0.15
Nodes (11): AsyncError, ErrorBoundary, ErrorBoundaryState, GenericError, InstrumentationProvider(), isIgnoredRuntimeNoise(), normalizeRejection(), reportErrorToVly() (+3 more)

### Frontend Tsconfig Node Json - "Frontend Tsconfig Node Json"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, isolatedModules, lib, module, moduleDetection, moduleResolution, noEmit (+8 more)

### Backend Tests Test Llm Logger Py - "Backend Tests Test Llm Logger Py"
Cohesion: 0.18
Nodes (7): _drain_on_exit(), flush_pending_llm_calls(), Block until both sinks have drained. For tests and graceful shutdown., Both writers are daemon threads, so without this the interpreter would kill…, Record one call under a temp logs dir and return the parsed JSONL rows., TestRecordLlmCall, register

### Backend Src Prompts - "Backend Src Prompts"
Cohesion: 0.15
Nodes (9): agentnode_prompt_loader(), _has_tool(), _load_module(), Load a versioned reusable prompt module., Whether any of `names` is in the available tool list. Capability rules are…, Build the agent node's context and render `agentnode.txt`., TestPromptLoader, TestPromptInjection (+1 more)

### Backend Api Services - "Backend Api Services"
Cohesion: 0.25
Nodes (7): pick_files(), post, FilePickRequest, FilePickResponse, BaseModel, FilePickerService, Native OS file/folder picker — returns absolute paths for local agent tools.

### Backend Api Services - "Backend Api Services"
Cohesion: 0.18
Nodes (5): ChatPacketQueue, Packet, Any, Per-chat outbound packet buffer. WS flushers consume; runs only enqueue., Clear queue and bump epoch (e.g. after rollback).

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.15
Nodes (10): AGENT_MODES, AgentMode, AgentSettingsPanel(), AgentSettingsPanelProps, patchSettings(), DataSource, DataStackingInfoPanelProps, processes (+2 more)

### Frontend Src Lib - "Frontend Src Lib"
Cohesion: 0.15
Nodes (10): getAccessToken(), healthAPI, mcpAPI, toolsAPI, API_HOST, fetchMCPTools(), fetchToolsCatalog(), MCPPrompt (+2 more)

### Frontend Src Pages - "Frontend Src Pages"
Cohesion: 0.19
Nodes (11): CATEGORY_META, ExperiencesTab(), formatDate(), formatDisplayValue(), Memory(), OUTCOME_META, OUTCOMES, prettyCategory() (+3 more)

### Backend Tests Test Context Memory Py - "Backend Tests Test Context Memory Py"
Cohesion: 0.28
Nodes (5): empty_context_memory(), RunnableConfig, tool_node(), TestToolAndSubagentIngest, TestToonTokenSavings

### Backend Tests Test Context Memory Py - "Backend Tests Test Context Memory Py"
Cohesion: 0.35
Nodes (4): _coerce_token(), context_selector_node(), RunnableConfig, TestContextSelectorNode

### Backend Src Utils - "Backend Src Utils"
Cohesion: 0.23
Nodes (11): count_tokens(), Estimate token counts for input and output text (~4 chars per token)., _context_stats(), _get_limits(), input_context_checker(), output_context_checker(), Return (input_limit, output_limit) for a model, falling back to safe defaults., Summarise the given text using the LLM. (+3 more)

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.24
Nodes (12): edit_file(), Any, Path, tool, Internal tools for file I/O operations, file search, and directory management., Read content from a text-based file. Supports optional line-range slicing via…, Make targeted edits to a text file by replacing an exact string match. Finds…, Search a text file for lines matching a pattern or literal string. Streams the… (+4 more)

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.15
Nodes (11): get_current_datetime_info(), GetCurrentDatetimeInfoArgs, Any, BaseModel, field_validator, tool, Internal tool for getting comprehensive date and time information in the user's…, Get comprehensive date and time information for the user's current timezone.… (+3 more)

### Tests Test Backend Correctness Py - "Tests Test Backend Correctness Py"
Cohesion: 0.21
Nodes (7): check_atomic_admission(), check_message_sync(), check_rollback_ownership(), Connection, connection_context(), Message, Focused runnable checks for backend checkpoint and runtime correctness.

### Backend Tests Test Py - "Backend Tests Test Py"
Cohesion: 0.24
Nodes (5): argparse, GitHubRepoDownloader, main(), re, requests

### Backend Api Ws - "Backend Api Ws"
Cohesion: 0.23
Nodes (9): asyncio, chat_ws(), _handle_client_message(), Any, WebSocket, Accept then close so clients always get a proper close frame., _reject(), WebSocket protocol helpers. (+1 more)

### Backend Src Models - "Backend Src Models"
Cohesion: 0.23
Nodes (11): _embed_numpy(), embed_text(), embed_texts(), _get_hf_model(), Local text embeddings: sentence-transformers model, or a dependency-free numpy…, Deterministic hashing bag-of-words vectorizer (no ML dependencies)., Embed a single string using the configured local method., Embed multiple strings, batching when possible. (+3 more)

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.26
Nodes (6): BashArgs, _check_blacklist(), PowerShellArgs, BaseModel, field_validator, PythonScriptArgs

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.26
Nodes (11): _brave_search(), _ddg_search(), _import_ddgs(), _import_requests(), Any, tool, Internal tool for web search. Primary provider : Brave Search API (set…, DuckDuckGo web search via ddgs library — no key required, full search results. (+3 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.21
Nodes (10): CHECKPOINT_PRIMARY_BTN, CheckpointActionPanel(), CheckpointActionPanelProps, checkpointDetailText(), checkpointNodeStyle(), NODE_STYLE, formatArgs(), InterruptPrompt() (+2 more)

### Frontend Readme Md - "Frontend Readme Md"
Cohesion: 0.22
Nodes (11): Project Agent Guide, Backend API and Agent Runtime, Frontend Application, Project Knowledge Graph, Cross-Application Tests, Frontend README, Convex Authentication, Convex Backend (+3 more)

### Backend Api Db - "Backend Api Db"
Cohesion: 0.36
Nodes (7): analytics_dir(), analytics_events_file(), data_root(), experience_dir(), Path, AnalyticsRepository, Any

### Backend Tests Test Context Memory Py - "Backend Tests Test Context Memory Py"
Cohesion: 0.27
Nodes (4): Conditional edge out of agent_node. Reads next_step["action"] and returns the…, route_from_agent(), TestRouting, TestRouting

### Backend Src Subagents - "Backend Src Subagents"
Cohesion: 0.20
Nodes (4): BackgroundIdleWatcher, IdleWatcher, Asyncio polling loop; learn work runs in a worker thread., Run the async watcher in a daemon thread for non-async entrypoints.

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.24
Nodes (10): Any, BaseModel, tool, Tools for reading and writing per-user long-term memory / preferences., Save a durable memory piece or preference for the logged-in user. Call when the…, Fetch the logged-in user's stored memory entries and preferences. Use when a…, user_memory_fetch(), user_memory_update() (+2 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.18
Nodes (9): DropdownMenuCheckboxItem, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuRadioItem, DropdownMenuSeparator, DropdownMenuSubContent, DropdownMenuSubTrigger (+1 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.18
Nodes (7): InputOTP, InputOTPGroup, InputOTPSeparator, InputOTPSlot, input-otp, @radix-ui/react-icons, react-resizable-panels

### Backend Api Domain - "Backend Api Domain"
Cohesion: 0.36
Nodes (8): health(), live(), Depends, get, HealthResponse, LiveResponse, BaseModel, get_agent_app()

### Backend Api Services - "Backend Api Services"
Cohesion: 0.42
Nodes (7): _mcp_tools_from_metadata(), _parameters_from_mcp_item(), _parameters_from_schema(), _parameters_from_schema_dict(), Any, _tool_info(), ToolsService

### Backend Src Bootstrap Py - "Backend Src Bootstrap Py"
Cohesion: 0.33
Nodes (9): ensure_venv_on_path(), get_python_executable(), get_venv_python(), get_venv_site_packages(), Path, Ensure the project .venv is used by the current Python process., Prepend the project venv site-packages directory to sys.path., Return the project venv Python when available, otherwise sys.executable. (+1 more)

### Backend Src Prompts - "Backend Src Prompts"
Cohesion: 0.27
Nodes (8): _Node, _parse(), Prompt rendering and loading for every agent and sub-agent in the project. One…, _render_node(), _subst(), replace(), _tidy(), toons

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.24
Nodes (6): EditFileArgs, BaseModel, field_validator, ReadFileArgs, SearchFileArgs, model_validator

### Backend Src Utils - "Backend Src Utils"
Cohesion: 0.24
Nodes (6): Recursively truncate oversized strings in payloads., Append-only JSONL writer for one chat session., SessionLogger, truncate_value(), _utc_now(), TestTruncate

### Backend Tests Test Endpoints Py - "Backend Tests Test Endpoints Py"
Cohesion: 0.24
Nodes (9): check(), main(), Comprehensive endpoint + edge-case tests for the EVA FastAPI API., Return True if the socket is rejected/closed without a session.ready., ws_rejected(), fastapi_testclient, starlette_websockets, TestClient (+1 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.31
Nodes (9): CATEGORY_COLOR, categoryColor(), clamp(), LayoutNode, lerp(), MemoryGraph(), MemoryGraphProps, prettyCategory() (+1 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.24
Nodes (9): Card, CardProps, CardRef, CardSwap(), CardSwapProps, makeSlot(), placeNow(), Slot (+1 more)

### Backend Opencode Plugins - "Backend Opencode Plugins"
Cohesion: 0.22
Nodes (6): IMPORTANT: keep the reminder string free of backticks and $(...) constructs., ref_fs, ref_path, @tailwindcss/vite, vite, @vitejs/plugin-react

### Backend Tests Test Prompt Render Py - "Backend Tests Test Prompt Render Py"
Cohesion: 0.33
Nodes (6): _fmt(), Any, Serialize structured prompt context as TOON., to_toon(), json.dumps(indent=2) was 2.6x more tokens for the same data., TestFormatting

### Backend Tests Test Prompt Render Py - "Backend Tests Test Prompt Render Py"
Cohesion: 0.36
Nodes (3): _present(), The prototype returned True here, so `if=turn_start` always fired and the model…, TestPresence

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.22
Nodes (8): decompose_query(), DecomposeQueryArgs, Any, BaseModel, tool, Tool for decomposing a user query into a structured, multi-dimensional…, Decompose a user query into a structured multi-dimensional breakdown. Produces…, src_models_llm_client

### Frontend Package Json - "Frontend Package Json"
Cohesion: 0.22
Nodes (9): scripts, build, dev, format, lint, preview, test, test:coverage (+1 more)

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.36
Nodes (8): CheckpointTree(), CheckpointTreeProps, labelLineCount(), LaidOutNode, layout(), nodeLabel(), nodeStyle(), ref_components_checkpointactionpanel

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.31
Nodes (8): clamp(), ExperienceGraph(), ExperienceGraphProps, LayoutLink, LayoutNode, lerp(), OUTCOME_COLOR, outcomeColor()

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.25
Nodes (7): Any, tool, Internal tool for getting comprehensive system information., Return comprehensive information about the host system. Covers OS, CPU, memory,…, system_info(), langchain_core_tools, platform

### Backend Tests Test Embeddings Quiet Py - "Backend Tests Test Embeddings Quiet Py"
Cohesion: 0.32
Nodes (3): HfLoadIsQuiet, _install_fakes(), Fake sentence_transformers + transformers.utils.logging. Returns a record.

### Backend Tests Test Subagents Integration Py - "Backend Tests Test Subagents Integration Py"
Cohesion: 0.36
Nodes (4): Simulate the node-update fan-out logic used by AgentRuntime.run_turn., Mirror the fixed started/finished branching from agent_runtime., Regression: previously node_name==subagent_node also fired started., TestAgentRuntimeFanout

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.25
Nodes (6): defaultColors, LiquidEther(), LiquidEtherProps, LiquidEtherWebGL, SimOptions, three

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.25
Nodes (5): DialogContent, DialogDescription, DialogOverlay, DialogTitle, @radix-ui/react-dialog

### Frontend Src Components - "Frontend Src Components"
Cohesion: 0.25
Nodes (3): SwapCardContext, SwapCardItemProps, SwapCardProps

### Frontend Src Hooks - "Frontend Src Hooks"
Cohesion: 0.25
Nodes (7): clearAuthStorageMock, getAccessTokenMock, loginMock, logoutMock, meMock, setAccessTokenMock, ref_hooks_use_backend_auth

### Backend Src Utils - "Backend Src Utils"
Cohesion: 0.43
Nodes (6): _record_tool_result(), Any, Shared stringify + truncate helpers for AIMessage previews., stringify_for_preview(), truncate_for_aimessage(), truncate_text()

### Backend Src Subagents - "Backend Src Subagents"
Cohesion: 0.33
Nodes (4): build_embed_text(), Build retrieval / embed keys shared by learner and main agent., Situation key used for both indexing and retrieval., TestEmbedKeys

### Frontend Package Json - "Frontend Package Json"
Cohesion: 0.29
Nodes (6): eslint-config-prettier, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh, globals, typescript-eslint

### Backend Src Config Py - "Backend Src Config Py"
Cohesion: 0.33
Nodes (4): get_settings(), BaseSettings, Create standard data/log directories if missing. Users, chats, and checkpoints…, Settings

### Backend Tests Test Experience System Py - "Backend Tests Test Experience System Py"
Cohesion: 0.40
Nodes (4): learn_session(), Any, Run the learner graph for one chat. Soft-fails: returns status dict, never…, TestLearnSessionSoftFail

### Backend Tests Test Llm Logger Py - "Backend Tests Test Llm Logger Py"
Cohesion: 0.47
Nodes (3): lookup_cached_response(), Most recent successful, non-replayed call with this exact key. Global across…, TestLookupSoftFails

### Frontend Src Lib - "Frontend Src Lib"
Cohesion: 0.33
Nodes (5): LS_ACTIVE_TOOL_BUCKET, LS_TOOL_BUCKETS, TOOL_BUCKET_ALL_ID, TOOL_BUCKET_MIXED_ID, ToolBucketDef

### Backend Src Models - "Backend Src Models"
Cohesion: 0.40
Nodes (4): Top-level package for models. This package automatically imports submodules in…, importlib, mnt_c_users_aanzar_onedrive_rimini_street_documents_agenticai_meta_agent_v2_backend_src_models_version_py, pkgutil

### Backend Src Tools - "Backend Src Tools"
Cohesion: 0.50
Nodes (3): BaseModel, field_validator, WebSearchArgs

### Frontend Src Lib - "Frontend Src Lib"
Cohesion: 0.40
Nodes (4): mockMemory, mockMessages, mockSessions, mockUser

### Backend File Structure Py - "Backend File Structure Py"
Cohesion: 0.50
Nodes (3): generate_tree(), Path, Recursively generates a string representation of a directory tree.

### Frontend Src Lib - "Frontend Src Lib"
Cohesion: 0.50
Nodes (3): EVA_BEDROCK_MODEL_IDS, NODE_MODEL_LABELS, NodeModelKey

## Knowledge Gaps
- **485 isolated node(s):** `$schema`, `plugin`, `$schema`, `style`, `rsc` (+480 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1048 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TurnRenderer` connect `Backend Src Cli` to `Backend Src Cli`, `Backend Src Agent`, `Backend Tests Test Cli Repl Py`, `Backend Tests Test Cli Repl Py`, `Backend Src Cli`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Why does `react` connect `Frontend Src Hooks` to `Frontend Src Pages`, `Frontend Package Json`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Instrumentation Tsx`, `Frontend Src Components`, `Frontend Src Pages`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`, `Frontend Src Components`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `dependencies` connect `Frontend Package Json` to `Frontend Package Json`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Are the 34 inferred relationships involving `CurrentUser` (e.g. with `summary()` and `logout()`) actually correct?**
  _`CurrentUser` has 34 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `Repositories` (e.g. with `summary()` and `login()`) actually correct?**
  _`Repositories` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `TurnRenderer` (e.g. with `handle_step()` and `run_turn_interactive()`) actually correct?**
  _`TurnRenderer` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `$schema` to the rest of the system?**
  _485 weakly-connected nodes found - possible documentation gaps or missing edges._