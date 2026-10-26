"""Reference self-consistency gate and run-folder persistence for C014 (Exact Discrete Hodge Decomposition).

AuthorityEffect: None.

This gate scores the frozen reference solver against this package's own judge
packet. It evaluates no model and it is not a Woland verdict: the Woland swarm
(``omega_engine_woland``) is the only final evaluator. Its labels are:

- REFERENCE_SELF_CONSISTENT: at least one case was scored, every case passed
  with checker agreement, the reported defect count is zero and every exact
  defect value that was measured is zero.
- REFERENCE_SELF_INCONSISTENT: anything else, including an empty suite.
- OPEN_RESIDUAL: consistent, but the caller declared a closed residual.

Run folders hold a four-file bundle (report.md written as novella.md,
dda_actions.jsonl, summary.json, receipt.json). Every value in the bundle is
derived from the inputs; nothing is templated. The bundle is staged beside the
destination and moved into place with os.replace. If writing fails, a
failure_receipt.json is written and the staged files are moved into the run
folder anyway: nothing under ``_intelligence/`` is ever deleted.
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

CHALLENGE_ID = "c014_discrete_hodge_decomposition"
CHALLENGE_TITLE = "C014 (Exact Discrete Hodge Decomposition)"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
TERMINAL_VERDICTS = (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE, TERMINAL_OPEN_RESIDUAL)

RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
FAILURE_RECEIPT_NAME = "failure_receipt.json"


class RunFolderExistsError(FileExistsError):
    """Raised when attempting to overwrite an existing run directory."""

    def __init__(self, message: str) -> None:
        self.code = RUN_FOLDER_EXISTS
        super().__init__(f"{RUN_FOLDER_EXISTS}: {message}")


def utc_timestamp_now() -> str:
    """Returns canonical UTC ISO timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def sanitize_run_key(key: str) -> str:
    """Sanitizes run key for directory safety while preserving deterministic naming."""
    clean = key.strip().replace(" ", "_").replace(":", "-").replace("/", "_").replace("\\", "_")
    if not clean:
        clean = "c014_run"
    return clean


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


def generate_c014_novella(
    task_key: str,
    verdict: str,
    case_count: int,
    passed_count: int,
    defect_count: int,
    phi1: Fraction | int | None,
    gamma2: Fraction | int | None,
    claim_hygiene: Mapping[str, str],
    *,
    agreement_count: int | None = None,
    has_closed_residual: bool = False,
) -> str:
    """Render the run report from measured values only (kept under the historical function name)."""
    phi1_exact = exact_defect_value("phi1", phi1)
    gamma2_exact = exact_defect_value("gamma2", gamma2)
    lines = [
        f"# Reference self-consistency report: {CHALLENGE_TITLE}",
        "",
        f"**Task key**: `{task_key}`  ",
        f"**Label**: `{verdict}`  ",
        f"**Scope**: `{GATE_SCOPE}`: the frozen reference solver scored against this package's own judge packet. "
        "No model was evaluated and this is not a Woland verdict.  ",
        "**AuthorityEffect**: None  ",
        f"**Timestamp**: {utc_timestamp_now()}  ",
        "",
        "## Measured values",
        "",
        "| Quantity | Value |",
        "| --- | --- |",
        f"| Judge cases scored | {case_count} |",
        f"| Cases with verdict PASS | {passed_count} |",
        f"| Cases with checker agreement | {'not reported' if agreement_count is None else agreement_count} |",
        f"| Defect count reported by the runner | {defect_count} |",
        f"| Phi_1 (exact) | {'not measured' if phi1_exact is None else phi1_exact} |",
        f"| Gamma_2 (exact) | {'not measured' if gamma2_exact is None else gamma2_exact} |",
        f"| Closed residual declared | {'yes' if has_closed_residual else 'no'} |",
        "",
        "## Four-Part Claim Hygiene Summary",
        "",
        f"1. **Supports**: {claim_hygiene.get('supports', 'not stated')}",
        f"2. **Does not support**: {claim_hygiene.get('does_not_support', 'not stated')}",
        f"3. **Narrowest defensible claim**: {claim_hygiene.get('narrowest_defensible_claim', 'not stated')}",
        f"4. **Next test needed**: {claim_hygiene.get('next_test_needed', 'not stated')}",
        "",
    ]
    return "\n".join(lines)


