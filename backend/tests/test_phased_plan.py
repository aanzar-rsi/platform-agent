"""A plan must be safe to dispatch and parallel phases must merge once."""

import json
import threading
import time

import pytest
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from src.agent.nodes.execution_dispatcher import dispatch_execution, execution_dispatcher_node
from src.agent.nodes.result_collector import branch_result, result_collector_node
from src.agent.nodes.output_security_gate import output_security_gate_node
from src.agent.plan import parse_plan


def test_parse_plan_accepts_batch_name():
    raw = {
        "batch_name": "answer-lookup-1",
        "phases": [{
            "sequence": 1,
            "steps": [{
                "id": "s1", "action": "finish", "resource_type": None,
                "name": "", "task": "Answer", "parameters": {"answer": "done"},
                "uses": [], "child_calls": [],
            }],
        }],
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=1, resources=set())
    assert phases[0]["steps"][0]["action"] == "finish"
from src.agent.state import PlanExecuteState


def step(id, name, *, uses=None):
    return {"id": id, "action": "armory_call", "resource_type": "tool", "name": name, "task": id, "parameters": {}, "uses": uses or []}


def test_plan_validation_rejects_partial_or_unsafe_plans():
    tools = {"first", "second"}
    phases = [{"sequence": 1, "steps": [step("a", "first"), step("b", "second")]},
              {"sequence": 2, "steps": [step("c", "first", uses=["a", "b"])]}]
    assert len(parse_plan(json.dumps({"phases": phases}), max_plan_steps=3, resources={("tool", name) for name in tools})) == 2
    for broken in (
        {"phases": phases},
        {"phases": [{"sequence": 2, "steps": [step("a", "first")]}]},
        {"phases": [{"sequence": 1, "steps": [step("a", "first"), step("a", "second")]}]},
        {"phases": [{"sequence": 1, "steps": [step("a", "unknown")]}]},
        {"phases": [{"sequence": 1, "steps": [step("a", "first", uses=["a"])]}]},
    ):
        with pytest.raises(ValueError):
            parse_plan(json.dumps(broken), max_plan_steps=2, resources={("tool", name) for name in tools})


def test_parse_plan_accepts_ask_user_prompt_alias_and_normalizes_to_question():
    tools = {"first"}
    raw = {
        "phases": [
            {
                "sequence": 1,
                "steps": [
                    {
                        "id": "S1",
                        "action": "ask_user",
                        "name": "clarify",
                        "task": "clarify",
                        "parameters": {"prompt": "Which system should I check?"},
                        "uses": [],
                        "child_calls": [],
                    }
                ],
            }
        ]
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=4, resources={("tool", name) for name in tools})
    step = phases[0]["steps"][0]
    assert step["parameters"]["question"] == "Which system should I check?"


def test_parse_plan_serializes_context_loads_and_replans_before_finish():
    context_step = lambda id, key: {
        "id": id,
        "action": "context_select",
        "name": "",
        "task": f"load {key}",
        "parameters": {"key": key},
        "uses": [],
        "child_calls": [],
    }
    raw = {
        "phases": [
            {
                "sequence": 1,
                "steps": [context_step("tokyo", "tokyo-key"), context_step("dubai", "dubai-key")],
            },
            {
                "sequence": 2,
                "steps": [{
                    "id": "finish",
                    "action": "finish",
                    "name": "",
                    "task": "compare",
                    "parameters": {"answer": "Placeholder without loaded values"},
                    "uses": [],
                    "child_calls": [],
                }],
            },
        ]
    }

    phases = parse_plan(json.dumps(raw), max_plan_steps=4, resources=set())

    assert [phase["sequence"] for phase in phases] == [1, 2]
    assert [phase["steps"][0]["id"] for phase in phases] == ["tokyo", "dubai"]


