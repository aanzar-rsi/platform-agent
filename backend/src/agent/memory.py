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
    """Return every execution key and description without exposing values."""
    context_entries = {
        e.get("key"): e
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
            content = entry.get("value", entry.get("result", entry))
            entry_type = entry.get("type", "unknown")
            name = entry.get("name") or entry.get("tool_name") or entry.get("agent_name") or ""
            task = entry.get("task") or ""

        visible = context_entries.get(key) or {}
        description = (
            entry.get("description") if isinstance(entry, dict) else "Stored execution output"
        ) or task or name or "Stored execution output"

        index.append(
            {
                "key": key,
                "type": entry_type,
                "name": name,
                "description": description,
                "total_tokens": (
                    int(entry["total_tokens"])
                    if isinstance(entry, dict) and entry.get("total_tokens") is not None
                    else count_content_tokens(content)
                ),
                "in_context": key in context_entries,
                "context_from": visible.get("from_token"),
                "context_to": visible.get("to_token"),
                "context_complete": visible.get("complete", False),
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
    3. Slide/trim the oldest entries until the new slice fits.
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
        excess = used + new_tokens - budget
        oldest = entries[0]
        oldest_tokens = _entry_tokens(oldest)
        if oldest_tokens <= excess:
            entries.pop(0)
            used -= oldest_tokens
            continue
        trimmed, actual_from, actual_to, total, truncated = slice_by_tokens(
            oldest.get("content"), from_token=excess,
        )
        # The content is already a window, so translate local offsets back to
        # the original execution value's token coordinates.
        original_from = int(oldest.get("from_token") or 0)
        oldest.update(
            content=trimmed,
            tokens=_token_count_of_value(trimmed),
            from_token=original_from + actual_from,
            to_token=original_from + actual_to,
            total_tokens=int(oldest.get("total_tokens") or total),
            complete=False,
            truncated=True,
        )
        used = sum(_entry_tokens(e) for e in entries)

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

    complete = actual_from == 0 and actual_to >= total_tokens and not was_truncated
    entries.append(
        {
            "key": key,
            "tokens": new_tokens,
            "from_token": actual_from,
            "to_token": actual_to,
            "total_tokens": total_tokens,
            "content": sliced,
            "complete": complete,
            "truncated": not complete,
        }
    )
    used += new_tokens

    cm["entries"] = entries
    cm["used_tokens"] = used
    # Compatibility field: whether this insertion was budget-clipped. Entry
    # completeness is authoritative because older windows may also be partial.
    cm["truncated"] = was_truncated
    return cm


def record_execution(
    execution_memory: dict[str, Any] | None,
    context_memory: dict[str, Any] | None,
    *,
    key: str,
    value: Any,
    description: str,
    entry_type: str,
    name: str = "",
    task: str = "",
    success: bool = True,
    metadata: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Store a complete execution value and expose only its FIFO context window."""
    if not key or not description.strip():
        raise ValueError("execution memory requires a key and description")
    memory = dict(execution_memory or {})
    entry = {
        "key": key,
        "type": entry_type,
        "name": name,
        "description": description.strip(),
        "task": task,
        "value": value,
        # Keep result during checkpoint migration; prompt/index readers prefer value.
        "result": value,
        "total_tokens": count_content_tokens(value),
        "success": bool(success),
        **(metadata or {}),
    }
    memory[key] = entry
    context = update_context_memory(context_memory, key=key, content=value)
    return memory, context, entry


def record_human_input(
    execution_history: list[dict[str, Any]] | None,
    execution_memory: dict[str, Any] | None,
    context_memory: dict[str, Any] | None,
    *,
    value: str,
    description: str,
    task: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Record supplemental human input before it can reach another agent call."""
    history = list(execution_history or [])
    memory = dict(execution_memory or {})
    sequence = len(history) + 1
    key = f"human_input_{sequence}"
    while key in memory:
        sequence += 1
        key = f"human_input_{sequence}"
    memory, context, entry = record_execution(
        memory, context_memory, key=key, value=value,
        description=description, entry_type="human_input", name="human_input",
        task=task, success=True,
    )
    history.append(entry)
    return history, memory, context
