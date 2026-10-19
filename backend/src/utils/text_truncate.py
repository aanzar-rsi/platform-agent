"""Shared stringify + truncate helpers for AIMessage previews."""

from __future__ import annotations

import json
from typing import Any

DEFAULT_AIMESSAGE_PREVIEW_LIMIT = 2000


def stringify_for_preview(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


def truncate_text(text: str, limit: int = DEFAULT_AIMESSAGE_PREVIEW_LIMIT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def truncate_for_aimessage(
    value: Any, limit: int = DEFAULT_AIMESSAGE_PREVIEW_LIMIT
) -> str:
    return truncate_text(stringify_for_preview(value), limit)