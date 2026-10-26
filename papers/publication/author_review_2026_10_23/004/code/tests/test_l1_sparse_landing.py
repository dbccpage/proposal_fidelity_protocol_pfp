"""
Unit tests for the weighted NSP unique sparse landing module (Paper 032 Section 5.4).
Reference: Paper 032 (PO-032), Theorems 5.3 and 5.4; legacy Paper 040i.
"""

from fractions import Fraction

from l1_sparse_landing import (
    certify_unique_landing,
    cycle_space_basis,
    null_space,
    run_landing_benchmark,
    solve_linear,
    three_cycle,
    three_cycle_demo,
    weighted_l1_cost,
)


def test_exact_linear_algebra_over_rationals():
    """Null space and linear solve are exact over Q."""
    # A = [[1, 1, 1]] ; null space is 2-dimensional, orthogonal to (1,1,1).
    basis = null_space([[Fraction(1), Fraction(1), Fraction(1)]], 3)
    assert len(basis) == 2
    for vec in basis:
        assert sum(vec, Fraction(0)) == 0  # each basis vector sums to zero
    x = solve_linear([[Fraction(2), Fraction(0)], [Fraction(0), Fraction(3)]],
                     [Fraction(1), Fraction(1)])
    assert x == [Fraction(1, 2), Fraction(1, 3)]
    assert solve_linear([[Fraction(1)], [Fraction(1)]], [Fraction(1), Fraction(2)]) is None


def test_three_cycle_cycle_space_is_one_dimensional():
    """The directed 3-cycle has cycle rank 1, spanned by the all-ones circulation."""
    basis = cycle_space_basis(three_cycle((1, 1, 1)))
    assert len(basis) == 1
    w = basis[0]
    # Proportional to (1,1,1): all entries equal and nonzero.
    assert w[0] == w[1] == w[2] and w[0] != 0


def test_uniform_weights_landing_is_not_unique():
    """Uniform weights tie: NSP fails, uniqueness is not certified (§5.4)."""
    target = {("0", "1"): Fraction(1), ("1", "2"): Fraction(0), ("2", "0"): Fraction(0)}
    cert = certify_unique_landing(three_cycle((1, 1, 1)), target)
    assert cert.phi1 == Fraction(1)
    assert cert.unique is False
    # Two distinct residuals attain the same weighted cost 1.
    assert weighted_l1_cost([Fraction(1), Fraction(0), Fraction(0)], [1, 1, 1]) == Fraction(1)
    assert weighted_l1_cost([Fraction(0), Fraction(1), Fraction(0)], [1, 1, 1]) == Fraction(1)


def test_asymmetric_weights_landing_is_unique():
    """Asymmetric weights (1,2,2): NSP holds, unique sparse landing on e0 (§5.4)."""
    target = {("0", "1"): Fraction(1), ("1", "2"): Fraction(0), ("2", "0"): Fraction(0)}
    cert = certify_unique_landing(three_cycle((1, 2, 2)), target)
    assert cert.phi1 == Fraction(1)
    assert cert.unique is True
    assert cert.support == [0]                 # lightest edge only
    assert cert.sparsity == 1 == cert.cycle_rank  # saturates the sparsity bound
    assert cert.sparsity_bound_ok is True
    # Dual witness is a circulation in the cycle space with g_0 = omega_0 * sign(r*_0) = 1.
    assert cert.dual_witness is not None
    assert cert.dual_witness[0] == Fraction(1)


def test_landing_on_zero_is_unique_with_zero_residual():
    """A target that is already a coboundary lands exactly on Zero: r* = 0, unique."""
    # delta c0 for c0 = (0,1,0): e0 -> 1, e1 -> -1, e2 -> 0.
    target = {("0", "1"): Fraction(1), ("1", "2"): Fraction(-1), ("2", "0"): Fraction(0)}
    cert = certify_unique_landing(three_cycle((1, 2, 2)), target)
    assert cert.phi1 == Fraction(0)
    assert cert.support == []
    assert cert.sparsity == 0
    assert cert.unique is True


def test_sparsity_bound_across_family():
    """Every instance in the benchmark respects |supp(r*)| <= cycle rank (Thm 5.4)."""
    summary = run_landing_benchmark()
    assert summary["all_sparsity_bounds_satisfied"] is True
    for inst in summary["instances"]:
        assert inst["sparsity"] <= inst["cycle_rank"]


def test_demo_matches_paper_section_5_4():
    """The reported 3-cycle demo matches the §5.4 narrative."""
    demo = three_cycle_demo()
    assert demo["uniform_weights"]["unique"] is False
    assert demo["asymmetric_weights"]["unique"] is True
    assert demo["asymmetric_weights"]["support"] == [0]
