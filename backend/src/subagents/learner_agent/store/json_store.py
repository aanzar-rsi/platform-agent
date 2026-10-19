"""Plain-text JSONL mirror of experience chunks for human review."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

from src.subagents.learner_agent.config import CHUNKS_JSONL, ensure_experience_dir

logger = logging.getLogger(__name__)
_lock = threading.RLock()


def append_chunks(chunks: list[dict[str, Any]]) -> int:
    if not chunks:
        return 0
    ensure_experience_dir()
    with _lock:
        with CHUNKS_JSONL.open("a", encoding="utf-8") as fh:
            for chunk in chunks:
                fh.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    return len(chunks)


def read_all_chunks() -> list[dict[str, Any]]:
    if not CHUNKS_JSONL.exists():
        return []
    out: list[dict[str, Any]] = []
    with _lock:
        try:
            text = CHUNKS_JSONL.read_text(encoding="utf-8")
        except Exception:
            logger.warning("Failed reading chunks.jsonl", exc_info=True)
            return []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                out.append(row)
        except json.JSONDecodeError:
            logger.warning("Skipping corrupt chunks.jsonl line")
    return out


def get_chunk_by_id(chunk_id: str) -> dict[str, Any] | None:
    for row in read_all_chunks():
        if row.get("id") == chunk_id:
            return row
    return None