def generate_c014_dda_steps(
    task_key: str,
    verdict: str,
    case_count: int,
    defect_count: int,
    *,
    passed_count: int | None = None,
    agreement_count: int | None = None,
) -> list[dict[str, Any]]:
    """Hash-chained DDC steps whose payloads are the measured values of this run."""
    step_defs = [
        ("C", "intake_judge_cases", {"case_count": case_count}),
        (
            "R",
            "score_reference_outputs",
            {
                "agreement_count": agreement_count,
                "defect_count": defect_count,
                "passed_count": passed_count,
            },
        ),
        ("T", "emit_self_consistency_label", {"label": verdict, "scope": GATE_SCOPE}),
    ]

    steps: list[dict[str, Any]] = []
    prev_hash = "0" * 64
    for idx, (letter, action, payload) in enumerate(step_defs):
        item = {
            "step_id": idx,
            "task_key": task_key,
            "timestamp_utc": utc_timestamp_now(),
            "letter": letter,
            "action": action,
            "payload": payload,
            "authority_effect": "None",
            "parent_sha256": prev_hash,
        }
        item_bytes = json.dumps(item, sort_keys=True, separators=(",", ":")).encode("utf-8")
        step_hash = hashlib.sha256(item_bytes).hexdigest()
        item["step_hash"] = step_hash
        steps.append(item)
        prev_hash = step_hash

    return steps


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
    dda_steps: Sequence[Mapping[str, Any]],
    summary_data: Mapping[str, Any],
    receipt_data: Mapping[str, Any],
) -> tuple[Path, dict[str, str]]:
    """Persist the 4-file bundle into target_dir (reverse write order, atomic rename).

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

        dda_lines = [json.dumps(s, sort_keys=True) for s in dda_steps]
        dda_bytes = ("\n".join(dda_lines) + "\n").encode("utf-8") if dda_lines else b""
        (temp_dir / "dda_actions.jsonl").write_bytes(dda_bytes)
        dda_actions_sha256 = hashlib.sha256(dda_bytes).hexdigest()
        dda_head_sha256 = dda_steps[-1].get("step_hash") if dda_steps else None

        summary_payload = dict(summary_data)
        summary_payload["novella_sha256"] = novella_sha256
        summary_payload["dda_actions_sha256"] = dda_actions_sha256
        if dda_head_sha256 is not None:
            summary_payload["dda_head_sha256"] = dda_head_sha256
        summary_payload["authority_effect"] = "None"
        summary_bytes = (json.dumps(summary_payload, indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        (temp_dir / "summary.json").write_bytes(summary_bytes)
        summary_sha256 = hashlib.sha256(summary_bytes).hexdigest()

        receipt_payload = dict(receipt_data)
        receipt_payload["novella_sha256"] = novella_sha256
        receipt_payload["dda_actions_sha256"] = dda_actions_sha256
        receipt_payload["summary_sha256"] = summary_sha256
        if dda_head_sha256 is not None:
            receipt_payload["dda_head_sha256"] = dda_head_sha256
        receipt_payload["authority_effect"] = "None"
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
    digests = {
        "novella_sha256": novella_sha256,
        "dda_actions_sha256": dda_actions_sha256,
        "summary_sha256": summary_sha256,
        "receipt_sha256": receipt_sha256,
        "dda_head_sha256": dda_head_sha256 or "",
    }
    return target_dir, digests


def persist_woland_run_bundle(
    task_key: str,
    run_id: str,
    novella_md: str,
    dda_steps: Sequence[Mapping[str, Any]],
    summary_data: Mapping[str, Any],
    receipt_data: Mapping[str, Any],
    base_repo_root: Path | None = None,
) -> tuple[Path, Path, dict[str, str]]:
    """Persist the bundle into the _woland and symbol_game run stores under the intelligence root."""
    repo_root = base_repo_root if base_repo_root is not None else resolve_intelligence_repo_root()

    clean_task_key = sanitize_run_key(task_key)
    clean_run_id = sanitize_run_key(run_id)

    woland_runs_dir = repo_root / "_ic/darpa/woland" / "runs" / clean_task_key
    symbol_game_runs_dir = repo_root / "_ic/darpa/symbol_game" / "runs" / clean_run_id

    if woland_runs_dir.exists():
        raise RunFolderExistsError(f"Woland run directory already exists: {woland_runs_dir}")
    if symbol_game_runs_dir.exists():
        raise RunFolderExistsError(
            f"Symbol Game run directory already exists: {symbol_game_runs_dir}"
        )

    path_woland, digests = persist_single_bundle(
        woland_runs_dir, novella_md, dda_steps, summary_data, receipt_data
    )
    path_sg, _ = persist_single_bundle(
        symbol_game_runs_dir, novella_md, dda_steps, summary_data, receipt_data
    )

    return path_woland, path_sg, digests


class WolandGate:
    """Reference self-consistency gate for C014 (historical class name kept for callers).

    AuthorityEffect: None.
    """

    def __init__(
        self, base_repo_root: Path | None = None, challenge_id: str = CHALLENGE_ID
    ) -> None:
        self.base_repo_root: Path | None = base_repo_root
        self.challenge_id: str = challenge_id
        self.authority_effect: str = "None"

    def determine_terminal_verdict(
        self,
        case_results: Sequence[Mapping[str, Any]],
        *,
        defect_count: int = 0,
        phi1: Fraction | int | None = None,
        gamma2: Fraction | int | None = None,
        has_closed_residual: bool = False,
    ) -> str:
        """Return REFERENCE_SELF_CONSISTENT, REFERENCE_SELF_INCONSISTENT or OPEN_RESIDUAL.

        An empty suite is inconsistent. Defect values are exact: any measured
        non-zero Phi_1 or Gamma_2 is inconsistent, with no tolerance.
        """
        _require_count("defect_count", defect_count)
        if type(has_closed_residual) is not bool:
            raise TypeError("has_closed_residual must be a bool")
        phi1_exact = exact_defect_value("phi1", phi1)
        gamma2_exact = exact_defect_value("gamma2", gamma2)

        all_passed = (
            len(case_results) > 0
            and all(r.get("verdict") == "PASS" for r in case_results)
            and all(r.get("agreement") is True for r in case_results)
        )
        nonzero_defect = (phi1_exact is not None and phi1_exact != 0) or (
            gamma2_exact is not None and gamma2_exact != 0
        )
        if defect_count > 0 or not all_passed or nonzero_defect:
            return TERMINAL_REFUSE
        if has_closed_residual:
            return TERMINAL_OPEN_RESIDUAL
        return TERMINAL_REFERENCE_SELF_CONSISTENT

    def evaluate_and_persist(
        self,
        task_key: str,
        run_id: str,
        case_results: Sequence[Mapping[str, Any]],
        claim_hygiene: Mapping[str, str],
        *,
        defect_count: int = 0,
        phi1: Fraction | int | None = None,
        gamma2: Fraction | int | None = None,
        has_closed_residual: bool = False,
        budget_accounting: Mapping[str, Any] | None = None,
    ) -> tuple[str, Path, Path, dict[str, str]]:
        """Label the run and persist the bundle to both run stores."""
        verdict = self.determine_terminal_verdict(
            case_results,
            defect_count=defect_count,
            phi1=phi1,
            gamma2=gamma2,
            has_closed_residual=has_closed_residual,
        )

        case_count = len(case_results)
        passed_count = sum(1 for r in case_results if r.get("verdict") == "PASS")
        agreement_count = sum(1 for r in case_results if r.get("agreement") is True)
        phi1_wire = exact_wire(exact_defect_value("phi1", phi1))
        gamma2_wire = exact_wire(exact_defect_value("gamma2", gamma2))

        novella_md = generate_c014_novella(
            task_key=task_key,
            verdict=verdict,
            case_count=case_count,
            passed_count=passed_count,
            defect_count=defect_count,
            phi1=phi1,
            gamma2=gamma2,
            claim_hygiene=claim_hygiene,
            agreement_count=agreement_count,
            has_closed_residual=has_closed_residual,
        )

        dda_steps = generate_c014_dda_steps(
            task_key=task_key,
            verdict=verdict,
            case_count=case_count,
            defect_count=defect_count,
            passed_count=passed_count,
            agreement_count=agreement_count,
        )

        summary_data: dict[str, Any] = {
            "agreement_count": agreement_count,
            "authority_effect": "None",
            "challenge_id": self.challenge_id,
            "claim_hygiene": dict(claim_hygiene),
            "defect_count": defect_count,
            "gamma2": gamma2_wire,
            "gate_scope": GATE_SCOPE,
            "has_closed_residual": has_closed_residual,
            "passed_count": passed_count,
            "phi1": phi1_wire,
            "run_id": run_id,
            "task_key": task_key,
            "timestamp_utc": utc_timestamp_now(),
            "total_cases": case_count,
            "verdict": verdict,
        }
        if budget_accounting is not None:
            summary_data["budget_accounting"] = dict(budget_accounting)

        receipt_data: dict[str, Any] = {
            "agreement_count": agreement_count,
            "authority_effect": "None",
            "bout_id": task_key,
            "case_count": case_count,
            "challenge_id": self.challenge_id,
            "defect_count": defect_count,
            "gamma2": gamma2_wire,
            "gate_scope": GATE_SCOPE,
            "has_closed_residual": has_closed_residual,
            "passed_count": passed_count,
            "phi1": phi1_wire,
            "protocol": "SG-CP v1",
            "run_id": run_id,
            "timestamp_utc": utc_timestamp_now(),
            "verdict": verdict,
        }
        if budget_accounting is not None and "spent_microusd" in budget_accounting:
            receipt_data["spent_microusd"] = budget_accounting["spent_microusd"]

        path_woland, path_sg, digests = persist_woland_run_bundle(
            task_key=task_key,
            run_id=run_id,
            novella_md=novella_md,
            dda_steps=dda_steps,
            summary_data=summary_data,
            receipt_data=receipt_data,
            base_repo_root=self.base_repo_root,
        )

        return verdict, path_woland, path_sg, digests


__all__ = [
    "CHALLENGE_ID",
    "FAILURE_RECEIPT_NAME",
    "GATE_SCOPE",
    "RUN_FOLDER_EXISTS",
    "RunFolderExistsError",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_VERDICTS",
    "WolandGate",
    "exact_defect_value",
    "exact_wire",
    "generate_c014_dda_steps",
    "generate_c014_novella",
    "persist_single_bundle",
    "persist_woland_run_bundle",
    "sanitize_run_key",
]
