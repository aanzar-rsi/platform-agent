"""Scoped KB access and admin-reviewed memory publication."""

from typing import Annotated, Literal
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api.core.deps import CurrentUser, require_user
from src.agent import kb
from src.agent.agent_core import default_policy
from api.db.repositories.preferences import PreferencesRepository
from src.agent.policy_schema import effective_memory_policy

router = APIRouter(prefix="/kb", tags=["knowledge base"], dependencies=[Depends(require_user)])


def _policy(user: CurrentUser, *, admin: bool = False) -> dict:
    ceiling = ((PreferencesRepository().get(user.uid).get("agent") or {}).get("memory_policy_ceiling"))
    policy = effective_memory_policy(default_policy().memory, ceiling)
    # TENANT remains unavailable until a server-verified tenant membership is provided.
    if admin and user.role == "admin":
        policy["write"] = ["USER", "AGENT", "TENANT"]
        policy["publish"] = ["AGENT"]
    return policy


def _handle(exc: Exception):
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise exc


class NewChunk(BaseModel):
    content: str = Field(min_length=1)
    chunk_type: Literal["resource", "user_preference", "user_details", "tenant_details",
                        "workflow", "troubleshooting", "anti_pattern"] = "workflow"
    memory_weight: float = Field(default=0.5, ge=0, le=1)
    sensitivity: Literal["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"] = "INTERNAL"


class PromotionBody(BaseModel):
    target_scope: Literal["TENANT", "AGENT"]
    proposed_content: str | None = None


class ReviewBody(BaseModel):
    approve: bool
    reason: str = ""


class ExpiryBody(BaseModel):
    expires_at: datetime | None = None
    retention_class: Literal["TRANSIENT", "STANDARD", "LONG_TERM", "LEGAL_HOLD"] | None = None


@router.get("/chunks")
def chunks(user: Annotated[CurrentUser, Depends(require_user)],
           scope: Literal["USER", "TENANT", "AGENT"] | None = None,
           limit: int = Query(default=100, ge=1, le=200)):
    try:
        return kb.list_chunks(user.uid, _policy(user), scope=scope, limit=limit)
    except (PermissionError, ValueError) as exc:
        _handle(exc)


@router.post("/chunks")
def create_chunk(body: NewChunk, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.write(user.uid, _policy(user), body.content, chunk_type=body.chunk_type,
                        sensitivity=body.sensitivity, memory_weight=body.memory_weight)
    except (PermissionError, ValueError) as exc:
        _handle(exc)


@router.get("/search")
def search(user: Annotated[CurrentUser, Depends(require_user)],
           q: str = Query(min_length=1), top_k: int = Query(default=5, ge=1, le=100)):
    try:
        return kb.search(user.uid, _policy(user), q, top_k=top_k)
    except (PermissionError, ValueError) as exc:
        _handle(exc)


@router.get("/chunks/{chunk_id}/history")
def history(chunk_id: str, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.history(user.uid, _policy(user), chunk_id)
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)


@router.post("/chunks/{chunk_id}/versions")
def append_version(chunk_id: str, body: NewChunk, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        old = kb.history(user.uid, _policy(user), chunk_id)
        if old["scope"] != "USER" or old["chunk_type"] != body.chunk_type:
            raise PermissionError("memory_scope_denied")
        return kb.write(user.uid, _policy(user), body.content, chunk_id=chunk_id,
                        chunk_type=body.chunk_type, memory_weight=body.memory_weight,
                        sensitivity=body.sensitivity)
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)


@router.post("/chunks/{chunk_id}/promotions")
def request_promotion(chunk_id: str, body: PromotionBody,
                      user: Annotated[CurrentUser, Depends(require_user)],
                      idempotency_key: Annotated[str, Header(min_length=1, max_length=160)]):
    try:
        return kb.request_promotion(user.uid, _policy(user), chunk_id, body.target_scope,
                                    idempotency_key=idempotency_key, proposed_content=body.proposed_content)
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)


@router.get("/promotions")
def promotions(user: Annotated[CurrentUser, Depends(require_user)]):
    return kb.promotions(user.uid, user.role)


@router.get("/promotions/{request_id}")
def promotion_detail(request_id: str, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.promotion_detail(user.uid, user.role, request_id)
    except (PermissionError, KeyError) as exc:
        _handle(exc)


@router.get("/audit")
def audit(user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.audit_log(user.uid, user.role)
    except PermissionError as exc:
        _handle(exc)


@router.post("/promotions/{request_id}/review")
def review(request_id: str, body: ReviewBody, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.review_promotion(user.uid, user.role, request_id, approve=body.approve,
                                   policy=_policy(user, admin=True), reason=body.reason)
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)


@router.post("/promotions/{request_id}/cancel")
def cancel(request_id: str, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.cancel_promotion(user.uid, user.role, request_id)
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)


@router.post("/chunks/{chunk_id}/revoke")
def revoke(chunk_id: str, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.revoke(user.uid, user.role, chunk_id, _policy(user, admin=True))
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)


@router.post("/chunks/{chunk_id}/demote")
def demote(chunk_id: str, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.demote(user.uid, user.role, chunk_id, _policy(user, admin=True))
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)


@router.post("/chunks/{chunk_id}/expiry")
def expiry(chunk_id: str, body: ExpiryBody, user: Annotated[CurrentUser, Depends(require_user)]):
    try:
        return kb.set_expiry(user.uid, user.role, chunk_id, _policy(user, admin=True), body.expires_at,
                             retention_class=body.retention_class)
    except (PermissionError, ValueError, KeyError) as exc:
        _handle(exc)
