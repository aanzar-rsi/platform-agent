"""Build retrieval / embed keys shared by learner and main agent."""

from __future__ import annotations

from typing import Any


def build_decision_state(user_query: str, execution_history: list[dict[str, Any]] | None = None) -> dict[str, str]:
    """Describe the current decision using task outcomes rather than result bodies."""
    history = [item for item in (execution_history or []) if isinstance(item, dict)]
    last = history[-1] if history else {}
    return {
        "query": (user_query or "").strip(),
        "decision_stage": "recovery" if last.get("success") is False else "general",
        "prior_task": str(last.get("task") or ""),
        "prior_tool": str(last.get("tool_name") or last.get("agent_name") or ""),
    }


def build_retrieval_queries(state: dict[str, str]) -> list[str]:
    query = build_embed_text(state.get("query", ""))
    detail = build_embed_text(state.get("query", ""), prior_task=state.get("prior_task", ""),
                              prior_tool=state.get("prior_tool", ""))
    return [query, f"{state.get('decision_stage', 'general')} after: {detail}"]


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
