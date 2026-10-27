# AuthorityEffect: None.
"""
Tests for Exact and Independent Dual Checkers in C044 Finite Group Identification.
"""

import json
from pathlib import Path

from pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.judge_packet.checkers.dual_evaluator import (
    evaluate_dual,
)
from pfp.tests.demo_004.e_formal_math.c044_finite_group_identification.reference_solver.solver import (
    solve,
)

BASE_DIR = Path(__file__).resolve().parent.parent


def test_public_examples():
    """All 12 public examples must be solved and accepted by dual checkers."""
    ex_dir = BASE_DIR / "participant_packet" / "examples"
    files = sorted(ex_dir.glob("c044_pub_*.json"))
    assert len(files) == 12

    for f in files:
        with open(f, "r", encoding="utf-8") as stream:
            case = json.load(stream)
        ans = solve(case)
        ok, msg, receipt = evaluate_dual(case, ans)
        assert ok is True, f"Failed on {f.name}: {msg}"
        assert receipt["checkers_agree"] is True


def test_hidden_base_cases():
    """All 40 base cases must be solved correctly and accepted by dual checkers."""
    cases_dir = BASE_DIR / "judge_packet" / "hidden_cases"
    base_files = sorted(cases_dir.glob("c044_hid_base_*.json"))
    assert len(base_files) == 40

    for f in base_files:
        with open(f, "r", encoding="utf-8") as stream:
            case = json.load(stream)
        ans = solve(case)
        ok, msg, receipt = evaluate_dual(case, ans)
        assert ok is True, f"Failed on {f.name}: {msg}"
        assert receipt["checkers_agree"] is True

        if case["task"] == "IDENTIFY":
            assert ans["rep_id"] == case["rep_id_expected"]


def test_gauge_controls():
    """All 16 relabelled gauge controls must yield the exact expected rep_id."""
    cases_dir = BASE_DIR / "judge_packet" / "hidden_cases"
    gauge_files = sorted(cases_dir.glob("c044_hid_gauge_*.json"))
    assert len(gauge_files) == 16

    for f in gauge_files:
        with open(f, "r", encoding="utf-8") as stream:
            case = json.load(stream)
        ans = solve(case)
        ok, msg, receipt = evaluate_dual(case, ans)
        assert ok is True, f"Failed on {f.name}: {msg}"
        assert ans["rep_id"] == case["rep_id_expected"]


def test_poisoned_cases():
    """All 8 poisoned cases must be handled without false acceptance."""
    cases_dir = BASE_DIR / "judge_packet" / "hidden_cases"
    poison_files = sorted(cases_dir.glob("c044_hid_poison_*.json"))
    assert len(poison_files) == 8

    for f in poison_files:
        with open(f, "r", encoding="utf-8") as stream:
            case = json.load(stream)
        ans = solve(case)
        ok, msg, receipt = evaluate_dual(case, ans)
        assert ok is True, f"Poisoned case handling failed on {f.name}: {msg}"
        # Ensure poisoned cases did not yield a false identification or isomorphism
        if case.get("poison_type") in {
            "NON_ASSOCIATIVE",
            "NOT_ASSOCIATIVE",
            "MISSING_INVERSE",
            "EXCEEDS_MAX_ORDER",
        }:
            assert ans["status"] == "OUT_OF_SCOPE"


def test_hostile_mutation_suite():
    """All 48 hostile mutated certificates must be rejected (100% kill rate)."""
    mut_dir = BASE_DIR / "judge_packet" / "mutation_suite"
    mut_files = sorted(mut_dir.glob("c044_mut_*.json"))
    assert len(mut_files) == 48

    killed = 0
    for f in mut_files:
        with open(f, "r", encoding="utf-8") as stream:
            payload = json.load(stream)
        case = payload["case"]
        corrupted_ans = payload["answer"]
        ok, msg, receipt = evaluate_dual(case, corrupted_ans)
        assert ok is False, f"Hostile mutation {f.name} falsely accepted: {msg}"
        killed += 1

    assert killed == 48
