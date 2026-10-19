from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import create_user


class TestCreateUser(unittest.TestCase):
    def test_creates_required_rows_with_hashed_password(self):
        connection = MagicMock()
        connection.__enter__.return_value = connection
        connection.execute.return_value.fetchone.return_value = ("user-id",)

        with patch.object(create_user, "PASSWORD", "secret"), patch.object(
            create_user.psycopg, "connect", return_value=connection
        ), patch.object(create_user, "hash_password", return_value="argon2-hash") as hasher:
            user_id = create_user.create_user()

        self.assertEqual(user_id, "user-id")
        hasher.assert_called_once_with("secret")
        calls = connection.execute.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertIn("INSERT INTO users", calls[0].args[0])
        self.assertIn("INSERT INTO user_credentials", calls[1].args[0])
        self.assertEqual(calls[1].args[1], ("user-id", "argon2-hash"))
        self.assertIn("INSERT INTO user_preferences", calls[2].args[0])

    def test_rejects_placeholder_password(self):
        with patch.object(create_user, "PASSWORD", "replace-with-a-strong-password"):
            with self.assertRaisesRegex(ValueError, "placeholder PASSWORD"):
                create_user.create_user()


if __name__ == "__main__":
    unittest.main()
