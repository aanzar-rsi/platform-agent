"""
Agent node — the reasoning core of the graph.

Receives the current state, decides what to do next, and writes `next_step`
to direct the conditional edges. It calls an LLM to plan, reflect, or
produce a final answer.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from contextvars import copy_context
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from src.agent.control import maybe_pause, note_text_from_resume
from src.agent.memory import (
    build_execution_memory_index,
    empty_context_memory,
    record_execution,
    slim_execution_history,
)
from src.agent.state import PlanExecuteState
from src.agent.token_stream import emit_token
from src.models.llm_client import DEFAULT_MODEL
from src.models.llm_client import call_llm_stream
from src.prompts.prompt_loader import fast_agent_prompt_loader, planner_agent_prompt_loader
from src.agent.facets import Armory

# Learned-experience retrieval is advisory-only (see prompt: "may be empty or
# irrelevant") but sits in front of *every* planning LLM call. A single small
# thread pool bounds how long we ever wait for it, so a slow/unreachable
# embedding backend degrades to "no experiences this turn" instead of
# stalling the entire turn by tens of seconds.
_EXPERIENCE_TIMEOUT_SECONDS = 4.0
_experience_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="learned-exp")


def _safe_learned_experiences(
    user_query: str,
    execution_history: list,
    *,
    uid: str | None = None,
    available_resources: set[tuple[str, str]] | None = None,
) -> str:
    """Retrieve experience chunks; never raise into the agent loop and never
    block it for more than a few seconds."""
    try:
        from src.subagents.learner_agent.retrieve import (
            format_experiences_for_prompt,
            retrieve_experiences,
        )

        prior_task = ""
        prior_tool = ""
        if execution_history:
            last = execution_history[-1] or {}
            prior_task = last.get("task") or ""
            prior_tool = last.get("tool_name") or last.get("agent_name") or ""

        future = _experience_executor.submit(copy_context().run, retrieve_experiences,
                                             user_query, prior_task=prior_task,
                                             prior_tool=prior_tool, execution_history=execution_history,
                                             available_resources=available_resources, uid=uid)
        try:
            chunks = future.result(timeout=_EXPERIENCE_TIMEOUT_SECONDS)
        except FutureTimeoutError:
            try:
                from src.utils.agent_logger import log_event

                log_event("agent.learned_experiences_timeout", timeout_s=_EXPERIENCE_TIMEOUT_SECONDS)
            except Exception:
                pass
            return "(none)"
        return format_experiences_for_prompt(chunks)
    except Exception:
        return "(none)"


def _extract_tag(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _parse_parameters(params_xml: str) -> dict:
    def _clean(value: str) -> str:
        text = value.strip()
        if text.startswith("<![CDATA[") and text.endswith("]]>"):
            text = text[len("<![CDATA["):-len("]]>")].strip()
        return text

    return {
        m.group(1): _clean(m.group(2))
        for m in re.finditer(r"<(\w+)>(.*?)</\1>", params_xml, re.DOTALL)
    }


def _coerce_int(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _parse_child_calls(raw: str) -> list[dict]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except Exception:
        return []
    if not isinstance(parsed, list):
        return []
    calls: list[dict] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        task = str(item.get("task") or "").strip()
        if not task:
            continue
        parameters = item.get("parameters") if isinstance(item.get("parameters"), dict) else {}
        requested_policy = (item.get("requested_policy")
                            if isinstance(item.get("requested_policy"), dict)
                            else None)
        calls.append({
            "task": task,
            "parameters": parameters,
            "requested_policy": requested_policy,
        })
    return calls


def _map_plan_step_to_next_step(step: dict) -> dict:
    action = step.get("action")
    if action == "armory_call":
        return {"action": "armory", "resource_type": step.get("resource_type"),
                "resource_name": step.get("name"), "arguments": step.get("parameters") or {},
                "task": step.get("task") or ""}
    if action == "spawn_children":
        calls = step.get("child_calls") if isinstance(step.get("child_calls"), list) else []
        return {"action": "child_agent", "task": step.get("task") or "", "child_calls": calls}
    if action == "collect_child":
        return {"action": "collect_child", "child_agent_id": (step.get("parameters") or {}).get("child_agent_id") or step.get("name") or "",
                "task": step.get("task") or ""}
    if action == "context_select":
        params = step.get("parameters") or {}
        return {
            "action": "context_select",
            "key": params.get("key") or "",
            "from_token": _coerce_int(params.get("from_token"), 0) or 0,
            "to_token": _coerce_int(params.get("to_token"), None),
            "task": step.get("task") or "",
        }
    if action == "ask_user":
        params = step.get("parameters") or {}
        options = params.get("options")
        if isinstance(options, str):
            options = [o.strip() for o in options.split("|") if o.strip()]
        return {
            "action": "ask_user",
            "question": params.get("question") or step.get("task") or "Could you clarify?",
            "options": options if isinstance(options, list) else [],
            "task": step.get("task") or "",
        }
    if action == "finish":
        return {"action": "finish", "answer": (step.get("parameters") or {}).get("answer") or step.get("task") or ""}
    return {"action": "finish", "answer": f"Unsupported planned action: {action}"}


def _run_stream(stream, on_token=None) -> str:
    """
    Consume the LLM stream, call on_token for each visible chunk, return the full buffer.

    Streams reasoning and, for exit actions, user-facing data.
    """
    buffer = ""
    exit_mode = None
    emitted = {"reasoning": "", "output": ""}
    completed: set[str] = set()

    def emit_tag(tag: str, channel: str) -> None:
        if channel in completed or not on_token:
            return
        open_tag = f"<{tag}>"
        close_tag = f"</{tag}>"
        open_pos = buffer.find(open_tag)
        if open_pos == -1:
            return
        content_start = open_pos + len(open_tag)
        close_pos = buffer.find(close_tag, content_start)
        content_end = close_pos if close_pos != -1 else len(buffer)
        if close_pos == -1:
            for size in range(1, min(len(close_tag), content_end - content_start) + 1):
                if buffer[content_end - size : content_end] == close_tag[:size]:
                    content_end -= size
                    break
        available = buffer[content_start:content_end]
        if len(available) > len(emitted[channel]):
            on_token(available[len(emitted[channel]) :], channel)
            emitted[channel] = available
        if close_pos != -1:
            completed.add(channel)

    for chunk in stream:
        buffer += chunk

        if exit_mode is None:
            action = _extract_tag(buffer, "action").lower()
            if action:
                exit_mode = action in {"exit", "planner_exit", "none"}
            elif "<planner_exit>True</planner_exit>" in buffer:
                exit_mode = True
            elif "<planner_exit>False</planner_exit>" in buffer:
                exit_mode = False

        if exit_mode is not None:
            emit_tag("reasoning", "reasoning")
            if exit_mode:
                if "<output>" in buffer:
                    emit_tag("output", "output")
                else:
                    emit_tag("data", "output")

    return buffer


def _latest_human_content(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        extra = getattr(msg, "additional_kwargs", {}) or {}
        if getattr(msg, "type", None) == "human" and not extra.get("ui_hidden"):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _is_turn_start(messages: list[BaseMessage]) -> bool:
    """True on the first agent visit after a new human message this invoke."""
    if not messages:
        return False
    extra = getattr(messages[-1], "additional_kwargs", {}) or {}
    return getattr(messages[-1], "type", None) == "human" and not extra.get("ui_hidden")


def _format_conversation(messages: list[BaseMessage], limit: int = 12) -> str:
    """Only expose the newest top-level request; prior context is memory-gated."""
    lines: list[str] = []
    for msg in reversed(messages):
        extra = getattr(msg, "additional_kwargs", {}) or {}
        if isinstance(extra, dict) and extra.get("ui_hidden"):
            continue
        role = getattr(msg, "type", "unknown")
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        lines.append(f"{role}: {content}")
        break
    return "\n".join(lines)


def _pending_children(execution_history: list[dict]) -> list[str]:
    return [entry["child_agent_id"] for entry in execution_history
            if entry.get("child_agent_id") and entry.get("status") == "running"]


def _parse_response(buffer: str, *, turn_start: bool) -> dict:
    """Parse the full LLM response into a state update dict."""
    action_raw = _extract_tag(buffer, "action").strip().lower()
    planner_exit = action_raw in {"exit", "planner_exit"} or _extract_tag(buffer, "planner_exit") == "True"
    task = _extract_tag(buffer, "task")
    intent = _extract_tag(buffer, "session_intent").lower()

    if planner_exit:
        answer = _extract_tag(buffer, "output") or _extract_tag(buffer, "data")
        reasoning = _extract_tag(buffer, "reasoning")
        update = {
            "current_task": "finish",
            "next_step": {"action": "finish", "answer": answer},
            "messages": [
                AIMessage(
                    content=answer,
                    additional_kwargs={
                        "ui_step": {"type": "reasoning", "content": reasoning}
                    }
                    if reasoning
                    else {},
                )
            ],
        }
    else:
        name = _extract_tag(buffer, "name") or _extract_tag(buffer, "tool") or _extract_tag(buffer, "operation")
        params_xml = _extract_tag(buffer, "parameters")
        params = _parse_parameters(params_xml)
        reasoning = _extract_tag(buffer, "reasoning")

        if action_raw == "context_select" or name == "context_selector":
            next_step = {
                "action": "context_select",
                "key": params.get("key") or "",
                "from_token": _coerce_int(params.get("from_token"), 0) or 0,
                "to_token": _coerce_int(params.get("to_token"), None),
                "task": task,
            }
        elif action_raw == "collect_child" or name == "collect_child":
            next_step = {"action": "collect_child", "child_agent_id": params.get("child_agent_id") or name,
                         "task": task}
        elif action_raw == "spawn_children" or name == "spawn_children":
            next_step = {
                "action": "child_agent",
                "task": task,
                "child_calls": _parse_child_calls(params.get("child_calls") or ""),
            }
        elif action_raw in {"plan", "planner", "continue", "retry"}:
            data = _extract_tag(buffer, "data")
            batch_data = data if data.lstrip().startswith(("{", "[")) else ""
            next_step = {
                "action": "plan",
                "task": task,
                "steps_json": params.get("steps_json") or batch_data,
            }
        elif action_raw == "armory_call":
            next_step = {
                "action": "armory",
                "resource_type": params.pop("resource_type", "tool"),
                "resource_name": name,
                "task": task,
                "arguments": params,
            }
        elif action_raw == "ask_user":
            question = (params.get("question") or "").strip()
            prompt_alias = (params.get("prompt") or "").strip()
            if not question and prompt_alias:
                question = prompt_alias
            options_raw = params.get("options")
            if isinstance(options_raw, list):
                options = [str(o).strip() for o in options_raw if str(o).strip()]
            else:
                options = [o.strip() for o in str(options_raw or "").split("|") if o.strip()]
            next_step = {
                "action": "ask_user",
                "question": question or reasoning or "Could you clarify?",
                "options": options,
                "task": task,
            }
        else:
            next_step = {"action": "armory", "resource_type": "tool", "resource_name": name,
                         "arguments": params, "task": task}

        step_content = reasoning or f"Calling {name}"
        update = {
            "current_task": task,
            "next_step": next_step,
            "messages": [
                AIMessage(
                    content=step_content,
                    additional_kwargs={
                        "ui_hidden": True,
                        "ui_step": {"type": "reasoning", "content": step_content},
                    },
                )
            ],
        }

    if turn_start and intent == "restart":
        update["execution_history"] = []
        update["execution_memory"] = {}
        update["context_memory"] = empty_context_memory()
        if planner_exit:
            update["current_task"] = "finish"

    return update


def agent_node(state: PlanExecuteState, config: RunnableConfig | None = None) -> dict:
    """
    Responsibilities:
    - Read messages, execution_memory index, and context_memory to understand progress.
    - On turn start, decide continue vs restart of prior plan scratch.
    - Decide the next action: armory, child_agent, context_select, or finish.
    - Write next_step so conditional edges can route control correctly.

    next_step conventions:
        {"action": "armory", "resource_type": "<type>", "resource_name": "<name>", "arguments": {...}}
        {"action": "child_agent",     "task": "<desc>", "child_calls": [{...}]}
        {"action": "context_select",  "key": "<em_key>", "from_token": int, "to_token": int|None}
        {"action": "ask_user",        "question": "<question>", "options": [...]}
        {"action": "finish",          "answer": "<final response>"}
    """
    from src.agent.edges.routing import AGENT_NODE as _AGENT_NODE
    from src.utils.trace import in_run, emit as trace_emit

    traced = in_run()

    paused_resume = maybe_pause(config, node=_AGENT_NODE)
    injected_note = note_text_from_resume(paused_resume).strip()

    messages = list(state["messages"])

    turn_start = _is_turn_start(messages)
    user_query = _latest_human_content(messages)

    execution_history = state.get("execution_history", [])

    pending_children = _pending_children(execution_history)
    has_child_history = any(entry.get("type") == "child_agent" for entry in execution_history)
    execution_memory = state.get("execution_memory", {})
    context_memory = state.get("context_memory") or empty_context_memory()
    preloaded = state.get("preloaded_context") or {}

    configurable = (config or {}).get("configurable") or {}
    uid = configurable.get("owner_id")

    # The newest top-level request stays direct. Older top-level human inputs
    # are durable/selectable instead of being blindly replayed in conversation.
    original_execution_memory = execution_memory
    for index, message in enumerate(messages[:-1], start=1):
        if getattr(message, "type", None) != "human":
            continue
        extra = getattr(message, "additional_kwargs", {}) or {}
        if extra.get("ui_hidden"):
            continue  # clarification/pause inputs are recorded by their nodes
        key = f"human_message_{index}"
        if key in execution_memory:
            continue
        value = message.content if isinstance(message.content, str) else str(message.content)
        execution_memory, context_memory, _ = record_execution(
            execution_memory, context_memory, key=key, value=value,
            description="Prior top-level user request", entry_type="human_input",
            name="user", task="Conversation context",
        )

    if injected_note:
        from src.agent.nodes.output_security_gate import sanitize_executor_output

        execution_id = str(configurable.get("execution_id") or "execution")
        return {"executor_output": sanitize_executor_output({
            "version": 1, "action_id": f"{execution_id}:agent-pause:{len(messages)}",
            "source": "human_input", "results": [{
                "kind": "human_input", "value": injected_note, "success": True,
                "task": "Pause instruction", "description": "User instruction supplied while agent was paused",
                "metadata": {"input_kind": "paused"},
            }],
        })}

    # Child IDs are runtime-generated, so the deterministic next action is to
    # collect pending children before asking the planner to decide anything else.
    if pending_children:
        child_id = pending_children[0]
        update = {
            "current_task": "collect_child",
            "next_step": {
                "action": "collect_child",
                "child_agent_id": child_id,
                "task": "Collect outstanding child before continuing",
            },
            "messages": [AIMessage(content=f"Collecting child {child_id}", additional_kwargs={"ui_hidden": True})],
        }
        if execution_memory is not original_execution_memory:
            update.update(execution_memory=execution_memory, context_memory=context_memory)
        return update

    effective_armory = (configurable.get("policy") or {}).get("armory") or {}
    resources = Armory(effective_armory, user_id=uid,
                       preloaded_context=state.get("preloaded_context")).list(reconnect=True)
    tools = [resource for resource in resources if resource.type == "tool"]
    subagents = [resource for resource in resources if resource.type == "subagent"]
    available_resources = {(resource.type, resource.name) for resource in resources}
    available_resources.update(
        ("mcp_server", resource.name) for resource in resources
        if resource.type == "tool" and resource.name.startswith("mcp_")
    )
    learned = _safe_learned_experiences(
        user_query, execution_history, uid=uid, available_resources=available_resources,
    ) if uid else "(none)"

    first_request = sum(getattr(message, "type", None) == "human" for message in messages) == 1 and not execution_history
    use_fast_prompt = first_request or len((user_query or "").strip()) < 10
    conversation_text = _format_conversation(messages) + (
        "\nPending child IDs: " + ", ".join(pending_children)
        + ". To collect one, use <action>collect_child</action> and <parameters><child_agent_id>ID</child_agent_id></parameters>."
        if pending_children else ""
    )
    # Fast/direct answering is safe only before execution memory exists. Every
    # LLM call after an external input receives the complete index + FIFO view.
    use_fast_prompt = use_fast_prompt and not execution_memory and not state.get("planner_mode")
    if use_fast_prompt:
        system_prompt, prompt = fast_agent_prompt_loader(
            user_query=user_query,
            tools=tools,
            subagents=subagents,
            conversation=conversation_text,
            learned_experiences=learned,
        )
    else:
        system_prompt, prompt = planner_agent_prompt_loader(
            user_query=user_query,
            tools=tools,
            subagents=subagents,
            execution_history=slim_execution_history(execution_history),
            execution_memory_index=build_execution_memory_index(execution_memory, context_memory),
            context_memory=context_memory,
            conversation=conversation_text,
            current_task=state.get("current_task", ""),
            max_plan_steps=int(configurable.get("max_plan_steps") or 8),
            child_mode=bool(configurable.get("child_agent_id")),
            planner_error=state.get("planner_error"),
            learned_experiences=learned,
        )

    if traced:
        trace_emit("guardrail.input.check", data={"guardrail_type": "input"}, component="agent_node")
    if not isinstance(user_query, str):
        if traced:
            trace_emit("guardrail.decision.deny", status="denied", error=ValueError("invalid_input"),
                       data={"guardrail_type": "input", "decision": "deny", "reason_code": "invalid_input"},
                       component="agent_node")
        raise ValueError("invalid_input")
    if traced:
        trace_emit("guardrail.decision.allow", data={"guardrail_type": "input", "decision": "allow"},
                   component="agent_node")

    stream = call_llm_stream(
        prompt,
        system_prompt=system_prompt,
        model_id=configurable.get("model_id") or DEFAULT_MODEL,
    )

    def _on_token(text: str, channel: str) -> None:
        emit_token(text, channel)

    buffer = _run_stream(stream, on_token=_on_token)
    update = {
        "planner_response": buffer,
        "planner_response_type": "classifier" if use_fast_prompt else "planner",
        "planner_resources": [{"type": resource.type, "name": resource.name} for resource in resources],
        "next_step": {"action": "validate_response"},
    }

    if configurable.get("child_agent_id") and update.get("planned_phases"):
        phases = update["planned_phases"]
        if any(step.get("action") == "spawn_children" for phase in phases for step in phase.get("steps", [])):
            update = _planner_escalation_error(
                "nested_child_spawn",
                "child agents must complete their assigned task directly and cannot spawn children",
            )

    if has_child_history and update.get("planned_phases"):
        phases = update["planned_phases"]
        if any(step.get("action") == "spawn_children" for phase in phases for step in phase.get("steps", [])):
            child_results = [entry.get("result") for entry in execution_history
                             if entry.get("type") == "child_agent" and entry.get("result")]
            summary = "\n\n".join(str(result) for result in child_results)
            answer = (
                "The child agents completed, but did not return usable data.\n\n" + summary
                if summary else "The child agents completed without usable results."
            )
            update = {
                "current_task": "finish",
                "next_step": {"action": "finish", "answer": answer},
                "messages": [AIMessage(content=answer)],
                "planned_phases": [],
                "planned_phase_index": 0,
            }

    if update.get("next_step", {}).get("action") == "finish" and pending_children:
        child_id = pending_children[0]
        update["next_step"] = {"action": "collect_child", "child_agent_id": child_id,
                               "task": "Collect outstanding child before finishing"}
        update["current_task"] = "collect_child"
        # Replan after collection: the previous draft was written without the child's answer.
        update["messages"] = [AIMessage(content=f"Collecting child {child_id}",
                                        additional_kwargs={"ui_hidden": True})]

    try:
        from src.utils.agent_logger import log_agent_decision

        next_step = update.get("next_step") or {}
        log_agent_decision(
            turn_start=turn_start,
            user_query=user_query,
            current_task=update.get("current_task") or state.get("current_task") or "",
            action=next_step.get("action"),
            tool_name=next_step.get("tool_name"),
            agent_name=next_step.get("agent_name"),
            task=next_step.get("task") or "",
            tool_args=next_step.get("tool_args") or {},
            key=next_step.get("key"),
            from_token=next_step.get("from_token"),
            to_token=next_step.get("to_token"),
            answer=next_step.get("answer"),
            reasoning=_extract_tag(buffer, "reasoning"),
            session_intent="",
            raw_buffer=buffer,
            learned_experiences_chars=len(learned or ""),
        )
    except Exception:
        pass

    if injected_note:
        update["messages"] = [
            HumanMessage(
                content=injected_note,
                additional_kwargs={
                    "ui_hidden": True,
                    "ui_step": {"type": "reasoning", "content": f"User response: {injected_note}"},
                },
            )
        ] + list(update.get("messages", []))

    if execution_memory is not original_execution_memory and "execution_memory" not in update:
        update.update(execution_memory=execution_memory, context_memory=context_memory)

    if traced:
        if update.get("next_step", {}).get("action") == "finish":
            trace_emit("guardrail.output.check", data={"guardrail_type": "output"}, component="agent_node")
            if not isinstance(update["next_step"].get("answer"), str):
                trace_emit("guardrail.decision.deny", status="denied", error=ValueError("invalid_output"),
                           data={"guardrail_type": "output", "decision": "deny", "reason_code": "invalid_output"},
                           component="agent_node")
                raise ValueError("invalid_output")
            trace_emit("guardrail.decision.allow", data={"guardrail_type": "output", "decision": "allow"},
                       component="agent_node")

    return update


def _planner_escalation_error(code: str, detail: str) -> dict:
    message = f"Planner escalation failed ({code}): {detail}"
    return {
        "current_task": "finish",
        "next_step": {"action": "finish", "answer": message},
        "messages": [AIMessage(content=message)],
        "planned_phases": [],
        "planned_phase_index": 0,
    }
