"""Tests for real usage/cost capture and EVA_MOCK_LLM_CALL replay.

The gateway is faked at `_gateway_client`, so no network and no Postgres.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["EVA_SKIP_VENV_REEXEC"] = "1"

from src.config import settings
from src.models import llm_client
from src.models.llm_client import call_llm, call_llm_stream
from src.utils import llm_logger as ll


# ── Fake gateway ─────────────────────────────────────────────────────────────

class _Usage:
    def __init__(self, prompt_tokens: int, completion_tokens: int) -> None:
        self._d = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

    def model_dump(self):
        return dict(self._d)


class _Completion:
    def __init__(self, content: str, usage: _Usage | None, model: str = "gpt-5-nano-2026") -> None:
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]
        self.usage = usage
        self.model = model

    def model_dump(self):
        return {"id": "chatcmpl-fake", "model": self.model}


class _Chunk:
    def __init__(self, delta: str | None = None, usage: _Usage | None = None) -> None:
        # The usage-only chunk the gateway appends carries no choices at all.
        self.choices = (
            [SimpleNamespace(delta=SimpleNamespace(content=delta))] if delta is not None else []
        )
        self.usage = usage


class _Raw:
    """Stand-in for the SDK's raw-response wrapper: headers + .parse()."""

    def __init__(self, parsed, headers: dict) -> None:
        self._parsed = parsed
        self.headers = headers

    def parse(self):
        return self._parsed


DEFAULT_HEADERS = {
    "x-litellm-response-cost": "0.00004212",
    "x-litellm-model-id": "gpt-5-nano-2026",
}


def fake_gateway(parsed_factory, *, headers: dict | None = None, calls: list | None = None):
    """Build a client exposing chat.completions.with_raw_response.create."""
    calls = calls if calls is not None else []

    def create(**kwargs):
        calls.append(kwargs)
        return _Raw(parsed_factory(), headers if headers is not None else dict(DEFAULT_HEADERS))

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
        )
    )
    return client, calls


class _MockBase(unittest.TestCase):
    """Captures every record the client emits instead of writing it anywhere."""

    def setUp(self):
        self.records: list[dict] = []
        with llm_client._recent_cache_lock:
            llm_client._recent_cache.clear()
        self._patches = [
            patch.object(ll, "record_llm_call", self.records.append),
            patch.object(settings, "llm_call_log_enabled", True),
        ]
        for p in self._patches:
            p.start()

    def tearDown(self):
        for p in self._patches:
            p.stop()

    def use_gateway(self, parsed_factory, *, headers=None):
        client, calls = fake_gateway(parsed_factory, headers=headers)
        patcher = patch.object(llm_client, "_gateway_client", lambda: client)
        patcher.start()
        self.addCleanup(patcher.stop)
        return calls

    def use_cache(self, hit):
        """Patch the cache lookup; `hit` may be a dict, None, or a callable."""
        fn = hit if callable(hit) else (lambda _key: hit)
        patcher = patch.object(ll, "lookup_cached_response", fn)
        patcher.start()
        self.addCleanup(patcher.stop)

    def mock_mode(self, enabled: bool):
        patcher = patch.object(settings, "mock_llm_call", enabled)
        patcher.start()
        self.addCleanup(patcher.stop)


