"""Fan out independent phase steps; commit their results once in plan order."""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langgraph.types import Send

from src.agent.nodes.agentnode import _map_plan_step_to_next_step
from src.agent.memory import record_execution


def plan_dispatcher_node(state: dict, config=None) -> dict:
    phase = state["planned_phases"][state["planned_phase_index"]]
    return {"plan_event": {"kind": "phase.started", "sequence": phase["sequence"],
                           "steps": [{"id": s["id"], "action": s["action"], "name": s["name"], "task": s["task"]}
                                     for s in phase["steps"]]}}


def dispatch_phase(state: dict):
    phase = state["planned_phases"][state["planned_phase_index"]]
    # A branch gets a snapshot, not the parent's mutable execution channels.
    return [Send("planned_step", {"step": step, "sequence": phase["sequence"],
                                  "messages": state.get("messages", []),
                                  "execution_history": state.get("execution_history", []),
                                  "execution_memory": state.get("execution_memory", {}),
                                  "context_memory": state.get("context_memory"),
                                  "preloaded_context": state.get("preloaded_context"),
                                  "current_task": state.get("current_task")}) for step in phase["steps"]]


def planned_step_node(state: dict, config=None) -> dict:
    from src.agent.nodes.input_security_gate import input_security_gate_node
    from src.agent.nodes.armory_node import armory_node
    from src.agent.nodes.child_agent_node import child_agent_node
    from src.agent.nodes.collect_child import collect_child_node
    from src.agent.nodes.context_selector import context_selector_node
    from src.agent.nodes.human_input import human_input_node

    step = state["step"]
    next_step = _map_plan_step_to_next_step(step)
    snapshot = {**state, "next_step": next_step}
    validated = input_security_gate_node(snapshot, config)
    next_step = validated.get("next_step", next_step)
    if next_step.get("action") == "finish" and step["action"] != "finish":
        outcome = {"error": next_step.get("answer")}
    else:
        nodes = {
            "armory": armory_node, "child_agent": child_agent_node,
            "collect_child": collect_child_node, "context_select": context_selector_node,
            "ask_user": human_input_node,
        }
        if next_step["action"] == "finish":
            answer = next_step["answer"]
            outcome = {"messages": [AIMessage(content=answer)], "answer": answer}
        else:
            outcome = nodes[next_step["action"]]({**snapshot, "next_step": next_step}, config)
            if "messages" in outcome:
                from src.agent.nodes.output_security_gate import _sanitize_messages

                outcome["messages"] = _sanitize_messages(outcome["messages"])
    # The reducer is the only shared channel written by parallel branches.
    return {"phase_step_results": [{"id": step["id"], "sequence": state["sequence"],
                                    "action": next_step["action"], "task": step["task"],
                                    "name": step["name"], "outcome": outcome}]}


def phase_collector_node(state: dict, config=None) -> dict:
    phase_index = state["planned_phase_index"]
    phase = state["planned_phases"][phase_index]
    result_map = {result["id"]: result for result in state.get("phase_step_results", [])
                  if result["sequence"] == phase["sequence"]}
    if set(result_map) != {step["id"] for step in phase["steps"]}:
        raise ValueError("incomplete phase results")

    original_history = list(state.get("execution_history") or [])
    history = list(original_history)
    memory = dict(state.get("execution_memory") or {})
    context = state.get("context_memory")
    messages = []
    failed = False
    answer = None
    step_events = []
    for step in phase["steps"]:
        result = result_map[step["id"]]
        outcome = result["outcome"]
        entries = outcome.get("execution_history") or []
        new_entries = entries[len(original_history):]
        if result["action"] == "collect_child":
            new_entries = [entry for entry in entries if entry.get("child_agent_id") ==
                           (outcome.get("next_step") or {}).get("child_agent_id")]
        if outcome.get("error") or (not new_entries and result["action"] in {"armory", "child_agent", "collect_child"}):
            failed = True
        for entry in new_entries:
            original_key = entry.get("key")
            planned_key = f"plan_{step['id']}"
            if result["action"] == "child_agent" and entry.get("child_agent_id"):
                planned_key += f"_{entry['child_agent_id']}"
            entry = {**entry, "key": original_key if result["action"] == "collect_child" else planned_key,
                      "step_id": step["id"], "phase": phase["sequence"]}
            if result["action"] == "collect_child" and original_key:
                history = [entry if row.get("key") == original_key else row for row in history]
            else:
                history.append(entry)
            value = entry.get("value", entry.get("result"))
            memory, context, stored = record_execution(
                memory, context, key=entry["key"], value=value,
                description=entry.get("description") or entry.get("task") or f"Result of plan step {step['id']}",
                entry_type=entry.get("type") or result["action"],
                name=entry.get("name") or entry.get("tool_name") or entry.get("agent_name") or "",
                task=entry.get("task") or step["task"], success=entry.get("success", True),
                metadata={k: v for k, v in entry.items() if k not in {"key", "type", "name", "description", "task", "value", "result", "total_tokens", "success"}},
            )
            entry.update(stored)
            memory[entry["key"]] = entry
            if not entry.get("success", True):
                failed = True
            step_events.append({"id": step["id"], "sequence": phase["sequence"], "action": step["action"],
                                "success": bool(entry.get("success", True)), "result": entry.get("result")})
        if result["action"] == "context_select" and isinstance(outcome.get("context_memory"), dict):
            context = outcome["context_memory"]
            step_events.append({"id": step["id"], "sequence": phase["sequence"], "action": step["action"],
                                "success": True, "result": "Context loaded"})
        if result["action"] == "finish":
            answer = outcome["answer"]
            step_events.append({"id": step["id"], "sequence": phase["sequence"], "action": step["action"],
                                "success": True, "result": answer})
        if outcome.get("error"):
            step_events.append({"id": step["id"], "sequence": phase["sequence"], "action": step["action"],
                                "success": False, "result": outcome["error"]})
        messages.extend(outcome.get("messages") or [])

    update = {"execution_history": history, "execution_memory": memory, "context_memory": context,
              "messages": messages, "phase_step_results": [],
              "plan_event": {"kind": "phase.finished", "sequence": phase["sequence"], "failed": failed,
                             "step_ids": [step["id"] for step in phase["steps"]]},
              "step_events": step_events,
              "planned_phase_index": phase_index + 1}
    if answer is not None and not failed and not any(entry.get("status") == "running" for entry in history):
        update.update(next_step={"action": "finish", "answer": answer}, planned_phases=[], current_task="finish")
    elif answer is not None and not failed:
        update.update(next_step={}, planned_phases=[], current_task="")
    elif failed:
        update.update(planned_phases=[], next_step={}, current_task="")
    elif phase_index + 1 == len(state["planned_phases"]):
        update.update(planned_phases=[], next_step={}, current_task="collect_child"
                      if any(entry.get("status") == "running" for entry in history) else "")
    elif not failed:
        update["next_step"] = {}
    if any(getattr(message, "type", None) == "human" for message in messages):
        update.update(planned_phases=[], next_step={}, current_task="")
    return update
