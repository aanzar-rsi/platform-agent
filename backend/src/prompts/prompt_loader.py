"""Prompt rendering and loading for every agent and sub-agent in the project.

One generic entry point — `load_prompt(name, context, prompts_dir=...)` — renders
a declarative `.txt` skeleton and splits it into the
(system, user) pair every caller expects. Sections whose `if=` condition fails
are dropped entirely, so absent context costs zero tokens instead of rendering
an empty `(none)` header.

Everything above the separator becomes the small system prompt (role and
persona only); everything below becomes the normal prompt containing the task,
capabilities, constraints, context, and output contract.
"""

import re
from pathlib import Path
from typing import Any

import toons

_PROMPTS_DIR = Path(__file__).parent
PROMPT_SEPARATOR = "--------------------"
_DIRECTIVE = re.compile(r'^[ \t]*@(#|block(?=\s|$)|end(?=\s|$))[ \t]*(.*)$')
_VAR = re.compile(r'\{(\w+)\}')
_IF = re.compile(r'\bif=(\S+)')


class PromptRenderError(Exception):
    """Raised in strict mode when a template references an unknown variable."""


class _Node:
    __slots__ = ("kind", "ident", "cond", "text", "children")

    def __init__(self, kind, ident=None, cond=None, text=None):
        self.kind = kind
        self.ident = ident
        self.cond = cond
        self.text = text
        self.children = []


def _parse(template: str) -> _Node:
    root = _Node("root")
    stack = [root]
    for line in template.splitlines():
        match = _DIRECTIVE.match(line)
        if not match:
            stack[-1].children.append(_Node("text", text=line))
            continue

        keyword, rest = match.group(1), match.group(2).strip()
        if keyword == "#":
            continue
        if keyword == "block":
            parts = rest.split(None, 1)
            ident = parts[0] if parts else ""
            condition_match = _IF.search(parts[1]) if len(parts) > 1 else None
            node = _Node(
                "block",
                ident,
                condition_match.group(1) if condition_match else None,
            )
            stack[-1].children.append(node)
            stack.append(node)
        elif len(stack) > 1:
            stack.pop()
    return root


def _present(context: dict, key: str) -> bool:
    value = context.get(key)
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _eval_cond(condition: str | None, context: dict) -> bool:
    if not condition:
        return True
    for or_group in condition.split("|"):
        matches = True
        for term in or_group.split(","):
            term = term.strip()
            if not term:
                continue
            negated = term.startswith("!")
            present = _present(context, term[1:] if negated else term)
            if not (not present if negated else present):
                matches = False
                break
        if matches:
            return True
    return False


