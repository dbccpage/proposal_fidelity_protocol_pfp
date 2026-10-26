"""Commit-reveal runner for C014 (Exact Discrete Hodge Decomposition).

AuthorityEffect: None.

Three phases (SG-CP v1), all of which score the frozen reference solver against
this package's own judge packet (a self-consistency check, not a model
evaluation and not a Woland verdict):

  * Phase 1 verifies every entry of judge_packet/manifest.json against the files
    on disk and records the manifest digest in commitments/c014_judge_commitment.json.
  * Phase 2 records digests of the reference solver files in
    commitments/c014_freeze_record.json.
  * Phase 3 re-verifies the manifest file, every manifest entry and every frozen
    solver file, refuses judge case files that the manifest does not list,
    scores the solver with both checkers, labels the run with the reference
    self-consistency gate and writes commitments/c014_scoring_receipt.json.

All digests are SHA-256 over file bytes with CRLF normalised to LF, so they
equal git-blob content on every platform. Receipts are written atomically
(temporary file plus os.replace). If Phase 3 crashes, a failure receipt is
written next to the scoring receipt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_file_path = Path(__file__).resolve()
for _parent in _file_path.parents:
    if (_parent / "omega_engine_projects").exists() and (
        _parent / "omega_engine_providers"
    ).exists():
        _root_str = str(_parent)
        if _root_str not in sys.path:
            sys.path.insert(0, _root_str)
        break

try:
    from .budget_gate import BudgetGate
    from .woland_gate import WolandGate
except (ImportError, ValueError):
    try:
        from budget_gate import BudgetGate
        from woland_gate import WolandGate
    except (ImportError, ValueError):
        from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c014_discrete_hodge_decomposition.governance.budget_gate import (
            BudgetGate,
        )
        from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c014_discrete_hodge_decomposition.governance.woland_gate import (
            WolandGate,
        )

try:
    from ..judge_packet.checkers.dual_evaluator import evaluate_dual
except (ImportError, ValueError):
    try:
        from judge_packet.checkers.dual_evaluator import evaluate_dual
    except (ImportError, ValueError):
        from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c014_discrete_hodge_decomposition.judge_packet.checkers.dual_evaluator import (
            evaluate_dual,
        )

try:
    from ..reference_solver.solver import solve
except (ImportError, ValueError):
    try:
        from reference_solver.solver import solve
    except (ImportError, ValueError):
        from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c014_discrete_hodge_decomposition.reference_solver.solver import (
            solve,
        )

CHALLENGE_ID = "c014_discrete_hodge_decomposition"
FILE_PREFIX = "c014"

SOLVER_FILES_TO_FREEZE: list[str] = [
    "reference_solver/ddc_tracer.py",
    "reference_solver/discrete_hodge.py",
    "reference_solver/solver.py",
]

JUDGE_CASE_DIRS: tuple[str, ...] = ("base", "controls", "poisoned")


class ManifestCustodyError(ValueError):
    """A judge manifest, manifest entry, case file or frozen file failed custody checks."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def utc_now() -> str:
    """Returns canonical ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def lf_normalized_bytes(path: Path) -> bytes:
    """File bytes with CRLF normalised to LF, so digests equal git-blob content."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_of_file(path: Path) -> str:
    """SHA-256 of the LF-normalised file bytes."""
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON through a temporary file in the same directory and os.replace it into place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(tmp_name, path)


