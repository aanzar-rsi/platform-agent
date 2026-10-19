# Logging Architecture for a Multi-User LangGraph Agent Platform

## 1. Purpose

This document proposes a logging and observability architecture for an agent platform with the following identity and execution model:

- A user logs in and receives a `session_id`.
- A user opens or accesses an agent represented by an `agent_id`.
- The user interacts with the agent through chat.
- Every new user message invokes a LangGraph workflow with a unique `execution_id`.
- One `agent_id` can have many execution IDs.
- The same `agent_id` can be accessed from different sessions.
- Every agent has an owner, which is either a `user_id` or a parent `agent_id`.
- An agent may invoke child agents.

The logging system should support:

- End-to-end execution tracing
- LangGraph node flow visualization
- LLM request and response telemetry
- Tool and retrieval calls
- Sub-agent relationships
- Errors, retries, and checkpoints
- Cost, token usage, and latency analysis
- Security and audit requirements

## 2. Main Recommendation

Do not use a physical directory per agent or per session as the primary logging architecture.

Instead, use:

- One root trace per `execution_id`
- Nested spans for LangGraph nodes, LLM calls, tools, retrieval, guardrails, checkpoints, and sub-agents
- Structured logs correlated through `trace_id` and `span_id`
- Searchable metadata including `tenant_id`, `user_id`, `session_id`, `agent_id`, `message_id`, and `execution_id`
- Centralized trace, log, metric, and audit storage
- Time-based and tenant-based partitioning for long-term storage

The directory or object-store layout should be treated as a storage optimization, not as the mechanism used to correlate activity.

## 3. Identity and Execution Model

```text
Tenant
└── User
    ├── Session 1
    ├── Session 2
    └── Owned agent
        ├── Message 1
        │   └── Execution attempt 1
        ├── Message 2
        │   ├── Execution attempt 1
        │   └── Execution attempt 2
        └── Child agent
```

### Identifier definitions

| Identifier | Meaning | Typical lifetime |
|---|---|---|
| `tenant_id` | Security and data-isolation boundary | Long-lived |
| `user_id` | Authenticated platform identity | Long-lived |
| `session_id` | Login, browser, or application session | Hours or days |
| `agent_id` | Persistent agent instance or conversation entity | Long-lived |
| `message_id` | One user message submitted to an agent | Permanent |
| `execution_id` | One attempt to process a message | Seconds or minutes |
| `trace_id` | Distributed tracing identifier for an execution | Execution lifetime |
| `span_id` | One operation inside a trace | Operation lifetime |
| `thread_id` | LangGraph checkpoint and state namespace | Conversation or workflow lifetime |

An important distinction is:

```text
message_id != execution_id
```

A single message may produce more than one execution because of retries, replays, failover, or manual reruns:

```text
message_id = msg-221
├── execution_id = exec-901, attempt 1, failed
└── execution_id = exec-902, attempt 2, succeeded
```

This preserves the history of failed attempts instead of overwriting them.

## 4. Trace Hierarchy

Use `execution_id` as the application-level run identifier. Create one root trace for every LangGraph invocation.

```text
Trace: execution exec-902
│
├── Span: request_validation
├── Span: load_agent_state
├── Span: langgraph_execution
│   │
│   ├── Span: node.router
│   │   └── Span: llm.chat
│   │
│   ├── Span: edge.router_to_retrieval
│   │
│   ├── Span: node.retrieval
│   │   ├── Span: embedding.create
│   │   └── Span: vector_store.query
│   │
│   ├── Span: node.answer_generator
│   │   └── Span: llm.chat
│   │
│   ├── Span: node.tool_executor
│   │   └── Span: tool.execute
│   │
│   └── Span: node.output_validation
│
├── Span: persist_checkpoint
└── Span: persist_response
```

This structure makes it possible to reconstruct the complete execution waterfall, including node sequence, routing, LLM calls, tools, persistence, latency, errors, and cost.

## 5. Root Trace Metadata

Attach searchable correlation metadata to the root execution trace.

