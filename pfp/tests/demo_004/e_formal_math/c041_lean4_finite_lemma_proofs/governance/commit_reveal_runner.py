"""Commit-reveal runner for C041 (Lean 4 Proofs of Hidden Finite Lemmas).

AuthorityEffect: None.

Three phases (SG-CP v1), all of which score the frozen reference solver against
this package's own judge packet (a self-consistency check, not a model
evaluation and not a Woland verdict):

  * Phase 1 verifies every entry of judge_packet/manifest.json against the files
    on disk, checks the declared case and mutation counts against the listed
    files, and records the manifest digest and the checker file digests in
    commitments/c041_l41_judge_commitment.json.
  * Phase 2 records digests of the reference solver files (including the Lean
    compiler wrapper used by the checkers) in commitments/c041_l41_freeze_record.json.
  * Phase 3 re-verifies the manifest file, every manifest entry, every checker
    file and every frozen solver file, refuses judge case and mutation files that
    the manifest does not list, scores the solver with both checkers, runs the
    hostile mutation suite, labels the run with the reference self-consistency
    gate and writes commitments/c041_l41_scoring_receipt.json.

A case counts as passed only when both checkers accept the reference answer and
the answer matches the case's declared expectation (``expected_status`` /
``expected_kind``). An UNKNOWN answer on a case that declares a proof or a
refutation is therefore not a pass, even though the checkers accept UNKNOWN.

An INFRA_ERROR is a fact about the machine (Lean timed out or could not start),
not about the reference solver, so it is never an input to the label. When the
reference solver answers UNKNOWN with code INFRA_ERROR, or the checkers report
the outcome INFRA_ERROR for a case or a mutation, that step is rerun; if it is
still INFRA_ERROR after ``INFRA_ERROR_ATTEMPTS`` attempts, Phase 3 stops with
``InfraErrorRefusal`` (code INFRA_ERROR), no scoring receipt and no label are
written, and the failure receipt records the case and the attempts. Reruns that
recovered are counted in the scoring receipt.

All digests are SHA-256 over file bytes with CRLF normalised to LF. Receipts are
written atomically (temporary file plus os.replace). If Phase 3 crashes, a
failure receipt is written next to the scoring receipt.
"""

# ruff: noqa: E402
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
    if (_parent / "omega_engine_pfp").exists() and (
        _parent / "omega_engine_providers"
    ).exists():
        _root_str = str(_parent)
        if _root_str not in sys.path:
            sys.path.insert(0, _root_str)
        break

_pkg_root = _file_path.parent.parent
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.governance.budget_gate import C041BudgetGate
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.governance.woland_gate import (
    GATE_SCOPE,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    WolandRealityGate,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.judge_packet.checkers.dual_evaluator import evaluate_dual
from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.solver import solve

CHALLENGE_ID = "c041_lean4_finite_lemma_proofs"
FILE_PREFIX = "c041_l41"
CASES_REL = "judge_packet/cases"
MUTATIONS_REL = "judge_packet/mutation_suite"
CHECKERS_REL = "judge_packet/checkers"
MUTATION_KILL_RULE = "DUAL_EVALUATOR_REJECTS"
INFRA_ERROR_CODE = "INFRA_ERROR"
INFRA_ERROR_ATTEMPTS = 3  # one run plus two reruns


class ManifestCustodyError(ValueError):
    """A judge manifest, manifest entry, case file, mutation file or frozen file failed custody checks."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class InfraErrorRefusal(RuntimeError):
    """Lean could not be run for one case or mutation after every rerun; the run is refused, not labelled."""

    code = INFRA_ERROR_CODE

    def __init__(self, source: str, item: Any, attempts: int, errors: Any) -> None:
        self.detail = {"attempts": attempts, "errors": errors, "item": item, "source": source}
        super().__init__(
            f"{INFRA_ERROR_CODE}: {source} {item!r} was still INFRA_ERROR after {attempts} attempts; "
            "the run is refused and no label is written"
        )


def is_infra_error_answer(answer: Any) -> bool:
    """True when the reference solver reports that Lean could not be run (UNKNOWN with code INFRA_ERROR)."""
    return (
        isinstance(answer, Mapping)
        and answer.get("status") == "UNKNOWN"
        and answer.get("code") == INFRA_ERROR_CODE
    )


def is_infra_error_verdict(meta: Any) -> bool:
    """True when the dual evaluator reports that Lean could not be run."""
    return isinstance(meta, Mapping) and meta.get("outcome") == INFRA_ERROR_CODE


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_json_bytes(obj: Any) -> bytes:
    """Sorted-key compact JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def lf_normalized_bytes(path: Path) -> bytes:
    """File bytes with CRLF normalised to LF, so digests equal git-blob content."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_file(path: Path) -> str:
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
    """Return (relative path, sha256) pairs from the manifest's files/manifest/entries section."""
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
        "MANIFEST_HAS_NO_ENTRIES", "no files/manifest/entries section in the judge manifest"
    )


