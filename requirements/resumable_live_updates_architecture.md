# Resumable Live Updates for Long-Running Chatbot Workflows

## Overview

A chatbot agent may execute a multi-step workflow that runs for several minutes. During execution, it sends live progress updates to the frontend through a WebSocket connection.

However, WebSocket connections are temporary. They may be interrupted when:

- The network connection resets.
- The user refreshes the page.
- The user navigates to another page and returns.
- The browser tab is suspended.
- The frontend application restarts.
- The WebSocket gateway restarts.
- The same execution is opened in another browser tab or device.

A simple packet queue is not sufficient to solve this problem. A queue may retain packets generated while the user is disconnected, but packets delivered before the disconnection may already have been removed.

The solution is to separate:

1. **Agent execution state**
2. **Durable execution event history**
3. **Live WebSocket delivery**

The WebSocket should be treated only as a transport mechanism, not as the source of truth.

---

## Core Principle

> The agent execution must continue independently of the browser and its WebSocket connection.

Every execution should have an `execution_id`. All state changes and progress updates should be associated with that execution.

```text
User
 └── Session
      └── Agent Conversation
           ├── Execution E123
           │    ├── Event 1
           │    ├── Event 2
           │    ├── Event 3
           │    └── ...
           └── Execution E124
                ├── Event 1
                └── ...
```

The `execution_id` becomes the recovery boundary. A client reconnects to an execution, retrieves its current state, and resumes receiving events from the point it previously reached.

---

## Recommended Architecture

```text
                    ┌──────────────────────────┐
                    │     Agent Execution      │
                    │   execution_id = E123    │
                    └────────────┬─────────────┘
                                 │
                          produces events
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Durable Event Stream   │
                    │ Redis Streams / Kafka    │
                    │                          │
                    │ 101 thinking...          │
                    │ 102 calling tool         │
                    │ 103 tool completed       │
                    │ 104 generating answer    │
                    └───────────┬──────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
             ┌──────────────┐       ┌────────────────┐
             │ WebSocket    │       │ Persistent DB  │
             │ Gateway      │       │ execution/event│
             └──────┬───────┘       │ state/history  │
                    │               └────────────────┘
                    ▼
                 Browser
```

The durable event stream or database is the source of truth. The WebSocket gateway reads events from that source and forwards them to connected clients.

---

## Example: Disconnect at 10 Seconds and Reconnect at 20 Seconds

Assume execution `E123` produces the following ordered events:

```text
seq=1    Agent started
seq=2    Understanding request
seq=3    Searching documents
seq=4    Found 17 documents
seq=5    Processing document 1
...
seq=15   Processing document 8
seq=16   Summarizing results
seq=17   Generating response
seq=18   Completed
```

The frontend receives events `1` through `8`. At 10 seconds, the WebSocket disconnects.

The agent execution continues independently and writes additional events to durable storage:

```text
9
10
11
12
13
14
```

When the browser reconnects at 20 seconds, it sends a resume request:

```json
{
  "type": "resume",
  "execution_id": "E123",
  "last_event_id": 8
}
```

The backend retrieves all events for `E123` where the sequence number is greater than `8` and sends:

```text
9
10
11
12
13
14
```

After the replay is complete, the connection switches to live delivery:

```text
15
16
17
18
```

This prevents event loss without making the WebSocket queue responsible for long-term recovery.

---

## Use Both Snapshots and Event History

A robust implementation should maintain both an execution snapshot and an execution event log.

### Execution Snapshot

The snapshot represents the latest known state of the execution.

```json
{
  "execution_id": "E123",
  "status": "running",
  "current_step": "document_processing",
  "progress": {
    "completed": 8,
    "total": 17
  },
  "message": "Processing document 8",
  "latest_event_id": 143
}
```

The snapshot allows the frontend to render the current state immediately without replaying the complete event history.

### Execution Event Log

The event log records how the execution reached its current state.

```text
138 document_started
139 document_completed
140 document_started
141 document_completed
142 document_started
143 progress_updated
```

The snapshot supports fast loading. The event log supports reliable reconnection, replay, debugging, auditing, and observability.

This is a **snapshot plus event stream** design rather than a requirement to implement pure event sourcing.

---

## Page Refresh and Full Frontend Restart

A refresh destroys the frontend's in-memory state. The browser may no longer know which event was last rendered.

The frontend should therefore be able to retrieve the execution directly:

```http
GET /executions/E123
```

Example response:

```json
{
  "execution_id": "E123",
  "status": "running",
  "latest_event_id": 14,
  "state": {
    "phase": "document_processing",
    "message": "Processing documents",
    "documents_processed": 8,
    "documents_total": 17
  }
}
```

The frontend recovery flow becomes:

```text
Page opens
    │
    ▼
GET execution E123
    │
    ├── completed → render persisted final result
    │
    └── running
          │
          ▼
    render current snapshot
          │
          ▼
    connect WebSocket
          │
          ▼
    subscribe(E123, after_event=14)
```

