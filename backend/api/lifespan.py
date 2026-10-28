from __future__ import annotations

import logging
import os
import asyncio
import time
from contextlib import asynccontextmanager

from api.core.config import get_settings
from api.core.deps import get_repos
from api.core.logging_setup import configure_logging
from api.services.agent_runtime import ensure_client_path, get_agent_app

logger = logging.getLogger(__name__)


async def maintain_kb():
    while True:
        try:
            from src.agent import kb

            # Replay interrupted writes first; full rebuilds are explicit recovery operations.
            while await asyncio.to_thread(kb.sync_index):
                await asyncio.sleep(0)
            await asyncio.to_thread(kb.refresh_index)
        except Exception:
            logger.exception("KB index reconciliation failed")
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app):
    started_at = time.monotonic()
    settings = get_settings()
    configure_logging(logging.DEBUG if settings.debug else logging.INFO)
    os.environ["EVA_SKIP_VENV_REEXEC"] = "1"
    ensure_client_path()

    get_repos()
    from api.db.postgres import execute, fetch_one

    try:
        fetch_one("SELECT 1")
    except Exception as exc:
        raise RuntimeError(
            "PostgreSQL connection failed; check PGHOST, PGPORT, PGDATABASE, PGUSER, "
            "and PGPASSWORD in backend/.env against the running database"
        ) from exc
    logger.info("Startup PostgreSQL check completed in %.2fs", time.monotonic() - started_at)

    execute("ALTER TABLE agent_cores ADD COLUMN IF NOT EXISTS policy_ceiling JSONB")
    execute("ALTER TABLE mcp_servers_catalog ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'")
    execute("UPDATE agent_cores SET policy_ceiling = policy WHERE policy_ceiling IS NULL AND parent_agent_id IS NULL")
    execute(
        """
        CREATE TABLE IF NOT EXISTS memory_extraction_requests (
            request_id TEXT PRIMARY KEY,
            owner_id UUID NOT NULL,
            agent_id UUID NOT NULL,
            checkpoint_id TEXT NOT NULL,
            chunk_type TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('APPROVAL_PENDING', 'APPROVED', 'REJECTED', 'COMPLETED', 'SKIPPED')),
            reviewed_by UUID,
            reason TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    execute("CREATE INDEX IF NOT EXISTS idx_memory_extraction_owner_state ON memory_extraction_requests (owner_id, state, created_at DESC)")
    logger.info("Startup schema checks completed in %.2fs", time.monotonic() - started_at)

    async def cleanup_execution_events():
        while True:
            await asyncio.sleep(max(60, settings.execution_event_cleanup_interval_seconds))
            try:
                deleted = await asyncio.to_thread(
                    get_repos().execution_events.cleanup_completed_older_than,
                    settings.execution_event_retention_days,
                )
                if deleted:
                    logger.info("Execution event retention deleted=%s", deleted)
            except Exception:
                logger.exception("Execution event retention cleanup failed")

    cleanup_task = asyncio.create_task(cleanup_execution_events(), name="execution-event-retention")

    try:
        get_agent_app()
        app.state.agent_ready = True
        logger.info("Startup agent graph ready in %.2fs", time.monotonic() - started_at)
    except Exception:
        app.state.agent_ready = False
        logger.exception("Agent graph failed to initialize (API will start degraded)")

    idle_watcher = None
    try:
        from src.subagents.learner_agent.idle_watcher import IdleWatcher

        idle_watcher = IdleWatcher()
        await idle_watcher.start()
        app.state.idle_watcher = idle_watcher
    except Exception:
        app.state.idle_watcher = None
        logger.exception("Experience idle watcher failed to start (API continues)")

    logger.info("API startup complete in %.2fs port=%s data_root=%s",
                time.monotonic() - started_at, settings.port, settings.data_root)
    kb_task = asyncio.create_task(maintain_kb(), name="kb-index-reconciliation")
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    kb_task.cancel()
    try:
        await kb_task
    except asyncio.CancelledError:
        pass
    if idle_watcher is not None:
        try:
            await idle_watcher.stop()
        except Exception:
            logger.exception("Experience idle watcher stop failed")
    from api.services.mcp_runtime import mcp_runtime

    mcp_runtime.close()
    from src.agent.agent_core import child_runner

    child_runner.shutdown()
    logger.info("API shutting down")
