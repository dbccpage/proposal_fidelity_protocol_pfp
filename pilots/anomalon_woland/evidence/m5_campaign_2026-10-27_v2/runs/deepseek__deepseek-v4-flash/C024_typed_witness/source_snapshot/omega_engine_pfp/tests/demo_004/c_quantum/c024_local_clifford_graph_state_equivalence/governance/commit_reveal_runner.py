"""Commit-reveal runner for C024 (Local Clifford Graph State Equivalence).

AuthorityEffect: None.

Three phases (SG-CP v1), all of which score the frozen reference solver against
this package's own judge packet (a self-consistency check, not a model
evaluation and not a Woland verdict):

  * Phase 1 records the digest of judge_packet/manifest.json in
    commitments/c024_local_clifford_graph_state_equivalence_judge_commitment.json.
  * Phase 2 records digests of the reference solver files (reference_solver/
    graph.py, cut_rank.py, orbit_search.py, solver.py, ddc_tracer.py) in
    commitments/c024_local_clifford_graph_state_equivalence_freeze_record.json, bound to
    the Phase 1 commitment file.
  * Phase 3 re-verifies the manifest file, the Phase 2 binding, every frozen
    solver file and every manifest entry (paths relative to the package root),
    refuses judge case files that the manifest does not list and an empty
    suite, scores the solver with both checkers, labels the run with the
    reference self-consistency gate and writes
    commitments/c024_local_clifford_graph_state_equivalence_scoring_receipt.json.

All digests are SHA-256 over file bytes with CRLF normalised to LF, so they
equal git-blob content on every platform. Receipts are written atomically
(temporary file plus os.replace). If Phase 3 fails, a failure receipt is
written to commitments/c024_local_clifford_graph_state_equivalence_scoring_failure_receipt.json
before the exception propagates. ``intelligence_repo_root`` is the directory
that contains ``_ic/``.
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
    if (_parent / "omega_engine_projects").exists() and (
        _parent / "omega_engine_providers"
    ).exists():
        _root_str = str(_parent)
        if _root_str not in sys.path:
            sys.path.insert(0, _root_str)
        break

try:
    from .budget_gate import HARD_CEILING_MICROUSD, BudgetGate
    from .woland_gate import GATE_SCOPE, WolandGate
except (ImportError, ValueError):
    try:
        from budget_gate import HARD_CEILING_MICROUSD, BudgetGate
        from woland_gate import GATE_SCOPE, WolandGate
    except (ImportError, ValueError):
        from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.governance.budget_gate import (
            HARD_CEILING_MICROUSD,
            BudgetGate,
        )
        from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.governance.woland_gate import (
            GATE_SCOPE,
            WolandGate,
        )

try:
    from ..judge_packet.checkers.dual_evaluator import evaluate_dual
    from ..reference_solver.solver import solve
except (ImportError, ValueError):
    from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.judge_packet.checkers.dual_evaluator import (
        evaluate_dual,
    )
    from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.solver import (
        solve,
    )

CHALLENGE_ID = "c024_local_clifford_graph_state_equivalence"
FILE_PREFIX = "c024_local_clifford_graph_state_equivalence"

SOLVER_FILES_TO_FREEZE: list[str] = [
    "reference_solver/graph.py",
    "reference_solver/cut_rank.py",
    "reference_solver/orbit_search.py",
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


def reference_claim_hygiene(verdict: str, total: int, passed: int) -> dict[str, str]:
    """Claim hygiene derived from the measured counts of this run."""
    return {
        "supports": f"The frozen reference solver's outputs were accepted by the dual evaluator on {passed}/{total} judge cases.",
        "does_not_support": (
            "Any statement about a model (none was evaluated), about checker soundness or independence, "
            "about local-unitary equivalence beyond the Clifford group, or a Woland verdict."
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
    """Orchestrates the three-phase reference self-consistency run for C024.

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

        self.commitments_dir = self.challenge_root / "commitments"
        self.judge_packet_dir = self.challenge_root / "judge_packet"
        self.manifest_path = self.judge_packet_dir / "manifest.json"
        self.cases_dir = self.judge_packet_dir / "cases"
        self.judge_commit_file = self.commitments_dir / f"{FILE_PREFIX}_judge_commitment.json"
        self.freeze_record_file = self.commitments_dir / f"{FILE_PREFIX}_freeze_record.json"
        self.scoring_receipt_file = self.commitments_dir / f"{FILE_PREFIX}_scoring_receipt.json"
        self.failure_receipt_file = (
            self.commitments_dir / f"{FILE_PREFIX}_scoring_failure_receipt.json"
        )

        self.budget_gate = BudgetGate(ceiling_microusd=HARD_CEILING_MICROUSD)
        self.woland_gate = WolandGate(
            intelligence_root=None
            if intelligence_repo_root is None
            else Path(intelligence_repo_root) / "_ic"
        )

    def phase_1_commit_judge_packet(self) -> dict[str, Any]:
        """Phase 1: record the LF-normalised digest of the judge manifest."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Judge manifest not found: {self.manifest_path}")

        manifest_bytes = lf_normalized_bytes(self.manifest_path)
        manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
        manifest_data = json.loads(manifest_bytes.decode("utf-8"))
        counts = manifest_data.get("counts", {})

        commitment = {
            "authority_effect": "None",
            "case_count": counts.get("judge_cases"),
            "challenge_id": CHALLENGE_ID,
            "checker_count": counts.get("checker_modules"),
            "digest_normalization": "CRLF_TO_LF",
            "manifest_entry_count": len(manifest_data.get("files", {})),
            "manifest_file": self.manifest_path.name,
            "manifest_sha256": manifest_sha256,
            "mutation_count": counts.get("hostile_mutations"),
            "phase": "PHASE_1_JUDGE_COMMITMENT",
            "timestamp_utc": utc_now(),
        }

        atomic_write_json(self.judge_commit_file, commitment)
        return commitment

    def phase_2_freeze_deliverables(self) -> dict[str, Any]:
        """Phase 2: record digests of the solver files, bound to the Phase 1 commitment."""
        if not self.judge_commit_file.exists():
            raise RuntimeError(
                "Commit-reveal sequence violation: Phase 1 judge commitment must precede Phase 2 solver freeze"
            )

        file_digests: dict[str, str] = {}
        for rel_path in SOLVER_FILES_TO_FREEZE:
            full_path = self.challenge_root / rel_path
            if not full_path.exists():
                raise FileNotFoundError(f"Deliverable solver file not found: {full_path}")
            file_digests[rel_path] = sha256_of_file(full_path)

        combined_hasher = hashlib.sha256()
        for k in sorted(file_digests.keys()):
            combined_hasher.update(k.encode("utf-8"))
            combined_hasher.update(file_digests[k].encode("utf-8"))

        freeze_record = {
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "composite_freeze_sha256": combined_hasher.hexdigest(),
            "deliverable_files": file_digests,
            "digest_normalization": "CRLF_TO_LF",
            "judge_commitment_sha256": sha256_of_file(self.judge_commit_file),
            "phase": "PHASE_2_SOLVER_FREEZE",
            "timestamp_utc": utc_now(),
        }

        atomic_write_json(self.freeze_record_file, freeze_record)
        return freeze_record

    def phase_3_evaluate_and_score(
        self,
        task_key: str = "c024_lc_graph_equiv_eval",
        force_clean: bool = True,
    ) -> dict[str, Any]:
        """Phase 3: verify custody, score the frozen solver, label and persist the run.

        ``force_clean`` is accepted for compatibility and deletes nothing: an
        existing run folder always raises RunFolderExistsError. Any failure
        writes a failure receipt before the exception propagates.
        """
        try:
            return self._phase_3(task_key=task_key, force_clean=force_clean)
        except BaseException as error:
            atomic_write_json(
                self.failure_receipt_file,
                {
                    "authority_effect": "None",
                    "challenge_id": CHALLENGE_ID,
                    "error_code": getattr(error, "code", None),
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                    "phase": "PHASE_3_SCORING_FAILED",
                    "task_key": task_key,
                    "timestamp_utc": utc_now(),
                },
            )
            raise

    def _phase_3(self, *, task_key: str, force_clean: bool) -> dict[str, Any]:
        if not self.judge_commit_file.exists() or not self.freeze_record_file.exists():
            raise RuntimeError(
                "Commit-reveal sequence violation: Both judge commitment and solver freeze record must exist before Phase 3"
            )

        # 1. The manifest file must match the Phase 1 commitment.
        if not self.manifest_path.is_file():
            raise CustodyFileMissingError(
                "MANIFEST_MISSING", f"Judge manifest not found: {self.manifest_path}"
            )
        commitment = json.loads(self.judge_commit_file.read_text(encoding="utf-8"))
        current_manifest_sha256 = sha256_of_file(self.manifest_path)
        if current_manifest_sha256 != commitment.get("manifest_sha256"):
            raise ManifestCustodyError(
                "MANIFEST_DIGEST_MISMATCH",
                f"Judge manifest tampered! Expected {commitment.get('manifest_sha256')}, got {current_manifest_sha256}",
            )

        # 2. The freeze record must be bound to this commitment and every frozen file must match.
        freeze_record = json.loads(self.freeze_record_file.read_text(encoding="utf-8"))
        judge_commit_sha256 = sha256_of_file(self.judge_commit_file)
        if freeze_record.get("judge_commitment_sha256") != judge_commit_sha256:
            raise ManifestCustodyError(
                "FREEZE_BINDING_MISMATCH",
                "Solver freeze record is not bound to the current judge commitment",
            )
        frozen = freeze_record.get("deliverable_files")
        if not isinstance(frozen, Mapping) or not frozen:
            raise ManifestCustodyError(
                "FREEZE_RECORD_EMPTY", "the solver freeze record lists no files"
            )
        for rel_path, expected_sha in frozen.items():
            full_path = self.challenge_root / rel_path
            if not full_path.is_file():
                raise CustodyFileMissingError(
                    "SOLVER_FILE_MISSING", f"Frozen solver file not found: {rel_path}"
                )
            actual_sha = sha256_of_file(full_path)
            if actual_sha != expected_sha:
                raise ManifestCustodyError(
                    "SOLVER_FILE_MISMATCH",
                    f"Solver file tampered! {rel_path} expected {expected_sha}, got {actual_sha}",
                )

        # 3. Every manifest entry must match the bytes on disk.
        verified_paths = verify_manifest_entries(self.manifest_path, self.challenge_root)

        # 4. Every scored case file must be listed in the verified manifest; an empty suite is refused.
        case_files = sorted(self.cases_dir.glob("*.json"))
        for case_path in case_files:
            if case_path.resolve() not in verified_paths:
                raise ManifestCustodyError(
                    "CASE_FILE_NOT_IN_MANIFEST",
                    f"{case_path.name} is not listed in the judge manifest",
                )
        if not case_files:
            raise ManifestCustodyError(
                "EMPTY_JUDGE_SUITE", f"No judge test cases found in {self.cases_dir}"
            )

        # 5. Score every case with the dual evaluator. No Phi_1 / Gamma_2 is measured here.
        case_results: list[dict[str, Any]] = []
        dda_events: list[dict[str, Any]] = []
        for idx, case_path in enumerate(case_files):
            case_raw = json.loads(case_path.read_text(encoding="utf-8"))
            case_input = case_raw.get("input", case_raw)
            case_id = case_input.get("id", case_input.get("case_id", f"case_{idx:03d}"))

            sol_out = solve(case_input)
            passed, detail, _meta = evaluate_dual(case_input, sol_out)
            checker_pass = passed is True
            status = sol_out.get("status", "UNKNOWN")
            case_results.append(
                {
                    "checker_detail": detail,
                    "checker_pass": checker_pass,
                    "equivalent": sol_out.get("equivalent"),
                    "id": case_id,
                    "status": status,
                }
            )
            dda_events.append(
                {
                    "case_file": case_path.name,
                    "case_id": case_id,
                    "checker_pass": checker_pass,
                    "index": idx,
                    "status": status,
                    "timestamp_utc": utc_now(),
                }
            )

        accounting = self.budget_gate.to_accounting_dict()
        case_count = len(case_results)
        passed_count = sum(1 for r in case_results if r["checker_pass"] is True)
        claim_hygiene = reference_claim_hygiene(
            self.woland_gate.judge(case_results), case_count, passed_count
        )

        persisted = self.woland_gate.persist_run(
            task_key=task_key,
            case_results=case_results,
            dda_events=dda_events,
            accounting=accounting,
            claim_hygiene=claim_hygiene,
            force_clean=force_clean,
        )

        portable_persisted = {
            key: value
            for key, value in persisted.items()
            if key not in {"symbol_game_run_dir", "woland_run_dir"}
        }

        scoring_receipt = {
            "accounting": accounting,
            "all_passed": passed_count == case_count,
            "authority_effect": "None",
            "case_count": case_count,
            "challenge_id": CHALLENGE_ID,
            "claim_hygiene": claim_hygiene,
            "composite_freeze_sha256": freeze_record.get("composite_freeze_sha256"),
            "digest_normalization": "CRLF_TO_LF",
            "gate_scope": GATE_SCOPE,
            "judge_manifest_entries_verified": len(verified_paths),
            "judge_manifest_sha256": current_manifest_sha256,
            "passed_count": passed_count,
            "persisted_receipt": portable_persisted,
            "phase": "PHASE_3_SCORING_RECEIPT",
            "task_key": task_key,
            "timestamp_utc": utc_now(),
            "verdict": persisted["verdict"],
        }

        atomic_write_json(self.scoring_receipt_file, scoring_receipt)
        return scoring_receipt

    def run_full_protocol(self, task_key: str = "c024_lc_graph_equiv_eval") -> dict[str, Any]:
        """Runs the entire 3-phase Commit-Reveal protocol sequentially."""
        p1 = self.phase_1_commit_judge_packet()
        p2 = self.phase_2_freeze_deliverables()
        p3 = self.phase_3_evaluate_and_score(task_key=task_key, force_clean=True)
        return {
            "phase_1": p1,
            "phase_2": p2,
            "phase_3": p3,
            "verdict": p3["verdict"],
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="C024 reference self-consistency commit-reveal runner."
    )
    parser.add_argument("--phase", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--task-key", default="c024_lc_graph_equiv_eval")
    args = parser.parse_args()

    runner = CommitRevealRunner()
    if args.phase == "1":
        res = runner.phase_1_commit_judge_packet()
        print(f"[Phase 1 Complete] Manifest digest: {res['manifest_sha256']}")
    elif args.phase == "2":
        res = runner.phase_2_freeze_deliverables()
        print(
            f"[Phase 2 Complete] Composite solver freeze digest: {res['composite_freeze_sha256']}"
        )
    elif args.phase == "3":
        res = runner.phase_3_evaluate_and_score(task_key=args.task_key, force_clean=True)
        print(
            f"[Phase 3 Complete] Label: {res['verdict']} ({res['passed_count']}/{res['case_count']} passed)"
        )
    else:
        full = runner.run_full_protocol(task_key=args.task_key)
        print(f"[Commit-Reveal Complete] Label: {full['verdict']}")


if __name__ == "__main__":
    main()