```json
{
  "tenant_id": "tenant-acme",
  "user_id": "user-123",
  "session_id": "session-789",
  "agent_id": "agent-456",
  "message_id": "msg-221",
  "execution_id": "exec-902",

  "owner_type": "user",
  "owner_id": "user-123",

  "parent_agent_id": null,
  "root_agent_id": "agent-456",

  "langgraph_thread_id": "agent-456",
  "execution_attempt": 2,

  "environment": "production",
  "agent_version": "support-agent:2.4.1",
  "graph_version": "sha256:...",
  "prompt_version": "answer-generator:17",
  "model_provider": "azure-openai",

  "trace_id": "...",
  "request_started_at": "...",
  "request_completed_at": "...",
  "status": "success"
}
```

For an agent owned by another agent:

```json
{
  "agent_id": "agent-child-12",
  "owner_type": "agent",
  "owner_id": "agent-parent-4",
  "parent_agent_id": "agent-parent-4",
  "root_agent_id": "agent-root-1"
}
```

Do not encode ownership relationships in directory paths. Keep them in indexed metadata and in an agent relationship table.

## 6. Sub-Agent Execution

### 6.1 Preferred model: Same distributed trace

When a parent agent invokes a child agent synchronously, keep the child execution within the same distributed trace.

```text
Trace: exec-A-100
├── node.plan
├── invoke_agent: agent-B
│   ├── node.router
│   ├── llm.chat
│   └── tool.execute
└── node.synthesize
```

Add child-agent attributes to the invocation span:

```json
{
  "agent_id": "agent-B",
  "invoking_agent_id": "agent-A",
  "root_agent_id": "agent-A",
  "parent_execution_id": "exec-A-100",
  "agent_depth": 1
}
```

This produces one end-to-end trace waterfall.

### 6.2 Alternative model: Linked child trace

Create a separate child trace when the child agent:

- Executes asynchronously
- Is dispatched through a queue
- Outlives the parent request
- Has an independent retry lifecycle
- Runs in a separate service or trust boundary

Store the relationship explicitly:

```json
{
  "execution_id": "exec-B-201",
  "parent_execution_id": "exec-A-100",
  "parent_trace_id": "...",
  "invocation_id": "invocation-77"
}
```

Use span links when strict parent-child timing is not appropriate.

## 7. Operation-Level Telemetry

### 7.1 LangGraph node span

```json
{
  "event_type": "node_execution",
  "node_name": "answer_generator",
  "node_type": "llm_node",
  "node_sequence": 5,
  "previous_node": "retrieval",
  "selected_edge": "answer_generator_to_validation",
  "status": "success",
  "duration_ms": 842,
  "state_input_ref": "state://...",
  "state_output_ref": "state://..."
}
```

Store state references, hashes, or an approved state diff rather than automatically copying the complete graph state into telemetry.

### 7.2 LLM span

```json
{
  "event_type": "llm_call",
  "provider": "azure-openai",
  "model": "model-name",
  "operation": "chat",
  "temperature": 0.1,
  "prompt_version": "router:8",
  "input_tokens": 1250,
  "output_tokens": 180,
  "cached_input_tokens": 700,
  "finish_reason": "stop",
  "latency_ms": 620,
  "estimated_cost": 0.0042,
  "status": "success"
}
```

Recommended default fields:

- Prompt template ID and version
- Hash of the rendered prompt
- Model and provider
- Model configuration
- Input, output, and cached token counts
- Latency
- Finish reason
- Cost or cost-estimation inputs
- Redacted input and output when permitted
- Secure references to full content where necessary

Do not log private chain-of-thought or hidden model reasoning. Log observable inputs, structured decisions, outputs, validation results, and external actions.

### 7.3 Tool span

```json
{
  "event_type": "tool_call",
  "tool_name": "search_customer_records",
  "tool_version": "3.2",
  "tool_call_id": "call-998",
  "input_schema_version": "2",
  "input_redacted": {
    "customer_id": "hash:..."
  },
  "status": "error",
  "error_category": "authorization",
  "retryable": false,
  "duration_ms": 92
}
```

