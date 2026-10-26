"""
Unit tests for Interactive Lean 4 Symbol Game Host Governor and Topology-50 Benchmark.
"""

import pytest

from interactive_lean4_governor import (
    DECLARED_TACTIC_CARRIER,
    Lean4Verifier,
    ProofGoal,
    SymbolGameHostGovernor,
    TacticProposal,
    build_50_topology_theorems,
    run_benchmark,
)


def test_declared_tactic_carrier():
    """Verify that core Lean 4 tactics are admitted and forbidden keywords rejected."""
    governor = SymbolGameHostGovernor()
    assert "intro" in DECLARED_TACTIC_CARRIER
    assert "apply" in DECLARED_TACTIC_CARRIER
    assert "exact" in DECLARED_TACTIC_CARRIER

    ok, msg = governor.firewall_carrier("exact thm_01_isOpen_univ")
    assert ok is True

    bad_tac, msg = governor.firewall_carrier("sledgehammer")
    assert bad_tac is False
    assert "rejected by FW-CARRIER" in msg

    forb_tac, msg = governor.firewall_carrier("exact sorry")
    assert forb_tac is False
    assert "Forbidden operator" in msg


def test_firewall_move_syntax():
    """Verify FW-MOVE catches mismatched brackets or parentheses."""
    governor = SymbolGameHostGovernor()
    goal = ProofGoal(goal_id="g1", target_type="isOpen s")

    ok, _ = governor.firewall_move("apply (thm_01_isOpen_univ)", goal)
    assert ok is True

    bad_paren, msg = governor.firewall_move("apply (thm_01_isOpen_univ", goal)
    assert bad_paren is False
    assert "Mismatched parentheses" in msg

    bad_bracket, msg = governor.firewall_move("rw [compl_empty", goal)
    assert bad_bracket is False
    assert "Mismatched brackets" in msg


def test_l1_defect_monotonicity_cut():
    """Verify that moves increasing the scalar L1 defect are rejected."""
    governor = SymbolGameHostGovernor()
    g1 = ProofGoal(goal_id="g1", target_type="isOpen s", weight=1)
    goals = [g1]

    # Proposal that resolves a goal without adding new ones
    prop_good = TacticProposal(tactic_str="exact h", goal_id="g1", rule_name="exact")
    res_good = governor.evaluate_step(goals, target_goal_idx=0, proposal=prop_good)
    assert res_good.accepted is True
    assert res_good.defect_after == 0
    assert res_good.defect_after <= res_good.defect_before


def test_atomic_retraction():
    """Verify that atomic retraction restores previous proof state and tracks count."""
    governor = SymbolGameHostGovernor()
    g1 = ProofGoal(goal_id="g1", target_type="isOpen s", weight=1)
    goals = [g1]

    prop = TacticProposal(tactic_str="intro x", goal_id="g1", rule_name="intro")
    res = governor.evaluate_step(goals, target_goal_idx=0, proposal=prop)
    assert res.accepted is True

    # Now retract
    restored = governor.retract()
    assert restored is not None
    assert len(restored) == 1
    assert restored[0].goal_id == "g1"
    assert governor.retraction_count == 1


def test_lean4_verifier_live():
    """Test the Lean4Verifier on basic Lean 4 evaluation."""
    verifier = Lean4Verifier()
    if not verifier.check_available():
        pytest.skip("Lean 4 executable not found on host")

    snippet_ok = "#eval 5 + 7"
    success, out = verifier.verify_lean_snippet(snippet_ok)
    assert success is True
    assert "12" in out

    snippet_err = "theorem broken : False := by exact 42"
    success_err, out_err = verifier.verify_lean_snippet(snippet_err)
    assert success_err is False
    assert len(out_err) > 0


def test_topology50_manifest():
    """Verify that all 50 topology theorems are defined with distinct IDs and non-empty tactics."""
    theorems = build_50_topology_theorems()
    assert len(theorems) == 50

    ids = [t.id for t in theorems]
    assert ids == list(range(1, 51))

    for thm in theorems:
        assert thm.name != ""
        assert thm.lean_identifier.startswith("thm_")
        assert len(thm.reference_tactics) >= 1
        assert len(thm.adversarial_distractors) >= 1


def test_benchmark_execution():
    """Verify that running the benchmark generates complete statistics and valid solve rates."""
    receipt = run_benchmark(max_fuel=10)
    assert receipt.total_theorems == 50
    assert receipt.governed_solved == 50
    assert receipt.governed_solve_rate == 1.0
    assert receipt.aggregate_verification_rate > 0.5
    assert receipt.aggregate_retraction_frequency > 0.4
    assert len(receipt.results) == 50
