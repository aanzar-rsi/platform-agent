"""Local text embeddings: sentence-transformers model, or a dependency-free
numpy hashing vectorizer, selected via settings.embed_method."""

from __future__ import annotations

import hashlib
import logging
import os
import sys
import threading
import time
from typing import Sequence

import numpy as np

from src.config import settings

logger = logging.getLogger(__name__)

_hf_model_lock = threading.Lock()
_hf_model = None


def _get_hf_model(model_id: str):
    global _hf_model
    if _hf_model is None:
        with _hf_model_lock:
            if _hf_model is None:
                started_at = time.monotonic()
                _embedding_timing("model_load", "hf", started_at, start=True)
                try:
                    _hf_model = _load_hf_model(model_id)
                except Exception:
                    _embedding_timing("model_load", "hf", started_at, error=True)
                    raise
                _embedding_timing("model_load", "hf", started_at)
    return _hf_model


def _load_hf_model(model_id: str):
    dependency_path = os.environ.get("EMBED_DEPENDENCY_PATH")
    if dependency_path and dependency_path not in sys.path:
        sys.path.insert(0, dependency_path)
    from sentence_transformers import SentenceTransformer
    from transformers.utils import logging as hf_logging

    hf_logging.disable_progress_bar()
    try:
        return SentenceTransformer(model_id, local_files_only=True)
    except Exception:
        logger.info("Embedding model %s not cached; downloading once", model_id)
        return SentenceTransformer(model_id)


def _embedding_timing(stage: str, method: str, started_at: float, *, start: bool = False,
                      error: bool = False) -> None:
    from src.utils.trace import emit, in_run

    if in_run():
        emit("memory.embedding.start" if start else "memory.embedding.error" if error else "memory.embedding.end",
             component="embeddings", status="error" if error else "ok",
             duration_ms=None if start else (time.monotonic() - started_at) * 1000,
             data={"stage": stage, "embedding_method": method})


def _embed_numpy(text: str, dimensions: int) -> list[float]:
    """Deterministic hashing bag-of-words vectorizer (no ML dependencies)."""
    vec = np.zeros(dimensions)
    for token in (text or "").lower().split():
        digest = hashlib.md5(token.encode("utf-8")).hexdigest()
        idx = int(digest, 16) % dimensions
        vec[idx] += 1.0
    norm = np.linalg.norm(vec)
    return (vec / norm if norm else vec).tolist()


def embed_text(
    text: str,
    *,
    method: str | None = None,
    model_id: str | None = None,
    dimensions: int | None = None,
) -> list[float]:
    """Embed a single string using the configured local method."""
    method = method or settings.embed_method
    if method == "hf":
        model = _get_hf_model(model_id or settings.embed_model_id)
        started_at = time.monotonic()
        _embedding_timing("encode", method, started_at, start=True)
        try:
            vector = model.encode(text or "", show_progress_bar=False).tolist()
        except Exception:
            _embedding_timing("encode", method, started_at, error=True)
            raise
        _embedding_timing("encode", method, started_at)
        return vector
    if method == "numpy":
        vector = _embed_numpy(text, dimensions or settings.embed_dimensions)
        _embedding_timing("encode", method, started_at)
        return vector
    raise ValueError(f"Unknown embed method: '{method}'. Supported: 'hf', 'numpy'")


def embed_texts(
    texts: Sequence[str],
    *,
    method: str | None = None,
    model_id: str | None = None,
    dimensions: int | None = None,
) -> list[list[float]]:
    """Embed multiple strings, batching when possible."""
    method = method or settings.embed_method
    if method == "hf":
        model = _get_hf_model(model_id or settings.embed_model_id)
        return model.encode(list(texts), show_progress_bar=False).tolist()
    if method == "numpy":
        dims = dimensions or settings.embed_dimensions
        return [_embed_numpy(t, dims) for t in texts]
    raise ValueError(f"Unknown embed method: '{method}'. Supported: 'hf', 'numpy'")


def try_embed_text(text: str, **kwargs) -> list[float] | None:
    """Soft-fail embed; returns None on any error."""
    try:
        return embed_text(text, **kwargs)
    except Exception:
        logger.warning("embed_text failed", exc_info=True)
        return None
