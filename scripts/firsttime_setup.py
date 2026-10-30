"""First-time local setup helper for Meta-Agent v2.

This script checks local prerequisites, initializes PostgreSQL schema, and
creates/updates a developer test user for login.

Usage:
    backend/.venv/bin/python scripts/firsttime_setup.py
"""

from __future__ import annotations

import getpass
import shutil
import sys
from pathlib import Path

from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
for p in (BACKEND_ROOT, ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import psycopg

from api.core.security import hash_password
from scripts.db_setup import ensure_checkpointer_tables, ensure_database, ensure_schema
from src.config import settings


def _status(mark: bool) -> str:
    return "[x]" if mark else "[ ]"


def print_prereq_checklist() -> None:
    print("\n=== Installation Checklist ===")
    checks = [
        ("Python available", shutil.which("python3") is not None),
        ("Node.js available", shutil.which("node") is not None),
        ("npm available", shutil.which("npm") is not None),
        ("psql client available", shutil.which("psql") is not None),
        ("Backend venv exists", (BACKEND_ROOT / ".venv" / "bin" / "python").exists()),
        ("Frontend node_modules exists", (ROOT / "frontend" / "node_modules").exists()),
        ("backend/.env present", (BACKEND_ROOT / ".env").exists()),
    ]
    for label, ok in checks:
        print(f"{_status(ok)} {label}")

    print("\nRequired manual installs if unchecked:")
    print("- PostgreSQL server (running locally and reachable via backend/.env PG* settings)")
    print("- Backend deps: cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements.txt")
    print("- Frontend deps: cd frontend && npm install")


def prompt_value(label: str, default: str) -> str:
    raw = input(f"{label} [{default}]: ").strip()
    return raw or default


def prompt_password() -> str:
    while True:
        first = getpass.getpass("Password [password123]: ").strip()
        if not first:
            return "password123"
        second = getpass.getpass("Confirm password: ").strip()
        if first != second:
            print("Passwords do not match. Try again.")
            continue
        if len(first) < 8:
            print("Password must be at least 8 characters.")
            continue
        return first


def create_or_update_test_user(
    *,
    username: str,
    email: str,
    display_name: str,
    password: str,
    role: str = "user",
    status: str = "active",
) -> tuple[str, bool]:
    with psycopg.connect(settings.database_url, autocommit=True) as conn:
        existing = conn.execute(
            """
            SELECT user_id FROM users
            WHERE lower(user_name) = lower(%s) OR lower(email) = lower(%s)
            LIMIT 1
            """,
            (username, email),
        ).fetchone()

        created = existing is None
        if created:
            row = conn.execute(
                """
                INSERT INTO users (user_name, email, display_name, role, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING user_id
                """,
                (username, email, display_name, role, status),
            ).fetchone()
            user_id = str(row[0])
        else:
            user_id = str(existing[0])
            conn.execute(
                """
                UPDATE users
                SET user_name = %s, email = %s, display_name = %s, role = %s, status = %s, updated_at = now()
                WHERE user_id = %s
                """,
                (username, email, display_name, role, status, user_id),
            )

        conn.execute(
            """
            INSERT INTO user_credentials (user_id, password_hash)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET password_hash = EXCLUDED.password_hash, updated_at = now()
            """,
            (user_id, hash_password(password)),
        )

        conn.execute(
            """
            INSERT INTO user_preferences (user_id, app_preferences, agent_preferences)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET app_preferences = user_preferences.app_preferences,
                agent_preferences = user_preferences.agent_preferences,
                updated_at = now()
            """,
            (
                user_id,
                Jsonb({"theme": "system", "console_mode": "basic"}),
                Jsonb({}),
            ),
        )
    return user_id, created


def shutdown_pools() -> None:
    """Best-effort cleanup for pooled DB connections used during setup."""
    try:
        from api.db.postgres import close_pool as close_api_pool

        close_api_pool()
    except Exception:
        pass

    try:
        from src.utils.postgres.db_utils import close_pool as close_src_pool

        close_src_pool()
    except Exception:
        pass

    try:
        import src.utils.postgres_checkpointer as checkpointer

        pool = getattr(checkpointer, "_pool", None)
        if pool is not None:
            pool.close()
            setattr(checkpointer, "_pool", None)
        setattr(checkpointer, "_checkpointer", None)
    except Exception:
        pass


def main() -> int:
    try:
        print("Meta-Agent v2 first-time setup")
        print_prereq_checklist()

        print("\n=== PostgreSQL setup ===")
        print(f"Using database URL from backend settings: {settings.pghost}:{settings.pgport}/{settings.pgdatabase}")
        try:
            ensure_database()
            ensure_schema()
            ensure_checkpointer_tables()
        except Exception as exc:
            print("\nSetup failed while preparing database/schema.")
            print(f"Reason: {type(exc).__name__}: {exc}")
            print("Action: verify PostgreSQL is running and PG* values in backend/.env are correct.")
            return 1

        print("\n=== Test user setup ===")
        username = prompt_value("Username", "test_user")
        email = prompt_value("Email", f"{username}@example.com").lower()
        display_name = prompt_value("Display name", "Test User")
        password = prompt_password()

        try:
            user_id, created = create_or_update_test_user(
                username=username,
                email=email,
                display_name=display_name,
                password=password,
            )
        except Exception as exc:
            print("\nDatabase is ready, but user setup failed.")
            print(f"Reason: {type(exc).__name__}: {exc}")
            return 1

        print("\n=== Setup complete ===")
        print(f"User {'created' if created else 'updated'}: {username} (user_id={user_id})")
        print("\nNext steps checklist:")
        print("[ ] Ensure backend/.env has valid LLM_GATEWAY_API_KEY and MCP_CREDENTIALS_KEY")
        print("[ ] Start both apps: ./run_dev")
        print(f"[ ] Sign in at http://localhost:5173 with username={username}")
        print("[ ] Verify backend health: http://localhost:5000/v1/live")
        return 0
    finally:
        shutdown_pools()


if __name__ == "__main__":
    raise SystemExit(main())