Optionally, the frontend can also persist its most recently rendered sequence number in browser storage. However, backend snapshot retrieval must remain available because browser-local state may be missing, stale, or cleared.

---

## Preventing the Snapshot-to-WebSocket Race Condition

A subtle race condition occurs with this sequence:

```text
1. Frontend retrieves the current snapshot.
2. Snapshot reports latest_event_id = 100.
3. Event 101 is generated.
4. Frontend connects to the WebSocket.
```

If the WebSocket only begins forwarding new events after connection, event `101` may be missed.

To prevent this, the subscription request must include the last sequence represented by the snapshot:

```json
{
  "type": "subscribe",
  "execution_id": "E123",
  "after_sequence": 100
}
```

The server must:

1. Replay all persisted events where `sequence > 100`.
2. Follow the same execution's live event stream.
3. Ensure there is no gap between replay and live consumption.

```text
Durable event history
────────────────────────────────────────────►

             100 101 102 103 104 105
              ▲               ▲
              │               │
         snapshot read     WS connected

Replay: 101 → 104
Then continue live from 105
```

The replay-to-live transition should be implemented so that events cannot be inserted into an unobserved gap.

---

## Suggested Data Model

### `agent_execution`

```text
agent_execution
────────────────────────────────
execution_id
agent_id
user_id
session_id
status
started_at
completed_at
latest_event_seq
current_state
final_result
error_details
```

`current_state` may be stored as structured JSON if the workflow state differs across agent types.

### `execution_event`

```text
execution_event
────────────────────────────────
execution_id
sequence_number
event_type
payload
created_at
```

Example event:

```json
{
  "execution_id": "E123",
  "sequence_number": 143,
  "event_type": "tool_completed",
  "payload": {
    "tool": "document_search",
    "message": "Search completed"
  }
}
```

The database should enforce ordering uniqueness:

```text
UNIQUE(execution_id, sequence_number)
```

This creates a deterministic event timeline for every execution.

---

## WebSocket Protocol

The WebSocket protocol should explicitly support subscription and resumption.

### Subscribe or Resume

```json
{
  "type": "subscribe",
  "execution_id": "E123",
  "after_sequence": 143
}
```

### Event Delivery

```json
{
  "type": "event",
  "execution_id": "E123",
  "sequence": 144,
  "event_type": "step_started",
  "data": {
    "step": "generate_summary"
  }
}
```

### Progress Event

```json
{
  "type": "event",
  "execution_id": "E123",
  "sequence": 145,
  "event_type": "progress",
  "data": {
    "message": "Generating summary"
  }
}
```

### Completion Event

```json
{
  "type": "event",
  "execution_id": "E123",
  "sequence": 146,
  "event_type": "completed",
  "data": {}
}
```

### Optional Acknowledgement

The client may acknowledge the latest event it has successfully applied:

```json
{
  "type": "ack",
  "execution_id": "E123",
  "sequence": 145
}
```

Acknowledgements can be useful when the backend tracks delivery state per user, device, or connection. They are not a replacement for durable event storage.

---

## Idempotency and Duplicate Delivery

A resumable stream should normally provide **at-least-once delivery**, which means the frontend may occasionally receive the same event more than once.

The frontend should track the highest applied sequence number per execution:

```text
if event.sequence <= last_applied_sequence:
    ignore event
else:
    apply event
    last_applied_sequence = event.sequence
```

All events should be safe to process more than once, or the client should deduplicate them using:

```text
(execution_id, sequence_number)
```

A small number of duplicates is generally easier to handle reliably than silent event loss.

---

## Queue Versus Durable Stream

A WebSocket packet queue and a durable execution stream serve different purposes.

### Packet Queue

A packet queue is useful for:

- Buffering short bursts
- Handling temporary network backpressure
- Decoupling WebSocket writes from event production
- Managing per-connection outbound delivery

It is not sufficient for:

- Page refresh recovery
- Long disconnections
- Browser-local state loss
- Server restart recovery
- Reconstructing execution state
- Multiple clients viewing the same execution

### Durable Event Stream

A durable stream or event table is used for:

- Ordered event history
- Replay after reconnection
- Execution recovery
- Observability
- Auditing
- Multiple consumers

The preferred model is:

```text
Agent → Durable Stream / Database → WebSocket Gateway → Browser
```

not:

```text
Agent → Temporary WebSocket Queue → Browser
```

---

## Technology Options

### Redis Streams

Redis Streams is a practical option for resumable execution events because entries are stored with ordered stream IDs and can be read from a known position.

A possible architecture is:

```text
                        ┌───────────────┐
                        │ Agent Worker  │
                        └───────┬───────┘
                                │
                          execution events
                                │
                                ▼
                        ┌───────────────┐
                        │ Redis Streams │
                        └───────┬───────┘
                                │
                 ┌──────────────┴──────────────┐
                 │                             │
                 ▼                             ▼
          WebSocket Gateway              State Writer
                 │                             │
                 ▼                             ▼
             Browser                     PostgreSQL
                                      execution state
```

