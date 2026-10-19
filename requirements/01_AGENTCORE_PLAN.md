# AgentCore implementation plan

## Scope and decisions

- Implement `01_AGENTCORE_REQUIREMENTS.md` and its mandatory `02_TRACE_SCHEMA.md` dependency. The new chunk/version store in `03_MEMORY_PHASE_1_REQUIREMENTS.md` is a later phase; AgentCore's policy-controlled memory boundary is in scope now.
- Persist minimal PostgreSQL agent, policy, run, child and result records. Keep existing chat transcripts and LangGraph checkpoints.
- Spawn returns a child ID immediately. The parent can do other work, await selected children explicitly, and must collect or cancel outstanding children before finishing its run.
- Reject a concurrent run for one agent; close terminal children automatically. A top-level agent remains open between runs.

## Implementation checklist

### 1. Durable identity and lifecycle

- [x] Add `backend/src/agent/agent_core.py`: AgentID, Policy, Message, AgentCore, lifecycle transitions, versioned policy updates, per-agent conversation and child handles.
- [x] Edit `scripts/db_setup.py`: idempotent agent, run and conversation/result tables and indexes. Update `backend/tests/test_db_setup.py`.
- [x] Add `backend/api/db/repositories/agents.py`; register in `backend/api/db/repositories/__init__.py` and `backend/api/core/deps.py`: create/load by chat, atomic run reservation/finish, policy version updates, durable child status/result and close.
- [x] Edit `backend/api/services/chat_service.py` to create/load a top-level agent for each chat, including existing chats; retain existing ownership checks and response shape.
- [x] Edit `backend/api/services/chat_runtime_manager.py` to coordinate persisted active runs with existing independent per-chat threads, propagate trusted user/session IDs, and handle interrupted/resumed runs without closing top-level agents.
- [x] Edit `backend/api/services/agent_runtime.py`, `backend/src/utils/postgres_checkpointer.py` and `backend/src/cli/repl.py` so API and CLI turns share stable agent identity, distinct run IDs, log IDs, policy version and checkpoint correlation.

### 2. Effective permissions and memory boundary

- [x] Initialize armory, memory, guardrails and observability from mandatory policy in `backend/src/agent/agent_core.py`; allow only authorized, atomic, versioned armory/memory updates.
- [x] Restrict client preferences in `backend/api/services/preferences_service.py` and `backend/api/domain/memory.py` so they cannot forge tenant membership or immutable policy.
- [x] Enforce effective armory permissions at discovery and invocation in `backend/src/agent/nodes/agentnode.py`, `backend/src/agent/nodes/toolnode.py` and `backend/api/services/mcp_runtime.py`; preserve human tool confirmation.
- [x] Route `backend/src/tools/user_memory.py`, `backend/api/services/memory_service.py` and `backend/src/subagents/learner_agent/retrieve.py` through policy-controlled memory access. USER storage works; the separately scoped TENANT/AGENT chunk store remains in Memory Phase 1, with no unscoped fallback.

### 3. Nonblocking child agents

- [x] Add immediate-return spawn, specific-child await, timeout/cancel, count/depth limits and policy intersection in `backend/src/agent/agent_core.py`; persist terminal result before idempotent auto-close.
- [x] Keep `backend/src/agent/nodes/subagentnode.py` for synchronous configured armory subagent calls.
- [x] Add dedicated child-agent spawning path with batched calls (`spawn_children`) and a separate child node.
- [x] Wire pending handles, explicit collection, and join-or-cancel before parent completion through `backend/src/agent/graph.py`, `backend/src/agent/edges/routing.py`, `backend/src/agent/nodes/agentnode.py` and `backend/src/agent/nodes/collect_child.py`. Running child cancellation is cooperative at the adapter boundary.
- [x] Pass effective policy and trace identity to child adapters and route child-ID progress through `backend/src/agent/subagent_stream.py`.
- [x] Edit `backend/api/services/agent_runtime.py` to keep `subagent.*` for configured subagents and emit separate `child.*` packets for spawned AgentCore children.

### 4. End-to-end backend tracing

- [x] Add `backend/src/utils/trace.py`: canonical `02_TRACE_SCHEMA.md` JSON envelope, event validation, redaction, start/end/error spans, and context propagation across threads/callbacks.
- [x] Update `backend/src/utils/agent_logger.py` and `backend/api/core/logging_setup.py` for queryable structured trace emission. Canonical traces use Python logging independently of the best-effort legacy per-chat JSONL writer.
- [x] Trace HTTP and WS entry/exit/errors in `backend/api/app.py` and `backend/api/ws/endpoint.py`.
- [x] Trace run, interrupt/resume/cancel, checkpoints, routing, nodes, tool/armory authorization, guardrails, children, memory and policy changes in their respective runtime/node/service/repository files above and `backend/api/services/checkpoint_service.py`.
- [x] Add `node.execution.error` to `requirements/02_TRACE_SCHEMA.md`. Preserve separate frontend packet names.

### 5. Verification

- [x] Add `backend/tests/test_agent_core.py` for independent children, one active run, interrupted/busy close, child immutability, policy versions, cancellation and lineage; run a live PostgreSQL spawn/result/closure check.
- [x] Retain and run `backend/tests/test_subagents_integration.py` alongside AgentCore tests.
- [x] Add `backend/tests/test_trace_schema.py` for required IDs, lineage, redaction, node failures, and handled exceptions.
- [x] Update `backend/tests/test_db_setup.py` and stale prompt/user/contract test assertions; run the backend suite and root correctness/contract checks.
- [x] Run `graphify update .` in `backend/` after implementation, per `backend/AGENTS.md`.

## Verification status (2026-10-05)

- Backend pytest: 258 passed, 29 subtests passed.
- Live PostgreSQL schema and durable child spawn/result/closure check passed.
- Root backend correctness and frontend/backend contract checks passed.
