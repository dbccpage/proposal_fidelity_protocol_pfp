"""DTO boundary for native Woland run custody. AuthorityEffect: None."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.native import NativeOperationPort

from ..domain.native import invoke, value

RECEIPT_ID_SCHEMA = "omega.woland.bout-receipt-id.v1"
DDC_TAPE = "ddc.jsonl"
"""The run folder's DDC tape."""
LEGACY_DDA_TAPE = "dda_actions.jsonl"
"""A byte copy of the tape that run folders written before 2026-10-16 also carry."""


def run_tape_path(run_dir: Path | str) -> Path:
    """Return the tape of a run folder: ``ddc.jsonl``, else the legacy copy."""
    folder = Path(run_dir)
    ddc = folder / DDC_TAPE
    return ddc if ddc.is_file() else folder / LEGACY_DDA_TAPE


def _steps_json(steps: Sequence[Any]) -> str:
    return json.dumps(
        [step.to_dict() if hasattr(step, "to_dict") else dict(step) for step in steps],
        ensure_ascii=False,
    )


def _novella_bytes(novella_md: str) -> bytes:
    return (novella_md.rstrip("\n") + "\n").encode("utf-8")


def _dda_tape(dda_steps: Sequence[Any], *, native_support: NativeOperationPort) -> tuple[bytes, str | None]:
    tape = value(native_support, "tape", steps_json=_steps_json(dda_steps))
    return bytes.fromhex(tape["bytes_hex"]), tape["head_sha256"]


def _summary_bytes(summary: Mapping[str, Any]) -> bytes:
    return (json.dumps(dict(summary), indent=2, sort_keys=True) + "\n").encode("utf-8")


def ddc_trace_digest(steps: Sequence[Any], *, native_support: NativeOperationPort) -> str | None:
    return value(native_support, "trace_digest", steps_json=_steps_json(steps))


def content_addressed_receipt_id(
    novella_md: str, dda_steps: Sequence[Any], summary_data: Mapping[str, Any]
, *, native_support: NativeOperationPort) -> str:
    return value(native_support,
        "receipt_id",
        novella_md=novella_md,
        steps_json=_steps_json(dda_steps),
        summary_json=json.dumps(dict(summary_data), ensure_ascii=False),
    )


def _reported_projection_payload(summary_data: Mapping[str, Any]) -> dict:
    summary = dict(summary_data or {})
    return {"history_json": json.dumps(summary, ensure_ascii=False),
            "context_json": json.dumps({"work_status": summary.get("work_status", summary.get("status", "INCOMPLETE")),
                                        "evidence_verdict": summary.get("terminal_verdict")}),
            "source_reference": "summary.json"}


def _reported_projection(summary_data: Mapping[str, Any], *, native_support: NativeOperationPort) -> dict:
    return value(native_support, "project_run_reports", **_reported_projection_payload(summary_data))


def reported_receipt_id(novella_md: str, dda_steps: Sequence[Any],
                        summary_data: Mapping[str, Any], *, native_support: NativeOperationPort) -> str:
    """Identity for fresh single-DDC bundles; historical v1 identity stays readable."""
    projection = _reported_projection(summary_data, native_support=native_support)
    return value(native_support, "receipt_id_v3", novella_md=novella_md, steps_json=_steps_json(dda_steps),
                 summary_json=json.dumps(dict(summary_data), ensure_ascii=False),
                 uts_jsonl=projection["uts_jsonl"])


def recompute_receipt_id(run_dir: Path | str, *, native_support: NativeOperationPort) -> str:
    return value(native_support, "recompute_receipt", run_dir=str(run_dir))


def run_directory_name(run_key: str, *, native_support: NativeOperationPort) -> str:
    if type(run_key) is not str:
        raise ValueError("run_key must be an exact nonempty string")
    return value(native_support, "run_name", run_key=run_key)


_run_directory_name = run_directory_name


def persist_bout_run_folder(
    output_dir: Path | str,
    run_key: str,
    receipt: Any,
    novella_md: str,
    dda_steps: Sequence[Any],
    summary_data: dict[str, Any],
    *,
    native_support: NativeOperationPort,
) -> Result[Path, Refusal]:
    """Seal a fresh UNS/UTS bundle with one DDC tape; refuse overwrite."""
    raw_receipt = (
        receipt.to_dict() if hasattr(receipt, "to_dict") and callable(receipt.to_dict) else receipt
    )
    raw_receipt = raw_receipt if isinstance(raw_receipt, dict) else {}
    projection = invoke(native_support, "project_run_reports", **_reported_projection_payload(summary_data))
    if isinstance(projection, Err):
        return projection
    result = invoke(native_support,
        "persist_v3",
        output_dir=str(output_dir),
        run_key=run_key,
        receipt_json=json.dumps(raw_receipt, ensure_ascii=False),
        novella_md=novella_md,
        steps_json=_steps_json(dda_steps),
        summary_json=json.dumps(dict(summary_data or {}), ensure_ascii=False),
        uts_jsonl=projection.value["uts_jsonl"],
    )
    if isinstance(result, Err):
        return result
    return Ok(Path(result.value))


def persist_bout_run_folder_historical(
    output_dir: Path | str, run_key: str, receipt: Any, novella_md: str,
    dda_steps: Sequence[Any], summary_data: dict[str, Any],
    *,
    native_support: NativeOperationPort,
) -> Result[Path, Refusal]:
    """Retain the explicit v1 format of fixed historical experiment producers."""
    raw = receipt.to_dict() if hasattr(receipt, "to_dict") and callable(receipt.to_dict) else receipt
    result = invoke(native_support, "persist", output_dir=str(output_dir), run_key=run_key,
                    receipt_json=json.dumps(raw if isinstance(raw, dict) else {}, ensure_ascii=False),
                    novella_md=novella_md, steps_json=_steps_json(dda_steps),
                    summary_json=json.dumps(dict(summary_data or {}), ensure_ascii=False))
    return result if isinstance(result, Err) else Ok(Path(result.value))


__all__ = [
    "DDC_TAPE",
    "LEGACY_DDA_TAPE",
    "RECEIPT_ID_SCHEMA",
    "content_addressed_receipt_id",
    "reported_receipt_id",
    "ddc_trace_digest",
    "persist_bout_run_folder",
    "persist_bout_run_folder_historical",
    "recompute_receipt_id",
    "run_directory_name",
    "run_tape_path",
]
