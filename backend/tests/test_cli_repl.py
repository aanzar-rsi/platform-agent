"""Unit tests for the CLI REPL: command parsing, step handling, interrupts,
and the interrupt/resume turn loop (no DB or network involved)."""

from __future__ import annotations

import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langchain_core.messages import AIMessage
from rich.console import Console

from src.cli.repl import (
    handle_step,
    parse_command,
    prompt_for_interrupt,
    run_turn_interactive,
)
from src.cli.renderer import TurnRenderer


def make_console() -> Console:
    return Console(file=io.StringIO(), force_terminal=False, width=120)


def interrupt_step(payload: dict) -> dict:
    return {"__interrupt__": (SimpleNamespace(value=payload),)}


class TestParseCommand(unittest.TestCase):
    def test_bare_quit_exit(self):
        self.assertEqual(parse_command("quit"), ("quit", None))
        self.assertEqual(parse_command("exit"), ("quit", None))

    def test_slash_commands(self):
        self.assertEqual(parse_command("/help"), ("help", None))
        self.assertEqual(parse_command("/rewind abc123"), ("rewind", "abc123"))
        self.assertEqual(parse_command("  /new  "), ("new", None))
        self.assertEqual(parse_command("/model"), ("model", None))
        self.assertEqual(parse_command("/tools"), ("tools", None))
        self.assertEqual(parse_command("/agents"), ("agents", None))
        self.assertEqual(parse_command("/mcp"), ("mcp", None))
        self.assertEqual(parse_command("/settings"), ("settings", None))

    def test_plain_text_is_not_a_command(self):
        self.assertIsNone(parse_command("summarize the docs"))
        self.assertIsNone(parse_command(""))


