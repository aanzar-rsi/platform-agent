from __future__ import annotations

from fastapi import HTTPException

from api.core.deps import CurrentUser, Repositories
from api.domain.chat import CheckpointOut, CheckpointTreeOut, RollbackRequest
from src.utils.trace import bind, emit, reset


class CheckpointService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos

    def _owned(self, agent_id: str, user: CurrentUser) -> dict:
        doc = self.repos.sessions.get(agent_id)
        if not doc or doc.get("deleted"):
            raise HTTPException(status_code=404, detail="Agent not found")
        if doc.get("owner_id") != user.uid:
            raise HTTPException(status_code=403, detail="Forbidden")
        return doc

    def list(self, user: CurrentUser, agent_id: str) -> list[CheckpointOut]:
        self._owned(agent_id, user)
        from src.utils.postgres_checkpointer import list_checkpoints

        rows = list_checkpoints(agent_id)
        self._trace(user, agent_id, "checkpoint.list", {"returned_count": len(rows)})
        return [CheckpointOut(**row) for row in rows]

    def tree(self, user: CurrentUser, agent_id: str) -> list[CheckpointTreeOut]:
        self._owned(agent_id, user)
        from src.utils.postgres_checkpointer import list_checkpoint_tree

        rows = list_checkpoint_tree(agent_id)
        self._trace(user, agent_id, "checkpoint.list", {"returned_count": len(rows)})
        return [CheckpointTreeOut(**row) for row in rows]

    def rollback(self, user: CurrentUser, agent_id: str, body: RollbackRequest) -> dict:
        self._owned(agent_id, user)
        self.set_rollback(agent_id, body.checkpoint_id, user=user)
        from api.services.chat_runtime_manager import get_runtime_manager

        get_runtime_manager().fence_queue(agent_id)
        self.repos.analytics.append("rollback", uid=user.uid,
                                    payload={"agent_id": agent_id, "checkpoint_id": body.checkpoint_id})
        return {"success": True, "agent_id": agent_id, "checkpoint_id": body.checkpoint_id,
                "message": "Next execution will resume from this checkpoint"}

    def set_rollback(self, agent_id: str, checkpoint_id: str, *, user: CurrentUser | None = None) -> None:
        from src.utils.postgres_checkpointer import list_checkpoints

        if checkpoint_id not in {row["checkpoint_id"] for row in list_checkpoints(agent_id)}:
            raise HTTPException(status_code=400, detail="Checkpoint does not belong to this agent")
        self.repos.sessions.set_rollback(agent_id, checkpoint_id)
        doc = self.repos.sessions.get(agent_id)
        if doc:
            self._trace(user or CurrentUser(uid=doc["owner_id"], session_id="", role="user", raw={}),
                        agent_id, "checkpoint.resume", {"checkpoint_id": checkpoint_id})

    def _trace(self, user: CurrentUser, agent_id: str, event: str, data: dict) -> None:
        active = self.repos.agents.active_execution(agent_id)
        token = bind(agent_id=agent_id, execution_id=active["execution_id"] if active else None,
                     owner_id=user.uid, session_id=user.session_id)
        try:
            emit(event, component="checkpoint_service", data=data)
        finally:
            reset(token)
