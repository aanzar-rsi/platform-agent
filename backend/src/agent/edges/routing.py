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


def dispatcher_target(state: PlanExecuteState) -> str:
    """Expose the dispatcher's single routing decision to LangGraph."""
    return state.get("dispatch_target") or AGENT_NODE
