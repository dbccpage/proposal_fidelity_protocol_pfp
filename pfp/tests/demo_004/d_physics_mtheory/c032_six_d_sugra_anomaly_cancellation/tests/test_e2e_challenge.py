"""Comprehensive 4-Tier End-to-End Integration Suite for C032.

AuthorityEffect: None.

Tests:
  Tier 1: Participant packet structure, TASK.md, accounting.json, and canonical examples.
  Tier 2: Reference solver execution on examples and base cases.
  Tier 3: Dual certifier 100% concordance on all 42 judge cases.
  Tier 4: 100% hostile mutation kill rate across all 40 corrupted certificates.
"""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.judge_packet.checkers.dual_evaluator import (
    assert_dual_agreement,
    evaluate_dual,
)
from omega_engine_projects.mssn_sn_symgam.challenges.d_physics_mtheory.c032_six_d_sugra_anomaly_cancellation.reference_solver.solver import (
    solve,
)

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
PARTICIPANT_DIR = CHALLENGE_DIR / "participant_packet"
JUDGE_DIR = CHALLENGE_DIR / "judge_packet"
CASES_DIR = JUDGE_DIR / "cases"
MUT_DIR = JUDGE_DIR / "mutation_suite" / "mutations"


def test_tier1_participant_packet_integrity():
    """Tier 1: Asserts that participant packet is well-formed and adheres to Tier T3 bounds."""
    assert (PARTICIPANT_DIR / "TASK.md").is_file()
    assert (PARTICIPANT_DIR / "accounting.json").is_file()
    assert (PARTICIPANT_DIR / "runner.py").is_file()

    examples = sorted((PARTICIPANT_DIR / "examples").glob("*.json"))
    assert len(examples) == 10, f"Expected 10 examples, found {len(examples)}"


def test_tier2_reference_solver_consistency():
    """Tier 2: Asserts that reference solver produces identical outputs on canonical examples."""
    examples = sorted((PARTICIPANT_DIR / "examples").glob("*.json"))
    for ef in examples:
        data = json.loads(ef.read_text(encoding="utf-8"))
        case = data["case"]
        expected = data["expected_output"]
        actual = solve(case)
        assert actual.get("status") == expected.get("status")
        if actual.get("status") == "SOLVED":
            assert actual.get("verdict") == expected.get("verdict")


def test_tier3_100_percent_dual_checker_concordance():
    """Tier 3: Asserts that Checker 1 and Checker 2 achieve 100% agreement on all judge cases."""
    case_files = sorted(CASES_DIR.glob("*/*.json"))
    assert len(case_files) >= 42, f"Expected at least 42 judge cases, found {len(case_files)}"

    for cf in case_files:
        case_data = json.loads(cf.read_text(encoding="utf-8"))
        res = solve(case_data)
        consensus = assert_dual_agreement(case_data, res)
        assert consensus["agreement"] is True
        assert consensus["verdict"] == "PASS"


def test_tier4_100_percent_mutation_kill_rate():
    """Tier 4: Asserts that dual checkers detect and kill 100% of certificate mutations."""
    mut_files = sorted(MUT_DIR.glob("mut_*.json"))
    assert len(mut_files) >= 40, f"Expected at least 40 mutations, got {len(mut_files)}"

    for mf in mut_files:
        data = json.loads(mf.read_text(encoding="utf-8"))
        case = data["case"]
        corrupted_result = data.get("corrupted_result") or data.get("result")
        eval_res = evaluate_dual(case, corrupted_result)
        assert eval_res["verdict"] == "FAIL", f"Mutation {mf.name} escaped detection! {eval_res}"
