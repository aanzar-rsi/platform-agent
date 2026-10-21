# Multi-User Agentic AI Platform — Database Design

<!-- ## 0. Storage architecture (polyglot, not one-size-fits-all)

Don't force all 7 concerns into one database. Use the right tool per workload, but keep it to a **small, justified set** so you're not managing five different systems for no reason.

| Concern | Store | Why |
|---|---|---|
| Users, credentials, preferences, activity, chats, checkpoints, MCP config | **PostgreSQL** (Aurora Postgres Serverless v2 — fits your AWS stack) | Relational integrity, ACID, JSONB for flexible blobs, mature LangGraph checkpointer support |
| Active sessions / rate limits / ephemeral state | **Redis** (ElastiCache) | Sub-ms reads, TTL-native, don't hit Postgres for every "is this session alive" check |
| Long-term memory (semantic) | **pgvector extension on the same Postgres**, or a dedicated vector DB (Qdrant, since you've already used it in PANDORA) | Needs similarity search, not just key lookup |
| Analytics | **Event stream → warehouse** (Kinesis Firehose → S3 → Athena/Redshift, or ClickHouse) | OLTP tables should never serve analytical scans — keep them out of Postgres's write path |

Rule of thumb: Postgres is the system of record for everything transactional and relational. Analytics and vector search are read-heavy, different-access-pattern workloads — split them out early rather than retrofitting later.

--- -->

## 1. Users, credentials, preferences

**Don't build your own auth if you can avoid it.** Given your AWS-heavy stack, use **AWS Cognito** (or Auth0/Clerk) for credential storage, password hashing, MFA, and session tokens. Store only a reference (`external_auth_id`) in your DB. This removes an entire category of security liability from your design.

```sql
CREATE TABLE users (
    user_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_auth_id  TEXT UNIQUE NOT NULL,      -- Cognito sub / Auth0 user_id
    email             TEXT UNIQUE NOT NULL,
    display_name      TEXT,
    role              TEXT NOT NULL,
    status            TEXT NOT NULL DEFAULT 'active', -- active, suspended, deleted
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Only needed if you insist on owning auth yourself. Prefer NOT to populate this.
CREATE TABLE user_credentials (
    user_id        UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    password_hash  TEXT NOT NULL,   -- argon2id, never bcrypt-only, never plaintext
    mfa_secret     TEXT,
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE user_preferences (
    user_id        UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    app_preferences    JSONB NOT NULL DEFAULT '{}',
	agent_preferences JSONB NOT NULL DEFAULT '{}',
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`preferences` as JSONB is the right call here — it's genuinely schemaless (arbitrary UI/agent-behavior settings), unlike your relational entities where flexibility would just hide bugs.

---

## 2. User activity & sessions

Split **durable activity log** (Postgres) from **ephemeral live session state** (Redis). Don't make Redis the source of truth for anything you need to query historically.

```sql
CREATE TABLE user_activity_log (
    activity_id     BIGSERIAL,
    user_id         UUID NOT NULL REFERENCES users(user_id),
    event_type      TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    ip_address      INET,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);

CREATE INDEX idx_activity_user_time ON user_activity_log (user_id, created_at DESC);
```

Live sessions in Redis:
```
session:{session_id}  -> { user_id, device, started_at, last_seen_at, active_chat_ids: [...] }
TTL: sliding, refreshed on activity
```
`users.last_login_at` gets updated in Postgres on login; everything moment-to-moment (which sessions are open right now, across which devices) lives in Redis and never touches Postgres. This matters for your "multiple parallel chat instances" requirement — session liveness is a hot-path check, not a query you want a relational join for.

---

## 3. Chats & agent activity

```sql
CREATE TABLE chats (
    chat_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(user_id),
    agent_type        TEXT NOT NULL,          -- which agent/graph this chat runs
    title             TEXT,
    status            TEXT NOT NULL DEFAULT 'active', -- active, archived, deleted
    last_checkpoint_id TEXT,                  -- pointer to latest LangGraph checkpoint
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_chats_user ON chats (user_id, updated_at DESC);

CREATE TABLE messages (
    message_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chat_id        UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    role           TEXT NOT NULL,             -- user, assistant, tool, system
    content        TEXT,
    checkpoint_id  TEXT,                      -- links this message to the state that produced it
    plan_summary   JSONB,                     -- lightweight plan snapshot for quick UI rendering
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_messages_chat_time ON messages (chat_id, created_at);
```

Key design decision: `messages` is your **UI-facing** history — fast to paginate, cheap to render. `checkpoints` (next section) is your **engine-facing** history — heavy, used for rollback/replay, not for rendering chat bubbles. Don't conflate them; if you store full state on every message row, chat list queries get slow as chats grow long.

`plan_summary` is a deliberately small JSONB field (e.g. `{steps: [...], status: "completed"}`) just so the UI can show "here's what the agent planned" without deserializing a full checkpoint. The *authoritative* plan/state lives in the checkpoint.

---

## 4. Checkpoints & execution details (LangGraph)

Use LangGraph's built-in `AsyncPostgresSaver` rather than hand-rolling this — it already implements exactly what you're asking for (per-superstep state persistence, rollback, forking).

```sql
-- These are the checkpointer's own tables (created via saver.setup()); shown here for clarity
CREATE TABLE checkpoints (
    thread_id            TEXT NOT NULL,      -- = chat_id
    checkpoint_ns         TEXT NOT NULL DEFAULT '',  -- subgraph namespace
    checkpoint_id         TEXT NOT NULL,
    parent_checkpoint_id  TEXT,
    checkpoint            JSONB NOT NULL,     -- serialized graph state
    metadata               JSONB,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);

CREATE TABLE checkpoint_writes (
    thread_id      TEXT NOT NULL,
    checkpoint_ns  TEXT NOT NULL DEFAULT '',
    checkpoint_id  TEXT NOT NULL,
    task_id        TEXT NOT NULL,
    channel        TEXT NOT NULL,
    value          JSONB,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, channel)
);

CREATE INDEX idx_checkpoints_thread ON checkpoints (thread_id, checkpoint_id);
```

- `thread_id = chat_id` — this is the natural mapping, and it's what gives you clean isolation for parallel chats per user (each parallel chat = its own thread, no locking contention between them).
- Rollback = list checkpoints for a `thread_id`, pick a `checkpoint_id`, resume the graph with that config. **Forking** (start a new branch from an old checkpoint without destroying the original) comes free from the same mechanism — worth exposing as "regenerate from here" in your UI rather than a destructive rollback.
- **Don't store large tool outputs inline in `checkpoint`.** If a node output includes big documents/embeddings/scraped content, store a reference (S3 key) in the checkpoint and keep the JSONB itself lean — otherwise every superstep write gets slower as the conversation grows.
- Given your existing OpenTelemetry instrumentation on LangGraph nodes: keep trace/span IDs in `checkpoints.metadata`, not as new columns. That way execution *traces* (for debugging/observability) stay linked to the exact state they came from, and you're not duplicating what OTel/X-Ray already captures.

---
<!-- 
## 5. Long-term memory (per user)

This is semantically different from checkpoints — checkpoints are per-conversation execution state; long-term memory is cross-conversation, user-level, and needs **similarity search**, not exact lookup.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE user_memories (
    memory_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id        UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    content        TEXT NOT NULL,          -- the extracted fact/preference/summary
    embedding      VECTOR(1536),           -- match your embedding model's dims
    source_chat_id UUID REFERENCES chats(chat_id),
    memory_type    TEXT NOT NULL,          -- fact, preference, skill_level, correction...
    confidence     REAL DEFAULT 1.0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_reinforced_at TIMESTAMPTZ         -- bump when the same fact resurfaces/confirmed
);
CREATE INDEX idx_memories_user ON user_memories (user_id);
CREATE INDEX idx_memories_embedding ON user_memories USING hnsw (embedding vector_cosine_ops);
```

Design notes:
- **pgvector is fine to start** — keeps you on one database, avoids an extra service. Move to a dedicated vector DB (you already know Qdrant) only once you're doing memory retrieval at a scale where HNSW-in-Postgres starts contending with your OLTP write load.
- `memory_type` + `confidence` matter more than people expect: you want the agent to be able to *revise or decay* memories, not just accumulate them forever. A naive "dump every extracted fact into a table" design turns into an unmanageable pile within a few months — treat memory writes as an explicit agent step (extract → dedupe/merge against existing memories → write), not an automatic side effect of every message.
- `source_chat_id` gives you traceability ("why does the agent think this about me") which you'll want for debugging and for user-facing "here's what I remember about you" transparency features.

--- -->

## 6. MCP server details (global + per-user)

Two-tier, matching how you described it:

```sql
-- Global catalog: servers available on the platform
CREATE TABLE mcp_servers_catalog (
    server_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name           TEXT NOT NULL UNIQUE,
    description    TEXT,
    server_url     TEXT NOT NULL,
    auth_type      TEXT NOT NULL,        -- oauth2, api_key, none
    is_global      BOOLEAN NOT NULL DEFAULT true,  -- available to all users by default
    status         TEXT NOT NULL DEFAULT 'active',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-user connections (their own auth to a given server)
CREATE TABLE user_mcp_connections (
    connection_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    server_id         UUID NOT NULL REFERENCES mcp_servers_catalog(server_id),
    credential_ref     TEXT,             -- pointer into Secrets Manager / KMS-encrypted, NEVER raw tokens in this table
    connection_status  TEXT NOT NULL DEFAULT 'connected',  -- connected, expired, revoked
    connected_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_used_at         TIMESTAMPTZ,
    UNIQUE (user_id, server_id)
);

-- Optional: which servers are enabled for a specific chat (subset of user's connections)
CREATE TABLE chat_mcp_enabled (
    chat_id        UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    server_id      UUID NOT NULL REFERENCES mcp_servers_catalog(server_id),
    PRIMARY KEY (chat_id, server_id)
);
```

- **Never store OAuth tokens or API keys directly in Postgres.** `credential_ref` points to AWS Secrets Manager (which you're already using) — the DB just tracks *that* a connection exists and its status, not the secret itself. This is the same zero-trust instinct as the multi-agent security architecture you designed earlier — same principle, applied to MCP credentials.
- `chat_mcp_enabled` is optional but useful if a user has 10 MCP servers connected globally but only wants 2 active in a given chat (keeps tool-selection scope tight per conversation, which also helps LLM tool-choice accuracy).

<!-- ---

## 7. Analytics

**Do not run analytics queries against your OLTP tables.** Even well-indexed, aggregate scans (DAU, funnel analysis, token usage over time) will eventually compete with live chat traffic for the same rows. Two viable patterns, pick based on your scale:

**Simple (works fine up to moderate scale):**
```sql
CREATE TABLE analytics_events (
    event_id       BIGSERIAL PRIMARY KEY,
    user_id        UUID,
    chat_id        UUID,
    event_type     TEXT NOT NULL,     -- message_sent, checkpoint_created, tool_called, error...
    properties     JSONB DEFAULT '{}',
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
) PARTITION BY RANGE (created_at);
```
Write to this from a background worker (not inline in the request path), and run heavy aggregate queries against a **read replica**, not the primary.

**At real scale:** stream events (app → Kinesis Firehose → S3, partitioned by date) and query with Athena, or sink into a purpose-built OLAP store (ClickHouse/Redshift). Given you're already comfortable with AWS App Runner/CloudWatch, Kinesis Firehose → S3 → Athena is the path of least new-infra-to-learn.

Either way: **analytics is append-only and asynchronous.** It should never sit in the critical path of a chat response. -->

---

## 8. Entity relationship summary

```
users ─┬─< user_credentials (1:1, optional if using external auth)
       ├─< user_preferences (1:1)
       ├─< user_activity_log (1:N)
       ├─< chats (1:N)
       │     └─< messages (1:N)
       │     └─< checkpoints (1:N, via thread_id = chat_id)   [LangGraph-owned]
       │     └─< chat_mcp_enabled (N:M with mcp_servers_catalog)
       ├─< user_memories (1:N, vector-indexed)
       └─< user_mcp_connections (N:M with mcp_servers_catalog)

mcp_servers_catalog ─< user_mcp_connections
                     ─< chat_mcp_enabled
```

## 9. Practical guardrails as this grows

- **Partition early**, not late: `user_activity_log`, `analytics_events`, and eventually `checkpoints` (by month) — retrofitting partitioning on a live multi-TB table is painful.
- **Retention policy up front**: decide now whether old checkpoints get archived to S3 after N days (you rarely need to roll back a chat from 6 months ago) vs. kept forever. This affects Postgres storage cost directly since checkpoint payloads are the heaviest thing in this whole schema.
- **Read replicas** for analytics and for chat-history pagination once you have real concurrent load — keep the primary focused on writes (messages, checkpoints) and interactive reads for the active chat.
<!-- - **Don't skip the external auth provider.** Every self-rolled credentials table is a future incident; Cognito/Auth0 removes it as a category of risk for cheap. -->