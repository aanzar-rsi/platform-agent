"""The HF embedding backend must load quietly: no 'Loading weights' tqdm bar,
no Hub round-trip (which returns the 'set a HF_TOKEN' warning) once cached.

sentence_transformers/transformers are faked in sys.modules, so this runs
without torch installed.
"""

from __future__ import annotations

import os
import sys
import types
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

os.environ["EVA_SKIP_VENV_REEXEC"] = "1"

from src.models import embeddings


class _FakeEncoded(list):
    def tolist(self):
        return list(self)


class _FakeModel:
    def __init__(self, model_id, **kwargs):
        self.model_id = model_id
        self.kwargs = kwargs
        self.encode_calls = []

    def encode(self, text, **kwargs):
        self.encode_calls.append(kwargs)
        return _FakeEncoded([0.1, 0.2])


def _install_fakes(cached: bool) -> dict:
    """Fake sentence_transformers + transformers.utils.logging. Returns a record."""
    record = {"progress_disabled": False, "constructed": [], "model": None}

    def SentenceTransformer(model_id, **kwargs):
        record["constructed"].append(kwargs)
        if kwargs.get("local_files_only") and not cached:
            raise OSError("model not found locally")
        model = _FakeModel(model_id, **kwargs)
        record["model"] = model
        return model

    st = types.ModuleType("sentence_transformers")
    st.SentenceTransformer = SentenceTransformer

    hf_logging = types.ModuleType("transformers.utils.logging")
    hf_logging.disable_progress_bar = lambda: record.__setitem__("progress_disabled", True)
    utils = types.ModuleType("transformers.utils")
    utils.logging = hf_logging
    transformers = types.ModuleType("transformers")
    transformers.utils = utils

    sys.modules["sentence_transformers"] = st
    sys.modules["transformers"] = transformers
    sys.modules["transformers.utils"] = utils
    sys.modules["transformers.utils.logging"] = hf_logging
    return record


class HfLoadIsQuiet(unittest.TestCase):
    def setUp(self):
        embeddings._hf_model = None
        self._saved = {k: sys.modules.get(k) for k in (
            "sentence_transformers",
            "transformers",
            "transformers.utils",
            "transformers.utils.logging",
        )}

    def tearDown(self):
        embeddings._hf_model = None
        for name, mod in self._saved.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod

    def test_cached_model_loads_offline_with_no_progress_bar(self):
        record = _install_fakes(cached=True)
        embeddings._get_hf_model("some/model")

        self.assertTrue(record["progress_disabled"], "tqdm 'Loading weights' bar not disabled")
        self.assertEqual(record["constructed"], [{"local_files_only": True}])

    def test_uncached_model_falls_back_to_download(self):
        record = _install_fakes(cached=False)
        embeddings._get_hf_model("some/model")

        self.assertEqual(
            record["constructed"],
            [{"local_files_only": True}, {}],
            "should retry without local_files_only when the model is not cached",
        )

    def test_encode_never_shows_a_progress_bar(self):
        record = _install_fakes(cached=True)
        embeddings.embed_text("hello", method="hf", model_id="some/model")
        embeddings.embed_texts(["a", "b"], method="hf", model_id="some/model")

        self.assertEqual(
            record["model"].encode_calls,
            [{"show_progress_bar": False}, {"show_progress_bar": False}],
        )


if __name__ == "__main__":
    unittest.main()
