from unittest.mock import patch
from types import SimpleNamespace

from langchain_core.messages import HumanMessage

from src.agent.nodes import agentnode


def _state(query: str) -> dict:
    return {
        "messages": [HumanMessage(content=query)],
        "execution_history": [],
        "execution_memory": {},
        "context_memory": None,
        "preloaded_context": {},
        "current_task": "",
    }


def _config() -> dict:
    return {
        "configurable": {
            "owner_id": "u1",
            "policy": {"armory": {
                "resources": {"tools": [{"type": "tool", "name": "system_info", "enabled": True}]},
                "groups": {"tools": {"enabled": True}},
            }},
            "max_plan_steps": 8,
        }
    }


@patch.object(agentnode, "_safe_learned_experiences", return_value="")
@patch("api.services.mcp_runtime.available_mcp_tools", return_value={})
@patch.object(agentnode, "fast_agent_prompt_loader", return_value=("fast-sys", "fast-user"))
@patch.object(agentnode, "call_llm_stream")
def test_agent_leaves_classifier_parsing_to_input_gate(mock_stream, _fast_prompt, _mcp, _learned):
    response = "<action>planner</action><reasoning>needs a tool</reasoning>"
    mock_stream.return_value = iter([response])

    out = agentnode.agent_node(_state("hello"), _config())

    assert out["planner_response"] == response
    assert out["planner_response_type"] == "classifier"
    assert out["next_step"]["action"] == "validate_response"
    assert out["planner_resources"] == [{"type": "tool", "name": "system_info"}]


@patch.object(agentnode, "_safe_learned_experiences", return_value="")
@patch("api.services.mcp_runtime.available_mcp_tools", return_value={})
@patch.object(agentnode, "planner_agent_prompt_loader", return_value=("planner-sys", "planner-user"))
@patch.object(agentnode, "call_llm_stream")
def test_planner_error_forces_planner_prompt(mock_stream, planner_prompt, _mcp, _learned):
    mock_stream.return_value = iter(["<action>retry</action>"])
    state = {**_state("hello"), "planner_mode": True,
             "planner_error": {"stage": "planner_validation", "message": "missing data"}}

    out = agentnode.agent_node(state, _config())

    assert out["planner_response_type"] == "planner"
    assert planner_prompt.call_args.kwargs["planner_error"] == state["planner_error"]


@patch.object(agentnode.Armory, "list", return_value=[SimpleNamespace(type="tool", name="mcp_weather")])
@patch.object(agentnode, "_safe_learned_experiences", return_value="")
@patch.object(agentnode, "fast_agent_prompt_loader", return_value=("fast-sys", "fast-user"))
@patch.object(agentnode, "call_llm_stream", return_value=iter(["<action>finish</action>"]))
def test_mcp_resource_alias_does_not_mutate_set_during_iteration(_stream, _prompt, learned, _resources):
    agentnode.agent_node(_state("weather"), _config())

    assert learned.call_args.kwargs["available_resources"] == {
        ("tool", "mcp_weather"),
        ("mcp_server", "mcp_weather"),
    }
