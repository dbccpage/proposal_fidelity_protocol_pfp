"""Reference self-consistency run for C044 (Finite Group Identification).

AuthorityEffect: None.

Scores the frozen reference solver against this package's own judge packet and
checks that the judge's hostile mutations are rejected. It evaluates no model
and is not a Woland verdict.

Custody, stated plainly:

* This package has no judge manifest, so judge custody is not established
  (``"judge_custody_established": false``). The runner records the
  LF-normalised SHA-256 of every scored case and mutation file and of the
  solver and checker code instead.
* Those digests are computed when this runner executes, after the judge cases
  are visible. They bind the receipt to the bytes that were scored; they are not
  a commitment made before the run (``"pre_run_commitment": false``,
  ``"commitment_timing": "COMPUTED_AT_REVEAL"``). The runner therefore no longer
  rewrites the historical files commit_reveal/c044_l41_judge_commitment.json
  and c044_l41_freeze_record.json. Both facts are recorded as informational
  residuals (JUDGE_MANIFEST_MISSING, NO_PRE_RUN_COMMITMENT) and do not change
  the label.
* A case passes only when both checkers accept the reference answer, the two
  checkers agree, and the answer is not an abstention (status UNKNOWN).
* A mutation counts as rejected when the dual evaluator rejects it
  (DUAL_EVALUATOR_REJECTS, the package's original rule); the number rejected
  by both checkers is recorded separately.
* Empty judge or mutation suites are refused. The scoring receipt is written
  atomically to commit_reveal/c044_l41_scoring_receipt.json; a crash writes
  commit_reveal/c044_l41_scoring_failure_receipt.json instead.
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
for _parent in PKG_ROOT.parents:
    if (_parent / "omega_engine_pfp").is_dir() and (_parent / "omega_engine_woland").is_dir():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.governance.woland_gate import (
    GATE_SCOPE,
    TERMINAL_REFUSE,
    WolandGateC044,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.reference_solver.solver import (
    solve,
)

CHALLENGE_ID = "c044_finite_group_identification"
COMMIT_REVEAL_DIR = PKG_ROOT / "commit_reveal"
CASES_SUBDIR = "hidden_cases"
SCORING_RECEIPT_NAME = "c044_l41_scoring_receipt.json"
FAILURE_RECEIPT_NAME = "c044_l41_scoring_failure_receipt.json"
MUTATION_ANSWER_KEY = "answer"
CHECKER_FLAG_KEYS = ("exact_pass", "independent_pass")
MUTATION_KILL_RULE = "DUAL_EVALUATOR_REJECTS"
# Custody facts recorded in every receipt; they do not change the label.
INFORMATIONAL_RESIDUALS = ("JUDGE_MANIFEST_MISSING", "NO_PRE_RUN_COMMITMENT")


class ManifestCustodyError(ValueError):
    """A judge suite is empty or malformed, or custody of the scored bytes cannot be recorded."""

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


def digest_tree(root: Path, paths: Sequence[Path]) -> tuple[str, dict[str, str]]:
    """Per-file digests keyed by path relative to root, plus a digest over the sorted pairs."""
    per_file = {p.relative_to(root).as_posix(): compute_file_sha256(p) for p in paths}
    combined = hashlib.sha256()
    for rel in sorted(per_file, key=lambda s: s.encode("utf-8")):
        combined.update(f"{rel}\0{per_file[rel]}\n".encode("utf-8"))
    return combined.hexdigest(), per_file


def load_items(paths: Sequence[Path], kind: str) -> list[dict[str, Any]]:
    """Load JSON objects (a file may hold one object or a list of objects); refuse anything else."""
    items: list[dict[str, Any]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        for item in data if isinstance(data, list) else [data]:
            if not isinstance(item, dict):
                raise ManifestCustodyError(
                    f"{kind}_MALFORMED", f"{path.name} holds a non-object {kind.lower()}"
                )
            items.append(item)
    return items


def checker_flags(receipt: Mapping[str, Any]) -> tuple[Any, Any]:
    """The two checkers' verdicts as reported by the dual evaluator."""
    return receipt.get(CHECKER_FLAG_KEYS[0]), receipt.get(CHECKER_FLAG_KEYS[1])


def _trace_string(trace: Any) -> str:
    if isinstance(trace, Mapping):
        value = trace.get("trace_string", "")
        return value if isinstance(value, str) else ""
    return trace if isinstance(trace, str) else ""


def score_reference_case(case: Mapping[str, Any], answer: Mapping[str, Any]) -> dict[str, Any]:
    """A pass needs dual acceptance, checker agreement and no abstention."""
    ok, msg, receipt = evaluate_dual(case, answer)
    first, second = checker_flags(receipt)
    agree = type(first) is bool and type(second) is bool and first == second
    status = answer.get("status")
    abstained = status == "UNKNOWN"
    passed = ok is True and agree and not abstained
    return {
        "abstained": abstained,
        "case_id": case.get("case_id"),
        "checkers_agree": agree,
        "dual_accepted": ok is True,
        "message": msg,
        "task": case.get("task"),
        "status": status,
        "verified": passed,
        "ddc_trace": _trace_string(answer.get("ddc_trace")),
    }


