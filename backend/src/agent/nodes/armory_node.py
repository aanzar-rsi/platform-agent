"""Unified graph adapter for every executable armory resource."""

from langchain_core.messages import AIMessage, HumanMessage
from src.agent.control import clear_pause, note_text_from_resume, pause_gate_active, thread_id_from_config
from src.agent.facets import Armory
from src.agent.memory import count_content_tokens, record_execution, record_human_input
from src.agent.subagent_stream import emit_subagent_event
from src.utils.text_truncate import truncate_for_aimessage


def armory_node(state: dict, config=None) -> dict:
    next_step = state["next_step"]
    resource_type = next_step.get("resource_type", "")
    resource_name = next_step.get("resource_name", "")
    arguments = next_step.get("arguments", {})
    task = state.get("current_task") or next_step.get("task") or ""
    history = list(state.get("execution_history", []))
    memory = dict(state.get("execution_memory", {}))
    context_memory = state.get("context_memory")
    configurable = (config or {}).get("configurable") or {}
    policy = ((configurable.get("policy") or {}).get("armory") or {})
    armory = Armory(policy, user_id=configurable.get("owner_id"),
                    preloaded_context=state.get("preloaded_context"))

    thread_id = thread_id_from_config(config)
    paused = pause_gate_active(thread_id, "armory_node", kinds=frozenset({"paused", "confirm_resource"}))
    resource = armory.get(resource_type, resource_name, reconnect=True)
    confirm = bool(resource and resource.confirmation_required and policy.get("confirm_tools", True))
    if paused or confirm:
        from langgraph.types import interrupt

        decision = interrupt({"kind": "confirm_resource" if confirm else "paused", "node": "armory_node",
                              "resource_type": resource_type, "resource_name": resource_name,
                              "arguments": arguments, "task": task, "confirm_required": confirm})
        if paused:
            clear_pause(thread_id)
        note = note_text_from_resume(decision).strip()
        approved = not confirm or (isinstance(decision, dict) and bool(decision.get("approved")))
        if note:
            history, memory, context_memory = record_human_input(
                history, memory, context_memory, value=note,
                description="User response at armory approval or pause gate", task=task)
        if paused and not confirm:
            return ({"messages": [HumanMessage(content=note, additional_kwargs={"ui_hidden": True})],
                     "execution_history": history, "execution_memory": memory,
                     "context_memory": context_memory} if note else {})
        if not approved:
            return _record(resource_type, resource_name, arguments, task,
                           {"success": False, "error": "User declined to run this resource."}, None,
                           history, memory, context_memory)

    if resource_type == "subagent":
        emit_subagent_event(resource_name, {"kind": "start", "message": "Starting"})
    try:
        result, structured = armory.call(resource_type, resource_name, arguments, task=task, reconnect=True)
        success = not (isinstance(result, dict) and result.get("success") is False)
    except Exception as exc:
        result, structured, success = {"success": False, "error": str(exc)}, None, False
    if resource_type == "subagent":
        emit_subagent_event(resource_name, {"kind": "complete" if success else "error",
                                             "message": "Completed" if success else str(result)})
    return _record(resource_type, resource_name, arguments, task, result, structured,
                   history, memory, context_memory)


def _record(resource_type, resource_name, arguments, task, result, structured,
            history, memory, context_memory):
    key = f"armory_{len(history) + 1}"
    success = not (isinstance(result, dict) and result.get("success") is False)
    entry = {"type": "armory", "resource_type": resource_type, "resource_name": resource_name,
             "resource": f"armory.{resource_type}.{resource_name}", "arguments": arguments,
             "task": task, "key": key, "result": result, "success": success,
             "structured": structured}
    memory, context_memory, stored = record_execution(
        memory, context_memory, key=key, value=result, description=task or entry["resource"],
        entry_type="armory", name=resource_name, task=task, success=success,
        metadata={"resource_type": resource_type, "resource_name": resource_name,
                  "arguments": arguments, "structured": structured})
    entry.update(stored)
    history.append(entry)
    count_content_tokens(result)
    preview = truncate_for_aimessage(result)
    ui_type = "subagent" if resource_type == "subagent" else "tool"
    return {"messages": [AIMessage(content=f"{entry['resource']} result: {preview}",
                                    additional_kwargs={"ui_hidden": True, "ui_step": {
                                        "type": ui_type, ui_type: {"id": key, "name": resource_name,
                                                                   "result": preview, "success": success}}})],
            "execution_history": history, "execution_memory": memory,
            "context_memory": context_memory}
