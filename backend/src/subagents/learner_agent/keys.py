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