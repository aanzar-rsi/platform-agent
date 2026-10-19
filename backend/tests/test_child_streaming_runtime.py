from __future__ import annotations

from api.services.agent_runtime import AgentRuntime
from api.services.packet_queue import ChatPacketQueue


def test_child_events_emit_started_step_finished(monkeypatch):
    from src.agent.subagent_stream import emit_child_event

    runtime = AgentRuntime()
    queue = ChatPacketQueue("agent-parent")

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

    runtime.run_turn(agent_id="agent-parent", owner_id="u1", query="go", queue=queue)
    packets = queue.snapshot_undelivered(0)
    child_packets = [p for p in packets if p["type"].startswith("child.")]
    assert [p["type"] for p in child_packets] == ["child.started", "child.step", "child.finished"]
    assert child_packets[0]["payload"]["child_agent_id"] == "child-1"
    assert child_packets[1]["payload"]["event"]["message"] == "child thought"
    assert child_packets[2]["payload"]["result"] == "child done"
    assert child_packets[2]["payload"]["success"] is True
