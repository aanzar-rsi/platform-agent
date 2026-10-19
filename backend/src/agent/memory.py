"""Context memory helpers — FIFO budget, token slicing, execution_memory index.

Serialization for counting, slicing, and agent prompts uses TOON (via `toons`)
instead of JSON for lower token cost.
"""

from __future__ import annotations

from typing import Any

import toons

from src.models.llm_client import count_tokens

CONTEXT_MEMORY_BUDGET = 5000
_CHARS_PER_TOKEN = 4


def empty_context_memory(budget: int = CONTEXT_MEMORY_BUDGET) -> dict[str, Any]:
    return {
        "budget_tokens": budget,
        "used_tokens": 0,
        "truncated": False,
        "entries": [],
    }


def serialize_content(content: Any) -> str:
    """Encode content as TOON text for token counting / window slicing."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        return toons.dumps(content)
    except Exception:
        return str(content)


def count_content_tokens(content: Any) -> int:
    text = serialize_content(content)
    if not text:
        return 0
    return count_tokens(text)["input"]


def _token_count_of_value(value: Any) -> int:
    if value is None or value == "":
        return 0
    return count_content_tokens(value)


def slice_by_tokens(
    content: Any,
    from_token: int = 0,
    to_token: int | None = None,
    *,
    budget: int | None = None,
) -> tuple[Any, int, int, int, bool]:
    """
    Slice content by approximate token offsets.

    Returns (slice_value, actual_from, actual_to, total_tokens, was_truncated_to_budget).

    When the full structured payload fits the requested window and budget,
    returns the original structured object (not a string) so prompt TOON
    encoding can keep tabular nesting. Partial / budget-clipped windows
    return a TOON text slice.
    """
    text = serialize_content(content)
    total_tokens = count_content_tokens(text)
    if total_tokens == 0:
        empty = "" if isinstance(content, str) or content is None else content
        return empty, 0, 0, 0, False

    start = max(0, int(from_token))
    end = total_tokens if to_token is None else max(start, int(to_token))
    end = min(end, total_tokens)

    full_window = start == 0 and end == total_tokens

    if full_window and (budget is None or total_tokens <= budget):
        if not isinstance(content, str) and content is not None:
            return content, 0, total_tokens, total_tokens, False
        return text, 0, total_tokens, total_tokens, False

    char_start = start * _CHARS_PER_TOKEN
    char_end = end * _CHARS_PER_TOKEN
    sliced: Any = text[char_start:char_end]

    was_truncated = False
    if budget is not None and count_content_tokens(sliced) > budget:
        sliced = sliced[: budget * _CHARS_PER_TOKEN]
        was_truncated = True

    actual_tokens = count_content_tokens(sliced) if sliced else 0
    actual_to = start + actual_tokens
    return sliced, start, actual_to, total_tokens, was_truncated


def _entry_tokens(entry: dict[str, Any]) -> int:
    return int(entry.get("tokens") or 0)


def build_execution_memory_index(
    execution_memory: dict[str, Any],
    context_memory: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """keys + short meta: name, task, total_tokens, in_context."""
    in_context_keys = {
        e.get("key")
        for e in (context_memory or {}).get("entries", [])
        if e.get("key")
    }
    index: list[dict[str, Any]] = []
    for key, entry in (execution_memory or {}).items():
        if not isinstance(entry, dict):
            content = entry
            name = ""
            task = ""
            entry_type = "unknown"
        else:
            content = entry.get("result", entry)
            entry_type = entry.get("type", "unknown")
            name = entry.get("tool_name") or entry.get("agent_name") or ""
            task = entry.get("task") or ""

        index.append(
            {
                "key": key,
                "type": entry_type,
                "name": name,
                "task": task,
                "total_tokens": count_content_tokens(content),
                "in_context": key in in_context_keys,
            }
        )
    return index


def slim_execution_history(
    execution_history: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """History rows without result bodies, for agent prompts."""
    slim: list[dict[str, Any]] = []
    for entry in execution_history or []:
        if not isinstance(entry, dict):
            continue
        result = entry.get("result")
        slim.append(
            {
                "type": entry.get("type"),
                "name": entry.get("tool_name") or entry.get("agent_name") or "",
                "task": entry.get("task") or "",
                "key": entry.get("key") or "",
                "tokens": count_content_tokens(result) if result is not None else 0,
                "success": entry.get("success", True),
            }
        )
    return slim


def update_context_memory(
    context_memory: dict[str, Any] | None,
    *,
    key: str,
    content: Any,
    from_token: int = 0,
    to_token: int | None = None,
    budget: int = CONTEXT_MEMORY_BUDGET,
) -> dict[str, Any]:
    """
    Insert/replace a sliced window for `key` under a FIFO token budget.

    1. Slice content to [from_token, to_token); clip to budget if needed.
    2. Remove any existing entries for `key`.
    3. Evict oldest entries until the new slice fits.
    4. Append the new entry (structured when possible, else TOON text).
    """
    cm = dict(context_memory) if context_memory else empty_context_memory(budget)
    cm["budget_tokens"] = budget
    entries: list[dict[str, Any]] = [
        dict(e) for e in cm.get("entries", []) if e.get("key") != key
    ]

    sliced, actual_from, actual_to, total_tokens, was_truncated = slice_by_tokens(
        content,
        from_token=from_token,
        to_token=to_token,
        budget=budget,
    )
    new_tokens = _token_count_of_value(sliced)

    used = sum(_entry_tokens(e) for e in entries)
    while entries and used + new_tokens > budget:
        evicted = entries.pop(0)
        used -= _entry_tokens(evicted)

    if new_tokens > budget:
        sliced, actual_from, actual_to, total_tokens, was_truncated = slice_by_tokens(
            content,
            from_token=from_token,
            to_token=to_token,
            budget=budget,
        )
        new_tokens = _token_count_of_value(sliced)
        entries = []
        used = 0

    entries.append(
        {
            "key": key,
            "tokens": new_tokens,
            "from_token": actual_from,
            "to_token": actual_to,
            "total_tokens": total_tokens,
            "content": sliced,
        }
    )
    used += new_tokens

    cm["entries"] = entries
    cm["used_tokens"] = used
    cm["truncated"] = was_truncated
    return cm