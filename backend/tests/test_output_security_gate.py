from langchain_core.messages import HumanMessage

from src.agent.memory import CONTEXT_MEMORY_BUDGET, empty_context_memory
from src.agent.nodes.output_security_gate import output_security_gate_node, sanitize_value


def envelope(result, *, action_id="run:action:1", source="armory"):
    return {"version": 1, "action_id": action_id, "source": source, "results": [result]}


def tool_result(value="ok", success=True):
    return {
        "kind": "armory_result", "value": value, "success": success,
        "name": "lookup", "task": "find", "description": "find",
        "metadata": {"resource_type": "tool", "arguments": {"q": "x"}, "ignored": "drop"},
    }


def state(output):
    return {"executor_output": output, "execution_history": [], "execution_memory": {},
            "context_memory": empty_context_memory(), "planned_phases": []}


def test_sanitizer_redacts_credentials_controls_and_cycles():
    value = {"api_key": "abc", "text": "password=hunter2\x00"}
    value["self"] = value
    clean = sanitize_value(value)
    assert clean["api_key"] == "[REDACTED]"
    assert clean["text"] == "password=[REDACTED]"
    assert clean["self"] == "[CYCLE]"
    assert sanitize_value(clean) == clean


def test_gate_commits_tool_result_and_auto_ingests_context():
    out = output_security_gate_node(state(envelope(tool_result({"rows": [1, 2]}))))
    assert out["execution_history"][0]["value"] == {"rows": [1, 2]}
    assert out["execution_memory"]["run:action:1"]["result"] == {"rows": [1, 2]}
    assert out["context_memory"]["entries"][0]["key"] == "run:action:1"
    assert out["output_events"][0]["kind"] == "tool.finished"
    assert out["messages"][0].additional_kwargs["ui_hidden"] is True


def test_parallel_actions_keep_individual_tasks_in_history_and_events(monkeypatch):
    from unittest.mock import MagicMock
    from src.agent.nodes.armory_node import armory_node
    from src.agent.nodes.result_collector import result_collector_node

    monkeypatch.setattr("src.agent.nodes.armory_node.Armory.get",
                        lambda *args, **kwargs: MagicMock(confirmation_required=False))
    monkeypatch.setattr("src.agent.nodes.armory_node.Armory.call",
                        lambda *args, **kwargs: ("ok", None))
    current = state({})
    current.update(current_task="batch task", planned_phase_index=0,
                   planned_phases=[{"sequence": 1, "steps": [
                       {"id": "vendors"}, {"id": "materials"},
                   ]}])
    results = []
    for step_id, task in (("vendors", "Retrieve vendors"), ("materials", "Find laptop materials")):
        branch = {**current, "next_step": {"action": "armory", "action_id": step_id,
                                           "resource_type": "tool", "resource_name": "lookup",
                                           "task": task},
                  "dispatch_step": {"id": step_id, "sequence": 1, "action_id": step_id}}
        results += armory_node(branch)["step_results"]
    out = output_security_gate_node({**current, "step_results": results,
                                     **result_collector_node({**current, "step_results": results})})
    assert [row["task"] for row in out["execution_history"]] == ["Retrieve vendors", "Find laptop materials"]
    assert [event["payload"]["task"] for event in out["output_events"]
            if event["kind"] == "tool.finished"] == ["Retrieve vendors", "Find laptop materials"]


def test_gate_is_idempotent_for_replayed_action():
    first = output_security_gate_node(state(envelope(tool_result("one"))))
    replay_state = {**state(envelope(tool_result("two"))),
                    "execution_history": first["execution_history"],
                    "execution_memory": first["execution_memory"],
                    "context_memory": first["context_memory"]}
    second = output_security_gate_node(replay_state)
    assert len(second["execution_history"]) == 1
    assert second["execution_history"][0]["value"] == "two"
    assert len(second["context_memory"]["entries"]) == 1


def test_malformed_envelope_fails_closed():
    out = output_security_gate_node(state({"source": "armory", "action_id": "bad", "results": [{}]}))
    assert out["execution_history"][0]["type"] == "executor_error"
    assert out["execution_history"][0]["success"] is False


def test_human_input_becomes_trusted_human_message():
    result = {"kind": "human_input", "value": "Hyderabad", "success": True,
              "task": "city", "description": "Which city?", "metadata": {"question": "Which city?"}}
    out = output_security_gate_node(state(envelope(result, source="human_input")))
    assert isinstance(out["messages"][0], HumanMessage)


def test_oversized_output_stays_full_in_memory_and_bounded_in_context():
    huge = "x" * ((CONTEXT_MEMORY_BUDGET + 100) * 4)
    out = output_security_gate_node(state(envelope(tool_result(huge))))
    assert out["execution_memory"]["run:action:1"]["value"] == huge
    assert out["context_memory"]["used_tokens"] <= CONTEXT_MEMORY_BUDGET


