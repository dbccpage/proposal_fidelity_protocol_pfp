"""Provisional local evaluation runner for C018.

The solver snapshot and already-visible cases are read in one invocation.  No
persisted pre-reveal commitment or provider billing receipt is synthesized.

This scores the reference solver against the package's own judge packet (a
self-consistency check, not a model evaluation and not a Woland verdict). The
judge_packet/ entries of governance/manifest.json are verified over
LF-normalised bytes before scoring, every scored case and mutation file must be
listed there, and empty suites are refused.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections.abc import Mapping
from typing import Any

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c018_signed_graph_frustration_index.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c018_signed_graph_frustration_index.reference_solver.solver import (
    solve,
)

from .budget_gate import verify_budget
from .woland_gate import (
    evaluate_woland_gate,
)

C018_DIR = pathlib.Path(__file__).parent.parent
MANIFEST_FILE = C018_DIR / "governance" / "manifest.json"
JUDGE_PREFIX = "judge_packet/"


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


def verify_judge_entries(
    manifest_file: pathlib.Path, package_root: pathlib.Path
) -> set[pathlib.Path]:
    """Verify every judge_packet/ entry of the manifest; return the verified paths."""
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    raw = manifest.get("files")
    entries = (
        [(str(k), str(v["sha256"] if isinstance(v, Mapping) else v)) for k, v in raw.items()]
        if isinstance(raw, Mapping)
        else []
    )
    entries = [(rel, digest) for rel, digest in entries if rel.startswith(JUDGE_PREFIX)]
    if not entries:
        raise ManifestCustodyError(
            "MANIFEST_HAS_NO_JUDGE_ENTRIES", f"{manifest_file} lists no judge_packet files"
        )
    verified: set[pathlib.Path] = set()
    for rel, expected in entries:
        path = package_root / rel
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
            "FILE_NOT_IN_MANIFEST", f"{path.name} is not listed in the manifest"
        )


def run_provisional_evaluation() -> dict[str, Any]:
    """Run local checks without claiming a three-phase commit/reveal."""
    verified = verify_judge_entries(MANIFEST_FILE, C018_DIR)
    solver_path = C018_DIR / "reference_solver" / "solver.py"
    solver_hash = sha256_of_file(solver_path)

    cases_dir = C018_DIR / "judge_packet" / "cases"
    case_files = sorted(cases_dir.glob("*.json"))

    passed = 0
    total = len(case_files)

    for cf in case_files:
        _require_listed(cf, verified)
        case = json.loads(cf.read_text(encoding="utf-8"))
        res, tracer = solve(case)
        ok, reason, details = evaluate_dual(case, res)
        if ok:
            passed += 1

    mut_dir = C018_DIR / "judge_packet" / "mutation_suite" / "mutations"
    mut_files = sorted(mut_dir.glob("mut_*.json"))
    killed = 0
    for mf in mut_files:
        _require_listed(mf, verified)
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted = data["corrupted_result"]
        ok, reason, details = evaluate_dual(case, corrupted)
        if not ok:
            killed += 1

    acc_path = C018_DIR / "participant_packet" / "accounting.json"
    acc = json.loads(acc_path.read_text(encoding="utf-8"))
    b_ok, b_msg = verify_budget(acc)

    summary = {
        "passed_cases": passed,
        "total_cases": total,
        "mutations_killed": killed,
        "mutations_total": len(mut_files),
        # Display only; the gate decides on the exact counts above. None when no mutation ran.
        "mutation_kill_rate": (killed / len(mut_files)) if mut_files else None,
        "budget_passed": b_ok,
        "budget_reason": b_msg,
    }

    # Policy: no commitment was made before the run. That is recorded, and it does not change the label.
    verdict = evaluate_woland_gate(summary)
    verdict["details"] = {
        **verdict["details"],
        "commit_reveal_enforced": False,
        "commitment_timing": "COMPUTED_AT_REVEAL",
        "pre_run_commitment": False,
    }

    return {
        "pre_run_commitment": False,
        "integrity_snapshot": {
            "digest_normalization": "CRLF_TO_LF",
            "judge_manifest_entries_verified": len(verified),
            "solver_sha256": solver_hash,
        },
        "evaluation": summary,
        "provisional_verdict": verdict,
    }
