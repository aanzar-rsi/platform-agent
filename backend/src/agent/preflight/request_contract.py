from __future__ import annotations

import re
import secrets

DEFAULT_QUERY_TYPE = "chat"
MAX_QUERY_CHARS = 10_000
OBJECT_ID_RE = re.compile(r"^[0-9a-f]{24}$")


def is_object_id(value: object) -> bool:
    """Check whether a value is a lower-case BSON ObjectId string."""

    text = str(value or "").strip().lower()
    return bool(OBJECT_ID_RE.fullmatch(text))


def build_object_id(raw_request_id: object | None = None) -> str:
    """Preserve a valid request ID or generate a new ObjectId string."""

    text = str(raw_request_id or "").strip().lower()
    if OBJECT_ID_RE.fullmatch(text):
        return text
    return secrets.token_hex(12)


def validate_request_fields(
    *,
    request_id: str,
    query: str,
    query_type: str,
    max_query_chars: int = MAX_QUERY_CHARS,
) -> tuple[str, str, dict[str, str] | None] | None:
    """Validate the normalized request fields shared by API and graph gates."""

    if not OBJECT_ID_RE.fullmatch(str(request_id or "").strip().lower()):
        return (
            "request_id_invalid",
            "request_id must be a BSON ObjectId (24 lowercase hex chars)",
            None,
        )
    if not str(query or "").strip():
        return ("query_required", "query required", None)
    if len(str(query or "").strip()) > int(max_query_chars):
        return (
            "query_too_large",
            f"query exceeds max length ({int(max_query_chars)})",
            {"max_query_chars": str(int(max_query_chars))},
        )
    if str(query_type or DEFAULT_QUERY_TYPE).strip().lower() != DEFAULT_QUERY_TYPE:
        return (
            "query_type_invalid",
            f"Unsupported query_type: {str(query_type or DEFAULT_QUERY_TYPE).strip().lower()}",
            {"allowed": DEFAULT_QUERY_TYPE},
        )
    return None
