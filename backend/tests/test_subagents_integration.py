"""End-to-end tests for EVA subagent integration.

Covers: registry catalog, subagent_node (happy path / unknown / exception / uid),
progress streaming via ContextVar, catalog API, agent_runtime event fan-out
(no duplicate started), and planner prompt wiring for agent_call.
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["EVA_SKIP_VENV_REEXEC"] = "1"
os.environ.setdefault("EVA_AGENT_LOG_ENABLED", "true")


class TestSubagentRegistry(unittest.TestCase):
    def test_registry_catalog_is_consistent(self):
        from src.subagents.registry import SUBAGENT_MAP, SUBAGENTS

        self.assertEqual(set(SUBAGENT_MAP), {s.name for s in SUBAGENTS})
        for spec in SUBAGENTS:
            self.assertTrue(spec.description)
            self.assertTrue(spec.when_to_use)
            self.assertTrue(callable(spec.adapter))

    def test_learner_agent_not_registered(self):
        from src.subagents.registry import SUBAGENT_MAP

        self.assertNotIn("learner_agent", SUBAGENT_MAP)
        self.assertNotIn("learner", SUBAGENT_MAP)

    def test_subagentnode_registry_matches_catalog(self):
        from src.agent.nodes.subagentnode import _SUBAGENT_REGISTRY
        from src.subagents.registry import SUBAGENT_MAP

        self.assertEqual(set(_SUBAGENT_REGISTRY), set(SUBAGENT_MAP))


class TestSubagentNode(unittest.TestCase):
    def _state(self, agent_name: str, task: str = "do the thing", **extra):
        return {
            "next_step": {"action": "subagent", "agent_name": agent_name, "task": task},
            "execution_history": [],
            "execution_memory": {},
            "context_memory": None,
            "preloaded_context": extra.get("preloaded_context", {}),
            "messages": [],
        }

    def test_unknown_subagent(self):
        from src.agent.nodes.subagentnode import subagent_node

        out = subagent_node(self._state("does_not_exist"))
        self.assertEqual(len(out["execution_history"]), 1)
        entry = out["execution_history"][0]
        self.assertEqual(entry["type"], "subagent")
        self.assertFalse(entry["success"])
        self.assertIn("Unknown sub-agent", entry["result"])
        self.assertIn("No sub-agents are registered.", entry["result"])
        self.assertIn("Subagent 'does_not_exist' result:", out["messages"][0].content)

    def test_adapter_exception_is_soft_fail(self):
        from src.agent.nodes import subagentnode as mod

        def boom(_task, _ctx):
            raise RuntimeError("kaboom")

        with patch.dict(mod._SUBAGENT_REGISTRY, {"boom": boom}, clear=False):
            out = mod.subagent_node(self._state("boom"))
        entry = out["execution_history"][0]
        self.assertFalse(entry["success"])
        self.assertIn("kaboom", entry["result"])

    def test_happy_path_and_uid_injection(self):
        from src.agent.nodes import subagentnode as mod

        seen = {}

        def echo(task, ctx):
            seen["task"] = task
            seen["ctx"] = dict(ctx)
            return f"OK:{task}"

        with patch.dict(mod._SUBAGENT_REGISTRY, {"echo": echo}, clear=False):
            out = mod.subagent_node(
                self._state("echo", task="build me a thing"),
                config={"configurable": {"owner_id": "user-42"}},
            )

        self.assertEqual(seen["task"], "build me a thing")
        self.assertEqual(seen["ctx"].get("uid"), "user-42")
        entry = out["execution_history"][0]
        self.assertTrue(entry["success"])
        self.assertEqual(entry["result"], "OK:build me a thing")
        self.assertEqual(entry["key"], "subagent_1")
        self.assertIn("subagent_1", out["execution_memory"])

    def test_uid_not_overwritten_if_already_present(self):
        from src.agent.nodes import subagentnode as mod

        seen = {}

        def echo(task, ctx):
            seen["ctx"] = dict(ctx)
            return "ok"

        with patch.dict(mod._SUBAGENT_REGISTRY, {"echo": echo}, clear=False):
            mod.subagent_node(
                self._state("echo", preloaded_context={"uid": "pre-set"}),
                config={"configurable": {"user_id": "user-42"}},
            )
        self.assertEqual(seen["ctx"]["uid"], "pre-set")

    def test_tool_args_forwarded_as_parameters(self):
        """Extra <parameters> on an agent_call reach the sub-agent as context['parameters'],
        so it can resolve things (e.g. clarification answers) in this same call."""
        from src.agent.nodes import subagentnode as mod

        seen = {}

        def echo(task, ctx):
            seen["ctx"] = dict(ctx)
            return "ok"

        state = self._state("echo")
        state["next_step"]["tool_args"] = {"output_format": "json"}
        with patch.dict(mod._SUBAGENT_REGISTRY, {"echo": echo}, clear=False):
            mod.subagent_node(state)
        self.assertEqual(seen["ctx"]["parameters"], {"output_format": "json"})

    def test_second_call_same_turn_is_allowed(self):
        from src.agent.nodes import subagentnode as mod

        calls = []

        def echo(task, ctx):
            calls.append(task)
            return "first result"

        with patch.dict(mod._SUBAGENT_REGISTRY, {"echo": echo}, clear=False):
            state = self._state("echo", task="attempt 1")
            state["messages"] = [HumanMessage(content="please build it")]
            out1 = mod.subagent_node(state)

            state2 = dict(state)
            state2["execution_history"] = out1["execution_history"]
            state2["execution_memory"] = out1["execution_memory"]
            state2["next_step"] = {"action": "subagent", "agent_name": "echo", "task": "attempt 2"}
            out2 = mod.subagent_node(state2)

        self.assertEqual(calls, ["attempt 1", "attempt 2"])
        self.assertTrue(out2["execution_history"][-1]["success"])

    def test_retry_allowed_in_a_later_turn(self):
        """A follow-up human message starts a new turn, so a retry is allowed again."""
        from src.agent.nodes import subagentnode as mod

        calls = []

        def echo(task, ctx):
            calls.append(task)
            return "result"

        with patch.dict(mod._SUBAGENT_REGISTRY, {"echo": echo}, clear=False):
            state = self._state("echo", task="attempt 1")
            state["messages"] = [HumanMessage(content="please build it")]
            out1 = mod.subagent_node(state)

            state2 = dict(state)
            state2["execution_history"] = out1["execution_history"]
            state2["execution_memory"] = out1["execution_memory"]
            state2["messages"] = [
                HumanMessage(content="please build it"),
                HumanMessage(content="ok please try again"),
            ]
            state2["next_step"] = {"action": "subagent", "agent_name": "echo", "task": "attempt 2"}
            out2 = mod.subagent_node(state2)

        self.assertEqual(calls, ["attempt 1", "attempt 2"])
        self.assertTrue(out2["execution_history"][-1]["success"])

    def test_start_and_end_logging(self):
        from src.agent.nodes import subagentnode as mod
        from src.utils.agent_logger import bind_session_logger, flush_pending_logs, reset_session_logger

        with tempfile.TemporaryDirectory() as tmp:
            token = bind_session_logger(
                "test_subagent_log",
                execution_id="execution1",
                owner_id="u1",
                logs_dir=Path(tmp),
            )
            try:
                with patch.dict(
                    mod._SUBAGENT_REGISTRY,
                    {"echo": lambda t, c: f"done:{t}"},
                    clear=False,
                ):
                    mod.subagent_node(self._state("echo", task="t1"))
            finally:
                reset_session_logger(token)

            self.assertTrue(flush_pending_logs(timeout=5.0))
            log_path = Path(tmp) / "test_subagent_log.jsonl"
            self.assertTrue(log_path.is_file())
            lines = log_path.read_text(encoding="utf-8").strip().splitlines()
            events = [__import__("json").loads(line)["event"] for line in lines]
            self.assertIn("subagent.start", events)
            self.assertIn("subagent.end", events)


class TestSubagentStream(unittest.TestCase):
    def test_emit_invokes_callback(self):
        from src.agent.subagent_stream import (
            emit_subagent_event,
            reset_subagent_callback,
            set_subagent_callback,
        )

        received = []

        def cb(name, event):
            received.append((name, event))

        token = set_subagent_callback(cb)
        try:
            emit_subagent_event("test_agent", {"step": "validate", "message": "ok", "status": "ok"})
        finally:
            reset_subagent_callback(token)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "test_agent")
        self.assertEqual(received[0][1]["step"], "validate")

    def test_emit_without_callback_is_noop(self):
        from src.agent.subagent_stream import emit_subagent_event

        # Must not raise
        emit_subagent_event("test_agent", {"step": "x", "message": "y", "status": "ok"})


class TestPromptWiring(unittest.TestCase):
    def test_prompt_shows_none_available_when_empty(self):
        from src.prompts.prompt_loader import agentnode_prompt_loader
        from src.subagents.registry import SUBAGENTS

        system, user = agentnode_prompt_loader(
            user_query="build an agent",
            tools=[],
            execution_history=[],
            execution_memory_index=[],
            context_memory={},
            subagents=SUBAGENTS,
            turn_start=True,
        )
        combined = system + "\n" + user
        # The subagents block is gated on a non-empty catalog: with no
        # sub-agents registered the section is omitted entirely.
        self.assertNotIn("Available Sub-agents", combined)

    def test_prompt_none_available_when_empty(self):
        from src.prompts.prompt_loader import agentnode_prompt_loader

        _, user = agentnode_prompt_loader(
            user_query="x",
            tools=[],
            execution_history=[],
            execution_memory_index=[],
            context_memory={},
            subagents=[],
        )
        self.assertNotIn("Available Sub-agents", user)

    def test_agentnode_parses_agent_call(self):
        from src.agent.nodes.agentnode import _parse_response

        buffer = (
            "<planner_exit>False</planner_exit>\n"
            "<action>agent_call</action>\n"
            "<reasoning>delegate</reasoning>\n"
            "<task>Do the thing</task>\n"
            "<data>\n"
            "    <name>helper</name>\n"
            "    <parameters></parameters>\n"
            "</data>\n"
        )
        update = _parse_response(buffer, turn_start=False)
        self.assertEqual(update["next_step"]["action"], "subagent")
        self.assertEqual(update["next_step"]["agent_name"], "helper")
        self.assertEqual(update["next_step"]["task"], "Do the thing")

    def test_agentnode_parses_spawn_children(self):
        from src.agent.nodes.agentnode import _parse_response

        buffer = (
            "<planner_exit>False</planner_exit>\n"
            "<action>spawn_children</action>\n"
            "<reasoning>parallelize</reasoning>\n"
            "<task>delegate</task>\n"
            "<data>\n"
            "    <name>child_agent</name>\n"
            "    <parameters><child_calls>[{\"task\":\"a\"},{\"task\":\"b\",\"parameters\":{\"k\":\"v\"}}]</child_calls></parameters>\n"
            "</data>\n"
        )
        update = _parse_response(buffer, turn_start=False)
        self.assertEqual(update["next_step"]["action"], "child_agent")
        self.assertEqual(len(update["next_step"]["child_calls"]), 2)
        self.assertEqual(update["next_step"]["child_calls"][1]["parameters"], {"k": "v"})

    def test_planner_tool_call_named_spawn_children_routes_to_child_agent(self):
        from src.agent.nodes.agentnode import _parse_response
        from src.agent.edges.routing import CHILD_AGENT_NODE, route_from_agent

        buffer = (
            "<planner_exit>False</planner_exit>"
            "<action>tool_call</action><task>spawn_children</task>"
            "<data><name>spawn_children</name><parameters>"
            '<child_calls>[{"task":"Fetch Tokyo weather"},{"task":"Fetch Manhattan weather"}]</child_calls>'
            "</parameters></data>"
        )
        update = _parse_response(buffer, turn_start=False)
        self.assertEqual(update["next_step"]["action"], "child_agent")
        self.assertEqual(route_from_agent(update), CHILD_AGENT_NODE)
        self.assertEqual([call["task"] for call in update["next_step"]["child_calls"]],
                         ["Fetch Tokyo weather", "Fetch Manhattan weather"])


class TestCatalogAPI(unittest.TestCase):
    def test_subagents_service_catalog(self):
        from api.services.subagents_service import SubagentsService

        catalog = SubagentsService().list_catalog()
        self.assertIn("subagents", catalog)
        self.assertEqual(catalog["counts"]["subagents"], len(catalog["subagents"]))


class TestAgentRuntimeFanout(unittest.TestCase):
    """Simulate the node-update fan-out logic used by AgentRuntime.run_turn."""

    def _fanout(self, node_name: str, updates: dict) -> list[tuple[str, dict]]:
        """Mirror the fixed started/finished branching from agent_runtime."""
        events: list[tuple[str, dict]] = []
        next_step = updates.get("next_step") or {}
        action = next_step.get("action")

        if action == "tool":
            events.append(
                (
                    "tool.started",
                    {
                        "tool_name": next_step.get("tool_name"),
                        "task": next_step.get("task"),
                    },
                )
            )
        if action == "subagent":
            events.append(
                (
                    "subagent.started",
                    {
                        "agent_name": next_step.get("agent_name"),
                        "task": next_step.get("task"),
                    },
                )
            )
        if "execution_history" in updates:
            hist = updates.get("execution_history") or []
            if hist:
                last = hist[-1]
                if last.get("type") == "tool":
                    events.append(("tool.finished", {"tool_name": last.get("tool_name")}))
                elif last.get("type") == "subagent":
                    events.append(
                        (
                            "subagent.finished",
                            {
                                "agent_name": last.get("agent_name"),
                                "success": bool(last.get("success", True)),
                            },
                        )
                    )
                elif last.get("type") == "child_agent":
                    events.append(("child.finished", {"child_agent_id": last.get("child_agent_id")}))
        return events

    def test_agent_decision_emits_started_once(self):
        events = self._fanout(
            "agent_node",
            {
                "next_step": {
                    "action": "subagent",
                    "agent_name": "helper",
                    "task": "build X",
                }
            },
        )
        types = [e[0] for e in events]
        self.assertEqual(types.count("subagent.started"), 1)
        self.assertNotIn("subagent.finished", types)

    def test_subagent_node_finish_does_not_reemit_started(self):
        """Regression: previously node_name==subagent_node also fired started."""
        events = self._fanout(
            "subagent_node",
            {
                "execution_history": [
                    {
                        "type": "subagent",
                        "agent_name": "helper",
                        "task": "build X",
                        "result": "ok",
                        "success": True,
                    }
                ]
            },
        )
        types = [e[0] for e in events]
        self.assertNotIn("subagent.started", types)
        self.assertEqual(types.count("subagent.finished"), 1)

    def test_failed_subagent_finished_success_false(self):
        events = self._fanout(
            "subagent_node",
            {
                "execution_history": [
                    {
                        "type": "subagent",
                        "agent_name": "missing",
                        "result": "Unknown",
                        "success": False,
                    }
                ]
            },
        )
        finished = [e for e in events if e[0] == "subagent.finished"]
        self.assertEqual(len(finished), 1)
        self.assertFalse(finished[0][1]["success"])

    def test_child_agent_fanout(self):
        events = self._fanout(
            "agent_node",
            {
                "next_step": {"action": "child_agent", "task": "delegate"},
                "execution_history": [
                    {
                        "type": "child_agent",
                        "child_agent_id": "child-1",
                        "status": "failed",
                    }
                ],
            },
        )
        types = [e[0] for e in events]
        self.assertIn("child.finished", types)


class TestRouting(unittest.TestCase):
    def test_route_subagent(self):
        from src.agent.edges.routing import SUBAGENT_NODE, route_from_agent

        dest = route_from_agent({"next_step": {"action": "subagent", "agent_name": "helper"}})
        self.assertEqual(dest, SUBAGENT_NODE)

    def test_route_child_agent(self):
        from src.agent.edges.routing import CHILD_AGENT_NODE, route_from_agent

        dest = route_from_agent({"next_step": {"action": "child_agent", "child_calls": [{"task": "a"}]}})
        self.assertEqual(dest, CHILD_AGENT_NODE)


class TestProtocolConstants(unittest.TestCase):
    def test_subagent_event_constants(self):
        from api.ws import protocol

        self.assertEqual(protocol.SUBAGENT_STARTED, "subagent.started")
        self.assertEqual(protocol.SUBAGENT_STEP, "subagent.step")
        self.assertEqual(protocol.SUBAGENT_FINISHED, "subagent.finished")
        self.assertEqual(protocol.CHILD_STARTED, "child.started")
        self.assertEqual(protocol.CHILD_STEP, "child.step")
        self.assertEqual(protocol.CHILD_FINISHED, "child.finished")


if __name__ == "__main__":
    unittest.main()
