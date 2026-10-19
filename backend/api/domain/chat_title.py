"""Derive a short default chat title from the first human message."""

from __future__ import annotations

DEFAULT_TITLE = "New chat"
TITLE_CHAR_LIMIT = 40


def title_from_first_message(text: str | None, *, limit: int = TITLE_CHAR_LIMIT) -> str:
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return DEFAULT_TITLE
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit] + "..."


def is_placeholder_title(title: str | None) -> bool:
    """True for empty / New chat / legacy `Chat <locale datetime>` titles."""
    if not title or not title.strip():
        return True
    t = title.strip()
    if t == DEFAULT_TITLE:
        return True
    # Legacy sidebar default: "Chat 7/15/2026, 3:20:24 PM"
    if t.startswith("Chat ") and any(ch.isdigit() for ch in t):
        return True
    return False
