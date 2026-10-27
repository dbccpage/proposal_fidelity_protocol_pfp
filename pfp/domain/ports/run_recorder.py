"""Domain port for the Symbol Game Run-Folder Mandate (U01).

AuthorityEffect: None.
Every execution produces exactly one sealed RunFolderV1 under _intelligence/symbol_game/runs/.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from operations.domain.rop.result import Err, Ok, Refusal, Result


class RunTrigger(str, Enum):
    """Closed enum of run triggers."""

    CLI = "cli"
    DEMO = "demo"
    BENCH = "bench"
    TRIAL = "trial"
    ADVERSARY = "adversary"
    ADVERSARY_SKILL = "adversary_skill"
    OEWAS = "oewas"
    CHALLENGE = "challenge"
    MINING = "mining"
    OPERAND_ADMISSION = "operand_admission"
    TEST = "test"


class RunStream(str, Enum):
    """Streams recorded within a RunFolder."""

    PACKETS = "packets.jsonl"
    DDC_TRACE = "ddc_trace.jsonl"
    PRIME_TRACE = "prime_trace.jsonl"
    OBSTRUCTIONS = "obstructions.jsonl"
    CEMETERY = "cemetery.jsonl"


@dataclass(frozen=True)
class RunId:
    """Canonical run identifier and directory name."""

    value: str

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise TypeError("RunId value must be str")
        if not self.value.strip():
            raise ValueError("RunId value cannot be empty")

    def __str__(self) -> str:
        return self.value


class RunRecorder(Protocol):
    """Protocol for recording execution streams into a sealed RunFolder."""

    def open_run(
        self,
        trigger: RunTrigger,
        task_slug: str,
        *,
        parent_run_ids: Sequence[str] = (),
        run_mode: str = "fixture",
        budget_micro_usd: int | None = None,
        code_hashes: Mapping[str, str] | None = None,
        model_registry_entries: Sequence[str] = (),
    ) -> Result[RunId, Refusal]:
        """Open a new streaming run folder."""
        ...

    def append(
        self,
        run_id: RunId,
        stream: RunStream,
        row: Mapping[str, Any],
    ) -> Result[None, Refusal]:
        """Append a record row to an open stream."""
        ...

    def close(
        self,
        run_id: RunId,
        summary: Mapping[str, Any],
        report_md: str,
    ) -> Result[str, Refusal]:
        """Seal the run folder with final summary and report, and atomically rename into place."""
        ...

    def abort(
        self,
        run_id: RunId,
        reason: str,
        *,
        summary: Mapping[str, Any] | None = None,
    ) -> Result[str, Refusal]:
        """Seal an aborted run folder (never deleted), preserving partial records."""
        ...


RunRecorderPort = RunRecorder


class RunRunnerPort(Protocol):
    """Protocol for runners executing tasks within a governed RunFolder context."""

    def run(
        self,
        trigger: RunTrigger,
        task_slug: str,
        execution_fn: Callable[[RunId, RunRecorderPort], Result[tuple[Mapping[str, Any], str], Refusal]],
        **kwargs: Any,
    ) -> Result[str, Refusal]:
        """Execute a task and seal its RunFolder."""
        ...


class RunRecorderRunner:
    """Executes a workflow within a governed RunFolder, managing open, append, close, and abort."""

    def __init__(self, recorder: RunRecorderPort) -> None:
        self._recorder = recorder

    @property
    def recorder(self) -> RunRecorderPort:
        return self._recorder

    def run(
        self,
        trigger: RunTrigger,
        task_slug: str,
        execution_fn: Callable[[RunId, RunRecorderPort], Result[tuple[Mapping[str, Any], str], Refusal]],
        *,
        parent_run_ids: Sequence[str] = (),
        run_mode: str = "fixture",
        budget_micro_usd: int | None = None,
        code_hashes: Mapping[str, str] | None = None,
        model_registry_entries: Sequence[str] = (),
    ) -> Result[str, Refusal]:
        """Open a run, execute execution_fn, and close or abort based on the outcome."""
        open_res = self._recorder.open_run(
            trigger,
            task_slug,
            parent_run_ids=parent_run_ids,
            run_mode=run_mode,
            budget_micro_usd=budget_micro_usd,
            code_hashes=code_hashes,
            model_registry_entries=model_registry_entries,
        )
        if not open_res.is_ok:
            return Err(open_res.error)

        run_id = open_res.value
        try:
            res = execution_fn(run_id, self._recorder)
            if res.is_ok:
                summary, report_md = res.value
                return self._recorder.close(run_id, summary, report_md)
            else:
                self._recorder.abort(run_id, str(res.error))
                return Err(res.error)
        except Exception as exc:
            self._recorder.abort(run_id, f"UNHANDLED_EXCEPTION: {exc}")
            return Err(Refusal("EXECUTION_FAILED", str(exc)))


__all__ = [
    "RunId",
    "RunRecorder",
    "RunRecorderPort",
    "RunRecorderRunner",
    "RunRunnerPort",
    "RunStream",
    "RunTrigger",
]
