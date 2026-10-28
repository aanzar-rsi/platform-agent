"""Build retrieval / embed keys shared by learner and main agent."""

from __future__ import annotations


def build_embed_text(
    user_query: str,
    *,
    prior_task: str = "",
    prior_tool: str = "",
) -> str:
    """Situation key used for both indexing and retrieval."""
    q = (user_query or "").strip()
    if not prior_task and not prior_tool:
        return f"query: {q}"
    parts = [f"query: {q}"]
    if prior_tool:
        parts.append(f"prior_tool: {prior_tool.strip()}")
    if prior_task:
        parts.append(f"prior_task: {prior_task.strip()}")
    return " | ".join(parts)


def build_decision_state(
    user_query: str,
    execution_history: list[dict] | None = None,
) -> dict:
    """Return the bounded state available before the agent's next decision."""
    history = [row for row in (execution_history or []) if isinstance(row, dict)]
    recent = history[-3:]
    completed = []
    failures = []
    corrections = []
    for row in recent:
        item = {
            "kind": row.get("type") or "unknown",
            "resource_type": row.get("resource_type") or "",
            "name": row.get("resource_name") or row.get("tool_name") or row.get("agent_name") or "",
            "task": row.get("task") or "",
            "outcome": "success" if row.get("success", True) else "failure",
        }
        if row.get("type") == "human_input":
            corrections.append(item)
        elif item["outcome"] == "failure":
            failures.append(item)
        else:
            completed.append(item)
    stage = "recovery" if failures or corrections else "transition" if history else "entry"
    return {
        "goal": (user_query or "").strip(),
        "decision_stage": stage,
        "current_subgoal": (recent[-1].get("task") or "") if recent else "form initial response or plan",
        "completed": completed,
        "failures": failures,
        "corrections": corrections,
        "pending": [item for item in completed if item.get("kind") == "child_agent" and
                    next((row.get("status") for row in recent if (row.get("task") or "") == item["task"]), "") == "running"],
    }


def build_retrieval_queries(decision_state: dict) -> list[str]:
    """Build small complementary queries instead of one over-specific history key."""
    goal = str(decision_state.get("goal") or "").strip()
    queries = [f"goal: {goal} | stage: {decision_state.get('decision_stage') or 'entry'}"]
    recent = (decision_state.get("failures") or decision_state.get("corrections") or
              decision_state.get("completed") or [])
    if recent:
        cues = "; ".join(
            " ".join(str(item.get(key) or "") for key in ("kind", "resource_type", "name", "task", "outcome")).strip()
            for item in recent[-3:]
        )
        queries.append(
            f"goal: {goal} | after: {cues} | next: {decision_state.get('current_subgoal') or 'next decision'}"
        )
    return queries
