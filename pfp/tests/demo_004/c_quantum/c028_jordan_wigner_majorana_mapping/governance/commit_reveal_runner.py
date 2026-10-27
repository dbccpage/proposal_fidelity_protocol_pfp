# AuthorityEffect: None.
"""Commit-reveal runner for C028 (Jordan-Wigner and Majorana Mapping).

Three phases (SG-CP v1), all of which score the frozen reference solver against
this package's own judge packet (a self-consistency check, not a model
evaluation and not a Adversary verdict):

  * Phase 1 records the digest of judge_packet/manifest.json in
    commitments/c028_jw_judge_commitment.json.
  * Phase 2 records digests of the reference solver files in
    commitments/c028_jw_freeze_record.json, bound to the Phase 1 commitment.
  * Phase 3 re-verifies the manifest file, the Phase 2 binding, every frozen
    solver file and every manifest entry (paths relative to the package root),
    refuses case or mutation files that the manifest does not list and an
    empty case suite, scores the solver and the mutation suite with the dual
    evaluator, labels the run on exact counts and writes
    commitments/c028_jw_scoring_receipt.json.

All digests are SHA-256 over file bytes with CRLF normalised to LF, so they
equal git-blob content on every platform. Receipts are written atomically
(temporary file plus os.replace). If Phase 3 fails, a failure receipt is
written to commitments/c028_jw_scoring_failure_receipt.json before the
exception propagates. ``intelligence_repo_root`` is the directory that
contains ``_intelligence/``.
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
from fractions import Fraction
from pathlib import Path
from typing import Any

_file_path = Path(__file__).resolve()
for _parent in _file_path.parents:
    if (_parent / "projects").exists() and (
        _parent / "providers"
    ).exists():
        _root_str = str(_parent)
        if _root_str not in sys.path:
            sys.path.insert(0, _root_str)
        break

_pkg_root = _file_path.parent.parent

try:
    from .budget_gate import C028BudgetGate
    from .adversary_gate import GATE_SCOPE, AdversaryRealityGate
except ImportError:
    if str(_pkg_root) not in sys.path:
        sys.path.insert(0, str(_pkg_root))
    from governance.budget_gate import C028BudgetGate
    from governance.adversary_gate import GATE_SCOPE, AdversaryRealityGate

try:
    from ..judge_packet.checkers.dual_evaluator import evaluate_dual
    from ..reference_solver.solver import solve
except ImportError:
    if str(_pkg_root) not in sys.path:
        sys.path.insert(0, str(_pkg_root))
    from judge_packet.checkers.dual_evaluator import evaluate_dual
    from reference_solver.solver import solve

CHALLENGE_ID = "c028_jordan_wigner_majorana_mapping"
FILE_PREFIX = "c028_jw"
MUTATION_ANSWER_KEY = "mutated_answer"
SOLVER_FILES: tuple[str, ...] = (
    "f2_linear_algebra.py",
    "pauli_algebra.py",
    "majorana_mapper.py",
    "fermion_term_expander.py",
    "ddc_tracer.py",
    "solver.py",
)


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


def sha256_file(path: Path) -> str:
    """SHA-256 of the LF-normalised file bytes."""
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write sorted-key JSON through a temporary file in the same directory, then os.replace it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
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


def verify_manifest_entries(manifest_file: Path, package_root: Path) -> set[Path]:
    """Verify every manifest entry against the LF-normalised bytes on disk; return the verified paths."""
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries, base_kind = manifest_entries(manifest)
    if not entries:
        raise ManifestCustodyError("MANIFEST_HAS_NO_ENTRIES", f"{manifest_file} lists no files")
    base_dir = (manifest_file.parent if base_kind == "judge_packet" else package_root).resolve()
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
        actual = sha256_file(path)
        if actual != expected:
            raise ManifestCustodyError(
                "MANIFEST_ENTRY_MISMATCH",
                f"Judge file {rel} was modified or corrupted! Expected {expected}, got {actual}",
            )
        verified.add(path)
    return verified


def _require_listed(path: Path, verified: set[Path]) -> None:
    if path.resolve() not in verified:
        raise ManifestCustodyError(
            "FILE_NOT_IN_MANIFEST", f"{path.name} is not listed in the judge manifest"
        )


class CommitRevealRunner:
    """Manages the 3-phase reference self-consistency run for C028."""

    def __init__(
        self, pkg_dir: Path | None = None, *, intelligence_repo_root: Path | None = None
    ) -> None:
        self.pkg_dir = Path(pkg_dir).resolve() if pkg_dir is not None else _pkg_root
        self.commitments_dir = self.pkg_dir / "commitments"
        self.judge_dir = self.pkg_dir / "judge_packet"
        self.solver_dir = self.pkg_dir / "reference_solver"
        self.manifest_path = self.judge_dir / "manifest.json"
        self.judge_commit_file = self.commitments_dir / f"{FILE_PREFIX}_judge_commitment.json"
        self.freeze_record_file = self.commitments_dir / f"{FILE_PREFIX}_freeze_record.json"
        self.scoring_receipt_file = self.commitments_dir / f"{FILE_PREFIX}_scoring_receipt.json"
        self.failure_receipt_file = (
            self.commitments_dir / f"{FILE_PREFIX}_scoring_failure_receipt.json"
        )
        self.budget_gate = C028BudgetGate()
        self.adversary_gate = AdversaryRealityGate(base_repo_root=intelligence_repo_root)

    def phase_1_judge_commitment(self) -> dict[str, Any]:
        """Phase 1: Commit the LF-normalised judge manifest digest."""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Judge manifest not found: {self.manifest_path}")

        manifest_data = json.loads(lf_normalized_bytes(self.manifest_path).decode("utf-8"))
        counts = manifest_data.get("counts", {})
        record = {
            "authority_effect": "None",
            "case_count": counts.get("judge_cases"),
            "challenge_id": CHALLENGE_ID,
            "digest_normalization": "CRLF_TO_LF",
            "manifest_entry_count": len(manifest_data.get("files", {})),
            "manifest_path": "judge_packet/manifest.json",
            "manifest_sha256": sha256_file(self.manifest_path),
            "mutation_count": counts.get("hostile_mutations"),
            "phase": "PHASE_1_JUDGE_COMMITMENT",
            "timestamp_utc": utc_now(),
        }
        atomic_write_json(self.judge_commit_file, record)
        return record

    def phase_2_solver_freeze(self) -> dict[str, Any]:
        """Phase 2: Freeze solver files and record digests, bound to the Phase 1 commitment."""
        if not self.judge_commit_file.exists():
            raise RuntimeError(
                "Commit-reveal sequence violation: Phase 1 judge commitment must precede Phase 2 solver freeze"
            )

        digests: dict[str, str] = {}
        for fn in SOLVER_FILES:
            fp = self.solver_dir / fn
            if not fp.exists():
                raise FileNotFoundError(f"Solver file not found: {fp}")
            digests[fn] = sha256_file(fp)

        freeze_record = {
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "digest_normalization": "CRLF_TO_LF",
            "judge_commitment_sha256": sha256_file(self.judge_commit_file),
            "phase": "PHASE_2_SOLVER_FREEZE",
            "solver_files": digests,
            "timestamp_utc": utc_now(),
        }
        atomic_write_json(self.freeze_record_file, freeze_record)
        return freeze_record

    def phase_3_execute_and_score(self, task_key: str = "c028_jw_eval") -> dict[str, Any]:
        """Phase 3: verify custody, run the frozen solver and the mutation suite, label and persist.

        Any failure writes a failure receipt before the exception propagates.
        """
        try:
            return self._phase_3(task_key)
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

    def _phase_3(self, task_key: str) -> dict[str, Any]:
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
        manifest_sha256 = sha256_file(self.manifest_path)
        if manifest_sha256 != commitment.get("manifest_sha256"):
            raise ManifestCustodyError(
                "MANIFEST_DIGEST_MISMATCH",
                f"Judge manifest tampered! Expected {commitment.get('manifest_sha256')}, got {manifest_sha256}",
            )

        # 2. The freeze record must be bound to this commitment and every frozen file must match.
        freeze_record = json.loads(self.freeze_record_file.read_text(encoding="utf-8"))
        judge_commit_sha256 = sha256_file(self.judge_commit_file)
        if freeze_record.get("judge_commitment_sha256") != judge_commit_sha256:
            raise ManifestCustodyError(
                "FREEZE_BINDING_MISMATCH",
                "Solver freeze record is not bound to the current judge commitment",
            )
        frozen = freeze_record.get("solver_files")
        if not isinstance(frozen, Mapping) or not frozen:
            raise ManifestCustodyError(
                "FREEZE_RECORD_EMPTY", "the solver freeze record lists no files"
            )
        for fn, expected_sha in frozen.items():
            fp = self.solver_dir / fn
            if not fp.is_file():
                raise CustodyFileMissingError(
                    "SOLVER_FILE_MISSING", f"Frozen solver file not found: {fn}"
                )
            actual_sha = sha256_file(fp)
            if actual_sha != expected_sha:
                raise ManifestCustodyError(
                    "SOLVER_FILE_MISMATCH",
                    f"Solver file tampered! {fn} expected {expected_sha}, got {actual_sha}",
                )

        # 3. Every manifest entry must match the bytes on disk.
        verified = verify_manifest_entries(self.manifest_path, self.pkg_dir)

        # 4. Every scored case and mutation file must be listed; an empty case suite is refused.
        case_files = sorted((self.judge_dir / "cases").glob("*.json"))
        mut_files = sorted((self.judge_dir / "mutation_suite").glob("*.json"))
        for path in case_files + mut_files:
            _require_listed(path, verified)
        if not case_files:
            raise ManifestCustodyError(
                "EMPTY_JUDGE_SUITE", "no judge case files were found; an empty suite is refused"
            )

        cases_passed = 0
        dda_events: list[dict[str, Any]] = []
        for cf in case_files:
            case_data = json.loads(cf.read_text(encoding="utf-8"))
            ans = solve(case_data)
            passed, msg, _det = evaluate_dual(case_data, ans)
            accepted = passed is True
            cases_passed += 1 if accepted else 0
            dda_events.append(
                {
                    "accepted": accepted,
                    "action": "evaluate_case",
                    "case_file": cf.name,
                    "case_id": case_data.get("case_id"),
                    "message": msg,
                }
            )

        # 5. Every hostile mutation must be rejected; an empty mutation suite is labelled inconsistent by the gate.
        mutations_killed = 0
        for mf in mut_files:
            mdata = json.loads(mf.read_text(encoding="utf-8"))
            if (
                not isinstance(mdata, Mapping)
                or "case" not in mdata
                or MUTATION_ANSWER_KEY not in mdata
            ):
                raise ManifestCustodyError(
                    "MUTATION_FILE_MALFORMED", f"{mf.name} lacks 'case' or '{MUTATION_ANSWER_KEY}'"
                )
            passed, _msg, _det = evaluate_dual(mdata["case"], mdata[MUTATION_ANSWER_KEY])
            rejected = passed is not True
            mutations_killed += 1 if rejected else 0
            dda_events.append(
                {"action": "evaluate_mutation", "mutation_file": mf.name, "rejected": rejected}
            )

        cases_evaluated = len(case_files)
        mutations_total = len(mut_files)
        cost_usd = Fraction(self.budget_gate.spent_microusd, 1_000_000)
        ceiling_usd = Fraction(self.budget_gate.limit_microusd, 1_000_000)

        verdict = self.adversary_gate.evaluate_verdict(
            cases_evaluated=cases_evaluated,
            cases_passed=cases_passed,
            mutations_killed=mutations_killed,
            mutations_total=mutations_total,
            cost_usd=cost_usd,
            ceiling_usd=ceiling_usd,
        )

        evidence = {
            "cases_evaluated": cases_evaluated,
            "cases_passed": cases_passed,
            "ceiling_microusd": self.budget_gate.limit_microusd,
            "ceiling_usd": str(ceiling_usd),
            "cost_usd": str(cost_usd),
            "gate_scope": GATE_SCOPE,
            "judge_manifest_entries_verified": len(verified),
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "spent_microusd": self.budget_gate.spent_microusd,
        }

        run_folder = self.adversary_gate.persist_run(
            task_key=task_key,
            verdict=verdict,
            cases_evaluated=cases_evaluated,
            cases_passed=cases_passed,
            mutations_killed=mutations_killed,
            mutations_total=mutations_total,
            cost_usd=cost_usd,
            dda_events=dda_events,
            evidence_summary=evidence,
        )

        scoring_receipt = {
            "authority_effect": "None",
            "cases_evaluated": cases_evaluated,
            "cases_passed": cases_passed,
            "challenge_id": CHALLENGE_ID,
            "cost_usd": str(cost_usd),
            "digest_normalization": "CRLF_TO_LF",
            "evidence": evidence,
            "freeze_record_sha256": sha256_file(self.freeze_record_file),
            "gate_scope": GATE_SCOPE,
            "judge_commitment_sha256": judge_commit_sha256,
            "judge_manifest_sha256": manifest_sha256,
            "mutation_kill_fraction": f"{mutations_killed}/{mutations_total}",
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "phase": "PHASE_3_SCORING_RECEIPT",
            "run_folder": str(run_folder),
            "task_key": task_key,
            "timestamp_utc": utc_now(),
            "verdict": verdict,
        }
        atomic_write_json(self.scoring_receipt_file, scoring_receipt)
        return scoring_receipt

    def run_full_lifecycle(self, task_key: str = "c028_jw_eval") -> dict[str, Any]:
        """Runs the entire 3-phase Commit-Reveal pipeline."""
        p1 = self.phase_1_judge_commitment()
        p2 = self.phase_2_solver_freeze()
        p3 = self.phase_3_execute_and_score(task_key=task_key)
        return {
            "phase_1": p1,
            "phase_2": p2,
            "phase_3": p3,
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="C028 reference self-consistency commit-reveal runner."
    )
    parser.add_argument(
        "--phase", choices=["1", "2", "3", "all"], default="all", help="Protocol phase to execute"
    )
    parser.add_argument("--task-key", default="c028_jw_eval", help="Identifier for run artifacts")
    args = parser.parse_args()

    runner = CommitRevealRunner()

    if args.phase == "1":
        rec = runner.phase_1_judge_commitment()
        print(f"Phase 1 Complete: manifest_sha256 = {rec['manifest_sha256']}")
    elif args.phase == "2":
        rec = runner.phase_2_solver_freeze()
        print(f"Phase 2 Complete: {len(rec['solver_files'])} solver files frozen")
    elif args.phase == "3":
        rec = runner.phase_3_execute_and_score(task_key=args.task_key)
        print(
            f"Phase 3 Complete: Label = {rec['verdict']}, Passed = {rec['cases_passed']}/{rec['cases_evaluated']}"
        )
    else:
        full = runner.run_full_lifecycle(task_key=args.task_key)
        print("--- C028 REFERENCE SELF-CONSISTENCY RUN ---")
        print(f"Phase 1 Manifest Hash: {full['phase_1']['manifest_sha256']}")
        print(f"Phase 2 Files Frozen:  {len(full['phase_2']['solver_files'])}")
        print(f"Phase 3 Label:         {full['phase_3']['verdict']}")
        print(
            f"Passed:                {full['phase_3']['cases_passed']}/{full['phase_3']['cases_evaluated']}"
        )
        print(f"Mutations Rejected:    {full['phase_3']['mutation_kill_fraction']}")


if __name__ == "__main__":
    main()
