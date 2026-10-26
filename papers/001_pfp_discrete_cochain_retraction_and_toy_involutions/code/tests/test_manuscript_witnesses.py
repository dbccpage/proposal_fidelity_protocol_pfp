"""The manuscript's worked witnesses, checked in exact rational arithmetic."""

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demo1_holonomy import run_demo1
from symbol_game_governor import (
    ConstraintGraph,
    Edge,
    MoveType,
    Phi1Certificate,
    SymbolGameGovernor,
    compute_exact_phi_1,
    verify_phi_1_certificate,
)

VERTICES = ("a", "b", "c")
TRIANGLE = (("a", "b", 1), ("b", "c", 2), ("c", "a", 3))
REPORTS = {("a", "b"): 1, ("b", "c"): 1, ("c", "a"): 1}


def test_manuscript_triangle_costs_and_certificate():
    governor = SymbolGameGovernor(
        ConstraintGraph(VERTICES, tuple(Edge(u, v, w) for u, v, w in TRIANGLE)), dict(REPORTS)
    )
    assert governor.compute_section_defect(governor.section) == 6
    best = {"a": Fraction(0), "b": Fraction(-2), "c": Fraction(-1)}
    assert governor.compute_section_defect(best) == 3
    unit_flow = {("a", "b"): Fraction(1), ("b", "c"): Fraction(1), ("c", "a"): Fraction(1)}
    manual = Phi1Certificate(Fraction(3), best, unit_flow, Fraction(0))
    assert verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, manual)
    built = compute_exact_phi_1(VERTICES, TRIANGLE, REPORTS)
    assert built.phi_1 == 3
    assert verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, built)
    exact = dict(REPORTS)
    exact[("c", "a")] = -2
    assert compute_exact_phi_1(VERTICES, TRIANGLE, exact).phi_1 == 0


def test_rational_descent_exhausts_fuel_without_reaching_minimum():
    governor = SymbolGameGovernor(ConstraintGraph(("a", "b"), (Edge("a", "b", 1),)), {("a", "b"): 1})
    costs = []
    for t in range(1, 11):
        step = governor.execute_move(MoveType.CUT, {"potentials": {"b": 1 - Fraction(1, 2**t)}})
        assert step.admitted
        costs.append(step.defect)
    assert costs == [Fraction(1, 2**t) for t in range(1, 11)]
    assert governor.compute_phi_1()[0] == 0 < costs[-1]
    assert not governor.execute_move(MoveType.VERIFY, {}).admitted


def test_demo1_replays_every_manuscript_witness(capsys):
    assert run_demo1() is True
    output = capsys.readouterr().out
    assert "FAIL" not in output
    assert "DEMO 1 PASSED" in output
