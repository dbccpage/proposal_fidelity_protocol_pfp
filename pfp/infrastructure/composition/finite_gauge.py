"""Composition root for the finite-gauge workbench."""

from __future__ import annotations

from datetime import datetime, timezone
from time import sleep
from uuid import uuid4

from pfp.domain.finite_gauge import RunConfig
from pfp.infrastructure.adapters.finite_gauge.paper002_checker import (
    Paper002FiniteGaugeChecker,
)
from pfp.infrastructure.adapters.finite_gauge.run_store import RunStore
from pfp.use_cases.finite_gauge_workbench import (
    FiniteGaugeRun,
    GaugeRunRuntime,
)


def _clock() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sleep(milliseconds: int) -> None:
    sleep(milliseconds / 1000)


def build_runtime() -> GaugeRunRuntime:
    return GaugeRunRuntime(
        checker=Paper002FiniteGaugeChecker(),
        clock=_clock,
        sleeper=_sleep,
        id_factory=lambda: uuid4().hex,
    )


def build_run(
    config: RunConfig,
    *,
    event_sink=None,
    input_text: str | None = None,
) -> FiniteGaugeRun:
    return FiniteGaugeRun(
        config=config,
        runtime=build_runtime(),
        event_sink=event_sink,
        input_text=input_text,
    )


def build_run_store(max_runs: int = 32) -> RunStore:
    return RunStore(runtime=build_runtime(), max_runs=max_runs)


__all__ = ["build_run", "build_run_store", "build_runtime"]
