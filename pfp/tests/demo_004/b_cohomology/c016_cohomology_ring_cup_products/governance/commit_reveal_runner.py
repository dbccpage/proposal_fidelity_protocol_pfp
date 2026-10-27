"""Provisional local evaluation runner for C016.

This runner computes an integrity snapshot and evaluates already-visible cases in
one process.  It is deliberately *not* described as commit/reveal: no solver
commitment was persisted before the judge cases were published.

It scores the reference solver against this package's own judge packet (a
self-consistency check, not a model evaluation and not a Adversary verdict). Every
entry of judge_packet/manifest.json is verified over LF-normalised bytes before
scoring, and every scored case and mutation file must be listed there. Empty
suites are refused.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections.abc import Mapping
from typing import Any

from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.governance.budget_gate import (
    check_budget_gate,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.governance.adversary_gate import (
    evaluate_adversary_terminal_gate,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c016_cohomology_ring_cup_products.reference_solver.solver import (
    solve,
)

CHALLENGE_ID = "c016_cohomology_ring_cup_products"
C016_DIR = pathlib.Path(__file__).parent.parent
PARTICIPANT_DIR = C016_DIR / "participant_packet"
JUDGE_DIR = C016_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"
MANIFEST_FILE = JUDGE_DIR / "manifest.json"


class ManifestCustodyError(ValueError):
    """A judge manifest entry is missing or unlisted, or its digest does not match."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def lf_normalized_bytes(path: pathlib.Path) -> bytes:
    """File bytes with CRLF normalised to LF, so digests equal git-blob content."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def sha256_of_file(path: pathlib.Path) -> str:
    return hashlib.sha256(lf_normalized_bytes(path)).hexdigest()


def verify_manifest_entries(
    manifest_file: pathlib.Path, package_root: pathlib.Path
) -> set[pathlib.Path]:
    """Verify every manifest entry over LF-normalised bytes; return the verified paths."""
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
    verified: set[pathlib.Path] = set()
    for rel, expected in entries:
        candidate = manifest_file.parent / rel
        path = candidate if candidate.is_file() else package_root / rel
        if not path.is_file():
            raise ManifestCustodyError("MANIFEST_ENTRY_MISSING", f"{rel} is listed but absent")
        actual = sha256_of_file(path)
        if actual != expected:
            raise ManifestCustodyError(
                "MANIFEST_ENTRY_MISMATCH", f"{rel}: expected {expected}, got {actual}"
            )
        verified.add(path.resolve())
    return verified


def _require_listed(path: pathlib.Path, verified: set[pathlib.Path]) -> None:
    if path.resolve() not in verified:
        raise ManifestCustodyError(
            "FILE_NOT_IN_MANIFEST", f"{path.name} is not listed in the judge manifest"
        )


def run_provisional_evaluation() -> dict[str, Any]:
    """Run local checks without making a promotion-grade commit/reveal claim."""
    verified = verify_manifest_entries(MANIFEST_FILE, C016_DIR)
    solver_py = C016_DIR / "reference_solver" / "solver.py"
    solver_sha256 = sha256_of_file(solver_py)

    accounting_file = PARTICIPANT_DIR / "accounting.json"
    accounting_data = json.loads(accounting_file.read_text(encoding="utf-8"))
    budget_ok, budget_msg, budget_details = check_budget_gate(accounting_data)

    all_case_files = (
        sorted((CASES_DIR / "base").glob("*.json"))
        + sorted((CASES_DIR / "controls").glob("*.json"))
        + sorted((CASES_DIR / "poisoned").glob("*.json"))
    )

    total = len(all_case_files)
    passed = 0
    failures = []

    for cf in all_case_files:
        _require_listed(cf, verified)
        case = json.loads(cf.read_text(encoding="utf-8"))
        res, tracer = solve(case)
        if res["status"] in ("SOLVED", "OUT_OF_SCOPE"):
            ok, reason, details = evaluate_dual(case, res)
            if ok:
                passed += 1
            else:
                failures.append({"file": cf.name, "reason": reason})
        else:
            failures.append({"file": cf.name, "reason": f"Unverified status {res['status']}"})

    mut_dir = JUDGE_DIR / "mutation_suite" / "mutations"
    mut_files = sorted(mut_dir.glob("*.json"))
    killed = 0
    for mf in mut_files:
        _require_listed(mf, verified)
        mut_data = json.loads(mf.read_text(encoding="utf-8"))
        case = mut_data["case"]
        corrupted = mut_data["corrupted_result"]
        ok, reason, _ = evaluate_dual(case, corrupted)
        if not ok:
            killed += 1

    eval_summary = {
        "total_cases": total,
        "passed_cases": passed,
        "failures": failures,
        "mutations_killed": killed,
        "mutations_total": len(mut_files),
        # Display only; the gate decides on the exact counts above. None when no mutation ran.
        "mutation_kill_rate": (killed / len(mut_files)) if mut_files else None,
    }

    # Policy: no commitment was made before the run. That is recorded, and it does not change the label.
    verdict, verdict_reason, verdict_details = evaluate_adversary_terminal_gate(
        eval_summary, budget_ok
    )
    verdict_details = {
        **verdict_details,
        "budget_message": budget_msg,
        "commit_reveal_enforced": False,
        "commitment_timing": "COMPUTED_AT_REVEAL",
        "pre_run_commitment": False,
    }

    receipt = {
        "challenge_id": CHALLENGE_ID,
        "pre_run_commitment": False,
        "integrity_snapshot": {
            "digest_normalization": "CRLF_TO_LF",
            "judge_manifest_entries_verified": len(verified),
            "judge_manifest_sha256": sha256_of_file(MANIFEST_FILE),
            "solver_sha256": solver_sha256,
        },
        "evaluation": eval_summary,
        "provisional_verdict": {
            "verdict": verdict,
            "reason": verdict_reason,
            "details": verdict_details,
        },
    }
    return receipt
