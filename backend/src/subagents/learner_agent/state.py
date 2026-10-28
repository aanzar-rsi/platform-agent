"""Learner agent graph state."""

from __future__ import annotations

from typing import Any, List

from typing_extensions import TypedDict


class LearnerState(TypedDict, total=False):
    agent_id: str
    uid: str
    branch_checkpoint_id: str  # optional — learn from a specific branch tip instead of the latest
    user_query: str
    messages_summary: str
    conversation_messages: List[dict[str, Any]]
    execution_history: List[dict[str, Any]]
    decision_snapshots: List[dict[str, Any]]
    allowed_chunk_types: List[str]
    chunks: List[dict[str, Any]]
    stored_count: int
    status: str  # pending|learned|skipped|error
    error: str
    policy: dict[str, Any]
    extraction_request_id: str
    extraction_requests: dict[str, dict[str, Any]]
