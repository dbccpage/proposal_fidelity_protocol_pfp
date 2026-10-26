"""Reference self-consistency gate and run-folder persistence for C042 (SAT Encodings with DRAT Certificates).

AuthorityEffect: None.

This gate scores the frozen reference solver against this package's own judge
packet. It evaluates no model and it is not a Woland verdict: the Woland swarm
(``omega_engine_woland``) is the only final evaluator. The label is computed
here from exact counts, never taken from the caller:

- REFERENCE_SELF_CONSISTENT: at least one case was scored, every case passed,
  no defect was recorded, and, when a mutation suite was run, it held at least
  one mutation and every mutation was rejected.
- REFERENCE_SELF_INCONSISTENT: anything else, including an empty suite.
- OPEN_RESIDUAL: consistent, but the caller declared a closed residual in
  ``residuals``. Custody facts such as a missing pre-run commitment are passed
  as ``informational_residuals``: they are recorded and do not change the label.

C042 has one checker per answer branch (SAT model check or DRAT check), so no
checker agreement is measured or claimed.

The run folder ``<intelligence root>/_intelligence/_woland/runs/<task_key>_<stamp>``
holds report (novella.md), dda_actions.jsonl, summary.json and receipt.json,
all derived from the inputs. It is built in a staging directory beside the
destination and moved into place with os.replace; an existing folder is never
overwritten. If writing fails, a failure_receipt.json is written and the staged
files are moved into the run folder anyway: nothing under ``_intelligence/`` is
ever deleted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)

CHALLENGE_ID = "c042_sat_with_drat_certificates"
CHALLENGE_TITLE = "C042 (SAT Encodings with DRAT Certificates)"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
TERMINAL_VERDICTS = (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE, TERMINAL_OPEN_RESIDUAL)

RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
LABEL_MISMATCH = "LABEL_MISMATCH"
FAILURE_RECEIPT_NAME = "failure_receipt.json"


class RunFolderExistsError(FileExistsError):
    """Raised instead of overwriting an existing run folder."""

    def __init__(self, message: str) -> None:
        self.code = RUN_FOLDER_EXISTS
        super().__init__(f"{RUN_FOLDER_EXISTS}: {message}")


class LabelMismatchError(ValueError):
    """A caller-supplied label differs from the label computed from the counts."""

    def __init__(self, message: str) -> None:
        self.code = LABEL_MISMATCH
        super().__init__(f"{LABEL_MISMATCH}: {message}")


def utc_timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _run_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def sanitize_run_key(key: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]", "_", key.strip())
    return clean if clean.strip("_") else "c042_run"


def _require_count(name: str, value: Any) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative int; got {value!r}")
    return value


def label_with_reason(
    total_cases: int,
    passed_cases: int,
    defect_count: int,
    *,
    mutations_total: int | None = None,
    mutations_killed: int | None = None,
    residuals: Sequence[str] = (),
) -> tuple[str, str]:
    """Return (label, reason) from exact counts. Empty suites are inconsistent."""
    _require_count("total_cases", total_cases)
    _require_count("passed_cases", passed_cases)
    _require_count("defect_count", defect_count)
    if passed_cases > total_cases:
        raise ValueError(f"passed_cases ({passed_cases}) exceeds total_cases ({total_cases})")
    if (mutations_total is None) != (mutations_killed is None):
        raise TypeError("mutations_total and mutations_killed must both be given or both be None")
    if mutations_total is not None:
        _require_count("mutations_total", mutations_total)
        _require_count("mutations_killed", mutations_killed)
        if mutations_killed > mutations_total:
            raise ValueError(
                f"mutations_killed ({mutations_killed}) exceeds mutations_total ({mutations_total})"
            )
    if isinstance(residuals, str) or any(type(r) is not str for r in residuals):
        raise TypeError("residuals must be a sequence of strings")

    if total_cases == 0:
        return TERMINAL_REFUSE, "Empty judge suite: 0 cases scored."
    if passed_cases != total_cases or defect_count != 0:
        return (
            TERMINAL_REFUSE,
            f"{total_cases - passed_cases} of {total_cases} cases failed; {defect_count} defects.",
        )
    if mutations_total is not None and mutations_total == 0:
        return TERMINAL_REFUSE, "Empty mutation suite: 0 mutations run."
    if mutations_total is not None and mutations_killed != mutations_total:
        return (
            TERMINAL_REFUSE,
            f"{mutations_total - mutations_killed} of {mutations_total} mutations were accepted.",
        )
    if residuals:
        return (
            TERMINAL_OPEN_RESIDUAL,
            f"All {total_cases} cases passed; residuals: {', '.join(residuals)}.",
        )
    return TERMINAL_REFERENCE_SELF_CONSISTENT, f"All {total_cases} cases passed."


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


class WolandGateC042:
    """Reference self-consistency gate for C042 (historical class name kept for callers).

    Constructing the gate creates no directory; the run folder is created only
    when a bundle is persisted.

    AuthorityEffect: None.
    """

    def __init__(
        self, task_key: str = "c042_eval", *, intelligence_repo_root: Path | None = None
    ) -> None:
        self.task_key = task_key
        self.repo_root = (
            intelligence_repo_root
            if intelligence_repo_root is not None
            else resolve_intelligence_repo_root()
        )
        self.run_folder = self._init_run_folder(task_key)

    def _init_run_folder(self, task_key: str) -> Path:
        """Return the run-folder path (not created) under the intelligence root."""
        runs_dir = self.repo_root / "_ic/darpa/woland" / "runs"
        return runs_dir / f"{sanitize_run_key(task_key)}_{_run_stamp()}"

    def emit_structurebench_quad(
        self,
        total_cases: int,
        passed_cases: int,
        defects: Sequence[Mapping[str, Any]],
        receipt_meta: Mapping[str, Any],
        *,
        verdict: str | None = None,
        mutations_total: int | None = None,
        mutations_killed: int | None = None,
        residuals: Sequence[str] = (),
        informational_residuals: Sequence[str] = (),
    ) -> Path:
        """Compute the label, write the four files and return the run folder.

        ``verdict`` is an optional caller expectation; it is refused unless it
        equals the label computed from the counts. ``informational_residuals``
        are recorded in the bundle and never change the label.
        """
        if isinstance(informational_residuals, str) or any(
            type(r) is not str for r in informational_residuals
        ):
            raise TypeError("informational_residuals must be a sequence of strings")
        notes = list(informational_residuals)
        label, reason = label_with_reason(
            total_cases,
            passed_cases,
            len(defects),
            mutations_total=mutations_total,
            mutations_killed=mutations_killed,
            residuals=residuals,
        )
        if verdict is not None and verdict != label:
            raise LabelMismatchError(
                f"caller label {verdict!r} differs from computed label {label!r}"
            )

        target = self.run_folder
        if target.exists():
            raise RunFolderExistsError(f"Refusing to overwrite existing run directory: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.staging.", dir=str(target.parent)))

        counts = {
            "defect_count": len(defects),
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "passed_cases": passed_cases,
            "total_cases": total_cases,
        }
        try:
            report = self._render_report(label, reason, counts, list(residuals), notes)
            novella_bytes = report.encode("utf-8")
            (staging / "novella.md").write_bytes(novella_bytes)

            rows = [
                {
                    "action": "intake_judge_cases",
                    "case_count": total_cases,
                    "letter": "C",
                    "mutation_count": mutations_total,
                },
                {
                    "action": "score_reference_outputs",
                    "defect_count": len(defects),
                    "letter": "R",
                    "passed_cases": passed_cases,
                },
            ]
            if mutations_total is not None:
                rows.append(
                    {
                        "action": "run_hostile_mutations",
                        "letter": "D",
                        "mutations_killed": mutations_killed,
                    }
                )
            rows.append(
                {
                    "action": "emit_self_consistency_label",
                    "label": label,
                    "letter": "T",
                    "scope": GATE_SCOPE,
                }
            )
            dda_bytes = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode("utf-8")
            (staging / "dda_actions.jsonl").write_bytes(dda_bytes)

            summary = {
                **counts,
                "authority_effect": "None",
                "challenge_id": CHALLENGE_ID,
                "defects": [dict(d) for d in defects],
                "gate_scope": GATE_SCOPE,
                "informational_residuals": notes,
                "reason": reason,
                "residuals": list(residuals),
                "run_folder": target.name,
                "timestamp_utc": utc_timestamp_now(),
                "verdict": label,
            }
            summary_bytes = _json_bytes(summary)
            (staging / "summary.json").write_bytes(summary_bytes)

            receipt = {
                **counts,
                "authority_effect": "None",
                "challenge_id": CHALLENGE_ID,
                "dda_actions_sha256": hashlib.sha256(dda_bytes).hexdigest(),
                "gate_scope": GATE_SCOPE,
                "informational_residuals": notes,
                "metadata": dict(receipt_meta),
                "novella_sha256": hashlib.sha256(novella_bytes).hexdigest(),
                "receipt_id": f"rcpt_{target.name}",
                "residuals": list(residuals),
                "summary_sha256": hashlib.sha256(summary_bytes).hexdigest(),
                "timestamp_utc": utc_timestamp_now(),
                "verdict": label,
            }
            (staging / "receipt.json").write_bytes(_json_bytes(receipt))
        except BaseException as error:
            try:
                failure = {
                    "authority_effect": "None",
                    "challenge_id": CHALLENGE_ID,
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                    "files_present": sorted(p.name for p in staging.iterdir()),
                    "status": "RUN_FAILED",
                    "timestamp_utc": utc_timestamp_now(),
                }
                (staging / FAILURE_RECEIPT_NAME).write_bytes(_json_bytes(failure))
                os.replace(staging, target)
            except OSError as custody_error:
                error.add_note(
                    f"failure receipt not moved into place: {custody_error!r}; staging kept at {staging}"
                )
            raise

        os.replace(staging, target)
        return target

    def _render_report(
        self,
        label: str,
        reason: str,
        counts: Mapping[str, Any],
        residuals: list[str],
        notes: list[str] | None = None,
    ) -> str:
        mutations = (
            "not run"
            if counts["mutations_total"] is None
            else f"{counts['mutations_killed']}/{counts['mutations_total']}"
        )
        lines = [
            f"# Reference self-consistency report: {CHALLENGE_TITLE}",
            "",
            f"- Task key: `{self.task_key}`",
            f"- Label: `{label}`",
            f"- Scope: `{GATE_SCOPE}`: the frozen reference solver scored against this package's own judge packet; "
            "no model was evaluated and this is not a Woland verdict.",
            f"- Reason: {reason}",
            f"- Judge cases passed: {counts['passed_cases']}/{counts['total_cases']}",
            f"- Defects recorded: {counts['defect_count']}",
            f"- Hostile mutations rejected: {mutations}",
            "- Checker agreement: not measured (one checker per answer branch).",
            f"- Closed residuals (change the label): {', '.join(residuals) if residuals else 'none declared'}",
            f"- Recorded residuals (label unchanged): {', '.join(notes) if notes else 'none'}",
            "",
        ]
        return "\n".join(lines)


__all__ = [
    "CHALLENGE_ID",
    "FAILURE_RECEIPT_NAME",
    "GATE_SCOPE",
    "LABEL_MISMATCH",
    "LabelMismatchError",
    "RUN_FOLDER_EXISTS",
    "RunFolderExistsError",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_VERDICTS",
    "WolandGateC042",
    "label_with_reason",
    "sanitize_run_key",
]
