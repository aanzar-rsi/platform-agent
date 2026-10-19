"""Spawn one or more child AgentCore runs from a single planner action."""

from __future__ import annotations

from langchain_core.messages import AIMessage

from src.agent.agent_core import AgentCore, Policy, child_runner
from src.agent.memory import update_context_memory


def _requested_policy(raw: dict | None) -> Policy | None:
    if not isinstance(raw, dict):
        return None
    return Policy(
        armory=raw.get("armory") if isinstance(raw.get("armory"), dict) else {},
        memory=raw.get("memory") if isinstance(raw.get("memory"), dict) else {},
        guardrails={}, observability={},
    )


def _root_owner(repository, record: dict) -> str:
    while record.get("parent_agent_id"):
        record = repository.get(str(record["parent_agent_id"]))
        if not record:
            return ""
    return str(record["owner_id"])


def child_agent_node(state: dict, config=None) -> dict:
    values = (config or {}).get("configurable") or {}
    parent_id = values.get("agent_id")
    parent_execution_id = values.get("execution_id")
    if not parent_id or not parent_execution_id:
        return {
            "messages": [
                AIMessage(content="Child spawning requires authenticated AgentCore runtime.",
                          additional_kwargs={"ui_hidden": True})
            ]
        }

    repository = child_runner.repository
    parent_record = repository.get(parent_id)
    if (not parent_record or not values.get("owner_id") or
        str(_root_owner(repository, parent_record)) != str(values["owner_id"]) or
        parent_record["state"] != "open"):
        return {
            "messages": [
                AIMessage(content="Parent agent not found or not owned.", additional_kwargs={"ui_hidden": True})
            ]
        }

    execution = repository.active_execution(parent_id)
    if not execution or str(execution["execution_id"]) != str(parent_execution_id) or execution["state"] != "running":
        return {"messages": [AIMessage(content="Parent agent is not running.", additional_kwargs={"ui_hidden": True})]}

    parent = AgentCore(parent_record, repository, active_execution_id=parent_execution_id)
    uid = values.get("owner_id")
    preloaded_context = dict(state.get("preloaded_context") or {})
    if uid and "uid" not in preloaded_context:
        preloaded_context["uid"] = uid

    execution_history = list(state.get("execution_history") or [])
    execution_memory = dict(state.get("execution_memory") or {})
    context_memory = state.get("context_memory")
    calls = (state.get("next_step") or {}).get("child_calls") or []
    if not isinstance(calls, list):
        calls = []

    spawned: list[dict] = []
    errors: list[str] = []
    started = 0
    for index, call in enumerate(calls, start=1):
        if not isinstance(call, dict):
            errors.append(f"call {index}: invalid payload")
            continue
        task = str(call.get("task") or "").strip()
        if not task:
            errors.append(f"call {index}: missing task")
            continue
        parameters = call.get("parameters") if isinstance(call.get("parameters"), dict) else {}
        requested_policy = _requested_policy(call.get("requested_policy"))

        child_context = {**preloaded_context, "parameters": parameters}
        child_task = task
        if parameters:
            child_task += f"\nParameters: {parameters}"
        try:
            handle = child_runner.spawn_child(parent, child_task, child_runner.run_child_graph, child_context,
                                              requested_policy=requested_policy)
            started += 1
            spawned.append({
                "type": "child_agent",
                "agent_name": "child_agent",
                "task": child_task,
                "tool_args": parameters,
                "requested_policy": call.get("requested_policy"),
                "child_agent_id": handle.child_agent_id,
                "status": "running",
                "success": True,
            })
        except Exception as exc:
            errors.append(f"call {index}: {type(exc).__name__}")

    if started == 0:
        summary = "No child agents started" + (": " + "; ".join(errors) if errors else "")
    else:
        summary = f"Spawned {started} child agent(s)"
        if errors:
            summary += "; failed: " + "; ".join(errors)

    for entry in spawned:
        execution_history.append(entry)
        step_key = f"child_agent_{len(execution_history)}"
        entry["key"] = step_key
        execution_memory[step_key] = entry

    context_memory = update_context_memory(
        context_memory,
        key=f"child_spawn_{len(execution_history)}",
        content=summary,
        from_token=0,
        to_token=None,
    )

    return {
        "messages": [
            AIMessage(
                content=summary,
                additional_kwargs={"ui_hidden": True},
            )
        ],
        "execution_history": execution_history,
        "execution_memory": execution_memory,
        "context_memory": context_memory,
    }
