# AgentCore Requirements (Initial Implementation Draft)

Status: draft for implementation planning.

## 1) Purpose

Define a minimal, implementable AgentCore architecture where:
- each chat session is represented by one top-level `AgentCore`
- each delegated worker is a child `AgentCore`
- active agents run independently (no waiting on unrelated agents)
- policy initializes and governs armory/memory/guardrails/observability
- child lifecycle is simple (close child when done)

This document is intentionally structured for coding agents to implement in steps.

## 2) Scope

### In scope
- Agent identity model (`AgentID`)
- Agent lifecycle/state model (including `closed`)
- Policy model and mutability rules
- Agent-owned conversation model
- Child spawning contract (`spawn_child`)
- Required runtime behavior for independent execution
- Acceptance criteria and implementation checklist

### Out of scope (for this draft)
- Full memory-store migration details
- Learner extraction/promotion internals
- New database schema definitions
- UI/UX redesign

## 3) Glossary

- AgentCore: runtime object for a top-level chat or child task agent.
- Top-level agent: chat-owned agent for a user session.
- Child agent: agent owned by another agent, created via delegation.
- Run: one execution cycle of an agent.
- Session ID: latest user login session marker (not the same as run/checkpoint thread).
- Policy: armory/memory/guardrails/observability configuration.
- Closed agent: immutable, non-runnable, non-reopenable agent.
- Agent-scoped memory: globally readable platform memory; it is not tied to an `AgentCore.agent_id`.

## 4) Core design decisions

1. One top-level AgentCore per chat session.
2. Child agents are durable records owned by the parent agent.
3. Active agents run independently from each other.
4. One active run per AgentCore at a time; run outcomes do not close a top-level agent.
5. `armory` and `memory` policy are mutable; `guardrails` and `observability` are immutable.
6. Child effective permissions are bounded by parent effective permissions.
7. Global/agent memory level exists for universal platform-agent experiences, independent of AgentCore instance IDs.
8. Child agents are expected to be closed once purpose is complete.

## 5) Required behavior

### 5.1 Independent execution requirement

- If 5 agents are active, each must progress without waiting on unrelated agents.
- Implementation may use threads, asyncio tasks, workers, or a hybrid.
- Requirement is independence of execution and state, not permanent thread allocation.
- Idle agents should not require dedicated workers.

### 5.2 Identity requirements

Each `AgentCore` has:
- stable `agent_id`
- `owner_id` and `owner_type` (`user` or `agent`)
- optional `parent_agent_id` (for children)
- `latest_session_id` (the authenticated login session for top-level tracking)

`agent_id` identifies a chat or child instance for runtime lineage, not a memory-access namespace. A global memory chunk has no `agent_id`.

Each execution has a unique `execution_id`; a login `session_id` may encompass several executions.

### 5.3 Policy initialization and mutability

At AgentCore creation, policy is mandatory and must initialize:
- `armory`
- `memory`
- `guardrails`
- `observability`

Mutability:
- allowed: `armory`, `memory`
- disallowed after create: `guardrails`, `observability`

Policy updates are:
- authorized
- versioned
- atomic at call boundaries
- applied to future calls/runs (not retroactive to already-authorized in-flight actions)

Memory policy may grant user, tenant, and global reads independently. A tenant scope is available only when the effective memory policy contains a trusted `tenant_id`; absence of that ID removes tenant retrieval entirely. Policy updates must not create tenant membership from an unverified client value. A child cannot gain a tenant scope absent from its parent effective policy.

### 5.4 Conversation requirements

- Each agent owns its own message list.
- Parent conversation stores child delegation and outcome entries by `child_agent_id`.
- Child keeps full transcript separately.
- Parent should not blindly inline full child transcript into its own prompt history.

### 5.5 Child spawn contract

`spawn_child` must:
- create child AgentCore with parent ownership
- start child work independently
- return child identifier/handle immediately
- allow parent to await specific children and collect results
- reject close while a child's run is active; cancel/finish the run first

Child permission model:
- `effective_child_policy = intersect(platform_constraints, parent_effective_policy, requested_child_policy)`

Runtime limits required:
- max children per parent run
- max nesting depth
- per-child timeout/runtime limit

### 5.6 Codebase-wide tracing requirement

Proper tracing is mandatory across the full backend codebase, not just agent execution hotspots.

Required tracing standards (event names, status values, and envelope are defined by `requirements/02_TRACE_SCHEMA.md`):
- Every request, run, tool call, configured-subagent call, child-agent call, memory operation, policy update, and guardrail decision must emit structured trace events.
- Every execution trace must include `agent_id`, `execution_id`, and when applicable `parent_agent_id`, `child_agent_id`, `session_id`, and `owner_id`.
- Every major operation must emit both start and end events with status (`success`, `error`, `cancelled`, `timeout`), duration, and error details when failed.
- Trace schema must be consistent across modules so events can be queried end-to-end for a single run.
- Trace propagation must be explicit across thread/task boundaries, child delegation boundaries, and callbacks.
- No silent failure paths: caught exceptions must still emit failure trace events.
- Sensitive data must be redacted in traces according to guardrail/security policy.

