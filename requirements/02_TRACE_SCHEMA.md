# Trace Schema (Backend + Agent Runtime)

Status: required baseline schema for implementation.

## 1) Purpose

Define one structured tracing schema for the entire backend so every request, run, tool call, configured-subagent, child-agent, memory operation, policy action, and guardrail decision is traceable end-to-end.

This schema is designed to be:
- machine-parsable
- stable across modules
- easy to query by correlation IDs
- safe for production logging

## 2) Scope

In scope:
- event envelope format
- required/optional fields
- event naming taxonomy
- parent-child correlation rules
- error and redaction requirements
- minimal examples

Out of scope:
- storage backend choice (ELK, OpenSearch, Datadog, etc.)
- dashboard implementation
- log transport plumbing

## 3) Event naming convention

Format:

```text
<domain>.<entity>.<action>
```

Examples:
- `api.request.start`
- `run.lifecycle.end`
- `tool.call.error`
- `child.lifecycle.spawn`
- `memory.retrieve.end`

Rules:
- lowercase, dot-separated
- stable names (no ad-hoc free-form event names)
- new names require schema update

## 4) Canonical event envelope

Every trace event must follow this envelope.

```json
{
  "ts": "2026-10-05T10:12:34.567Z",
  "event": "run.lifecycle.start",
  "status": "ok",
  "level": "info",
  "message": "Run started",

  "trace": {
    "trace_id": "trc_01J...",
    "span_id": "spn_01J...",
    "parent_span_id": null
  },

  "ids": {
    "request_id": "req_01J...",
    "agent_id": "agt_01J...",
    "execution_id": "exe_01J...",
    "session_id": "sess_01J...",
    "owner_id": "usr_01J...",
    "owner_type": "user",
    "tenant_id": "ten_01J...",
    "parent_agent_id": null,
    "child_agent_id": null
  },

  "runtime": {
    "service": "backend",
    "component": "agent_runtime",
    "environment": "prod",
    "host": "api-1",
    "thread": "agent_123",
    "process": 4123,
    "version": "git:abcd123"
  },

  "metrics": {
    "duration_ms": null,
    "attempt": 1
  },

  "data": {},
  "error": null,
  "security": {
    "contains_redacted": false,
    "redaction_tags": []
  }
}
```

## 5) Field requirements

### 5.1 Required fields (all events)

- `ts`
- `event`
- `status` (`ok`, `error`, `cancelled`, `timeout`, `denied`)
- `level` (`debug`, `info`, `warn`, `error`)
- `trace.trace_id`
- `trace.span_id`
- `ids.agent_id` (or null only for pre-agent API events)
- `runtime.service`
- `runtime.component`
- `data` (object, may be empty)

### 5.2 Required on run-scoped events

- `ids.execution_id`
- `ids.owner_id` (if authenticated)
- `ids.tenant_id` (when a trusted tenant ID is available in effective policy; otherwise null)

### 5.3 Required on end/error events

- `metrics.duration_ms`
- `status` final value

### 5.4 Required on failure events

- `error.code`
- `error.type`
- `error.message`

Stack traces are optional and environment-gated.

## 6) Correlation and propagation rules

1. `trace_id` is constant for one top-level request/run path.
2. New operation = new `span_id`, linked via `parent_span_id`.
3. Child spawn must create child span linked to parent span.
4. Thread/task boundary crossings must explicitly carry trace context.
5. WebSocket events must preserve correlation IDs from originating run when applicable.
6. If an ID is unknown, use null and populate once known in subsequent events.
7. `ids.agent_id` is an AgentCore instance ID for tracing; global memory chunks have no `agent_id`. For memory events record `scope` in `data` and use `ids.owner_id` / `ids.tenant_id` when applicable; do not log content.
8. These are backend trace events; websocket UI packets (for example `run.started`) have their own names and are not alternate trace taxonomy entries.

## 7) Event taxonomy (minimum)

### 7.1 API and session
- `api.request.start`
- `api.request.end`
- `api.request.error`
- `session.websocket.attach`
- `session.websocket.detach`

### 7.2 Agent run lifecycle
- `run.lifecycle.start`
- `run.lifecycle.interrupt`
- `run.lifecycle.cancel`
- `run.lifecycle.end`
- `run.lifecycle.error`

### 7.3 Node and routing
- `node.execution.start`
- `node.execution.end`
- `node.execution.error`
- `node.routing.decision`

### 7.4 Tooling and armory
- `armory.discovery.list`
- `armory.authz.allow`
- `armory.authz.deny`
- `tool.call.start`
- `tool.call.end`
- `tool.call.error`

### 7.5 Memory
- `memory.retrieve.start`
- `memory.retrieve.end`
- `memory.retrieve.denied`
- `memory.write.start`
- `memory.write.end`
- `memory.write.denied`
- `memory.promotion.requested`, `memory.promotion.validated`, `memory.promotion.approved`, `memory.promotion.rejected`, `memory.promotion.activated`, `memory.promotion.failed`
- `memory.promotion.cancelled`
- `memory.revoke`, `memory.demote`
- `memory.revalidate`

### 7.6 Subagents and child agents
- `subagent.lifecycle.spawn`
- `subagent.lifecycle.start`
- `subagent.lifecycle.progress`
- `subagent.lifecycle.end`
- `subagent.lifecycle.error`
- `subagent.lifecycle.close`
- `child.lifecycle.spawn`
- `child.lifecycle.start`
- `child.lifecycle.progress`
- `child.lifecycle.end`
- `child.lifecycle.error`
- `child.lifecycle.close`

