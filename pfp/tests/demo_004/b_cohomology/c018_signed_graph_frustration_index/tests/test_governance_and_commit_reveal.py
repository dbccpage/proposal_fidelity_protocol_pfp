"""Test budget gate, provisional evaluation, and Adversary gate."""

from __future__ import annotations

import pathlib

from projects.mssn_sn_symgam.challenges.b_cohomology.c018_signed_graph_frustration_index.governance.budget_gate import (
    verify_budget,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c018_signed_graph_frustration_index.governance.commit_reveal_runner import (
    run_provisional_evaluation,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c018_signed_graph_frustration_index.governance.adversary_gate import (
    evaluate_adversary_gate,
)

C018_DIR = pathlib.Path(__file__).parent.parent


def test_budget_gate_enforcement():
    ok, _ = verify_budget({"tier": "T3", "billed_cost_usd": 0.50, "allow_fallbacks": False})
    assert ok is True
    fail, _ = verify_budget({"tier": "T3", "billed_cost_usd": 1.50, "allow_fallbacks": False})
    assert fail is False
    missing, msg = verify_budget({"tier": "T3", "allow_fallbacks": False})
    assert missing is False
    assert "billed_cost_usd" in msg


def test_provisional_evaluation_refuses_unreceipted_cost():
    receipt = run_provisional_evaluation()
    verdict = receipt["provisional_verdict"]
    assert verdict["verdict"] == "REFERENCE_SELF_INCONSISTENT"
    assert verdict["details"]["commit_reveal_enforced"] is False
    assert receipt["evaluation"]["budget_passed"] is False


def test_gate_refuses_zero_of_zero_mutations():
    """Counterexample (C054): an empty mutation suite must never be consistent."""
    base = {
        "passed_cases": 5,
        "total_cases": 5,
        "mutations_total": 4,
        "mutations_killed": 4,
        "budget_passed": True,
    }
    assert evaluate_adversary_gate(base)["verdict"] == "REFERENCE_SELF_CONSISTENT"
    assert evaluate_adversary_gate({**base, "mutations_total": 0, "mutations_killed": 0})[
        "verdict"
    ] == ("REFERENCE_SELF_INCONSISTENT")
