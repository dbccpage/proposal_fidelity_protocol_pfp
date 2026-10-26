"""Reference self-consistency gate and run-folder persistence for C032 (Six-Dimensional Supergravity Anomaly Cancellation).

AuthorityEffect: None.

This gate scores the frozen reference solver against this package's own judge
packet. It evaluates no model and it is not a Woland verdict: the Woland swarm
(``omega_engine_woland``) is the only final evaluator. Its labels are:

- REFERENCE_SELF_CONSISTENT: at least one case was scored, every case passed
  with checker agreement, no defect was reported and every exact defect value
  that was measured is zero.
- REFERENCE_SELF_INCONSISTENT: anything else, including an empty suite.
- OPEN_RESIDUAL: consistent, but the caller declared a closed residual.

A run folder holds four files: novella.md (a factual report whose values are
taken only from the measured counts passed in; the file name is historical),
dda_actions.jsonl, summary.json and receipt.json. Each bundle is staged in a
directory beside its destination and moved into place with os.replace. An
existing run folder is never replaced. If writing fails, a failure_receipt.json
is written and the staged files are moved into the run folder anyway: nothing
under ``_intelligence/`` is ever deleted. Run roots come from
``resolve_intelligence_repo_root`` unless a base directory is passed.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
from typing import Any

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (
    resolve_intelligence_repo_root,
)

CHALLENGE_ID = "c032_six_d_sugra_anomaly_cancellation"
CHALLENGE_TITLE = "C032 (Six-Dimensional Supergravity Anomaly Cancellation)"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
TERMINAL_VERDICTS = (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE, TERMINAL_OPEN_RESIDUAL)

CANONICAL_OUTPUT_FILES = ("novella.md", "dda_actions.jsonl", "summary.json", "receipt.json")
RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
UNKNOWN_LABEL = "UNKNOWN_LABEL"
FAILURE_RECEIPT_NAME = "failure_receipt.json"
_LABEL_KEYS = ("verdict", "final_verdict")


class RunFolderExistsError(FileExistsError):
    """Raised when a run folder already exists; existing run folders are never replaced."""

    def __init__(self, message: str) -> None:
        self.code = RUN_FOLDER_EXISTS
        super().__init__(f"{RUN_FOLDER_EXISTS}: {message}")


class UnknownLabelError(ValueError):
    """Raised when a report, summary or receipt carries a label this gate does not emit."""

    def __init__(self, label: object) -> None:
        self.code = UNKNOWN_LABEL
        super().__init__(f"{UNKNOWN_LABEL}: {label!r} is not one of {TERMINAL_VERDICTS}")


def utc_timestamp_now() -> str:
    """Canonical UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sanitize_run_key(key: str) -> str:
    """Make a run key safe as a single directory name."""
    clean = (
        str(key).strip().replace(" ", "_").replace(":", "-").replace("/", "_").replace("\\", "_")
    )
    clean = clean.replace("..", "_")
    return clean or f"{CHALLENGE_ID}_run"


def require_known_label(label: object) -> str:
    """Return the label when it is one this gate emits; raise UnknownLabelError otherwise."""
    if type(label) is not str or label not in TERMINAL_VERDICTS:
        raise UnknownLabelError(label)
    return label


def exact_defect_value(name: str, value: Any) -> Fraction | None:
    """Return an exact defect value, or None when it was not measured.

    Floats and booleans are refused: a defect value is an exact rational.
    """
    if value is None:
        return None
    if type(value) is int or type(value) is Fraction:
        return Fraction(value)
    raise TypeError(
        f"{name} must be an exact int or Fraction, or None when not measured; got {type(value).__name__}"
    )


def exact_wire(value: Fraction | None) -> str | None:
    """Serialise an exact value as 'p/q' (integers without a slash); None stays None."""
    return None if value is None else str(value)


def _require_count(name: str, value: Any) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative int; got {value!r}")
    return value


def _optional_count(stats: Mapping[str, Any], key: str) -> int | None:
    value = stats.get(key)
    return None if value is None else _require_count(key, value)


