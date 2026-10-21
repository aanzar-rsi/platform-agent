"""Human input node — the agent explicitly asks the user a question.

Reached when `agent_node` sets `next_step = {"action": "ask_user", ...}`.
This node's entire body is a single, unconditional `interrupt()` call (safe
per LangGraph's "keep interrupt calls stable across replay" rule — there is
no branching around it). Once resumed, the user's answer is folded back in
as a HumanMessage and control returns to `agent_node` to continue planning.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage
from langgraph.types import interrupt

from src.agent.control import note_text_from_resume
from src.agent.memory import record_human_input
from src.agent.state import PlanExecuteState


def human_input_node(state: PlanExecuteState, config=None) -> dict:
    next_step = state.get("next_step") or {}

    answer = interrupt(
        {
            "kind": "question",
            "node": "human_input",
            "prompt": next_step.get("question") or "The agent needs more information to continue.",
            "options": next_step.get("options") or [],
            "task": next_step.get("task") or state.get("current_task") or "",
        }
    )

    answer_text = note_text_from_resume(answer) or (str(answer) if answer is not None else "")

    try:
        from src.utils.agent_logger import log_event

        log_event("agent.ask_user_answered", question=next_step.get("question"), answer_chars=len(answer_text))
    except Exception:
        pass

    history, memory, context = record_human_input(
        state.get("execution_history"), state.get("execution_memory"), state.get("context_memory"),
        value=answer_text or "(no answer provided)",
        description=next_step.get("question") or "User response to agent question",
        task=next_step.get("task") or state.get("current_task") or "",
    )
    return {
        "messages": [
            HumanMessage(
                content=answer_text or "(no answer provided)",
                additional_kwargs={
                    "ui_hidden": True,
                    "ui_step": {
                        "type": "reasoning",
                        "content": f"User response: {answer_text or '(no answer provided)'}",
                    },
                },
            )
        ],
        "execution_history": history,
        "execution_memory": memory,
        "context_memory": context,
    }