def run_commit_reveal_protocol(
    *,
    judge_dir: Path | None = None,
    receipt_dir: Path | None = None,
    intelligence_repo_root: Path | None = None,
) -> dict[str, Any]:
    """Score the reference solver, run the mutations, persist the run folder and the scoring receipt.

    ``judge_dir`` selects the judge data (default: this package's judge_packet);
    the solver and checker code that runs, and whose digests are recorded, is
    always this package's.
    """
    receipts = receipt_dir if receipt_dir is not None else COMMIT_REVEAL_DIR
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    try:
        return _run(judge_dir, receipts, intelligence_repo_root, run_id)
    except BaseException as error:
        atomic_write_json(
            receipts / FAILURE_RECEIPT_NAME,
            {
                "authority_effect": "None",
                "challenge_id": CHALLENGE_ID,
                "error_code": getattr(error, "code", None),
                "error_message": str(error),
                "error_type": type(error).__name__,
                "run_id": run_id,
                "status": "RUN_FAILED",
                "timestamp_utc": utc_now(),
            },
        )
        raise


def _run(
    judge_dir: Path | None, receipts: Path, intelligence_repo_root: Path | None, run_id: str
) -> dict[str, Any]:
    judge = judge_dir if judge_dir is not None else PKG_ROOT / "judge_packet"

    solver_files = sorted((PKG_ROOT / "reference_solver").glob("*.py"))
    checker_files = sorted((PKG_ROOT / "judge_packet" / "checkers").glob("*.py"))
    if not solver_files or not checker_files:
        raise ManifestCustodyError("NO_CODE_FILES", "reference solver or checker files are missing")
    case_files = sorted((judge / CASES_SUBDIR).glob("*.json"))
    mutation_files = sorted((judge / "mutation_suite").glob("*.json"))

    solver_tree_sha256, solver_hashes = digest_tree(PKG_ROOT, solver_files)
    checker_tree_sha256, checker_hashes = digest_tree(PKG_ROOT, checker_files)
    judge_tree_sha256, judge_hashes = digest_tree(judge, case_files + mutation_files)

    cases = load_items(case_files, "CASE")
    mutations = load_items(mutation_files, "MUTATION")
    if not cases:
        raise ManifestCustodyError("EMPTY_JUDGE_SUITE", f"no judge cases in {judge / CASES_SUBDIR}")
    if not mutations:
        raise ManifestCustodyError(
            "EMPTY_MUTATION_SUITE", f"no mutations in {judge / 'mutation_suite'}"
        )

    case_records = [score_reference_case(case, solve(case)) for case in cases]
    passed = sum(1 for rec in case_records if rec["verified"])
    disagreements = sum(1 for rec in case_records if not rec["checkers_agree"])

    mutations_killed = 0
    mutations_rejected_by_both = 0
    for mutation in mutations:
        if MUTATION_ANSWER_KEY not in mutation or "case" not in mutation:
            raise ManifestCustodyError(
                "MUTATION_MALFORMED", f"mutation without case or {MUTATION_ANSWER_KEY!r}"
            )
        _ok, _msg, receipt = evaluate_dual(mutation["case"], mutation[MUTATION_ANSWER_KEY])
        first, second = checker_flags(receipt)
        mutations_killed += 1 if _ok is not True else 0
        mutations_rejected_by_both += 1 if (first is False and second is False) else 0

    gate = WolandGateC044(run_id, intelligence_repo_root=intelligence_repo_root)
    residuals: list[str] = []  # closed residuals that change the label; none are declared
    verdict = gate.evaluate_verdict(
        total_cases=len(case_records),
        passed_cases=passed,
        disagreements=disagreements,
        mutations_killed=mutations_killed,
        total_mutations=len(mutations),
        residuals=residuals,
    )

    scoring = {
        "abstained_cases": sum(1 for rec in case_records if rec["abstained"]),
        "checker_files_sha256": checker_hashes,
        "checker_tree_sha256": checker_tree_sha256,
        "commitment_timing": "COMPUTED_AT_REVEAL",
        "digest_normalization": "CRLF_TO_LF",
        "disagreements": disagreements,
        "informational_residuals": list(INFORMATIONAL_RESIDUALS),
        "judge_custody_established": False,
        "judge_files_sha256": judge_hashes,
        "judge_tree_sha256": judge_tree_sha256,
        "mutation_kill_rule": MUTATION_KILL_RULE,
        "mutations_killed": mutations_killed,
        "mutations_rejected_by_both_checkers": mutations_rejected_by_both,
        "passed_cases": passed,
        "pre_run_commitment": False,
        "residuals": residuals,
        "solver_files_sha256": solver_hashes,
        "solver_tree_sha256": solver_tree_sha256,
        "total_cases": len(case_records),
        "total_mutations": len(mutations),
    }
    sealed_dir = gate.emit_quad_bundle(verdict, scoring, case_records)

    scoring_receipt = {
        "authority_effect": "None",
        "challenge_id": CHALLENGE_ID,
        "gate_scope": GATE_SCOPE,
        "protocol": "SG-CP v1",
        "run_folder": sealed_dir.name,
        "run_id": run_id,
        "scored_at": utc_now(),
        "scoring": scoring,
        "terminal_verdict": verdict,
        "verdict": verdict,
    }
    atomic_write_json(receipts / SCORING_RECEIPT_NAME, scoring_receipt)
    return scoring_receipt


if __name__ == "__main__":
    result = run_commit_reveal_protocol()
    s = result["scoring"]
    print(
        f"{CHALLENGE_ID}: {result['verdict']} (cases {s['passed_cases']}/{s['total_cases']}, "
        f"mutations {s['mutations_killed']}/{s['total_mutations']}); run folder {result['run_folder']}"
    )
    sys.exit(1 if result["verdict"] == TERMINAL_REFUSE else 0)
