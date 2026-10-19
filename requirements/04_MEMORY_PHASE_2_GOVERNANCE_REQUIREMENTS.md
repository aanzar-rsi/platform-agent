# Memory Requirements - Phase 2 (Governance and Promotion)

Status: future phase after Phase 1 delivery.

Depends on:
- `requirements/03_MEMORY_PHASE_1_REQUIREMENTS.md`

## 1) Purpose

Define governance-heavy memory capabilities that should be implemented after the base memory path is stable:
- promotion workflows
- admin approval and policy gates
- advanced sanitization/generalization
- revocation/demotion lifecycle
- stronger audit and compliance controls

## 2) Scope

### In scope
- Promotion request/review/activation lifecycle
- Admin approval requirements
- Generalization and sanitization before broad publication
- Idempotent promotion operations
- Revocation and demotion behavior
- Conflict handling and policy precedence
- Retention and revalidation controls

### Out of scope
- Re-defining Phase 1 schema basics
- Replacing AgentCore contracts

## 3) Promotion as controlled publication

Promotion is publication into a broader trust domain.

Rules:
- never direct autonomous publish to broader scope
- create a new target-scope chunk with its first version; keep the source chunk/version and restricted provenance link
- keep operation idempotent and auditable

Supported transitions:
- `USER -> TENANT`
- `USER -> AGENT`
- `TENANT -> AGENT`

## 4) Admin and policy gating

Promotion activation to broader scopes must require:
1. deterministic policy checks
2. sensitivity checks
3. admin approval when configured/required

AGENT/global publication requires an authorized publisher and deterministic policy gates; no learner or ordinary user write is sufficient. TENANT publication requires a trusted tenant ID in effective policy and an authorized publisher. Approval requirements must be specified by policy for each target scope.

Learner/agent systems may recommend promotion but cannot finalize activation alone.

## 5) Promotion workflow states

Recommended state machine:

```text
SOURCE_ACTIVE
  -> PROMOTION_PENDING
  -> VALIDATION_PENDING
  -> APPROVAL_PENDING (if required)
  -> TARGET_ACTIVE (new chunk, linked to source)

failure terminals:
  PROMOTION_REJECTED | PROMOTION_FAILED | PROMOTION_CANCELLED
```

## 6) Transaction and idempotency requirements

Promotion transaction must:
1. load source active version
2. revalidate authorization and ownership
3. re-check source freshness/supersession
4. run policy + sensitivity checks
5. apply sanitization/generalization if needed
6. enforce approval policy
7. create target-scope chunk and first active version
8. link provenance (`promoted_from_version_id`)
9. keep the original source active for its owner unless an explicit, separately authorized policy decision supersedes it
10. write append-only audit event

Retrying the same idempotency key must not create duplicate active targets. Target creation and audit/outbox write must be atomic in PostgreSQL. Until Chroma indexes the target, it is not searchable; if indexing fails, retry/reconcile by target version ID and do not report a partial search result. PostgreSQL revalidation prevents stale indexed records from leaking after revocation.

## 7) Generalization and sanitization

Before publishing to AGENT scope, remove or generalize tenant/private details unless explicit approved policy allows retention.

Check at least for:
- names
- customer identifiers
- emails
- URLs/hosts/IPs
- credentials/tokens
- tenant-private configurations
- confidential/regulated data

Generalized output should preserve useful operational guidance while removing private specifics.

## 8) Conflict handling

When chunks conflict, use deterministic precedence (recommended):
1. explicit policy priority
2. scope applicability
3. effective date/version
4. evidence quality
5. recency
6. human-review status

Do not silently merge contradictory memories as one fact.

## 9) Revocation and demotion

Must support:
- revoking active TENANT/AGENT versions
- removing revoked versions from normal retrieval immediately
- retaining governance/audit history
- controlled demotion flows when policy requires

## 10) Retention and freshness

Add managed lifecycle controls:
- optional expiry per version
- revalidation timestamps
- stale-memory handling
- retention classes for archival/deletion policies

Expired/revoked/superseded versions must not enter normal retrieval. Enforce the authoritative revocation check after Chroma search even if index removal lags; evict index records and caches promptly.

## 11) Trace and audit requirements

All governance actions must emit trace events via `requirements/02_TRACE_SCHEMA.md`.

Minimum additional events:
- `memory.promotion.requested`
- `memory.promotion.validated`
- `memory.promotion.approved`
- `memory.promotion.rejected`
- `memory.promotion.activated`
- `memory.promotion.failed`
- `memory.revoke`
- `memory.demote`

These are canonical names in `requirements/02_TRACE_SCHEMA.md`.

Audit log must remain append-only and access-controlled.

## 12) Implementation checklist

- [ ] Implement promotion request entity + idempotency handling.
- [ ] Implement validation + approval gates.
- [ ] Implement linked target-chunk creation and optional, explicitly authorized source supersession.
- [ ] Implement sanitization/generalization checks for broad scopes.
- [ ] Implement revocation/demotion paths.
- [ ] Implement deterministic conflict resolution policy.
- [ ] Implement governance trace + audit coverage.

## 13) Acceptance criteria

1. No broader-scope promotion is activated without required policy/admin gates.
2. Promotion retries are idempotent and do not create duplicate active targets.
3. Failed promotion does not destroy source active memory; successful promotion preserves it by default.
4. AGENT-scope publication includes sanitization/generalization checks.
5. Revoked memories are excluded from normal retrieval immediately.
6. Governance flows are fully traceable and auditable.
