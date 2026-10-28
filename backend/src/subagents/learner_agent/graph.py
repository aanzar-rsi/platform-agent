"""Standalone learner LangGraph: load_session → extract_chunks → persist."""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.subagents.learner_agent.nodes.extract_chunks import extract_chunks_node
from src.subagents.learner_agent.nodes.load_session import load_session_node
from src.subagents.learner_agent.nodes.persist import persist_node
from src.subagents.learner_agent.state import LearnerState

logger = logging.getLogger(__name__)

LOAD = "load_session"
EXTRACT = "extract_chunks"
PERSIST = "persist"

_workflow = StateGraph(LearnerState)
_workflow.add_node(LOAD, load_session_node)
_workflow.add_node(EXTRACT, extract_chunks_node)
_workflow.add_node(PERSIST, persist_node)
_workflow.add_edge(START, LOAD)
_workflow.add_edge(LOAD, EXTRACT)
_workflow.add_edge(EXTRACT, PERSIST)
_workflow.add_edge(PERSIST, END)

learner_app = _workflow.compile()


def learn_session(agent_id: str, *, uid: str = "", checkpoint_id: str | None = None) -> dict[str, Any]:
    """
    Run the learner graph for one chat. Soft-fails: returns status dict, never raises.
    Events are appended to the same logs/{agent_id}.jsonl as the main agent.

    `checkpoint_id`, when given, learns from that specific branch tip instead
    of the thread's latest checkpoint — lets the idle watcher cover every
    forked branch, not just the current head.
    """
    if not agent_id:
        return {"status": "error", "error": "missing agent_id", "stored_count": 0, "chunks": []}

    from src.utils.agent_logger import (
        bind_session_logger,
        log_event,
        reset_session_logger,
    )

    token = bind_session_logger(agent_id, owner_id=uid or "")
    log_event("learner.start", agent_id=agent_id, checkpoint_id=checkpoint_id or "")
    try:
        result = learner_app.invoke(
            {
                "agent_id": agent_id,
                "uid": uid or "",
                "branch_checkpoint_id": checkpoint_id or "",
                "chunks": [],
                "stored_count": 0,
                "status": "pending",
                "error": "",
                "policy": {},
                "extraction_request_id": "",
                "extraction_requests": {},
                "conversation_messages": [],
                "decision_snapshots": [],
                "allowed_chunk_types": [],
            }
        )
        out = {
            "status": result.get("status") or "error",
            "error": result.get("error") or "",
            "stored_count": result.get("stored_count") or 0,
            "chunks": [],
            "agent_id": agent_id,
            "uid": uid,
        }
        log_event(
            "learner.end",
            status=out["status"],
            stored_count=out["stored_count"],
            error=out["error"],
            chunk_count=len(out["chunks"]),
        )
        return out
    except Exception as e:
        logger.warning("learn_session failed agent_id=%s", agent_id, exc_info=True)
        log_event("learner.end", status="error", error=str(e), stored_count=0)
        return {
            "status": "error",
            "error": str(e),
            "stored_count": 0,
            "chunks": [],
            "agent_id": agent_id,
            "uid": uid,
        }
    finally:
        reset_session_logger(token)
