"""Idempotent Postgres setup for this project.

Creates the target database (if missing), then every table/index the app
relies on (`api/db/repositories/*`, `src/utils/postgres_checkpointer.py`),
using `CREATE ... IF NOT EXISTS` everywhere so re-running this is always
safe. Reads connection settings from `.env` via `src.config.settings`.

Usage:
    python scripts/db_setup.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import psycopg

from src.config import settings

# Order matters: a table with a REFERENCES clause must come after the table
# it points to.
SCHEMA_STATEMENTS: list[str] = [
    "CREATE EXTENSION IF NOT EXISTS pgcrypto",
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_name    TEXT UNIQUE,
        email        TEXT UNIQUE NOT NULL,
        display_name TEXT,
        role         TEXT NOT NULL DEFAULT 'user',
        status       TEXT NOT NULL DEFAULT 'active',
        created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_credentials (
        user_id       UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
        password_hash TEXT NOT NULL,
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id            UUID PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
        app_preferences    JSONB NOT NULL DEFAULT '{}',
        agent_preferences  JSONB NOT NULL DEFAULT '{}',
        updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS auth_sessions (
        session_id  TEXT PRIMARY KEY,
        user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        expires_at  TIMESTAMPTZ NOT NULL,
        revoked_at  TIMESTAMPTZ
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_cores (
        agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_id UUID NOT NULL,
        owner_type TEXT NOT NULL CHECK (owner_type IN ('user', 'agent')),
        parent_agent_id UUID REFERENCES agent_cores(agent_id),
        latest_session_id TEXT,
        state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open', 'closed')),
        policy JSONB NOT NULL,
        policy_ceiling JSONB,
        policy_version INTEGER NOT NULL DEFAULT 1,
        depth INTEGER NOT NULL DEFAULT 0,
        title TEXT NOT NULL DEFAULT 'New chat',
        preloaded_context JSONB NOT NULL DEFAULT '{}',
        rollback_checkpoint_id TEXT,
        last_activity_at TIMESTAMPTZ,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        closed_at TIMESTAMPTZ
    )
    """,
    "ALTER TABLE agent_cores ADD COLUMN IF NOT EXISTS policy_ceiling JSONB",
    "UPDATE agent_cores SET policy_ceiling = policy WHERE policy_ceiling IS NULL AND parent_agent_id IS NULL",
    "CREATE INDEX IF NOT EXISTS idx_agent_owner ON agent_cores (owner_id, updated_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_agent_parent ON agent_cores (parent_agent_id)",
    """
    CREATE TABLE IF NOT EXISTS agent_executions (
        execution_id UUID PRIMARY KEY,
        agent_id UUID NOT NULL REFERENCES agent_cores(agent_id) ON DELETE CASCADE,
        parent_execution_id UUID REFERENCES agent_executions(execution_id),
        state TEXT NOT NULL CHECK (state IN ('running', 'interrupted', 'completed', 'failed', 'cancelled')),
        policy_version INTEGER NOT NULL,
        result TEXT,
        error TEXT,
        started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        ended_at TIMESTAMPTZ
    )
    """,
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_agent_active_execution ON agent_executions (agent_id) WHERE state IN ('running', 'interrupted')",
    "CREATE INDEX IF NOT EXISTS idx_agent_executions_parent ON agent_executions (parent_execution_id)",
    """
    CREATE TABLE IF NOT EXISTS agent_messages (
        message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        agent_id UUID NOT NULL REFERENCES agent_cores(agent_id) ON DELETE CASCADE,
        execution_id UUID NOT NULL REFERENCES agent_executions(execution_id) ON DELETE CASCADE,
        sender_type TEXT NOT NULL,
        sender_id UUID,
        content TEXT NOT NULL,
        child_agent_id UUID REFERENCES agent_cores(agent_id),
        visible_to_user BOOLEAN NOT NULL DEFAULT true,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_agent_messages_owner ON agent_messages (agent_id, created_at)",
    """
    CREATE TABLE IF NOT EXISTS messages (
        message_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        agent_id      UUID NOT NULL REFERENCES agent_cores(agent_id) ON DELETE CASCADE,
        role          TEXT NOT NULL,
        content       TEXT,
        checkpoint_id TEXT,
        plan_summary  JSONB,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_messages_agent_time ON messages (agent_id, created_at)",
    """
    CREATE TABLE IF NOT EXISTS mcp_servers_catalog (
        server_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name           TEXT NOT NULL,
        description    TEXT,
        server_url     TEXT NOT NULL,
        auth_type      TEXT NOT NULL DEFAULT 'none',
        is_global      BOOLEAN NOT NULL DEFAULT false,
        status         TEXT NOT NULL DEFAULT 'active',
        owner_user_id  UUID REFERENCES users(user_id) ON DELETE CASCADE,
        metadata       JSONB NOT NULL DEFAULT '{}',
        created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_mcp_catalog_owner ON mcp_servers_catalog (owner_user_id)",
    """
    CREATE TABLE IF NOT EXISTS user_mcp_connections (
        connection_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id            UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        server_id          UUID NOT NULL REFERENCES mcp_servers_catalog(server_id) ON DELETE CASCADE,
        connection_status  TEXT NOT NULL DEFAULT 'connected',
        connected_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
        last_used_at       TIMESTAMPTZ,
        UNIQUE (user_id, server_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_memory_entries (
        user_id     UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        key         TEXT NOT NULL,
        value       TEXT,
        category    TEXT NOT NULL DEFAULT 'general',
        updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
        PRIMARY KEY (user_id, key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memory_chunks (
        chunk_id TEXT PRIMARY KEY,
        chunk_type TEXT NOT NULL CHECK (chunk_type IN
            ('resource', 'user_preference', 'user_details', 'tenant_details', 'workflow',
             'troubleshooting', 'anti_pattern')),
        scope TEXT NOT NULL CHECK (scope IN ('USER', 'TENANT', 'AGENT')),
        owner_user_id UUID REFERENCES users(user_id),
        tenant_id TEXT,
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'REVOKED', 'DELETED')),
        memory_weight DOUBLE PRECISION NOT NULL DEFAULT 0.5 CHECK (memory_weight BETWEEN 0 AND 1),
        active_version_id TEXT,
        source_id TEXT UNIQUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        CHECK ((scope = 'USER' AND owner_user_id IS NOT NULL) OR
               (scope = 'TENANT' AND owner_user_id IS NULL AND tenant_id IS NOT NULL) OR
               (scope = 'AGENT' AND owner_user_id IS NULL AND tenant_id IS NULL))
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_memory_chunks_owner ON memory_chunks (owner_user_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_memory_chunks_tenant ON memory_chunks (tenant_id, status)",
    """
    CREATE TABLE IF NOT EXISTS memory_versions (
        version_id TEXT PRIMARY KEY,
        chunk_id TEXT NOT NULL REFERENCES memory_chunks(chunk_id),
        content TEXT NOT NULL,
        search_text TEXT NOT NULL,
        content_hash TEXT NOT NULL,
        embedding JSONB NOT NULL,
        embedding_model TEXT NOT NULL,
        embedding_dimensions INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        created_by UUID REFERENCES users(user_id),
        source_agent_id TEXT,
        source_message_ids JSONB NOT NULL DEFAULT '[]',
        sensitivity TEXT NOT NULL CHECK (sensitivity IN ('PUBLIC', 'INTERNAL', 'CONFIDENTIAL', 'RESTRICTED')),
        status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'REVOKED')),
        expires_at TIMESTAMPTZ,
        revalidated_at TIMESTAMPTZ,
        retention_class TEXT,
        promoted_from_version_id TEXT REFERENCES memory_versions(version_id),
        metadata JSONB NOT NULL DEFAULT '{}'
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_memory_versions_chunk ON memory_versions (chunk_id, created_at)",
    """
    CREATE TABLE IF NOT EXISTS memory_promotion_requests (
        request_id TEXT PRIMARY KEY,
        idempotency_key TEXT NOT NULL,
        requested_by UUID NOT NULL REFERENCES users(user_id),
        source_chunk_id TEXT NOT NULL REFERENCES memory_chunks(chunk_id),
        source_version_id TEXT NOT NULL REFERENCES memory_versions(version_id),
        from_scope TEXT NOT NULL,
        to_scope TEXT NOT NULL CHECK (to_scope IN ('TENANT', 'AGENT')),
        target_tenant_id TEXT,
        proposed_content TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN
            ('APPROVAL_PENDING', 'TARGET_ACTIVE', 'PROMOTION_REJECTED',
             'PROMOTION_FAILED', 'PROMOTION_CANCELLED')),
        target_chunk_id TEXT UNIQUE REFERENCES memory_chunks(chunk_id),
        reviewed_by UUID REFERENCES users(user_id),
        reason TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (requested_by, idempotency_key)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_memory_promotions_state ON memory_promotion_requests (state, created_at)",
    """
    CREATE TABLE IF NOT EXISTS memory_extraction_requests (
        request_id TEXT PRIMARY KEY,
        owner_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
        agent_id UUID NOT NULL REFERENCES agent_cores(agent_id) ON DELETE CASCADE,
        checkpoint_id TEXT NOT NULL,
        chunk_type TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('APPROVAL_PENDING', 'APPROVED', 'REJECTED', 'COMPLETED', 'SKIPPED')),
        reviewed_by UUID REFERENCES users(user_id),
        reason TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_memory_extraction_owner_state ON memory_extraction_requests (owner_id, state, created_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS memory_audit (
        audit_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        action TEXT NOT NULL,
        actor_user_id UUID REFERENCES users(user_id),
        chunk_id TEXT,
        version_id TEXT,
        request_id TEXT,
        details JSONB NOT NULL DEFAULT '{}',
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS memory_index_outbox (
        version_id TEXT PRIMARY KEY REFERENCES memory_versions(version_id),
        operation TEXT NOT NULL CHECK (operation IN ('UPSERT', 'DELETE')),
        attempts INTEGER NOT NULL DEFAULT 0,
        last_error TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS agent_branch_learn_state (
        agent_id           TEXT NOT NULL,
        leaf_checkpoint_id TEXT NOT NULL,
        learned_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
        status             TEXT,
        PRIMARY KEY (agent_id, leaf_checkpoint_id)
    )
    """,
    # One row per LLM call made through src/models/llm_client.py. Also the
    # lookup table for EVA_MOCK_LLM_CALL replay (see src/utils/llm_logger.py).
    # agent_id is TEXT: standalone CLI/test runs may use non-UUID identifiers.
    """
    CREATE TABLE IF NOT EXISTS llm_calls (
        call_id           UUID PRIMARY KEY,
        agent_id          TEXT,
        owner_id          TEXT,
        session_id        TEXT,
        execution_id      TEXT,
        created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
        mode              TEXT NOT NULL,
        model_id          TEXT NOT NULL,
        provider_model    TEXT,
        output_type       TEXT,
        temperature       DOUBLE PRECISION,
        cache_key         TEXT NOT NULL,
        cached            BOOLEAN NOT NULL DEFAULT false,
        source_call_id    UUID,
        status            TEXT NOT NULL DEFAULT 'ok',
        error             TEXT,
        latency_ms        INTEGER,
        system_prompt     TEXT,
        prompt            TEXT,
        response_text     TEXT,
        prompt_tokens     INTEGER,
        completion_tokens INTEGER,
        total_tokens      INTEGER,
        usage_estimated   BOOLEAN NOT NULL DEFAULT false,
        cost_usd          NUMERIC(14,8),
        usage             JSONB NOT NULL DEFAULT '{}',
        response_headers  JSONB NOT NULL DEFAULT '{}',
        raw_response      JSONB NOT NULL DEFAULT '{}'
    )
    """,
    # Partial index: replays and failed calls are excluded, so a cache lookup
    # can only ever resolve to a real, successful provider call (never a
    # replay of a replay), and the index stays small.
    """
    CREATE INDEX IF NOT EXISTS idx_llm_calls_cache
        ON llm_calls (cache_key, created_at DESC)
        WHERE status = 'ok' AND cached = false
    """,
    "CREATE INDEX IF NOT EXISTS idx_llm_calls_agent ON llm_calls (agent_id, created_at DESC)",
]


def ensure_database() -> None:
    """Create the target database if it doesn't exist yet.

    `CREATE DATABASE` can't run inside a transaction or take `IF NOT EXISTS`,
    so this connects to the `postgres` maintenance database first and checks.
    """
    maintenance_url = (
        f"postgresql://{settings.pguser}:{settings.pgpassword}"
        f"@{settings.pghost}:{settings.pgport}/postgres"
    )
    with psycopg.connect(maintenance_url, autocommit=True) as conn:
        exists = conn.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s", (settings.pgdatabase,)
        ).fetchone()
        if exists:
            print(f"Database {settings.pgdatabase!r} already exists")
            return
        conn.execute(f'CREATE DATABASE "{settings.pgdatabase}"')
        print(f"Created database {settings.pgdatabase!r}")


def ensure_schema() -> None:
    """Create the agent schema and migrate existing conversations in place."""
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        _migrate_identity(conn)
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
    print("Application tables and indexes verified/created")


def _migrate_identity(conn) -> None:
    """One-time move from conversation/run keys to agent/execution identity."""
    exists = conn.execute("SELECT to_regclass('public.chats')").fetchone()[0]
    if not exists:
        return
    with conn.transaction():
        conn.execute("LOCK TABLE chats, agent_cores, agent_runs, messages, llm_calls IN ACCESS EXCLUSIVE MODE")
        conn.execute("ALTER TABLE agent_cores ADD COLUMN IF NOT EXISTS title TEXT NOT NULL DEFAULT 'New chat'")
        conn.execute("ALTER TABLE agent_cores ADD COLUMN IF NOT EXISTS preloaded_context JSONB NOT NULL DEFAULT '{}'")
        conn.execute("ALTER TABLE agent_cores ADD COLUMN IF NOT EXISTS rollback_checkpoint_id TEXT")
        conn.execute("ALTER TABLE agent_cores ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ")
        conn.execute("ALTER TABLE agent_cores ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()")
        conn.execute("""UPDATE agent_cores a SET title = COALESCE(c.title, 'New chat'),
                    preloaded_context = c.preloaded_context,
                    rollback_checkpoint_id = c.rollback_checkpoint_id, last_activity_at = c.last_activity_at,
                    updated_at = c.updated_at, created_at = c.created_at,
                    state = CASE WHEN c.status = 'deleted' THEN 'closed' ELSE a.state END
                    FROM chats c WHERE a.chat_id = c.chat_id AND a.parent_agent_id IS NULL""")
        conn.execute("""INSERT INTO agent_cores (owner_id, owner_type, chat_id, latest_session_id, policy,
                    title, preloaded_context, rollback_checkpoint_id, last_activity_at,
                    created_at, updated_at, state)
                    SELECT c.user_id, 'user', c.chat_id, NULL,
                           jsonb_build_object(
                               'armory', jsonb_build_object('tools', to_jsonb(ARRAY[
                                   'get_current_datetime_info', 'system_info', 'read_file', 'edit_file',
                                   'search_file', 'web_search', 'decompose_query', 'execute_bash',
                                   'execute_powershell', 'execute_python_script', 'user_memory_update',
                                   'user_memory_fetch', 'mcp:*']), 'subagents', '[]'::jsonb,
                                   'confirm_tools', true),
                               'memory', jsonb_build_object('read', to_jsonb(ARRAY['USER','AGENT']),
                                   'write', to_jsonb(ARRAY['USER']), 'tenant_id', null),
                               'guardrails', jsonb_build_object('confirm_tools', true),
                               'observability', jsonb_build_object('enabled', true)),
                            COALESCE(c.title, 'New chat'),
                           c.preloaded_context, c.rollback_checkpoint_id, c.last_activity_at,
                           c.created_at, c.updated_at,
                           CASE WHEN c.status = 'deleted' THEN 'closed' ELSE 'open' END
                    FROM chats c WHERE NOT EXISTS (SELECT 1 FROM agent_cores a WHERE a.chat_id = c.chat_id
                                                     AND a.parent_agent_id IS NULL)""")
        conn.execute("ALTER TABLE agent_runs RENAME TO agent_executions")
        conn.execute("ALTER TABLE agent_executions RENAME COLUMN run_id TO execution_id")
        conn.execute("ALTER TABLE agent_executions RENAME COLUMN parent_run_id TO parent_execution_id")
        conn.execute("ALTER TABLE agent_messages RENAME COLUMN run_id TO execution_id")
        # Assign each historical execution to the canonical root AgentCore. The
        # old deployment may have created multiple root cores for one conversation.
        conn.execute("""UPDATE agent_executions e SET agent_id = root.agent_id
                    FROM agent_cores old, agent_cores root
                    WHERE e.agent_id = old.agent_id AND old.parent_agent_id IS NULL
                    AND root.chat_id = old.chat_id AND root.parent_agent_id IS NULL
                    AND root.agent_id = (SELECT r.agent_id FROM agent_cores r
                                         WHERE r.chat_id = old.chat_id AND r.parent_agent_id IS NULL
                                         ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("""UPDATE agent_messages m SET agent_id = e.agent_id
                    FROM agent_executions e WHERE m.execution_id = e.execution_id""")
        conn.execute("ALTER TABLE messages ADD COLUMN IF NOT EXISTS agent_id UUID")
        conn.execute("""UPDATE messages m SET agent_id = a.agent_id FROM agent_cores a
                    WHERE m.chat_id = a.chat_id AND a.parent_agent_id IS NULL
                    AND a.agent_id = (SELECT r.agent_id FROM agent_cores r
                                      WHERE r.chat_id = m.chat_id AND r.parent_agent_id IS NULL
                                      ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("ALTER TABLE messages ALTER COLUMN agent_id SET NOT NULL")
        conn.execute("ALTER TABLE messages ADD CONSTRAINT messages_agent_fk FOREIGN KEY (agent_id) REFERENCES agent_cores(agent_id) ON DELETE CASCADE")
        # Materialized transcript rows may already exist under an old checkpoint
        # thread id; their agent_id is updated above and their checkpoint ids
        # stay stable across the thread rename.
        conn.execute("""UPDATE checkpoints p SET thread_id = a.agent_id::text FROM agent_cores a
                    WHERE p.thread_id = a.chat_id::text AND a.parent_agent_id IS NULL
                    AND a.agent_id = (SELECT r.agent_id FROM agent_cores r
                                      WHERE r.chat_id = a.chat_id AND r.parent_agent_id IS NULL
                                      ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("""UPDATE checkpoint_blobs p SET thread_id = a.agent_id::text FROM agent_cores a
                    WHERE p.thread_id = a.chat_id::text AND a.parent_agent_id IS NULL
                    AND a.agent_id = (SELECT r.agent_id FROM agent_cores r
                                      WHERE r.chat_id = a.chat_id AND r.parent_agent_id IS NULL
                                      ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("""UPDATE checkpoint_writes p SET thread_id = a.agent_id::text FROM agent_cores a
                    WHERE p.thread_id = a.chat_id::text AND a.parent_agent_id IS NULL
                    AND a.agent_id = (SELECT r.agent_id FROM agent_cores r
                                      WHERE r.chat_id = a.chat_id AND r.parent_agent_id IS NULL
                                      ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("ALTER TABLE memory_versions RENAME COLUMN source_conversation_id TO source_agent_id")
        conn.execute("""UPDATE memory_versions v SET source_agent_id = a.agent_id::text
                    FROM agent_cores a WHERE v.source_agent_id = a.chat_id::text AND a.parent_agent_id IS NULL
                    AND a.agent_id = (SELECT r.agent_id FROM agent_cores r
                                      WHERE r.chat_id = a.chat_id AND r.parent_agent_id IS NULL
                                      ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("ALTER TABLE chat_branch_learn_state RENAME TO agent_branch_learn_state")
        conn.execute("ALTER TABLE agent_branch_learn_state RENAME COLUMN chat_id TO agent_id")
        conn.execute("""UPDATE agent_branch_learn_state b SET agent_id = a.agent_id::text
                    FROM agent_cores a WHERE b.agent_id = a.chat_id::text AND a.parent_agent_id IS NULL
                    AND a.agent_id = (SELECT r.agent_id FROM agent_cores r
                                      WHERE r.chat_id = a.chat_id AND r.parent_agent_id IS NULL
                                      ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS agent_id TEXT")
        conn.execute("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS owner_id TEXT")
        conn.execute("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS session_id TEXT")
        conn.execute("ALTER TABLE llm_calls ADD COLUMN IF NOT EXISTS execution_id TEXT")
        conn.execute("""UPDATE llm_calls l SET agent_id = a.agent_id::text FROM agent_cores a
                    WHERE l.chat_id = a.chat_id::text AND a.parent_agent_id IS NULL
                    AND a.agent_id = (SELECT r.agent_id FROM agent_cores r
                                      WHERE r.chat_id = a.chat_id AND r.parent_agent_id IS NULL
                                      ORDER BY r.agent_id LIMIT 1)""")
        conn.execute("UPDATE llm_calls SET owner_id = user_id, execution_id = run_id WHERE owner_id IS NULL")
        conn.execute("UPDATE llm_calls SET agent_id = 'unbound' WHERE agent_id IS NULL")
        conn.execute("ALTER TABLE llm_calls DROP COLUMN chat_id, DROP COLUMN run_id, DROP COLUMN user_id, DROP COLUMN coreid")
        conn.execute("ALTER TABLE messages DROP COLUMN chat_id")
        conn.execute("ALTER TABLE agent_cores DROP COLUMN chat_id, DROP COLUMN log_id")
        conn.execute("DROP TABLE chats")


def ensure_checkpointer_tables() -> None:
    """LangGraph owns `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` —
    let its own `setup()` create them rather than hand-rolling the schema."""
    from src.utils.postgres_checkpointer import get_checkpointer

    get_checkpointer()
    print("LangGraph checkpoint tables verified/created")


def main() -> None:
    ensure_database()
    ensure_schema()
    ensure_checkpointer_tables()
    print("Database setup complete.")


if __name__ == "__main__":
    main()
