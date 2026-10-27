"""Local FastAPI workbench for observable finite Symbol Game controls.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse

from pfp.domain.finite_gauge import RunConfig
from pfp.infrastructure.adapters.finite_gauge.input_yaml import (
    parse_input_yaml,
)
from pfp.infrastructure.adapters.finite_gauge.run_store import RunStore
from pfp.infrastructure.composition.finite_gauge import build_run_store
from pfp.use_cases.finite_gauge_workbench import FiniteGaugeRun, fixtures

_WEB_DIR = Path(__file__).resolve().parent


def _parse_config(body: dict[str, Any]) -> tuple[RunConfig, str | None]:
    input_text = body.get("input_yaml")
    if input_text is not None:
        if set(body) != {"input_yaml"}:
            raise ValueError("input_yaml cannot be combined with other run fields")
        return parse_input_yaml(input_text), input_text
    if "input" in body:
        if set(body) != {"input"}:
            raise ValueError("input cannot be combined with other run fields")
        return RunConfig.from_packet(body["input"]), None
    unknown = set(body) - {"fixture_id", "node_budget", "pace_ms"}
    if unknown:
        raise ValueError("unknown run fields: " + ", ".join(sorted(unknown)))
    return (
        RunConfig(
            fixture_id=body.get("fixture_id", "gauge_even_triangle"),
            node_budget=body.get("node_budget", 8),
            pace_ms=body.get("pace_ms", 180),
        ),
        None,
    )


def _event_rows(run: FiniteGaugeRun, cursor: int) -> Iterator[str]:
    current = cursor
    while True:
        batch, finished = run.wait_for_events(current)
        for event in batch:
            current = event["seq"]
            payload = json.dumps(event, ensure_ascii=False, separators=(",", ":"))
            yield f"id: {current}\nevent: update\ndata: {payload}\n\n"
        if finished:
            return
        if not batch:
            yield ": keep-alive\n\n"


class WorkbenchApi:
    """HTTP adapter around the bounded process-local registry."""

    def __init__(self, store: RunStore) -> None:
        self.store = store

    def list_fixtures(self) -> dict[str, Any]:
        return {"fixtures": fixtures(), "authority_effect": "None"}

    def start_run(self, body: dict[str, Any]) -> dict[str, Any]:
        try:
            config, input_text = _parse_config(body)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        started = self.store.start(config, input_text=input_text)
        if started.is_err:
            raise HTTPException(status_code=503, detail=started.unwrap_err().message)
        run = started.unwrap()
        return {"run_id": run.run_id, "snapshot": run.snapshot()}

    def require_run(self, run_id: str) -> FiniteGaugeRun:
        run = self.store.get(run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="run not found in this server process")
        return run

    def get_run(self, run_id: str) -> dict[str, Any]:
        return self.require_run(run_id).snapshot()

    def stream_events(
        self,
        run_id: str,
        after: int = Query(default=0, ge=0),
        last_event_id: str | None = Header(default=None),
    ) -> StreamingResponse:
        run = self.require_run(run_id)
        cursor = after
        if last_event_id is not None:
            try:
                cursor = max(cursor, int(last_event_id))
            except ValueError:
                cursor = after
        return StreamingResponse(
            _event_rows(run, cursor),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    def index(self) -> FileResponse:
        return FileResponse(_WEB_DIR / "index.html")

    def stylesheet(self) -> FileResponse:
        return FileResponse(_WEB_DIR / "app.css", media_type="text/css")

    def script(self) -> FileResponse:
        return FileResponse(_WEB_DIR / "app.js", media_type="text/javascript")


def create_app(store: RunStore | None = None) -> FastAPI:
    api = WorkbenchApi(store or build_run_store())
    app = FastAPI(
        title="Core Symbol Game Workbench",
        description="Live finite signed-graph gauge controls. AuthorityEffect: None.",
        version="0.1.0",
    )
    app.add_api_route("/api/workbench/fixtures", api.list_fixtures, methods=["GET"])
    app.add_api_route(
        "/api/workbench/runs", api.start_run, methods=["POST"], status_code=202
    )
    app.add_api_route("/api/workbench/runs/{run_id}", api.get_run, methods=["GET"])
    app.add_api_route(
        "/api/workbench/runs/{run_id}/events", api.stream_events, methods=["GET"]
    )
    app.add_api_route("/", api.index, methods=["GET"], include_in_schema=False)
    app.add_api_route(
        "/assets/app.css", api.stylesheet, methods=["GET"], include_in_schema=False
    )
    app.add_api_route(
        "/assets/app.js", api.script, methods=["GET"], include_in_schema=False
    )
    return app


app = create_app()

__all__ = ["WorkbenchApi", "app", "create_app"]