def test_parse_plan_reports_empty_or_invalid_json_cleanly():
    tools = {"first"}
    with pytest.raises(ValueError, match="steps_json is empty"):
        parse_plan("", max_plan_steps=2, resources={("tool", name) for name in tools})

    with pytest.raises(ValueError, match="steps_json is not valid JSON"):
        parse_plan("not json", max_plan_steps=2, resources={("tool", name) for name in tools})

    with pytest.raises(ValueError, match="validation error|steps_json must be a JSON object"):
        parse_plan("[]", max_plan_steps=2, resources={("tool", name) for name in tools})


def test_parse_plan_accepts_fenced_json():
    tools = {"first"}
    raw = """```json
{
  "phases": [
    {
      "sequence": 1,
      "steps": [
        {
          "id": "a",
          "action": "armory_call", "resource_type": "tool",
          "name": "first",
          "task": "run",
          "parameters": {},
          "uses": [],
          "child_calls": []
        }
      ]
    }
  ]
}
```"""
    phases = parse_plan(raw, max_plan_steps=2, resources={("tool", name) for name in tools})
    assert phases[0]["steps"][0]["id"] == "a"


def test_parse_plan_recovers_from_wrapper_text_and_trailing_comma():
    tools = {"first"}
    raw = """Planner draft:\n{"phases":[{"sequence":1,"steps":[{"id":"a","action":"armory_call","resource_type":"tool","name":"first","task":"run","parameters":{},"uses":[],"child_calls":[],},],},],}\nIgnore above."""
    phases = parse_plan(raw, max_plan_steps=2, resources={("tool", name) for name in tools})
    assert phases[0]["steps"][0]["name"] == "first"


def test_parse_plan_accepts_literal_newline_in_string_via_lenient_json():
    tools = {"first"}
    raw = '{"phases":[{"sequence":1,"steps":[{"id":"a","action":"armory_call","resource_type":"tool","name":"first","task":"line1\nline2","parameters":{},"uses":[],"child_calls":[]}]}]}'
    phases = parse_plan(raw, max_plan_steps=2, resources={("tool", name) for name in tools})
    assert phases[0]["steps"][0]["task"].startswith("line1")


def test_parse_plan_recovers_from_unescaped_quotes_in_string_values():
    tools = {"first"}
    raw = '{"phases":[{"sequence":1,"steps":[{"id":"a","action":"armory_call","resource_type":"tool","name":"first","task":"Use "live" weather source","parameters":{},"uses":[],"child_calls":[]}]}]}'
    phases = parse_plan(raw, max_plan_steps=2, resources={("tool", name) for name in tools})
    assert phases[0]["steps"][0]["task"] == 'Use "live" weather source'


def test_parse_plan_accepts_top_level_phases_list():
    tools = {"first"}
    raw = json.dumps(
        [
            {
                "sequence": 1,
                "steps": [
                    {
                        "id": "a",
                        "action": "armory_call", "resource_type": "tool",
                        "name": "first",
                        "task": "run",
                        "parameters": {},
                        "uses": [],
                        "child_calls": [],
                    }
                ],
            }
        ]
    )
    phases = parse_plan(raw, max_plan_steps=2, resources={("tool", name) for name in tools})
    assert phases[0]["steps"][0]["id"] == "a"


def test_parse_plan_normalizes_spawn_children_string_child_calls():
    tools = {"first"}
    raw = {
        "phases": [
            {
                "sequence": 1,
                "steps": [
                    {
                        "id": "s1",
                        "action": "spawn_children",
                        "name": "spawn",
                        "task": "spawn weather workers",
                        "parameters": {},
                        "uses": [],
                        "child_calls": ["tokyo_child", "hyderabad_child"],
                    }
                ],
            }
        ]
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=4, resources={("tool", name) for name in tools})
    calls = phases[0]["steps"][0]["child_calls"]
    assert calls == [{"task": "tokyo_child"}, {"task": "hyderabad_child"}]


