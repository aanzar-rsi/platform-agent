"""Background idle watcher: learn from chats idle for IDLE_SECONDS."""

from __future__ import annotations

import asyncio
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Callable

from src.subagents.learner_agent.config import (
    EXPERIENCE_ENABLED,
    IDLE_SECONDS,
    WATCHER_POLL_SECONDS,
)
from src.subagents.learner_agent.graph import learn_session

logger = logging.getLogger(__name__)
_active_chats: set[str] = set()
_active_chats_lock = threading.Lock()


def _parse_iso(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_run_active(agent_id: str) -> bool:
    with _active_chats_lock:
        if agent_id in _active_chats:
            return True
    try:
        from api.services.chat_runtime_manager import get_runtime_manager

        mgr = get_runtime_manager()
        with mgr._lock:
            rt = mgr._runtimes.get(agent_id)
            return bool(rt and rt.run_active)
    except Exception:
        return False


def set_chat_active(agent_id: str, active: bool) -> None:
    """Expose synchronous CLI turns to the background idle watcher."""
    with _active_chats_lock:
        if active:
            _active_chats.add(agent_id)
        else:
            _active_chats.discard(agent_id)


def _mark_session(agent_id: str, **fields: Any) -> None:
    try:
        from api.db.repositories import SessionRepository

        SessionRepository().update(agent_id, **fields)
    except Exception:
        logger.warning("Failed updating agent after learn agent_id=%s", agent_id, exc_info=True)


def sessions_ready_to_learn(
    sessions: list[dict[str, Any]],
    *,
    idle_seconds: int = IDLE_SECONDS,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Pure helper: sessions idle long enough to consider for learning.

    Per-branch learn state lives in `agent_branch_learn_state` (keyed by
    leaf checkpoint); every idle agent is re-checked, and
    `process_idle_sessions` skips branches that already have a recorded leaf.
    """
    now = now or datetime.now(timezone.utc)
    ready: list[dict[str, Any]] = []
    for row in sessions:
        if row.get("deleted"):
            continue
        last_activity = _parse_iso(row.get("last_activity_at"))
        if last_activity is None:
            continue
        age = (now - last_activity).total_seconds()
        if age < idle_seconds:
            continue
        ready.append(row)
    return ready


def process_idle_sessions(
    *,
    list_sessions: Callable[[], list[dict[str, Any]]] | None = None,
    is_active: Callable[[str], bool] | None = None,
    learn: Callable[..., dict[str, Any]] | None = None,
    mark: Callable[..., None] | None = None,
    list_leaves: Callable[[str], list[str]] | None = None,
    leaf_learned: Callable[[str, str], bool] | None = None,
    mark_leaf: Callable[..., None] | None = None,
    idle_seconds: int = IDLE_SECONDS,
) -> list[dict[str, Any]]:
    """Scan sessions and run learn_session for every not-yet-learned branch
    leaf of each eligible idle chat — so a rewind/fork's abandoned branch
    still feeds experience learning instead of dying out."""
    if not EXPERIENCE_ENABLED:
        return []

    if list_sessions is None:
        from api.db.repositories import SessionRepository

        list_sessions = SessionRepository().list_all

    is_active = is_active or _is_run_active
    learn = learn or learn_session
    mark = mark or _mark_session

    if list_leaves is None or leaf_learned is None or mark_leaf is None:
        from src.utils.postgres_checkpointer import (
            is_leaf_learned as _is_leaf_learned,
            list_leaf_checkpoints as _list_leaf_checkpoints,
            mark_leaf_learned as _mark_leaf_learned,
        )

        list_leaves = list_leaves or _list_leaf_checkpoints
        leaf_learned = leaf_learned or _is_leaf_learned
        mark_leaf = mark_leaf or _mark_leaf_learned

    results: list[dict[str, Any]] = []
    for row in sessions_ready_to_learn(list_sessions(), idle_seconds=idle_seconds):
        agent_id = row.get("agent_id") or ""
        uid = row.get("owner_id") or ""
        if not agent_id or is_active(agent_id):
            continue

        try:
            leaves = list_leaves(agent_id)
        except Exception:
            logger.warning("Failed listing leaf checkpoints agent_id=%s", agent_id, exc_info=True)
            continue

        pending_leaves = [leaf for leaf in leaves if not leaf_learned(agent_id, leaf)]
        if not pending_leaves:
            continue

        mark(agent_id, experience_learn_status="pending")
        last_status = "skipped"
        for leaf in pending_leaves:
            outcome = learn(agent_id, uid=uid, checkpoint_id=leaf)
            last_status = outcome.get("status") or "error"
            if last_status in {"learned", "skipped"} and outcome.get("error") != "awaiting_extraction_confirmation":
                mark_leaf(agent_id, leaf, status=last_status)
            results.append(outcome)
            logger.info(
                "Learner finished agent_id=%s leaf=%s status=%s stored=%s",
                agent_id,
                leaf,
                last_status,
                outcome.get("stored_count"),
            )
        mark(
            agent_id,
            experience_learn_status=last_status,
            experience_learned_at=datetime.now(timezone.utc).isoformat(),
        )
    return results


class IdleWatcher:
    """Asyncio polling loop; learn work runs in a worker thread."""

    def __init__(
        self,
        *,
        poll_seconds: float = WATCHER_POLL_SECONDS,
        idle_seconds: int = IDLE_SECONDS,
    ) -> None:
        self.poll_seconds = poll_seconds
        self.idle_seconds = idle_seconds
        self._task: asyncio.Task | None = None
        self._stop = asyncio.Event()

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop = asyncio.Event()
        self._task = asyncio.create_task(self._loop(), name="experience-idle-watcher")
        logger.info(
            "Experience idle watcher started idle=%ss poll=%ss",
            self.idle_seconds,
            self.poll_seconds,
        )

    async def stop(self) -> None:
        self._stop.set()
        task = self._task
        self._task = None
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("Experience idle watcher stopped")

    async def _loop(self) -> None:
        try:
            while not self._stop.is_set():
                if EXPERIENCE_ENABLED:
                    try:
                        await asyncio.to_thread(
                            process_idle_sessions,
                            idle_seconds=self.idle_seconds,
                        )
                    except Exception:
                        logger.warning("Idle watcher tick failed", exc_info=True)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=self.poll_seconds)
                except asyncio.TimeoutError:
                    continue
        except asyncio.CancelledError:
            return


class BackgroundIdleWatcher:
    """Run the async watcher in a daemon thread for non-async entrypoints."""

    def __init__(self, **watcher_options: Any) -> None:
        self.watcher_options = watcher_options
        self._loop: asyncio.AbstractEventLoop | None = None
        self._watcher: IdleWatcher | None = None
        self._thread: threading.Thread | None = None
        self._started = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._started.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="experience-idle-watcher",
            daemon=True,
        )
        self._thread.start()
        self._started.wait(timeout=5)

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._watcher = IdleWatcher(**self.watcher_options)
        loop.run_until_complete(self._watcher.start())
        self._started.set()
        try:
            loop.run_forever()
        finally:
            loop.run_until_complete(self._watcher.stop())
            loop.close()

    def stop(self) -> None:
        loop = self._loop
        thread = self._thread
        if loop and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        if thread and thread.is_alive():
            thread.join(timeout=5)
        self._loop = None
        self._watcher = None
        self._thread = None
