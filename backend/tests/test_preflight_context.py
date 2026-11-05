"""Governed Preflight context policy, retrieval, and audit safety tests."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest

from src.agent.preflight.audit_repository import normalized_query_hash, write_preflight_audit
from src.agent.preflight.context import (
    classify_episodic_memory_need,
    derive_governed_memory_policy,
    load_governed_context,
)


USER_ID = str(uuid.uuid4())


def _identity(**policy):
    return {
        "user_id": USER_ID,
        "tenant_id": "65f0a1b2c3d4e5f607182901",
        "tenant_policy": {
            "allowed_memory_scopes": ["USER", "TENANT"],
            "allowed_memory_types": ["workflow"],
            "maximum_sensitivity": "CONFIDENTIAL",
            **policy,
        },
    }


def _config(tenant_id="65f0a1b2c3d4e5f607182901"):
    return {"configurable": {"policy": {"memory": {
        "enabled": True,
        "tenant_id": tenant_id,
        "read": ["USER", "TENANT", "AGENT"],
        "write": ["USER"],
    }}}}


def test_policy_intersects_scopes_and_verified_tenant():
    policy = derive_governed_memory_policy(_identity(), _config())
    assert policy["read"] == ["USER", "TENANT"]
    assert policy["tenant_id"] == "65f0a1b2c3d4e5f607182901"
    assert policy["allowed_memory_types"] == ["workflow"]


def test_policy_rejects_mismatched_tenant():
    with pytest.raises(PermissionError, match="memory_tenant_mismatch"):
        derive_governed_memory_policy(_identity(), _config("65f0a1b2c3d4e5f607182999"))


def test_context_filters_sensitivity_and_keeps_safe_references():
    hits = [
        {"chunk_id": "chk_1", "active_version_id": "v_1", "scope": "USER", "chunk_type": "workflow",
         "content": "approved guidance", "sensitivity": "INTERNAL", "score": 0.8},
        {"chunk_id": "chk_2", "active_version_id": "v_2", "scope": "USER", "chunk_type": "workflow",
         "content": "restricted guidance", "sensitivity": "RESTRICTED", "score": 0.9},
    ]
    result = load_governed_context(
        request={"query": "remember my previous approach"},
        state={},
        identity_context=_identity(),
        config=_config(),
        search=lambda *_args, **_kwargs: hits,
        index_available=lambda: True,
        classify_memory_need=lambda *_args, **_kwargs: (True, "prior_context_required"),
    )
    assert result.decision == "degrade"
    assert [item.content for item in result.items] == ["approved guidance"]
    assert result.planner_context()["memory_references"] == [{
        "chunk_id": "chk_1", "version_id": "v_1", "scope": "USER", "provenance": "episodic_memory"
    }]


def test_optional_index_failure_degrades_without_memory():
    result = load_governed_context(
        request={"query": "remember my previous approach"}, state={}, identity_context=_identity(), config=_config(),
        search=lambda *_args, **_kwargs: [], index_available=lambda: False,
        classify_memory_need=lambda *_args, **_kwargs: (True, "prior_context_required"),
    )
    assert result.decision == "degrade"
    assert result.reason_code == "optional_memory_unavailable"
    assert result.items == ()


def test_slow_optional_memory_search_degrades_before_planning():
    from concurrent.futures import TimeoutError as SearchTimeout

    with patch("src.agent.preflight.context._search_executor") as executor:
        executor.submit.return_value.result.side_effect = SearchTimeout()
        result = load_governed_context(
            request={"query": "remember my previous approach"}, state={},
            identity_context=_identity(), config=_config(),
            index_available=lambda: True, search=lambda *_args, **_kwargs: [],
            classify_memory_need=lambda *_args, **_kwargs: (True, "prior_context_required"),
        )
    assert result.decision == "degrade"
    assert result.reason_code == "optional_memory_timeout"
    assert result.items == ()
    executor.submit.return_value.result.assert_called_once_with(timeout=5)


def test_memory_authorization_failure_denies():
    def deny(*_args, **_kwargs):
        raise PermissionError("memory_scope_denied")

    result = load_governed_context(
        request={"query": "remember my previous approach"}, state={},
        identity_context=_identity(), config=_config(), search=deny, index_available=lambda: True,
        classify_memory_need=lambda *_args, **_kwargs: (True, "prior_context_required"),
    )
    assert result.decision == "deny"
    assert result.reason_code == "memory_scope_mismatch"


def test_working_memory_requires_verified_provenance():
    state = {
        "execution_memory": {
            "trusted": {"owner_user_id": USER_ID, "tenant_id": "65f0a1b2c3d4e5f607182901", "sensitivity": "INTERNAL"},
            "legacy": {"value": "legacy"},
        },
        "context_memory": {"entries": [
            {"key": "trusted", "content": "current result", "complete": True},
            {"key": "legacy", "content": "legacy", "complete": True},
        ]},
    }
    result = load_governed_context(
        request={"query": "help"}, state=state, identity_context=_identity(), config={"configurable": {"policy": {}}},
    )
    assert [item.content for item in result.items] == ["current result"]
    assert result.decision == "degrade"


def test_llm_decision_skips_optional_episodic_index():
    result = load_governed_context(
        request={"query": "calculate this total"}, state={}, identity_context=_identity(), config=_config(),
        search=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
        index_available=lambda: (_ for _ in ()).throw(AssertionError("index should not run")),
        classify_memory_need=lambda *_args, **_kwargs: (False, "current_context_sufficient"),
    )
    assert result.decision == "allow"
    assert result.reason_code == "context_ready"


def test_context_timing_separates_classification_index_and_search():
    records = []
    with patch("src.agent.preflight.context.in_run", return_value=True), \
         patch("src.agent.preflight.context.trace_emit", side_effect=lambda *args, **kwargs: records.append((args, kwargs))):
        load_governed_context(
            request={"query": "previous workflow"}, state={}, identity_context=_identity(), config=_config(),
            classify_memory_need=lambda *_args, **_kwargs: (True, "prior_context_required"),
            index_available=lambda: True, search=lambda *_args, **_kwargs: [],
        )
    assert [event[1]["data"]["stage"] for event in records] == [
        "memory.need_classification", "memory.index_check", "memory.search",
    ]
    assert all(event[1]["duration_ms"] >= 0 for event in records)


def test_memory_need_classifier_uses_strict_json_llm_output():
    with patch("src.models.llm_client.call_llm", return_value={
        "needed": True, "reason_code": "personalization_useful"
    }) as call:
        needed, reason = classify_episodic_memory_need("recommend a supplier", working_context_count=0)
    assert needed is True
    assert reason == "personalization_useful"
    assert call.call_args.kwargs["output_type"] == "json"
    assert call.call_args.kwargs["temperature"] == 0.0


def test_invalid_memory_need_classification_degrades_without_search():
    result = load_governed_context(
        request={"query": "recommend a supplier"}, state={}, identity_context=_identity(), config=_config(),
        search=lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("search should not run")),
        index_available=lambda: (_ for _ in ()).throw(AssertionError("index should not run")),
        classify_memory_need=lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("invalid")),
    )
    assert result.decision == "degrade"
    assert result.reason_code == "memory_need_classification_unavailable"


def test_inconsistent_memory_need_classification_is_rejected():
    with patch("src.models.llm_client.call_llm", return_value={
        "needed": False, "reason_code": "personalization_useful"
    }):
        with pytest.raises(ValueError, match="invalid_memory_need_classification"):
            classify_episodic_memory_need("recommend a supplier", working_context_count=0)


def test_audit_hash_normalizes_whitespace():
    assert normalized_query_hash("  compare   quotes ") == normalized_query_hash("compare quotes")


def test_audit_writer_never_receives_raw_memory_content():
    captured = {}

    def execute(_sql, params):
        captured["params"] = params
        return 1

    with patch("src.utils.postgres.db_utils.execute", execute):
        write_preflight_audit({
            "request_id": "65f0a1b2c3d4e5f607182901",
            "query_hash": "a" * 64,
            "decision": "allow",
            "reason_code": "context_ready",
            "memory_references": [{"chunk_id": "chk_1", "version_id": "v_1"}],
        })
    assert "secret recalled value" not in repr(captured["params"])
    assert "chk_1" in repr(captured["params"])
