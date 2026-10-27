"""Test governance controllers and provisional runner for C017."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.governance.budget_gate import (
    check_budget_gate,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.governance.commit_reveal_runner import (
    run_provisional_evaluation,
)
from projects.mssn_sn_symgam.challenges.b_cohomology.c017_nonabelian_lattice_holonomy.governance.adversary_gate import (
    evaluate_adversary_terminal_gate,
)


def test_budget_gate_pass():
    acc = {
        "allow_fallbacks": False,
        "audit_trail": {"billed_cost_usd": 0.0118},
    }
    ok, msg, details = check_budget_gate(acc)
    assert ok
    assert details["meets_fast_path"] is True


def test_budget_gate_rejects_allow_fallbacks():
    acc = {
        "allow_fallbacks": True,
        "audit_trail": {"billed_cost_usd": 0.01},
    }
    ok, msg, _ = check_budget_gate(acc)
    assert not ok


def test_budget_gate_rejects_missing_provider_cost():
    ok, msg, _ = check_budget_gate({"allow_fallbacks": False, "audit_trail": {}})
    assert not ok
    assert "billed_cost_usd" in msg


def test_provisional_evaluation_cannot_promote():
    receipt = run_provisional_evaluation()
    verdict = receipt["provisional_verdict"]
    # Policy: a run without a pre-run commitment records that fact; the label follows the exact counts.
    evaluation = receipt["evaluation"]
    consistent = (
        verdict["details"]["budget_passed"] is True
        and evaluation["total_cases"] > 0
        and evaluation["passed_cases"] == evaluation["total_cases"]
        and evaluation["mutations_total"] > 0
        and evaluation["mutations_killed"] == evaluation["mutations_total"]
    )
    assert verdict["verdict"] == (
        "REFERENCE_SELF_CONSISTENT" if consistent else "REFERENCE_SELF_INCONSISTENT"
    )
    assert verdict["details"]["commit_reveal_enforced"] is False
    assert verdict["details"]["pre_run_commitment"] is False
    assert receipt["pre_run_commitment"] is False
    assert receipt["evaluation"]["mutation_kill_rate"] == 1.0


def test_gate_refuses_empty_mutation_suite_and_float_only_kill_rate():
    """Counterexample (C054): 0 of 0 mutations was reported as a 100% kill rate and passed.

    A summary that only carries the old float ``mutation_kill_rate`` is also refused.
    """
    full = {"total_cases": 4, "passed_cases": 4, "mutations_total": 3, "mutations_killed": 3}
    assert evaluate_adversary_terminal_gate(full, True)[0] == "REFERENCE_SELF_CONSISTENT"
    empty = {**full, "mutations_total": 0, "mutations_killed": 0}
    assert evaluate_adversary_terminal_gate(empty, True)[0] == "REFERENCE_SELF_INCONSISTENT"
    legacy = {"total_cases": 4, "passed_cases": 4, "mutation_kill_rate": 1.0}
    assert evaluate_adversary_terminal_gate(legacy, True)[0] == "REFERENCE_SELF_INCONSISTENT"
    assert evaluate_adversary_terminal_gate({**full, "total_cases": 0, "passed_cases": 0}, True)[
        0
    ] == ("REFERENCE_SELF_INCONSISTENT")
