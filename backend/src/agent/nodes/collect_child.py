"""Explicitly collect a selected child without importing its full transcript."""

from langchain_core.messages import AIMessage

from src.agent.agent_core import child_runner
from src.agent.memory import record_execution


def collect_child_node(state: dict, config=None) -> dict:
    child_id = (state.get("next_step") or {}).get("child_agent_id")
    values = (config or {}).get("configurable") or {}
    history = list(state.get("execution_history") or [])
    index = next((i for i, entry in enumerate(history) if entry.get("child_agent_id") == child_id), None)
    if index is None:
        result, success = "Unknown child ID", False
    else:
        try:
            result = child_runner.await_child(child_id, parent_agent_id=values.get("agent_id"),
                                               parent_execution_id=values.get("execution_id"))
            run = child_runner.repository.latest_execution(child_id)
            success = run["state"] == "completed"
        except TimeoutError:
            raise  # A timed-out live worker cannot be marked collected or closed.
        except Exception as exc:
            result, success = type(exc).__name__, False
        matching = dict(history[index])
        matching.update(result=result, success=success, status="completed" if success else "failed")
        if matching.get("type") == "subagent":
            matching["type"] = "child_agent"
        history[index] = matching

        if values.get("agent_id") and values.get("execution_id"):
            child_runner.repository.append_message(values["agent_id"], values["execution_id"], str(result),
                                                   sender_type="agent", sender_id=child_id,
                                                   child_agent_id=child_id, visible_to_user=False)

    memory_key = matching.get("key") if index is not None else f"child_collect_{len(history) + 1}"
    description = matching.get("task") if index is not None else "Unknown child collection result"
    memory, context, stored = record_execution(
        state.get("execution_memory"), state.get("context_memory"),
        key=memory_key, value=result, description=description or "Child-agent result",
        entry_type="child_agent", name="child_agent", task=description or "",
        success=success, metadata={"child_agent_id": child_id,
                                   "status": "completed" if success else "failed"},
    )
    if index is not None:
        matching.update(stored)
        history[index] = matching
        memory[memory_key] = matching
    return {
        "next_step": {"action": "collect_child", "child_agent_id": child_id},
        "execution_history": history,
        "execution_memory": memory,
        "context_memory": context,
        "messages": [AIMessage(content=f"Child {child_id} collected (memory key: {memory_key}).",
                               additional_kwargs={"ui_hidden": True,
                                                   "ui_step": {"type": "child_agent", "child_agent": {
                                                       "id": child_id, "child_agent_id": child_id,
                                                       "agent_name": "child_agent",
                                                       "result": "Collected. Use context_select to view full result.", "success": success,
                                                       "status": "done" if success else "error", "progress": []}}})],
    }
