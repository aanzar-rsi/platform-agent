"""The single routing authority for validated execution batches."""

from __future__ import annotations

from langgraph.graph import END
from langgraph.types import Send

from src.agent.nodes.agentnode import _map_plan_step_to_next_step


_EXECUTORS = {
    "armory": "armory_node",
    "child_agent": "child_agent_node",
    "collect_child": "collect_child",
}


def _command(step: dict) -> dict:
    command = step.get("command")
    return dict(command) if isinstance(command, dict) else _map_plan_step_to_next_step(step)


def execution_dispatcher_node(state: dict, config=None) -> dict:
    phases = state.get("planned_phases") or []
    phase_index = int(state.get("planned_phase_index") or 0)

    if state.get("pending_context_selection") and state.get("next_step", {}).get("action") == "context_select":
        return {"dispatch_target": "context_selector"}
    if state.get("human_request_kind") == "context_pause":
        return {"dispatch_target": "human_input"}
    if phase_index >= len(phases):
        return {"planned_phases": [], "planned_phase_index": 0,
                "dispatch_target": "agent_node", "next_step": {}}

    phase = phases[phase_index]
    steps = phase["steps"]
    if all(step["id"] in {result.get("id") for result in state.get("step_results") or []}
           for step in steps):
        return {"dispatch_target": "result_collector"}
    event_steps = []
    execution_id = str(((config or {}).get("configurable") or {}).get("execution_id") or "execution")
    for step in steps:
        command = _command(step)
        event_steps.append({
            "id": step["id"], "action_id": step.get("action_id") or command.get("action_id")
            or f"{execution_id}:phase:{phase['sequence']}:step:{step['id']}",
            "action": command.get("action") or step["action"], "name": step.get("name", ""),
            "task": step.get("task", ""), "resource_type": command.get("resource_type"),
            "tool_args": command.get("arguments") or {},
        })
    event = {"kind": "phase.started", "sequence": phase["sequence"], "steps": event_steps}
    if len(steps) == 1:
        next_step = _command(steps[0])
        execution_id = str(((config or {}).get("configurable") or {}).get("execution_id") or "execution")
        next_step["action_id"] = str(steps[0].get("action_id") or next_step.get("action_id")
                                     or f"{execution_id}:phase:{phase['sequence']}:step:{steps[0]['id']}")
        action = next_step["action"]
        if action == "replan":
            return {"next_step": {}, "dispatch_target": "agent_node",
                    "planned_phases": [], "planned_phase_index": 0}
        if action == "finish":
            return {"plan_event": event, "next_step": next_step, "dispatch_target": "__end__",
                    "planned_phases": [], "planned_phase_index": 0}
        if action == "context_select":
            return {"plan_event": event, "next_step": next_step, "dispatch_target": "context_selector",
                    "dispatch_step": {"id": steps[0]["id"], "sequence": phase["sequence"],
                                      "action": action, "task": steps[0].get("task", ""),
                                      "name": steps[0].get("name", "")}}
        if action == "ask_user":
            return {"plan_event": event, "next_step": next_step, "dispatch_target": "human_input",
                    "dispatch_step": {"id": steps[0]["id"], "sequence": phase["sequence"],
                                      "action": action, "task": steps[0].get("task", ""),
                                      "name": steps[0].get("name", "")}}
    return {"plan_event": event, "dispatch_target": "execute"}


def dispatch_execution(state: dict):
    target = state.get("dispatch_target") or "agent_node"
    if target != "execute":
        return END if target == "__end__" else target

    phase = state["planned_phases"][state["planned_phase_index"]]
    configurable = state.get("configurable") or {}
    execution_id = str(configurable.get("execution_id") or "execution")
    sends = []
    for step in phase["steps"]:
        next_step = _command(step)
        next_step["action_id"] = str(step.get("action_id") or next_step.get("action_id")
                                     or f"{execution_id}:phase:{phase['sequence']}:step:{step['id']}")
        branch = {
            **state,
            "next_step": next_step,
            "dispatch_step": {"id": step["id"], "sequence": phase["sequence"],
                               "action": next_step["action"], "task": step.get("task", ""),
                               "name": step.get("name", ""), "action_id": next_step["action_id"]},
        }
        sends.append(Send(_EXECUTORS[next_step["action"]], branch))
    return sends
