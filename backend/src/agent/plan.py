"""Validated, checkpoint-friendly phased plans."""

from __future__ import annotations

import json
import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PlanStep(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    id: str = Field(min_length=1)
    action: Literal["armory_call", "spawn_children", "collect_child", "context_select", "ask_user", "finish"]
    resource_type: Literal["tool", "subagent"] | None = None
    name: str = ""
    task: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    child_calls: list[dict[str, Any]] = Field(default_factory=list)
    uses: list[str] = Field(default_factory=list)


class PlanPhase(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    sequence: int = Field(ge=1)
    steps: list[PlanStep] = Field(min_length=1)


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    batch_name: str = ""
    phases: list[PlanPhase] = Field(min_length=1)

    @model_validator(mode="after")
    def check_order(self):
        prior: set[str] = set()
        for index, phase in enumerate(self.phases, 1):
            if phase.sequence != index:
                raise ValueError("phase sequences must be consecutive starting at 1")
            for step in phase.steps:
                if step.id in prior or any(step.id == other.id for other in phase.steps if other is not step):
                    raise ValueError(f"duplicate step id: {step.id}")
                if len(step.uses) != len(set(step.uses)) or not set(step.uses) <= prior:
                    raise ValueError(f"step {step.id} may only use earlier phase results")
                if step.action == "finish" and (len(phase.steps) != 1 or index != len(self.phases)):
                    raise ValueError("finish must be the sole step of the final phase")
                if step.action == "ask_user" and len(phase.steps) != 1:
                    raise ValueError("ask_user must be alone in its phase")
            prior.update(step.id for step in phase.steps)
        return self


def _escape_unescaped_quotes_in_json_strings(text: str) -> str:
    """Best-effort repair for planner JSON with raw quotes inside string values."""
    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if not in_string:
            out.append(ch)
            if ch == '"':
                in_string = True
                escape = False
            i += 1
            continue

        if escape:
            out.append(ch)
            escape = False
            i += 1
            continue

        if ch == "\\":
            out.append(ch)
            escape = True
            i += 1
            continue

        if ch == '"':
            j = i + 1
            while j < n and text[j].isspace():
                j += 1
            next_sig = text[j] if j < n else ""
            if next_sig in {",", "}", "]", ":", ""}:
                out.append(ch)
                in_string = False
            else:
                out.append('\\"')
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def parse_plan(raw: str, *, max_plan_steps: int, resources: set[tuple[str, str]]) -> list[dict]:
    """Reject the entire plan if any step is invalid or exceeds the runtime limit."""
    if max_plan_steps < 1:
        raise ValueError("max_plan_steps must be positive")

    text = str(raw or "").strip()
    if not text:
        raise ValueError("steps_json is empty")
    if text.startswith("```"):
        lines = text.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    if not text:
        raise ValueError("steps_json is empty")

    # Planner occasionally wraps JSON in prose or appends extra XML fragments.
    # Keep only the first balanced JSON object/array payload.
    open_char = text[0]
    if open_char not in "[{":
        first_obj = text.find("{")
        first_arr = text.find("[")
        starts = [idx for idx in (first_obj, first_arr) if idx >= 0]
        if starts:
            text = text[min(starts):]
            open_char = text[0]
    if text and text[0] in "[{":
        close_char = "}" if text[0] == "{" else "]"
        depth = 0
        in_string = False
        escape = False
        for idx, ch in enumerate(text):
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == text[0]:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0:
                    text = text[: idx + 1]
                    break

    # Repair minor planner drift: trailing commas before closing braces/brackets.
    text = re.sub(r",\s*([}\]])", r"\1", text)

    if not text:
        raise ValueError("steps_json is empty")

    try:
        decoded = json.loads(text, strict=False)
    except json.JSONDecodeError as exc:
        repaired = _escape_unescaped_quotes_in_json_strings(text)
        if repaired != text:
            try:
                decoded = json.loads(repaired, strict=False)
                text = repaired
            except json.JSONDecodeError:
                raise ValueError(
                    f"steps_json is not valid JSON: {exc.msg} (line {exc.lineno} column {exc.colno})"
                ) from None
        else:
            raise ValueError(
                f"steps_json is not valid JSON: {exc.msg} (line {exc.lineno} column {exc.colno})"
            ) from None

    if isinstance(decoded, list):
        decoded = {"phases": decoded}
    if not isinstance(decoded, dict):
        raise ValueError("steps_json must be a JSON object")

    # Normalize common planner shape drift before strict model validation.
    phases = decoded.get("phases")
    if isinstance(phases, list):
        spawn_phase_index = None
        for phase_index, phase in enumerate(phases):
            if not isinstance(phase, dict):
                continue
            if "sequence" not in phase:
                alias = phase.get("phase") if isinstance(phase.get("phase"), int) else phase.get("phase_id")
                if isinstance(alias, int):
                    phase["sequence"] = alias
            phase.pop("phase", None)
            phase.pop("phase_id", None)
            phase.pop("name", None)
            steps = phase.get("steps")
            if not isinstance(steps, list):
                continue
            for step in steps:
                if not isinstance(step, dict):
                    continue
                if not isinstance(step.get("id"), str):
                    step["id"] = str(step.get("id") or f"step-{phase_index + 1}")
                uses = step.get("uses")
                if isinstance(uses, list):
                    # Some planner responses put resource names in `uses`; that
                    # field is only for IDs produced by earlier phases.
                    resource_names = {name for _, name in resources}
                    step["uses"] = [value for value in uses if value not in resource_names]
                if isinstance(step.get("task"), dict):
                    task = step["task"]
                    step["task"] = str(task.get("description") or task.get("notes") or json.dumps(task))
                if step.get("action") != "spawn_children":
                    continue
                calls = step.get("child_calls")
                if not isinstance(calls, list):
                    continue
                normalized_calls = []
                for call in calls:
                    if isinstance(call, dict):
                        if isinstance(call.get("task"), dict):
                            task = call["task"]
                            call["task"] = str(task.get("description") or task.get("notes") or json.dumps(task))
                        normalized_calls.append(call)
                        continue
                    if isinstance(call, str) and call.strip():
                        normalized_calls.append({"task": call.strip()})
                step["child_calls"] = normalized_calls


            spawn_steps = [step for step in steps if isinstance(step, dict) and step.get("action") == "spawn_children"]
            if spawn_steps:
                first = spawn_steps[0]
                first["child_calls"] = [
                    call
                    for step in spawn_steps
                    for call in (step.get("child_calls") or [])
                    if isinstance(call, dict)
                ]
                phase["steps"] = [first]
                spawn_phase_index = phase_index
                break

        # Child IDs are generated at runtime. Any planned collect/finish steps
        # after spawning necessarily reference guessed IDs or unavailable results.
        # Prior phases are also unnecessary setup the model commonly invents
        # (for example a non-existent "decompose_query" tool). Execute only the
        # self-contained spawn phase, then replan from execution_history.
        if spawn_phase_index is not None:
            decoded["phases"] = [phases[spawn_phase_index]]
            for sequence, phase in enumerate(decoded["phases"], 1):
                if isinstance(phase, dict):
                    phase["sequence"] = sequence

        # Context branches each receive the same snapshot, so parallel loads
        # would overwrite one another. Serialize them and replan with the data.
        normalized_phases = []
        serialized_context = False
        for phase in decoded.get("phases", []):
            steps = phase.get("steps") if isinstance(phase, dict) else None
            if not isinstance(steps, list) or not steps:
                normalized_phases.append(phase)
                continue
            context_steps = [
                step for step in steps
                if isinstance(step, dict) and step.get("action") == "context_select"
            ]
            if not context_steps:
                normalized_phases.append(phase)
                continue
            if len(context_steps) != len(steps):
                normalized_phases.append(phase)
                continue
            normalized_phases.extend({"sequence": 0, "steps": [step]} for step in context_steps)
            serialized_context = True
            break
        if serialized_context:
            for sequence, phase in enumerate(normalized_phases, 1):
                if isinstance(phase, dict):
                    phase["sequence"] = sequence
            decoded["phases"] = normalized_phases

    plan = Plan.model_validate(decoded)

    # Normalize common planner aliasing before strict validation checks.
    # The planner sometimes emits ask_user.parameters.prompt instead of
    # ask_user.parameters.question; accept and rewrite to keep execution stable.
    for phase in plan.phases:
        for step in phase.steps:
            if step.action != "ask_user":
                continue
            question = step.parameters.get("question")
            if isinstance(question, str) and question.strip():
                step.parameters["question"] = question.strip()
                continue
            prompt = step.parameters.get("prompt")
            if isinstance(prompt, str) and prompt.strip():
                step.parameters["question"] = prompt.strip()
    if sum(len(phase.steps) for phase in plan.phases) > max_plan_steps:
        raise ValueError("plan exceeds max_plan_steps")
    for phase in plan.phases:
        for step in phase.steps:
            if step.action == "armory_call":
                if not step.resource_type:
                    raise ValueError("armory_call requires resource_type")
                if (step.resource_type, step.name) not in resources:
                    raise ValueError(f"unavailable armory resource: {step.resource_type}.{step.name}")
            if step.action == "spawn_children" and not step.child_calls:
                raise ValueError("spawn_children requires child_calls")
            if step.action == "collect_child" and not (step.parameters.get("child_agent_id") or step.name):
                raise ValueError("collect_child requires child_agent_id")
            if step.action == "context_select" and not step.parameters.get("key"):
                raise ValueError("context_select requires key")
            if step.action == "ask_user" and not step.parameters.get("question"):
                raise ValueError("ask_user requires question")
            if step.action == "finish" and not isinstance(step.parameters.get("answer"), str):
                raise ValueError("finish requires a literal answer")
            if step.action == "finish" and step.uses:
                raise ValueError("finish cannot assume unavailable step results; replan after execution")
            if len(phase.steps) > 1 and step.action != "armory_call":
                raise ValueError("only armory steps may run in parallel")
            if len(phase.steps) > 1 and step.action == "armory_call" and step.resource_type == "tool" and step.name in {
                "edit_file", "execute_bash", "execute_powershell", "execute_python_script",
            }:
                raise ValueError("confirmation-requiring tools must run alone")
    return plan.model_dump()["phases"]
