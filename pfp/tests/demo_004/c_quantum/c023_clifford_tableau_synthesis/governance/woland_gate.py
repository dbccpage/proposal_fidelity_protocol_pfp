"""Reference self-consistency gate and run-folder persistence for C023 (Clifford Tableau Synthesis).

AuthorityEffect: None.

This gate scores the frozen reference solver against this package's own judge
packet. It evaluates no model and it is not a Woland verdict: the Woland swarm
(``omega_engine_woland``) is the only final evaluator. Its labels are:

- REFERENCE_SELF_CONSISTENT: at least one case was scored, every case has an
  admitted status and ``checker_pass is True``, and every exact defect value
  that was measured is zero.
- REFERENCE_SELF_INCONSISTENT: anything else, including an empty suite.
- OPEN_RESIDUAL: reserved label (this gate does not emit it).

Run folders hold a four-file bundle (report written as novella.md,
dda_actions.jsonl, summary.json, receipt.json). Every value in the bundle is
derived from the inputs; nothing is templated. ``intelligence_root`` is the
``_ic`` folder itself; by default it is
``resolve_intelligence_repo_root() / "_ic"``. Each bundle is staged
beside its destination and moved into place with os.replace. An existing
destination always raises RunFolderExistsError. If writing fails, a
failure_receipt.json is written and the staged files are moved into the run
folder anyway: nothing under ``_ic/`` is ever deleted.
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

CHALLENGE_ID = "c023_clifford_tableau_synthesis"
CHALLENGE_TITLE = "C023 (Clifford Tableau Synthesis)"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
TERMINAL_REFUSE = "REFERENCE_SELF_INCONSISTENT"
TERMINAL_OPEN_RESIDUAL = "OPEN_RESIDUAL"
TERMINAL_VERDICTS = (TERMINAL_REFERENCE_SELF_CONSISTENT, TERMINAL_REFUSE, TERMINAL_OPEN_RESIDUAL)

ADMITTED_CASE_STATUSES = ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN")

RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
FAILURE_RECEIPT_NAME = "failure_receipt.json"
BUNDLE_FILE_ORDER = ("novella.md", "dda_actions.jsonl", "summary.json", "receipt.json")


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
        clean = "c023_run"
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


def _max_measured(name: str, case_results: Sequence[Mapping[str, Any]]) -> Fraction | None:
    measured = [
        v for v in (exact_defect_value(name, r.get(name)) for r in case_results) if v is not None
    ]
    return max(measured) if measured else None


def generate_c023_novella(
    task_key: str,
    verdict: str,
    case_count: int,
    passed_count: int,
    defect_count: int,
    phi1: Fraction | int | None,
    gamma2: Fraction | int | None,
    claim_hygiene: Mapping[str, str],
) -> str:
    """Render the run report from measured values only (kept under the historical function name)."""
    phi1_exact = exact_defect_value("phi1", phi1)
    gamma2_exact = exact_defect_value("gamma2", gamma2)
    narrowest = claim_hygiene.get(
        "narrowest_defensible_claim", claim_hygiene.get("narrowest_claim", "not stated")
    )
    next_test = claim_hygiene.get("next_test_needed", claim_hygiene.get("next_test", "not stated"))
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
        f"| Cases accepted by the dual evaluator | {passed_count} |",
        f"| Cases not accepted | {defect_count} |",
        f"| Largest Phi_1 (exact) | {'not measured' if phi1_exact is None else phi1_exact} |",
        f"| Largest Gamma_2 (exact) | {'not measured' if gamma2_exact is None else gamma2_exact} |",
        "",
        "## Four-Part Claim Hygiene Summary",
        "",
        f"1. **Supports**: {claim_hygiene.get('supports', 'not stated')}",
        f"2. **Does not support**: {claim_hygiene.get('does_not_support', 'not stated')}",
        f"3. **Narrowest defensible claim**: {narrowest}",
        f"4. **Next test needed**: {next_test}",
        "",
    ]
    return "\n".join(lines)


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


def write_bundle(target_dir: Path, files: Mapping[str, bytes]) -> Path:
    """Stage the bundle beside target_dir, then os.replace it into place.

    On failure a failure_receipt.json is written and the staged files are moved
    into target_dir; if that move fails the staging directory is left in place.
    Nothing is deleted.
    """
    if target_dir.exists():
        raise RunFolderExistsError(f"Run folder already exists: {target_dir}")
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{target_dir.name}.staging.", dir=str(target_dir.parent))
    )
    try:
        for name in BUNDLE_FILE_ORDER:
            (staging_dir / name).write_bytes(files[name])
    except BaseException as error:
        try:
            _write_failure_receipt(staging_dir, target_dir, error)
            os.replace(staging_dir, target_dir)
        except OSError as custody_error:
            error.add_note(
                f"failure receipt not moved into place: {custody_error!r}; staging kept at {staging_dir}"
            )
        raise
    os.replace(staging_dir, target_dir)
    return target_dir


class WolandGate:
    """Reference self-consistency gate and run-folder writer for C023 (historical class name kept).

    AuthorityEffect: None.
    """

    def __init__(
        self,
        intelligence_root: Path | None = None,
        challenge_id: str = CHALLENGE_ID,
    ) -> None:
        self.challenge_id = challenge_id
        if intelligence_root is None:
            self.intelligence_root = resolve_intelligence_repo_root() / "_ic"
        else:
            self.intelligence_root = Path(intelligence_root)

        self.woland_runs_dir = self.intelligence_root / "darpa/woland/runs"
        self.symbol_game_runs_dir = self.intelligence_root / "darpa/symbol_game/runs"

    def judge(self, case_results: Sequence[Mapping[str, Any]]) -> str:
        """Return REFERENCE_SELF_CONSISTENT or REFERENCE_SELF_INCONSISTENT from exact per-case results.

        An empty suite is inconsistent. ``checker_pass`` must be the bool True.
        ``phi1``/``gamma2`` per case are exact (int or Fraction) or None when not
        measured; any measured non-zero value is inconsistent, with no tolerance.
        """
        if not case_results:
            return TERMINAL_REFUSE

        verdict = TERMINAL_REFERENCE_SELF_CONSISTENT
        for res in case_results:
            phi1 = exact_defect_value("phi1", res.get("phi1"))
            gamma2 = exact_defect_value("gamma2", res.get("gamma2"))
            if res.get("status") not in ADMITTED_CASE_STATUSES:
                verdict = TERMINAL_REFUSE
            elif res.get("checker_pass") is not True:
                verdict = TERMINAL_REFUSE
            elif (phi1 is not None and phi1 != 0) or (gamma2 is not None and gamma2 != 0):
                verdict = TERMINAL_REFUSE
        return verdict

    def persist_run(
        self,
        task_key: str,
        case_results: Sequence[Mapping[str, Any]],
        dda_events: Sequence[Mapping[str, Any]],
        accounting: Mapping[str, Any],
        claim_hygiene: Mapping[str, str],
        *,
        force_clean: bool = False,
    ) -> dict[str, Any]:
        """Persist the four-file bundle to both run stores (reverse write order).

        ``force_clean`` is accepted for compatibility and deletes nothing: an
        existing destination always raises RunFolderExistsError.
        """
        del force_clean
        safe_key = sanitize_run_key(task_key)
        woland_dest = self.woland_runs_dir / safe_key
        symbol_game_dest = self.symbol_game_runs_dir / safe_key

        if woland_dest.exists():
            raise RunFolderExistsError(f"Run folder already exists: {woland_dest}")
        if symbol_game_dest.exists():
            raise RunFolderExistsError(f"Run folder already exists: {symbol_game_dest}")

        verdict = self.judge(case_results)
        case_count = len(case_results)
        passed_count = sum(1 for r in case_results if r.get("checker_pass") is True)
        defect_count = case_count - passed_count
        phi1 = _max_measured("phi1", case_results)
        gamma2 = _max_measured("gamma2", case_results)

        # File 1: novella.md (measured-value report)
        novella_bytes = generate_c023_novella(
            task_key=safe_key,
            verdict=verdict,
            case_count=case_count,
            passed_count=passed_count,
            defect_count=defect_count,
            phi1=phi1,
            gamma2=gamma2,
            claim_hygiene=claim_hygiene,
        ).encode("utf-8")
        novella_sha256 = hashlib.sha256(novella_bytes).hexdigest()

        # File 2: dda_actions.jsonl (hash-chained measured events)
        running_sha = "0" * 64
        dda_lines: list[str] = []
        for ev in dda_events:
            ev_dict = dict(ev)
            ev_dict["parent_sha256"] = running_sha
            ev_bytes = json.dumps(ev_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")
            running_sha = hashlib.sha256(ev_bytes).hexdigest()
            ev_dict["event_sha256"] = running_sha
            dda_lines.append(json.dumps(ev_dict, sort_keys=True, separators=(",", ":")) + "\n")
        dda_bytes = "".join(dda_lines).encode("utf-8")
        dda_actions_sha256 = hashlib.sha256(dda_bytes).hexdigest()
        dda_head_sha256 = running_sha

        # File 3: summary.json
        summary_data = {
            "accounting": dict(accounting),
            "authority_effect": "None",
            "cases_evaluated": case_count,
            "cases_passed": passed_count,
            "challenge_id": self.challenge_id,
            "claim_hygiene": dict(claim_hygiene),
            "dda_event_count": len(dda_lines),
            "defects_encountered": defect_count,
            "gate_scope": GATE_SCOPE,
            "max_gamma2": exact_wire(gamma2),
            "max_phi1": exact_wire(phi1),
            "protocol": "SG-CP v1",
            "task_key": safe_key,
            "timestamp_utc": utc_timestamp_now(),
            "verdict": verdict,
        }
        summary_bytes = (json.dumps(summary_data, indent=2, sort_keys=True) + "\n").encode("utf-8")
        summary_sha256 = hashlib.sha256(summary_bytes).hexdigest()

        # File 4: receipt.json (binds the three digests above)
        receipt_data = {
            "authority_effect": "None",
            "challenge_id": self.challenge_id,
            "dda_actions_sha256": dda_actions_sha256,
            "dda_head_sha256": dda_head_sha256,
            "gate_scope": GATE_SCOPE,
            "novella_sha256": novella_sha256,
            "receipt_version": "1.0",
            "summary_sha256": summary_sha256,
            "task_key": safe_key,
            "timestamp_utc": utc_timestamp_now(),
            "verdict": verdict,
        }
        receipt_bytes = (json.dumps(receipt_data, indent=2, sort_keys=True) + "\n").encode("utf-8")
        receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest()

        files = {
            "novella.md": novella_bytes,
            "dda_actions.jsonl": dda_bytes,
            "summary.json": summary_bytes,
            "receipt.json": receipt_bytes,
        }
        write_bundle(woland_dest, files)
        write_bundle(symbol_game_dest, files)

        return {
            "dda_actions_sha256": dda_actions_sha256,
            "dda_head_sha256": dda_head_sha256,
            "gate_scope": GATE_SCOPE,
            "novella_sha256": novella_sha256,
            "receipt_sha256": receipt_sha256,
            "summary_sha256": summary_sha256,
            "symbol_game_run_dir": str(symbol_game_dest),
            "task_key": safe_key,
            "verdict": verdict,
            "woland_run_dir": str(woland_dest),
        }


__all__ = [
    "ADMITTED_CASE_STATUSES",
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
    "generate_c023_novella",
    "sanitize_run_key",
    "write_bundle",
]