class TestUsageAndCostCapture(_MockBase):
    def test_records_real_tokens_and_cost_not_estimates(self):
        self.mock_mode(False)
        self.use_gateway(lambda: _Completion("Paris.", _Usage(1234, 7)))

        out = call_llm("What is the capital of France?", system_prompt="Be terse.")

        self.assertEqual(out, "Paris.")
        self.assertEqual(len(self.records), 1)
        rec = self.records[0]
        self.assertEqual(rec["prompt_tokens"], 1234)
        self.assertEqual(rec["completion_tokens"], 7)
        self.assertEqual(rec["total_tokens"], 1241)
        self.assertFalse(rec["usage_estimated"])
        self.assertAlmostEqual(rec["cost_usd"], 0.00004212)
        self.assertEqual(rec["provider_model"], "gpt-5-nano-2026")
        self.assertEqual(rec["raw_response"], {"id": "chatcmpl-fake", "model": "gpt-5-nano-2026"})
        self.assertEqual(rec["status"], "ok")
        self.assertFalse(rec["cached"])

    def test_falls_back_to_estimate_when_gateway_omits_usage(self):
        self.mock_mode(False)
        self.use_gateway(lambda: _Completion("hi", None), headers={})

        call_llm("prompt")

        rec = self.records[0]
        self.assertTrue(rec["usage_estimated"])
        self.assertIsNotNone(rec["prompt_tokens"])
        self.assertIsNone(rec["cost_usd"])

    def test_stream_requests_usage_and_records_it(self):
        self.mock_mode(False)
        chunks = [_Chunk("Hel"), _Chunk("lo"), _Chunk(usage=_Usage(50, 2))]
        calls = self.use_gateway(lambda: iter(chunks))

        out = "".join(call_llm_stream("say hi"))

        self.assertEqual(out, "Hello")
        self.assertTrue(calls[0]["stream"])
        self.assertEqual(calls[0]["stream_options"], {"include_usage": True})
        rec = self.records[0]
        self.assertEqual(rec["mode"], "stream")
        self.assertEqual(rec["prompt_tokens"], 50)
        self.assertEqual(rec["completion_tokens"], 2)
        self.assertFalse(rec["usage_estimated"])
        self.assertEqual(rec["response_text"], "Hello")

    def test_stream_retries_once_without_stream_options_if_rejected(self):
        self.mock_mode(False)
        attempts = []

        def create(**kwargs):
            attempts.append(kwargs)
            if "stream_options" in kwargs:
                raise TypeError("unsupported parameter: stream_options")
            return _Raw(iter([_Chunk("ok")]), dict(DEFAULT_HEADERS))

        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
            )
        )
        with patch.object(llm_client, "_gateway_client", lambda: client):
            out = "".join(call_llm_stream("hi"))

        self.assertEqual(out, "ok")
        self.assertEqual(len(attempts), 2)
        self.assertNotIn("stream_options", attempts[1])
        self.assertTrue(self.records[0]["usage_estimated"])

    def test_unrelated_stream_error_is_not_retried(self):
        self.mock_mode(False)
        attempts = []

        def create(**kwargs):
            attempts.append(kwargs)
            raise RuntimeError("gateway exploded")

        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
            )
        )
        with patch.object(llm_client, "_gateway_client", lambda: client):
            with self.assertRaises(RuntimeError):
                list(call_llm_stream("hi"))

        self.assertEqual(len(attempts), 1)
        self.assertEqual(self.records[0]["status"], "error")
        self.assertIn("gateway exploded", self.records[0]["error"])


class TestErrorsAreRecorded(_MockBase):
    def test_failed_sync_call_records_an_error_row_and_reraises(self):
        self.mock_mode(False)

        def create(**kwargs):
            raise RuntimeError("429 rate limited")

        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(with_raw_response=SimpleNamespace(create=create))
            )
        )
        with patch.object(llm_client, "_gateway_client", lambda: client):
            with self.assertRaises(RuntimeError):
                call_llm("boom")

        rec = self.records[0]
        self.assertEqual(rec["status"], "error")
        self.assertIn("429", rec["error"])
        self.assertFalse(rec["cached"])

    def test_unparseable_json_records_exactly_one_error_row(self):
        self.mock_mode(False)
        self.use_gateway(lambda: _Completion("not json at all", _Usage(5, 5)))

        with self.assertRaises(Exception):
            call_llm("give me json", output_type="json")

        self.assertEqual(len(self.records), 1)
        self.assertEqual(self.records[0]["status"], "error")


class TestMockModeOff(_MockBase):
    def test_identical_calls_both_hit_the_gateway(self):
        self.mock_mode(False)
        calls = self.use_gateway(lambda: _Completion("4", _Usage(3, 1)))
        self.use_cache({"call_id": "should-never-be-used", "response_text": "cached!"})

        self.assertEqual(call_llm("2+2"), "4")
        self.assertEqual(call_llm("2+2"), "4")
        self.assertEqual(len(calls), 2)


