from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from api.core.deps import CurrentUser, Repositories
from api.db.postgres import fetch_all
from api.domain.chat import (
    ChatCreateRequest,
    ChatDetailOut,
    ChatOut,
    ChatUpdateRequest,
    ExtractionDecisionRequest,
    PolicyUpdateRequest,
)
from api.domain.chat_title import is_placeholder_title, title_from_first_message
from api.services.preload_service import PreloadService
from src.agent.policy_schema import effective_memory_policy, normalize_armory_policy, normalize_memory_policy


def _first_human_content(messages: list[dict[str, Any]] | None) -> str | None:
    for message in messages or []:
        if message.get("role") in ("human", "user") and isinstance(message.get("content"), str):
            if message["content"].strip():
                return message["content"]
    return None


def _message_role(message: Any) -> str:
    return {"human": "user", "ai": "assistant"}.get(
        getattr(message, "type", None), getattr(message, "type", "unknown")
    )


def _message_content(message: Any) -> str:
    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content)


def _ui_messages(messages: list[Any], mirrored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    visible: list[dict[str, Any]] = []
    pending_steps: list[dict[str, Any]] = []
    for index, message in enumerate(messages):
        extras = getattr(message, "additional_kwargs", None) or {}
        step = extras.get("ui_step")
        if isinstance(step, dict):
            pending_steps.append(step)
        if extras.get("ui_hidden"):
            continue
        row = mirrored[index] if index < len(mirrored) else {}
        item = {"role": _message_role(message), "content": _message_content(message),
                "checkpoint_id": row.get("checkpoint_id"), "created_at": row.get("created_at")}
        if item["role"] == "assistant" and pending_steps:
            item["metadata"] = {"steps": pending_steps}
            pending_steps = []
        visible.append(item)
    return visible


def _load_messages(agent_id: str) -> list[dict[str, Any]]:
    from src.utils.postgres_checkpointer import active_checkpoint_path, get_thread_state, reconcile_thread_messages

    rows = fetch_all("SELECT role, content, checkpoint_id, created_at FROM messages WHERE agent_id = %s ORDER BY created_at", (agent_id,))
    active_path = active_checkpoint_path(agent_id)
    mirrored = [{"role": row["role"], "content": row["content"], "checkpoint_id": row.get("checkpoint_id"),
                 "created_at": row["created_at"].isoformat() if row.get("created_at") else None}
                for row in rows if active_path is None or not row.get("checkpoint_id") or row["checkpoint_id"] in active_path]
    canonical = (get_thread_state(agent_id) or {}).get("messages") or []
    if canonical and [(r["role"], r["content"]) for r in mirrored] != [(_message_role(m), _message_content(m)) for m in canonical]:
        reconcile_thread_messages(agent_id)
    return _ui_messages(canonical, mirrored) if canonical else mirrored


def _load_execution_history(agent_id: str) -> list[dict[str, Any]]:
    from src.utils.postgres_checkpointer import get_thread_state

    history = (get_thread_state(agent_id) or {}).get("execution_history") or []
    return history if isinstance(history, list) else []


class ChatService:
    def __init__(self, repos: Repositories) -> None:
        self.repos = repos
        self.preload = PreloadService(repos)

    def _owned(self, agent_id: str, user: CurrentUser) -> dict[str, Any]:
        doc = self.repos.sessions.get(agent_id)
        if not doc or doc.get("deleted"):
            raise HTTPException(status_code=404, detail="Agent not found")
        if doc.get("owner_id") != user.uid:
            raise HTTPException(status_code=403, detail="Forbidden")
        return doc

    def create(self, user: CurrentUser, body: ChatCreateRequest) -> ChatOut:
        doc = self.repos.sessions.create(owner_id=user.uid, session_id=user.session_id,
                                         title=body.title,
                                         preloaded_context=self.preload.build(user.uid))
        self.repos.analytics.append("agent_create", uid=user.uid, payload={"agent_id": doc["agent_id"]})
        return ChatOut.model_validate(doc)

    def list(self, user: CurrentUser) -> list[ChatOut]:
        return [ChatOut.model_validate(row) for row in self.repos.sessions.list_for_user(user.uid)]

    def get(self, user: CurrentUser, agent_id: str) -> ChatDetailOut:
        doc = self._owned(agent_id, user)
        messages = _load_messages(agent_id)
        history = _load_execution_history(agent_id) if doc.get("last_activity_at") else []
        if is_placeholder_title(doc.get("title")):
            first = _first_human_content(messages)
            if first:
                doc = self.repos.sessions.update(agent_id, title=title_from_first_message(first)) or doc
        return ChatDetailOut(**ChatOut.model_validate(doc).model_dump(), messages=messages,
                             execution_history=history, preloaded_context=doc.get("preloaded_context") or {})

    def update(self, user: CurrentUser, agent_id: str, body: ChatUpdateRequest) -> ChatOut:
        self._owned(agent_id, user)
        doc = self.repos.sessions.update(agent_id, **body.model_dump(exclude_none=True))
        if not doc:
            raise HTTPException(status_code=404, detail="Agent not found")
        return ChatOut.model_validate(doc)

    def get_policy(self, user: CurrentUser, agent_id: str) -> dict:
        self._owned(agent_id, user)
        from src.agent.agent_core import AgentCore

        record = self.repos.agents.for_agent(agent_id, user.uid, user.session_id)
        agent = AgentCore(record, self.repos.agents)
        user_ceiling = ((self.repos.preferences.get(user.uid).get("agent") or {}).get("memory_policy_ceiling"))
        policy = agent.policy.as_dict()
        policy["memory"] = effective_memory_policy(policy.get("memory") or {}, user_ceiling)
        ceiling = dict(record.get("policy_ceiling") or record["policy"])
        ceiling["armory"] = normalize_armory_policy(ceiling.get("armory") or {})
        ceiling["memory"] = normalize_memory_policy(ceiling.get("memory") or {})
        policy["armory"] = normalize_armory_policy(policy.get("armory") or {})
        return {"policy": policy, "version": agent.policy.version, "ceiling": ceiling}

    def update_policy(self, user: CurrentUser, agent_id: str, body: PolicyUpdateRequest) -> dict:
        self._owned(agent_id, user)
        if (body.armory is None) == (body.memory is None):
            raise HTTPException(status_code=422, detail="Update exactly one policy section")
        from src.agent.agent_core import AgentCore

        agent = AgentCore(self.repos.agents.for_agent(agent_id, user.uid, user.session_id), self.repos.agents)
        try:
            if body.armory is not None:
                agent.update_armory_policy(body.armory, uid=user.uid, expected_version=body.expected_version)
            else:
                agent.update_memory_policy(body.memory, uid=user.uid, expected_version=body.expected_version)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=409 if str(exc) == "policy_conflict" else 422,
                                detail=str(exc)) from exc
        user_ceiling = ((self.repos.preferences.get(user.uid).get("agent") or {}).get("memory_policy_ceiling"))
        policy = agent.policy.as_dict()
        policy["memory"] = effective_memory_policy(policy.get("memory") or {}, user_ceiling)
        policy["armory"] = normalize_armory_policy(policy.get("armory") or {})
        ceiling = dict(agent.record.get("policy_ceiling") or agent.record["policy"])
        ceiling["armory"] = normalize_armory_policy(ceiling.get("armory") or {})
        ceiling["memory"] = normalize_memory_policy(ceiling.get("memory") or {})
        return {"policy": policy, "version": agent.policy.version, "ceiling": ceiling}

    def list_extraction_requests(self, user: CurrentUser, agent_id: str, state: str | None = None) -> list[dict]:
        self._owned(agent_id, user)
        rows = self.repos.memory_extractions.list_for_user(user.uid, state=state)
        return [row for row in rows if str(row.get("agent_id")) == agent_id]

    def review_extraction_request(
        self,
        user: CurrentUser,
        agent_id: str,
        request_id: str,
        body: ExtractionDecisionRequest,
    ) -> dict:
        self._owned(agent_id, user)
        try:
            row = self.repos.memory_extractions.decide(
                owner_id=user.uid,
                request_id=request_id,
                approve=body.approve,
                reason=body.reason,
            )
        except PermissionError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        if str(row.get("agent_id")) != agent_id:
            raise HTTPException(status_code=404, detail="extraction_request_not_found")
        return row

    def delete(self, user: CurrentUser, agent_id: str) -> dict:
        self._owned(agent_id, user)
        from api.services.chat_runtime_manager import get_runtime_manager

        get_runtime_manager().stop_run(agent_id)
        self.repos.sessions.soft_delete(agent_id)
        return {"success": True, "agent_id": agent_id}
