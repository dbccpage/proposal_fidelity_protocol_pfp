"""Reference self-consistency run for C042 (SAT Encodings with DRAT Certificates).

AuthorityEffect: None.

Scores the frozen reference solver against this package's own judge packet and
checks that the judge's hostile mutations are rejected. It evaluates no model
and is not a Woland verdict.

Custody, stated plainly:

* Every entry of the package manifest (``manifest.json``) is verified over
  LF-normalised bytes before scoring, and every scored case and mutation file
  must be listed there. The manifest digest is recorded.
* The solver and checker digests are computed when this runner executes, after
  the judge cases are visible. They bind the receipt to the bytes that were
  scored; they are not a commitment made before the run
  (``"pre_run_commitment": false``, ``"commitment_timing": "COMPUTED_AT_REVEAL"``).
  This runner therefore no longer rewrites the historical files
  commit_reveal/c042_l41_judge_commitment.json and c042_l41_freeze_record.json.
  The missing commitment is recorded as the informational residual
  NO_PRE_RUN_COMMITMENT; it does not change the label.
* A case passes only when the checker accepts the reference answer and the
  answer matches the case's declared expectation (``expected_kind`` SAT/UNSAT, or
  ``expected_status``). An UNKNOWN or OUT_OF_SCOPE answer on a case that declares
  SAT or UNSAT is not a pass, although the checker accepts such refusals.
* Empty judge or mutation suites are refused. The scoring receipt is written
  atomically; a crash writes commit_reveal/c042_l41_scoring_failure_receipt.json.
"""

# ruff: noqa: E402
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PKG_ROOT = Path(__file__).resolve().parent.parent
# The checkers import the reference solver through its full package path, but
# reference_solver/solver.py still imports ``reference_solver.*`` as a top-level
# package, so the package root must stay on sys.path.
_repo_root = next((p for p in Path(__file__).resolve().parents if (p / "pyproject.toml").is_file()), None)
if _repo_root is not None and str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
for _parent in PKG_ROOT.parents:
    if (_parent / "omega_engine_pfp").is_dir() and (_parent / "omega_engine_woland").is_dir():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

# Absolute imports for the harness and solver; top-level ``governance`` collided across packages.
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.governance.woland_gate import (
    GATE_SCOPE,
    TERMINAL_REFUSE,
    WolandGateC042,
    label_with_reason,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c042_sat_with_drat_certificates.reference_solver.solver import (
    solve,
)

CHALLENGE_ID = "c042_sat_with_drat_certificates"
COMMIT_REVEAL_DIR = PKG_ROOT / "commit_reveal"
SCORING_RECEIPT_NAME = "c042_l41_scoring_receipt.json"
FAILURE_RECEIPT_NAME = "c042_l41_scoring_failure_receipt.json"
MUTATION_ANSWER_KEY = "corrupted_answer"
MUTATION_KILL_RULE = "DUAL_EVALUATOR_REJECTS"
NO_PRE_RUN_COMMITMENT = "NO_PRE_RUN_COMMITMENT"


class ManifestCustodyError(ValueError):
    """A manifest entry is missing, mismatched or unlisted, or a suite is empty."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def lf_normalized_bytes(path: Path) -> bytes:
    """File bytes with CRLF normalised to LF, so digests equal git-blob content."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def compute_file_sha256(path: Path) -> str:
    """SHA-256 of the LF-normalised file bytes."""
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write JSON through a temporary file in the same directory and os.replace it into place."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    os.replace(tmp_name, path)


def verify_manifest_entries(manifest_file: Path, package_root: Path) -> set[Path]:
    """Verify every entry of the manifest's ``files`` map over LF-normalised bytes; return the verified paths."""
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    raw = manifest.get("files")
    if isinstance(raw, Mapping):
        entries = [
            (str(k), str(v["sha256"] if isinstance(v, Mapping) else v)) for k, v in raw.items()
        ]
    elif isinstance(raw, list):
        entries = [(str(e["path"]), str(e["sha256"])) for e in raw]
    else:
        entries = []
    if not entries:
        raise ManifestCustodyError("MANIFEST_HAS_NO_ENTRIES", f"{manifest_file} lists no files")
    verified: set[Path] = set()
    for rel, expected in entries:
        path = package_root / rel
        if not path.is_file():
            raise ManifestCustodyError("MANIFEST_ENTRY_MISSING", f"{rel} is listed but absent")
        actual = compute_file_sha256(path)
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
                "FILE_NOT_IN_MANIFEST", f"{path.name} is not listed in the manifest"
            )
    if not files:
        raise ManifestCustodyError(
            empty_code, f"no files in {directory}; an empty suite is refused"
        )
    return files


