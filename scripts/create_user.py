"""Create one application user and their required onboarding records.

Edit the values below, then run:
    python scripts/create_user.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import psycopg

from api.core.security import hash_password
from src.config import settings


# User values: edit these before running the script.
USERNAME = "jdoe"
PASSWORD = "User@123"
EMAIL = "jdeo@riministreet.com"
DISPLAY_NAME = "Jane Doe"
ROLE = "user"
STATUS = "active"
APP_PREFERENCES = {"theme": "system", "console_mode": "basic"}
AGENT_PREFERENCES = {}


def create_user() -> str:
    """Create the user, credentials, and preferences in one transaction."""
    if not USERNAME.strip() or not EMAIL.strip() or not PASSWORD:
        raise ValueError("USERNAME, EMAIL, and PASSWORD are required")
    if PASSWORD == "replace-with-a-strong-password":
        raise ValueError("Replace the placeholder PASSWORD before running the script")

    with psycopg.connect(settings.database_url) as conn:
        user = conn.execute(
            """
            INSERT INTO users (user_name, email, display_name, role, status)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING user_id
            """,
            (USERNAME.strip(), EMAIL.strip().lower(), DISPLAY_NAME.strip(), ROLE, STATUS),
        ).fetchone()
        user_id = str(user[0])
        conn.execute(
            "INSERT INTO user_credentials (user_id, password_hash) VALUES (%s, %s)",
            (user_id, hash_password(PASSWORD)),
        )
        conn.execute(
            """
            INSERT INTO user_preferences (user_id, app_preferences, agent_preferences)
            VALUES (%s, %s, %s)
            """,
            (user_id, Jsonb(APP_PREFERENCES), Jsonb(AGENT_PREFERENCES)),
        )

    return user_id


if __name__ == "__main__":
    print(f"Created user {USERNAME!r} with user_id={create_user()}")
