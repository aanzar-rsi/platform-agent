"""Explicitly collect a selected child without importing its full transcript."""

from src.agent.agent_core import child_runner
from src.agent.nodes.output_security_gate import sanitize_executor_output
from src.agent.nodes.result_collector import branch_result


def collect_child_node(state: dict, config=None) -> dict:
    child_id = (state.get("next_step") or {}).get("child_agent_id")
    values = (config or {}).get("configurable") or {}
    history = list(state.get("execution_history") or [])
    index = next((i for i, entry in enumerate(history) if entry.get("child_agent_id") == child_id), None)
    if index is None:
        result, success, status = "Unknown child ID", False, "failed"
    else:
        try:
            result = child_runner.await_child(child_id, parent_agent_id=values.get("agent_id"),
                                               parent_execution_id=values.get("execution_id"))
            run = child_runner.repository.latest_execution(child_id)
            success = run["state"] == "completed"
            status = "completed" if success else "failed"
        except TimeoutError:
            # Keep the child marked running so the parent loops back to collect later.
            result, success, status = "child_still_running", True, "running"
        except Exception as exc:
            result, success, status = type(exc).__name__, False, "failed"
    description = history[index].get("task") if index is not None else "Unknown child collection result"
    next_step = state.get("next_step") or {}
    envelope = sanitize_executor_output({
        "version": 1, "action_id": next_step.get("action_id"), "source": "collect_child",
        "results": [{
            "kind": "child_collection", "value": result, "success": success,
            "status": status, "name": "child_agent",
            "task": description or "", "description": description or "Child-agent result",
            "metadata": {"child_agent_id": child_id},
        }],
    })
    return branch_result(state, envelope)