class TestHandleStep(unittest.TestCase):
    def test_returns_interrupt_payload(self):
        renderer = TurnRenderer(make_console(), live=False)
        step = interrupt_step({"kind": "question", "prompt": "pick", "options": ["a", "b"]})
        payload = handle_step(renderer, step)
        self.assertEqual(payload["kind"], "question")
        self.assertEqual(payload["prompt"], "pick")

    def test_accepts_legacy_nested_interrupt_payload(self):
        renderer = TurnRenderer(make_console(), live=False)
        step = {"__interrupt__": {"__interrupt__": (SimpleNamespace(value={"kind": "paused"}),)}}
        self.assertEqual(handle_step(renderer, step), {"kind": "paused"})

    def test_finish_extracts_answer(self):
        renderer = TurnRenderer(make_console(), live=False)
        step = {
            "agent_node": {
                "next_step": {"action": "finish", "answer": "done"},
                "messages": [AIMessage(content="done")],
            }
        }
        self.assertIsNone(handle_step(renderer, step))
        self.assertEqual(renderer.output_text, "done")

    def test_tool_decision_adds_row(self):
        renderer = TurnRenderer(make_console(), live=False)
        step = {
            "agent_node": {
                "next_step": {"action": "armory", "resource_type": "tool",
                              "resource_name": "web_search", "arguments": {"query": "x"}}
            }
        }
        handle_step(renderer, step)
        self.assertIn("web_search", renderer.lines[0])

    def test_tool_result_success(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.tool_call("web_search", {"query": "x"}, "Find x")
        step = {"armory_node": {"execution_history": [{"type": "armory", "resource_type": "tool",
                                                         "resource_name": "web_search", "result": {"success": True}}]}}
        handle_step(renderer, step)
        self.assertTrue(renderer.lines[0].startswith("[OK] "))
        output = renderer.console.file.getvalue()
        self.assertEqual(output.count("Tool result · web_search · OK"), 1)
        self.assertNotIn("Tool call · web_search", output)

    def test_tool_result_failure_surfaces_error(self):
        renderer = TurnRenderer(make_console(), live=False)
        step = {"armory_node": {"execution_history": [{"type": "armory", "resource_type": "tool",
                                                         "resource_name": "execute_bash",
                                                         "result": {"success": False, "error": "boom"}}]}}
        handle_step(renderer, step)
        self.assertTrue(renderer.lines[0].startswith("[FAILED] "))
        self.assertIn("boom", renderer.lines[0])


class TestPromptForInterrupt(unittest.TestCase):
    @patch("src.cli.repl.Prompt.ask", return_value="2")
    def test_question_with_options_selects_number(self, ask):
        console = make_console()
        result = prompt_for_interrupt(console, {"kind": "question", "prompt": "pick one", "options": ["a", "b"]})
        self.assertEqual(result, "b")

    @patch("src.cli.repl.Prompt.ask", return_value="Hyderabad")
    def test_question_with_options_accepts_free_text(self, ask):
        console = make_console()
        result = prompt_for_interrupt(console, {"kind": "question", "prompt": "location?", "options": ["Use location"]})
        self.assertEqual(result, "Hyderabad")

    @patch("src.cli.repl.Prompt.ask", return_value="free text")
    def test_question_without_options(self, ask):
        console = make_console()
        result = prompt_for_interrupt(console, {"kind": "question", "prompt": "clarify?", "options": []})
        self.assertEqual(result, "free text")
        rendered = console.file.getvalue()
        self.assertIn("Question answered", rendered)
        self.assertIn("You: free text", rendered)

    @patch("src.cli.repl.Prompt.ask", return_value="not safe")
    @patch("src.cli.repl.Confirm.ask", return_value=False)
    def test_confirm_tool_declined(self, confirm, ask):
        console = make_console()
        result = prompt_for_interrupt(
            console,
            {"kind": "confirm_tool", "tool_name": "execute_bash", "tool_args": {"command": "rm -rf"}, "task": "t"},
        )
        self.assertIs(result["approved"], False)
        self.assertEqual(result["reason"], "not safe")

    @patch("src.cli.repl.Prompt.ask", return_value="carry on")
    def test_paused(self, ask):
        console = make_console()
        result = prompt_for_interrupt(console, {"kind": "paused", "value": "paused"})
        self.assertEqual(result, "carry on")


class TestRunTurnInteractive(unittest.TestCase):
    def test_resumes_after_interrupt(self):
        calls: list[dict] = []

        def fake_run_turn(graph, thread_id, query, *, checkpoint_id=None, resume_value=None, is_resume=False, **kwargs):
            calls.append(
                {
                    "query": query,
                    "checkpoint_id": checkpoint_id,
                    "resume_value": resume_value,
                    "is_resume": is_resume,
                }
            )
            if not is_resume:
                def first():
                    yield interrupt_step({"kind": "paused", "value": "paused"})
                return first()
            else:
                def second():
                    yield {
                        "agent_node": {
                            "next_step": {"action": "finish"},
                            "messages": [AIMessage(content="final answer")],
                        }
                    }
                return second()

        console = make_console()
        renderer = TurnRenderer(console, live=False)
        finish_spy = MagicMock(wraps=renderer.finish)
        renderer.finish = finish_spy  # type: ignore[method-assign]

        with patch("src.cli.repl.run_turn", side_effect=fake_run_turn), patch(
            "src.cli.repl.Prompt.ask", return_value="go ahead"
        ):
            run_turn_interactive(console, renderer, "app", "thread-x", "hello")

        self.assertEqual(len(calls), 2)
        self.assertFalse(calls[0]["is_resume"])
        self.assertEqual(calls[0]["query"], "hello")
        self.assertTrue(calls[1]["is_resume"])
        self.assertIsNone(calls[1]["query"])
        self.assertEqual(calls[1]["resume_value"], "go ahead")
        self.assertEqual(renderer.output_text, "final answer")
        finish_spy.assert_called_once()
        self.assertIn("usage unavailable", console.file.getvalue())


class TestHumanInputNode(unittest.TestCase):
    @patch("src.agent.nodes.human_input.interrupt", return_value="Hyderabad")
    def test_accepts_runtime_config_argument(self, interrupt_mock):
        from src.agent.nodes.human_input import human_input_node

        result = human_input_node(
            {"next_step": {"question": "Which city?", "options": ["City and Country"]}},
            config={"configurable": {"thread_id": "chat-1"}},
        )
        self.assertEqual(result["messages"][0].content, "Hyderabad")
        self.assertEqual(interrupt_mock.call_count, 1)


if __name__ == "__main__":
    unittest.main()