def manifest_entries(manifest: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Return (relative path, sha256) pairs from any of the manifest layouts used in this package."""
    for key in ("files", "manifest", "entries"):
        raw = manifest.get(key)
        if isinstance(raw, list):
            return [(str(entry["path"]), str(entry["sha256"])) for entry in raw]
        if isinstance(raw, dict):
            return [
                (str(rel), str(value["sha256"] if isinstance(value, Mapping) else value))
                for rel, value in raw.items()
            ]
    raise ManifestCustodyError(
        "MANIFEST_HAS_NO_ENTRIES", "no files/manifest/entries list in the judge manifest"
    )


def verify_manifest_entries(manifest_file: Path, challenge_root: Path) -> set[Path]:
    """Verify every manifest entry against the LF-normalised bytes on disk; return the verified paths."""
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries = manifest_entries(manifest)
    if not entries:
        raise ManifestCustodyError("MANIFEST_HAS_NO_ENTRIES", f"{manifest_file} lists no files")
    verified: set[Path] = set()
    for rel, expected in entries:
        candidate = manifest_file.parent / rel
        path = candidate if candidate.is_file() else challenge_root / rel
        if not path.is_file():
            raise ManifestCustodyError("MANIFEST_ENTRY_MISSING", f"{rel} is listed but absent")
        actual = sha256_of_file(path)
        if actual != expected:
            raise ManifestCustodyError(
                "MANIFEST_ENTRY_MISMATCH", f"{rel}: expected {expected}, got {actual}"
            )
        verified.add(path.resolve())
    return verified


def reference_claim_hygiene(
    verdict: str, total: int, passed: int, agreements: int
) -> dict[str, str]:
    """Claim hygiene derived from the measured counts of this run."""
    return {
        "supports": (
            f"The frozen reference solver's outputs were accepted on {passed}/{total} judge cases, "
            f"with checker agreement on {agreements}/{total}."
        ),
        "does_not_support": (
            "Any statement about a model (none was evaluated), about checker soundness or independence, "
            "or a Woland verdict."
        ),
        "narrowest_defensible_claim": (
            f"Reference self-consistency label {verdict} on the {total} judge case files that match the committed manifest."
        ),
        "next_test_needed": (
            "Score a participant submission under a commitment made before the run and have the Woland swarm "
            "evaluate the bound checker receipts."
        ),
    }


class CommitRevealRunner:
    """Orchestrates the three-phase reference self-consistency run for C014.

    AuthorityEffect: None.
    """

    def __init__(
        self,
        challenge_root: Path | None = None,
        base_repo_root: Path | None = None,
        budget_gate: BudgetGate | None = None,
        woland_gate: WolandGate | None = None,
    ) -> None:
        self.challenge_root: Path = (
            challenge_root if challenge_root is not None else Path(__file__).resolve().parent.parent
        )
        self.commitments_dir: Path = self.challenge_root / "commitments"
        self.judge_dir: Path = self.challenge_root / "judge_packet"
        self.manifest_file: Path = self.judge_dir / "manifest.json"

        self.phase1_file: Path = self.commitments_dir / f"{FILE_PREFIX}_judge_commitment.json"
        self.phase2_file: Path = self.commitments_dir / f"{FILE_PREFIX}_freeze_record.json"
        self.phase3_file: Path = self.commitments_dir / f"{FILE_PREFIX}_scoring_receipt.json"
        self.failure_file: Path = (
            self.commitments_dir / f"{FILE_PREFIX}_scoring_failure_receipt.json"
        )

        self.budget_gate: BudgetGate = budget_gate if budget_gate is not None else BudgetGate()
        self.woland_gate: WolandGate = (
            woland_gate if woland_gate is not None else WolandGate(base_repo_root=base_repo_root)
        )
        self.authority_effect: str = "None"

    def run_phase1_commit_judge(self) -> dict[str, Any]:
        """Phase 1: verify every manifest entry, then record the manifest digest."""
        if not self.manifest_file.is_file():
            raise FileNotFoundError(f"Judge manifest missing: {self.manifest_file}")

        verified = verify_manifest_entries(self.manifest_file, self.challenge_root)
        manifest_digest = sha256_of_file(self.manifest_file)

        commitment_payload = {
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "digest_normalization": "CRLF_TO_LF",
            "file_count": len(verified),
            "manifest_path": "judge_packet/manifest.json",
            "manifest_sha256": manifest_digest,
            "phase": "PHASE_1_OPERATOR_JUDGE_COMMITMENT",
            "protocol": "SG-CP v1",
            "timestamp_utc": utc_now(),
        }
        atomic_write_json(self.phase1_file, commitment_payload)
        return commitment_payload

    def run_phase2_freeze_solver(self) -> dict[str, Any]:
        """Phase 2: record digests of the reference solver files."""
        if not self.phase1_file.is_file():
            raise RuntimeError("Phase 1 commitment required before Phase 2 freeze")

        phase1_data = json.loads(self.phase1_file.read_text(encoding="utf-8"))
        p1_digest = phase1_data["manifest_sha256"]

        solver_file_records: list[dict[str, Any]] = []
        combined_hasher = hashlib.sha256()

        for rel_path in sorted(SOLVER_FILES_TO_FREEZE):
            full_path = self.challenge_root / rel_path
            if not full_path.is_file():
                raise FileNotFoundError(f"Solver file not found for freeze: {full_path}")
            data = lf_normalized_bytes(full_path)
            digest = hashlib.sha256(data).hexdigest()
            solver_file_records.append(
                {
                    "path": rel_path,
                    "sha256": digest,
                    "size_bytes": len(data),
                }
            )
            combined_hasher.update(digest.encode("utf-8"))

        freeze_payload = {
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "digest_normalization": "CRLF_TO_LF",
            "freeze_sha256": combined_hasher.hexdigest(),
            "phase": "PHASE_2_SOLVER_FREEZE_RECORD",
            "phase1_binding_sha256": p1_digest,
            "protocol": "SG-CP v1",
            "solver_files": solver_file_records,
            "timestamp_utc": utc_now(),
        }
        atomic_write_json(self.phase2_file, freeze_payload)
        return freeze_payload

    def run_phase3_reveal_and_score(
        self,
        *,
        task_key: str | None = None,
        run_id: str | None = None,
        persist_woland: bool = True,
    ) -> dict[str, Any]:
        """Phase 3: verify custody, score the frozen solver and label the run.

        A crash writes a failure receipt before the exception propagates.
        """
        try:
            return self._run_phase3(task_key=task_key, run_id=run_id, persist_woland=persist_woland)
        except BaseException as error:
            atomic_write_json(
                self.failure_file,
                {
                    "authority_effect": "None",
                    "challenge_id": CHALLENGE_ID,
                    "error_code": getattr(error, "code", None),
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                    "phase": "PHASE_3_REVEAL_AND_SCORING_FAILED",
                    "protocol": "SG-CP v1",
                    "task_key": task_key,
                    "timestamp_utc": utc_now(),
                },
            )
            raise

    def _run_phase3(
        self,
        *,
        task_key: str | None,
        run_id: str | None,
        persist_woland: bool,
    ) -> dict[str, Any]:
        if not self.phase1_file.is_file():
            raise RuntimeError("Phase 1 commitment required before Phase 3 scoring")
        if not self.phase2_file.is_file():
            raise RuntimeError("Phase 2 freeze required before Phase 3 scoring")

        # 1. Custody: manifest file, every manifest entry, every frozen solver file.
        current_manifest_sha = sha256_of_file(self.manifest_file)
        phase1_data = json.loads(self.phase1_file.read_text(encoding="utf-8"))
        if current_manifest_sha != phase1_data["manifest_sha256"]:
            raise ManifestCustodyError(
                "MANIFEST_DIGEST_MISMATCH",
                f"Judge manifest tampered! Expected {phase1_data['manifest_sha256']}, got {current_manifest_sha}",
            )
        verified_paths = verify_manifest_entries(self.manifest_file, self.challenge_root)

        phase2_data = json.loads(self.phase2_file.read_text(encoding="utf-8"))
        for rec in phase2_data["solver_files"]:
            full_path = self.challenge_root / rec["path"]
            actual_sha = sha256_of_file(full_path)
            if actual_sha != rec["sha256"]:
                raise ManifestCustodyError(
                    "SOLVER_FILE_MISMATCH",
                    f"Solver file tampered! {rec['path']} expected {rec['sha256']}, got {actual_sha}",
                )

        # 2. Collect judge cases; every case file must be listed in the verified manifest.
        all_cases: list[dict[str, Any]] = []
        for sub in JUDGE_CASE_DIRS:
            case_dir = self.judge_dir / "cases" / sub
            if not case_dir.is_dir():
                continue
            for case_file in sorted(case_dir.glob("*.json")):
                if case_file.resolve() not in verified_paths:
                    raise ManifestCustodyError(
                        "CASE_FILE_NOT_IN_MANIFEST",
                        f"{case_file.name} is not listed in the judge manifest",
                    )
                all_cases.append(json.loads(case_file.read_text(encoding="utf-8")))
        if not all_cases:
            raise ManifestCustodyError(
                "EMPTY_JUDGE_SUITE", "no judge case files were found; an empty suite is refused"
            )

        # 3. Score all cases with both checkers.
        case_evaluations: list[dict[str, Any]] = []
        for case in all_cases:
            res = solve(case)
            case_evaluations.append(evaluate_dual(case, res))

        total_cases = len(case_evaluations)
        passed_cases = sum(1 for e in case_evaluations if e.get("verdict") == "PASS")
        agreements = sum(1 for e in case_evaluations if e.get("agreement") is True)
        all_passed = (passed_cases == total_cases) and (agreements == total_cases)
        defect_count = total_cases - passed_cases

        # 4. Label the run.
        effective_task_key = (
            task_key
            or f"{FILE_PREFIX}_scoring_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        effective_run_id = run_id or f"run_{effective_task_key}"

        verdict = self.woland_gate.determine_terminal_verdict(
            case_evaluations, defect_count=defect_count
        )
        claim_hygiene = reference_claim_hygiene(verdict, total_cases, passed_cases, agreements)
        budget_accounting = self.budget_gate.to_accounting_dict()

        if persist_woland:
            verdict, _path_woland, _path_sg, digests = self.woland_gate.evaluate_and_persist(
                task_key=effective_task_key,
                run_id=effective_run_id,
                case_results=case_evaluations,
                claim_hygiene=claim_hygiene,
                defect_count=defect_count,
                budget_accounting=budget_accounting,
            )
        else:
            digests = {}

        scoring_receipt = {
            "agreements_count": agreements,
            "all_passed": all_passed,
            "authority_effect": "None",
            "budget_accounting": budget_accounting,
            "case_count": total_cases,
            "challenge_id": CHALLENGE_ID,
            "claim_hygiene": claim_hygiene,
            "digest_normalization": "CRLF_TO_LF",
            "freeze_sha256": phase2_data["freeze_sha256"],
            "gate_scope": "REFERENCE_SOLVER_SELF_CHECK",
            "judge_manifest_entries_verified": len(verified_paths),
            "judge_manifest_sha256": phase1_data["manifest_sha256"],
            "passed_count": passed_cases,
            "phase": "PHASE_3_REVEAL_AND_SCORING_RECEIPT",
            "protocol": "SG-CP v1",
            "task_key": effective_task_key,
            "timestamp_utc": utc_now(),
            "verdict": verdict,
            "woland_digests": digests,
        }
        atomic_write_json(self.phase3_file, scoring_receipt)
        return scoring_receipt

    def run_all(self, *, task_key: str | None = None, run_id: str | None = None) -> dict[str, Any]:
        """Runs Phase 1, Phase 2, and Phase 3 sequentially."""
        p1 = self.run_phase1_commit_judge()
        p2 = self.run_phase2_freeze_solver()
        p3 = self.run_phase3_reveal_and_score(task_key=task_key, run_id=run_id)
        return {"phase1": p1, "phase2": p2, "phase3": p3}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="C014 reference self-consistency commit-reveal runner"
    )
    parser.add_argument(
        "action",
        choices=["phase1", "phase2", "phase3", "all"],
        default="all",
        nargs="?",
        help="Action to perform",
    )
    parser.add_argument(
        "--task-key", type=str, default=None, help="Custom task key for the run folder"
    )
    parser.add_argument(
        "--run-id", type=str, default=None, help="Custom run id for the Symbol Game run store"
    )

    args = parser.parse_args()
    runner = CommitRevealRunner()

    if args.action == "phase1":
        runner.run_phase1_commit_judge()
        print(f"Phase 1 complete: {runner.phase1_file}")
    elif args.action == "phase2":
        runner.run_phase2_freeze_solver()
        print(f"Phase 2 complete: {runner.phase2_file}")
    elif args.action == "phase3":
        res = runner.run_phase3_reveal_and_score(task_key=args.task_key, run_id=args.run_id)
        print(f"Phase 3 complete: {runner.phase3_file}, label: {res['verdict']}")
    else:
        res = runner.run_all(task_key=args.task_key, run_id=args.run_id)
        print(f"All 3 phases complete. Label: {res['phase3']['verdict']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
