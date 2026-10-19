"""Output security gate for executor node updates before re-planning."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage


def _sanitize_messages(messages: list) -> list:
    out = []
    for msg in messages:
        if isinstance(msg, (AIMessage, HumanMessage)):
            out.append(msg)
            continue
        text = str(getattr(msg, "content", msg))
        out.append(AIMessage(content=text, additional_kwargs={"ui_hidden": True}))
    return out


def _sanitize_history(history: list[dict]) -> list[dict]:
    if not isinstance(history, list):
        return []
    sanitized = []
    for entry in history:
        if isinstance(entry, dict):
            sanitized.append(entry)
    return sanitized


def _sanitize_memory(execution_memory: dict) -> dict:
    return execution_memory if isinstance(execution_memory, dict) else {}


def output_security_gate_node(state: dict, config=None) -> dict:
    update: dict = {}
    if "messages" in state:
        update["messages"] = _sanitize_messages(list(state.get("messages") or []))
    if "execution_history" in state:
        update["execution_history"] = _sanitize_history(list(state.get("execution_history") or []))
    if "execution_memory" in state:
        update["execution_memory"] = _sanitize_memory(state.get("execution_memory") or {})
    if "next_step" in state and not isinstance(state.get("next_step"), dict):
        update["next_step"] = {}
    if "context_memory" in state and not isinstance(state.get("context_memory"), dict):
        update["context_memory"] = {}
    return update
