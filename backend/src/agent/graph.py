"""
Agent graph definition.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from langgraph.graph import END, START, StateGraph

from src.agent.edges.routing import (
    AGENT_NODE,
    INPUT_SECURITY_GATE_NODE,
    OUTPUT_SECURITY_GATE_NODE,
    CHILD_AGENT_NODE,
    CONTEXT_SELECTOR_NODE,
    HUMAN_INPUT_NODE,
    SUBAGENT_NODE,
    COLLECT_CHILD_NODE,
    TOOL_NODE,
    route_from_input_gate,
)
from src.agent.nodes.agentnode import agent_node
from src.agent.nodes.input_security_gate import input_security_gate_node
from src.agent.nodes.output_security_gate import output_security_gate_node
from src.agent.nodes.context_selector import context_selector_node
from src.agent.nodes.collect_child import collect_child_node
from src.agent.nodes.child_agent_node import child_agent_node
from src.agent.nodes.human_input import human_input_node
from src.agent.nodes.subagentnode import subagent_node
from src.agent.nodes.toolnode import tool_node
from src.agent.nodes.plan_dispatcher import dispatch_phase, phase_collector_node, plan_dispatcher_node, planned_step_node
from src.agent.state import AgentConfig, PlanExecuteState
from src.utils.postgres_checkpointer import get_checkpointer
from src.utils.trace import traced_node

workflow = StateGraph(PlanExecuteState, context_schema=AgentConfig)

# ── Nodes ─────────────────────────────────────────────────────────────────────
workflow.add_node(AGENT_NODE, traced_node(AGENT_NODE, agent_node))
workflow.add_node(INPUT_SECURITY_GATE_NODE, traced_node(INPUT_SECURITY_GATE_NODE, input_security_gate_node))
workflow.add_node(OUTPUT_SECURITY_GATE_NODE, traced_node(OUTPUT_SECURITY_GATE_NODE, output_security_gate_node))
workflow.add_node(TOOL_NODE, traced_node(TOOL_NODE, tool_node))
workflow.add_node(SUBAGENT_NODE, traced_node(SUBAGENT_NODE, subagent_node))
workflow.add_node(CHILD_AGENT_NODE, traced_node(CHILD_AGENT_NODE, child_agent_node))
workflow.add_node(COLLECT_CHILD_NODE, traced_node(COLLECT_CHILD_NODE, collect_child_node))
workflow.add_node(CONTEXT_SELECTOR_NODE, traced_node(CONTEXT_SELECTOR_NODE, context_selector_node))
workflow.add_node(HUMAN_INPUT_NODE, traced_node(HUMAN_INPUT_NODE, human_input_node))
workflow.add_node("plan_dispatcher", traced_node("plan_dispatcher", plan_dispatcher_node))
workflow.add_node("planned_step", traced_node("planned_step", planned_step_node))
workflow.add_node("phase_collector", traced_node("phase_collector", phase_collector_node))

# ── Edges ─────────────────────────────────────────────────────────────────────
workflow.add_edge(START, AGENT_NODE)

workflow.add_conditional_edges(AGENT_NODE, lambda state: "plan_dispatcher" if state.get("planned_phases") else INPUT_SECURITY_GATE_NODE)
workflow.add_conditional_edges("plan_dispatcher", dispatch_phase, ["planned_step"])
workflow.add_edge("planned_step", "phase_collector")
workflow.add_conditional_edges("phase_collector", lambda state: INPUT_SECURITY_GATE_NODE if state.get("next_step", {}).get("action") == "finish" else ("agent_node" if not state.get("planned_phases") else "plan_dispatcher"))

workflow.add_conditional_edges(
    INPUT_SECURITY_GATE_NODE,
    route_from_input_gate,
    {
        TOOL_NODE: TOOL_NODE,
        SUBAGENT_NODE: SUBAGENT_NODE,
        CHILD_AGENT_NODE: CHILD_AGENT_NODE,
        COLLECT_CHILD_NODE: COLLECT_CHILD_NODE,
        CONTEXT_SELECTOR_NODE: CONTEXT_SELECTOR_NODE,
        HUMAN_INPUT_NODE: HUMAN_INPUT_NODE,
        END: END,
    },
)

workflow.add_edge(TOOL_NODE, OUTPUT_SECURITY_GATE_NODE)
workflow.add_edge(SUBAGENT_NODE, OUTPUT_SECURITY_GATE_NODE)
workflow.add_edge(CHILD_AGENT_NODE, OUTPUT_SECURITY_GATE_NODE)
workflow.add_edge(COLLECT_CHILD_NODE, OUTPUT_SECURITY_GATE_NODE)
workflow.add_edge(CONTEXT_SELECTOR_NODE, OUTPUT_SECURITY_GATE_NODE)
workflow.add_edge(HUMAN_INPUT_NODE, OUTPUT_SECURITY_GATE_NODE)
workflow.add_edge(OUTPUT_SECURITY_GATE_NODE, AGENT_NODE)

# ── Compile with the Postgres checkpointer ────────────────────────────────────
agent_app = workflow.compile(checkpointer=get_checkpointer())


def run_cli() -> None:
    """Interactive multi-turn agent CLI loop (rendered by src.cli.repl)."""
    from src.cli.repl import run_cli as repl_run_cli

    repl_run_cli()


if __name__ == "__main__":
    run_cli()
