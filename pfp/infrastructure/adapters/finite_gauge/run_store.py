"""Bounded in-process run registry and thread launcher."""

from __future__ import annotations

from threading import Lock, Thread

from pfp.domain.finite_gauge import GaugeRefusal, GaugeRefusalCode, RunConfig
from pfp.domain.kernel.result import Result
from pfp.use_cases.finite_gauge_workbench import FiniteGaugeRun, GaugeRunRuntime


class RunStore:
    """Outer adapter owning process-local capacity and thread lifecycle."""

    def __init__(self, runtime: GaugeRunRuntime, max_runs: int = 32) -> None:
        self.runtime = runtime
        self.max_runs = max_runs
        self._lock = Lock()
        self._runs: dict[str, FiniteGaugeRun] = {}

    def start(
        self, config: RunConfig, input_text: str | None = None
    ) -> Result[FiniteGaugeRun, GaugeRefusal]:
        with self._lock:
            if len(self._runs) >= self.max_runs:
                return Result.err(
                    GaugeRefusal(
                        GaugeRefusalCode.RUN_CAPACITY_REACHED,
                        "process-local run capacity reached",
                    )
                )
            try:
                run = FiniteGaugeRun(config, self.runtime, input_text=input_text)
            except Exception as exc:
                return Result.err(
                    GaugeRefusal(GaugeRefusalCode.RUNTIME_DEPENDENCY_FAILED, str(exc))
                )
            self._runs[run.run_id] = run
        Thread(target=run.execute, name=f"finite-gauge-{run.run_id}", daemon=True).start()
        return Result.ok(run)

    def get(self, run_id: str) -> FiniteGaugeRun | None:
        with self._lock:
            return self._runs.get(run_id)


__all__ = ["RunStore"]