def determine_terminal_verdict(
    case_count: int,
    passed_count: int,
    agreed_count: int,
    *,
    defect_count: int = 0,
    phi1: Fraction | int | None = None,
    gamma2: Fraction | int | None = None,
    has_closed_residual: bool = False,
) -> str:
    """Label a reference self-consistency run from exact counts.

    An empty suite is inconsistent. Every case must pass and every case must
    have checker agreement. Defect values are exact: any measured non-zero
    Phi_1 or Gamma_2 is inconsistent, with no tolerance.
    """
    _require_count("case_count", case_count)
    _require_count("passed_count", passed_count)
    _require_count("agreed_count", agreed_count)
    _require_count("defect_count", defect_count)
    if passed_count > case_count or agreed_count > case_count:
        raise ValueError(
            f"counts exceed the suite: passed {passed_count}, agreed {agreed_count}, cases {case_count}"
        )
    if type(has_closed_residual) is not bool:
        raise TypeError("has_closed_residual must be a bool")
    phi1_exact = exact_defect_value("phi1", phi1)
    gamma2_exact = exact_defect_value("gamma2", gamma2)
    nonzero_defect = (phi1_exact is not None and phi1_exact != 0) or (
        gamma2_exact is not None and gamma2_exact != 0
    )
    if (
        case_count == 0
        or passed_count != case_count
        or agreed_count != case_count
        or defect_count > 0
        or nonzero_defect
    ):
        return TERMINAL_REFUSE
    if has_closed_residual:
        return TERMINAL_OPEN_RESIDUAL
    return TERMINAL_REFERENCE_SELF_CONSISTENT


def render_reference_report(
    task_key: str,
    verdict: str,
    stats: Mapping[str, Any],
    *,
    case_id: str | None = None,
) -> str:
    """Render the run report from the measured values in ``stats`` only.

    Recognised keys: total_cases, passed_count, agreements_count, defect_count
    (non-negative ints), phi_1 and gamma_2 (exact int or Fraction), and
    claim_hygiene (a mapping). A value that is absent is reported as such.
    """
    label = require_known_label(verdict)
    total = _optional_count(stats, "total_cases")
    passed = _optional_count(stats, "passed_count")
    agreed = _optional_count(stats, "agreements_count")
    defects = _optional_count(stats, "defect_count")
    phi1 = exact_defect_value("phi_1", stats.get("phi_1"))
    gamma2 = exact_defect_value("gamma_2", stats.get("gamma_2"))

    def shown(value: object, absent: str = "not reported") -> str:
        return absent if value is None else str(value)

    lines = [
        f"# Reference self-consistency report: {CHALLENGE_TITLE}",
        "",
        f"**Task key**: `{task_key}`  ",
    ]
    if case_id is not None:
        lines.append(f"**Case**: `{case_id}`  ")
    lines += [
        f"**Label**: `{label}`  ",
        f"**Scope**: `{GATE_SCOPE}`: the frozen reference solver scored against this package's own judge packet. "
        "No model was evaluated and this is not a Woland verdict.  ",
        "**AuthorityEffect**: None  ",
        f"**Timestamp**: {utc_timestamp_now()}  ",
        "",
        "## Measured values",
        "",
        "| Quantity | Value |",
        "| --- | --- |",
        f"| Judge cases scored | {shown(total)} |",
        f"| Cases with verdict PASS | {shown(passed)} |",
        f"| Cases with checker agreement | {shown(agreed)} |",
        f"| Defect count | {shown(defects)} |",
        f"| Phi_1 (exact) | {shown(phi1, 'not measured')} |",
        f"| Gamma_2 (exact) | {shown(gamma2, 'not measured')} |",
        "",
    ]
    claim_hygiene = stats.get("claim_hygiene")
    if isinstance(claim_hygiene, Mapping):
        lines += [
            "## Four-Part Claim Hygiene Summary",
            "",
            f"1. **Supports**: {claim_hygiene.get('supports', 'not stated')}",
            f"2. **Does not support**: {claim_hygiene.get('does_not_support', 'not stated')}",
            f"3. **Narrowest defensible claim**: {claim_hygiene.get('narrowest_defensible_claim', 'not stated')}",
            f"4. **Next test needed**: {claim_hygiene.get('next_test_needed', 'not stated')}",
            "",
        ]
    return "\n".join(lines)