Minimum trace coverage areas:
- API request entry/exit and websocket session lifecycle.
- Agent run lifecycle (`run.started`, `run.interrupted`, `run.completed`, `run.error`).
- Node transitions and routing decisions.
- Armory discovery/invocation and resource authorization outcomes.
- Memory retrieval/write/update outcomes.
- `spawn_child` lifecycle (spawned, running, progress, completed/failed, closed).
- Policy update events with before/after policy version metadata.
- Guardrail checks and decisions.
- Checkpointer operations needed for run traceability.

Trace quality requirements:
- Use structured logs/events (machine-parsable fields) instead of ad-hoc text-only logs.
- Event names must be stable and documented.
- Sampling (if any) must not remove critical lifecycle/error events.
- Tracing must be test-validated for required critical paths.

## 6) Lifecycle and closure model

### 6.1 States

Agent states: `open`, `closed`. Execution states: `running`, `completed`, `failed`, `cancelled` (plus `interrupted` while awaiting resume). Outcomes are recorded per `execution_id`, not as terminal agent states.

### 6.2 State transition rules

Only these agent transitions are valid:
- `open -> closed` (only when no run is running or interrupted)

Each run transitions from `running` to a terminal result (or `interrupted`, then resumed/cancelled). A top-level agent stays `open` across runs. A child may be closed after its run reaches a terminal result.

No transition out of `closed`.

### 6.3 Closed semantics

If state is `closed`:
- no new runs
- no conversation edits
- no policy updates
- no reopen

Closing a running or interrupted agent is rejected; it must first finish or be cancelled.

Rules by agent type:
- top-level agents: normally not closed via regular runtime flow
- child agents: should be closed when delegation purpose is complete

### 6.4 Close API behavior

- `close()` must be idempotent.
- Calling `close()` on an already closed agent returns success no-op.
- `close()` on an agent with a running or interrupted run returns `agent_busy` without changing state.

## 7) State machine (text diagram)

```text
agent: open --close when idle--> closed
run:   running --success/error/cancel--> completed/failed/cancelled
       running --pause--> interrupted --resume--> running
top-level agent remains open; child closes after terminal run result
```

## 8) Memory boundary (agent-level responsibilities only)

For this phase:
- AgentCore must construct and use a `Memory` object from policy.
- Memory object enforces read/write scope for the agent.
- Retrieval can run per call according to memory policy.
- USER access uses the authenticated user identity; TENANT access requires a trusted tenant ID in effective memory policy; AGENT access is the global store available to authenticated platform users when policy permits. No tenant ID means no tenant memory access.

Not required in this phase:
- learner extraction redesign
- promotion workflow implementation details
- store internals beyond contract

Visibility levels to preserve in contract:
- user
- tenant
- agent/global (platform-wide universal experiences, no instance `agent_id` on chunks)

## 9) Observability and tracing contract

Observability is not optional. Implementation must provide end-to-end traceability from API entry through agent orchestration, tools, memory, subagents, and completion.

### 9.1 Required event taxonomy

Use the canonical names in `requirements/02_TRACE_SCHEMA.md` for API, session, run, node, tool, configured-subagent, child-agent, memory, policy, guardrail, and checkpoint events. Frontend packet names such as `run.started` are a separate transport contract.

### 9.2 Required event fields

Each event should include:
- timestamp (UTC)
- event name
- status
- duration_ms (for end/error events)
- `agent_id`
- `execution_id` (when in execution scope)
- `owner_id` (where available)
- `session_id` (where available)
- `parent_agent_id` / `child_agent_id` (where applicable)
- error code/message/class (for failure paths)

### 9.3 Traceability guarantees

- A single run must be reconstructable from traces alone.
- Parent-child execution lineage must be reconstructable via IDs and events.
- It must be possible to answer: who invoked what, when, under which policy version, and with what outcome.

### 9.4 Testing requirement

Add focused tests for trace-critical flows:
- normal run
- tool success/failure
- child spawn + completion + close
- cancellation/timeout paths
- handled exceptions still producing error traces

## 10) Mock class templates

