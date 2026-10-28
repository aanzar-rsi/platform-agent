"""Contract tests for every prompt template in the project.

Guards the three things the str.format() -> @block migration could silently
break: unsupplied variables, leftover {{ }} escaping, and the system/user split.
Plus a token budget so the prompt cannot quietly re-bloat.
"""

from __future__ import annotations

import os
import re
import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["EVA_SKIP_VENV_REEXEC"] = "1"

from src.models.llm_client import count_tokens
from src.prompts.prompt_loader import (
    PROMPT_SEPARATOR,
    agentnode_prompt_loader,
    load_prompt,
    render_file,
)

_VAR = re.compile(r"\{(\w+)\}")

_LEARNER = _ROOT / "src" / "subagents" / "learner_agent" / "prompts"
_MAIN = _ROOT / "src" / "prompts"

# name -> (prompts_dir, every key its loader supplies). Keeping this table in
# sync with the loaders is the point: a template variable outside its loader's
# key set renders empty at runtime, silently degrading the prompt.
TEMPLATES = {
    "agentnode": (_MAIN, {
        "tools", "subagents", "user_query", "conversation",
        "turn_start", "learned_experiences", "current_task", "execution_history",
        "execution_memory_index", "context_memory", "preloaded_context",
        "persona", "constraints", "user_preferences",
    }),
    "fast_agent": (_MAIN, {"persona", "user_query", "conversation", "learned_experiences"}),
    "planner_agent": (_MAIN, {
        "persona", "user_query", "conversation", "current_task", "execution_history",
        "execution_memory_index", "context_memory", "constraints", "armory", "max_plan_steps", "child_mode",
        "planner_error", "learned_experiences",
    }),
    "extract_memory_chunks": (_LEARNER, {
        "user_query", "messages_summary", "conversation_messages", "execution_history",
        "decision_snapshots", "allowed_chunk_types",
    }),
}


def _all_template_files():
    # Modules are fragments loaded into templates, not standalone prompts.
    return sorted(
        p for p in (_ROOT / "src").rglob("*.txt")
        if not p.stem.endswith("_backup") and "modules" not in p.parts
    )


def _strip_comments(text: str) -> str:
    """@# lines never render, so their contents are not template variables."""
    return "\n".join(ln for ln in text.splitlines() if not ln.strip().startswith("@#"))


class TestEveryTemplateFileIsRegistered(unittest.TestCase):
    def test_no_orphan_templates(self):
        on_disk = {p.stem for p in _all_template_files()}
        self.assertEqual(on_disk, set(TEMPLATES), "a prompt file is not covered by these tests")


