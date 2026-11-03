"""Human input node — the agent explicitly asks the user a question.

Reached when `agent_node` sets `next_step = {"action": "ask_user", ...}`.
This node's entire body is a single, unconditional `interrupt()` call (safe
per LangGraph's "keep interrupt calls stable across replay" rule — there is
no branching around it). Once resumed, the user's answer is folded back in
as a HumanMessage and control returns to `agent_node` to continue planning.
"""

from __future__ import annotations

from langgraph.types import interrupt

from src.agent.control import clear_pause, note_text_from_resume, thread_id_from_config
from src.agent.nodes.output_security_gate import sanitize_executor_output
from src.agent.nodes.result_collector import branch_result
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
    if state.get("human_request_kind") == "context_pause":
        thread_id = thread_id_from_config(config)
        if thread_id:
            clear_pause(thread_id)

    try:
        from src.utils.agent_logger import log_event

        log_event("agent.ask_user_answered", question=next_step.get("question"), answer_chars=len(answer_text))
    except Exception:
        pass

    envelope = sanitize_executor_output({
            "version": 1, "action_id": next_step.get("action_id"), "source": "human_input",
            "results": [{
                "kind": "human_input", "value": (answer_text if state.get("human_request_kind") == "context_pause"
                                                    else answer_text or "(no answer provided)"),
                "success": True, "task": next_step.get("task") or state.get("current_task") or "",
                "description": next_step.get("question") or "User response to agent question",
                "metadata": {"question": next_step.get("question") or "",
                             "input_kind": state.get("human_request_kind") or "question",
                             "resume_context": ("context_selector" if state.get("pending_context_selection") else "")},
            }],
        })
    return branch_result(state, envelope)
