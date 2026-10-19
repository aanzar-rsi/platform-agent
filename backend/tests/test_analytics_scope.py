from api.db.repositories.analytics import AnalyticsRepository


def test_summary_can_filter_one_agent(monkeypatch):
    repo = AnalyticsRepository()

    monkeypatch.setattr(
        repo,
        "_llm_rows",
        lambda **_: [
            {
                "model_id": "gpt-4o-mini",
                "provider_model": "gpt-4o-mini",
                "status": "ok",
                "cached": False,
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "cost_usd": None,
                "usage": {},
                "latency_ms": 40,
            }
        ],
    )
    monkeypatch.setattr(repo, "_message_counts", lambda **_: {"total": 3, "human": 1, "ai": 1, "system": 1, "tool": 0, "other": 0})
    monkeypatch.setattr(
        repo,
        "_planner_analytics",
        lambda **_: {
            "invocations": 1,
            "plans_created": 1,
            "steps_created": 2,
            "steps_completed": 1,
            "steps_failed": 1,
            "retries": 0,
            "tokens": {"input": 0, "output": 0, "overhead": 0},
            "current_plan_overhead": {
                "total_tokens": 0,
                "tool_definitions": 0,
                "completed_steps": 0,
                "current_steps": 0,
                "remaining_steps": 0,
                "other": 0,
            },
        },
    )
    monkeypatch.setattr(
        repo,
        "_runtime_analytics",
        lambda **_: {
            "runs": 4,
            "successful_runs": 3,
            "failed_runs": 1,
            "cancelled_runs": 0,
            "total_ms": 1000,
            "average_ms": 250,
            "maximum_ms": 600,
            "splits": {
                "planning_ms": 0,
                "llm_ms": 0,
                "tool_ms": 0,
                "subagent_ms": 0,
                "memory_ms": 0,
                "checkpoint_ms": 0,
                "other_ms": 1000,
            },
        },
    )
    monkeypatch.setattr(
        repo,
        "_armory_analytics",
        lambda **_: {
            "configured": {"tools": 0, "mcp_servers": 0, "mcp_tools": 0, "subagents": 0},
            "invocations": {"tools": 0, "subagents": 0},
            "failures": {"tools": 0, "subagents": 0, "authorization": 0, "mcp_connection": 0},
            "by_resource": [],
        },
    )
    monkeypatch.setattr(
        repo,
        "_memory_analytics",
        lambda **_: {
            "extraction_attempts": 0,
            "extraction_failures": 0,
            "chunks_extracted": 0,
            "chunks_promoted": 0,
            "reads": 0,
            "writes": 0,
        },
    )
    monkeypatch.setattr(
        repo,
        "_context_analytics",
        lambda **_: {
            "latest": {"total_tokens": 0, "components": {}},
            "aggregate": {
                "samples": 0,
                "average_tokens": 0,
                "maximum_tokens": 0,
                "component_tokens": {},
                "component_percentages": {},
            },
        },
    )

    summary = repo.summary(uid="user-1", agent_id="agent-1")

    assert summary["uid"] == "user-1"
    assert summary["agent_id"] == "agent-1"
    assert summary["llm"]["tokens"]["total"] == 200
    assert summary["by_type"] == {"run_complete": 3, "run_error": 1, "agent_create": 0}
    assert summary["total_events"] == 4
