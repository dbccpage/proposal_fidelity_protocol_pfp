# AuthorityEffect: None.
"""Tests for Arm E deterministic tactic portfolio in C041."""

from omega_engine_pfp.tests.demo_004.e_formal_math.c041_lean4_finite_lemma_proofs.reference_solver.tactic_portfolio import solve_deterministic


def test_tactic_portfolio_proof():
    case = {
        "case_id": "test_port_01",
        "statement": "∀ a b : Fin 3, a + b = b + a",
        "prelude": "",
    }
    ans = solve_deterministic(case)
    assert ans["status"] == "SOLVED"
    assert ans["kind"] == "PROOF"
    assert "proof" in ans


def test_tactic_portfolio_refutation():
    case = {
        "case_id": "test_port_02",
        "statement": "∀ a : Fin 4, a + 1 = a",
        "prelude": "",
    }
    ans = solve_deterministic(case)
    assert ans["status"] == "SOLVED"
    assert ans["kind"] == "REFUTATION"


def test_tactic_portfolio_out_of_scope():
    case = {
        "case_id": "test_port_bad",
        "statement": "bad_syntax 1 = 1",
        "prelude": "def bad_syntax (n : Nat) : Nat := n + + 1\n",
    }
    ans = solve_deterministic(case)
    assert ans["status"] == "OUT_OF_SCOPE"