```python
from dataclasses import dataclass
from typing import Literal
from uuid import UUID


@dataclass(frozen=True)
class AgentID:
    agent_id: UUID
    owner_id: UUID
    owner_type: Literal["user", "agent"]
    latest_session_id: UUID | None = None
    parent_agent_id: UUID | None = None


@dataclass(frozen=True)
class Policy:
    armory: dict
    memory: dict
    observability: dict
    guardrails: dict
    version: int = 1


@dataclass(frozen=True)
class Message:
    message_id: UUID
    content: str
    sender_id: UUID
    sender_type: Literal["user", "agent", "tool", "system"]
    execution_id: UUID
    created_at: str
    child_agent_id: UUID | None = None
    visible_to_user: bool = True


@dataclass
class AgentCore:
    id: AgentID
    conversation: list[Message]
    policy: Policy
    armory: "Armory"
    memory: "Memory"
    guardrails: "Guardrails"
    observability: "Observability"
    state: Literal["open", "closed"] = "open"
    active_execution_id: UUID | None = None
    auto_close_on_result: bool = False  # should default True for child agents

    def run(self, input_message: Message) -> UUID:
        ...

    def spawn_child(self, task: str, requested_policy: Policy | None = None) -> AgentID:
        ...

    def update_armory_policy(self, new_scope: dict) -> None:
        ...

    def update_memory_policy(self, new_scope: dict) -> None:
        ...

    def close(self) -> None:
        ...


class Armory:
    def update_policy(self, new_scope: dict) -> None: ...
    def invoke(self, resource_type: str, name: str, arguments: dict) -> object: ...


class Memory:
    def update_policy(self, new_scope: dict) -> None: ...
    def retrieve(self, query: str) -> list[object]: ...


class Guardrails:
    def check_input(self, message: Message) -> object: ...
    def check_resource_call(self, resource: str, arguments: dict) -> object: ...
    def check_output(self, message: Message) -> object: ...


class Observability:
    def record(self, event: str, details: dict) -> None: ...
```

## 11) Implementation checklist (coding-agent ready)

### Phase A: models and contracts
- [ ] Separate reusable agent state from per-run results and add `closed` semantics.
- [ ] Add one-way state transition validator.
- [ ] Add/align `AgentID` fields (`owner_type`, `parent_agent_id`, etc.).
- [ ] Add policy versioning and mutable/immutable partition.

### Phase B: runtime behavior
- [ ] Enforce single active run per AgentCore.
- [ ] Reject new run with `already_running` unless queueing is explicitly enabled.
- [ ] Implement independent execution model for concurrent agents.
- [ ] Attach run-level IDs and logging correlation.

### Phase B2: tracing foundation (mandatory)
- [ ] Define a stable tracing event taxonomy and schema.
- [ ] Add correlation ID propagation helpers across threads/tasks/callbacks.
- [ ] Standardize start/end/error trace emission helpers.
- [ ] Ensure exception paths emit structured error traces.

### Phase C: child agents
- [ ] Implement `spawn_child` with immediate return handle.
- [ ] Enforce child effective-policy intersection.
- [ ] Add child limits (count, depth, timeout).
- [ ] Persist child status and result for parent retrieval.
- [ ] Add `auto_close_on_result` path for child agents.
- [ ] Emit parent-child lineage traces for spawn/progress/end/close.

### Phase D: closure and immutability
- [ ] Implement idempotent `close()` for idle agents and reject close while running/interrupted.
- [ ] Block run/policy/message edits when closed.
- [ ] Keep top-level agents non-closed in normal runtime flow.
- [ ] Ensure closed child remains queryable but immutable.

### Phase E: acceptance tests
- [ ] Concurrency test: multiple agents progress independently.
- [ ] Closure test: active child cannot close; closed child cannot reopen or mutate; top-level agent accepts another run after completion.
- [ ] Policy test: armory/memory mutable; guardrails/observability immutable.
- [ ] Delegation test: child cannot exceed parent permissions.
- [ ] Trace tests: required lifecycle/error events are emitted with required IDs.

## 12) Acceptance criteria

1. Multiple active agents can progress in parallel without unrelated blocking.
2. One active run per agent is enforced deterministically.
3. Child agents can run in parallel and report results by child ID.
4. Child agents can be closed and cannot be reopened.
5. Closed agent rejects run, write, and policy update operations.
6. Top-level agents remain non-closed in standard runtime path.
7. Armory/memory policy updates apply safely to subsequent operations.
8. Guardrails/observability policy cannot be mutated after agent creation.
9. End-to-end tracing exists across API, runtime, tools, memory, policy, and subagents with correlation IDs.
10. Critical error/cancel/timeout paths emit structured failure traces (no silent failures).

## 13) Open choices

1. Busy-agent behavior default is currently `reject`; switch to queue only if needed.
2. Child defaults should be `auto_close_on_result=True` unless a workflow explicitly requires post-completion inspection window.
3. Parent wait semantics should be explicit handle-based waits (not implicit wait-for-all).
