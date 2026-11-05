from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.exceptions import HTTPException

from api.core.request_validation import RequestValidationError, validate_run_start_payload
from api.core.deps import get_repos, user_from_token
from api.core.security import utc_now_iso
from api.services.chat_runtime_manager import get_runtime_manager
from api.services.checkpoint_service import CheckpointService
from api.ws import protocol as proto
from src.utils.trace import bind, emit, reset

logger = logging.getLogger(__name__)

router = APIRouter()


async def _reject(websocket: WebSocket, code: int, reason: str) -> None:
    """Accept then close so clients always get a proper close frame."""
    try:
        await websocket.accept()
    except Exception:
        return
    try:
        await websocket.close(code=code, reason=reason[:120])
    except Exception:
        pass


@router.websocket("/ws/agents/{agent_id}")
async def agent_ws(websocket: WebSocket, agent_id: str) -> None:
    token = websocket.query_params.get("token")
    after_seq_raw = websocket.query_params.get("after_seq", "0")
    execution_id = websocket.query_params.get("execution_id")
    try:
        after_seq = int(after_seq_raw)
    except ValueError:
        after_seq = 0

    if not token:
        await _reject(websocket, 4401, "Missing token")
        return

    repos = get_repos()
    try:
        user = user_from_token(token, repos)
    except HTTPException as exc:
        await _reject(websocket, 4401, str(exc.detail))
        return
    except Exception as exc:
        await _reject(websocket, 4401, str(exc))
        return

    agent = repos.sessions.get(agent_id)
    if not agent or agent.get("deleted"):
        await _reject(websocket, 4404, "Agent not found")
        return
    if agent.get("owner_id") != user.uid:
        await _reject(websocket, 4403, "Forbidden")
        return

    repos.agents.for_agent(agent_id, user.uid, user.session_id)
    await websocket.accept()
    trace_token = bind(agent_id=agent_id, owner_id=user.uid, session_id=user.session_id)
    started = time.monotonic()
    emit("session.websocket.attach", component="websocket")
    mgr = get_runtime_manager()
    detach_error = None
    try:
        await mgr.attach(agent_id, user.uid, websocket, execution_id=execution_id, after_seq=after_seq)
    except Exception as exc:
        logger.exception("WS attach failed")
        try:
            await websocket.close(code=1011, reason=str(exc)[:120])
        except Exception:
            pass
        emit("session.websocket.detach", status="error", error=exc, component="websocket",
             duration_ms=(time.monotonic() - started) * 1000)
        reset(trace_token)
        return

    try:
        while True:
            raw = await websocket.receive_json()
            if not isinstance(raw, dict):
                mgr.enqueue_control(
                    agent_id, proto.ERROR, {"message": "Message must be a JSON object"}
                )
                continue
            await _handle_client_message(mgr, repos, user.uid, agent_id, raw, websocket,
                                         session_id=user.session_id)
    except WebSocketDisconnect:
        logger.info("WS disconnected agent_id=%s", agent_id)
    except Exception as exc:
        logger.exception("WS error agent_id=%s", agent_id)
        detach_error = exc
    finally:
        await mgr.detach(agent_id, websocket)
        emit("session.websocket.detach", status="error" if detach_error else "ok", error=detach_error,
             component="websocket",
             duration_ms=(time.monotonic() - started) * 1000)
        reset(trace_token)


async def _handle_client_message(
    mgr,
    repos,
    uid: str,
    agent_id: str,
    raw: dict[str, Any],
    websocket: WebSocket,
    session_id: str | None = None,
) -> None:
    async def _send_error(message: str) -> None:
        await websocket.send_json(
            {
                "v": 1,
                "type": proto.ERROR,
                "id": "error",
                "agent_id": agent_id,
                "seq": None,
                "ts": utc_now_iso(),
                "payload": {"message": message},
            }
        )

    type_ = raw.get("type")
    payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}

    if type_ == proto.CLIENT_PING:
        await websocket.send_json(
            {
                "v": 1,
                "type": proto.PONG,
                "id": raw.get("id") or "pong",
                "agent_id": agent_id,
                "seq": None,
                "ts": utc_now_iso(),
                "payload": {},
            }
        )
        return

    if type_ == proto.CLIENT_RUN_START:
        try:
            req = validate_run_start_payload(
                payload,
                request_id=raw.get("id"),
                uid=uid,
                session_id=session_id,
            )
        except RequestValidationError as exc:
            details = exc.payload.details or {}
            detail_text = ", ".join(f"{key}={value}" for key, value in details.items())
            msg = f"[{exc.payload.code}] {exc.payload.message}"
            if detail_text:
                msg = f"{msg} ({detail_text})"
            await _send_error(msg)
            return
        result = mgr.start_run(
            agent_id=agent_id,
            owner_id=uid,
            query=req.query,
            checkpoint_id=req.checkpoint_id,
            session_id=session_id,
            request_id=req.request_id,
            query_type=req.query_type,
        )
        if not result.get("ok"):
            await _send_error(str(result.get("error") or "run_start_failed"))
        return

    if type_ == proto.CLIENT_RUN_STOP:
        result = mgr.stop_run(agent_id)
        if not result.get("ok"):
            await _send_error(str(result.get("error") or "run_stop_failed"))
        return

    if type_ == proto.CLIENT_RUN_PAUSE:
        result = mgr.pause_run(agent_id)
        if not result.get("ok"):
            await _send_error(str(result.get("error") or "run_pause_failed"))
        return

    if type_ == proto.CLIENT_RUN_RESUME:
        result = await asyncio.to_thread(
            mgr.resume_run, agent_id=agent_id, owner_id=uid, resume_value=payload.get("value"),
            session_id=session_id,
        )
        if not result.get("ok"):
            await _send_error(str(result.get("error") or "run_resume_failed"))
        return

    if type_ == proto.CLIENT_RUN_ROLLBACK:
        checkpoint_id = payload.get("checkpoint_id")
        if not checkpoint_id:
            await _send_error("checkpoint_id required")
            return
        try:
            CheckpointService(repos).set_rollback(agent_id, checkpoint_id)
        except HTTPException as exc:
            await _send_error(str(exc.detail))
            return
        mgr.enqueue_control(
            agent_id,
            proto.CHECKPOINT_CREATED,
            {"checkpoint_id": checkpoint_id, "rollback": True},
        )
        return

    await _send_error(f"Unknown type: {type_}")
