"""Unit + edge-case tests for context memory, selector, routing, and agent parse."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.graph import END
from langchain_core.messages import HumanMessage

from src.agent.edges.routing import (
    CHILD_AGENT_NODE,
    CONTEXT_SELECTOR_NODE,
    SUBAGENT_NODE,
    TOOL_NODE,
    route_from_agent,
    route_from_input_gate,
)
from src.agent.memory import (
    CONTEXT_MEMORY_BUDGET,
    build_execution_memory_index,
    count_content_tokens,
    empty_context_memory,
    serialize_content,
    slice_by_tokens,
    slim_execution_history,
    update_context_memory,
)
from src.agent.nodes.agentnode import _format_conversation, _latest_human_content, _parse_response, _run_stream
from src.agent.nodes.context_selector import context_selector_node
from src.agent.nodes.subagentnode import subagent_node
from src.agent.nodes.toolnode import tool_node
from src.models.llm_client import count_tokens
from src.prompts.prompt_loader import agentnode_prompt_loader, to_toon
import toons


def _tokens_of_chars(n: int) -> str:
    """Build a string that is approximately n tokens (~4 chars/token)."""
    return "x" * (n * 4)


class TestEmptyAndSerialize(unittest.TestCase):
    def test_empty_context_memory_defaults(self):
        cm = empty_context_memory()
        self.assertEqual(cm["budget_tokens"], CONTEXT_MEMORY_BUDGET)
        self.assertEqual(cm["used_tokens"], 0)
        self.assertFalse(cm["truncated"])
        self.assertEqual(cm["entries"], [])

    def test_empty_custom_budget(self):
        cm = empty_context_memory(budget=100)
        self.assertEqual(cm["budget_tokens"], 100)

    def test_serialize_str_passthrough(self):
        self.assertEqual(serialize_content("hello"), "hello")

    def test_serialize_dict_toon(self):
        out = serialize_content({"a": 1})
        self.assertEqual(toons.loads(out), {"a": 1})
        self.assertNotIn("{", out)  # TOON object form, not JSON braces

    def test_serialize_uniform_array_tabular(self):
        out = serialize_content([{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
        self.assertIn("{id,name}", out)
        self.assertNotIn('"id"', out)

    def test_count_empty_is_zero(self):
        self.assertEqual(count_content_tokens(""), 0)
        self.assertEqual(count_content_tokens(None), 0)


class TestSliceByTokens(unittest.TestCase):
    def test_full_slice_default(self):
        text = _tokens_of_chars(100)
        sliced, f, t, total, trunc = slice_by_tokens(text)
        self.assertEqual(f, 0)
        self.assertEqual(total, 100)
        self.assertEqual(t, 100)
        self.assertFalse(trunc)
        self.assertEqual(len(sliced), 400)

    def test_range_window(self):
        text = _tokens_of_chars(200)
        sliced, f, t, total, trunc = slice_by_tokens(text, 50, 100)
        self.assertEqual(f, 50)
        self.assertEqual(t, 100)
        self.assertEqual(total, 200)
        self.assertFalse(trunc)
        self.assertEqual(len(sliced), 200)  # 50 tokens * 4

    def test_to_token_none_means_end(self):
        text = _tokens_of_chars(80)
        _, f, t, total, _ = slice_by_tokens(text, 20, None)
        self.assertEqual(f, 20)
        self.assertEqual(t, 80)
        self.assertEqual(total, 80)

    def test_from_beyond_end_yields_empty(self):
        text = _tokens_of_chars(10)
        sliced, f, t, total, trunc = slice_by_tokens(text, 50, 60)
        self.assertEqual(sliced, "")
        self.assertEqual(f, 50)
        self.assertEqual(t, 50)
        self.assertEqual(total, 10)
        self.assertFalse(trunc)

    def test_negative_from_clamped_to_zero(self):
        text = _tokens_of_chars(20)
        sliced, f, t, total, _ = slice_by_tokens(text, -5, 10)
        self.assertEqual(f, 0)
        self.assertEqual(t, 10)

    def test_to_less_than_from_clamped(self):
        text = _tokens_of_chars(50)
        sliced, f, t, total, _ = slice_by_tokens(text, 30, 10)
        self.assertEqual(f, 30)
        self.assertEqual(t, 30)
        self.assertEqual(sliced, "")

    def test_budget_truncates_oversized_slice(self):
        text = _tokens_of_chars(8000)
        sliced, f, t, total, trunc = slice_by_tokens(text, 0, None, budget=5000)
        self.assertTrue(trunc)
        self.assertEqual(f, 0)
        self.assertLessEqual(count_content_tokens(sliced), 5000)
        self.assertEqual(total, 8000)

    def test_empty_content(self):
        sliced, f, t, total, trunc = slice_by_tokens("")
        self.assertEqual((sliced, f, t, total, trunc), ("", 0, 0, 0, False))

    def test_dict_content_partial_slice_is_toon_string(self):
        payload = {"rows": ["a" * 100] * 20}
        sliced, f, t, total, trunc = slice_by_tokens(payload, 0, 5)
        self.assertIsInstance(sliced, str)
        self.assertEqual(f, 0)
        self.assertEqual(t, 5)
        self.assertGreater(total, 5)

    def test_full_structured_slice_keeps_object(self):
        payload = [{"id": i, "v": i * 2} for i in range(5)]
        sliced, f, t, total, trunc = slice_by_tokens(payload, budget=5000)
        self.assertIs(sliced, payload)
        self.assertFalse(trunc)
        self.assertEqual(f, 0)
        self.assertEqual(t, total)


class TestUpdateContextMemory(unittest.TestCase):
    def test_auto_ingest_small(self):
        cm = update_context_memory(None, key="tool_1", content="hello")
        self.assertEqual(len(cm["entries"]), 1)
        self.assertEqual(cm["entries"][0]["key"], "tool_1")
        self.assertFalse(cm["truncated"])
        self.assertEqual(cm["used_tokens"], cm["entries"][0]["tokens"])

    def test_auto_ingest_keeps_structured_content(self):
        rows = [{"id": i, "drug": f"D{i}", "sales": 100 + i} for i in range(10)]
        cm = update_context_memory(None, key="tool_1", content=rows)
        self.assertIsInstance(cm["entries"][0]["content"], list)
        self.assertEqual(cm["entries"][0]["content"][0]["id"], 0)
        self.assertFalse(cm["truncated"])

    def test_partial_window_stores_toon_string(self):
        rows = [{"id": i, "drug": f"D{i}", "sales": 100 + i} for i in range(30)]
        cm = update_context_memory(
            None, key="tool_1", content=rows, from_token=5, to_token=20
        )
        self.assertIsInstance(cm["entries"][0]["content"], str)
        self.assertEqual(cm["entries"][0]["from_token"], 5)

    def test_oversized_single_result_truncated_flag(self):
        big = _tokens_of_chars(CONTEXT_MEMORY_BUDGET + 500)
        cm = update_context_memory(None, key="tool_1", content=big)
        self.assertTrue(cm["truncated"])
        self.assertLessEqual(cm["used_tokens"], CONTEXT_MEMORY_BUDGET)
        self.assertEqual(cm["entries"][0]["from_token"], 0)
        self.assertEqual(cm["entries"][0]["total_tokens"], CONTEXT_MEMORY_BUDGET + 500)

    def test_fifo_evicts_oldest(self):
        budget = 100
        cm = empty_context_memory(budget=budget)
        cm = update_context_memory(cm, key="a", content=_tokens_of_chars(40), budget=budget)
        cm = update_context_memory(cm, key="b", content=_tokens_of_chars(40), budget=budget)
        cm = update_context_memory(cm, key="c", content=_tokens_of_chars(40), budget=budget)
        keys = [e["key"] for e in cm["entries"]]
        self.assertIn("a", keys)
        self.assertEqual(cm["entries"][0]["from_token"], 20)
        self.assertIn("c", keys)
        self.assertLessEqual(cm["used_tokens"], budget)

    def test_exact_budget_fit_clears_others(self):
        budget = 50
        cm = update_context_memory(
            None, key="old", content=_tokens_of_chars(20), budget=budget
        )
        cm = update_context_memory(
            cm, key="new", content=_tokens_of_chars(50), budget=budget
        )
        self.assertEqual([e["key"] for e in cm["entries"]], ["new"])
        self.assertEqual(cm["used_tokens"], 50)

    def test_same_key_replaced_not_duplicated(self):
        text = _tokens_of_chars(200)
        cm = update_context_memory(None, key="tool_1", content=text, from_token=0, to_token=50)
        cm = update_context_memory(cm, key="tool_1", content=text, from_token=50, to_token=100)
        self.assertEqual(len(cm["entries"]), 1)
        self.assertEqual(cm["entries"][0]["from_token"], 50)
        self.assertEqual(cm["entries"][0]["to_token"], 100)

    def test_range_load_preserves_window_meta(self):
        text = _tokens_of_chars(300)
        cm = update_context_memory(
            None, key="tool_2", content=text, from_token=100, to_token=150
        )
        e = cm["entries"][0]
        self.assertEqual(e["from_token"], 100)
        self.assertEqual(e["to_token"], 150)
        self.assertEqual(e["total_tokens"], 300)
        self.assertFalse(cm["truncated"])

    def test_requested_range_larger_than_budget_sets_truncated(self):
        text = _tokens_of_chars(10000)
        cm = update_context_memory(
            None,
            key="tool_1",
            content=text,
            from_token=0,
            to_token=8000,
            budget=5000,
        )
        self.assertTrue(cm["truncated"])
        self.assertLessEqual(cm["entries"][0]["tokens"], 5000)

    def test_none_context_memory_bootstraps(self):
        cm = update_context_memory(None, key="k", content="abc")
        self.assertIn("entries", cm)
        self.assertEqual(cm["budget_tokens"], CONTEXT_MEMORY_BUDGET)

    def test_does_not_mutate_input_entries_list(self):
        cm = empty_context_memory()
        cm = update_context_memory(cm, key="a", content="one")
        before = list(cm["entries"])
        update_context_memory(cm, key="b", content="two")
        self.assertEqual(cm["entries"], before)


class TestIndexAndSlimHistory(unittest.TestCase):
    def test_index_marks_in_context(self):
        em = {
            "tool_1": {
                "type": "tool",
                "tool_name": "read_file",
                "task": "load",
                "result": "data",
            },
            "tool_2": {
                "type": "tool",
                "tool_name": "search",
                "task": "find",
                "result": "hits",
            },
        }
        cm = update_context_memory(None, key="tool_1", content="data")
        idx = build_execution_memory_index(em, cm)
        by_key = {row["key"]: row for row in idx}
        self.assertTrue(by_key["tool_1"]["in_context"])
        self.assertFalse(by_key["tool_2"]["in_context"])
        self.assertEqual(by_key["tool_1"]["name"], "read_file")
        self.assertEqual(by_key["tool_1"]["description"], "load")
        self.assertNotIn("result", by_key["tool_1"])

    def test_index_handles_non_dict_entries(self):
        idx = build_execution_memory_index({"raw": "plain string"}, None)
        self.assertEqual(idx[0]["type"], "unknown")
        self.assertFalse(idx[0]["in_context"])

    def test_index_subagent_name(self):
        em = {
            "subagent_1": {
                "type": "subagent",
                "agent_name": "coder",
                "task": "write",
                "result": "ok",
            }
        }
        idx = build_execution_memory_index(em, empty_context_memory())
        self.assertEqual(idx[0]["name"], "coder")

    def test_slim_history_strips_result(self):
        hist = [
            {
                "type": "tool",
                "tool_name": "read_file",
                "task": "load",
                "key": "tool_1",
                "result": {"huge": "payload" * 100},
                "success": True,
            }
        ]
        slim = slim_execution_history(hist)
        self.assertEqual(len(slim), 1)
        self.assertNotIn("result", slim[0])
        self.assertEqual(slim[0]["key"], "tool_1")
        self.assertGreater(slim[0]["tokens"], 0)

    def test_slim_history_skips_non_dicts(self):
        self.assertEqual(slim_execution_history(["x", None, 1]), [])

    def test_slim_empty(self):
        self.assertEqual(slim_execution_history([]), [])
        self.assertEqual(slim_execution_history(None), [])


class TestContextSelectorNode(unittest.TestCase):
    def _state(self, **kwargs):
        base = {
            "next_step": {"key": "tool_1", "from_token": 0, "to_token": None},
            "execution_memory": {
                "tool_1": {
                    "type": "tool",
                    "tool_name": "read_file",
                    "result": _tokens_of_chars(200),
                }
            },
            "context_memory": empty_context_memory(),
        }
        base.update(kwargs)
        return base

    def test_loads_result_into_context(self):
        out = context_selector_node(self._state())
        self.assertIn("context_memory", out)
        self.assertEqual(out["context_memory"]["entries"][0]["key"], "tool_1")
        self.assertEqual(len(out), 1)  # only context_memory returned

    def test_token_range(self):
        out = context_selector_node(
            self._state(next_step={"key": "tool_1", "from_token": 50, "to_token": 100})
        )
        e = out["context_memory"]["entries"][0]
        self.assertEqual(e["from_token"], 50)
        self.assertEqual(e["to_token"], 100)

    def test_missing_key_writes_error_stub(self):
        out = context_selector_node(
            self._state(
                next_step={"key": "missing", "from_token": 0},
                execution_memory={},
            )
        )
        content = out["context_memory"]["entries"][0]["content"]
        self.assertIn("not found", content)
        self.assertEqual(out["context_memory"]["entries"][0]["key"], "missing")

    def test_empty_key_uses_missing_sentinel(self):
        out = context_selector_node(
            self._state(next_step={"key": "", "from_token": 0}, execution_memory={})
        )
        self.assertEqual(out["context_memory"]["entries"][0]["key"], "_missing")

    def test_string_token_params_coerced(self):
        out = context_selector_node(
            self._state(
                next_step={"key": "tool_1", "from_token": "10", "to_token": "30"}
            )
        )
        e = out["context_memory"]["entries"][0]
        self.assertEqual(e["from_token"], 10)
        self.assertEqual(e["to_token"], 30)

    def test_invalid_token_params_fall_back(self):
        out = context_selector_node(
            self._state(
                next_step={"key": "tool_1", "from_token": "nope", "to_token": "x"}
            )
        )
        e = out["context_memory"]["entries"][0]
        self.assertEqual(e["from_token"], 0)
        # to_token invalid -> None -> end of content
        self.assertEqual(e["to_token"], e["total_tokens"])

    def test_raw_non_dict_memory_entry(self):
        out = context_selector_node(
            self._state(
                execution_memory={"tool_1": "raw payload text here"},
                next_step={"key": "tool_1", "from_token": 0, "to_token": 2},
            )
        )
        self.assertIn("raw", out["context_memory"]["entries"][0]["content"])

    def test_replaces_existing_same_key_window(self):
        cm = update_context_memory(
            None, key="tool_1", content=_tokens_of_chars(200), from_token=0, to_token=40
        )
        out = context_selector_node(
            self._state(
                context_memory=cm,
                next_step={"key": "tool_1", "from_token": 80, "to_token": 120},
            )
        )
        entries = out["context_memory"]["entries"]
        self.assertEqual(len([e for e in entries if e["key"] == "tool_1"]), 1)
        self.assertEqual(entries[-1]["from_token"], 80)


class TestRouting(unittest.TestCase):
    def test_tool(self):
        self.assertEqual(route_from_agent({"next_step": {"action": "tool"}}), TOOL_NODE)

    def test_subagent(self):
        self.assertEqual(
            route_from_agent({"next_step": {"action": "subagent"}}), SUBAGENT_NODE
        )

    def test_child_agent(self):
        self.assertEqual(
            route_from_agent({"next_step": {"action": "child_agent"}}), CHILD_AGENT_NODE
        )

    def test_context_select(self):
        self.assertEqual(
            route_from_agent({"next_step": {"action": "context_select"}}),
            CONTEXT_SELECTOR_NODE,
        )

    def test_finish(self):
        self.assertEqual(route_from_agent({"next_step": {"action": "finish"}}), END)

    def test_missing_next_step_ends(self):
        self.assertEqual(route_from_agent({}), END)

    def test_unknown_action_ends(self):
        self.assertEqual(route_from_agent({"next_step": {"action": "nope"}}), END)

    def test_input_gate_reuses_action_map(self):
        self.assertEqual(route_from_input_gate({"next_step": {"action": "tool"}}), TOOL_NODE)
        self.assertEqual(route_from_input_gate({"next_step": {"action": "subagent"}}), SUBAGENT_NODE)
        self.assertEqual(route_from_input_gate({"next_step": {"action": "child_agent"}}), CHILD_AGENT_NODE)
        self.assertEqual(route_from_input_gate({"next_step": {"action": "context_select"}}), CONTEXT_SELECTOR_NODE)
        self.assertEqual(route_from_input_gate({"next_step": {"action": "finish"}}), END)


class TestAgentParseResponse(unittest.TestCase):
    def test_final_response_streams_and_persists_reasoning(self):
        visible = []
        buffer = _run_stream(
            iter([
                "<planner_exit>True</planner_exit><reasoning>Checking results</reasoning>",
                "<output>It is sunny.</output>",
            ]),
            lambda text, channel: visible.append((text, channel)),
        )
        update = _parse_response(buffer, turn_start=False)

        self.assertEqual(
            visible,
            [("Checking results", "reasoning"), ("It is sunny.", "output")],
        )
        self.assertEqual(
            update["messages"][0].additional_kwargs["ui_step"],
            {"type": "reasoning", "content": "Checking results"},
        )

    def test_stream_does_not_emit_partial_closing_xml_tag(self):
        visible = []
        chunks = iter(
            [
                "<planner_exit>False</planner_exit><reasoning>Hello</rea",
                "soning><task>x</task>",
            ]
        )
        _run_stream(chunks, lambda text, channel: visible.append((text, channel)))
        self.assertEqual(visible, [("Hello", "reasoning")])

    def test_context_select_action(self):
        buf = """
        <planner_exit>False</planner_exit>
        <action>context_select</action>
        <reasoning>need more of the file</reasoning>
        <task>Load window</task>
        <data>
            <name>context_selector</name>
            <parameters>
                <key>tool_3</key>
                <from_token>2000</from_token>
                <to_token>4000</to_token>
            </parameters>
        </data>
        """
        update = _parse_response(buf, turn_start=False)
        ns = update["next_step"]
        self.assertEqual(ns["action"], "context_select")
        self.assertEqual(ns["key"], "tool_3")
        self.assertEqual(ns["from_token"], 2000)
        self.assertEqual(ns["to_token"], 4000)

    def test_context_select_via_name_only(self):
        buf = """
        <planner_exit>False</planner_exit>
        <action>tool_call</action>
        <reasoning>reload</reasoning>
        <task>window</task>
        <data>
            <name>context_selector</name>
            <parameters>
                <key>tool_1</key>
                <from_token>0</from_token>
            </parameters>
        </data>
        """
        update = _parse_response(buf, turn_start=False)
        self.assertEqual(update["next_step"]["action"], "context_select")
        self.assertEqual(update["next_step"]["key"], "tool_1")
        self.assertIsNone(update["next_step"]["to_token"])

    def test_tool_call_not_confused_with_selector(self):
        buf = """
        <planner_exit>False</planner_exit>
        <action>tool_call</action>
        <reasoning>read</reasoning>
        <task>load</task>
        <data>
            <name>read_file</name>
            <parameters>
                <path>a.csv</path>
            </parameters>
        </data>
        """
        update = _parse_response(buf, turn_start=False)
        self.assertEqual(update["next_step"]["action"], "tool")
        self.assertEqual(update["next_step"]["tool_name"], "read_file")

    def test_restart_clears_context_memory(self):
        buf = """
        <session_intent>restart</session_intent>
        <planner_exit>True</planner_exit>
        <action>None</action>
        <reasoning>new topic</reasoning>
        <data>
            <output>Fresh start</output>
        </data>
        """
        update = _parse_response(buf, turn_start=True)
        self.assertEqual(update["execution_history"], [])
        self.assertEqual(update["execution_memory"], {})
        self.assertEqual(update["context_memory"]["entries"], [])
        self.assertEqual(update["context_memory"]["used_tokens"], 0)

    def test_continue_does_not_clear(self):
        buf = """
        <session_intent>continue</session_intent>
        <planner_exit>True</planner_exit>
        <action>None</action>
        <reasoning>done</reasoning>
        <data><output>ok</output></data>
        """
        update = _parse_response(buf, turn_start=True)
        self.assertNotIn("context_memory", update)
        self.assertNotIn("execution_memory", update)

    def test_invalid_from_token_defaults_zero(self):
        buf = """
        <planner_exit>False</planner_exit>
        <action>context_select</action>
        <reasoning>x</reasoning>
        <task>y</task>
        <data>
            <name>context_selector</name>
            <parameters>
                <key>tool_1</key>
                <from_token>abc</from_token>
                <to_token>10</to_token>
            </parameters>
        </data>
        """
        update = _parse_response(buf, turn_start=False)
        self.assertEqual(update["next_step"]["from_token"], 0)
        self.assertEqual(update["next_step"]["to_token"], 10)


class TestPromptLoader(unittest.TestCase):
    def test_injects_index_and_context_not_full_memory(self):
        class T:
            name = "demo"
            description = "d"

        index = [{"key": "tool_1", "name": "demo", "in_context": True, "total_tokens": 3}]
        cm = empty_context_memory()
        cm = update_context_memory(cm, key="tool_1", content="abc")
        hist = [{"type": "tool", "name": "demo", "key": "tool_1", "tokens": 1}]

        system, user = agentnode_prompt_loader(
            user_query="q",
            tools=[T()],
            execution_history=hist,
            execution_memory_index=index,
            context_memory=cm,
            turn_start=False,
        )
        self.assertIn("execution_memory_index", user)
        self.assertIn("context_memory", user)
        self.assertIn("tool_1", user)
        self.assertIn("context_select", user)
        self.assertIn("execution_memory_index", user)
        # Index should be tabular TOON, not pretty JSON
        self.assertIn("{key,name,in_context,total_tokens}", user)
        self.assertNotIn('"in_context":', user)
        self.assertNotIn("SECRET_FULL_PAYLOAD", user)

    def test_turn_start_session_intent_block(self):
        class T:
            name = "demo"
            description = "d"

        _, user = agentnode_prompt_loader(
            user_query="q",
            tools=[T()],
            execution_history=[],
            execution_memory_index=[],
            context_memory=empty_context_memory(),
            turn_start=True,
        )
        self.assertIn("session_intent", user)

    def test_hidden_human_answer_is_not_direct_prompt_input(self):
        messages = [
            HumanMessage(content="original request"),
            HumanMessage(content="SECRET_ANSWER", additional_kwargs={"ui_hidden": True}),
        ]
        self.assertEqual(_latest_human_content(messages), "original request")
        self.assertNotIn("SECRET_ANSWER", _format_conversation(messages))


class TestToonTokenSavings(unittest.TestCase):
    def test_structured_bundle_saves_at_least_40_percent_vs_json_pretty(self):
        rows = [
            {"id": i, "drug": f"DRUG_{i}", "sales": 1000 + i * 3.5, "region": ["US", "EU", "APAC"][i % 3]}
            for i in range(40)
        ]
        search = {
            "results": [
                {
                    "title": f"Result {i}",
                    "url": f"https://example.com/{i}",
                    "snippet": "lorem ipsum dolor sit amet " * 8,
                }
                for i in range(8)
            ]
        }
        hist = [
            {"type": "tool", "name": "read_table", "task": "Load sales", "key": "tool_1", "tokens": 0, "success": True},
            {"type": "tool", "name": "web_search", "task": "Find docs", "key": "tool_2", "tokens": 0, "success": True},
        ]
        cm = empty_context_memory()
        cm = update_context_memory(cm, key="tool_1", content=rows)
        cm = update_context_memory(cm, key="tool_2", content=search)
        em = {
            "tool_1": {"type": "tool", "tool_name": "read_table", "task": "Load sales", "result": rows},
            "tool_2": {"type": "tool", "tool_name": "web_search", "task": "Find docs", "result": search},
        }
        index = build_execution_memory_index(em, cm)
        preloaded = {
            "user_memories": [{"k": "prefers_tables", "v": True}, {"k": "timezone", "v": "Asia/Kolkata"}],
            "mcp_connections": [{"name": "mdm", "status": "connected"}],
        }

        bundle = {
            "execution_history": hist,
            "execution_memory_index": index,
            "context_memory": cm,
            "preloaded_context": preloaded,
        }
        json_pretty = json.dumps(bundle, indent=2, default=str)
        toon_text = "\n".join(
            [
                to_toon(hist),
                to_toon(index),
                to_toon(cm),
                to_toon(preloaded),
            ]
        )
        json_tokens = count_tokens(json_pretty)["input"]
        toon_tokens = count_tokens(toon_text)["input"]
        savings = (json_tokens - toon_tokens) / json_tokens
        self.assertGreaterEqual(
            savings,
            0.40,
            f"expected >=40% savings, got {savings:.1%} (json={json_tokens}, toon={toon_tokens})",
        )

    def test_prompt_loader_uses_toon_not_json_braces_for_index(self):
        class T:
            name = "demo"
            description = "d"

        index = [
            {"key": "tool_1", "type": "tool", "name": "read_table", "task": "Load", "total_tokens": 10, "in_context": True},
            {"key": "tool_2", "type": "tool", "name": "search", "task": "Find", "total_tokens": 20, "in_context": False},
        ]
        _, user = agentnode_prompt_loader(
            user_query="Summarize regional sales",
            tools=[T()],
            execution_history=slim_execution_history([]),
            execution_memory_index=index,
            context_memory=empty_context_memory(),
        )
        self.assertIn("[2]{key,type,name,task,total_tokens,in_context}:", user)
        self.assertNotIn('{\n  "key": "tool_1"', user)


class TestToolAndSubagentIngest(unittest.TestCase):
    def test_duplicate_successful_tool_call_is_allowed(self):
        fake_tool = MagicMock()
        fake_tool.name = "lookup"
        fake_tool.args_schema = None

        with patch("src.agent.nodes.toolnode._TOOL_MAP", {"lookup": fake_tool}):
            out = tool_node(
                {
                    "next_step": {"tool_name": "lookup", "tool_args": {"q": "x"}, "task": "again"},
                    "execution_history": [
                        {
                            "type": "tool",
                            "tool_name": "lookup",
                            "tool_args": {"q": "x"},
                            "key": "tool_1",
                            "success": True,
                            "result": {"success": True, "value": "done"},
                        }
                    ],
                    "execution_memory": {},
                    "context_memory": empty_context_memory(),
                    "current_task": "again",
                }
            )
        fake_tool.invoke.assert_called_once_with({"q": "x"})
        self.assertTrue(out["execution_history"][-1]["success"])

    def test_second_web_search_is_allowed_when_query_changes(self):
        fake_tool = MagicMock()
        fake_tool.name = "web_search"
        fake_tool.args_schema = None

        with patch("src.agent.nodes.toolnode._TOOL_MAP", {"web_search": fake_tool}):
            out = tool_node(
                {
                    "next_step": {
                        "tool_name": "web_search",
                        "tool_args": {"query": "Hyderabad weather now"},
                        "task": "refresh",
                    },
                    "execution_history": [
                        {
                            "type": "tool",
                            "tool_name": "web_search",
                            "tool_args": {"query": "Hyderabad weather"},
                            "key": "tool_1",
                            "success": True,
                            "result": {"success": True, "results": ["28 C"]},
                        }
                    ],
                    "execution_memory": {},
                    "context_memory": empty_context_memory(),
                    "current_task": "refresh",
                }
            )
        fake_tool.invoke.assert_called_once_with({"query": "Hyderabad weather now"})
        self.assertTrue(out["execution_history"][-1]["success"])

    def test_success_flag_is_stored_in_history(self):
        fake_tool = MagicMock()
        fake_tool.name = "lookup"
        fake_tool.args_schema = None
        fake_tool.invoke.return_value = {"success": True, "value": "done"}
        with patch("src.agent.nodes.toolnode._TOOL_MAP", {"lookup": fake_tool}):
            out = tool_node(
                {
                    "next_step": {"tool_name": "lookup", "tool_args": {}, "task": "once"},
                    "execution_history": [],
                    "execution_memory": {},
                    "context_memory": empty_context_memory(),
                    "current_task": "once",
                }
            )
        self.assertTrue(out["execution_history"][-1]["success"])

    def test_unknown_tool_auto_ingests_and_stubs_message(self):
        state = {
            "next_step": {"tool_name": "no_such_tool", "tool_args": {}, "task": "x"},
            "execution_history": [],
            "execution_memory": {},
            "context_memory": empty_context_memory(),
            "current_task": "x",
        }
        out = tool_node(state)
        self.assertIn("tool_1", out["execution_memory"])
        self.assertEqual(out["context_memory"]["entries"][0]["key"], "tool_1")
        msg = out["messages"][0].content
        self.assertIn("Tool 'no_such_tool' result:", msg)
        self.assertIn("Unknown tool", msg)
        self.assertFalse(out["execution_memory"]["tool_1"]["success"])

    def test_tool_oversized_result_truncates_in_context(self):
        huge = _tokens_of_chars(CONTEXT_MEMORY_BUDGET + 100)
        fake_tool = MagicMock()
        fake_tool.name = "huge_tool"
        fake_tool.args_schema = None
        fake_tool.invoke.return_value = huge

        with patch("src.agent.nodes.toolnode._TOOL_MAP", {"huge_tool": fake_tool}):
            out = tool_node(
                {
                    "next_step": {"tool_name": "huge_tool", "tool_args": {}, "task": "t"},
                    "execution_history": [],
                    "execution_memory": {},
                    "context_memory": empty_context_memory(),
                    "current_task": "t",
                }
            )
        # full payload retained in execution_memory
        self.assertEqual(out["execution_memory"]["tool_1"]["result"], huge)
        self.assertTrue(out["context_memory"]["truncated"])
        self.assertLessEqual(out["context_memory"]["used_tokens"], CONTEXT_MEMORY_BUDGET)
        self.assertFalse(out["context_memory"]["entries"][0]["complete"])

    def test_subagent_unknown_auto_ingests(self):
        out = subagent_node(
            {
                "next_step": {"agent_name": "ghost", "task": "do"},
                "execution_history": [],
                "execution_memory": {},
                "context_memory": empty_context_memory(),
                "preloaded_context": {},
            }
        )
        self.assertIn("subagent_1", out["execution_memory"])
        self.assertEqual(out["context_memory"]["entries"][0]["key"], "subagent_1")
        self.assertIn("Subagent 'ghost' result:", out["messages"][0].content)

    def test_fifo_trims_only_needed_prefix(self):
        cm = empty_context_memory(100)
        cm = update_context_memory(cm, key="a", content=_tokens_of_chars(70), budget=100)
        cm = update_context_memory(cm, key="b", content=_tokens_of_chars(50), budget=100)
        self.assertEqual([entry["key"] for entry in cm["entries"]], ["a", "b"])
        self.assertEqual(cm["entries"][0]["from_token"], 20)
        self.assertFalse(cm["entries"][0]["complete"])
        self.assertEqual(cm["used_tokens"], 100)


class TestGraphWiring(unittest.TestCase):
    def test_context_selector_registered(self):
        from src.agent.graph import agent_app

        self.assertIn("context_selector", agent_app.nodes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
