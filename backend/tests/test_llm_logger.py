"""Tests for the LLM call recorder and its mock-replay cache key.

No live Postgres required — the DB sink is patched out everywhere.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["EVA_SKIP_VENV_REEXEC"] = "1"

from src.config import settings
from src.utils import agent_logger as al
from src.utils import llm_logger as ll
from src.utils.agent_logger import bind_session_logger, reset_session_logger
from src.utils.llm_logger import (
    build_cache_key,
    build_record,
    current_session_ids,
    flush_pending_llm_calls,
    lookup_cached_response,
    record_llm_call,
)

_BASE = dict(
    model_id="gpt-5-nano",
    system_prompt="you are helpful",
    prompt="what is 2+2",
    output_type="text",
    temperature=0.7,
)


class TestCacheKey(unittest.TestCase):
    def test_stable_across_calls(self):
        self.assertEqual(build_cache_key(**_BASE), build_cache_key(**_BASE))

    def test_sensitive_to_every_field(self):
        base = build_cache_key(**_BASE)
        for field, other in (
            ("model_id", "gpt-4o"),
            ("system_prompt", "you are terse"),
            ("prompt", "what is 3+3"),
            ("output_type", "json"),
            ("temperature", 0.0),
        ):
            with self.subTest(field=field):
                changed = build_cache_key(**{**_BASE, field: other})
                self.assertNotEqual(base, changed, f"{field} did not affect the key")

    def test_none_system_prompt_is_empty_string(self):
        a = build_cache_key(**{**_BASE, "system_prompt": None})
        b = build_cache_key(**{**_BASE, "system_prompt": ""})
        self.assertEqual(a, b)

    def test_field_boundaries_cannot_be_forged(self):
        """A newline inside one field must not be able to impersonate the
        boundary between two fields."""
        a = build_cache_key(**{**_BASE, "system_prompt": "a", "prompt": "b"})
        b = build_cache_key(**{**_BASE, "system_prompt": "a\nb", "prompt": ""})
        self.assertNotEqual(a, b)

    def test_temperature_int_and_float_match(self):
        a = build_cache_key(**{**_BASE, "temperature": 1})
        b = build_cache_key(**{**_BASE, "temperature": 1.0})
        self.assertEqual(a, b)


class TestSessionIdentity(unittest.TestCase):
    def test_unbound_falls_back(self):
        ids = current_session_ids()
        self.assertEqual(ids["agent_id"], "unbound")

    def test_bound_picks_up_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(al, "AGENT_LOG_ENABLED", True):
                token = bind_session_logger(
                    "agent_ids", execution_id="e1", owner_id="u1", session_id="s1", logs_dir=Path(tmp)
                )
                ids = current_session_ids()
                reset_session_logger(token)
        self.assertEqual(ids, {"agent_id": "agent_ids", "execution_id": "e1", "owner_id": "u1", "session_id": "s1"})


def _record_kwargs(**overrides):
    kwargs = dict(
        call_id="11111111-1111-1111-1111-111111111111",
        mode="sync",
        model_id="gpt-5-nano",
        output_type="text",
        temperature=0.7,
        cache_key="deadbeef",
        system_prompt="sys",
        prompt="hello",
        response_text="world",
        usage={"prompt_tokens": 11, "completion_tokens": 3, "total_tokens": 14},
        cost_usd=0.000123,
        provider_model="gpt-5-nano-2026",
        response_headers={"x-litellm-response-cost": "0.000123"},
        raw_response={"id": "chatcmpl-abc"},
        latency_ms=42,
    )
    kwargs.update(overrides)
    return kwargs


class TestRecordLlmCall(unittest.TestCase):
    def _write_and_read(self, agent_id, record_overrides=None, db_sink=None):
        """Record one call under a temp logs dir and return the parsed JSONL rows."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            sink = db_sink if db_sink is not None else (lambda rec: None)
            with patch.object(al, "AGENT_LOG_ENABLED", True), patch.object(ll, "_write_db", sink):
                token = bind_session_logger(agent_id, execution_id="e", owner_id="u", logs_dir=tmp_path)
                record_llm_call(build_record(**_record_kwargs(**(record_overrides or {}))))
                reset_session_logger(token)
            self.assertTrue(flush_pending_llm_calls(timeout=5.0), "sinks did not drain")
            path = tmp_path / "llm" / f"{agent_id}.jsonl"
            if not path.exists():
                return None
            return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def test_writes_one_full_record_to_its_own_session_file(self):
        rows = self._write_and_read("chat_rec")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["agent_id"], "chat_rec")
        self.assertEqual(row["execution_id"], "e")
        self.assertEqual(row["mode"], "sync")
        self.assertEqual(row["status"], "ok")
        self.assertFalse(row["cached"])
        # Real usage, flattened for SQL plus kept whole in `usage`
        self.assertEqual(row["prompt_tokens"], 11)
        self.assertEqual(row["completion_tokens"], 3)
        self.assertEqual(row["total_tokens"], 14)
        self.assertFalse(row["usage_estimated"])
        self.assertAlmostEqual(row["cost_usd"], 0.000123)
        self.assertEqual(row["raw_response"], {"id": "chatcmpl-abc"})
        self.assertEqual(row["response_text"], "world")

    def test_separate_file_per_session(self):
        rows_a = self._write_and_read("chat_a")
        rows_b = self._write_and_read("chat_b")
        self.assertEqual(rows_a[0]["agent_id"], "chat_a")
        self.assertEqual(rows_b[0]["agent_id"], "chat_b")

    def test_db_sink_failure_does_not_propagate_or_lose_the_file_write(self):
        def _boom(_record):
            raise RuntimeError("postgres is down")

        rows = self._write_and_read("chat_dbfail", db_sink=_boom)  # must not raise
        self.assertEqual(len(rows), 1)

    def test_db_sink_receives_the_record(self):
        seen = []
        self._write_and_read("chat_dbok", db_sink=seen.append)
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0]["cache_key"], "deadbeef")

    def test_oversized_text_is_truncated(self):
        with patch.object(ll, "MAX_TEXT_CHARS", 50):
            rows = self._write_and_read("chat_big", {"prompt": "Z" * 500})
        self.assertIn("truncated", rows[0]["prompt"])

    def test_disabled_writes_nothing(self):
        with patch.object(settings, "llm_call_log_enabled", False):
            rows = self._write_and_read("chat_off")
        self.assertIsNone(rows)

    def test_db_disabled_still_writes_the_file(self):
        seen = []
        with patch.object(settings, "llm_call_log_to_db", False):
            rows = self._write_and_read("chat_nodb", db_sink=seen.append)
        self.assertEqual(len(rows), 1)
        self.assertEqual(seen, [])


