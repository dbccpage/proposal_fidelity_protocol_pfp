"""Provisional local evaluation runner for C020.

The snapshot and cases are read in one process.  No prior commitment or
provider billing receipt is synthesized, so the result cannot promote.

This scores the reference solver against the package's own judge packet (a
self-consistency check, not a model evaluation and not a Adversary verdict). The
package has no judge manifest with per-file digests, so judge custody is not
established: the runner records the LF-normalised digest of every scored file
instead, and the label can be at best OPEN_RESIDUAL. Empty suites are refused.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any

from projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.reference_solver.solver import (
    solve,
)

from .budget_gate import verify_budget
from .adversary_gate import (
    evaluate_adversary_gate,
)

C020_DIR = pathlib.Path(__file__).parent.parent


def lf_normalized_bytes(path: pathlib.Path) -> bytes:
    """File bytes with CRLF normalised to LF, so digests equal git-blob content."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_of_file(path: pathlib.Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def run_provisional_evaluation() -> dict[str, Any]:
    """Run local checks without claiming a three-phase commit/reveal."""
    solver_path = C020_DIR / "reference_solver" / "solver.py"
    solver_hash = sha256_of_file(solver_path)
    scored_file_digests: dict[str, str] = {}

    cases_dir = C020_DIR / "judge_packet" / "cases"
    case_files = sorted(cases_dir.glob("*.json"))

    passed = 0
    total = len(case_files)
    failures: list[dict[str, str]] = []

    for cf in case_files:
        scored_file_digests[cf.relative_to(C020_DIR).as_posix()] = sha256_of_file(cf)
        case = json.loads(cf.read_text(encoding="utf-8"))
        res = solve(case)
        ok, reason, details = evaluate_dual(case, res)
        if ok:
            passed += 1
        else:
            failures.append({"file": cf.name, "reason": reason})

    mut_dir = C020_DIR / "judge_packet" / "mutation_suite" / "mutations"
    mut_files = sorted(mut_dir.glob("mut_*.json"))
    killed = 0
    for mf in mut_files:
        scored_file_digests[mf.relative_to(C020_DIR).as_posix()] = sha256_of_file(mf)
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted = data["certificate"]
        ok, reason, details = evaluate_dual(case, corrupted)
        if not ok:
            killed += 1

    acc_path = C020_DIR / "participant_packet" / "accounting.json"
    acc = json.loads(acc_path.read_text(encoding="utf-8"))
    b_ok, b_msg = verify_budget(acc)

    summary = {
        "passed_cases": passed,
        "total_cases": total,
        "failures": failures,
        "mutations_killed": killed,
        "mutations_total": len(mut_files),
        # Display only; the gate decides on the exact counts above. None when no mutation ran.
        "mutation_kill_rate": (killed / len(mut_files)) if mut_files else None,
        "budget_passed": b_ok,
        "budget_reason": b_msg,
    }

    # Policy: no commitment was made before the run. That is recorded, and it does not change the label.
    verdict = evaluate_adversary_gate(summary)
    verdict["details"] = {
        **verdict["details"],
        "commit_reveal_enforced": False,
        "commitment_timing": "COMPUTED_AT_REVEAL",
        "judge_custody_established": False,
        "pre_run_commitment": False,
    }

    return {
        "pre_run_commitment": False,
        "integrity_snapshot": {
            "digest_normalization": "CRLF_TO_LF",
            "scored_file_sha256": scored_file_digests,
            "solver_sha256": solver_hash,
        },
        "evaluation": summary,
        "provisional_verdict": verdict,
    }
