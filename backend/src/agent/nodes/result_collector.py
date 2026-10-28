"""Order one or more executor branch results into one security-gate envelope."""

from src.agent.nodes.output_security_gate import sanitize_executor_output


def branch_result(state: dict, envelope: dict) -> dict:
    step = state.get("dispatch_step") or {}
    return {"step_results": [{**step, "results": envelope.get("results") or []}]}


def result_collector_node(state: dict, config=None) -> dict:
    phase = state["planned_phases"][state["planned_phase_index"]]
    result_map = {result["id"]: result for result in state.get("step_results") or []
                  if result.get("sequence") == phase["sequence"]}
    expected = [step["id"] for step in phase["steps"]]
    if set(result_map) != set(expected):
        raise ValueError("incomplete execution results")

    if any(result_map[step_id].get("pending") for step_id in expected):
        return {"step_results": [], "dispatch_target": "agent_node",
                "planned_phases": [], "planned_phase_index": 0}

    execution_id = str(((config or {}).get("configurable") or {}).get("execution_id") or "execution")
    return {
        "step_results": [],
        "executor_output": sanitize_executor_output({
            "version": 1,
            "action_id": f"{execution_id}:phase:{phase['sequence']}",
            "source": "dispatch_batch",
            "phase": phase["sequence"],
            "steps": [result_map[step_id] for step_id in expected],
        }),
    }
