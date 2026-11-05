from __future__ import annotations

import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import psycopg
from psycopg_pool import PoolTimeout

from api.api_routes import (
    agents,
    analytics,
    armory,
    auth,
    experience,
    files,
    health,
    kb,
    memory,
    preferences,
)
from api.core.config import get_settings
from api.lifespan import lifespan
from api.ws import endpoint as ws_endpoint
from src.utils.trace import bind, reset, span


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.dependencies = {"postgres": False, "chroma": False}
    app.state.startup_warnings = []

    @app.middleware("http")
    async def trace_requests(request, call_next):
        token = bind(request_id="req_" + uuid.uuid4().hex)
        try:
            data = {"method": request.method, "path": request.url.path}
            with span("api", "request", component="http", data=data):
                response = await call_next(request)
                data["http_status"] = response.status_code
                return response
        finally:
            reset(token)

    @app.exception_handler(PoolTimeout)
    async def handle_pool_timeout(_request: Request, _exc: PoolTimeout):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database unavailable. Check PostgreSQL is running and backend/.env PG* values.",
                "code": "postgres_unavailable",
            },
        )

    @app.exception_handler(psycopg.Error)
    async def handle_psycopg_error(_request: Request, _exc: psycopg.Error):
        return JSONResponse(
            status_code=503,
            content={
                "detail": "Database error. Verify PostgreSQL availability and credentials.",
                "code": "postgres_error",
            },
        )

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix

    # Public
    app.include_router(auth.login_router, prefix=prefix)
    app.include_router(health.live_router, prefix=prefix)

    # Authenticated REST
    app.include_router(auth.router, prefix=prefix)
    app.include_router(agents.router, prefix=prefix)
    app.include_router(armory.router, prefix=prefix)
    app.include_router(memory.router, prefix=prefix)
    app.include_router(kb.router, prefix=prefix)
    app.include_router(preferences.router, prefix=prefix)
    app.include_router(files.router, prefix=prefix)
    app.include_router(analytics.router, prefix=prefix)
    app.include_router(experience.router, prefix=prefix)
    app.include_router(health.router, prefix=prefix)

    # WebSocket (auth via query token)
    app.include_router(ws_endpoint.router, prefix=prefix)

    return app
