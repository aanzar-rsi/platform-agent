"""Full-fidelity recording of every LLM call, plus the mock-replay cache.

Two responsibilities, both driven from `src/models/llm_client.py`:

1. **Record.** Every call (success, error, or replay) becomes one complete JSON
   record carrying the real provider `usage`, the gateway-reported cost, the
   raw response body, and the session identity it happened under. Records fan
   out to two sinks:
      - `logs/llm/{timestamp}_{agent_id}.jsonl` — one line per call,
        segregated by agent.
       Reuses the writer thread in `agent_logger` rather than starting a second
       one, so the existing "never block the agent on a disk write" guarantee
       applies here too.
     - the `llm_calls` Postgres table, via its own background writer thread.

2. **Replay.** `build_cache_key` + `lookup_cached_response` implement
   `EVA_MOCK_LLM_CALL`: an identical earlier call is served from `llm_calls`
   instead of the gateway.

Every public function soft-fails. A dead Postgres, a full disk, or a malformed
record must degrade recording — never break an agent run.
"""

from __future__ import annotations

import atexit
import hashlib
import json
import logging
import queue
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.utils.agent_logger import (
    DEFAULT_MAX_FIELD_CHARS,
    _ensure_writer_started,
    _filename_timestamp,
    _log_filename,
    _log_queue,
    _safe_agent_id,
    get_session_logger,
    truncate_value,
)

logger = logging.getLogger(__name__)

# Prompts and responses are the whole point of this log, so they get a much
# larger budget than the 50k the agent trace uses — but still bounded, so one
# pathological call can't write a gigabyte.
MAX_TEXT_CHARS = 200_000

_DB_QUEUE_MAX_SIZE = 10_000
_db_queue: "queue.Queue[dict[str, Any]]" = queue.Queue(maxsize=_DB_QUEUE_MAX_SIZE)
_db_thread: threading.Thread | None = None
_db_thread_lock = threading.Lock()
_table_ready = False
_llm_files: dict[str, str] = {}

_INSERT_SQL = """
INSERT INTO llm_calls (
    call_id, agent_id, owner_id, session_id, execution_id, mode, model_id, provider_model,
    output_type, temperature, cache_key, cached, source_call_id, status, error,
    latency_ms, system_prompt, prompt, response_text, prompt_tokens,
    completion_tokens, total_tokens, usage_estimated, cost_usd, usage,
    response_headers, raw_response
) VALUES (
    %(call_id)s, %(agent_id)s, %(owner_id)s, %(session_id)s, %(execution_id)s, %(mode)s,
    %(model_id)s, %(provider_model)s, %(output_type)s, %(temperature)s,
    %(cache_key)s, %(cached)s, %(source_call_id)s, %(status)s, %(error)s,
    %(latency_ms)s, %(system_prompt)s, %(prompt)s, %(response_text)s,
    %(prompt_tokens)s, %(completion_tokens)s, %(total_tokens)s,
    %(usage_estimated)s, %(cost_usd)s, %(usage)s, %(response_headers)s,
    %(raw_response)s
)
ON CONFLICT (call_id) DO NOTHING
"""

_LOOKUP_SQL = """
SELECT call_id, response_text, model_id, created_at
FROM llm_calls
WHERE cache_key = %s AND status = 'ok' AND cached = false
  AND response_text IS NOT NULL
ORDER BY created_at DESC
LIMIT 1
"""

# Kept in sync with scripts/db_setup.py — this is the "works even if db_setup
# was never re-run" guard, same pattern as _ensure_branch_learn_table() in
# src/utils/postgres_checkpointer.py.
_CREATE_TABLE_SQL = """
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
"""

_CREATE_INDEX_SQL = [
    """
    CREATE INDEX IF NOT EXISTS idx_llm_calls_cache
        ON llm_calls (cache_key, created_at DESC)
        WHERE status = 'ok' AND cached = false
    """,
    "CREATE INDEX IF NOT EXISTS idx_llm_calls_agent ON llm_calls (agent_id, created_at DESC)",
]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Cache key ────────────────────────────────────────────────────────────────

