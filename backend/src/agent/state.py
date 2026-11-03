from typing import List, Annotated, Dict, Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from src.config import settings


def merge_step_results(left: list[dict], right: list[dict]) -> list[dict]:
    """Merge parallel executor results; an empty update clears a completed batch."""
    return right if not right else left + right

class AgentConfig(BaseModel):
    """
    Defines the external configuration parameters for the graph run.
    These parameters are static during a thread run and are used to identify
    who is talking and what access permissions they have.
    """
    owner_id: str = Field(
        ..., 
        description="Unique identity key of the user (e.g., UUID format)."
    )
    session_id: str = Field(
        ..., 
        description="Identity of the current authenticated login session."
    )
    # Add any feature flags or environment limits here
    max_loops: int = Field(
        default=settings.max_loops,
        description="Max cycles the planner/executor can perform per question."
    )
    max_plan_steps: int = Field(
        default=8,
        description="Maximum number of planner steps allowed in a generated phased plan.",
    )

class PlanExecuteState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # Format: [("tool", "search_mdm", "No results found"), ("subagent", "coder", "Generated script...")]
    execution_history: List[dict[str, Any]]
    current_task: str  # The current task being executed, e.g., "search_mdm" or "coder"

    # The designated next destination or specific task assignment details.
    # The Agent node populates this, and conditional edges read it to route control.
    next_step: Dict[str, Any] 

    #Main memory dump of tool or agent calls
    execution_memory: Dict[str, Any]

    # FIFO window of tool/subagent results visible to the agent (budgeted tokens)
    context_memory: Dict[str, Any]

    # Compact ledger of recent context-select windows and loop summary metadata.
    context_selection_history: List[dict[str, Any]]
    context_selection_summary: Dict[str, Any]

    # Context loaded at the very beginning of the thread (User memories, MCP connections)
    preloaded_context: Dict[str, Any]

    agent_id: str
    planned_phases: List[dict[str, Any]]
    planned_phase_index: int
    plan_created: Dict[str, Any]
    plan_event: Dict[str, Any]
    step_events: List[dict[str, Any]]
    step_results: Annotated[list[dict[str, Any]], merge_step_results]
    planner_response: str
    planner_response_type: str
    planner_error: Dict[str, Any]
    planner_resources: List[dict[str, str]]
    planner_mode: bool
    action_sequence: int
    executor_output: Dict[str, Any]
    output_events: List[dict[str, Any]]
    dispatch_target: str
    dispatch_step: Dict[str, Any]
    pending_context_selection: Dict[str, Any]
    human_request_kind: str