Redis Pub/Sub alone is not sufficient because messages published while a subscriber is disconnected are not available to that disconnected subscriber later.

### PostgreSQL

For a simpler initial deployment, the application can persist `execution_event` records and execution snapshots directly in PostgreSQL.

PostgreSQL can be combined with:

- Polling for missed events
- `LISTEN/NOTIFY` for live notification hints
- A WebSocket gateway that queries durable events after receiving a notification

Notifications should trigger retrieval, while the event table remains the durable source of truth.

### Kafka, Azure Event Hubs, or NATS JetStream

These technologies may be appropriate when the platform requires distributed event processing, multiple independent consumers, high throughput, retention policies, or cross-service integration.

They introduce more operational complexity and may be unnecessary if the immediate requirement is only resumable browser updates for a modest number of agent executions.

---

## UI Events Versus Semantic Execution Events

Avoid persisting presentation-specific events such as:

```json
{
  "event_type": "display_spinner"
}
```

Instead, persist semantic execution events:

```json
{
  "event_type": "tool_started",
  "tool": "document_search"
}
```

```json
{
  "event_type": "tool_completed",
  "tool": "document_search"
}
```

```json
{
  "event_type": "agent_progress",
  "message": "Analysing retrieved documents"
}
```

The frontend decides how each semantic event should be rendered:

```text
tool_started   → show spinner
tool_completed → show checkmark
```

This keeps the execution protocol independent of a specific frontend and allows the same events to be consumed by observability, audit, notification, and analytics systems.

---

## Handling Long Absences

If the user returns after the execution has completed, replaying every intermediate event is usually unnecessary.

The frontend can retrieve:

```json
{
  "execution_id": "E123",
  "status": "completed",
  "latest_event_id": 928,
  "final_result": {}
}
```

It can then render the persisted final result immediately.

Replay should be used when:

- The execution is still running.
- The UI must display missed intermediate activity.
- The user opens an execution history or diagnostic view.

Otherwise, the latest snapshot or final result should be preferred.

---

## Event Retention and Compaction

Event history does not necessarily need to be retained forever.

A retention strategy can include:

1. Retaining all events while the execution is running.
2. Retaining events for a limited recovery and diagnostic period after completion.
3. Persisting the final result and final execution snapshot for longer-term access.
4. Removing high-volume transient progress events after the retention period.
5. Retaining important lifecycle, tool, error, and audit events according to platform requirements.

Snapshots allow older low-value progress events to be compacted without losing the final state of the execution.

---

## Security and Authorization

Reconnect and replay APIs must validate that the requesting user is authorized to access the execution.

A client must not gain access merely by knowing an `execution_id`.

The authorization check should consider the platform's ownership model, such as:

```text
user_id → session_id → agent_id → execution_id
```

The backend should validate access for:

- Snapshot retrieval
- Event replay
- WebSocket subscription
- Final result retrieval
- Cancellation or other execution controls

Authorization must be evaluated on every new connection because a WebSocket connection may outlive a browser navigation or authentication refresh.

---

## Failure Scenarios Covered

This design handles:

- Temporary network disconnects
- Browser refreshes
- Navigation away from and back to the execution page
- Browser crashes or restarts
- WebSocket gateway restarts
- Agent worker and WebSocket gateway separation
- Multiple tabs viewing the same execution
- Delayed reconnection after execution completion
- Duplicate event delivery
- Gaps between snapshot retrieval and WebSocket subscription

Additional mechanisms such as worker checkpoints are required if the agent execution itself must resume after an agent worker crash. WebSocket recovery and workflow recovery are related but separate concerns.

---

## Recommended Recovery Flow

```text
1. Start the agent workflow and create an execution_id.
2. Persist every meaningful state transition as an ordered event.
3. Update the current execution snapshot.
4. Publish events to connected WebSocket clients.
5. Allow the frontend connection to disappear without affecting execution.
6. When the frontend returns, retrieve the latest execution snapshot.
7. Render the snapshot immediately.
8. Subscribe to the execution using the snapshot's latest sequence number.
9. Replay all events generated after that sequence.
10. Continue with live event delivery.
11. Deduplicate events using execution_id and sequence number.
12. Render the persisted final result when the execution is complete.
```

---

## Final Design Principle

The WebSocket is a disposable connection and a live projection of the execution. It is not the execution itself and should not be the only location where execution updates exist.

The preferred design provides:

- **Durable execution**
- **Persisted snapshots**
- **Resumable event history**
- **Ordered, idempotent events**
- **Replay followed by live delivery**
- **Disposable WebSocket connections**

When the client reconnects, it should reconstruct the latest state from the snapshot, request events after the last known sequence, replay the gap, and then continue receiving live updates.