def build_cache_key(
    *,
    model_id: str,
    system_prompt: Optional[str],
    prompt: str,
    output_type: Optional[str],
    temperature: float,
) -> str:
    """Stable hash of everything that can change the answer.

    Fields are length-prefixed rather than just newline-joined so a prompt
    containing a newline can't impersonate a different field split — i.e.
    (system="a", prompt="b") and (system="a\\nb", prompt="") hash differently.
    """
    parts = [
        ("model_id", model_id or ""),
        ("system_prompt", system_prompt or ""),
        ("prompt", prompt or ""),
        ("output_type", output_type or ""),
        ("temperature", repr(float(temperature))),
    ]
    blob = "".join(f"{name}:{len(value)}:{value}\n" for name, value in parts)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def lookup_cached_response(cache_key: str) -> dict[str, Any] | None:
    """Most recent successful, non-replayed call with this exact key.

    Global across agents and owners — mock mode is a development/replay
    feature, so a match recorded by any earlier execution counts. Returns None on
    any DB error (including "table doesn't exist yet"), which makes a cold or
    unreachable cache behave exactly like a miss.
    """
    try:
        from src.utils.postgres.db_utils import fetch_one

        row = fetch_one(_LOOKUP_SQL, (cache_key,))
        if not row or row.get("response_text") is None:
            return None
        return {
            "call_id": str(row["call_id"]),
            "response_text": row["response_text"],
            "model_id": row.get("model_id"),
        }
    except Exception:
        logger.warning("llm cache lookup failed (treating as miss)", exc_info=True)
        return None


# ── Session identity ─────────────────────────────────────────────────────────

def current_session_ids() -> dict[str, str]:
    """Agent identity from the ContextVar-bound logger.

    Falls back to agent_id="unbound" for scripts and tests —
    those calls still get recorded, just into logs/llm/{timestamp}_unbound.jsonl.
    """
    try:
        session = get_session_logger()
        if session is not None:
            return {
                "agent_id": session.agent_id or "unbound",
                "execution_id": session.execution_id or "",
                "owner_id": session.owner_id or "",
                "session_id": session.session_id or "",
            }
    except Exception:
        pass
    return {"agent_id": "unbound", "execution_id": "", "owner_id": "", "session_id": ""}


# ── Record construction ──────────────────────────────────────────────────────

def new_call_id() -> str:
    return str(uuid.uuid4())


def build_record(
    *,
    call_id: str,
    mode: str,
    model_id: str,
    output_type: Optional[str],
    temperature: float,
    cache_key: str,
    system_prompt: Optional[str],
    prompt: str,
    response_text: str = "",
    usage: dict[str, Any] | None = None,
    usage_estimated: bool = False,
    cost_usd: float | None = None,
    provider_model: str | None = None,
    response_headers: dict[str, Any] | None = None,
    raw_response: dict[str, Any] | None = None,
    status: str = "ok",
    error: str | None = None,
    latency_ms: int | None = None,
    cached: bool = False,
    source_call_id: str | None = None,
) -> dict[str, Any]:
    ids = current_session_ids()
    usage = usage or {}
    return {
        "ts": _utc_now(),
        "call_id": call_id,
        **ids,
        "mode": mode,
        "model_id": model_id,
        "provider_model": provider_model,
        "output_type": output_type,
        "temperature": float(temperature),
        "cache_key": cache_key,
        "cached": cached,
        "source_call_id": source_call_id,
        "status": status,
        "error": error,
        "latency_ms": latency_ms,
        "system_prompt": system_prompt or "",
        "prompt": prompt or "",
        "response_text": response_text or "",
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "usage_estimated": usage_estimated,
        "cost_usd": cost_usd,
        "usage": usage,
        "response_headers": response_headers or {},
        "raw_response": raw_response or {},
    }


# ── Sinks ────────────────────────────────────────────────────────────────────

def _logs_dir() -> Path:
    """Honour a test-injected logs_dir on the bound session logger."""
    try:
        session = get_session_logger()
        if session is not None:
            return Path(session.logs_dir) / "llm"
    except Exception:
        pass
    from src.utils.agent_logger import LOGS_DIR

    return LOGS_DIR / "llm"


