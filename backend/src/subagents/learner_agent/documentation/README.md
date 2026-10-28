# Governed Learner Memory

The learner is a background LangGraph workflow:

```text
load_session -> extract_chunks -> persist
```

It learns bounded, advisory memories from conversation, Armory calls, child-agent runs, corrections, and useful execution outcomes. It uses the shared PostgreSQL-authoritative KB with Chroma as a disposable search index; the legacy file store exists only for migration.

## Chunk types

Every new memory starts in `USER` scope and uses one of seven types:

- `resource`
- `user_preference`
- `user_details`
- `tenant_details`
- `workflow`
- `troubleshooting`
- `anti_pattern`

Resource kind, decision stage, workflow kind, and similar distinctions are normalized metadata rather than extra chunk types.

## Extraction and governance

`load_session.py` computes effective per-type write policy and approval state, retains bounded conversation/execution evidence, and builds entry, transition, or recovery snapshots. `extract_chunks.py` makes one LLM call through `src/models/llm_client.py`, then deterministically rejects unknown types, invalid metadata, secrets, protected-trait profiling, invented resources, and invalid weights.

Confirmation requests are keyed by agent, checkpoint, and chunk type. Approved types can proceed while other types remain pending. Pending confirmation leaves stay retryable.

## Persistence

Each candidate has a deterministic evidence ID for branch-rerun idempotence and a semantic key for consolidation across sessions. Equivalent content reinforces weight. Improved or corrected content appends a version. A direct unresolved negation is stored separately rather than silently replacing the prior memory. All writes are reauthorized immediately before persistence.

## Retrieval

Before both the fast classifier and planner calls, `retrieve.py` derives the current decision stage and searches bounded lanes:

- entry: preferences/details, workflows, resources, anti-patterns;
- transition: preferences/details, workflows, resources, anti-patterns;
- recovery: preferences, troubleshooting, anti-patterns, workflows, resources.

Results are deduplicated, stage-adjusted, and resource memories are removed when the named resource is not currently available. PostgreSQL revalidates active version, owner/tenant, expiry, scope, and type policy after Chroma candidate retrieval.

Prompt memory is explicitly untrusted. It cannot grant a resource, permission, scope, or policy change, and current user instructions and system policy override it.

## Publication lifecycle

Promotion creates a separate TENANT or AGENT target and preserves the USER source. Request and review both revalidate effective target/type policy. Activation requires an admin publisher, target `publish` permission, chunk-level `promote` permission, and `allow_admin_promotion`. AGENT content is rejected when deterministic checks find private identifiers, contact/network details, credentials, or tenant-private configuration. Rejection, cancellation, validation failure, activation, revocation, demotion, expiry, and revalidation remain audited; failed activation reaches `PROMOTION_FAILED` without modifying the source.

Published versions can carry `TRANSIENT`, `STANDARD`, `LONG_TERM`, or `LEGAL_HOLD` retention classes and optional timezone-aware expiry. Expired, revoked, and superseded versions fail PostgreSQL visibility checks even if Chroma deletion is delayed.

## Operations

- `EXPERIENCE_ENABLED` enables extraction/retrieval.
- `EXPERIENCE_IDLE_SECONDS` and `EXPERIENCE_WATCHER_POLL_SECONDS` control scheduling.
- `EXPERIENCE_TOP_K` bounds prompt retrieval.
- Extraction and retrieval soft-fail; retrieval waits at most four seconds in the live path.
- Use memory audit/trace records to diagnose authorization, writes, reinforcement, promotion, revocation, and retrieval.

The learner-specific `graphify-out/` is generated only from learner source, prompts, and this documentation. It must never include runtime memories, logs, credentials, or user data.