def verify_manifest_entries(manifest_file: Path, package_root: Path) -> set[Path]:
    """Verify every manifest entry against the LF-normalised bytes on disk; return the verified paths."""
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    entries = manifest_entries(manifest)
    if not entries:
        raise ManifestCustodyError("MANIFEST_HAS_NO_ENTRIES", f"{manifest_file} lists no files")
    verified: set[Path] = set()
    for rel, expected in entries:
        candidate = manifest_file.parent / rel
        path = candidate if candidate.is_file() else package_root / rel
        if not path.is_file():
            raise ManifestCustodyError("MANIFEST_ENTRY_MISSING", f"{rel} is listed but absent")
        actual = sha256_file(path)
        if actual != expected:
            raise ManifestCustodyError(
                "MANIFEST_ENTRY_MISMATCH", f"{rel}: expected {expected}, got {actual}"
            )
        verified.add(path.resolve())
    return verified


def listed_files(directory: Path, verified: set[Path], empty_code: str) -> list[Path]:
    """All *.json files in directory; each must be listed in the verified manifest, and there must be at least one."""
    files = sorted(directory.glob("*.json"))
    for path in files:
        if path.resolve() not in verified:
            raise ManifestCustodyError(
                "FILE_NOT_IN_MANIFEST", f"{path.name} is not listed in the judge manifest"
            )
    if not files:
        raise ManifestCustodyError(
            empty_code, f"no files in {directory}; an empty suite is refused"
        )
    return files


def expected_outcome(case: Mapping[str, Any]) -> tuple[str, str | None] | None:
    """The (status, kind) a case declares, or None when it declares nothing."""
    if "expected_status" in case:
        status = case["expected_status"]
        return str(status), (case.get("expected_kind") if status == "SOLVED" else None)
    if "expected_kind" in case:
        return "SOLVED", case["expected_kind"]
    return None


def reference_case_outcome(case: Mapping[str, Any], answer: Mapping[str, Any]) -> dict[str, Any]:
    """Score one reference answer from the checkers' verdict, their outcome and the declared expectation.

    * verified: both checkers accept (``ok`` exactly True) and the answer matches the expectation;
    * warranted_refusal: the checkers accept no solution (refusals never pass) but report the
      outcome WARRANTED_REFUSAL, and the refusal matches the expectation;
    * anything else (ABSTAINED, UNWARRANTED_REFUSAL, REJECTED, DIVERGENCE, INFRA_ERROR) is a defect.
    A warranted refusal is consistent but is not counted as a verified answer.
    """
    ok, msg, meta = evaluate_dual(dict(case), dict(answer))
    checker_outcome = meta.get("outcome") if isinstance(meta, Mapping) else None
    checker_accepted = ok is True
    expectation = expected_outcome(case)
    status = answer.get("status")
    kind = answer.get("kind") if status == "SOLVED" else None
    matches_expected = expectation is not None and (status, kind) == expectation
    verified = checker_accepted and matches_expected
    warranted_refusal = (
        not checker_accepted
        and checker_outcome == "WARRANTED_REFUSAL"
        and matches_expected
        and status != "SOLVED"
    )
    return {
        "abstained": status == "UNKNOWN" or checker_outcome == "ABSTAINED",
        "case_id": case.get("case_id"),
        "checker_accepted": checker_accepted,
        "checker_outcome": checker_outcome,
        "defects": 0 if (verified or warranted_refusal) else 1,
        "eval_message": msg,
        "expectation_declared": expectation is not None,
        "expected_kind": None if expectation is None else expectation[1],
        "expected_status": None if expectation is None else expectation[0],
        "kind": kind,
        "matches_expected": matches_expected,
        "status": status,
        "verified": verified,
        "warranted_refusal": warranted_refusal,
    }