def digest_tree(root: Path, paths: Sequence[Path]) -> tuple[str, dict[str, str]]:
    """Per-file digests keyed by path relative to root, plus a digest over the sorted pairs."""
    per_file = {p.relative_to(root).as_posix(): compute_file_sha256(p) for p in paths}
    combined = hashlib.sha256()
    for rel in sorted(per_file, key=lambda s: s.encode("utf-8")):
        combined.update(f"{rel}\0{per_file[rel]}\n".encode("utf-8"))
    return combined.hexdigest(), per_file


def expected_outcome(case: Mapping[str, Any]) -> tuple[str, str | None] | None:
    """The (status, kind) a case declares, or None when it declares nothing."""
    if "expected_status" in case:
        status = str(case["expected_status"])
        return status, (case.get("expected_kind") if status == "SOLVED" else None)
    if "expected_kind" in case:
        return "SOLVED", case["expected_kind"]
    return None


def score_reference_case(case: Mapping[str, Any], answer: Mapping[str, Any]) -> dict[str, Any]:
    """Score one reference answer from the checkers' verdict, their metadata and the declared expectation.

    A case is consistent when the checkers accept the answer and it matches the
    expectation. A consistent SOLVED answer is a verified answer; a consistent
    OUT_OF_SCOPE (the checker calls it warranted) is a warranted refusal and is
    reported separately, never as a verified answer. An abstention (UNKNOWN, or
    ``abstained`` in the checker metadata) is never consistent.
    """
    ok, msg, meta = evaluate_dual(dict(case), dict(answer))
    abstained = answer.get("status") == "UNKNOWN" or (
        isinstance(meta, Mapping) and meta.get("abstained") is True
    )
    expectation = expected_outcome(case)
    status = answer.get("status")
    kind = answer.get("kind") if status == "SOLVED" else None
    checker_accepted = ok is True
    matches_expected = expectation is not None and (status, kind) == expectation
    consistent = checker_accepted and matches_expected and not abstained
    return {
        "abstained": abstained,
        "case_id": case.get("case_id"),
        "checker_accepted": checker_accepted,
        "expected": None if expectation is None else list(expectation),
        "kind": kind,
        "matches_expected": matches_expected,
        "message": msg,
        "status": status,
        "verified": consistent,
        "verified_answer": consistent and status == "SOLVED",
        "warranted_refusal": consistent and status != "SOLVED",
    }


def run_commit_reveal_protocol(
    *,
    judge_dir: Path | None = None,
    manifest_file: Path | None = None,
    receipt_dir: Path | None = None,
    intelligence_repo_root: Path | None = None,
) -> dict[str, Any]:
    """Score the reference solver, run the mutations, persist the run folder and the scoring receipt.

    ``judge_dir``/``manifest_file`` select the judge data (default: this
    package); the solver and checker code that runs, and whose digests are
    recorded, is always this package's.
    """
    receipts = receipt_dir if receipt_dir is not None else COMMIT_REVEAL_DIR
    task_key = "c042_eval"
    try:
        return _run(judge_dir, manifest_file, receipts, intelligence_repo_root, task_key)
    except BaseException as error:
        atomic_write_json(
            receipts / FAILURE_RECEIPT_NAME,
            {
                "authority_effect": "None",
                "challenge_id": CHALLENGE_ID,
                "error_code": getattr(error, "code", None),
                "error_message": str(error),
                "error_type": type(error).__name__,
                "status": "RUN_FAILED",
                "task_key": task_key,
                "timestamp_utc": utc_now(),
            },
        )
        raise