def to_toon(value: Any) -> str:
    """Serialize structured prompt context as TOON."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return toons.dumps(value)
    except Exception:
        return str(value)


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (dict, list, tuple)):
        return to_toon(list(value) if isinstance(value, tuple) else value)
    return str(value)


def _subst(line: str, context: dict, strict: bool) -> str:
    def replace(match):
        name = match.group(1)
        if name not in context:
            if strict:
                raise PromptRenderError(
                    f"template references unknown variable {{{name}}}"
                )
            return ""
        return _fmt(context[name])

    return _VAR.sub(replace, line)


def _render_node(node: _Node, context: dict, output: list, strict: bool) -> None:
    if node.kind == "root":
        for child in node.children:
            _render_node(child, context, output, strict)
    elif node.kind == "block":
        if _eval_cond(node.cond, context):
            for child in node.children:
                _render_node(child, context, output, strict)
    else:
        output.append(_subst(node.text, context, strict))


def _tidy(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return text.strip() + "\n"


def render(template_str: str, context: dict, *, strict: bool = False) -> str:
    output: list[str] = []
    _render_node(_parse(template_str), context, output, strict)
    return _tidy("\n".join(output))


def render_file(path: Path | str, context: dict, *, strict: bool = False) -> str:
    return render(Path(path).read_text(encoding="utf-8"), context, strict=strict)


def _load_module(name: str, version: str = "v1") -> str:
    """Load a versioned reusable prompt module."""
    return (_PROMPTS_DIR / "modules" / name / f"{version}.txt").read_text(
        encoding="utf-8"
    ).strip()


def load_prompt(
    name: str,
    context: dict[str, Any],
    *,
    prompts_dir: Path | str = _PROMPTS_DIR,
    strict: bool = False,
) -> tuple[str, str]:
    """Render `<name>.txt` and split it into (system_prompt, user_prompt).

    This is the single loader for every prompt in the project. Sub-agents pass
    their own `prompts_dir`; everything else uses `src/prompts/`.
    """
    text = render_file(Path(prompts_dir) / f"{name}.txt", context, strict=strict)
    system_prompt, _, user_prompt = text.partition(PROMPT_SEPARATOR)
    return system_prompt.strip(), user_prompt.strip()


def agentnode_prompt_loader(
    user_query: str,
    tools: list,
    execution_history: list[dict[str, Any]],
    execution_memory_index: list[dict[str, Any]],
    context_memory: dict[str, Any],
    *,
    conversation: str = "",
    current_task: str = "",
    turn_start: bool = False,
    preloaded_context: dict[str, Any] | None = None,
    learned_experiences: str = "(none)",
    subagents: list | None = None,
) -> tuple[str, str]:
    """Build the agent node's context and render `agentnode.txt`."""
    tools_text = "\n".join(f"- {t.name}: {t.description}" for t in (tools or []))

    subagents_text = "\n".join(
        f"- {s.name}: {s.description} (when to use: {s.when_to_use})"
        for s in (subagents or [])
    )

    # "(none)" is a real caller default, not absent — treat it as absent so the
    # whole Learned Experiences section drops instead of rendering a dead header.
    experiences = (learned_experiences or "").strip()
    if experiences.lower() in ("(none)", "none"):
        experiences = ""

    preloaded = dict(preloaded_context or {})
    user_preferences = preloaded.pop("preferences", {}) or {}

    context = {
        "persona": _load_module("persona"),
        "constraints": _load_module("constraints"),
        # Available capabilities.
        "tools": tools_text,
        "subagents": subagents_text,
        # tier 2 — turn-volatile
        "user_query": user_query,
        "conversation": conversation,
        # The session_intent tag used to be spliced into all five output
        # templates. It is now stated once, inside the turn_start block, so the
        # output contract stays byte-identical across turns (cacheable) and the
        # instruction simply disappears on turns that must not emit the tag.
        "turn_start": bool(turn_start),
        "learned_experiences": experiences,
        "user_preferences": user_preferences,
        # tier 3 — loop-volatile
        "current_task": current_task,
        "execution_history": execution_history,
        "execution_memory_index": execution_memory_index,
        "context_memory": context_memory,
        "preloaded_context": preloaded,
    }
    return load_prompt("agentnode", context)


def _armory_text(*, tools: list, subagents: list | None = None) -> str:
    tools_text = "\n".join(f"- armory.tool.{t.name}: {t.description}" for t in (tools or []))
    subagents_text = "\n".join(
        f"- armory.subagent.{s.name}: {s.description}"
        for s in (subagents or [])
    )
    static_actions = "\n".join([
        "- spawn_children: start one or more child agent runs",
        "- collect_child: collect one running child result",
        "- context_select: load execution_memory window into context",
        "- ask_user: ask user for required missing detail",
        "- finish: return final answer to user",
    ])
    return "\n".join(
        section for section in [
            "Tools:\n" + tools_text if tools_text else "",
            "Subagents:\n" + subagents_text if subagents_text else "",
            "Control Actions:\n" + static_actions,
        ] if section
    )


def fast_agent_prompt_loader(
    *,
    user_query: str,
    tools: list,
    subagents: list | None = None,
    conversation: str = "",
) -> tuple[str, str]:
    context = {
        "persona": _load_module("persona"),
        "user_query": user_query,
        "conversation": conversation,
    }
    return load_prompt("fast_agent", context)


def planner_agent_prompt_loader(
    *,
    user_query: str,
    tools: list,
    subagents: list | None,
    execution_history: list[dict[str, Any]],
    execution_memory_index: list[dict[str, Any]],
    context_memory: dict[str, Any],
    conversation: str = "",
    current_task: str = "",
    max_plan_steps: int = 8,
    child_mode: bool = False,
    planner_error: dict[str, Any] | None = None,
) -> tuple[str, str]:
    context = {
        "persona": _load_module("persona"),
        "constraints": _load_module("constraints"),
        "user_query": user_query,
        "conversation": conversation,
        "current_task": current_task,
        "execution_history": execution_history,
        "execution_memory_index": execution_memory_index,
        "context_memory": context_memory,
        "armory": _armory_text(tools=tools, subagents=subagents),
        "max_plan_steps": max(1, int(max_plan_steps or 1)),
        "child_mode": child_mode,
        "planner_error": planner_error or {},
    }
    return load_prompt("planner_agent", context)
