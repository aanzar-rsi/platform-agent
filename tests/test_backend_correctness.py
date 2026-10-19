"""Focused runnable checks for backend checkpoint and runtime correctness."""

from __future__ import annotations

import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
for path in (str(BACKEND), str(BACKEND / "src")):
    if path not in sys.path:
        sys.path.insert(0, path)

from api.services.chat_runtime_manager import ChatRuntimeManager
from api.services.checkpoint_service import CheckpointService
from fastapi import HTTPException
from src.utils.postgres_checkpointer import PostgresSaver


class Connection:
    def __init__(self) -> None:
        self.rows: set[tuple[str, str | None, int]] = set()
        self.calls: list[tuple[str, tuple]] = []

    def execute(self, sql: str, params: tuple):
        self.calls.append((sql, params))
        self.rows.add((params[0], params[3], params[4]))


@contextmanager
def connection_context(connection: Connection):
    yield connection


class Message:
    def __init__(self, content: str, type_: str = "human") -> None:
        self.content = content
        self.type = type_


def check_message_sync() -> None:
    saver = object.__new__(PostgresSaver)
    saver.conn = object()
    saver._sync_lock = threading.Lock()
    conn = Connection()
    messages = [Message("root"), Message("fork")]
    with patch(
        "src.utils.postgres_checkpointer._internal.get_connection",
        side_effect=lambda _: connection_context(conn),
    ):
        saver._sync_messages("00000000-0000-0000-0000-000000000001", messages, "fork-cp", [messages[0]])
        saver._sync_messages("00000000-0000-0000-0000-000000000001", messages, "fork-cp", [messages[0]])
    assert len(conn.calls) == 2
    assert all("count(*)" not in sql.lower() for sql, _ in conn.calls)
    assert conn.rows == {("00000000-0000-0000-0000-000000000001", "fork-cp", 1)}


def check_atomic_admission() -> None:
    manager = ChatRuntimeManager()
    with patch("api.services.chat_runtime_manager.get_repos") as repos, patch.object(manager, "_begin_run", return_value={"ok": True}) as begin:
        repos.return_value.sessions.get.return_value = {"agent_id": "agent", "owner_id": "user", "deleted": False}
        first = manager.start_run(agent_id="agent", owner_id="user", query="one")
        second = manager.start_run(agent_id="agent", owner_id="user", query="two")
    assert first == {"ok": True}
    assert second == {"ok": False, "error": "Run already active for this chat"}
    assert begin.call_count == 1


def check_rollback_ownership() -> None:
    class Sessions:
        def __init__(self) -> None:
            self.rollback = None

        def set_rollback(self, agent_id: str, checkpoint_id: str) -> None:
            self.rollback = (agent_id, checkpoint_id)

        def get(self, agent_id: str) -> None:
            return None

    class Repos:
        sessions = Sessions()

    service = CheckpointService(Repos())
    with patch("src.utils.postgres_checkpointer.list_checkpoints", return_value=[{"checkpoint_id": "own"}]):
        service.set_rollback("agent", "own")
        assert service.repos.sessions.rollback == ("agent", "own")
        try:
            service.set_rollback("agent", "other")
        except HTTPException as exc:
            assert exc.status_code == 400
        else:
            raise AssertionError("foreign checkpoint was accepted")


if __name__ == "__main__":
    check_message_sync()
    check_atomic_admission()
    check_rollback_ownership()
    print("PASS backend correctness checks")