def test_planned_results_commit_in_step_order_and_advance_plan():
    output = {"version": 1, "action_id": "run:phase:1", "source": "planned_phase", "phase": 1,
              "steps": [{"id": "a", "results": [tool_result("first")]},
                        {"id": "b", "results": [tool_result("second")]}]}
    current = state(output)
    current.update(planned_phases=[{"sequence": 1}, {"sequence": 2}], planned_phase_index=0)
    out = output_security_gate_node(current)
    assert [row["value"] for row in out["execution_history"]] == ["first", "second"]
    assert [row["step_id"] for row in out["execution_history"]] == ["a", "b"]
    assert out["planned_phase_index"] == 1
    assert [event["kind"] for event in out["output_events"]] == [
        "tool.finished", "plan.step.finished", "tool.finished", "plan.step.finished",
        "plan.phase.finished",
    ]
    assert out["output_events"][0]["payload"]["action_id"] == "run:phase:1"


def test_multiple_results_from_one_dispatched_step_keep_distinct_keys():
    human = {"kind": "human_input", "value": "approved", "success": True,
             "task": "confirm", "description": "confirmation", "metadata": {"input_kind": "confirmation"}}
    output = {"version": 1, "action_id": "run:phase:1", "source": "planned_phase", "phase": 1,
              "steps": [{"id": "a", "results": [human, tool_result("done")]}]}
    current = state(output)
    current.update(planned_phases=[{"sequence": 1}], planned_phase_index=0)
    out = output_security_gate_node(current)
    assert [row["key"] for row in out["execution_history"]] == [
        "run:phase:1:step:a", "run:phase:1:step:a:result:2",
    ]


def test_child_collection_preserves_spawn_parameters_and_policy():
    child_id = "child-1"
    spawned = output_security_gate_node(state(envelope({
        "kind": "child_spawn", "value": {"status": "running"}, "success": True,
        "status": "running", "task": "research", "metadata": {
            "child_agent_id": child_id, "tool_args": {"topic": "memory"},
            "requested_policy": {"memory": {"read": ["USER"]}},
        },
    }, action_id="run:spawn", source="child_agent")))
    collected_state = state(envelope({
        "kind": "child_collection", "value": "done", "success": True,
        "task": "research", "metadata": {"child_agent_id": child_id},
    }, action_id="run:collect", source="collect_child"))
    collected_state.update(
        execution_history=spawned["execution_history"], execution_memory=spawned["execution_memory"],
        context_memory=spawned["context_memory"],
    )
    out = output_security_gate_node(collected_state)
    assert len(out["execution_history"]) == 1
    assert out["execution_history"][0]["tool_args"] == {"topic": "memory"}
    assert out["execution_history"][0]["requested_policy"] == {"memory": {"read": ["USER"]}}


def test_collect_child_timeout_keeps_child_running_and_requeues(monkeypatch):
    from src.agent.nodes.collect_child import collect_child_node
    from src.agent.nodes.result_collector import result_collector_node

    child_id = "child-1"

    def _timeout(*args, **kwargs):
        raise TimeoutError("child_still_running")

    monkeypatch.setattr("src.agent.nodes.collect_child.child_runner.await_child", _timeout)

    current = {
        "next_step": {
            "action": "collect_child",
            "child_agent_id": child_id,
            "task": "Collect outstanding child",
            "action_id": "run:phase:1:step:c1",
        },
        "dispatch_step": {
            "id": "c1",
            "sequence": 1,
            "action": "collect_child",
            "task": "Collect outstanding child",
            "name": "child_agent",
            "action_id": "run:phase:1:step:c1",
        },
        "execution_history": [{
            "key": "run:spawn:child:child-1",
            "type": "child_agent",
            "child_agent_id": child_id,
            "status": "running",
            "success": True,
            "task": "Research",
        }],
        "execution_memory": {"run:spawn:child:child-1": {"key": "run:spawn:child:child-1"}},
        "context_memory": empty_context_memory(),
        "planned_phases": [{"sequence": 1, "steps": [{"id": "c1"}]}],
        "planned_phase_index": 0,
    }

    branch = collect_child_node(current)
    collected = result_collector_node({**current, **branch})
    out = output_security_gate_node({**current, **branch, **collected})

    assert out["execution_history"][0]["status"] == "running"
    assert out["execution_history"][0]["value"] == "child_still_running"
    assert out["planned_phases"] == []
    assert out["current_task"] == "collect_child"
    assert any(event["kind"] == "child.started" for event in out["output_events"])
