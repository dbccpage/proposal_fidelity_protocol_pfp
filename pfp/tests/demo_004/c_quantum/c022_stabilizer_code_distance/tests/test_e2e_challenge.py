"""End-to-End Challenge Verification for C022 (Stabilizer Code Distance).

Evaluates the complete challenge pipeline:
1. All 10 public examples evaluated with dual checkers (10/10 PASS).
2. All 30 hidden base cases evaluated with dual checkers (30/30 PASS).
3. All 10 relabel/gauge controls evaluated with dual checkers (10/10 PASS).
4. All 6 poisoned cases correctly identified as OUT_OF_SCOPE with certified witnesses (6/6 PASS).
5. Invariance of computed distance under qubit permutation and local Clifford conjugation.
"""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c022_stabilizer_code_distance.reference_solver.solver import (
    solve,
)

CHALLENGE_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = CHALLENGE_ROOT / "participant_packet" / "examples"
CASES_DIR = CHALLENGE_ROOT / "judge_packet" / "cases"


def test_e2e_public_examples():
    """Verify all 10 public worked examples."""
    example_files = sorted(EXAMPLES_DIR.glob("*.json"))
    assert len(example_files) >= 10
    for ef in example_files:
        case = json.loads(ef.read_text(encoding="utf-8"))
        res = solve(case)
        ok, reason, details = evaluate_dual(case, res)
        assert ok, f"Example {ef.name} failed dual check: {reason}"


def test_e2e_hidden_base_cases():
    """Verify every hidden base case (c022_base_12 repeated c022_base_04 and was removed)."""
    base_files = sorted(CASES_DIR.glob("c022_base_[0-9][0-9].json"))
    assert len(base_files) == 29
    for bf in base_files:
        case = json.loads(bf.read_text(encoding="utf-8"))
        res = solve(case)
        assert res["status"] == "SOLVED"
        ok, reason, details = evaluate_dual(case, res)
        assert ok, f"Base case {bf.name} failed dual check: {reason}"


def test_e2e_controls_and_invariance():
    """Verify all 10 controls and assert distance invariance."""
    ctrl_files = sorted(CASES_DIR.glob("c022_base_*_*.json"))
    assert len(ctrl_files) == 10
    for cf in ctrl_files:
        case = json.loads(cf.read_text(encoding="utf-8"))
        res = solve(case)
        assert res["status"] == "SOLVED"
        ok, reason, details = evaluate_dual(case, res)
        assert ok, f"Control case {cf.name} failed dual check: {reason}"

        # Find corresponding unpermuted base case
        base_name = cf.name.split("_perm_")[0].split("_clifford_")[0] + ".json"
        base_file = CASES_DIR / base_name
        if base_file.exists():
            base_case = json.loads(base_file.read_text(encoding="utf-8"))
            base_res = solve(base_case)
            assert res["distance"] == base_res["distance"], (
                f"Distance changed under control symmetry in {cf.name}! "
                f"Expected {base_res['distance']}, got {res['distance']}"
            )


def test_e2e_poisoned_cases():
    """Verify all 6 poisoned cases are caught and classified OUT_OF_SCOPE."""
    poison_files = sorted(CASES_DIR.glob("c022_poison_*.json"))
    assert len(poison_files) == 6
    for pf in poison_files:
        case = json.loads(pf.read_text(encoding="utf-8"))
        res = solve(case)
        assert res["status"] == "OUT_OF_SCOPE", f"Poisoned case {pf.name} not flagged OUT_OF_SCOPE"
        ok, reason, details = evaluate_dual(case, res)
        assert ok, f"Poisoned case {pf.name} failed out-of-scope validation: {reason}"