def _require_labels(name: str, payload: Mapping[str, Any]) -> None:
    for key in _LABEL_KEYS:
        if key in payload:
            try:
                require_known_label(payload[key])
            except UnknownLabelError as error:
                raise UnknownLabelError(f"{name}.{key}={payload[key]!r}") from error


def _write_failure_receipt(staging_dir: Path, target_dir: Path, error: BaseException) -> None:
    payload = {
        "authority_effect": "None",
        "error_message": str(error),
        "error_type": type(error).__name__,
        "files_present": sorted(p.name for p in staging_dir.iterdir()),
        "status": "RUN_FAILED",
        "target_dir": target_dir.name,
        "timestamp_utc": utc_timestamp_now(),
    }
    (staging_dir / FAILURE_RECEIPT_NAME).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def persist_single_bundle(
    target_dir: Path,
    novella_md: str,
    dda_actions: Sequence[Mapping[str, Any]],
    summary_data: Mapping[str, Any],
    receipt_data: Mapping[str, Any],
) -> tuple[Path, dict[str, str]]:
    """Persist the four-file bundle into target_dir (staged beside it, then os.replace).

    On failure a failure_receipt.json is written and the staged files are moved
    into target_dir; if that move fails the staging directory is left in place.
    Nothing is deleted.
    """
    if target_dir.exists():
        raise RunFolderExistsError(f"Refusing to overwrite existing run directory: {target_dir}")
    parent_dir = target_dir.parent
    parent_dir.mkdir(parents=True, exist_ok=True)

    temp_dir = Path(tempfile.mkdtemp(prefix=f".{target_dir.name}.staging.", dir=str(parent_dir)))

    try:
        novella_bytes = novella_md.encode("utf-8")
        (temp_dir / "novella.md").write_bytes(novella_bytes)
        novella_sha256 = hashlib.sha256(novella_bytes).hexdigest()

        dda_lines = [json.dumps(dict(row), sort_keys=True) for row in dda_actions]
        dda_bytes = ("\n".join(dda_lines) + "\n").encode("utf-8") if dda_lines else b""
        (temp_dir / "dda_actions.jsonl").write_bytes(dda_bytes)
        dda_actions_sha256 = hashlib.sha256(dda_bytes).hexdigest()

        summary_payload = dict(summary_data)
        summary_payload["novella_sha256"] = novella_sha256
        summary_payload["dda_actions_sha256"] = dda_actions_sha256
        summary_bytes = (json.dumps(summary_payload, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        (temp_dir / "summary.json").write_bytes(summary_bytes)
        summary_sha256 = hashlib.sha256(summary_bytes).hexdigest()

        receipt_payload = dict(receipt_data)
        receipt_payload["novella_sha256"] = novella_sha256
        receipt_payload["dda_actions_sha256"] = dda_actions_sha256
        receipt_payload["summary_sha256"] = summary_sha256
        receipt_bytes = (json.dumps(receipt_payload, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        (temp_dir / "receipt.json").write_bytes(receipt_bytes)
        receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()
    except BaseException as error:
        try:
            _write_failure_receipt(temp_dir, target_dir, error)
            os.replace(temp_dir, target_dir)
        except OSError as custody_error:
            # The staging directory stays where it is; nothing is deleted.
            error.add_note(
                f"failure receipt not moved into place: {custody_error!r}; staging kept at {temp_dir}"
            )
        raise

    os.replace(temp_dir, target_dir)
    return target_dir, {
        "dda_actions_sha256": dda_actions_sha256,
        "novella_sha256": novella_sha256,
        "receipt_sha256": receipt_sha256,
        "summary_sha256": summary_sha256,
    }


class WolandGate:
    """Reference self-consistency gate for C032 (historical class name kept for callers).

    AuthorityEffect: None.
    """

    def __init__(
        self,
        task_key: str = CHALLENGE_ID,
        base_dir: Path | None = None,
    ) -> None:
        self.task_key = task_key
        # base_dir is the directory that contains ``_intelligence/``.
        self.base_dir = base_dir if base_dir is not None else resolve_intelligence_repo_root()
        self.woland_runs_root = self.base_dir / "_ic/darpa/woland" / "runs"
        self.symgam_runs_root = self.base_dir / "_ic/darpa/symbol_game" / "runs"
        self.last_bundle_digests: dict[str, str] = {}
        self.authority_effect = "None"

    def _run_parents(self) -> tuple[Path, Path]:
        clean_task = sanitize_run_key(self.task_key)
        return self.woland_runs_root / clean_task, self.symgam_runs_root / clean_task

    def determine_terminal_verdict(
        self,
        case_count: int,
        passed_count: int,
        agreed_count: int,
        *,
        defect_count: int = 0,
        phi1: Fraction | int | None = None,
        gamma2: Fraction | int | None = None,
        has_closed_residual: bool = False,
    ) -> str:
        """Return REFERENCE_SELF_CONSISTENT, REFERENCE_SELF_INCONSISTENT or OPEN_RESIDUAL."""
        return determine_terminal_verdict(
            case_count,
            passed_count,
            agreed_count,
            defect_count=defect_count,
            phi1=phi1,
            gamma2=gamma2,
            has_closed_residual=has_closed_residual,
        )

    def generate_novella(
        self,
        verdict: str,
        stats: Mapping[str, Any] | None = None,
        case_id: str | None = None,
    ) -> str:
        """Render the factual run report (kept under the historical method name)."""
        return render_reference_report(self.task_key, verdict, stats or {}, case_id=case_id)

    def persist_run_bundle(
        self,
        receipt: Mapping[str, Any],
        summary: Mapping[str, Any],
        dda_actions: Sequence[Mapping[str, Any]],
        novella: str,
    ) -> dict[str, Path]:
        """Persist the four-file bundle into a new run folder in each run store.

        Raises RunFolderExistsError if either destination exists and
        UnknownLabelError if the receipt or summary carries a label this gate
        does not emit.
        """
        _require_labels("receipt", receipt)
        _require_labels("summary", summary)
        run_name = f"{sanitize_run_key(self.task_key)}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
        woland_parent, symgam_parent = self._run_parents()
        woland_target = woland_parent / run_name
        symgam_target = symgam_parent / run_name
        for target_dir in (woland_target, symgam_target):
            if target_dir.exists():
                raise RunFolderExistsError(f"Target run folder already exists: {target_dir}")

        summary_payload = {**summary, "authority_effect": "None", "gate_scope": GATE_SCOPE}
        receipt_payload = {**receipt, "authority_effect": "None", "gate_scope": GATE_SCOPE}
        woland_dir, digests = persist_single_bundle(
            woland_target, novella, dda_actions, summary_payload, receipt_payload
        )
        symgam_dir, _ = persist_single_bundle(
            symgam_target, novella, dda_actions, summary_payload, receipt_payload
        )
        self.last_bundle_digests = digests
        return {
            "woland_run_dir": woland_dir,
            "symgam_run_dir": symgam_dir,
        }


__all__ = [
    "CANONICAL_OUTPUT_FILES",
    "CHALLENGE_ID",
    "FAILURE_RECEIPT_NAME",
    "GATE_SCOPE",
    "RUN_FOLDER_EXISTS",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_VERDICTS",
    "UNKNOWN_LABEL",
    "RunFolderExistsError",
    "UnknownLabelError",
    "WolandGate",
    "determine_terminal_verdict",
    "exact_defect_value",
    "exact_wire",
    "persist_single_bundle",
    "render_reference_report",
    "require_known_label",
    "sanitize_run_key",
]
