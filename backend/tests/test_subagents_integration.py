"""End-to-end tests for EVA subagent integration.

Covers registry, progress streaming, catalog API, runtime event fan-out,
and planner wiring for Armory subagent calls.
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

    def test_agentnode_parses_armory_subagent_call(self):
        from src.agent.nodes.agentnode import _parse_response

        buffer = (
            "<planner_exit>False</planner_exit>\n"
            "<action>armory_call</action>\n"
            "<reasoning>delegate</reasoning>\n"
            "<task>Do the thing</task>\n"
            "<data>\n"
            "    <name>helper</name>\n"
            "    <parameters><resource_type>subagent</resource_type></parameters>\n"
            "</data>\n"
        )
        update = _parse_response(buffer, turn_start=False)
        self.assertEqual(update["next_step"]["action"], "armory")
        self.assertEqual(update["next_step"]["resource_type"], "subagent")
        self.assertEqual(update["next_step"]["resource_name"], "helper")
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

    def test_spawn_children_routes_to_child_agent(self):
        from src.agent.nodes.agentnode import _parse_response
        from src.agent.edges.routing import CHILD_AGENT_NODE, route_from_agent

        buffer = (
            "<planner_exit>False</planner_exit>"
            "<action>spawn_children</action><task>spawn_children</task>"
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

        if action == "armory":
            resource_type = next_step.get("resource_type")
            events.append(
                (
                    "subagent.started" if resource_type == "subagent" else "tool.started",
                    {
                        ("agent_name" if resource_type == "subagent" else "tool_name"):
                            next_step.get("resource_name"),
                        "task": next_step.get("task"),
                    },
                )
            )
        if "execution_history" in updates:
            hist = updates.get("execution_history") or []
            if hist:
                last = hist[-1]
                if last.get("type") == "armory" and last.get("resource_type") == "tool":
                    events.append(("tool.finished", {"tool_name": last.get("resource_name")}))
                elif last.get("type") == "armory" and last.get("resource_type") == "subagent":
                    events.append(
                        (
                            "subagent.finished",
                            {
                                "agent_name": last.get("resource_name"),
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
                    "action": "armory",
                    "resource_type": "subagent",
                    "resource_name": "helper",
                    "task": "build X",
                }
            },
        )
        types = [e[0] for e in events]
        self.assertEqual(types.count("subagent.started"), 1)
        self.assertNotIn("subagent.finished", types)

    def test_armory_node_finish_does_not_reemit_started(self):
        events = self._fanout(
            "armory_node",
            {
                "execution_history": [
                    {
                        "type": "armory",
                        "resource_type": "subagent",
                        "resource_name": "helper",
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
            "armory_node",
            {
                "execution_history": [
                    {
                        "type": "armory",
                        "resource_type": "subagent",
                        "resource_name": "missing",
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
    def test_route_subagent_through_armory(self):
        from src.agent.edges.routing import ARMORY_NODE, route_from_agent

        dest = route_from_agent({"next_step": {"action": "armory", "resource_type": "subagent",
                                                "resource_name": "helper"}})
        self.assertEqual(dest, ARMORY_NODE)

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
