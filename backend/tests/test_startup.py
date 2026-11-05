"""Startup must not replay the entire memory KB before serving requests."""

import asyncio
from unittest.mock import patch

from api import lifespan
from src.agent import kb


def test_kb_maintenance_drains_pending_batches_then_reconciles():
    calls = []
    batches = iter((100, 2, 0))

    def sync():
        calls.append("sync")
        return next(batches)

    def refresh():
        calls.append("refresh")

    async def run():
        real_sleep = asyncio.sleep

        async def stop_after_first_tick(seconds):
            if seconds:
                raise asyncio.CancelledError
            await real_sleep(0)

        with patch.object(kb, "sync_index", side_effect=sync), \
             patch.object(kb, "refresh_index", side_effect=refresh), \
             patch.object(kb, "rebuild_index", side_effect=AssertionError("full rebuild")), \
             patch.object(lifespan.asyncio, "sleep", side_effect=stop_after_first_tick):
            try:
                await lifespan.maintain_kb()
            except asyncio.CancelledError:
                pass

    asyncio.run(run())
    assert calls == ["sync", "sync", "sync", "refresh"]


def test_kb_maintenance_retries_after_failure():
    calls = []

    def sync():
        calls.append("sync")
        if calls.count("sync") == 1:
            raise RuntimeError("temporary failure")
        return 0

    async def run():
        async def sleep(_seconds):
            if calls.count("sync") == 2:
                raise asyncio.CancelledError

        with patch.object(kb, "sync_index", side_effect=sync), \
             patch.object(kb, "refresh_index", side_effect=lambda: calls.append("refresh")), \
             patch.object(lifespan.asyncio, "sleep", side_effect=sleep):
            try:
                await lifespan.maintain_kb()
            except asyncio.CancelledError:
                pass

    asyncio.run(run())
    assert calls == ["sync", "sync", "refresh"]
