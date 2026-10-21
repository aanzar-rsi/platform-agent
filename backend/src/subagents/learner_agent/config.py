"""Learner / experience-system configuration."""

from __future__ import annotations

import os
from pathlib import Path

# src/subagents/learner_agent/config.py → client2.0/
_CLIENT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = _CLIENT_ROOT / "data"
EXPERIENCE_DIR = DATA_ROOT / "experience"
CHUNKS_JSONL = EXPERIENCE_DIR / "chunks.jsonl"
VECTORS_JSON = EXPERIENCE_DIR / "vectors.json"
INDEX_META_JSON = EXPERIENCE_DIR / "index_meta.json"

IDLE_SECONDS = int(os.environ.get("EVA_EXPERIENCE_IDLE_SECONDS", "120"))
WATCHER_POLL_SECONDS = float(os.environ.get("EVA_EXPERIENCE_POLL_SECONDS", "20"))
TOP_K = int(os.environ.get("EVA_EXPERIENCE_TOP_K", "5"))

EXPERIENCE_ENABLED = os.environ.get("EVA_EXPERIENCE_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
    "on",
)


def ensure_experience_dir() -> Path:
    EXPERIENCE_DIR.mkdir(parents=True, exist_ok=True)
    return EXPERIENCE_DIR