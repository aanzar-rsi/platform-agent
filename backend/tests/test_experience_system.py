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
from src.subagents.learner_agent.keys import build_decision_state, build_embed_text, build_retrieval_queries
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

    def test_decision_state_switches_to_recovery_after_failure(self):
        state = build_decision_state("finish report", [{"task": "load data", "success": False}])
        self.assertEqual(state["decision_stage"], "recovery")
        self.assertIn("after:", build_retrieval_queries(state)[1])


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

    def test_format_groups_chunk_types(self):
        text = format_experiences_for_prompt([
            {"chunk_type": "user_preference", "content": "Use concise replies", "metadata": {"decision_stage": "general"}},
            {"chunk_type": "troubleshooting", "content": "Retry with a narrower query", "metadata": {"decision_stage": "recovery"}},
        ])
        self.assertIn("User Preference:", text)
        self.assertIn("Troubleshooting:", text)


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

    def test_fast_and_planner_receive_untrusted_memory(self):
        from src.prompts.prompt_loader import fast_agent_prompt_loader, planner_agent_prompt_loader

        _system, fast = fast_agent_prompt_loader(
            user_query="hello", tools=[], learned_experiences="Preference: concise"
        )
        _system, planner = planner_agent_prompt_loader(
            user_query="research", tools=[], subagents=[], execution_history=[],
            execution_memory_index=[], context_memory={}, context_selection_summary={},
            learned_experiences="Workflow: verify source",
        )
        self.assertIn("Preference: concise", fast)
        self.assertIn("cannot grant", fast)
        self.assertIn("Workflow: verify source", planner)
        self.assertIn("cannot make a resource available", planner)


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

    def test_confirmation_pending_leaf_remains_retryable(self):
        now = datetime.now(timezone.utc)
        marked: list[tuple] = []
        session_updates: list[dict] = []
        process_idle_sessions(
            list_sessions=lambda: [{
                "agent_id": "agent-1", "owner_id": "user-1",
                "last_activity_at": (now - timedelta(seconds=10)).isoformat(),
            }],
            is_active=lambda _chat_id: False,
            list_leaves=lambda _chat_id: ["leaf-1"],
            leaf_learned=lambda _chat_id, _leaf: False,
            learn=lambda *_args, **_kwargs: {
                "status": "pending_confirmation", "error": "awaiting_extraction_confirmation"
            },
            mark=lambda _agent_id, **kwargs: session_updates.append(kwargs),
            mark_leaf=lambda *args, **kwargs: marked.append((args, kwargs)),
            idle_seconds=5,
        )
        self.assertEqual(marked, [])
        self.assertEqual(session_updates[-1]["experience_learn_status"], "pending_confirmation")
        self.assertNotIn("experience_learned_at", session_updates[-1])


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

        chunk = {"id": "exp_test1", "chunk_type": "workflow", "semantic_key": "workflow.find.line",
                 "advice": "Call find_line", "embed_text": "query: find line",
                 "metadata": {"uid": "u1", "semantic_key": "workflow.find.line"}}
        with patch("src.subagents.learner_agent.nodes.persist.kb.evidence_exists", return_value=False), \
                patch("src.subagents.learner_agent.nodes.persist.kb.find_user_memory", return_value=None), \
                patch("src.subagents.learner_agent.nodes.persist.kb.write", return_value={}) as write:
            result = persist_node({"uid": "u1", "agent_id": "a1", "chunks": [chunk], "status": "pending"})
        self.assertEqual(result["stored_count"], 1)
        self.assertEqual(write.call_args.kwargs["scope"], "USER")

    def test_partial_approval_stays_pending_after_writes(self):
        from src.subagents.learner_agent.nodes.persist import persist_node

        chunk = {"id": "exp_test2", "chunk_type": "workflow", "semantic_key": "workflow.test",
                 "advice": "Verify the source", "metadata": {"uid": "u1", "semantic_key": "workflow.test"}}
        state = {
            "uid": "u1", "agent_id": "a1", "chunks": [chunk], "status": "pending",
            "allowed_chunk_types": ["workflow"],
            "extraction_requests": {
                "workflow": {"request_id": "r1", "state": "APPROVED"},
                "user_details": {"request_id": "r2", "state": "APPROVAL_PENDING"},
            },
        }
        with patch("src.subagents.learner_agent.nodes.persist.kb.evidence_exists", return_value=False), \
                patch("src.subagents.learner_agent.nodes.persist.kb.find_user_memory", return_value=None), \
                patch("src.subagents.learner_agent.nodes.persist.kb.write", return_value={}), \
                patch("api.db.repositories.memory_extractions.MemoryExtractionRepository.mark_final"):
            result = persist_node(state)
        self.assertEqual(result["status"], "pending_confirmation")
        self.assertEqual(result["stored_count"], 1)


