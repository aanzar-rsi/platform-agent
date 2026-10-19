"""Authorized view of active learned experiences."""

from collections import Counter
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from api.core.deps import CurrentUser, require_user
from src.agent import kb
from src.agent.agent_core import default_policy

router = APIRouter(prefix="/experience", tags=["experience"], dependencies=[Depends(require_user)])


@router.get("")
def list_experiences(user: Annotated[CurrentUser, Depends(require_user)], scope: str = "user") -> dict:
    if scope != "user":
        raise HTTPException(status_code=403, detail="Use authorized KB scopes")
    policy = default_policy().memory
    rows = kb.list_chunks(user.uid, policy, scope="USER")
    chunks = [{"id": row["chunk_id"], "type": row["chunk_type"], "advice": row["content"],
               "metadata": {**row["metadata"], "created_at": row["created_at"]}} for row in rows]
    tools = Counter((c["metadata"].get("observed_tool") or "unknown") for c in chunks)
    outcomes = Counter((c["metadata"].get("outcome") or "unknown") for c in chunks)
    nodes = [{"id": "tool:" + name, "kind": "tool", "label": name, "count": count}
             for name, count in tools.items()]
    nodes += [{"id": c["id"], "kind": "experience", "label": c["advice"][:80],
               "tool": c["metadata"].get("observed_tool") or "unknown",
               "outcome": c["metadata"].get("outcome") or "unknown"} for c in chunks]
    links = [{"source": c["id"], "target": "tool:" + (c["metadata"].get("observed_tool") or "unknown"),
              "weight": 1, "kind": "belongs"} for c in chunks]
    return {"chunks": chunks, "graph": {"nodes": nodes, "links": links,
            "stats": {"total": len(chunks), "tools": len(tools), "chats": 0,
                      "outcomes": dict(outcomes),
                      "tool_breakdown": [{"tool": k, "count": v} for k, v in tools.items()]}}, "scope": scope}


@router.get("/{chunk_id}")
def get_experience(chunk_id: str, user: Annotated[CurrentUser, Depends(require_user)]) -> dict:
    try:
        row = kb.get_chunk(user.uid, default_policy().memory, chunk_id)
        if row["scope"] != "USER":
            raise KeyError("chunk_not_found")
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")
    return {"chunk": {"id": row["chunk_id"], "type": row["chunk_type"],
                      "advice": row["content"], "metadata": row["metadata"]}}
