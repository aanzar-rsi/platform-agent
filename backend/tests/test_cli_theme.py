"""Unit tests for the CLI theme definition."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.cli.theme import REQUIRED_THEME_KEYS, THEME


class TestTheme(unittest.TestCase):
    def test_requires_named_keys_exist(self):
        missing = REQUIRED_THEME_KEYS - set(THEME)
        self.assertEqual(set(missing), set(), f"missing theme keys: {sorted(missing)}")

    def test_all_styles_are_nonempty_strings(self):
        for key, value in THEME.items():
            self.assertIsInstance(value, str, f"{key} is not a string")
            self.assertTrue(value.strip(), f"{key} has an empty style")