def test_parse_plan_stops_after_spawn_and_merges_parallel_spawn_steps():
    raw = {
        "phases": [
            {
                "sequence": 1,
                "steps": [
                    {"id": "s1", "action": "spawn_children", "name": "tokyo", "task": "spawn Tokyo",
                     "parameters": {}, "uses": [], "child_calls": [{"task": "Weather in Tokyo"}]},
                    {"id": "s2", "action": "spawn_children", "name": "hyderabad", "task": "spawn Hyderabad",
                     "parameters": {}, "uses": [], "child_calls": [{"task": "Weather in Hyderabad"}]},
                ],
            },
            {
                "sequence": 2,
                "steps": [
                    {"id": "c1", "action": "collect_child", "name": "made-up-id", "task": "collect",
                     "parameters": {}, "uses": [], "child_calls": []},
                    {"id": "c2", "action": "collect_child", "name": "another-made-up-id", "task": "collect",
                     "parameters": {}, "uses": [], "child_calls": []},
                ],
            },
        ]
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=8, resources=set())
    assert len(phases) == 1
    assert len(phases[0]["steps"]) == 1
    assert phases[0]["steps"][0]["child_calls"] == [
        {"task": "Weather in Tokyo"},
        {"task": "Weather in Hyderabad"},
    ]


def test_parse_plan_discards_invented_setup_tool_before_spawn():
    raw = {
        "phases": [
            {
                "sequence": 1,
                "steps": [
                    {"id": "setup", "action": "armory_call", "resource_type": "tool", "name": "decompose_query", "task": "decompose",
                     "parameters": {}, "uses": [], "child_calls": []},
                ],
            },
            {
                "sequence": 2,
                "steps": [
                    {"id": "spawn", "action": "spawn_children", "name": "spawn", "task": "spawn weather",
                     "parameters": {}, "uses": [], "child_calls": [{"task": "Weather in Tokyo"}]},
                ],
            },
        ]
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=4, resources=set())
    assert len(phases) == 1
    assert phases[0]["sequence"] == 1
    assert phases[0]["steps"][0]["action"] == "spawn_children"


def test_parse_plan_normalizes_phase_alias_to_sequence():
    raw = {
        "phases": [
            {
                "phase": 1,
                "steps": [
                    {"id": "s1", "action": "spawn_children", "name": "spawn", "task": "spawn",
                     "parameters": {}, "uses": [], "child_calls": [{"task": "Weather in Tokyo"}]},
                ],
            }
        ]
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=2, resources=set())
    assert phases[0]["sequence"] == 1
    assert "phase" not in phases[0]


def test_parse_plan_normalizes_phase_id_and_structured_child_tasks():
    raw = {
        "phases": [
            {
                "phase_id": 1,
                "name": "Weather",
                "steps": [
                    {"id": "s1", "action": "spawn_children", "name": "spawn",
                     "task": {"description": "Spawn weather agents"}, "parameters": {}, "uses": [],
                     "child_calls": [
                         {"task": {"action": "weather_fetch", "city": "Tokyo"}},
                         {"task": {"action": "weather_fetch", "city": "Hyderabad"}},
                     ]},
                ],
            }
        ]
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=2, resources=set())
    assert phases[0]["sequence"] == 1
    assert phases[0]["steps"][0]["task"] == "Spawn weather agents"
    assert all(isinstance(call["task"], str) for call in phases[0]["steps"][0]["child_calls"])


def test_parse_plan_drops_tool_names_from_uses():
    raw = {
        "phases": [
            {
                "sequence": 1,
                "steps": [
                    {"id": "s1", "action": "armory_call", "resource_type": "tool", "name": "web_search", "task": "weather",
                     "parameters": {"query": "Tokyo weather"}, "uses": ["web_search"], "child_calls": []},
                ],
            }
        ]
    }
    phases = parse_plan(json.dumps(raw), max_plan_steps=2, resources={("tool", "web_search")})
    assert phases[0]["steps"][0]["uses"] == []


def test_parse_plan_rejects_descriptive_resource_names():
    raw = {
        "phases": [{
            "sequence": 1,
            "steps": [{
                "id": 1,
                "action": "armory_call", "resource_type": "tool",
                "name": "Fetch weather via web_search",
                "task": "weather",
                "parameters": {"query": "Tokyo weather"},
                "uses": [],
                "child_calls": [],
            }],
        }]
    }
    with pytest.raises(ValueError, match="unavailable armory resource"):
        parse_plan(json.dumps(raw), max_plan_steps=2, resources={("tool", "web_search")})


