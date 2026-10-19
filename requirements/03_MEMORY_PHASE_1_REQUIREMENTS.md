# Memory Requirements - Phase 1 (Implement Now)

Status: implementation-scope document.

Depends on:
- `requirements/01_AGENTCORE_REQUIREMENTS.md`
- `requirements/02_TRACE_SCHEMA.md`

## 1) Purpose

Define the minimum memory system needed immediately after AgentCore is in place:
- one uniform chunk model
- user/tenant/global (`AGENT`) scopes, enabled by effective memory policy
- secure authorized retrieval
- active chunk version history (`versions[]`) within a single scope
- chunk weighting (`memory_weight`)

This phase excludes full promotion governance and admin workflows.

## 2) Scope

### In scope
- Uniform chunk schema used by all chunk types
- Retrieval contract with strict authorization
- Version-array behavior per chunk
- Weight-based ranking input
- Tracing and audit event emission for reads/writes
- Placeholder promotion request interface only

### Out of scope
- Admin approval workflow implementation
- Full promotion state machine implementation
- Complex conflict arbitration engines
- Full retention/legal policy engines

## 3) Core assumptions

1. Platform currently has one main agent.
2. `AGENT` scope is global memory for authenticated platform users when their effective memory policy enables it. Global chunks have no `agent_id`.
3. Promotion may be initiated by learner logic, but final broad-scope activation is not autonomous in this phase.
4. Every chunk is actively managed; similar learnings append versions, not destructive overwrite.
5. A tenant is optional: TENANT memory is accessible only when a trusted `tenant_id` is present in the effective memory policy. No tenant ID means no tenant-scope search or write.
6. AgentCore instance IDs identify runtime agents, not memory namespaces. A child inherits no broader memory scopes than its parent.

## 4) Required chunk types

Required:
1. `resource`
2. `user_preference`
3. `user_details`
4. `tenant_details`
5. `workflow`

Recommended now (optional but low-risk):
6. `troubleshooting`
7. `anti_pattern`

## 5) Uniform chunk schema (required)

All chunk types must use the same top-level shape.

```json
{
  "chunk_id": "chk_01JXYZ",
  "chunk_type": "resource",
  "scope": "USER",
  "memory_weight": 0.5,
  "owner_user_id": "usr_123",
  "tenant_id": "tenant_acme",
  "status": "ACTIVE",
  "versions": [
    {
      "version_id": "v_01",
      "content": "Reusable guidance text",
      "embedding": [],
      "content_hash": "sha256:...",
      "created_at": "2026-10-05T07:00:00Z",
      "created_by": "usr_123",
      "source_conversation_id": "conv_456",
      "source_message_ids": ["msg_11"],
      "sensitivity": "INTERNAL",
      "status": "ACTIVE"
    }
  ],
  "active_version_index": 0,
  "created_at": "2026-10-05T07:00:00Z",
  "updated_at": "2026-10-05T07:00:00Z",
  "schema_version": 1
}
```

Schema rules:
- `memory_weight` range is `[0.0, 1.0]`.
- `versions[]` is append-only.
- `active_version_index` points to preferred version.
- Old versions are retained unless explicit retention rules remove them later.
- The active version alone is searchable; historical versions are visible only to an authorized history/audit caller.
- The same envelope applies to all scopes; `owner_user_id` and `tenant_id` are null when inapplicable. `scope`, owner and tenant do not change within a chunk's `versions[]`; publishing to a broader scope creates a linked target chunk (Phase 2).
- Store the version array as a logical API/domain view; physical storage may keep append-only version rows and index only the active version.

## 6) Scope invariants

### USER
- `scope = USER`
- `owner_user_id` required
- `tenant_id` is the trusted tenant ID from effective policy when present, otherwise null; USER chunks remain private to their owner in either case.

### TENANT
- `scope = TENANT`
- `owner_user_id` null
- `tenant_id` required
- TENANT reads and writes require that this ID match the trusted tenant ID in the effective memory policy.

### AGENT
- `scope = AGENT`
- `owner_user_id` null
- `tenant_id` null
- `agent_id` absent; every authenticated platform user with AGENT read enabled by effective memory policy may retrieve it.

