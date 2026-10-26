"""Test governance and budget gate for C020."""

from __future__ import annotations

from pathlib import Path

from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.governance.budget_gate import (
    BUDGET_CEILING_USD,
    verify_budget,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.governance.commit_reveal_runner import (
    run_provisional_evaluation,
)
from omega_engine_projects.mssn_sn_symgam.challenges.b_cohomology.c020_spectral_sequence_double_complex.governance.woland_gate import (
    evaluate_woland_gate,
)

GOV_DIR = Path(__file__).resolve().parent.parent / "governance"


def test_budget_gate_pass():
    acc = {
        "tier": "T4",
        "billed_cost_usd": 0.04,
        "allow_fallbacks": False,
    }
    ok, msg = verify_budget(acc)
    assert ok


def test_budget_gate_fail_overspend():
    acc = {
        "tier": "T4",
        "billed_cost_usd": BUDGET_CEILING_USD + 0.10,
        "allow_fallbacks": False,
    }
    ok, msg = verify_budget(acc)
    assert not ok


def test_budget_gate_fail_missing_provider_cost():
    ok, msg = verify_budget({"tier": "T4", "allow_fallbacks": False})
    assert not ok
    assert "billed_cost_usd" in msg


def test_woland_gate_pass():
    summary = {
        "passed_cases": 54,
        "total_cases": 54,
        "mutations_total": 40,
        "mutations_killed": 40,
        "budget_passed": True,
    }
    verdict = evaluate_woland_gate(summary)
    assert verdict["verdict"] == "REFERENCE_SELF_CONSISTENT"


def test_woland_gate_refuses_float_kill_rate_without_counts_and_empty_suites():
    """Counterexamples: a float ``mutation_kill_rate`` of 1.0 with no counts, and 0 of 0 mutations."""
    legacy = {
        "passed_cases": 54,
        "total_cases": 54,
        "mutation_kill_rate": 1.0,
        "budget_passed": True,
    }
    assert evaluate_woland_gate(legacy)["verdict"] == "REFERENCE_SELF_INCONSISTENT"
    empty = {**legacy, "mutations_total": 0, "mutations_killed": 0}
    assert evaluate_woland_gate(empty)["verdict"] == "REFERENCE_SELF_INCONSISTENT"


def test_woland_gate_refusal_incomplete():
    summary = {
        "passed_cases": 53,
        "total_cases": 54,
        "mutations_total": 40,
        "mutations_killed": 40,
        "budget_passed": True,
    }
    verdict = evaluate_woland_gate(summary)
    assert verdict["verdict"] == "REFERENCE_SELF_INCONSISTENT"


def test_provisional_evaluation_refuses_unreceipted_cost():
    receipt = run_provisional_evaluation()
    verdict = receipt["provisional_verdict"]
    assert verdict["verdict"] == "REFERENCE_SELF_INCONSISTENT"
    assert verdict["details"]["commit_reveal_enforced"] is False
    assert receipt["evaluation"]["budget_passed"] is False
