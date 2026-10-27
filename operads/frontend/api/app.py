"""FastAPI Application factory for OEWAS V3."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from ...controllers.python_facade import OeopApiV3
from ...controllers.router import create_oeop_router
from ...infrastructure.bootstrap import OeopContainer


def create_app(
    api: OeopApiV3 | None = None,
    workspace_root: Path | None = None,
    db_path: str = ":memory:",
) -> FastAPI:
    """Create OEWAS V3 with local-only resource routes and public docs/health.

    The reusable router owns caller and streamed-body admission, so including
    it in another host retains the same boundary. This is not authentication;
    do not expose it through a proxy which erases forwarding/origin evidence.
    """
    app = FastAPI(
        title="OEWAS V3 API",
        description="Engine Workflows, Agents & Skills V3 REST API",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    if api is None:
        ws = workspace_root or Path.cwd()
        container = OeopContainer(workspace_root=ws, db_path=db_path)
        api = container.api

    router = create_oeop_router(api)
    app.include_router(router)

    @app.get("/healthz", tags=["Health"])
    def health_check():
        return {"status": "ok", "service": "oewas-v3"}

    return app
