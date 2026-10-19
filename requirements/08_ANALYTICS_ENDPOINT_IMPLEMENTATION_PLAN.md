# Analytics Endpoints Implementation Plan

## Scope and Endpoints

- Keep canonical agent analytics route as `GET /v1/agents/{agent_id}/analytics`.
- Keep global analytics route as `GET /v1/analytics`.
- Add optional query params on both: `from` and `to` (ISO-8601 with timezone).
- Defaults to all-time when no window is provided.

## Response Contract

Both endpoints return the same analytics structure:

- `llm`: calls, token breakdown, cost, per-model split.
- `agent.messages`: role counts (human, ai, system, tool, other).
- `agent.context`: latest context snapshot and aggregate context metrics.
- `agent.planner`: invocations, plans, steps, failures, overhead.
- `agent.armory`: configured resource counts, invocation/failure buckets.
- `agent.memory`: extraction attempts/failures/chunks and memory operation buckets.
- `agent.runtime`: run counts and runtime split.

`GET /v1/analytics` additionally includes `agents` summary (`total`, `active`, `deleted`, `with_runs`).

## Data Sources

- `llm_calls`: token, cost, model, latency, status.
- `messages`: message-role counts.
- `agent_executions`: runtime totals and run outcomes.
- `agent_cores.policy`: configured armory resources.
- `memory_extraction_requests`: extraction volume and failures.

## Instrumentation and Durability

- Add durable `analytics_events` table for analytics-domain events (`event_type`, `owner_id`, `agent_id`, `payload`).
- Keep existing append API in `AnalyticsRepository` and switch it to DB-backed writes.
- No historical backfill; richer telemetry is available for new runs after rollout.

## LLM Token and Cost Rules

- Normalize token classes from `llm_calls.usage`:
  - input, output, cached_input, cache_creation, reasoning, audio_input, audio_output, other, total.
- Cost precedence:
  1. provider-reported `cost_usd`
  2. estimated cost from LiteLLM-like per-model rates
- Return both actual and estimated totals plus model-level split.

## Validation and Ownership

- Validate `from`/`to` values in service layer.
- Require timezone-aware timestamps.
- Reject invalid ranges (`from > to`) with HTTP 422.
- Preserve ownership scoping:
  - non-admin users are scoped to their own `owner_id`
  - admins can query global aggregates.

## Frontend Migration

- Expand `AnalyticsSummary` type to reflect new schema.
- Update usage panel to consume real analytics metrics (tokens, cost, messages, failures, runs).
- Keep compatibility fields (`by_type`, `total_events`) during transition to avoid breakage.

## Test Plan

- Add tests for analytics time-window validation and error cases.
- Update analytics repository test to assert new rich payload shape.
- Keep route contract tests for `/v1/analytics` and `/v1/agents/{agent_id}/analytics`.
- Verify focused suites and frontend build.

## Delivery Notes

- Ship in one pass with compatibility fields retained.
- Follow-up can tighten planner/context/armory/memory runtime splits as deeper telemetry is added.