Also capture:

- Tool input and output references
- Tool policy decision
- Approval requirement and approval result
- Retry count
- External request ID
- Error code and category
- Whether the operation caused a side effect

### 7.4 Routing or graph-transition event

```json
{
  "event_type": "graph_transition",
  "from_node": "router",
  "to_node": "retrieval",
  "route_name": "requires_context",
  "decision_source": "structured_llm_output",
  "decision_value": "RETRIEVE"
}
```

Log the selected route and structured decision. Do not log hidden reasoning used to reach the decision.

### 7.5 Retrieval span

```json
{
  "event_type": "retrieval",
  "store_type": "vector_store",
  "collection": "tenant-knowledge",
  "query_hash": "sha256:...",
  "top_k": 10,
  "result_count": 7,
  "filters": {
    "tenant_id": "tenant-acme"
  },
  "duration_ms": 115,
  "status": "success"
}
```

Avoid placing sensitive retrieved document content directly in searchable telemetry. Prefer document identifiers, access-safe summaries, hashes, and secured content references.

## 8. Separate Traces, Logs, Metrics, and Audit Events

Do not place all observability data into one undifferentiated log stream.

### 8.1 Traces

Traces answer:

- What happened during this execution?
- Which node ran next?
- Which LLMs and tools were called?
- Where was time spent?
- Where did the execution fail?

Primary correlation keys:

```text
trace_id
execution_id
```

### 8.2 Application logs

Application logs provide diagnostic detail within a trace or span.

```json
{
  "timestamp": "...",
  "severity": "ERROR",
  "message": "Tool returned authorization failure",
  "trace_id": "...",
  "span_id": "...",
  "execution_id": "exec-902",
  "agent_id": "agent-456",
  "error_code": "TOOL_AUTH_403"
}
```

Every application log generated during an execution should include:

- `tenant_id`
- `agent_id`
- `execution_id`
- `trace_id`
- `span_id`
- `environment`
- `service_name`

### 8.3 Metrics

Metrics support aggregation, alerting, and dashboards.

Example metrics:

```text
agent_execution_count
agent_execution_duration
node_execution_count
node_duration
llm_request_count
llm_token_count
llm_cost
llm_error_count
tool_call_count
tool_error_count
checkpoint_failure_count
active_executions
```

Avoid high-cardinality identifiers such as `user_id`, `session_id`, `execution_id`, `trace_id`, and usually `agent_id` in metric labels. Keep those identifiers in traces and logs.

Suitable metric dimensions include:

- Environment
- Service
- Agent type
- Graph version
- Model provider
- Model name
- Node name
- Tool name
- Status
- Error category

### 8.4 Audit events

Audit events support security, compliance, and accountability.

Examples:

```text
agent_created
agent_owner_changed
agent_shared
agent_accessed
execution_started
privileged_tool_invoked
human_approval_requested
human_approval_given
agent_deleted
trace_viewed
prompt_content_accessed
```

Audit logs should be immutable or append-only and protected with stricter access controls than ordinary diagnostics.

## 9. Storage Architecture

```text
Agent API / LangGraph Runtime
        │
        ├── OpenTelemetry traces
        ├── Structured application logs
        ├── Metrics
        └── Audit events
                │
                ▼
       OpenTelemetry Collector
        ├── Agent/LLM trace backend
        ├── Distributed trace backend
        ├── Log backend
        ├── Metrics backend
        ├── Audit store
        └── Long-term object storage
```

A possible implementation could use:

- Langfuse or an equivalent platform for LLM and agent traces
- OpenTelemetry for common instrumentation and context propagation
- Grafana Tempo or another trace backend for distributed traces
- Grafana Loki or another structured log backend
- Prometheus or Mimir for metrics
- A database or immutable event store for audit records
- Object storage for approved long-term telemetry archives

The product selection is secondary to preserving standardized correlation fields and trace context.

## 10. Object-Store Partitioning

If telemetry must be archived as files, partition by tenant and time.

