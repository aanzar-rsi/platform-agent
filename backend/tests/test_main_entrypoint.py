"""Tests for the main.py boot dispatch (API server vs interactive agent CLI)."""

from __future__ import annotations

import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main


class TestDevPyRemoved(unittest.TestCase):
    def test_dev_py_no_longer_exists(self):
        self.assertFalse((ROOT / "dev.py").exists())


class TestMainDispatch(unittest.TestCase):
    def _fake_module(self, name: str, **attrs) -> types.ModuleType:
        module = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(module, key, value)
        return module

    def test_default_invocation_starts_api_server(self):
        fake_run = MagicMock()
        fake_api_main = self._fake_module("api.main", run=fake_run)
        with patch.dict(sys.modules, {"api.main": fake_api_main}):
            with patch.object(sys, "argv", ["main.py"]):
                main.main()
        fake_run.assert_called_once()

    def test_cli_flag_starts_agent_cli(self):
        fake_run_cli = MagicMock()
        fake_graph = self._fake_module("src.agent.graph", run_cli=fake_run_cli)
        with patch.dict(
            sys.modules,
            {"src.agent.graph": fake_graph},
        ):
            with patch.object(sys, "argv", ["main.py", "--cli"]):
                main.main()
        fake_run_cli.assert_called_once()


if __name__ == "__main__":
    unittest.main()
