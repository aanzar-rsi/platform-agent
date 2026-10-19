"""Unit tests for the live turn renderer (live rendering disabled in tests)."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rich.console import Console

from src.cli.renderer import TurnRenderer


def make_console() -> Console:
    return Console(file=io.StringIO(), force_terminal=False, width=120)


class TestTurnRenderer(unittest.TestCase):
    def test_streaming_output_tokens_accumulate(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.on_token("Hello, ", "output")
        renderer.on_token("world!", "output")
        self.assertEqual(renderer.output_text, "Hello, world!")

    def test_reasoning_streams_in_compact_mode(self):
        renderer = TurnRenderer(make_console(), verbose=False, live=False)
        renderer.on_token("chain of thought", "reasoning")
        self.assertEqual(renderer.reasoning_text, "chain of thought")

    def test_reasoning_shown_when_verbose(self):
        renderer = TurnRenderer(make_console(), verbose=True, live=False)
        renderer.on_token("chain of thought", "reasoning")
        self.assertEqual(renderer.reasoning_text, "chain of thought")

    def test_reasoning_shown_by_default(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.on_token("planner details", "reasoning")
        self.assertEqual(renderer.reasoning_text, "planner details")

    def test_final_answer_overrides_streamed_text(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.on_token("partial", "output")
        renderer.final_answer("the real answer")
        self.assertEqual(renderer.output_text, "the real answer")

    def test_tool_call_appends_styled_row(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.tool_call("web_search", {"query": "weather"})
        self.assertEqual(renderer.lines, [])
        renderer.tool_result("web_search", ok=True, result={"temperature": 28})
        self.assertTrue(renderer.lines[0].startswith("[OK]"))
        rendered = renderer.console.file.getvalue()
        self.assertIn("query=weather", rendered)
        self.assertIn("temperature", rendered)

    def test_tool_result_success_and_failure(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.tool_result("web_search", ok=True)
        self.assertTrue(renderer.lines[0].startswith("[OK] "))

        renderer.tool_result("execute_bash", ok=False, error="boom")
        self.assertTrue(renderer.lines[1].startswith("[FAILED] "))
        self.assertIn("boom", renderer.lines[1])

    def test_subagent_rows(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.subagent_call("coder", "write a script")
        self.assertIn("coder", renderer.lines[0])
        self.assertIn("write a script", renderer.lines[0])
        renderer.subagent_done("coder")
        self.assertTrue(renderer.lines[1].startswith("[OK] "))

    def test_subagent_progress_skips_reasoning_deltas(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.subagent_progress("coder", {"kind": "reasoning_delta", "message": "x"})
        self.assertEqual(renderer.lines, [])
        self.assertEqual(renderer.reasoning_text, "x")

        renderer.subagent_progress("coder", {"kind": "step", "message": "parsing spec"})
        self.assertIn("parsing spec", renderer.lines[0])

    def test_planner_decision_adds_trace_row(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.planner_decision(action="tool", name="web_search", args={"query": "weather"}, task="Find weather")
        self.assertIn("[plan] tool web_search(query=weather) -- Find weather", renderer.lines[0])

    def test_each_planner_pass_replaces_streamed_reasoning(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.on_token("first plan", "reasoning")
        renderer.planner_decision(action="tool", name="web_search", args={}, task="search")
        self.assertEqual(renderer.reasoning_text, "")
        renderer.on_token("second plan", "reasoning")
        self.assertEqual(renderer.reasoning_text, "second plan")
        renderer.planner_decision(action="finish", name="", args={}, task="")
        self.assertEqual(renderer.reasoning_text, "")
        self.assertEqual(len([line for line in renderer.lines if line.startswith("[plan]")]), 2)
        self.assertEqual(len([line for line in renderer.lines if line.startswith("[reasoning]")]), 2)
        first_reasoning = next(i for i, line in enumerate(renderer.lines) if line.startswith("[reasoning]"))
        first_plan = next(i for i, line in enumerate(renderer.lines) if line.startswith("[plan]"))
        self.assertLess(first_reasoning, first_plan)

    def test_as_text_roundtrip_without_errors(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.start(status="Thinking…")
        renderer.on_token("#heading\n", "output")
        renderer.final_answer("#heading\nbody")
        renderer.finish()
        self.assertEqual(renderer.output_text, "#heading\nbody")

    def test_renderable_excludes_completed_activity(self):
        renderer = TurnRenderer(make_console(), live=False)
        renderer.tool_call("web_search", {"query": "weather"})
        self.assertNotIn("web_search", str(renderer._renderable()))

    def test_finish_prints_final_answer_once(self):
        console = make_console()
        renderer = TurnRenderer(console, live=False)
        renderer.final_answer("Final answer")
        renderer.finish()
        renderer.finish()
        self.assertEqual(console.file.getvalue().count("Final answer"), 1)

    def test_finish_uses_exact_accumulated_usage(self):
        console = make_console()
        renderer = TurnRenderer(console, live=False, model_id="gpt-test")
        renderer.add_usage({"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12})
        renderer.add_usage({"prompt_tokens": 20, "completion_tokens": 3, "total_tokens": 23})
        renderer.final_answer("answer")
        renderer.finish()
        output = console.file.getvalue()
        self.assertIn("35 tokens (30 in / 5 out)", output)
        self.assertNotIn("visible tokens", output)

    def test_non_final_plan_does_not_print_usage_separator(self):
        console = make_console()
        renderer = TurnRenderer(console, live=False, model_id="gpt-test")
        renderer.add_usage({"prompt_tokens": 10, "completion_tokens": 2, "total_tokens": 12})
        renderer.on_token("need data", "reasoning")
        renderer.planner_decision(action="tool", name="search", args={}, task="find")
        self.assertNotIn("12 tokens", console.file.getvalue())


if __name__ == "__main__":
    unittest.main()
