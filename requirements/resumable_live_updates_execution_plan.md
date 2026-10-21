# Resumable Live Updates — Execution Plan

## Goal

Replace the current process-local WebSocket packet queue with a durable PostgreSQL execution event stream so frontend reload/reconnect can fully reconstruct in-flight agent state.

## Scope

1. Remove legacy queue remnants (`ChatPacketQueue`, ACK deletion flow, queue config knobs, single-socket backlog semantics).
2. Persist every agent execution event (including `llm.token`) into DB with per-execution sequence ordering.
3. Replay DB events on WS attach (`after_seq`) and continue live polling from DB.
4. Keep multiple WS viewers independent (no shared destructive consumption).
5. Extend chat snapshot payload with latest execution metadata.
6. Update frontend WS client to compatible replay semantics (no `session.ready` cursor jump, no ACK loop).
7. Ensure reload during active run rebuilds UI state via replay.
8. Add retention cleanup for completed execution events (7 days).

## Backend implementation

- Schema:
  - `agent_executions`: add `latest_event_seq`, `current_state`.
  - Add `agent_execution_events` table with `UNIQUE(execution_id, sequence_number)`.
- Repository:
  - Add `ExecutionEventRepository` with append/replay/snapshot/cleanup methods.
  - Register repository in dependency container.
- Runtime:
  - Add execution-bound event writer (`enqueue(type, payload)`).
  - Wire `AgentRuntime.run_turn(...)` to writer instead of in-memory queue.
- WS manager:
  - Replace single-socket queue flusher with per-connection DB replay loops.
  - Support `execution_id` + `after_seq` query params.
  - Remove ACK behavior.
- API:
  - Include `latest_execution` in `GET /v1/agents/{agent_id}` payload.
- Lifespan:
  - Add periodic event retention cleanup task (7 days, non-running executions only).

## Frontend implementation

- WS client:
  - Stop ACK loop.
  - Add `execution_id` query support.
  - Do not advance `lastSeq` from `session.ready`.
  - Deduplicate with strict `seq <= lastSeq` drop.
  - Carry `execution_id` on envelopes.
- Chat view:
  - Use `latest_execution` snapshot metadata for WS attach options.
  - Ensure active-run reload starts replay from seq 0 for execution reconstruction.

## Tests

- Update schema test for new table.
- Replace queue-coupled runtime test with writer-based event sink test.
- Update endpoint WS assertions for replay semantics without ACK.
- Add frontend websocket client unit tests for:
  - no session-ready cursor jump,
  - duplicate suppression,
  - execution-aware reconnect params.

## Rollout notes

- This is a behavior change: events become durable and replayable.
- Legacy queue code will be removed, not layered.
