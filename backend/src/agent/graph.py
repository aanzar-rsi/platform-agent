"""Agent graph with one validated execution pipeline."""

from langgraph.graph import END, START, StateGraph

from src.agent.edges.routing import (
    AGENT_NODE, ARMORY_NODE, CHILD_AGENT_NODE, COLLECT_CHILD_NODE,
    CONTEXT_SELECTOR_NODE, EXECUTION_DISPATCHER_NODE, HUMAN_INPUT_NODE,
    INPUT_SECURITY_GATE_NODE, OUTPUT_SECURITY_GATE_NODE, RESULT_COLLECTOR_NODE,
)
from src.agent.nodes.agentnode import agent_node
from src.agent.nodes.armory_node import armory_node
from src.agent.nodes.child_agent_node import child_agent_node
from src.agent.nodes.collect_child import collect_child_node
from src.agent.nodes.context_selector import context_selector_node
from src.agent.nodes.execution_dispatcher import dispatch_execution, execution_dispatcher_node
from src.agent.nodes.human_input import human_input_node
from src.agent.nodes.input_security_gate import input_security_gate_node
from src.agent.nodes.output_security_gate import output_security_gate_node
from src.agent.nodes.result_collector import result_collector_node
from src.agent.state import PlanExecuteState
from src.utils.postgres_checkpointer import get_checkpointer
from src.utils.trace import traced_node

workflow = StateGraph(PlanExecuteState)
workflow.add_node(AGENT_NODE, traced_node(AGENT_NODE, agent_node))
workflow.add_node(INPUT_SECURITY_GATE_NODE, traced_node(INPUT_SECURITY_GATE_NODE, input_security_gate_node))
workflow.add_node(EXECUTION_DISPATCHER_NODE, traced_node(EXECUTION_DISPATCHER_NODE, execution_dispatcher_node))
workflow.add_node(ARMORY_NODE, traced_node(ARMORY_NODE, armory_node))
workflow.add_node(CHILD_AGENT_NODE, traced_node(CHILD_AGENT_NODE, child_agent_node))
workflow.add_node(COLLECT_CHILD_NODE, traced_node(COLLECT_CHILD_NODE, collect_child_node))
workflow.add_node(HUMAN_INPUT_NODE, traced_node(HUMAN_INPUT_NODE, human_input_node))
workflow.add_node(CONTEXT_SELECTOR_NODE, traced_node(CONTEXT_SELECTOR_NODE, context_selector_node))
workflow.add_node(RESULT_COLLECTOR_NODE, traced_node(RESULT_COLLECTOR_NODE, result_collector_node))
workflow.add_node(OUTPUT_SECURITY_GATE_NODE, traced_node(OUTPUT_SECURITY_GATE_NODE, output_security_gate_node))

workflow.add_edge(START, AGENT_NODE)
workflow.add_edge(AGENT_NODE, INPUT_SECURITY_GATE_NODE)
workflow.add_edge(INPUT_SECURITY_GATE_NODE, EXECUTION_DISPATCHER_NODE)
workflow.add_conditional_edges(EXECUTION_DISPATCHER_NODE, dispatch_execution, {
    AGENT_NODE: AGENT_NODE,
    ARMORY_NODE: ARMORY_NODE,
    CHILD_AGENT_NODE: CHILD_AGENT_NODE,
    COLLECT_CHILD_NODE: COLLECT_CHILD_NODE,
    HUMAN_INPUT_NODE: HUMAN_INPUT_NODE,
    CONTEXT_SELECTOR_NODE: CONTEXT_SELECTOR_NODE,
    RESULT_COLLECTOR_NODE: RESULT_COLLECTOR_NODE,
    END: END,
})
for producer in (ARMORY_NODE, CHILD_AGENT_NODE, COLLECT_CHILD_NODE, HUMAN_INPUT_NODE):
    workflow.add_edge(producer, RESULT_COLLECTOR_NODE)
workflow.add_edge(RESULT_COLLECTOR_NODE, OUTPUT_SECURITY_GATE_NODE)
workflow.add_edge(OUTPUT_SECURITY_GATE_NODE, EXECUTION_DISPATCHER_NODE)
workflow.add_edge(CONTEXT_SELECTOR_NODE, EXECUTION_DISPATCHER_NODE)

agent_app = workflow.compile(checkpointer=get_checkpointer())
