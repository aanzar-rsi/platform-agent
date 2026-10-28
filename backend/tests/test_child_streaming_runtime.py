from __future__ import annotations

from unittest.mock import Mock

from api.services.agent_runtime import AgentRuntime


class _Writer:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def enqueue(self, type_: str, payload: dict | None = None) -> dict:
        event = {"type": type_, "payload": payload or {}}
        self.events.append(event)
        return event


def test_child_events_emit_started_step_finished(monkeypatch):
    from src.agent.subagent_stream import emit_child_event

    runtime = AgentRuntime()
    writer = _Writer()

    monkeypatch.setattr("api.services.agent_runtime.get_agent_app", lambda: object())
    monkeypatch.setattr("src.utils.agent_logger.log_event", lambda *args, **kwargs: None)

    def fake_run_turn(*args, **kwargs):
        emit_child_event(
            "child_agent",
            {
                "kind": "start",
                "step": "spawn",
                "status": "in_progress",
                "message": "Starting",
                "task": "child task",
                "child_agent_id": "child-1",
            },
        )
        emit_child_event(
            "child_agent",
            {
                "kind": "reasoning",
                "step": "reasoning",
                "status": "in_progress",
                "message": "child thought",
                "child_agent_id": "child-1",
            },
        )
        emit_child_event(
            "child_agent",
            {
                "kind": "complete",
                "step": "collect",
                "status": "completed",
                "message": "Completed",
                "result": "child done",
                "success": True,
                "child_agent_id": "child-1",
            },
        )
        yield {"agent_node": {"next_step": {"action": "finish", "answer": "parent done"}}}

    monkeypatch.setattr("src.utils.postgres_checkpointer.run_turn", fake_run_turn)

    runtime.run_turn(agent_id="agent-parent", owner_id="u1", query="go", event_writer=writer)
    packets = writer.events
    child_packets = [p for p in packets if p["type"].startswith("child.")]
    assert [p["type"] for p in child_packets] == ["child.started", "child.step", "child.finished"]
    assert child_packets[0]["payload"]["child_agent_id"] == "child-1"
    assert child_packets[1]["payload"]["event"]["message"] == "child thought"
    assert child_packets[2]["payload"]["result"] == "child done"
    assert child_packets[2]["payload"]["success"] is True


def test_runtime_forwards_llm_lifecycle_and_dispatch_resource_events(monkeypatch):
    from src.agent.token_stream import emit_lifecycle

    runtime = AgentRuntime()
    writer = _Writer()
    monkeypatch.setattr("api.services.agent_runtime.get_agent_app", lambda: object())
    monkeypatch.setattr("src.utils.agent_logger.log_event", lambda *args, **kwargs: None)

    def fake_run_turn(*args, **kwargs):
        emit_lifecycle("llm.started", {"call_id": "call-1", "model_id": "test"})
        emit_lifecycle("llm.done", {"call_id": "call-1", "model_id": "test"})
        yield {"execution_dispatcher": {"plan_event": {
            "kind": "phase.started", "sequence": 1, "steps": [{
                "id": "s1", "action_id": "action-1", "action": "armory",
                "resource_type": "tool", "name": "lookup", "task": "find",
                "tool_args": {"q": "x"},
            }],
        }}}
        yield {"agent_node": {"next_step": {"action": "finish", "answer": "done"}}}

    monkeypatch.setattr("src.utils.postgres_checkpointer.run_turn", fake_run_turn)
    runtime.run_turn(agent_id="agent-parent", owner_id="u1", query="go", event_writer=writer)

    assert [(event["type"], event["payload"].get("call_id")) for event in writer.events
            if event["type"].startswith("llm.")] == [
        ("llm.started", "call-1"), ("llm.done", "call-1"),
    ]
    started = next(event for event in writer.events if event["type"] == "tool.started")
    assert started["payload"] == {
        "action_id": "action-1", "tool_name": "lookup", "tool_args": {"q": "x"}, "task": "find",
    }


def test_runtime_handles_graph_recursion_limit_without_exception_log(monkeypatch):
    from langgraph.errors import GraphRecursionError

    runtime = AgentRuntime()
    writer = _Writer()
    completed = []
    monkeypatch.setattr("api.services.agent_runtime.get_agent_app", lambda: object())
    monkeypatch.setattr("src.utils.agent_logger.log_error", lambda **kwargs: None)
    exception_log = Mock()
    monkeypatch.setattr("api.services.agent_runtime.logger.exception", exception_log)

    def fake_run_turn(*args, **kwargs):
        raise GraphRecursionError("Recursion limit of 7 reached")
        yield

    monkeypatch.setattr("src.utils.postgres_checkpointer.run_turn", fake_run_turn)
    runtime.run_turn(
        agent_id="agent-parent",
        owner_id="u1",
        query="loop",
        event_writer=writer,
        runtime={"max_loops": 7},
        on_complete=lambda *args: completed.append(args),
    )

    error = next(event for event in writer.events if event["type"] == "run.error")
    assert error["payload"]["message"] == (
        "The agent stopped after reaching its 7-step execution limit. "
        "Try simplifying the request or increase Max loops in Settings."
    )
    exception_log.assert_not_called()
    assert completed == [("failed", None, "GraphRecursionError")]


def test_runtime_reports_configured_default_recursion_limit(monkeypatch):
    from langgraph.errors import GraphRecursionError
    from src.config import settings

    writer = _Writer()
    monkeypatch.setattr(settings, "max_loops", 500)
    monkeypatch.setattr("api.services.agent_runtime.get_agent_app", lambda: object())
    monkeypatch.setattr("src.utils.agent_logger.log_error", lambda **kwargs: None)

    def fake_run_turn(*args, **kwargs):
        raise GraphRecursionError("Recursion limit reached")
        yield

    monkeypatch.setattr("src.utils.postgres_checkpointer.run_turn", fake_run_turn)
    AgentRuntime().run_turn(agent_id="agent-parent", owner_id="u1", query="loop", event_writer=writer)
    error = next(event for event in writer.events if event["type"] == "run.error")
    assert "500-step execution limit" in error["payload"]["message"]