```text
telemetry/
  environment=production/
    tenant_id=tenant-acme/
      year=2026/
        month=10/
          day=06/
            hour=17/
              part-0001.parquet
```

Avoid layouts such as:

```text
logs/
  agent-1/
  agent-2/
  agent-3/
```

Tenant and time partitioning provides:

- Easier retention deletion
- Better tenant boundary enforcement
- Efficient time-range scanning
- Fewer small directories and files
- Support for concurrent executions
- Independent indexing by agent, session, user, message, and execution

## 11. Suggested Relational Model

### `agents`

```text
agent_id
 tenant_id
owner_type
owner_id
parent_agent_id
root_agent_id
agent_type
agent_version
created_at
```

### `messages`

```text
message_id
tenant_id
agent_id
user_id
session_id
created_at
content_reference
```

### `executions`

```text
execution_id
tenant_id
agent_id
message_id
user_id
session_id
parent_execution_id
trace_id
attempt_number
status
started_at
completed_at
error_category
agent_version
graph_version
```

### `execution_spans`

```text
span_id
trace_id
parent_span_id
execution_id
span_type
operation_name
started_at
completed_at
status
attributes_json
```

A dedicated OpenTelemetry-compatible trace backend can replace the application-managed `execution_spans` table.

### `audit_events`

```text
audit_event_id
tenant_id
actor_type
actor_id
action
resource_type
resource_id
trace_id
timestamp
details_json
```

## 12. Correlation Rules

1. Generate `execution_id` in the platform before invoking LangGraph.
2. Create one root trace for each execution attempt.
3. Store the telemetry-generated `trace_id` against the execution record.
4. Use `message_id` to identify the logical input across retries.
5. Use `thread_id` for resumable LangGraph state and checkpoints.
6. Treat `session_id` as request context, not as the primary trace grouping.
7. Use `agent_id` to group historical executions, not as a trace identifier.
8. Propagate trace context when invoking tools, services, and sub-agents.
9. Include `trace_id`, `span_id`, `execution_id`, and `agent_id` in application logs.
10. Apply tenant authorization before allowing access to traces or logged content.
11. Configure prompt, response, tool payload, and retrieved-document logging independently.
12. Preserve failed and retried execution attempts rather than overwriting them.

## 13. Privacy and Security Controls

The telemetry system may contain user messages, prompts, generated responses, retrieved documents, and tool payloads. Apply the following controls:

- Redact secrets, credentials, tokens, and personal data before export.
- Maintain allowlists for fields that may be logged.
- Store raw content separately from general-purpose indexed telemetry.
- Encrypt telemetry in transit and at rest.
- Enforce tenant-aware authorization on every query.
- Restrict access to prompts and model outputs more tightly than operational metadata.
- Use configurable retention periods by telemetry class.
- Record access to sensitive trace content in the audit log.
- Allow content logging to be disabled while retaining operational failures and usage totals.
- Do not collect private model reasoning or hidden chain-of-thought.

## 14. Final Recommended Hierarchy

```text
Tenant
└── User or owning agent
    └── Agent
        └── Message
            └── Execution attempt
                └── Trace
                    ├── Node spans
                    ├── LLM spans
                    ├── Tool spans
                    ├── Retrieval spans
                    ├── Guardrail spans
                    ├── Checkpoint spans
                    └── Sub-agent spans or linked traces
```

## 15. Final Decision

- Do not organize primary logs per session. The same agent can be accessed from multiple sessions, and a session can access multiple agents.
- Do not organize primary logs as a directory per agent. An agent can accumulate concurrent, retried, and nested executions.
- Create one root trace per `execution_id`.
- Associate the trace with `tenant_id`, `user_id`, `session_id`, `agent_id`, `message_id`, ownership metadata, and parent execution details.
- Use nested spans for LangGraph nodes, LLM calls, tools, retrieval, checkpoints, and synchronous sub-agents.
- Use linked traces for asynchronous or independently managed child-agent work.
- Partition archived telemetry by tenant and time.
- Use indexed metadata and distributed trace context for correlation instead of filesystem paths.