def _run(
    judge_dir: Path | None,
    manifest_file: Path | None,
    receipts: Path,
    intelligence_repo_root: Path | None,
    task_key: str,
) -> dict[str, Any]:
    judge = judge_dir if judge_dir is not None else PKG_ROOT / "judge_packet"
    manifest = manifest_file if manifest_file is not None else PKG_ROOT / "manifest.json"
    data_root = manifest.parent

    solver_files = sorted((PKG_ROOT / "reference_solver").glob("*.py"))
    checker_files = sorted((PKG_ROOT / "judge_packet" / "checkers").glob("*.py"))
    if not solver_files or not checker_files:
        raise ManifestCustodyError("NO_CODE_FILES", "reference solver or checker files are missing")
    solver_tree_sha256, solver_hashes = digest_tree(PKG_ROOT, solver_files)
    checker_tree_sha256, checker_hashes = digest_tree(PKG_ROOT, checker_files)

    verified = verify_manifest_entries(manifest, data_root)
    case_files = listed_files(judge / "cases", verified, "EMPTY_JUDGE_SUITE")
    mutation_files = listed_files(judge / "mutation_suite", verified, "EMPTY_MUTATION_SUITE")

    results: list[dict[str, Any]] = []
    defects: list[dict[str, Any]] = []
    for cpath in case_files:
        case = json.loads(cpath.read_text(encoding="utf-8"))
        result = score_reference_case(case, solve(case))
        results.append(result)
        if not result["verified"]:
            defects.append({"case_id": result["case_id"], "error": result["message"]})
    # Consistent cases (verified answers plus warranted refusals) decide the label;
    # the two kinds are reported separately below.
    passed_cases = sum(1 for r in results if r["verified"])

    mutations_killed = 0
    for mpath in mutation_files:
        mutation = json.loads(mpath.read_text(encoding="utf-8"))
        if mutation.get("expected_rejection") is not True or MUTATION_ANSWER_KEY not in mutation:
            raise ManifestCustodyError(
                "MUTATION_MALFORMED", f"{mpath.name}: not a rejection mutation"
            )
        ok, _msg, _meta = evaluate_dual(mutation["case"], mutation[MUTATION_ANSWER_KEY])
        mutations_killed += 0 if ok is True else 1

    total_cases = len(results)
    mutations_total = len(mutation_files)
    residuals: list[str] = []  # closed residuals that change the label; none are declared
    informational_residuals = [NO_PRE_RUN_COMMITMENT]  # recorded only; the label is not capped
    verdict, reason = label_with_reason(
        total_cases,
        passed_cases,
        len(defects),
        mutations_total=mutations_total,
        mutations_killed=mutations_killed,
        residuals=residuals,
    )

    scoring_receipt = {
        "abstained_cases": sum(1 for r in results if r["abstained"]),
        "authority_effect": "None",
        "case_results": results,
        "challenge_id": CHALLENGE_ID,
        "checker_accepted_cases": sum(1 for r in results if r["checker_accepted"]),
        "checker_files_sha256": checker_hashes,
        "checker_tree_sha256": checker_tree_sha256,
        "commitment_timing": "COMPUTED_AT_REVEAL",
        "defect_count": len(defects),
        "defects": defects,
        "digest_normalization": "CRLF_TO_LF",
        "gate_scope": GATE_SCOPE,
        "informational_residuals": informational_residuals,
        "judge_manifest_entries_verified": len(verified),
        "judge_manifest_sha256": compute_file_sha256(manifest),
        "mutation_kill_rule": MUTATION_KILL_RULE,
        "mutations_killed": mutations_killed,
        "mutations_total": mutations_total,
        "passed_cases": passed_cases,
        "pre_run_commitment": False,
        "protocol": "SG-CP v1",
        "reason": reason,
        "residuals": residuals,
        "scored_at": utc_now(),
        "solver_files_sha256": solver_hashes,
        "solver_tree_sha256": solver_tree_sha256,
        "total_cases": total_cases,
        "verdict": verdict,
        "verified_answer_cases": sum(1 for r in results if r["verified_answer"]),
        "warranted_refusal_cases": sum(1 for r in results if r["warranted_refusal"]),
    }

    woland = WolandGateC042(task_key=task_key, intelligence_repo_root=intelligence_repo_root)
    bundle_dir = woland.emit_structurebench_quad(
        total_cases=total_cases,
        passed_cases=passed_cases,
        defects=defects,
        receipt_meta={k: v for k, v in scoring_receipt.items() if k != "case_results"},
        verdict=verdict,
        mutations_total=mutations_total,
        mutations_killed=mutations_killed,
        residuals=residuals,
        informational_residuals=informational_residuals,
    )
    scoring_receipt["run_folder"] = bundle_dir.name
    atomic_write_json(receipts / SCORING_RECEIPT_NAME, scoring_receipt)
    return scoring_receipt


if __name__ == "__main__":
    receipt = run_commit_reveal_protocol()
    print(
        f"{CHALLENGE_ID}: {receipt['verdict']} (cases {receipt['passed_cases']}/{receipt['total_cases']}, "
        f"mutations {receipt['mutations_killed']}/{receipt['mutations_total']}); run folder {receipt['run_folder']}"
    )
    sys.exit(1 if receipt["verdict"] == TERMINAL_REFUSE else 0)
