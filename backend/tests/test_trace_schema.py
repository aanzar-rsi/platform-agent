"""Trace envelope, lineage, redaction and handled failure checks."""

import json
import logging
import os

import pytest

import src.utils.trace as trace_module
from src.utils.trace import bind, emit, reset, span
from src.utils.trace import bind_from_config, traced_node


def test_trace_correlations_and_redaction(caplog):
    old = os.environ.get("EVA_TRACE_LOGGER_ENABLED")
    os.environ["EVA_TRACE_LOGGER_ENABLED"] = "1"
    token = bind(agent_id="a", execution_id="e", owner_id="u", session_id="s")
    try:
        with caplog.at_level(logging.INFO, logger="agent.trace"):
            with span("tool", "call", component="tool_node", data={"tool_name": "search",
                                                                  "raw_secret": "password123"}):
                emit("child.lifecycle.spawn", child_agent_id="child", component="agent_core",
                     data={"task_size": 12})
        events = [json.loads(record.message) for record in caplog.records if record.name == "agent.trace"]
        assert [row["event"] for row in events] == ["tool.call.start", "child.lifecycle.spawn", "tool.call.end"]
        assert {row["trace"]["trace_id"] for row in events}.__len__() == 1
        assert events[1]["trace"]["parent_span_id"] == events[0]["trace"]["span_id"]
        assert all(row["ids"]["execution_id"] == "e" for row in events)
        assert events[0]["security"]["contains_redacted"]
        assert "password123" not in str(events)
        assert events[-1]["metrics"]["duration_ms"] is not None
    finally:
        reset(token)
        if old is None:
            os.environ.pop("EVA_TRACE_LOGGER_ENABLED", None)
        else:
            os.environ["EVA_TRACE_LOGGER_ENABLED"] = old


def test_missing_ids_fail_and_handled_error_emits(caplog):
    old = os.environ.get("EVA_TRACE_LOGGER_ENABLED")
    os.environ["EVA_TRACE_LOGGER_ENABLED"] = "1"
    with pytest.raises(ValueError, match="missing_trace_correlation"):
        emit("tool.call.start")
    token = bind(agent_id="a", execution_id="e")
    try:
        with caplog.at_level(logging.INFO, logger="agent.trace"):
            try:
                with span("tool", "call", component="tool_node"):
                    raise RuntimeError("sensitive details")
            except RuntimeError:
                pass
        error = json.loads([record.message for record in caplog.records
                            if record.name == "agent.trace"][-1])
        assert error["event"] == "tool.call.error"
        assert error["status"] == "error"
        assert error["error"]["type"] == "RuntimeError"
        assert "sensitive details" not in str(error)
    finally:
        reset(token)
        if old is None:
            os.environ.pop("EVA_TRACE_LOGGER_ENABLED", None)
        else:
            os.environ["EVA_TRACE_LOGGER_ENABLED"] = old


def test_node_error_and_config_propagation(caplog):
    old = os.environ.get("EVA_TRACE_LOGGER_ENABLED")
    os.environ["EVA_TRACE_LOGGER_ENABLED"] = "1"
    try:
        def boom(state, config):
            raise RuntimeError("sensitive payload")

        config = {"configurable": {"agent_id": "a", "execution_id": "e",
                                   "trace_id": "trc_original", "span_id": "spn_parent"}}
        with caplog.at_level(logging.INFO, logger="agent.trace"):
            with pytest.raises(RuntimeError):
                traced_node("agent_node", boom)({}, config)
        events = [json.loads(record.message) for record in caplog.records if record.name == "agent.trace"]
        assert [event["event"] for event in events] == ["node.execution.start", "node.execution.error"]
        assert all(event["trace"]["trace_id"] == "trc_original" for event in events)
        assert all(event["trace"]["parent_span_id"] == "spn_parent" for event in events)
        assert events[1]["metrics"]["duration_ms"] is not None
        assert "sensitive payload" not in str(events)
    finally:
        if old is None:
            os.environ.pop("EVA_TRACE_LOGGER_ENABLED", None)
        else:
            os.environ["EVA_TRACE_LOGGER_ENABLED"] = old


def test_checkpoint_event_outside_run_and_memory_denial(caplog):
    token = bind(agent_id="a", owner_id="u")
    try:
        assert emit("checkpoint.list", data={"returned_count": 0})["ids"]["execution_id"] is None
        with pytest.raises(ValueError, match="missing_trace_correlation"):
            emit("memory.retrieve.start")
    finally:
        reset(token)


def test_trace_persists_session_json(tmp_path):
    original = trace_module._TRACE_DIR
    trace_module._TRACE_DIR = tmp_path
    token = bind(agent_id="agent/1", session_id="sess:1", owner_id="u")
    try:
        emit("session.websocket.attach", component="websocket")
        emit("session.websocket.detach", component="websocket", duration_ms=1.0)
    finally:
        reset(token)
        trace_module._TRACE_DIR = original

    path = tmp_path / "agent_1.json"
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["session_id"] == "sess:1"
    assert payload["agent_id"] == "agent/1"
    assert [event["event"] for event in payload["events"]] == [
        "session.websocket.attach",
        "session.websocket.detach",
    ]
