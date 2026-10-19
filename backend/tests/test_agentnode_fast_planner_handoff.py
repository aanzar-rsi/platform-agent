from __future__ import annotations

from unittest.mock import patch

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
            "enabled_tools": ["system_info"],
            "enabled_subagents": [],
            "max_plan_steps": 8,
        }
    }


@patch.object(agentnode, "_safe_learned_experiences", return_value="")
@patch.object(agentnode, "available_mcp_tools", return_value={})
@patch.object(agentnode, "planner_agent_prompt_loader", return_value=("planner-sys", "planner-user"))
@patch.object(agentnode, "fast_agent_prompt_loader", return_value=("fast-sys", "fast-user"))
@patch.object(agentnode, "call_llm_stream")
def test_fast_plan_handoff_accepts_planner_finish_without_steps_json(mock_stream, _fast_prompt, _planner_prompt, _mcp_tools, _learned):
    mock_stream.side_effect = [
        iter([
            "<planner_exit>False</planner_exit><action>plan</action><reasoning>need plan</reasoning>"
            "<task>plan it</task><data><name>planner</name><parameters></parameters></data>"
        ]),
        iter([
            "<planner_exit>True</planner_exit><action>None</action><reasoning>done</reasoning>"
            "<data><output>final</output></data>"
        ]),
    ]

    out = agentnode.agent_node(_state("hello"), _config())
    answer = out["next_step"]["answer"]
    assert out["next_step"]["action"] == "finish"
    assert answer == "final"


@patch.object(agentnode, "_safe_learned_experiences", return_value="")
@patch.object(agentnode, "available_mcp_tools", return_value={})
@patch.object(agentnode, "planner_agent_prompt_loader", return_value=("planner-sys", "planner-user"))
@patch.object(agentnode, "fast_agent_prompt_loader", return_value=("fast-sys", "fast-user"))
@patch.object(agentnode, "call_llm_stream")
def test_fast_plan_handoff_retries_once_then_parses_plan(mock_stream, _fast_prompt, _planner_prompt, _mcp_tools, _learned):
    mock_stream.side_effect = [
        iter([
            "<planner_exit>False</planner_exit><action>plan</action><reasoning>need plan</reasoning>"
            "<task>plan it</task><data><name>planner</name><parameters></parameters></data>"
        ]),
        iter([
            "<planner_exit>False</planner_exit><action>plan</action><reasoning>planning</reasoning>"
            "<task>plan it</task><data><name>planner</name><parameters></parameters></data>"
        ]),
        iter([
            "<planner_exit>False</planner_exit><action>plan</action><reasoning>planning</reasoning>"
            "<task>plan it</task><data><name>planner</name><parameters>"
            "<steps_json>{\"phases\":[{\"sequence\":1,\"steps\":[{\"id\":\"a\",\"action\":\"tool_call\",\"name\":\"system_info\",\"task\":\"run\",\"parameters\":{},\"uses\":[],\"child_calls\":[]}]}]}</steps_json>"
            "</parameters></data>"
        ]),
    ]

    out = agentnode.agent_node(_state("hello"), _config())
    assert out.get("plan_created", {}).get("step_count") == 1
    assert out.get("planned_phases")


@patch.object(agentnode, "_safe_learned_experiences", return_value="")
@patch.object(agentnode, "available_mcp_tools", return_value={})
@patch.object(agentnode, "planner_agent_prompt_loader", return_value=("planner-sys", "planner-user"))
@patch.object(agentnode, "fast_agent_prompt_loader", return_value=("fast-sys", "fast-user"))
@patch.object(agentnode, "call_llm_stream")
def test_fast_plan_handoff_missing_steps_after_retry_surfaces_clear_error(
    mock_stream, _fast_prompt, _planner_prompt, _mcp_tools, _learned
):
    mock_stream.side_effect = [
        iter([
            "<planner_exit>False</planner_exit><action>plan</action><reasoning>need plan</reasoning>"
            "<task>plan it</task><data><name>planner</name><parameters></parameters></data>"
        ]),
        iter([
            "<planner_exit>False</planner_exit><action>plan</action><reasoning>planning</reasoning>"
            "<task>plan it</task><data><name>planner</name><parameters></parameters></data>"
        ]),
        iter([
            "<planner_exit>False</planner_exit><action>plan</action><reasoning>still no json</reasoning>"
            "<task>plan it</task><data><name>planner</name><parameters></parameters></data>"
        ]),
    ]

    out = agentnode.agent_node(_state("hello"), _config())
    assert out["next_step"]["action"] == "finish"
    assert "Planner escalation failed (missing_steps_json)" in out["next_step"]["answer"]


@patch.object(agentnode, "_safe_learned_experiences", return_value="")
@patch.object(agentnode, "available_mcp_tools", return_value={})
@patch.object(agentnode, "planner_agent_prompt_loader", return_value=("planner-sys", "planner-user"))
@patch.object(agentnode, "fast_agent_prompt_loader", return_value=("fast-sys", "fast-user"))
@patch.object(agentnode, "call_llm_stream")
def test_plan_parse_failure_retries_once_then_returns_graceful_message(
    mock_stream, _fast_prompt, _planner_prompt, _mcp_tools, _learned
):
    invalid_plan = (
        "<planner_exit>False</planner_exit><action>plan</action><reasoning>plan</reasoning>"
        "<task>plan it</task><data><name>planner</name><parameters>"
        "<steps_json>{\"phases\":[{\"sequence\":1,\"steps\":[{\"id\":\"a\",\"action\":\"tool_call\",}]}</steps_json>"
        "</parameters></data>"
    )
    mock_stream.side_effect = [
        iter([invalid_plan]),
        iter([invalid_plan]),
    ]

    out = agentnode.agent_node(_state("hello"), _config())
    assert out["next_step"]["action"] == "finish"
    assert "couldn't construct a valid execution plan" in out["next_step"]["answer"].lower()