class CommitRevealRunner:
    """Manages the 3-phase commit-reveal execution lifecycle for C041.

    AuthorityEffect: None.
    """

    def __init__(
        self,
        pkg_dir: Path | None = None,
        *,
        intelligence_root: Path | None = None,
        budget_gate: C041BudgetGate | None = None,
        woland_gate: WolandRealityGate | None = None,
    ) -> None:
        self.pkg_dir = pkg_dir if pkg_dir is not None else _pkg_root
        self.commitments_dir = self.pkg_dir / "commitments"
        self.judge_dir = self.pkg_dir / "judge_packet"
        self.solver_dir = self.pkg_dir / "reference_solver"
        self.manifest_path = self.judge_dir / "manifest.json"
        self.phase1_file = self.commitments_dir / f"{FILE_PREFIX}_judge_commitment.json"
        self.phase2_file = self.commitments_dir / f"{FILE_PREFIX}_freeze_record.json"
        self.phase3_file = self.commitments_dir / f"{FILE_PREFIX}_scoring_receipt.json"
        self.failure_file = self.commitments_dir / f"{FILE_PREFIX}_scoring_failure_receipt.json"
        self.budget_gate = budget_gate if budget_gate is not None else C041BudgetGate()
        self.woland_gate = (
            woland_gate if woland_gate is not None else WolandRealityGate(intelligence_root)
        )
        self.authority_effect = "None"

    def _checker_digests(self) -> dict[str, str]:
        checker_files = sorted((self.pkg_dir / CHECKERS_REL).glob("*.py"))
        if not checker_files:
            raise ManifestCustodyError(
                "NO_CHECKER_FILES", f"no checker files in {self.pkg_dir / CHECKERS_REL}"
            )
        return {p.name: sha256_file(p) for p in checker_files}

    def _solver_digests(self) -> dict[str, str]:
        solver_files = sorted(self.solver_dir.glob("*.py"))
        if not solver_files:
            raise ManifestCustodyError(
                "NO_SOLVER_FILES", f"no reference solver files in {self.solver_dir}"
            )
        return {p.name: sha256_file(p) for p in solver_files}

    def phase_1_judge_commitment(self) -> dict[str, Any]:
        """Phase 1: verify every manifest entry and the declared counts, then commit the manifest digest."""
        if not self.manifest_path.is_file():
            raise FileNotFoundError(f"Judge manifest not found: {self.manifest_path}")

        verified = verify_manifest_entries(self.manifest_path, self.pkg_dir)
        case_files = listed_files(self.pkg_dir / CASES_REL, verified, "EMPTY_JUDGE_SUITE")
        mutation_files = listed_files(
            self.pkg_dir / MUTATIONS_REL, verified, "EMPTY_MUTATION_SUITE"
        )

        manifest_data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        counted = {
            "case_count": len(case_files),
            "mutation_count": len(mutation_files),
            "total_files": len(verified),
        }
        for key, value in counted.items():
            declared = manifest_data.get(key)
            if declared is not None and (type(declared) is not int or declared != value):
                raise ManifestCustodyError(
                    "MANIFEST_COUNT_MISMATCH",
                    f"manifest declares {key}={declared!r}, the listed files give {value}",
                )

        record = {
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "checker_files": self._checker_digests(),
            "digest_normalization": "CRLF_TO_LF",
            "manifest_path": "judge_packet/manifest.json",
            "manifest_sha256": sha256_file(self.manifest_path),
            "phase": "PHASE_1_JUDGE_COMMITMENT",
            "protocol": "SG-CP v1",
            "timestamp_utc": utc_now(),
            **counted,
        }
        atomic_write_json(self.phase1_file, record)
        return record

    def phase_2_freeze_record(self) -> dict[str, Any]:
        """Phase 2: freeze solver artifact digests, bound to the Phase 1 commitment."""
        if not self.phase1_file.is_file():
            raise RuntimeError("Phase 1 commitment required before Phase 2 freeze")
        phase1_data = json.loads(self.phase1_file.read_text(encoding="utf-8"))

        hashes = self._solver_digests()
        combined_hash = hashlib.sha256(
            "".join(f"{k}:{v};" for k, v in sorted(hashes.items())).encode("utf-8")
        ).hexdigest()

        record = {
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "combined_solver_sha256": combined_hash,
            "deliverable": "reference_solver/solver.py",
            "digest_normalization": "CRLF_TO_LF",
            "phase": "PHASE_2_FREEZE_RECORD",
            "phase1_binding_sha256": phase1_data["manifest_sha256"],
            "protocol": "SG-CP v1",
            "solver_files": hashes,
            "timestamp_utc": utc_now(),
        }
        atomic_write_json(self.phase2_file, record)
        return record

    @staticmethod
    def _score_case(case_data: Mapping[str, Any]) -> dict[str, Any]:
        """Solve and score one case; an INFRA_ERROR from the solver or the checkers is rerun, then refused."""
        errors: Any = None
        for attempt in range(1, INFRA_ERROR_ATTEMPTS + 1):
            answer = solve(dict(case_data))
            if is_infra_error_answer(answer):
                errors = answer.get("infra_errors")
                continue
            outcome = reference_case_outcome(case_data, answer)
            if outcome["checker_outcome"] == INFRA_ERROR_CODE:
                errors = outcome["eval_message"]
                continue
            outcome["infra_error_reruns"] = attempt - 1
            return outcome
        raise InfraErrorRefusal("case", case_data.get("case_id"), INFRA_ERROR_ATTEMPTS, errors)

    @staticmethod
    def _mutation_rejected(name: str, mutation: Mapping[str, Any]) -> tuple[bool, int]:
        """Whether the dual evaluator rejects a mutation, and the reruns used; INFRA_ERROR is never a rejection."""
        msg: Any = None
        for attempt in range(1, INFRA_ERROR_ATTEMPTS + 1):
            ok, msg, meta = evaluate_dual(mutation["case"], mutation["answer"])
            if not is_infra_error_verdict(meta):
                return ok is not True, attempt - 1
        raise InfraErrorRefusal("mutation", name, INFRA_ERROR_ATTEMPTS, msg)

    def phase_3_scoring(self, task_key: str = "c041_eval_run") -> dict[str, Any]:
        """Phase 3: verify custody, score the frozen solver and label the run.

        A crash writes a failure receipt before the exception propagates.
        """
        try:
            return self._phase_3(task_key)
        except BaseException as error:
            atomic_write_json(
                self.failure_file,
                {
                    "authority_effect": "None",
                    "challenge_id": CHALLENGE_ID,
                    "error_code": getattr(error, "code", None),
                    "error_detail": getattr(error, "detail", None),
                    "error_message": str(error),
                    "error_type": type(error).__name__,
                    "phase": "PHASE_3_SCORING_FAILED",
                    "protocol": "SG-CP v1",
                    "task_key": task_key,
                    "timestamp_utc": utc_now(),
                },
            )
            raise

    def _phase_3(self, task_key: str) -> dict[str, Any]:
        if not self.phase1_file.is_file():
            raise RuntimeError("Phase 1 commitment required before Phase 3 scoring")
        if not self.phase2_file.is_file():
            raise RuntimeError("Phase 2 freeze required before Phase 3 scoring")
        phase1_data = json.loads(self.phase1_file.read_text(encoding="utf-8"))
        phase2_data = json.loads(self.phase2_file.read_text(encoding="utf-8"))

        # 1. Custody: manifest file, every entry, checker files, frozen solver files.
        current_manifest_sha = sha256_file(self.manifest_path)
        if current_manifest_sha != phase1_data["manifest_sha256"]:
            raise ManifestCustodyError(
                "MANIFEST_DIGEST_MISMATCH",
                f"Judge manifest tampered! Expected {phase1_data['manifest_sha256']}, got {current_manifest_sha}",
            )
        verified = verify_manifest_entries(self.manifest_path, self.pkg_dir)
        if self._checker_digests() != phase1_data["checker_files"]:
            raise ManifestCustodyError(
                "CHECKER_FILE_MISMATCH", "judge checker files differ from the Phase 1 commitment"
            )
        if self._solver_digests() != phase2_data["solver_files"]:
            raise ManifestCustodyError(
                "SOLVER_FILE_MISMATCH", "reference solver files differ from the Phase 2 freeze"
            )

        # 2. Judge cases and mutations: every file must be listed; empty suites are refused.
        case_files = listed_files(self.pkg_dir / CASES_REL, verified, "EMPTY_JUDGE_SUITE")
        mutation_files = listed_files(
            self.pkg_dir / MUTATIONS_REL, verified, "EMPTY_MUTATION_SUITE"
        )

        # 3. Score the reference solver (INFRA_ERROR is rerun, then refused; never scored).
        case_outcomes: list[dict[str, Any]] = []
        ddc_steps: list[dict[str, Any]] = []
        for cf in case_files:
            case_data = json.loads(cf.read_text(encoding="utf-8"))
            outcome = self._score_case(case_data)
            case_outcomes.append(outcome)
            ddc_steps.append(
                {
                    "action": "score_case",
                    "details": {
                        "case_id": outcome["case_id"],
                        "checker_accepted": outcome["checker_accepted"],
                        "checker_outcome": outcome["checker_outcome"],
                        "matches_expected": outcome["matches_expected"],
                        "status": outcome["status"],
                    },
                    "letter": "R",
                }
            )

        # 4. Hostile mutations: each must be rejected by the dual evaluator (an INFRA_ERROR is not a rejection).
        mutations_killed = 0
        mutation_reruns = 0
        for mf in mutation_files:
            mutation = json.loads(mf.read_text(encoding="utf-8"))
            if mutation.get("expected_rejection") is not True:
                raise ManifestCustodyError(
                    "MUTATION_MALFORMED", f"{mf.name}: expected_rejection is not true"
                )
            rejected, reruns = self._mutation_rejected(mf.name, mutation)
            mutations_killed += 1 if rejected else 0
            mutation_reruns += reruns
        mutations_total = len(mutation_files)
        ddc_steps.append(
            {
                "action": "run_hostile_mutations",
                "details": {
                    "mutations_killed": mutations_killed,
                    "mutations_total": mutations_total,
                },
                "letter": "D",
            }
        )

        # 5. Label the run and persist the bundle.
        budget_summary = self.budget_gate.get_summary()
        receipt = self.woland_gate.evaluate(
            task_key=task_key,
            case_outcomes=case_outcomes,
            budget_summary=budget_summary,
            ddc_steps=ddc_steps,
            mutations_total=mutations_total,
            mutations_killed=mutations_killed,
        )

        passed = sum(1 for c in case_outcomes if c["verified"] is True)
        warranted_refusals = sum(1 for c in case_outcomes if c["warranted_refusal"] is True)
        scoring_record = {
            "abstained_cases": sum(1 for c in case_outcomes if c["abstained"]),
            "authority_effect": "None",
            "challenge_id": CHALLENGE_ID,
            "checker_accepted_cases": sum(1 for c in case_outcomes if c["checker_accepted"]),
            "combined_solver_sha256": phase2_data["combined_solver_sha256"],
            "digest_normalization": "CRLF_TO_LF",
            "failed_cases": len(case_outcomes) - passed - warranted_refusals,
            "gate_scope": GATE_SCOPE,
            "infra_error_attempts_allowed": INFRA_ERROR_ATTEMPTS,
            "infra_error_reruns": {
                "cases": sum(c["infra_error_reruns"] for c in case_outcomes),
                "mutations": mutation_reruns,
            },
            "judge_manifest_entries_verified": len(verified),
            "judge_manifest_sha256": phase1_data["manifest_sha256"],
            "mutation_kill_rule": MUTATION_KILL_RULE,
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "passed_cases": passed,
            "phase": "PHASE_3_SCORING_RECEIPT",
            "protocol": "SG-CP v1",
            "receipt": receipt,
            "task_key": task_key,
            "timestamp_utc": utc_now(),
            "total_cases": len(case_outcomes),
            "verdict": receipt["verdict"],
            "warranted_refusal_cases": warranted_refusals,
        }
        atomic_write_json(self.phase3_file, scoring_record)
        return scoring_record

    def run_all(self, task_key: str = "c041_master_eval") -> dict[str, Any]:
        """Executes full 3-phase Commit-Reveal protocol sequentially."""
        p1 = self.phase_1_judge_commitment()
        p2 = self.phase_2_freeze_record()
        p3 = self.phase_3_scoring(task_key=task_key)
        return {
            "phase_1": p1,
            "phase_2": p2,
            "phase_3": p3,
            "verdict": p3.get("verdict"),
        }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="C041 reference self-consistency commit-reveal runner"
    )
    parser.add_argument("--phase", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--task-key", default=None)
    args = parser.parse_args()

    task_key = (
        args.task_key or f"c041_eval_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    )
    runner = CommitRevealRunner()

    if args.phase == "1":
        rec = runner.phase_1_judge_commitment()
        print(f"Phase 1 committed: {rec['manifest_sha256']}")
        return 0
    if args.phase == "2":
        rec = runner.phase_2_freeze_record()
        print(f"Phase 2 frozen: {rec['combined_solver_sha256']}")
        return 0
    if args.phase == "3":
        rec = runner.phase_3_scoring(task_key=task_key)
    else:
        rec = runner.run_all(task_key=task_key)["phase_3"]
    print(
        f"Label {rec['verdict']}: {rec['passed_cases']}/{rec['total_cases']} cases, "
        f"{rec['mutations_killed']}/{rec['mutations_total']} mutations rejected"
    )
    return 0 if rec["verdict"] == TERMINAL_REFERENCE_SELF_CONSISTENT else 1


if __name__ == "__main__":
    sys.exit(main())