class TestRecordShape(unittest.TestCase):
    def test_missing_usage_leaves_token_columns_null(self):
        record = build_record(**_record_kwargs(usage=None))
        self.assertIsNone(record["prompt_tokens"])
        self.assertEqual(record["usage"], {})

    def test_db_params_serialises_jsonb_columns(self):
        params = ll._db_params(build_record(**_record_kwargs()))
        self.assertNotIn("ts", params)
        for key in ("usage", "response_headers", "raw_response"):
            self.assertIsInstance(params[key], str)
            json.loads(params[key])  # must be valid JSON for psycopg


class TestLookupSoftFails(unittest.TestCase):
    def test_db_error_is_a_miss_not_an_exception(self):
        import src.utils.postgres.db_utils as db

        with patch.object(db, "fetch_one", side_effect=RuntimeError("no postgres")):
            self.assertIsNone(lookup_cached_response("whatever"))

    def test_no_row_is_a_miss(self):
        import src.utils.postgres.db_utils as db

        with patch.object(db, "fetch_one", return_value=None):
            self.assertIsNone(lookup_cached_response("whatever"))

    def test_hit_is_normalised(self):
        import src.utils.postgres.db_utils as db

        row = {"call_id": "22222222-2222-2222-2222-222222222222", "response_text": "hi", "model_id": "m"}
        with patch.object(db, "fetch_one", return_value=row):
            hit = lookup_cached_response("whatever")
        self.assertEqual(hit["call_id"], row["call_id"])
        self.assertEqual(hit["response_text"], "hi")


if __name__ == "__main__":
    unittest.main(verbosity=2)
