"""
Context selector node — loads a token window from execution_memory into context_memory.

No LLM. Agent routes here with next_step:
  {"action": "context_select", "key": "...", "from_token": int, "to_token": int|None}
Always returns to agent_node with updated context_memory.
"""

from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from src.agent.control import NOT_PAUSED, maybe_pause, note_text_from_resume
from src.agent.memory import record_human_input, update_context_memory
from src.agent.state import PlanExecuteState


def _coerce_token(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def context_selector_node(state: PlanExecuteState, config: RunnableConfig | None = None) -> dict:
    paused_resume = maybe_pause(config, node="context_selector")
    if paused_resume is not NOT_PAUSED:
        note = note_text_from_resume(paused_resume).strip()
        if note:
            history, memory, context = record_human_input(
                state.get("execution_history"), state.get("execution_memory"), state.get("context_memory"),
                value=note, description="User instruction supplied while context selection was paused",
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

    next_step = state.get("next_step") or {}
    key = next_step.get("key") or ""
    from_token = _coerce_token(next_step.get("from_token"), 0) or 0
    to_token = _coerce_token(next_step.get("to_token"), None)

    execution_memory = state.get("execution_memory") or {}
    context_memory = state.get("context_memory")
    entry = execution_memory.get(key)

    if entry is None:
        content = f"context_selector error: key '{key}' not found in execution_memory."
    elif isinstance(entry, dict) and ("value" in entry or "result" in entry):
        content = entry.get("value", entry.get("result"))
    else:
        content = entry

    context_memory = update_context_memory(
        context_memory,
        key=key or "_missing",
        content=content,
        from_token=from_token,
        to_token=to_token,
    )

    try:
        from src.utils.agent_logger import log_context_select

        entries = (context_memory or {}).get("entries") or []
        newest = entries[-1] if entries else {}
        log_context_select(
            key=key,
            from_token=from_token,
            to_token=to_token,
            found=entry is not None,
            truncated=bool((context_memory or {}).get("truncated")),
            loaded_tokens=newest.get("tokens"),
            task=next_step.get("task") or "",
        )
    except Exception:
        pass

    return {"context_memory": context_memory}
