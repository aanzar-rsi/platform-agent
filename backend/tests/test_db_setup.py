"""Tests for scripts/db_setup.py.

Static checks always run. The live integration test only runs when a
reachable Postgres server is configured via .env — it creates a throwaway
database, runs the setup script against it twice (idempotency), then drops it.
"""

from __future__ import annotations

import socket
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.db_setup import SCHEMA_STATEMENTS

EXPECTED_TABLES = [
    "users",
    "user_credentials",
    "user_preferences",
    "auth_sessions",
    "agent_cores",
    "agent_executions",
    "agent_execution_events",
    "agent_messages",
    "messages",
    "mcp_servers_catalog",
    "user_mcp_connections",
    "user_memory_entries",
    "memory_chunks",
    "memory_versions",
    "memory_promotion_requests",
    "memory_extraction_requests",
    "memory_audit",
    "memory_index_outbox",
    "agent_branch_learn_state",
    "llm_calls",
]


def _postgres_reachable() -> bool:
    try:
        from src.config import settings
    except Exception:
        return False
    try:
        with socket.create_connection((settings.pghost, settings.pgport), timeout=1.5):
            return True
    except OSError:
        return False


class TestSchemaStatementsAreIdempotent(unittest.TestCase):
    def test_every_create_uses_if_not_exists(self):
        for statement in SCHEMA_STATEMENTS:
            upper = statement.upper()
            if "CREATE TABLE" in upper or "CREATE INDEX" in upper or "CREATE EXTENSION" in upper:
                self.assertIn(
                    "IF NOT EXISTS",
                    upper,
                    f"statement is not idempotent: {statement.strip()[:60]}",
                )

    def test_all_expected_tables_are_declared(self):
        combined = "\n".join(SCHEMA_STATEMENTS)
        for table in EXPECTED_TABLES:
            self.assertIn(
                f"CREATE TABLE IF NOT EXISTS {table} ",
                combined,
                f"missing table definition: {table}",
            )

    def test_agent_schema_has_no_legacy_identity(self):
        combined = "\n".join(SCHEMA_STATEMENTS)
        for retired in ("chat_id", "run_id", "coreid", "log_id", "CREATE TABLE IF NOT EXISTS chats"):
            self.assertNotIn(retired, combined)

    def test_foreign_keys_come_after_their_target_table(self):
        """A REFERENCES users(...) statement must not appear before `users`
        is created, since CREATE_STATEMENTS run in list order."""
        seen: set[str] = set()
        for statement in SCHEMA_STATEMENTS:
            for table in EXPECTED_TABLES:
                if f"REFERENCES {table}(" in statement and f"CREATE TABLE IF NOT EXISTS {table} " not in statement:
                    self.assertIn(
                        table,
                        seen,
                        f"{table} referenced before it was created",
                    )
            for table in EXPECTED_TABLES:
                if f"CREATE TABLE IF NOT EXISTS {table} " in statement:
                    seen.add(table)


@unittest.skipUnless(_postgres_reachable(), "no reachable Postgres server configured in .env")
class TestDbSetupLive(unittest.TestCase):
    def test_setup_is_idempotent_against_a_throwaway_database(self):
        import psycopg

        from src.config import settings
        import scripts.db_setup as db_setup

        test_db_name = f"{settings.pgdatabase}_test_db_setup"
        original_db = settings.pgdatabase
        maintenance_url = (
            f"postgresql://{settings.pguser}:{settings.pgpassword}"
            f"@{settings.pghost}:{settings.pgport}/postgres"
        )

        def _drop():
            with psycopg.connect(maintenance_url, autocommit=True) as conn:
                conn.execute(f'DROP DATABASE IF EXISTS "{test_db_name}"')

        _drop()
        settings.pgdatabase = test_db_name
        try:
            db_setup.ensure_database()
            db_setup.ensure_schema()
            # Re-running must not raise (CREATE ... IF NOT EXISTS everywhere).
            db_setup.ensure_database()
            db_setup.ensure_schema()

            with psycopg.connect(settings.database_url, autocommit=True) as conn:
                rows = conn.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
                ).fetchall()
            created = {r[0] for r in rows}
            for table in EXPECTED_TABLES:
                self.assertIn(table, created)
        finally:
            settings.pgdatabase = original_db
            _drop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
