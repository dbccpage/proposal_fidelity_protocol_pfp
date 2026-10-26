"""
Unit and integration tests for symbol_game_matolcsi_conjecture2.py.
Verifies the illustrative carrier mechanics only:
1. Declared fixture values are preserved without being promoted to a computation.
2. Epistemic Immune System triggers quarantine and mints Antibody #A-G1-001.
3. Strict Lyapunov descent on the retracted Hadamard cube variety to Phi_1 = 0.
"""

from fractions import Fraction

from symbol_game_matolcsi_conjecture2 import (
    DangerSignal,
    create_g1_conjecture2_carrier_graph,
    evaluate_thymic_selection,
    run_symbol_game_matolcsi_conjecture2_bout,
)


def test_carrier_graph_creation(native_functional):
    graph, gov = create_g1_conjecture2_carrier_graph()
    assert len(graph.vertices) == 5
    assert len(graph.edges) == 6
    assert gov.primary_obstruction() == Fraction(0)


def test_danger_signal_quarantine_trigger():
    clean = DangerSignal(Fraction(0), Fraction(0), 0)
    assert not clean.is_quarantine_triggered()

    tainted = DangerSignal(Fraction(9), Fraction(9), 0)
    assert tainted.is_quarantine_triggered()


def test_thymic_selection():
    admitted = {"ASSERT", "CUT", "VERIFY", "RETRACT"}
    res1 = evaluate_thymic_selection("CUT", admitted)
    assert res1.admitted
    assert res1.is_self

    res2 = evaluate_thymic_selection("GUESS", admitted)
    assert not res2.admitted
    assert not res2.is_self


def test_symbol_game_matolcsi_bout_execution(native_functional):
    res = run_symbol_game_matolcsi_conjecture2_bout()
    assert res["status"] == "ILLUSTRATIVE_GRAPH_COMPLETE"
    assert res["initial_phi1"] == "9"
    assert res["final_phi1"] == "0"
    assert res["declared_fixture_g1"] == "9"
    assert res["declared_fixture_g2_product"] == "1296"
    assert res["cemetery_records"] == 2
    assert len(res["terminal_hash"]) == 64