def test_parse_plan_rejects_tool_parameter_alias():
    raw = {
        "phases": [{
            "sequence": 1,
            "steps": [{
                "id": "s1",
                "action": "armory_call", "resource_type": "tool",
                "name": "WebSearchFetchWeatherTokyo",
                "task": "weather",
                "parameters": {"tool": "web_search", "query": "Tokyo weather"},
                "uses": [],
                "child_calls": [],
            }],
        }]
    }
    with pytest.raises(ValueError, match="unavailable armory resource"):
        parse_plan(json.dumps(raw), max_plan_steps=2, resources={("tool", "web_search")})


def test_parse_plan_rejects_fuzzy_resource_names():
    raw = {
        "phases": [{
            "sequence": 1,
            "steps": [{
                "id": "s1",
                "action": "armory_call", "resource_type": "tool",
                "name": "Web search current weather Tokyo",
                "task": "weather",
                "parameters": {"query": "Tokyo weather"},
                "uses": [],
                "child_calls": [],
            }],
        }]
    }
    with pytest.raises(ValueError, match="unavailable armory resource"):
        parse_plan(json.dumps(raw), max_plan_steps=2, resources={("tool", "web_search")})


def test_parallel_phase_fanout_and_ordered_merge(monkeypatch):
    barrier = threading.Barrier(2)

    def fake_armory(state, config=None):
        barrier.wait(timeout=2)
        time.sleep(0.02 if state["next_step"]["resource_name"] == "first" else 0)
        return branch_result(state, {"action_id": state["next_step"]["action_id"], "source": "armory", "results": [{
            "kind": "armory_result", "value": state["next_step"]["resource_name"], "success": True,
            "name": state["next_step"]["resource_name"], "task": "run", "description": "run",
            "metadata": {"resource_type": "tool", "arguments": {}},
        }]})

    monkeypatch.setattr("src.agent.nodes.armory_node.armory_node", fake_armory)
    graph = StateGraph(PlanExecuteState)
    graph.add_node("execution_dispatcher", execution_dispatcher_node)
    graph.add_node("armory_node", fake_armory)
    graph.add_node("result_collector", result_collector_node)
    graph.add_node("output_security_gate", output_security_gate_node)
    graph.add_edge(START, "execution_dispatcher")
    graph.add_conditional_edges("execution_dispatcher", dispatch_execution,
                                {"armory_node": "armory_node", "agent_node": END})
    graph.add_edge("armory_node", "result_collector")
    graph.add_edge("result_collector", "output_security_gate")
    graph.add_edge("output_security_gate", END)
    app = graph.compile()
    state = {"messages": [HumanMessage(content="hi")], "execution_history": [], "execution_memory": {},
             "context_memory": None, "planned_phase_index": 0,
             "planned_phases": [{"sequence": 1, "steps": [step("a", "first"), step("b", "second")]}]}
    result = app.invoke(state, {"recursion_limit": 20})
    assert [entry["result"] for entry in result["execution_history"]] == ["first", "second"]
    assert [entry["step_id"] for entry in result["execution_history"]] == ["a", "b"]