def _write_file(record: dict[str, Any]) -> None:
    agent_key = _safe_agent_id(str(record.get("agent_id", "") or ""))
    session = get_session_logger()
    if session is not None and _safe_agent_id(session.agent_id) == agent_key:
        filename = _log_filename(agent_key, ts_prefix=session.file_ts_prefix)
        _llm_files[agent_key] = filename
    else:
        filename = _llm_files.get(agent_key)
        if filename is None:
            filename = _log_filename(agent_key, ts_prefix=_filename_timestamp())
            _llm_files[agent_key] = filename
    path = _logs_dir() / filename
    line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
    _ensure_writer_started()
    try:
        _log_queue.put_nowait((path, line))
    except queue.Full:
        logger.warning("llm log queue full; dropping call_id=%s", record.get("call_id"))


def _ensure_table(conn) -> None:
    global _table_ready
    if _table_ready:
        return
    conn.execute(_CREATE_TABLE_SQL)
    for stmt in _CREATE_INDEX_SQL:
        conn.execute(stmt)
    _table_ready = True


def _db_params(record: dict[str, Any]) -> dict[str, Any]:
    """Record -> INSERT params. JSONB columns need real JSON strings."""
    params = {k: v for k, v in record.items() if k != "ts"}
    for key in ("usage", "response_headers", "raw_response"):
        params[key] = json.dumps(params.get(key) or {}, ensure_ascii=False, default=str)
    return params


def _db_loop() -> None:
    while True:
        record = _db_queue.get()
        try:
            from src.utils.postgres.db_utils import get_connection

            with get_connection() as conn:
                _ensure_table(conn)
                conn.execute(_INSERT_SQL, _db_params(record))
        except Exception:
            logger.warning(
                "llm_calls insert failed for call_id=%s", record.get("call_id"), exc_info=True
            )
        finally:
            _db_queue.task_done()


def _ensure_db_writer_started() -> None:
    global _db_thread
    if _db_thread is not None and _db_thread.is_alive():
        return
    with _db_thread_lock:
        if _db_thread is not None and _db_thread.is_alive():
            return
        _db_thread = threading.Thread(target=_db_loop, name="eva-llm-db-writer", daemon=True)
        _db_thread.start()


def _write_db(record: dict[str, Any]) -> None:
    _ensure_db_writer_started()
    try:
        _db_queue.put_nowait(record)
    except queue.Full:
        logger.warning("llm db queue full; dropping call_id=%s", record.get("call_id"))


def record_llm_call(record: dict[str, Any]) -> None:
    """Fan a completed call out to the JSONL file and the Postgres table.

    Both sinks are non-blocking queue handoffs, and the whole function is
    wrapped so a logging bug can never surface as an LLM failure.
    """
    try:
        from src.config import settings

        if not settings.llm_call_log_enabled:
            return
        record = truncate_value(record, MAX_TEXT_CHARS)
        _write_file(record)
        if settings.llm_call_log_to_db:
            _write_db(record)
    except Exception:
        logger.warning("record_llm_call failed", exc_info=True)


def flush_pending_llm_calls(timeout: float = 5.0) -> bool:
    """Block until both sinks have drained. For tests and graceful shutdown."""
    from src.utils.agent_logger import flush_pending_logs

    deadline = time.monotonic() + timeout
    while _db_queue.unfinished_tasks > 0:
        if time.monotonic() >= deadline:
            return False
        time.sleep(0.01)
    return flush_pending_logs(timeout=max(0.0, deadline - time.monotonic()))


@atexit.register
def _drain_on_exit() -> None:
    """Both writers are daemon threads, so without this the interpreter would
    kill them mid-queue and silently lose the tail of a session's records —
    exactly the calls you most want when a run dies on an error. atexit runs
    before daemon threads are torn down, so this gets a last chance to drain.
    """
    try:
        flush_pending_llm_calls(timeout=5.0)
    except Exception:
        pass