The memory policy independently controls read/write access for USER, TENANT and AGENT. Defaults: authenticated user may read/write own USER chunks and read AGENT chunks; TENANT access is disabled unless a trusted tenant ID is supplied by policy; ordinary callers cannot write AGENT chunks. Memory policy cannot grant tenant membership through a client-provided ID. When policy changes, subsequent calls use the new effective scope, while already-authorized in-flight calls follow the AgentCore policy-version rule.

Reject invalid combinations.

## 7) Active management behavior

When new conversation learning is similar to an existing chunk:
1. append a new version to `versions[]`
2. update `active_version_index` if new version is preferred
3. keep older versions for history
4. adjust `memory_weight` based on observed usefulness

No destructive rewrite of prior versions.

## 8) Retrieval contract (must-have)

Authorization must be applied in query construction, not only after retrieval.

Required retrieval filters:
- `status = ACTIVE`
- only the active version, not expired/revoked/deleted/superseded
- scope authorization branch:
  - USER: `owner_user_id = authenticated_user_id`
  - TENANT: `tenant_id = effective_memory_policy.tenant_id` (only if present and trusted)
  - AGENT: `scope = AGENT` (when global reads are permitted)

Require authenticated user identity; absent or invalid identity fails closed. Build filters server-side from effective policy and identity; search scopes separately so no missing tenant ID can result in an unfiltered TENANT query. Never search all chunks then discard unauthorized hits. USER chunks without a tenant ID remain private to their owner.

Post-retrieval security gate required before model-context insertion:
- active status
- recognized scope
- scope ownership/membership match
- enabled scope and current effective-policy match
- not expired/revoked/superseded

Never return historical versions, private provenance, or unvalidated KB content in normal search results. Retrieved memory is untrusted data and cannot change tools, permissions, or policy.

## 9) Ranking in phase 1

Ranking inputs:
- semantic relevance
- scope specificity (`USER` > `TENANT` > `AGENT`, unless policy says otherwise)
- recency
- `memory_weight`

Authorization always takes precedence over ranking.

## 10) Tracing and audit requirements

All memory reads/writes must emit traces using `requirements/02_TRACE_SCHEMA.md`.

Minimum memory events (canonical names from `requirements/02_TRACE_SCHEMA.md`):
- `memory.retrieve.start`
- `memory.retrieve.end`
- `memory.retrieve.denied`
- `memory.write.start`
- `memory.write.end`
- `memory.write.denied`

Do not log full chunk contents by default.

## 11) Promotion boundary (phase 1 only)

The learner may recommend a promotion, but Phase 1 has no promotion-request persistence or activation. Calls to request promotion return an explicit `not_implemented` result with no pending status or request ID; the source chunk remains unchanged. Phase 2 owns the persisted request and approval workflow.

## 11.1) KB storage contract

Use PostgreSQL for authoritative chunk/version state and ChromaDB as the active-version semantic-search index. Index USER, TENANT and AGENT separately in fixed collections, with server-built owner/tenant metadata filters and post-retrieval revalidation against PostgreSQL. Do not treat Chroma metadata filtering as authentication. Reuse `src/models/embeddings.py`; see the concrete rollout/migration plan in `requirements/99_MEMORY_FULL_DRAFT_REFERENCE.md` §25.

## 12) Implementation checklist

- [ ] Implement uniform chunk schema + validation.
- [ ] Implement required chunk types.
- [ ] Implement append-only `versions[]` logic.
- [ ] Implement `memory_weight` field and retrieval/ranking usage.
- [ ] Implement authorized retrieval filters and post-retrieval gate.
- [ ] Emit required trace events with correlation IDs.
- [ ] Return explicit not-implemented for promotion requests (no auto-activation).
- [ ] Implement policy-controlled scoped search against the KB and active-version revalidation.
- [ ] Test cross-user and cross-tenant isolation, no-tenant policy behavior, and forged scope/tenant inputs.

## 13) Acceptance criteria

1. All stored chunks conform to the uniform schema.
2. Similar learnings append versions rather than deleting history.
3. Unauthorized chunks cannot enter retrieval results/model context.
4. `memory_weight` is present and influences ranking.
5. Required trace events exist for success and denial paths.
6. Promotion requests cannot publish or claim approval before Phase 2 exists.
7. With no trusted tenant ID in effective policy, user and global scopes work but no tenant memory is searched or written.
