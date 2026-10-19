"""Process-wide Postgres connection pool + small query helpers for `src/`.

The `src/`-side twin of `api/db/postgres.py`. Agent code must not import from
`api/` (the agent runs standalone via `main.py --cli` and inside the sandbox),
so it gets its own pool built from `src.config.settings.database_url`.
"""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                from src.config import settings

                _pool = ConnectionPool(
                    conninfo=settings.database_url,
                    min_size=1,
                    max_size=10,
                    kwargs={"row_factory": dict_row, "autocommit": True},
                    open=True,
                )
    return _pool


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def fetch_one(sql: str, params: tuple | dict | None = None) -> dict[str, Any] | None:
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchone()


def fetch_all(sql: str, params: tuple | dict | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.fetchall()


def execute(sql: str, params: tuple | dict | None = None) -> int:
    """Run an INSERT/UPDATE/DELETE, return affected row count."""
    with get_connection() as conn:
        cur = conn.execute(sql, params)
        return cur.rowcount


def close_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close()
            _pool = None
