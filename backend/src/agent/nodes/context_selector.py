"""
Context selector node — loads a token window from execution_memory into context_memory.

No LLM. Agent routes here with next_step:
  {"action": "context_select", "key": "...", "from_token": int, "to_token": int|None}
Always returns to agent_node with updated context_memory.
"""

from langchain_core.runnables import RunnableConfig
from src.agent.control import pause_gate_active, thread_id_from_config
from src.agent.memory import record_context_selection, update_context_memory
from src.agent.state import PlanExecuteState


def _coerce_token(value, default=None):
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def context_selector_node(state: PlanExecuteState, config: RunnableConfig | None = None) -> dict:
    next_step = state.get("next_step") or {}
    if pause_gate_active(thread_id_from_config(config), "context_selector"):
        return {
            "pending_context_selection": dict(next_step),
            "human_request_kind": "context_pause",
            "next_step": {
                "action": "ask_user", "action_id": next_step.get("action_id"),
                "question": "Context selection was paused. Add an instruction or resume.",
                "task": next_step.get("task") or "Resume context selection",
            },
        }
    key = next_step.get("key") or ""
    from_token = _coerce_token(next_step.get("from_token"), 0) or 0
    to_token = _coerce_token(next_step.get("to_token"), None)

    execution_memory = state.get("execution_memory") or {}
    context_memory = state.get("context_memory")
    selection_history = state.get("context_selection_history") or []
    selection_summary = state.get("context_selection_summary") or {}
    execution_history = list(state.get("execution_history") or [])
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

    entries = (context_memory or {}).get("entries") or []
    newest = entries[-1] if entries else {}
    selection_history, selection_summary = record_context_selection(
        selection_history,
        key=key,
        from_token=from_token,
        to_token=to_token,
        found=entry is not None,
        loaded_tokens=int(newest.get("tokens") or 0),
        total_tokens=int(newest.get("total_tokens") or 0),
        task=next_step.get("task") or "",
    )
    execution_history.append(
        {
            "type": "context_select",
            "name": "context_selector",
            "task": next_step.get("task") or "Load context window",
            "status": "completed",
            "success": True,
            "key": key,
            "from_token": from_token,
            "to_token": to_token,
            "loop_detected": bool(selection_summary.get("loop_detected")),
        }
    )

    phase_index = int(state.get("planned_phase_index") or 0) + 1
    phases = state.get("planned_phases") or []
    return {"context_memory": context_memory,
            "context_selection_history": selection_history,
            "context_selection_summary": selection_summary,
            "execution_history": execution_history,
            "pending_context_selection": {},
            "human_request_kind": "", "next_step": {}, "planned_phase_index": phase_index,
            "planned_phases": [] if phase_index >= len(phases) else phases}
