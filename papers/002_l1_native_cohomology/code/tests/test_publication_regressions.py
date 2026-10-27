"""Receipt regressions proposed by the publication review at 79fd9db72805."""

from fractions import Fraction
from dataclasses import replace

import pytest

import l1_cohomology as lc


def test_rational_weights_preserve_l1_receipt_roundtrip():
    """Primal integrality must not be confused with dual integrality."""
    graph = lc.DirectedGraph.cycle(3, weights=[Fraction(1, 2)] * 3)
    omega = [Fraction(1), Fraction(0), Fraction(0)]
    receipt = lc.L1QuotientSolver.solve(graph, omega)

    assert receipt.primal_norm == Fraction(1, 2)
    assert receipt.dual_bound == Fraction(1, 2)
    assert receipt.duality_gap == 0
    assert all(x.denominator == 1 for x in receipt.primal_potential)
    assert all(x.denominator == 1 for x in receipt.primal_residual)
    assert receipt.dual_circulation == (Fraction(1, 2),) * 3
    assert lc.check_certificate_receipt(receipt, graph, omega)


def test_linf_rejects_forged_zero_gap_with_infeasible_primal(monkeypatch):
    """A backend status and zero reported gap cannot replace feasibility checks."""
    graph = lc.DirectedGraph.cycle(3)

    def forged_solver(c, A, b, max_iter=10000):
        # t=0, f=0 and z=0 have zero reported gap but are primal infeasible.
        return lc.SimplexResult(
            "OPTIMAL", Fraction(0), [Fraction(0)] * len(c), []
        )

    monkeypatch.setattr(
        lc.ExactTwoPhaseSimplexSolver,
        "solve_standard_lp",
        staticmethod(forged_solver),
    )
    with pytest.raises(lc.CertificateViolationError):
        lc.ExactRationalLinfChebyshevSolver.solve(graph, [1, 0, 0])


@pytest.mark.parametrize("weights", [[1, 1, 1], [Fraction(1, 2), 2, 3]])
def test_linf_receipt_roundtrip_and_weighted_cycle_formula(weights):
    graph = lc.DirectedGraph.cycle(3, weights=weights)
    receipt = lc.ExactRationalLinfChebyshevSolver.solve(graph, [1, 0, 0])
    expected = 1 / sum((1 / Fraction(w) for w in weights), Fraction(0))
    assert receipt.chebyshev_norm == expected
    assert receipt.dual_circulation == (expected,) * 3
    assert lc.check_linf_certificate_receipt(receipt, graph, [1, 0, 0])


@pytest.mark.parametrize("field,value", [
    ("primal_potential", (Fraction(0),)),
    ("primal_residual", (Fraction(0),) * 3),
    ("dual_circulation", (Fraction(1, 3), Fraction(0), Fraction(0))),
    ("dual_circulation", (Fraction(1),) * 3),
    ("dual_circulation", (Fraction(0),) * 3),
    ("dual_bound", Fraction(0)),
    ("duality_gap", Fraction(1)),
    ("chebyshev_norm", Fraction(-1)),
    ("chebyshev_norm", Fraction(1)),
    ("chebyshev_norm", 1 / 3),
    ("peak_edges", ()),
    ("status", "UNVERIFIED"),
])
def test_linf_validator_rejects_tampered_receipts(field, value):
    graph = lc.DirectedGraph.cycle(3)
    receipt = lc.ExactRationalLinfChebyshevSolver.solve(graph, [1, 0, 0])
    with pytest.raises(lc.CertificateViolationError):
        lc.check_linf_certificate_receipt(replace(receipt, **{field: value}), graph, [1, 0, 0])


def test_linf_zero_flux_receipt_roundtrip():
    graph = lc.DirectedGraph.cycle(3)
    receipt = lc.ExactRationalLinfChebyshevSolver.solve(graph, [0, 0, 0])
    assert receipt.chebyshev_norm == 0
    assert lc.check_linf_certificate_receipt(receipt, graph, [0, 0, 0])