def test_dispatcher_runs_sequential_phases_without_reinvoking_agent(monkeypatch):
    seen = []

    def fake_armory(state, config=None):
        seen.append(state["next_step"]["resource_name"])
        return branch_result(state, {"action_id": state["next_step"]["action_id"], "source": "armory", "results": [{
            "kind": "armory_result", "value": seen[-1], "success": True, "name": seen[-1],
            "task": "run", "description": "run", "metadata": {"resource_type": "tool", "arguments": {}},
        }]})

    monkeypatch.setattr("src.agent.nodes.armory_node.armory_node", fake_armory)
    graph = StateGraph(PlanExecuteState)
    graph.add_node("execution_dispatcher", execution_dispatcher_node)
    graph.add_node("armory_node", fake_armory)
    graph.add_node("result_collector", result_collector_node)
    graph.add_node("output_security_gate", output_security_gate_node)
    graph.add_edge(START, "execution_dispatcher")
    graph.add_conditional_edges("execution_dispatcher", dispatch_execution,
                                {"armory_node": "armory_node", "agent_node": END})
    graph.add_edge("armory_node", "result_collector")
    graph.add_edge("result_collector", "output_security_gate")
    graph.add_edge("output_security_gate", "execution_dispatcher")
    phases = [{"sequence": 1, "steps": [step("a", "first")]},
              {"sequence": 2, "steps": [step("b", "second", uses=["a"])]}]
    result = graph.compile().invoke({"messages": [], "execution_history": [], "execution_memory": {},
                                     "context_memory": None, "planned_phase_index": 0, "planned_phases": phases})
    assert seen == ["first", "second"]
    assert [entry["step_id"] for entry in result["execution_history"]] == ["a", "b"]
    assert result["planned_phases"] == []


def test_parallel_failure_replans_and_does_not_run_later_phase(monkeypatch):
    seen = []

    def fake_armory(state, config=None):
        name = state["next_step"]["resource_name"]
        seen.append(name)
        return branch_result(state, {"action_id": state["next_step"]["action_id"], "source": "armory", "results": [{
            "kind": "armory_result", "value": name, "success": name != "second", "name": name,
            "task": "run", "description": "run", "metadata": {"resource_type": "tool", "arguments": {}},
        }]})

    monkeypatch.setattr("src.agent.nodes.armory_node.armory_node", fake_armory)
    graph = StateGraph(PlanExecuteState)
    graph.add_node("execution_dispatcher", execution_dispatcher_node)
    graph.add_node("armory_node", fake_armory)
    graph.add_node("result_collector", result_collector_node)
    graph.add_node("output_security_gate", output_security_gate_node)
    graph.add_edge(START, "execution_dispatcher")
    graph.add_conditional_edges("execution_dispatcher", dispatch_execution,
                                {"armory_node": "armory_node", "agent_node": END})
    graph.add_edge("armory_node", "result_collector")
    graph.add_edge("result_collector", "output_security_gate")
    graph.add_edge("output_security_gate", "execution_dispatcher")
    phases = [{"sequence": 1, "steps": [step("a", "first"), step("b", "second")]},
              {"sequence": 2, "steps": [step("c", "third")]}]
    result = graph.compile().invoke({"messages": [], "execution_history": [], "execution_memory": {},
                                     "context_memory": None, "planned_phase_index": 0, "planned_phases": phases})
    assert sorted(seen) == ["first", "second"]
    assert any(event["kind"] == "plan.phase.finished" and event["payload"]["failed"]
               for event in result["output_events"])
    assert result["planned_phases"] == []


def test_finished_spawn_phase_marks_next_task_for_collection():
    child_entry = {
        "type": "child_agent",
        "child_agent_id": "child-1",
        "status": "running",
        "success": True,
        "task": "weather in Tokyo",
        "key": "child_agent_1",
    }
    step = {
        "id": "s1",
        "action": "spawn_children",
        "name": "spawn",
        "task": "spawn weather",
        "parameters": {},
        "uses": [],
        "child_calls": [{"task": "weather in Tokyo"}],
    }
    state = {
        "planned_phase_index": 0,
        "planned_phases": [{"sequence": 1, "steps": [step]}],
        "step_results": [{
            "id": "s1",
            "sequence": 1,
            "action": "child_agent",
            "task": "spawn weather",
            "name": "spawn",
            "results": [{"kind": "child_spawn", "value": {"status": "running"}, "success": True,
                             "status": "running", "name": "child_agent", "task": "weather in Tokyo",
                             "description": "weather in Tokyo", "metadata": {"child_agent_id": "child-1"}}],
        }],
        "execution_history": [],
        "execution_memory": {},
        "context_memory": None,
    }
    collected = result_collector_node(state)
    out = output_security_gate_node({**state, **collected})
    assert out["current_task"] == "collect_child"
    assert out["execution_history"][0]["key"].endswith("child-1")
