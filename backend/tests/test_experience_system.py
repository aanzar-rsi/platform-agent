"""Smoke tests for experience retrieve soft-fail and idle eligibility."""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["EVA_SKIP_VENV_REEXEC"] = "1"

from src.subagents.learner_agent.idle_watcher import (
    _is_run_active,
    process_idle_sessions,
    sessions_ready_to_learn,
    set_chat_active,
)
from src.subagents.learner_agent.keys import build_embed_text
from src.subagents.learner_agent.retrieve import format_experiences_for_prompt, retrieve_experiences
from src.prompts.prompt_loader import agentnode_prompt_loader


class TestEmbedKeys(unittest.TestCase):
    def test_first_call(self):
        self.assertEqual(build_embed_text("find a line"), "query: find a line")

    def test_after_tool(self):
        text = build_embed_text(
            "find a line",
            prior_task="Load the document",
            prior_tool="read_file",
        )
        self.assertIn("query: find a line", text)
        self.assertIn("prior_tool: read_file", text)
        self.assertIn("prior_task: Load the document", text)


class TestRetrieveSoftFail(unittest.TestCase):
    def test_disabled(self):
        with patch("src.subagents.learner_agent.retrieve.EXPERIENCE_ENABLED", False):
            self.assertEqual(retrieve_experiences("anything"), [])

    def test_search_error(self):
        with patch("src.subagents.learner_agent.retrieve.EXPERIENCE_ENABLED", True):
            with patch(
                "src.subagents.learner_agent.retrieve.kb.search",
                side_effect=RuntimeError("store down"),
            ):
                self.assertEqual(retrieve_experiences("query", uid="user-1"), [])

    def test_format_empty(self):
        self.assertEqual(format_experiences_for_prompt([]), "(none)")


class TestPromptInjection(unittest.TestCase):
    def test_learned_block(self):
        _system, user = agentnode_prompt_loader(
            user_query="hello",
            tools=[],
            execution_history=[],
            execution_memory_index=[],
            context_memory={"budget_tokens": 5000, "entries": [], "truncated": False},
            learned_experiences="1.\nPrefer read_file first",
        )
        self.assertIn("Previous Experiences", user)
        self.assertIn("Prefer read_file first", user)


class TestIdleEligibility(unittest.TestCase):
    def test_default_repository_path_does_not_require_fastapi(self):
        with patch("api.db.repositories.SessionRepository.list_all", return_value=[]):
            with patch.dict(sys.modules, {"fastapi": None}):
                self.assertEqual(process_idle_sessions(), [])

    def test_cli_activity_is_visible_to_watcher(self):
        set_chat_active("chat-cli", True)
        try:
            self.assertTrue(_is_run_active("chat-cli"))
        finally:
            set_chat_active("chat-cli", False)

    def test_ready_sessions(self):
        now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone.utc)
        rows = [
            {
                "agent_id": "a",
                "last_activity_at": (now - timedelta(seconds=200)).isoformat(),
                "experience_learned_at": None,
            },
            {
                "agent_id": "b",
                "last_activity_at": (now - timedelta(seconds=30)).isoformat(),
                "experience_learned_at": None,
            },
            {
                "agent_id": "c",
                "last_activity_at": (now - timedelta(seconds=200)).isoformat(),
                "experience_learned_at": (now - timedelta(seconds=10)).isoformat(),
            },
            {
                "agent_id": "d",
                "deleted": True,
                "last_activity_at": (now - timedelta(seconds=200)).isoformat(),
            },
        ]
        ready = sessions_ready_to_learn(rows, idle_seconds=120, now=now)
        self.assertEqual([r["agent_id"] for r in ready], ["a", "c"])

    def test_process_uses_requested_idle_threshold(self):
        now = datetime.now(timezone.utc)
        rows = [{
            "agent_id": "agent-1",
            "owner_id": "user-1",
            "last_activity_at": (now - timedelta(seconds=10)).isoformat(),
        }]
        learned: list[str] = []
        process_idle_sessions(
            list_sessions=lambda: rows,
            is_active=lambda _chat_id: False,
            list_leaves=lambda _chat_id: ["leaf-1"],
            leaf_learned=lambda _chat_id, _leaf: False,
            learn=lambda agent_id, **_kwargs: learned.append(agent_id) or {"status": "learned"},
            mark=lambda *_args, **_kwargs: None,
            mark_leaf=lambda *_args, **_kwargs: None,
            idle_seconds=5,
        )
        self.assertEqual(learned, ["agent-1"])

    def test_failed_leaf_is_not_marked_so_it_can_retry(self):
        now = datetime.now(timezone.utc)
        rows = [{
            "agent_id": "agent-1",
            "owner_id": "user-1",
            "last_activity_at": (now - timedelta(seconds=10)).isoformat(),
        }]
        marked: list[tuple] = []
        process_idle_sessions(
            list_sessions=lambda: rows,
            is_active=lambda _chat_id: False,
            list_leaves=lambda _chat_id: ["leaf-1"],
            leaf_learned=lambda _chat_id, _leaf: False,
            learn=lambda *_args, **_kwargs: {"status": "error"},
            mark=lambda *_args, **_kwargs: None,
            mark_leaf=lambda *args, **kwargs: marked.append((args, kwargs)),
            idle_seconds=5,
        )
        self.assertEqual(marked, [])


class TestAgentNodeHelper(unittest.TestCase):
    def test_safe_learned_never_raises(self):
        from src.agent.nodes.agentnode import _safe_learned_experiences

        with patch(
            "src.subagents.learner_agent.retrieve.retrieve_experiences",
            side_effect=RuntimeError("nope"),
        ):
            text = _safe_learned_experiences(
                "q",
                [{"task": "t", "tool_name": "read_file"}],
            )
        self.assertEqual(text, "(none)")


class TestLearnSessionSoftFail(unittest.TestCase):
    def test_missing_chat_id(self):
        from src.subagents.learner_agent.graph import learn_session

        result = learn_session("")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["stored_count"], 0)

    def test_missing_checkpoint_skips(self):
        from src.subagents.learner_agent.graph import learn_session

        result = learn_session("chat_nonexistent_xyz", uid="u1")
        self.assertIn(result["status"], ("skipped", "error"))
        self.assertEqual(result["stored_count"], 0)


class TestVectorStoreRoundtrip(unittest.TestCase):
    def test_learner_writes_private_kb_chunks(self):
        from src.subagents.learner_agent.nodes.persist import persist_node

        chunk = {"id": "exp_test1", "advice": "Call find_line", "embed_text": "query: find line",
                 "metadata": {"uid": "u1", "observed_tool": "find_line"}}
        with patch("src.subagents.learner_agent.nodes.persist.kb.write", return_value={}) as write:
            result = persist_node({"uid": "u1", "agent_id": "a1", "chunks": [chunk], "status": "pending"})
        self.assertEqual(result["stored_count"], 1)
        self.assertEqual(write.call_args.kwargs["scope"], "USER")
        self.assertEqual(write.call_args.kwargs["source_id"], "exp_test1")


if __name__ == "__main__":
    unittest.main()
