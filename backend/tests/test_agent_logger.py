"""Smoke tests for per-agent session logger."""

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

from src.utils import agent_logger as al
from src.utils.agent_logger import (
    bind_session_logger,
    flush_pending_logs,
    get_session_logger,
    log_agent_decision,
    log_event,
    log_llm_request,
    log_llm_response,
    log_route,
    log_run_end,
    log_run_start,
    log_tool,
    reset_session_logger,
    truncate_value,
)


class TestTruncate(unittest.TestCase):
    def test_short_string_unchanged(self):
        self.assertEqual(truncate_value("hi", max_chars=10), "hi")

    def test_long_string_truncated(self):
        out = truncate_value("abcdefghij", max_chars=5)
        self.assertTrue(out.startswith("abcde"))
        self.assertIn("truncated", out)

    def test_nested_dict(self):
        out = truncate_value({"a": "x" * 20, "b": 1}, max_chars=5)
        self.assertIn("truncated", out["a"])
        self.assertEqual(out["b"], 1)


class TestSessionLoggerBind(unittest.TestCase):
    def test_bind_write_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(al, "AGENT_LOG_ENABLED", True):
                token = bind_session_logger(
                    "agent_test_1",
                    execution_id="execution_1",
                    owner_id="u1",
                    session_id="session_1",
                    logs_dir=tmp_path,
                )
                self.assertIsNotNone(get_session_logger())
                log_run_start(query="hello")
                log_llm_request(prompt="p", system_prompt="s", model_id="m")
                log_llm_response(response="out", model_id="m")
                log_agent_decision(action="tool", tool_name="read_file", reasoning="need file")
                log_tool("start", tool_name="read_file")
                log_tool("end", tool_name="read_file", success=True, result={"ok": True})
                log_route(action="tool", destination="tool_node")
                log_run_end(stopped=False)
                reset_session_logger(token)
                self.assertIsNone(get_session_logger())

            self.assertTrue(flush_pending_logs(timeout=5.0), "writer queue did not drain in time")
            path = tmp_path / "agent_test_1.jsonl"
            self.assertTrue(path.exists())
            lines = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
            events = [row["event"] for row in lines]
            self.assertEqual(events[0], "run.start")
            self.assertIn("llm.request", events)
            self.assertIn("llm.response", events)
            self.assertIn("agent.decision", events)
            self.assertIn("tool.start", events)
            self.assertIn("tool.end", events)
            self.assertIn("route", events)
            self.assertEqual(events[-1], "run.end")
            for row in lines:
                self.assertEqual(row["agent_id"], "agent_test_1")
                self.assertEqual(row["execution_id"], "execution_1")
                self.assertEqual(row["owner_id"], "u1")
                self.assertEqual(row["session_id"], "session_1")
                self.assertFalse({"chat_id", "run_id", "coreid", "log_id"} & row.keys())

    def test_unbound_log_is_noop(self):
        with patch.object(al, "AGENT_LOG_ENABLED", True):
            # ensure unbound
            self.assertIsNone(get_session_logger())
            log_event("should_not_write", x=1)  # must not raise

    def test_disabled_bind_is_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(al, "AGENT_LOG_ENABLED", False):
                token = bind_session_logger("chat_x", logs_dir=Path(tmp))
                self.assertIsNone(token)
                self.assertIsNone(get_session_logger())
                log_event("noop")
            self.assertFalse((Path(tmp) / "chat_x.jsonl").exists())

    def test_safe_agent_id_sanitizes_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(al, "AGENT_LOG_ENABLED", True):
                token = bind_session_logger(
                    "chat/../evil id!",
                    logs_dir=tmp_path,
                )
                log_event("ping")
                reset_session_logger(token)
            self.assertTrue(flush_pending_logs(timeout=5.0), "writer queue did not drain in time")
            files = list(tmp_path.glob("*.jsonl"))
            self.assertEqual(len(files), 1)
            # Must stay a single basename under logs_dir (no path separators)
            self.assertEqual(files[0].parent, tmp_path)
            self.assertNotIn("/", files[0].name)
            self.assertNotIn("\\", files[0].name)
            self.assertTrue(files[0].name.endswith(".jsonl"))

    def test_payload_truncation_on_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(al, "AGENT_LOG_ENABLED", True):
                token = bind_session_logger("chat_trunc", logs_dir=tmp_path)
                session = get_session_logger()
                session.max_field_chars = 20
                log_event("big", body="Z" * 100)
                reset_session_logger(token)
            self.assertTrue(flush_pending_logs(timeout=5.0), "writer queue did not drain in time")
            row = json.loads((tmp_path / "chat_trunc.jsonl").read_text(encoding="utf-8").strip())
            self.assertIn("truncated", row["payload"]["body"])


class TestAsyncWriterDoesNotBlockCaller(unittest.TestCase):
    def test_slow_disk_write_does_not_block_logging_call(self):
        """A slow/stalled write to one chat's file must not delay log() calls
        for the SAME or a DIFFERENT chat — this is the core fix for the
        previous global-lock contention issue."""
        import time as _time

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with patch.object(al, "AGENT_LOG_ENABLED", True):
                slow_token = bind_session_logger("chat_slow", logs_dir=tmp_path)
                slow_session = get_session_logger()
                real_open = Path.open

                def _slow_open(self, *args, **kwargs):
                    _time.sleep(0.4)
                    return real_open(self, *args, **kwargs)

                with patch.object(Path, "open", _slow_open):
                    log_event("slow_write")  # queued; writer thread will stall on this
                    _time.sleep(0.05)  # give the writer thread a chance to pick it up first

                    reset_session_logger(slow_token)
                    fast_token = bind_session_logger("chat_fast", logs_dir=tmp_path)
                    start = _time.monotonic()
                    log_event("fast_write")
                    elapsed = _time.monotonic() - start
                    reset_session_logger(fast_token)

                self.assertLess(elapsed, 0.2, "log_event() call blocked on an unrelated slow write")
                flush_pending_logs(timeout=3.0)

    def test_flush_pending_logs_times_out_gracefully(self):
        # No queued items -> should report fully drained immediately.
        self.assertTrue(flush_pending_logs(timeout=0.5))


class TestHelpersNeverRaise(unittest.TestCase):
    def test_reset_none(self):
        reset_session_logger(None)  # must not raise

    def test_write_failure_soft(self):
        with patch.object(al, "AGENT_LOG_ENABLED", True):
            token = bind_session_logger("chat_fail")
            session = get_session_logger()
            with patch.object(session, "path") as mock_path:
                mock_path.open.side_effect = OSError("disk full")
                # SessionLogger.log catches; log_event also catches
                log_event("x", a=1)
                flush_pending_logs(timeout=2.0)
            reset_session_logger(token)


if __name__ == "__main__":
    unittest.main(verbosity=2)
