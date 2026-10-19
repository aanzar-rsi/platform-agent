from __future__ import annotations

from pathlib import Path

from api.core.config import get_settings


def data_root() -> Path:
    root = get_settings().data_root
    root.mkdir(parents=True, exist_ok=True)
    return root


def analytics_dir() -> Path:
    path = data_root() / "analytics"
    path.mkdir(parents=True, exist_ok=True)
    return path


def analytics_events_file() -> Path:
    return analytics_dir() / "events.jsonl"


def experience_dir() -> Path:
    path = data_root() / "experience"
    path.mkdir(parents=True, exist_ok=True)
    return path