class TestMockModeOn(_MockBase):
    HIT = {
        "call_id": "33333333-3333-3333-3333-333333333333",
        "response_text": "cached answer",
        "model_id": "gpt-5-nano",
    }

    def test_cache_hit_skips_the_gateway_entirely(self):
        self.mock_mode(True)
        calls = self.use_gateway(lambda: _Completion("live answer", _Usage(1, 1)))
        self.use_cache(self.HIT)

        out = call_llm("2+2")

        self.assertEqual(out, "cached answer")
        self.assertEqual(calls, [], "gateway was called despite a cache hit")

    def test_replay_is_recorded_as_free_and_traceable(self):
        self.mock_mode(True)
        self.use_gateway(lambda: _Completion("live", _Usage(1, 1)))
        self.use_cache(self.HIT)

        call_llm("2+2")

        rec = self.records[0]
        self.assertTrue(rec["cached"])
        self.assertEqual(rec["cost_usd"], 0.0)
        self.assertEqual(rec["source_call_id"], self.HIT["call_id"])
        self.assertEqual(rec["response_text"], "cached answer")

    def test_json_replay_returns_a_parsed_dict(self):
        self.mock_mode(True)
        self.use_gateway(lambda: _Completion("{}", _Usage(1, 1)))
        self.use_cache({**self.HIT, "response_text": '{"answer": 4}'})

        out = call_llm("2+2", output_type="json")

        self.assertEqual(out, {"answer": 4})

    def test_cold_cache_falls_through_to_a_real_call(self):
        self.mock_mode(True)
        calls = self.use_gateway(lambda: _Completion("live answer", _Usage(1, 1)))
        self.use_cache(None)

        self.assertEqual(call_llm("2+2"), "live answer")
        self.assertEqual(len(calls), 1)

    def test_lookup_uses_the_full_call_signature(self):
        """Same prompt at a different temperature must miss."""
        self.mock_mode(True)
        seen_keys = []
        self.use_gateway(lambda: _Completion("live", _Usage(1, 1)))
        self.use_cache(lambda key: (seen_keys.append(key), None)[1])

        call_llm("2+2", temperature=0.7)
        call_llm("2+2", temperature=0.2)
        call_llm("2+2", temperature=0.7)

        # Third call is served from in-process replay cache, so DB lookup is skipped.
        self.assertEqual(len(seen_keys), 2)
        self.assertNotEqual(seen_keys[0], seen_keys[1])

    def test_output_type_instruction_is_part_of_the_key(self):
        """A text call and a json call with the same prompt must not collide —
        the json system-prompt suffix has to be inside the hash."""
        self.mock_mode(True)
        seen_keys = []
        self.use_gateway(lambda: _Completion('{"a":1}', _Usage(1, 1)))
        self.use_cache(lambda key: (seen_keys.append(key), None)[1])

        call_llm("same prompt")
        call_llm("same prompt", output_type="json")

        self.assertNotEqual(seen_keys[0], seen_keys[1])

    def test_second_identical_call_replays_without_waiting_for_db_flush(self):
        self.mock_mode(True)
        calls = self.use_gateway(lambda: _Completion("live answer", _Usage(2, 2)))
        self.use_cache(None)

        first = call_llm("no flush replay", system_prompt="sys", temperature=0.3)
        second = call_llm("no flush replay", system_prompt="sys", temperature=0.3)

        self.assertEqual(first, "live answer")
        self.assertEqual(second, "live answer")
        self.assertEqual(len(calls), 1, "second call should replay from in-process cache")
        self.assertFalse(self.records[0]["cached"])
        self.assertTrue(self.records[1]["cached"])


class TestStreamReplay(_MockBase):
    HIT = {
        "call_id": "44444444-4444-4444-4444-444444444444",
        "response_text": "x" * 100,
        "model_id": "gpt-5-nano",
    }

    def test_replays_in_chunks_that_reassemble_exactly(self):
        self.mock_mode(True)
        calls = self.use_gateway(lambda: iter([_Chunk("live")]))
        self.use_cache(self.HIT)

        chunks = list(call_llm_stream("say x"))

        self.assertEqual(calls, [], "gateway was called despite a cache hit")
        self.assertGreater(len(chunks), 1, "replay must stream, not emit one blob")
        self.assertEqual("".join(chunks), self.HIT["response_text"])

    def test_replay_chunk_size_is_small_for_progressive_flush(self):
        self.assertEqual(llm_client._REPLAY_CHUNK_CHARS, 24)

    def test_short_response_still_yields(self):
        self.mock_mode(True)
        self.use_gateway(lambda: iter([_Chunk("live")]))
        self.use_cache({**self.HIT, "response_text": "hi"})

        self.assertEqual(list(call_llm_stream("x")), ["hi"])

    def test_stream_replay_is_recorded(self):
        self.mock_mode(True)
        self.use_gateway(lambda: iter([_Chunk("live")]))
        self.use_cache(self.HIT)

        list(call_llm_stream("say x"))

        rec = self.records[0]
        self.assertEqual(rec["mode"], "stream")
        self.assertTrue(rec["cached"])
        self.assertEqual(rec["source_call_id"], self.HIT["call_id"])


class TestSandboxStubCompatibility(unittest.TestCase):
    def test_public_signatures_stayed_stub_compatible(self):
        """Wrappers sometimes replace these with
        `(prompt, system_prompt=None, temperature=0.0, **_k)`, so no caller may
        depend on a positional arg beyond `prompt`."""
        import inspect

        sync_params = list(inspect.signature(call_llm).parameters)
        self.assertEqual(sync_params[:2], ["prompt", "system_prompt"])
        self.assertIn("temperature", sync_params)
        stream_params = list(inspect.signature(call_llm_stream).parameters)
        self.assertEqual(stream_params[:2], ["prompt", "system_prompt"])
        self.assertIn("temperature", stream_params)


if __name__ == "__main__":
    unittest.main(verbosity=2)
