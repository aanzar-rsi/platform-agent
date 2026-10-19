from langgraph.graph import END
from src.agent.state import PlanExecuteState

# Node name constants — keep in sync with the names used in graph.py add_node calls.
AGENT_NODE             = "agent_node"
INPUT_SECURITY_GATE_NODE = "input_security_gate"
OUTPUT_SECURITY_GATE_NODE = "output_security_gate"
TOOL_NODE              = "tool_node"
SUBAGENT_NODE          = "subagent_node"
CHILD_AGENT_NODE       = "child_agent_node"
COLLECT_CHILD_NODE     = "collect_child"
CONTEXT_SELECTOR_NODE  = "context_selector"
HUMAN_INPUT_NODE       = "human_input"


def route_from_agent(state: PlanExecuteState) -> str:
    """Conditional edge out of agent_node.
    Reads next_step["action"] and returns the name of the next node.
    """
    action = state.get("next_step", {}).get("action", "finish")

    if action == "tool":
        dest = TOOL_NODE
    elif action == "subagent":
        dest = SUBAGENT_NODE
    elif action == "child_agent":
        dest = CHILD_AGENT_NODE
    elif action == "collect_child":
        dest = COLLECT_CHILD_NODE
    elif action == "context_select":
        dest = CONTEXT_SELECTOR_NODE
    elif action == "ask_user":
        dest = HUMAN_INPUT_NODE
    else:
        dest = END

    try:
        from src.utils.trace import in_run, emit

        if in_run():
            emit("node.routing.decision", component="routing", data={"node": AGENT_NODE, "action": action})
        from src.utils.agent_logger import log_route

        log_route(action=action, destination=str(dest))
    except Exception:
        pass

    return dest


def route_from_input_gate(state: PlanExecuteState) -> str:
    """Conditional edge out of input_security_gate.

    Reuses the same action->destination mapping as route_from_agent.
    """
    return route_from_agent(state)
