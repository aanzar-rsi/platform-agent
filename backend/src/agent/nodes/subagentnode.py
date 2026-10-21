"""
Sub-agent node — delegates a focused task to a configured armory sub-agent.

Reads the task from `next_step`, runs the sub-agent (e.g. a separate
LLM call with a specialist system prompt), and writes the outcome back
into `execution_history` and `execution_memory` for the parent agent
to reason about.

Sub-agents return a best-effort result for each invocation. The planner
may call the same sub-agent again when more work is needed.
"""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from src.agent.control import NOT_PAUSED, maybe_pause, note_text_from_resume
from src.agent.memory import count_content_tokens, record_execution, record_human_input
from src.agent.policy_schema import armory_resource_allowed
from src.agent.state import PlanExecuteState
from src.agent.subagent_stream import emit_subagent_event
from src.subagents.registry import BUILTIN_SUBAGENTS, get_subagents, resolve_subagent
from src.utils.text_truncate import truncate_for_aimessage


# Builtin adapters + test overrides.
_SUBAGENT_REGISTRY: dict = {spec.name: spec.adapter for spec in BUILTIN_SUBAGENTS}

def subagent_node(state: PlanExecuteState, config: RunnableConfig | None = None) -> dict:
    """
    Responsibilities:
    - Read next_step["agent_name"] and next_step["task"] set by agent_node.
    - Delegate the task to the matching sub-agent in _SUBAGENT_REGISTRY.
    - Append the result to execution_history and execution_memory.
    - Auto-ingest into context_memory (FIFO).
    - Return a truncated-result AIMessage for UI history.
    """

    from src.utils.trace import in_run, emit as trace_emit

    traced = in_run()
    paused_resume = maybe_pause(config, node="subagent_node")
    if paused_resume is not NOT_PAUSED:
        note = note_text_from_resume(paused_resume).strip()
        if note:
            history, memory, context = record_human_input(
                state.get("execution_history"), state.get("execution_memory"), state.get("context_memory"),
                value=note, description="User instruction supplied while subagent execution was paused",
                task=(state.get("next_step") or {}).get("task") or "",
            )
            return {
                "messages": [
                    HumanMessage(
                        content=note,
                        additional_kwargs={
                            "ui_hidden": True,
                            "ui_step": {"type": "reasoning", "content": f"User response: {note}"},
                        },
                    )
                ],
                "execution_history": history,
                "execution_memory": memory,
                "context_memory": context,
            }
        return {}

    next_step         = state["next_step"]
    execution_history = list(state.get("execution_history", []))
    execution_memory  = dict(state.get("execution_memory", {}))
    context_memory    = state.get("context_memory")
    preloaded_context = dict(state.get("preloaded_context") or {})

    # Inject authenticated uid so adapters can attribute work per user.
    configurable = (config or {}).get("configurable") or {}
    uid = configurable.get("owner_id")
    if uid and "uid" not in preloaded_context:
        preloaded_context["uid"] = uid

    agent_name = next_step.get("agent_name", "")
    task       = next_step.get("task", "")
    # Extra structured info agent supplied on the agent_call (e.g. answers to a
    # prior needs_clarification, or extra parameters) — forwarded so the
    # sub-agent can resolve things in this single call instead of a round trip.
    tool_args = next_step.get("tool_args") or {}
    if tool_args:
        preloaded_context = {**preloaded_context, "parameters": tool_args}

    try:
        from src.utils.agent_logger import log_subagent

        log_subagent("start", agent_name=agent_name, task=task)
    except Exception:
        pass
    emit_subagent_event(agent_name, {"kind": "start", "message": "Starting"})

    subagent = _SUBAGENT_REGISTRY.get(agent_name)
    if subagent is None:
        spec = resolve_subagent(agent_name, uid)
        subagent = spec.adapter if spec else None
    if subagent is None:
        available = sorted(
            set(_SUBAGENT_REGISTRY) | {s.name for s in get_subagents(uid)} | {s.name for s in BUILTIN_SUBAGENTS}
        )
        result = (
            f"Unknown sub-agent: '{agent_name}'."
            + (f" Available: {available}" if available else " No sub-agents are registered.")
        )
        success = False
    elif ((configurable.get("enabled_subagents") is not None and agent_name not in configurable["enabled_subagents"])
          or ("policy" in configurable and not armory_resource_allowed(
              ((configurable.get("policy") or {}).get("armory") or {}),
              group="subagents", name=agent_name))):
        result = f"Sub-agent '{agent_name}' is disabled for this session."
        success = False
    else:
        try:
            result = subagent(task, preloaded_context)
            success = True
        except Exception as e:
            result  = str(e)
            success = False

    # Structured side-channel some adapters stash on the
    # context dict — lets the output security gate decide whether a human interrupt
    # is needed without parsing the free-text report meant for the LLM/user.
    structured = preloaded_context.pop("_subagent_structured_result", None)

    history_entry = {
        "type":       "subagent",
        "agent_name": agent_name,
        "task":       task,
        "result":     result,
        "success":    success,
        "structured": structured,
        "status": "completed" if success else "failed",
    }
    step_key = f"subagent_{len(execution_history) + 1}"
    execution_memory, context_memory, stored_entry = record_execution(
        execution_memory,
        context_memory,
        key=step_key,
        value=result,
        description=task or f"Result of subagent {agent_name or 'unknown'}",
        entry_type="subagent",
        name=agent_name,
        task=task,
        success=success,
        metadata={"agent_name": agent_name, "structured": structured,
                  "status": "completed" if success else "failed"},
    )
    history_entry.update(stored_entry)
    execution_history.append(history_entry)

    tokens = count_content_tokens(result)

    try:
        from src.utils.agent_logger import log_subagent

        log_subagent(
            "end",
            agent_name=agent_name,
            task=task,
            key=step_key,
            result=result,
            success=success,
            tokens=tokens,
        )
    except Exception:
        pass
    emit_subagent_event(
        agent_name,
        {
            "kind": "complete" if success else "error",
            "message": "Completed" if success else result,
        },
    )

    preview = truncate_for_aimessage(result)
    return {
        "messages": [
            AIMessage(
                content=f"Subagent '{agent_name}' result: {preview}",
                additional_kwargs={
                    "ui_hidden": True,
                    "ui_step": {
                        "type": "subagent",
                        "subagent": {
                            "id": step_key,
                            "agent_name": agent_name,
                            "task": task,
                            "result": preview,
                            "success": history_entry.get("success", True),
                            "status": "done" if success else "error",
                            "progress": [],
                        },
                    },
                },
            )
        ],
        "execution_history": execution_history,
        "execution_memory": execution_memory,
        "context_memory": context_memory,
    }
