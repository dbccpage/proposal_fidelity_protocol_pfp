"""Commit-reveal runner for C022 (Stabilizer Code Distance).

AuthorityEffect: None.

Three phases (SG-CP v1), all of which score the frozen reference solver against
this package's own judge packet (a self-consistency check, not a model
evaluation and not a Adversary verdict):

  * Phase 1 records the digest of judge_packet/manifest.json in
    commitments/c022_stabilizer_code_distance_judge_commitment.json.
  * Phase 2 records digests of the reference solver files (reference_solver/pauli.py,
    cnf_encoder.py, sat_engine.py, solver.py, ddc_tracer.py) in
    commitments/c022_stabilizer_code_distance_freeze_record.json, bound to the
    Phase 1 commitment file.
  * Phase 3 re-verifies the manifest file, the Phase 2 binding, every frozen
    solver file and every manifest entry (paths relative to the package root),
    refuses judge case files that the manifest does not list, an empty suite
    and a case count other than the one the manifest declares, scores the
    solver with both checkers, labels the run with the
    reference self-consistency gate and writes
    commitments/c022_stabilizer_code_distance_scoring_receipt.json.

All digests are SHA-256 over file bytes with CRLF normalised to LF, so they
equal git-blob content on every platform. Receipts are written atomically
(temporary file plus os.replace). If Phase 3 fails, a failure receipt is
written to commitments/c022_stabilizer_code_distance_scoring_failure_receipt.json
before the exception propagates.
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

# Ensure repository root is in sys.path
_file_path = Path(__file__).resolve()
for _parent in _file_path.parents:
    if (_parent / "projects").exists() and (
        _parent / "providers"
    ).exists():
        _root_str = str(_parent)
        if _root_str not in sys.path:
            sys.path.insert(0, _root_str)
        break

try:
    from .budget_gate import BudgetGate
    from .adversary_gate import GATE_SCOPE, AdversaryGate
except (ImportError, ValueError):
    try:
        from budget_gate import BudgetGate
        from adversary_gate import GATE_SCOPE, AdversaryGate
    except (ImportError, ValueError):
        from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.governance.budget_gate import (
            BudgetGate,
        )
        from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.governance.adversary_gate import (
            GATE_SCOPE,
            AdversaryGate,
        )

try:
    from ..judge_packet.checkers.dual_evaluator import evaluate_dual
    from ..reference_solver.solver import solve
except (ImportError, ValueError):
    from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.judge_packet.checkers.dual_evaluator import (
        evaluate_dual,
    )
    from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.reference_solver.solver import (
        solve,
    )

CHALLENGE_ID = "c022_stabilizer_code_distance"
FILE_PREFIX = "c022_stabilizer_code_distance"

SOLVER_FILES_TO_FREEZE: list[str] = [
    "reference_solver/pauli.py",
    "reference_solver/cnf_encoder.py",
    "reference_solver/sat_engine.py",
    "reference_solver/solver.py",
    "reference_solver/ddc_tracer.py",
]


class ManifestCustodyError(ValueError):
    """A judge manifest, manifest entry, case file or frozen file failed custody checks."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class CustodyFileMissingError(ManifestCustodyError, FileNotFoundError):
    """A file named by the manifest or the freeze record is absent."""


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
    """Write sorted-key JSON through a temporary file in the same directory, then os.replace it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    tmp_path = Path(tmp_name)
    # On failure the temporary file is left in place and the target is untouched; nothing is deleted.
    tmp_path.write_bytes(data)
    os.replace(tmp_path, path)


def manifest_entries(manifest: Mapping[str, Any]) -> tuple[list[tuple[str, str]], str]:
    """Return ((relative path, sha256) pairs, base) for a list layout (base 'judge_packet') or dict layout (base 'package')."""
    raw = manifest.get("files")
    if isinstance(raw, list):
        return [(str(entry["path"]), str(entry["sha256"])) for entry in raw], "judge_packet"
    if isinstance(raw, Mapping):
        return (
            [
                (str(rel), str(value["sha256"] if isinstance(value, Mapping) else value))
                for rel, value in raw.items()
            ],
            "package",
        )
    raise ManifestCustodyError(
        "MANIFEST_HAS_NO_ENTRIES", "no 'files' list or mapping in the judge manifest"
    )


def verify_manifest_entries(manifest_file: Path, challenge_root: Path) -> set[Path]:
    """Verify every manifest entry against the LF-normalised bytes on disk; return the verified paths."""
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries, base_kind = manifest_entries(manifest)
    if not entries:
        raise ManifestCustodyError("MANIFEST_HAS_NO_ENTRIES", f"{manifest_file} lists no files")
    base_dir = (manifest_file.parent if base_kind == "judge_packet" else challenge_root).resolve()
    verified: set[Path] = set()
    for rel, expected in entries:
        path = (base_dir / rel).resolve()
        if not path.is_relative_to(base_dir):
            raise ManifestCustodyError(
                "MANIFEST_PATH_ESCAPE", f"Manifest path escape detected: {rel}"
            )
        if not path.is_file():
            raise CustodyFileMissingError(
                "MANIFEST_ENTRY_MISSING", f"Committed judge file not found: {rel}"
            )
        actual = sha256_of_file(path)
        if actual != expected:
            raise ManifestCustodyError(
                "MANIFEST_ENTRY_MISMATCH",
                f"Judge file {rel} was modified or corrupted! Expected {expected}, got {actual}",
            )
        verified.add(path)
    return verified


def declared_case_count(manifest: Mapping[str, Any]) -> int | None:
    """The judge case count the committed manifest declares, or None when it declares none."""
    case_counts = manifest.get("case_counts")
    if isinstance(case_counts, Mapping) and "total_cases" in case_counts:
        value = case_counts["total_cases"]
    elif isinstance(manifest.get("counts"), Mapping) and "judge_cases" in manifest["counts"]:
        value = manifest["counts"]["judge_cases"]
    else:
        return None
    if type(value) is not int or value < 0:
        raise ManifestCustodyError(
            "MANIFEST_CASE_COUNT_INVALID", f"declared judge case count {value!r} is not a count"
        )
    return value


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
            "about proof-system completeness, or a Adversary verdict."
        ),
        "narrowest_defensible_claim": (
            f"Reference self-consistency label {verdict} on the {total} judge case files that match the committed manifest."
        ),
        "next_test_needed": (
            "Score a participant submission under a commitment made before the run and have the Adversary swarm "
            "evaluate the bound checker receipts."
        ),
    }


class CommitRevealRunner:
    """Orchestrates the three-phase reference self-consistency run for C022.

    AuthorityEffect: None.
    """

    def __init__(
        self,
        challenge_root: Path | None = None,
        intelligence_repo_root: Path | None = None,
    ) -> None:
        if challenge_root is None:
            self.challenge_root = Path(__file__).resolve().parent.parent
        else:
            self.challenge_root = Path(challenge_root).resolve()

        self.commitments_dir: Path = self.challenge_root / "commitments"
        self.judge_packet_dir: Path = self.challenge_root / "judge_packet"
        self.reference_solver_dir: Path = self.challenge_root / "reference_solver"
        self.judge_commit_file: Path = self.commitments_dir / f"{FILE_PREFIX}_judge_commitment.json"
        self.freeze_record_file: Path = self.commitments_dir / f"{FILE_PREFIX}_freeze_record.json"
        self.scoring_receipt_file: Path = (
            self.commitments_dir / f"{FILE_PREFIX}_scoring_receipt.json"
        )
        self.failure_receipt_file: Path = (
            self.commitments_dir / f"{FILE_PREFIX}_scoring_failure_receipt.json"
        )
        self.intelligence_repo_root: Path | None = intelligence_repo_root
        self.budget_gate: BudgetGate = BudgetGate()
        self.adversary_gate: AdversaryGate = AdversaryGate(base_repo_root=intelligence_repo_root)
        self.authority_effect: str = "None"

    def run_phase1_judge_commitment(self) -> dict[str, Any]:
        """Phase 1: record the LF-normalised digest of judge_packet/manifest.json."""
        manifest_path = self.judge_packet_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Judge manifest not found at: {manifest_path}")

        manifest_bytes = lf_normalized_bytes(manifest_path)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        manifest_data = json.loads(manifest_bytes.decode("utf-8"))

        file_list = manifest_data.get("files", [])
        counts = manifest_data.get("counts", {})
        case_counts = manifest_data.get("case_counts", {"judge_cases": counts.get("judge_cases")})
        mutation_count = manifest_data.get("mutation_count", counts.get("hostile_mutations"))

        commitment_payload: dict[str, Any] = {
            "authority_effect": "None",
            "case_counts": case_counts,
            "challenge_id": CHALLENGE_ID,
            "created_utc": utc_now(),
            "digest_normalization": "CRLF_TO_LF",
            "manifest_relative_path": "judge_packet/manifest.json",
            "manifest_sha256": manifest_sha256,
            "mutation_count": mutation_count,
            "phase": "PHASE_1_OPERATOR_JUDGE_COMMITMENT",
            "protocol": "SG-CP-v1",
            "schema": "core.symbol-game.judge-commitment.v1",
            "total_judge_files": len(file_list),
        }

        atomic_write_json(self.judge_commit_file, commitment_payload)
        return commitment_payload

    def run_phase2_freeze_record(self) -> dict[str, Any]:
        """Phase 2: record digests of the reference solver files, bound to the Phase 1 commitment."""
        if not self.judge_commit_file.exists():
            raise RuntimeError(
                "Commit-reveal sequence violation: Phase 1 judge commitment must precede Phase 2 solver freeze record"
            )

        solver_files_info: list[dict[str, Any]] = []
        for rel_path in SOLVER_FILES_TO_FREEZE:
            file_path = self.challenge_root / rel_path
            if not file_path.exists():
                raise FileNotFoundError(f"Solver file not found: {file_path}")
            data = lf_normalized_bytes(file_path)
            solver_files_info.append(
                {
                    "path": rel_path,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "size_bytes": len(data),
                }
            )

        solver_files_info.sort(key=lambda s: s["path"].encode("utf-8"))
        freeze_material = json.dumps(
            solver_files_info, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")

        freeze_payload: dict[str, Any] = {
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "digest_normalization": "CRLF_TO_LF",
            "entrypoint": "reference_solver.solver:solve",
            "freeze_digest": hashlib.sha256(freeze_material).hexdigest(),
            "frozen_utc": utc_now(),
            "judge_commitment_file": self.judge_commit_file.name,
            "judge_commitment_sha256": sha256_of_file(self.judge_commit_file),
            "phase": "PHASE_2_SOLVER_FREEZE_RECORD",
            "protocol": "SG-CP-v1",
            "schema": "core.symbol-game.freeze-record.v1",
            "solver_files": solver_files_info,
        }

        atomic_write_json(self.freeze_record_file, freeze_payload)
        return freeze_payload

    def run_phase3_reveal_and_score(
        self,
        task_key: str = "c022_stabilizer_code_distance_scoring_run",
        run_id: str | None = None,
    ) -> dict[str, Any]:
        """Phase 3: verify custody, score the frozen solver and label the run.

        Any failure writes a failure receipt before the exception propagates.
        """
        try:
            return self._run_phase3(task_key=task_key, run_id=run_id)
        except BaseException as error:
            atomic_write_json(
                self.failure_receipt_file,
                {
                    "authority_effect": "None",
                    "challenge_id": CHALLENGE_ID,
                    "error_code": getattr(error, "code", None),
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                    "phase": "PHASE_3_REVEAL_AND_SCORING_FAILED",
                    "protocol": "SG-CP-v1",
                    "task_key": task_key,
                    "timestamp_utc": utc_now(),
                },
            )
            raise

    def _run_phase3(self, *, task_key: str, run_id: str | None) -> dict[str, Any]:
        judge_commit_file = self.judge_commit_file
        freeze_record_file = self.freeze_record_file

        if not judge_commit_file.exists() or not freeze_record_file.exists():
            raise RuntimeError(
                "Commit-reveal sequence violation: Both judge commitment and solver freeze record must exist before Phase 3 reveal and scoring"
            )

        # 1. The manifest file must match the Phase 1 commitment.
        manifest_path = self.judge_packet_dir / "manifest.json"
        if not manifest_path.is_file():
            raise CustodyFileMissingError(
                "MANIFEST_MISSING", f"Judge manifest not found at: {manifest_path}"
            )
        current_manifest_sha256 = sha256_of_file(manifest_path)
        judge_commit_data = json.loads(judge_commit_file.read_text(encoding="utf-8"))
        if current_manifest_sha256 != judge_commit_data.get("manifest_sha256"):
            raise ManifestCustodyError(
                "MANIFEST_DIGEST_MISMATCH",
                f"Judge manifest SHA-256 mismatch! Current: {current_manifest_sha256}, "
                f"Committed: {judge_commit_data.get('manifest_sha256')}",
            )

        # 2. The freeze record must be bound to this commitment and every frozen file must match.
        freeze_data = json.loads(freeze_record_file.read_text(encoding="utf-8"))
        judge_commit_sha256 = sha256_of_file(judge_commit_file)
        if freeze_data.get("judge_commitment_sha256") != judge_commit_sha256:
            raise ManifestCustodyError(
                "FREEZE_BINDING_MISMATCH",
                "Solver freeze record is not bound to the current judge commitment "
                f"(recorded {freeze_data.get('judge_commitment_sha256')}, current {judge_commit_sha256})",
            )
        frozen_files = freeze_data.get("solver_files")
        if not isinstance(frozen_files, list) or not frozen_files:
            raise ManifestCustodyError(
                "FREEZE_RECORD_EMPTY", "the solver freeze record lists no files"
            )
        for item in frozen_files:
            rel_path = item["path"]
            expected_sha = item["sha256"]
            full_path = self.challenge_root / rel_path
            if not full_path.is_file():
                raise CustodyFileMissingError(
                    "SOLVER_FILE_MISSING", f"Frozen solver file not found: {rel_path}"
                )
            actual_sha = sha256_of_file(full_path)
            if actual_sha != expected_sha:
                raise ManifestCustodyError(
                    "SOLVER_FILE_MISMATCH",
                    f"Solver file {rel_path} was modified after freeze! Expected {expected_sha}, got {actual_sha}",
                )

        # 3. Every manifest entry must match the bytes on disk.
        verified_paths = verify_manifest_entries(manifest_path, self.challenge_root)

        # 4. Collect judge cases; every case file must be listed in the verified manifest.
        cases_root = self.judge_packet_dir / "cases"
        case_files = sorted(cases_root.glob("*.json"), key=lambda p: p.name.encode("utf-8"))
        for case_file in case_files:
            if case_file.resolve() not in verified_paths:
                raise ManifestCustodyError(
                    "CASE_FILE_NOT_IN_MANIFEST",
                    f"{case_file.name} is not listed in the judge manifest",
                )
        if not case_files:
            raise ManifestCustodyError(
                "EMPTY_JUDGE_SUITE", "no judge case files were found; an empty suite is refused"
            )
        expected_cases = declared_case_count(json.loads(manifest_path.read_text(encoding="utf-8")))
        if expected_cases is not None and len(case_files) != expected_cases:
            raise ManifestCustodyError(
                "JUDGE_CASE_COUNT_MISMATCH",
                f"Expected exactly {expected_cases} judge cases, found {len(case_files)}",
            )

        # 5. Score every case with both checkers.
        case_results: list[dict[str, Any]] = []
        for case_file in case_files:
            try:
                case = json.loads(case_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as err:
                raise ValueError(f"Corrupted judge case file {case_file.name}: {err}") from err
            result = solve(case)
            ok, reason, details = evaluate_dual(case, result)
            res_exact = details.get("exact")
            res_indep = details.get("independent")
            agreement = (
                isinstance(res_exact, Mapping)
                and isinstance(res_indep, Mapping)
                and res_exact.get("verdict") == res_indep.get("verdict")
            )
            case_results.append(
                {
                    "agreement": agreement,
                    "case_file": case_file.name,
                    "details": details,
                    "reason": reason,
                    "verdict": "PASS" if ok is True else "FAIL",
                }
            )

        total_cases = len(case_results)
        passed_cases = sum(1 for r in case_results if r.get("verdict") == "PASS")
        agreements = sum(1 for r in case_results if r.get("agreement") is True)
        failed_cases = total_cases - passed_cases
        defects = failed_cases

        # 6. Label the run. No Phi_1 / Gamma_2 is measured by this runner, so none is passed.
        budget_accounting = self.budget_gate.to_accounting_dict()
        timestamp_slug = datetime.now(timezone.utc).strftime("%m%d%Y_%H%M%S")
        effective_run_id = run_id if run_id is not None else f"{timestamp_slug}_{task_key}"
        provisional_verdict = self.adversary_gate.determine_terminal_verdict(
            case_results, defect_count=defects
        )
        claim_hygiene = reference_claim_hygiene(
            provisional_verdict, total_cases, passed_cases, agreements
        )

        verdict, _path_adversary, _path_sg, digests = self.adversary_gate.evaluate_and_persist(
            task_key=task_key,
            run_id=effective_run_id,
            case_results=case_results,
            claim_hygiene=claim_hygiene,
            defect_count=defects,
            budget_accounting=budget_accounting,
        )

        scoring_receipt_payload: dict[str, Any] = {
            "authority_effect": "None",
            "budget_accounting": budget_accounting,
            "challenge_id": CHALLENGE_ID,
            "claim_hygiene": claim_hygiene,
            "digest_normalization": "CRLF_TO_LF",
            "evaluation_summary": {
                "agreement_count": agreements,
                "defects_detected": defects,
                "failed_cases": failed_cases,
                "pass_fraction": f"{passed_cases}/{total_cases}",
                "passed_cases": passed_cases,
                "total_cases_evaluated": total_cases,
            },
            "freeze_record_file": freeze_record_file.name,
            "freeze_record_sha256": sha256_of_file(freeze_record_file),
            "gate_scope": GATE_SCOPE,
            "judge_commitment_file": judge_commit_file.name,
            "judge_commitment_sha256": judge_commit_sha256,
            "judge_manifest_entries_verified": len(verified_paths),
            "phase": "PHASE_3_REVEAL_AND_SCORING_RECEIPT",
            "protocol": "SG-CP-v1",
            "run_id": effective_run_id,
            "schema": "core.symbol-game.scoring-receipt.v1",
            "scored_utc": utc_now(),
            "task_key": task_key,
            "verdict": verdict,
            "adversary_bundle_digests": digests,
        }

        atomic_write_json(self.scoring_receipt_file, scoring_receipt_payload)
        return scoring_receipt_payload


def run_phase1_judge_commitment(challenge_root: Path | None = None) -> dict[str, Any]:
    return CommitRevealRunner(challenge_root=challenge_root).run_phase1_judge_commitment()


def run_phase2_freeze_record(challenge_root: Path | None = None) -> dict[str, Any]:
    return CommitRevealRunner(challenge_root=challenge_root).run_phase2_freeze_record()


def run_phase3_reveal_and_score(
    challenge_root: Path | None = None,
    task_key: str = "c022_stabilizer_code_distance_scoring_run",
    run_id: str | None = None,
) -> dict[str, Any]:
    return CommitRevealRunner(challenge_root=challenge_root).run_phase3_reveal_and_score(
        task_key=task_key, run_id=run_id
    )


def run_commit_reveal_pipeline(
    challenge_root: Path | None = None,
    task_key: str = "c022_stabilizer_code_distance_scoring_run",
    run_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    runner = CommitRevealRunner(challenge_root=challenge_root)
    p1 = runner.run_phase1_judge_commitment()
    p2 = runner.run_phase2_freeze_record()
    p3 = runner.run_phase3_reveal_and_score(task_key=task_key, run_id=run_id)
    return p1, p2, p3


def main() -> None:
    parser = argparse.ArgumentParser(
        description="C022 reference self-consistency commit-reveal runner."
    )
    parser.add_argument(
        "--phase",
        choices=["1", "2", "3", "all"],
        default="all",
        help="Commit-reveal phase to execute (default: all)",
    )
    parser.add_argument("--task-key", type=str, default="c022_stabilizer_code_distance_scoring_run")
    parser.add_argument("--run-id", type=str, default=None)
    args = parser.parse_args()

    runner = CommitRevealRunner()
    if args.phase == "1":
        r = runner.run_phase1_judge_commitment()
        print(f"[Phase 1 Judge Commitment] Written. SHA-256: {r['manifest_sha256']}")
    elif args.phase == "2":
        r = runner.run_phase2_freeze_record()
        print(f"[Phase 2 Freeze Record] Written. Freeze digest: {r['freeze_digest']}")
    elif args.phase == "3":
        r = runner.run_phase3_reveal_and_score(task_key=args.task_key, run_id=args.run_id)
        print(f"[Phase 3 Reveal & Score] Complete. Label: {r['verdict']}")
    else:
        p1, p2, p3 = run_commit_reveal_pipeline(task_key=args.task_key, run_id=args.run_id)
        print("[C022 Commit-Reveal Pipeline] Complete.")
        print(f"  Phase 1 Manifest SHA: {p1['manifest_sha256']}")
        print(f"  Phase 2 Freeze SHA:   {p2['freeze_digest']}")
        print(f"  Phase 3 Label:        {p3['verdict']}")


if __name__ == "__main__":
    main()
