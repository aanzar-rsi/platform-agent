"""Graph node names and preflight/human routing."""

from langgraph.graph import END

from src.agent.state import PlanExecuteState

AGENT_NODE = "agent_node"
INPUT_SECURITY_GATE_NODE = "input_security_gate"
EXECUTION_DISPATCHER_NODE = "execution_dispatcher"
RESULT_COLLECTOR_NODE = "result_collector"
OUTPUT_SECURITY_GATE_NODE = "output_security_gate"
ARMORY_NODE = "armory_node"
CHILD_AGENT_NODE = "child_agent_node"
COLLECT_CHILD_NODE = "collect_child"
CONTEXT_SELECTOR_NODE = "context_selector"
HUMAN_INPUT_NODE = "human_input"
PREFLIGHT_NODE = "preflight_node"


def route_from_preflight(state: PlanExecuteState) -> str:
    decision = str((state.get("preflight_context") or {}).get("decision") or "").lower()
    if decision in {"allow", "degrade"}:
        return INPUT_SECURITY_GATE_NODE
    if decision == "clarify":
        return HUMAN_INPUT_NODE
    if decision == "retry":
        return PREFLIGHT_NODE
    return END


def route_from_human_input(state: PlanExecuteState) -> str:
    action = str((state.get("next_step") or {}).get("action") or "").lower()
    if action == "preflight":
        return PREFLIGHT_NODE
    if action == "finish":
        return END
    return RESULT_COLLECTOR_NODE
