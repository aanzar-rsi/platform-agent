"""Tests for the declarative prompt renderer in prompt_loader.py."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["EVA_SKIP_VENV_REEXEC"] = "1"

from src.prompts.prompt_loader import (
    PromptRenderError,
    _eval_cond,
    _fmt,
    _present,
    render,
    to_toon,
)


class TestPresence(unittest.TestCase):
    def test_false_is_absent(self):
        """The prototype returned True here, so `if=turn_start` always fired and
        the model got session_intent rules on turns that must not emit one."""
        self.assertFalse(_present({"turn_start": False}, "turn_start"))

    def test_true_is_present(self):
        self.assertTrue(_present({"turn_start": True}, "turn_start"))

    def test_zero_is_present(self):
        # 0 is a real value, not an unset flag.
        self.assertTrue(_present({"n": 0}, "n"))

    def test_empty_values_are_absent(self):
        for value in (None, "", "   ", [], {}, (), set()):
            with self.subTest(value=value):
                self.assertFalse(_present({"k": value}, "k"))

    def test_missing_key_is_absent(self):
        self.assertFalse(_present({}, "nope"))

    def test_non_empty_values_are_present(self):
        for value in ("x", [1], {"a": 1}, (1,), 3.5):
            with self.subTest(value=value):
                self.assertTrue(_present({"k": value}, "k"))


class TestConditions(unittest.TestCase):
    def test_no_condition_always_renders(self):
        self.assertTrue(_eval_cond(None, {}))
        self.assertTrue(_eval_cond("", {}))

    def test_and(self):
        self.assertTrue(_eval_cond("a,b", {"a": 1, "b": 2}))
        self.assertFalse(_eval_cond("a,b", {"a": 1}))

    def test_or(self):
        self.assertTrue(_eval_cond("a|b|c", {"c": 1}))
        self.assertFalse(_eval_cond("a|b|c", {"d": 1}))

    def test_negation(self):
        self.assertTrue(_eval_cond("!a", {}))
        self.assertFalse(_eval_cond("!a", {"a": 1}))

    def test_false_flag_fails_condition(self):
        self.assertFalse(_eval_cond("flag", {"flag": False}))
        self.assertTrue(_eval_cond("!flag", {"flag": False}))


class TestFormatting(unittest.TestCase):
    def test_structured_values_use_toon_not_json(self):
        """json.dumps(indent=2) was 2.6x more tokens for the same data."""
        history = [{"step": 1, "name": "read_file", "status": "ok"}]
        out = _fmt(history)
        self.assertEqual(out, to_toon(history))
        self.assertNotIn("\n  ", out.replace(to_toon(history), ""))

    def test_none_renders_empty(self):
        self.assertEqual(_fmt(None), "")

    def test_scalars_stringify(self):
        self.assertEqual(_fmt(4), "4")
        self.assertEqual(_fmt("x"), "x")


class TestRendering(unittest.TestCase):
    def test_absent_block_drops_header_and_placeholder(self):
        tmpl = "always\n@block t if=tools\nTools:\n{tools}\n@end\ntail"
        out = render(tmpl, {})
        self.assertNotIn("Tools:", out)
        self.assertNotIn("{tools}", out)
        self.assertIn("always", out)
        self.assertIn("tail", out)

    def test_present_block_renders(self):
        tmpl = "@block t if=tools\nTools:\n{tools}\n@end"
        self.assertIn("- read_file", render(tmpl, {"tools": "- read_file"}))

    def test_nested_parent_vanishes_when_all_children_absent(self):
        tmpl = (
            "@block parent if=a|b\nHeader:\n"
            "@block a if=a\n- a: {a}\n@end\n"
            "@block b if=b\n- b: {b}\n@end\n"
            "@end"
        )
        self.assertNotIn("Header:", render(tmpl, {}))
        out = render(tmpl, {"b": "two"})
        self.assertIn("Header:", out)
        self.assertIn("- b: two", out)
        self.assertNotIn("- a:", out)

    def test_directives_and_comments_never_appear(self):
        out = render("@# secret note\n@block x\nbody\n@end", {})
        self.assertNotIn("secret note", out)
        self.assertNotIn("@block", out)
        self.assertNotIn("@end", out)
        self.assertIn("body", out)

    def test_literal_json_braces_pass_through(self):
        """str.format() required {{ }} escaping; this renderer does not."""
        out = render('shape: {"a": 1, "b": {"c": 2}}', {})
        self.assertIn('{"a": 1, "b": {"c": 2}}', out)

    def test_blank_line_runs_collapse(self):
        out = render("a\n\n\n\n\nb", {})
        self.assertNotIn("\n\n\n", out)

    def test_unknown_var_renders_empty_by_default(self):
        self.assertNotIn("{missing}", render("x {missing} y", {}))

    def test_unknown_var_raises_in_strict_mode(self):
        with self.assertRaises(PromptRenderError):
            render("x {missing} y", {}, strict=True)

    def test_known_but_empty_var_is_fine_in_strict_mode(self):
        render("x {present} y", {"present": ""}, strict=True)  # must not raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