### 7.7 Guardrails and policy
- `guardrail.input.check`
- `guardrail.resource.check`
- `guardrail.output.check`
- `guardrail.decision.allow`
- `guardrail.decision.deny`
- `guardrail.decision.approval_required`
- `policy.armory.update`
- `policy.memory.update`

### 7.8 Checkpointer
- `checkpoint.create`
- `checkpoint.list`
- `checkpoint.resume`
- `checkpoint.error`

## 8) Event-specific `data` contract

`data` must be event-specific and bounded. Suggested required keys:

- `api.request.*`
  - `method`, `path`, `http_status` (end/error), `client_type`

- `run.lifecycle.*`
  - `reason` (interrupt/cancel/error), `checkpoint_id` (if available), `resumed`

- `node.routing.decision`
  - `node`, `action`, `tool_name` or `agent_name`, `task`

- `tool.call.*`
  - `tool_name`, `task`, `arg_keys`, `success`

- `memory.retrieve.*`
  - `query_hash`, `top_k`, `returned_count`, `scope_counts`, `policy_version`
- `memory.promotion.*` (Phase 2)
  - `promotion_request_id`, `source_chunk_id`, `target_chunk_id` (if created), `from_scope`, `to_scope`, `policy_version`

- `child.lifecycle.spawn`
  - `child_agent_id`, `task`, `requested_policy_version`, `effective_policy_version`

- `child.lifecycle.end/error`
  - `child_agent_id`, `success`, `result_size`; close is emitted separately after the child run reaches a terminal state

- `policy.*.update`
  - `old_version`, `new_version`, `changed_keys`

- `guardrail.decision.*`
  - `guardrail_type`, `decision`, `reason_code`

## 9) Error schema

When `status` is `error`/`timeout`/`denied`, `error` must be:

```json
{
  "code": "TOOL_TIMEOUT",
  "type": "TimeoutError",
  "message": "Tool execution exceeded timeout",
  "retryable": true,
  "stack": null
}
```

Rules:
- no secrets in `error.message`
- use stable `code` values
- `retryable` required for operational handling

## 10) Security and redaction rules

1. Never log raw secrets, credentials, tokens, API keys.
2. Do not log full memory chunk content by default.
3. For prompts/results, log hashes, sizes, and summaries rather than full payloads unless debug override is explicitly enabled.
4. If redaction is applied, set:
   - `security.contains_redacted = true`
   - `security.redaction_tags = [...]`
5. Guardrail/security denials must still be logged as structured events.

## 11) Sampling rules

- Lifecycle and error events are never sampled out.
- High-frequency progress/token events may be sampled.
- Sampling policy must be deterministic and environment-configurable.

## 12) Validation requirements

Implementation must provide:
- schema validation in tests for required events
- required-field checks in trace helper
- failing tests for missing correlation IDs on critical events
- tests that handled exceptions still emit `*.error`

## 13) Minimal examples

### 13.1 Child spawn

```json
{
  "ts": "2026-10-05T10:20:00.000Z",
  "event": "child.lifecycle.spawn",
  "status": "ok",
  "level": "info",
  "trace": {"trace_id": "trc_1", "span_id": "spn_2", "parent_span_id": "spn_1"},
  "ids": {
    "agent_id": "agt_parent",
    "parent_agent_id": "agt_parent",
    "child_agent_id": "agt_child",
    "execution_id": "exe_parent",
    "session_id": "sess_1",
    "owner_id": "usr_1",
    "tenant_id": "ten_1",
    "request_id": "req_1"
  },
  "runtime": {"service": "backend", "component": "subagent_node", "environment": "dev", "host": "local", "thread": "agent_1", "process": 1234, "version": "git:local"},
  "metrics": {"duration_ms": 4, "attempt": 1},
  "data": {
    "task": "analyze requirement doc",
    "requested_policy_version": 3,
    "effective_policy_version": 3
  },
  "error": null,
  "security": {"contains_redacted": false, "redaction_tags": []}
}
```

### 13.2 Tool error

```json
{
  "ts": "2026-10-05T10:22:10.111Z",
  "event": "tool.call.error",
  "status": "error",
  "level": "error",
  "trace": {"trace_id": "trc_1", "span_id": "spn_8", "parent_span_id": "spn_7"},
  "ids": {
    "agent_id": "agt_parent",
    "execution_id": "exe_parent",
    "session_id": "sess_1",
    "owner_id": "usr_1",
    "tenant_id": "ten_1",
    "parent_agent_id": null,
    "child_agent_id": null,
    "request_id": "req_1"
  },
  "runtime": {"service": "backend", "component": "toolnode", "environment": "dev", "host": "local", "thread": "agent_1", "process": 1234, "version": "git:local"},
  "metrics": {"duration_ms": 3000, "attempt": 1},
  "data": {"tool_name": "execute_bash", "task": "run tests", "arg_keys": ["command"]},
  "error": {
    "code": "TOOL_TIMEOUT",
    "type": "TimeoutError",
    "message": "Tool execution exceeded timeout",
    "retryable": true,
    "stack": null
  },
  "security": {"contains_redacted": false, "redaction_tags": []}
}
```

## 14) Rollout guidance

Recommended sequence:
1. Add centralized trace helper enforcing envelope + required fields.
2. Instrument run lifecycle + tool lifecycle first.
3. Add subagent + memory + policy + guardrail coverage.
4. Add API/session/checkpointer coverage.
5. Add tests for schema compliance and failure-path traces.

Done criteria:
- all minimum taxonomy events exist in code paths
- required IDs propagate across parent/child and thread/task boundaries
- critical flows reconstructible by querying `agent_id` + `execution_id`
