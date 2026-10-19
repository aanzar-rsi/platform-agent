"""Focused checks for CLI-configurable agent runtime controls."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.messages import HumanMessage

from src.agent.nodes import agentnode
from src.agent.nodes.toolnode import tool_node
from src.utils.postgres_checkpointer import build_config


class TestRuntimeControls(unittest.TestCase):
    def test_build_config_sets_runtime_and_recursion_limit(self):
        config = build_config("chat", runtime={"model_id": "gpt-4.1", "max_loops": 7})
        self.assertEqual(config["configurable"]["model_id"], "gpt-4.1")
        self.assertEqual(config["recursion_limit"], 7)

    def test_disabled_tool_is_not_invoked(self):
        state = {
            "next_step": {"tool_name": "get_current_datetime_info", "tool_args": {}},
            "execution_history": [],
            "execution_memory": {},
            "context_memory": None,
            "current_task": "time",
        }
        result = tool_node(state, {"configurable": {"enabled_tools": []}})
        entry = result["execution_history"][-1]
        self.assertFalse(entry["result"]["success"])
        self.assertIn("disabled", entry["result"]["error"])

    @patch.object(agentnode, "_safe_learned_experiences", return_value="")
    @patch.object(agentnode, "call_llm_stream")
    @patch.object(agentnode, "fast_agent_prompt_loader", return_value=("system", "prompt"))
    def test_agent_uses_selected_model_and_filtered_tools(self, prompt_loader, llm_stream, _learned):
        llm_stream.return_value = iter([
            "<planner_exit>True</planner_exit><output>done</output><session_intent>continue</session_intent>"
        ])
        state = {
            "messages": [HumanMessage(content="hello")],
            "execution_history": [],
            "execution_memory": {},
            "context_memory": None,
            "preloaded_context": {},
            "current_task": "",
        }
        agentnode.agent_node(
            state,
            {"configurable": {"model_id": "gpt-4.1", "enabled_tools": ["system_info"], "enabled_subagents": []}},
        )
        self.assertEqual([tool.name for tool in prompt_loader.call_args.kwargs["tools"]], ["system_info"])
        self.assertEqual(prompt_loader.call_args.kwargs["subagents"], [])
        self.assertEqual(llm_stream.call_args.kwargs["model_id"], "gpt-4.1")


if __name__ == "__main__":
    unittest.main()