class TestTemplateContracts(unittest.TestCase):
    def test_every_variable_is_supplied_by_its_loader(self):
        for name, (prompts_dir, keys) in TEMPLATES.items():
            with self.subTest(template=name):
                text = _strip_comments((prompts_dir / f"{name}.txt").read_text(encoding="utf-8"))
                used = set(_VAR.findall(text))
                self.assertTrue(
                    used <= keys,
                    f"{name}.txt uses variables its loader never passes: {sorted(used - keys)}",
                )

    def test_renders_strict_with_a_full_context(self):
        """strict=True turns a typo'd {var} into a failure instead of an empty
        string — the safety net str.format()'s KeyError used to provide."""
        for name, (prompts_dir, keys) in TEMPLATES.items():
            with self.subTest(template=name):
                ctx = {k: "X" for k in keys}
                out = render_file(prompts_dir / f"{name}.txt", ctx, strict=True)
                self.assertNotRegex(out, r"\{\w+\}", f"{name}: unresolved variable left in output")

    def test_no_leftover_format_escaping(self):
        """These were {{ }} for str.format(); the renderer would send them
        literally to the model."""
        for path in _all_template_files():
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("{{", text)
                self.assertNotIn("}}", text)

    def test_exactly_one_separator(self):
        for path in _all_template_files():
            with self.subTest(template=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(
                    text.count(PROMPT_SEPARATOR), 1,
                    f"{path.name} must contain exactly one PROMPT_SEPARATOR",
                )

    def test_both_halves_are_non_empty(self):
        for name, (prompts_dir, keys) in TEMPLATES.items():
            with self.subTest(template=name):
                system, user = load_prompt(name, {k: "X" for k in keys}, prompts_dir=prompts_dir)
                self.assertTrue(system.strip(), f"{name}: empty system prompt")
                self.assertTrue(user.strip(), f"{name}: empty user prompt")

    def test_blocks_are_balanced(self):
        for path in _all_template_files():
            with self.subTest(template=path.name):
                lines = path.read_text(encoding="utf-8").splitlines()
                depth = 0
                for ln in lines:
                    s = ln.strip()
                    if s.startswith("@block"):
                        depth += 1
                    elif s == "@end":
                        depth -= 1
                    self.assertGreaterEqual(depth, 0, f"{path.name}: @end without @block")
                self.assertEqual(depth, 0, f"{path.name}: {depth} unclosed @block")


# ── agentnode: the one called in a loop, so it gets the close attention ──────

class _Sub:
    name = "helper"
    description = "Help with a focused task"
    when_to_use = "the user wants a focused task delegated"


def _tools():
    from src.tools import INTERNAL_TOOLS

    return INTERNAL_TOOLS


RICH = dict(
    conversation="user: analyze sales\nassistant: reading data...",
    current_task="Compute Q3 totals",
    execution_history=[{"step": 1, "type": "tool", "name": "read_file", "status": "ok"}],
    execution_memory_index=[{"key": "tool_1", "tokens": 8200, "in_context": True}],
    context_memory={"budget_tokens": 5000, "used_tokens": 2100, "truncated": False},
    learned_experiences="1. Prefer read_file first",
)

# Behavioural rules that must survive the redundancy cleanup. If one of these
# disappears the agent silently loses a capability or a guardrail.
REQUIRED_RULES = [
    "session_intent",
    "planner_exit",
    "context_select",
    "context_selector",
    "from_token",
    "ask_user",
    "armory_call",
    "spawn_children",
    "child_calls",
    "FIFO",
    "truncated",
    "Markdown",
    "may call a sub-agent again",
]


class TestAgentNodePrompt(unittest.TestCase):
    def _render(self, **kw):
        base = dict(
            user_query="Summarize report.csv",
            tools=_tools(),
            execution_history=[],
            execution_memory_index=[],
            context_memory={},
        )
        base.update(kw)
        return agentnode_prompt_loader(**base)

    def test_sparse_call_drops_every_empty_section(self):
        system, user = self._render(turn_start=True)
        # NB: the literal word "preloaded_context" legitimately appears in the
        # user-memory rules, so assert on the tag the block actually emits.
        for absent in ("Prior Plan Context", "Previous Experiences", "Sub-agents:",
                       "User Preferences",
                       "<preloaded_context>", "(none)", "(none available)"):
            self.assertNotIn(absent, system + user, f"{absent!r} should not render when empty")

    def test_rich_call_includes_every_populated_section(self):
        system, user = self._render(subagents=[_Sub()], **RICH)
        for present in ("Prior Plan Context", "current_task", "execution_history",
                        "execution_memory_index", "context_memory", "Previous Experiences",
                        "Skills", "Sub-agents"):
            self.assertIn(present, system + user)

    def test_all_behavioural_rules_survived(self):
        system, user = self._render(turn_start=True, subagents=[_Sub()], **RICH)
        combined = system + user
        for rule in REQUIRED_RULES:
            self.assertIn(rule, combined, f"rule lost in migration: {rule!r}")

    def test_session_intent_instruction_only_at_turn_start(self):
        _, user_start = self._render(turn_start=True)
        _, user_mid = self._render(turn_start=False)
        self.assertIn("<session_intent>", user_start)
        self.assertNotIn("<session_intent>", user_mid)

    def test_system_prompt_is_identical_regardless_of_turn(self):
        """The role and persona stay stable regardless of volatile context."""
        sys_a, _ = self._render(turn_start=True)
        sys_b, _ = self._render(turn_start=False, **RICH)
        self.assertEqual(sys_a, sys_b)

    def test_volatile_state_lives_only_in_the_user_half(self):
        system, user = self._render(subagents=[_Sub()], **RICH)
        for volatile in ("Compute Q3 totals", "analyze sales", "Prefer read_file first"):
            self.assertIn(volatile, user)
            self.assertNotIn(volatile, system)

    def test_main_context_blocks_render_first_in_required_order(self):
        _, user = self._render(turn_start=True, **RICH)
        positions = [
            user.index("Turn Start:"),
            user.index("Latest User Message:"),
            user.index("Prior Plan Context:"),
            user.index("execution_history (meta only"),
            user.index("execution_memory_index (keys + meta"),
        ]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(positions[-1], user.index("Constraints:"))

    def test_static_scaffolding_lives_only_in_the_system_half(self):
        system, user = self._render(subagents=[_Sub()], **RICH)
        self.assertIn("autonomous agent", system)
        self.assertIn("Persona:", system)
        for normal in ("Skills", "Constraints", "planner_exit", "Context memory rules"):
            self.assertIn(normal, user)
            self.assertNotIn(normal, system)

    def test_system_prompt_contains_only_role_and_persona(self):
        system, _ = self._render(subagents=[_Sub()], **RICH)
        self.assertIn("RiminiOne", system)
        for excluded in ("Constraints", "Skills", "Latest User Message", "planner_exit"):
            self.assertNotIn(excluded, system)

    def test_user_preferences_have_a_dedicated_section(self):
        _, user = self._render(
            preloaded_context={
                "preferences": {"agent": {"response_style": "concise"}},
                "user": {"uid": "u1"},
            }
        )
        self.assertIn("User Preferences", user)
        self.assertIn("response_style", user)
        self.assertEqual(user.count("response_style"), 1)

    def test_preloaded_context_renders_when_given(self):
        _, user = self._render(preloaded_context={"uid": "u1"})
        self.assertIn("<preloaded_context>", user)

    def _scaffold_tokens(self, system, user, payload_chars):
        return count_tokens("X" * (len(system) + len(user) - payload_chars))["input"]

    def test_scaffolding_stays_within_budget(self):
        """Baseline before this migration was ~1887 tok of scaffolding on every
        call, re-sent up to max_loops times per turn. Fail loudly on re-bloat."""
        tools_text = "\n".join(f"- {t.name}: {t.description}" for t in _tools())

        system, user = self._render(turn_start=True)
        sparse = self._scaffold_tokens(system, user, len(tools_text) + len("Summarize report.csv"))
        self.assertLess(sparse, 1300, f"sparse scaffolding re-bloated to {sparse} tok")

        system, user = self._render(subagents=[_Sub()], **RICH)
        rich = self._scaffold_tokens(system, user, len(tools_text) + len("Summarize report.csv"))
        self.assertLess(rich, 1800, f"rich scaffolding re-bloated to {rich} tok")
        self.assertLess(sparse, rich, "gating should make the sparse call cheaper")


class TestFastPrompt(unittest.TestCase):
    def test_fast_prompt_omits_armory_block(self):
        system, user = load_prompt(
            "fast_agent",
            {
                "persona": "assistant",
                "user_query": "hey",
                "conversation": "user: hey",
            },
            prompts_dir=_MAIN,
        )
        combined = system + user
        self.assertNotIn("Armory:", combined)
        self.assertNotIn("Tools:", combined)
        self.assertNotIn("Subagents:", combined)
        self.assertIn("action: `planner` or `exit`", combined)
        self.assertNotIn("planner_exit", combined)

    def test_fast_prompt_uses_light_output_contract(self):
        _, user = load_prompt(
            "fast_agent",
            {"persona": "assistant", "user_query": "hey", "conversation": ""},
            prompts_dir=_MAIN,
        )
        self.assertIn("<action>planner</action>", user)
        self.assertIn("<action>exit</action>", user)
        self.assertNotIn("<task>", user)
        self.assertNotIn("<planner_exit>", user)


if __name__ == "__main__":
    unittest.main(verbosity=2)