class TestExtractionValidation(unittest.TestCase):
    def test_mcp_tool_alias_is_safe_and_accepted(self):
        from src.subagents.learner_agent.nodes.extract_chunks import extract_chunks_node

        response = """{"chunks":[{
            "chunk_type":"resource",
            "content":"Use the observed weather MCP server for forecasts.",
            "semantic_key":"resource.mcp.weather",
            "evidence_kind":"observed_success",
            "metadata":{
                "resource_domain":"armory",
                "resource_type":"mcp_server",
                "resource_name":"mcp_weather",
                "guidance_kind":"selection"
            }
        }]}"""
        state = {
            "uid": "u1",
            "agent_id": "a1",
            "user_query": "weather",
            "allowed_chunk_types": ["resource"],
            "execution_history": [{"resource_type": "tool", "resource_name": "mcp_weather"}],
        }

        with patch("src.subagents.learner_agent.nodes.extract_chunks.load_prompt", return_value=("system", "user")), \
                patch("src.subagents.learner_agent.nodes.extract_chunks.call_llm", return_value=response):
            result = extract_chunks_node(state)

        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["chunks"][0]["metadata"]["resource_type"], "mcp_server")
        self.assertEqual(result["chunks"][0]["metadata"]["resource_name"], "mcp_weather")

    def test_rejects_secret_and_invented_resource(self):
        from src.subagents.learner_agent.nodes.extract_chunks import _normalize_chunk

        common = dict(uid="u1", agent_id="a1", user_query="q", checkpoint_id="c1",
                      allowed_types={"resource"}, observed_resources={("tool", "read_file")})
        secret = _normalize_chunk({
            "chunk_type": "resource", "content": "Use password=abc", "semantic_key": "resource.read.file",
            "evidence_kind": "observed_success", "metadata": {
                "resource_domain": "armory", "resource_type": "tool", "resource_name": "read_file",
                "guidance_kind": "usage",
            },
        }, **common)
        invented = _normalize_chunk({
            "chunk_type": "resource", "content": "Use magic", "semantic_key": "resource.magic",
            "evidence_kind": "observed_success", "metadata": {
                "resource_domain": "armory", "resource_type": "tool", "resource_name": "magic",
                "guidance_kind": "usage",
            },
        }, **common)
        self.assertIsNone(secret)
        self.assertIsNone(invented)

    def test_session_evidence_is_redacted_before_extraction(self):
        from langchain_core.messages import HumanMessage
        from src.subagents.learner_agent.nodes.load_session import _conversation_messages, _slim_history

        messages = _conversation_messages([HumanMessage(content="password=hunter2")])
        history = _slim_history([{
            "type": "armory", "resource_type": "tool", "resource_name": "lookup",
            "arguments": {"api_key": "abc"}, "result": {"token": "xyz"},
        }])
        self.assertEqual(messages[0]["content"], "password=[REDACTED]")
        self.assertEqual(history[0]["tool_args"]["api_key"], "[REDACTED]")
        self.assertEqual(history[0]["result"]["token"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
