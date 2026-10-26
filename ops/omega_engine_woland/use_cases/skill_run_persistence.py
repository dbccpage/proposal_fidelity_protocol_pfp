"""DTO boundary for native skill-authored Woland runs. AuthorityEffect: None.

Rust validates checker evidence and persists UNS/UTS with one DDC tape.
Historical five-file and six-file readers remain available.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.native import NativeOperationPort

from ..domain.native import invoke

SKILL_RUN_RECEIPT_SCHEMA = "omega.woland.skill-run-receipt.v1"
TERMINAL_VERDICTS = (
    "PASS_TO_MASTER",
    "REFUSE",
    "OPEN_RESIDUAL",
    "REFERENCE_SELF_CONSISTENT",
    "REFERENCE_SELF_INCONSISTENT",
)
WORK_STATUSES = ("completed", "partial", "blocked")
CHECKER_BOUND_VERDICTS = frozenset({"PASS_TO_MASTER"})
DDC_LETTERS = frozenset({"E", "R", "C", "I", "Λ", "Lambda", "D", "M", "T"})


def parse_dda_actions(text: str, *, native_support: NativeOperationPort) -> Result[tuple[dict[str, Any], ...], Refusal]:
    result = invoke(native_support, "skill_actions", text=text)
    return result if isinstance(result, Err) else Ok(tuple(result.value))


def persist_skill_run(
    woland_output_dir: Path,
    *,
    task_key: str,
    objective: str,
    verdict: str,
    source: str,
    novella_md: str,
    created_utc: str,
    dda_steps: Sequence[Mapping[str, Any]] = (),
    summary: Mapping[str, Any] | None = None,
    checker_receipt_bytes: bytes | None = None,
    work_status: str | None = None,
    native_support: NativeOperationPort,
) -> Result[Path, Refusal]:
    """Persist task progress independently of the native evidence verdict."""
    summary_fields = dict(summary or {})
    if work_status is not None:
        if type(work_status) is not str or work_status not in WORK_STATUSES:
            return Err(Refusal("WORK_STATUS_INVALID", "unknown reported work status", __name__))
        if "work_status" in summary_fields and summary_fields["work_status"] != work_status:
            return Err(
                Refusal("SUMMARY_KEY_CONFLICT", "summary conflicts with work_status", __name__)
            )
        summary_fields["work_status"] = work_status
    if checker_receipt_bytes is not None and type(checker_receipt_bytes) is not bytes:
        return Err(Refusal("CHECKER_RECEIPT_EMPTY", "the checker receipt file is empty", __name__))
    result = invoke(native_support,
        "skill_persist",
        output_dir=str(woland_output_dir),
        request={
            "task_key": task_key,
            "objective": objective,
            "verdict": verdict,
            "source": source,
            "novella_md": novella_md,
            "created_utc": created_utc,
            "dda_steps": [dict(step) for step in dda_steps],
            "summary": summary_fields,
            "checker_receipt_hex": checker_receipt_bytes.hex()
            if checker_receipt_bytes is not None
            else None,
        },
    )
    return result if isinstance(result, Err) else Ok(Path(result.value))


parse_ddc_actions = parse_dda_actions
__all__ = [
    "CHECKER_BOUND_VERDICTS",
    "DDC_LETTERS",
    "SKILL_RUN_RECEIPT_SCHEMA",
    "TERMINAL_VERDICTS",
    "WORK_STATUSES",
    "parse_dda_actions",
    "parse_ddc_actions",
    "persist_skill_run",
]
