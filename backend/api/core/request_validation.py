from __future__ import annotations

from dataclasses import dataclass

from src.agent.preflight.request_contract import (
    DEFAULT_QUERY_TYPE,
    MAX_QUERY_CHARS,
    build_object_id,
    is_object_id,
    validate_request_fields,
)


@dataclass(frozen=True)
class RunStartRequest:
    request_id: str
    query: str
    query_type: str
    checkpoint_id: str | None = None


@dataclass(frozen=True)
class ValidationErrorPayload:
    code: str
    message: str
    status: int
    details: dict[str, str] | None = None


class RequestValidationError(Exception):
    def __init__(self, payload: ValidationErrorPayload) -> None:
        super().__init__(payload.message)
        self.payload = payload


def build_request_id(raw_request_id: object | None = None) -> str:
    return build_object_id(raw_request_id)


def validate_run_start_payload(
    payload: object,
    *,
    request_id: object | None,
    uid: str | None,
    session_id: str | None,
    max_query_chars: int = MAX_QUERY_CHARS,
) -> RunStartRequest:
    if not uid or not session_id:
        raise RequestValidationError(
            ValidationErrorPayload(
                code="auth_context_missing",
                message="Authenticated runtime context missing",
                status=401,
            )
        )

    raw_request_id = str(request_id or "").strip()
    if raw_request_id and not is_object_id(raw_request_id):
        raise RequestValidationError(
            ValidationErrorPayload(
                code="request_id_invalid",
                message="request_id must be a BSON ObjectId (24 lowercase hex chars)",
                status=422,
            )
        )

    resolved_request_id = build_request_id(request_id)

    if not isinstance(payload, dict):
        raise RequestValidationError(
            ValidationErrorPayload(
                code="payload_invalid",
                message="Payload must be a JSON object",
                status=422,
            )
        )

    raw_query = payload.get("query")
    if not isinstance(raw_query, str):
        raise RequestValidationError(
            ValidationErrorPayload(code="query_invalid", message="query must be a string", status=422)
        )
    normalized_query = raw_query.strip()
    query_type = str(payload.get("query_type", DEFAULT_QUERY_TYPE) or DEFAULT_QUERY_TYPE).strip().lower()
    validation_error = validate_request_fields(
        request_id=resolved_request_id,
        query=normalized_query,
        query_type=query_type,
        max_query_chars=max_query_chars,
    )
    if validation_error is not None:
        code, message, details = validation_error
        status = 413 if code == "query_too_large" else 422
        raise RequestValidationError(
            ValidationErrorPayload(
                code=code,
                message=message,
                status=status,
                details=details,
            )
        )

    checkpoint_id_raw = payload.get("checkpoint_id")
    checkpoint_id: str | None = None
    if checkpoint_id_raw is not None:
        checkpoint_id = str(checkpoint_id_raw).strip() or None

    return RunStartRequest(
        request_id=resolved_request_id,
        query=normalized_query,
        query_type=query_type,
        checkpoint_id=checkpoint_id,
    )
