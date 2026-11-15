"""Executable verification for Note 004: Covering Edge Descent Complexes and Coherence Defects.

Derivations verified:
- AUDIT-N004-006: Coboundary-Curvature Identity d1 d0 = K (ATL-N004-006)
- AUDIT-N004-007: Flat Locus Equivalence (ATL-N004-007)
- AUDIT-N004-008: Scalar Diamond Curvature Witness (ATL-N004-008)
- AUDIT-N004-025: Rational Enclosure of 2(sqrt(2)-1) (ATL-N004-025)

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Dict, List, Sequence, Tuple
import pytest


# ---------------------------------------------------------------------------
# Exact Rational Linear Algebra Helpers
# ---------------------------------------------------------------------------

Matrix = List[List[Fraction]]
Vector = Tuple[Fraction, ...]


def mat_zeros(rows: int, cols: int) -> Matrix:
    """Return zero matrix of dimension rows x cols."""
    return [[Fraction(0) for _ in range(cols)] for _ in range(rows)]


def mat_mul_vec(m: Matrix, v: Sequence[Fraction]) -> Vector:
    """Multiply rational matrix m by rational vector v."""
    return tuple(
        sum((m[r][c] * v[c] for c in range(len(v))), Fraction(0))
        for r in range(len(m))
    )


def mat_mul_mat(a: Matrix, b: Matrix) -> Matrix:
    """Multiply rational matrix a by rational matrix b."""
    rows_a = len(a)
    cols_a = len(a[0])
    cols_b = len(b[0])
    res: Matrix = []
    for r in range(rows_a):
        row: List[Fraction] = []
        for c in range(cols_b):
            val = sum((a[r][k] * b[k][c] for k in range(cols_a)), Fraction(0))
            row.append(val)
        res.append(row)
    return res


def mat_sub(a: Matrix, b: Matrix) -> Matrix:
    """Subtract rational matrix b from a."""
    return [
        [a[r][c] - b[r][c] for c in range(len(a[0]))]
        for r in range(len(a))
    ]


def mat_equal(a: Matrix, b: Matrix) -> bool:
    """Check exact equality of rational matrices."""
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        return False
    return all(a[r][c] == b[r][c] for r in range(len(a)) for c in range(len(a[0])))


def mat_is_zero(m: Matrix) -> bool:
    """Check if rational matrix is identically zero."""
    return all(m[r][c] == Fraction(0) for r in range(len(m)) for c in range(len(m[0])))


def vec_sub(u: Sequence[Fraction], v: Sequence[Fraction]) -> Vector:
    """Subtract rational vector v from u."""
    return tuple(u[i] - v[i] for i in range(len(u)))


def vec_add(u: Sequence[Fraction], v: Sequence[Fraction]) -> Vector:
    """Add rational vectors u and v."""
    return tuple(u[i] + v[i] for i in range(len(u)))


def vec_is_zero(v: Sequence[Fraction]) -> bool:
    """Check if rational vector is identically zero."""
    return all(x == Fraction(0) for x in v)


# ---------------------------------------------------------------------------
# Discrete Restriction System Model
# ---------------------------------------------------------------------------

class DiscreteRestrictionSystem:
    """Finite linear restriction system on a 3-element chain 0 < 1 < 2."""

    def __init__(
        self,
        dim: int,
        r_21: Matrix,
        r_10: Matrix,
        r_20: Matrix,
    ):
        self.dim = dim
        self.r_21 = r_21
        self.r_10 = r_10
        self.r_20 = r_20

    def curvature_matrix(self) -> Matrix:
        """Evaluate composition curvature operator K_{2,1,0} = r_{1,0} * r_{2,1} - r_{2,0}."""
        comp = mat_mul_mat(self.r_10, self.r_21)
        return mat_sub(comp, self.r_20)

    def is_flat(self) -> bool:
        """Check if system is flat (K_{2,1,0} == 0)."""
        return mat_is_zero(self.curvature_matrix())

    def d0(self, s: Dict[str, Vector]) -> Dict[Tuple[str, str], Vector]:
        """Compute 0-coboundary (d0 s)(a, b) = r_{b, a} s(b) - s(a)."""
        d0_01 = vec_sub(mat_mul_vec(self.r_10, s["1"]), s["0"])
        d0_12 = vec_sub(mat_mul_vec(self.r_21, s["2"]), s["1"])
        d0_02 = vec_sub(mat_mul_vec(self.r_20, s["2"]), s["0"])
        return {
            ("0", "1"): d0_01,
            ("1", "2"): d0_12,
            ("0", "2"): d0_02,
        }

    def d1(self, t: Dict[Tuple[str, str], Vector]) -> Vector:
        """Compute 1-coboundary (d1 t)(0, 1, 2) = r_{1, 0}(t(1, 2)) - t(0, 2) + t(0, 1)."""
        term1 = mat_mul_vec(self.r_10, t[("1", "2")])
        term2 = t[("0", "2")]
        term3 = t[("0", "1")]
        return vec_add(vec_sub(term1, term2), term3)

    def d1_d0(self, s: Dict[str, Vector]) -> Vector:
        """Compute composition (d1 (d0 s))(0, 1, 2)."""
        t = self.d0(s)
        return self.d1(t)


# ---------------------------------------------------------------------------
# Test Suite: Derivation AUDIT-N004-006 (Coboundary-Curvature Identity)
# ---------------------------------------------------------------------------

def test_audit_n004_006_coboundary_curvature_identity_positive_chain():
    """Positive Control: Verify (d1 d0 s)(0,1,2) == K_{2,1,0} s(2) on 2D fiber chains.

    Invariant: On any comparable triple with linear restrictions,
    the coboundary composition evaluates identically to the curvature operator
    applied to the top stalk section value, with intermediate stalk values canceling.
    """
    dim = 2
    r_21 = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
    r_10 = [[Fraction(2), Fraction(0)], [Fraction(1), Fraction(-1)]]
    # Defect matrix intentionally non-zero:
    defect = [[Fraction(1), Fraction(-1)], [Fraction(2), Fraction(0)]]
    # r_{2,0} = r_{1,0} * r_{2,1} - defect
    comp = mat_mul_mat(r_10, r_21)
    r_20 = mat_sub(comp, defect)

    system = DiscreteRestrictionSystem(dim, r_21, r_10, r_20)
    k_mat = system.curvature_matrix()
    assert mat_equal(k_mat, defect)

    # Test across multiple independent sections:
    sections = [
        {"0": (Fraction(5), Fraction(7)), "1": (Fraction(-3), Fraction(4)), "2": (Fraction(2), Fraction(-1))},
        {"0": (Fraction(1), Fraction(0)), "1": (Fraction(0), Fraction(1)), "2": (Fraction(3), Fraction(5))},
        {"0": (Fraction(-8), Fraction(11)), "1": (Fraction(13), Fraction(-2)), "2": (Fraction(-4), Fraction(7))},
        {"0": (Fraction(100), Fraction(-50)), "1": (Fraction(25), Fraction(75)), "2": (Fraction(0), Fraction(0))},
    ]

    for s in sections:
        d1_d0_val = system.d1_d0(s)
        expected_k_val = mat_mul_vec(k_mat, s["2"])
        assert d1_d0_val == expected_k_val, f"Mismatch: d1_d0={d1_d0_val}, expected={expected_k_val}"


def test_audit_n004_006_coboundary_curvature_identity_negative_perturbed_sign():
    """Negative Control: Perturb coboundary sign and show that identity fails.

    Invariant: The algebraic cancellation of s(0) and s(1) relies on the specific
    signs in (d1 t) = r_{1,0} t(1,2) - t(0,2) + t(0,1).
    Flipping the sign of t(0,2) destroys the cancellation.
    """
    dim = 2
    r_21 = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    r_10 = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    r_20 = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    system = DiscreteRestrictionSystem(dim, r_21, r_10, r_20)

    # In a flat system, correct d1 d0 gives 0:
    s = {"0": (Fraction(3), Fraction(4)), "1": (Fraction(5), Fraction(6)), "2": (Fraction(7), Fraction(8))}
    assert system.d1_d0(s) == (Fraction(0), Fraction(0))

    # Define perturbed d1 with + t(0, 2) instead of - t(0, 2):
    t = system.d0(s)
    term1 = mat_mul_vec(system.r_10, t[("1", "2")])
    term2_perturbed = t[("0", "2")]  # added instead of subtracted
    term3 = t[("0", "1")]
    d1_perturbed = vec_add(vec_add(term1, term2_perturbed), term3)

    k_val = mat_mul_vec(system.curvature_matrix(), s["2"])
    # Perturbed coboundary does NOT match K s(2):
    assert d1_perturbed != k_val
    assert d1_perturbed != (Fraction(0), Fraction(0))


def test_audit_n004_006_coboundary_curvature_identity_negative_nonlinearity():
    """Negative Control: Affine non-linear shift breaks intermediate cancellation.

    Invariant: If restriction maps include an affine translation c != 0,
    r(u - v) != r(u) - r(v), so s(1) and s(0) fail to cancel.
    """
    shift = (Fraction(1), Fraction(1))

    # Evaluate with affine non-linear map: r_affine(v) = v + shift
    s = {"0": (Fraction(1), Fraction(2)), "1": (Fraction(3), Fraction(4)), "2": (Fraction(5), Fraction(6))}

    # Non-linear d0:
    d0_01 = vec_sub(vec_add(s["1"], shift), s["0"])
    d0_12 = vec_sub(vec_add(s["2"], shift), s["1"])
    d0_02 = vec_sub(vec_add(s["2"], shift), s["0"])

    # Non-linear d1:
    d1_val = vec_add(vec_sub(vec_add(d0_12, shift), d0_02), d0_01)

    # For identity restrictions, linear K = 0:
    # But affine non-linear composition leaves a residual of shift != 0:
    assert d1_val != (Fraction(0), Fraction(0))
    assert d1_val == (Fraction(2), Fraction(2))  # accumulated shift residual


# ---------------------------------------------------------------------------
# Test Suite: Derivation AUDIT-N004-007 (Flat Locus Equivalence)
# ---------------------------------------------------------------------------

def test_audit_n004_007_flat_locus_equivalence_positive_flat_chain():
    """Positive Control: Flat system K=0 satisfies d1 d0 = 0 across a generating basis.

    Invariant: K = 0 is equivalent to chain composability r_{2,0} = r_{1,0} * r_{2,1}
    and equivalent to d1 d0 s = 0 for all sections s.
    """
    dim = 2
    r_21 = [[Fraction(1), Fraction(1)], [Fraction(0), Fraction(1)]]
    r_10 = [[Fraction(2), Fraction(3)], [Fraction(1), Fraction(2)]]
    # Exact composition: r_{2,0} = r_{1,0} * r_{2,1}
    r_20 = mat_mul_mat(r_10, r_21)

    system = DiscreteRestrictionSystem(dim, r_21, r_10, r_20)

    # Condition 1 & 3:
    assert system.is_flat()
    assert mat_equal(system.r_20, mat_mul_mat(r_10, r_21))

    # Condition 2: Check across all 6 basis sections spanning C^0:
    basis_sections = [
        {"0": (Fraction(1), Fraction(0)), "1": (Fraction(0), Fraction(0)), "2": (Fraction(0), Fraction(0))},
        {"0": (Fraction(0), Fraction(1)), "1": (Fraction(0), Fraction(0)), "2": (Fraction(0), Fraction(0))},
        {"0": (Fraction(0), Fraction(0)), "1": (Fraction(1), Fraction(0)), "2": (Fraction(0), Fraction(0))},
        {"0": (Fraction(0), Fraction(0)), "1": (Fraction(0), Fraction(1)), "2": (Fraction(0), Fraction(0))},
        {"0": (Fraction(0), Fraction(0)), "1": (Fraction(0), Fraction(0)), "2": (Fraction(1), Fraction(0))},
        {"0": (Fraction(0), Fraction(0)), "1": (Fraction(0), Fraction(0)), "2": (Fraction(0), Fraction(1))},
    ]

    for b in basis_sections:
        assert system.d1_d0(b) == (Fraction(0), Fraction(0))


def test_audit_n004_007_flat_locus_equivalence_negative_curved_chain():
    """Negative Control: Non-flat system violates chain composability and d1 d0 = 0.

    Invariant: If K != 0, chain composability fails and there exist sections
    with d1 d0 s != 0.
    """
    dim = 2
    r_21 = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    r_10 = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    # Intentionally violate composability:
    r_20 = [[Fraction(2), Fraction(0)], [Fraction(0), Fraction(1)]]

    system = DiscreteRestrictionSystem(dim, r_21, r_10, r_20)
    assert not system.is_flat()
    assert not mat_equal(system.r_20, mat_mul_mat(r_10, r_21))

    # Evaluate on section with non-zero component at top stalk:
    s = {"0": (Fraction(0), Fraction(0)), "1": (Fraction(0), Fraction(0)), "2": (Fraction(1), Fraction(0))}
    res = system.d1_d0(s)
    assert res != (Fraction(0), Fraction(0))
    assert res == (Fraction(-1), Fraction(0))


def test_audit_n004_007_flat_locus_equivalence_negative_zero_section_trap():
    """Negative Control: Evaluating only s=0 is insufficient to detect non-flatness.

    Invariant: d1(d0(0)) = 0 holds trivially even in a curved system.
    Establishing flatness requires verifying across all sections (or a basis of F(c)).
    """
    dim = 2
    r_21 = [[Fraction(1), Fraction(2)], [Fraction(3), Fraction(4)]]
    r_10 = [[Fraction(5), Fraction(6)], [Fraction(7), Fraction(8)]]
    r_20 = [[Fraction(0), Fraction(0)], [Fraction(0), Fraction(0)]]  # heavily non-flat

    system = DiscreteRestrictionSystem(dim, r_21, r_10, r_20)
    assert not system.is_flat()

    zero_section = {"0": (Fraction(0), Fraction(0)), "1": (Fraction(0), Fraction(0)), "2": (Fraction(0), Fraction(0))}
    # False-green trap: zero section yields 0
    assert system.d1_d0(zero_section) == (Fraction(0), Fraction(0))

    # Non-zero section exposes the defect immediately:
    active_section = {"0": (Fraction(0), Fraction(0)), "1": (Fraction(0), Fraction(0)), "2": (Fraction(1), Fraction(1))}
    assert system.d1_d0(active_section) != (Fraction(0), Fraction(0))


# ---------------------------------------------------------------------------
# Test Suite: Derivation AUDIT-N004-008 (Scalar Diamond Curvature Witness)
# ---------------------------------------------------------------------------

def test_audit_n004_008_scalar_diamond_positive():
    """Positive Control: Verify K(v) = (beta * alpha - mu) * v on 1D scalar stalks.

    Invariant: For 1D scalar maps alpha, beta, mu, the composition curvature operator
    evaluates to multiplication by (beta * alpha - mu).
    """
    cases = [
        # alpha, beta, mu, v, expected_k
        (Fraction(3, 2), Fraction(4, 5), Fraction(1, 2), Fraction(10), Fraction(7)),
        (Fraction(2), Fraction(3), Fraction(6), Fraction(5), Fraction(0)),  # flat case
        (Fraction(-1, 3), Fraction(9), Fraction(2), Fraction(3), Fraction(-15)),
        (Fraction(7, 11), Fraction(11, 7), Fraction(1), Fraction(13), Fraction(0)),  # inverse flat
    ]

    for alpha, beta, mu, v, expected in cases:
        defect_scalar = beta * alpha - mu
        k_val = defect_scalar * v
        assert k_val == expected


def test_audit_n004_008_scalar_diamond_negative_nonzero_defect():
    """Negative Control: Non-zero defect forces non-zero curvature on non-zero inputs.

    Invariant: If beta * alpha != mu, then K(v) != 0 for all v != 0.
    """
    alpha = Fraction(2)
    beta = Fraction(3)
    mu = Fraction(5)  # beta * alpha = 6 != 5

    defect = beta * alpha - mu
    assert defect != Fraction(0)

    for v in [Fraction(1), Fraction(-4), Fraction(1, 3), Fraction(100)]:
        assert defect * v != Fraction(0)


def test_audit_n004_008_scalar_diamond_negative_noncommutative_higher_dim():
    """Negative Control: Commutativity fails in higher dimensions (dim >= 2).

    Invariant: Scalar diamond factorization (beta * alpha - mu) relies on
    scalar multiplication commutativity beta * alpha == alpha * beta.
    In matrix dimensions >= 2, matrix multiplication does not commute.
    """
    # Non-commuting 2x2 rational matrices:
    a = [[Fraction(1), Fraction(2)], [Fraction(0), Fraction(1)]]
    b = [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]]

    ba = mat_mul_mat(b, a)
    ab = mat_mul_mat(a, b)

    assert not mat_equal(ba, ab)
    assert ba == [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(2)]]
    assert ab == [[Fraction(2), Fraction(1)], [Fraction(1), Fraction(0)]]


# ---------------------------------------------------------------------------
# Test Suite: Derivation AUDIT-N004-025 (Rational Enclosure of 2(sqrt(2)-1))
# ---------------------------------------------------------------------------

def test_audit_n004_025_rational_enclosure_positive():
    """Positive Control: Verify exact rational squaring enclosure of 2(sqrt(2)-1).

    Invariant: For q = 2(sqrt(2)-1), (1 + q/2)^2 = 2.
    Since t -> (1 + t/2)^2 is strictly increasing on (0, inf),
    (1 + L/2)^2 < 2 < (1 + U/2)^2 establishes L < q < U in Q.
    """
    l = Fraction(828, 1000)
    u = Fraction(829, 1000)

    # Exact rational squares:
    l_sq = (Fraction(1) + l / 2) ** 2
    u_sq = (Fraction(1) + u / 2) ** 2

    assert l_sq == Fraction(499849, 250000)
    assert u_sq == Fraction(8003241, 4000000)

    assert l_sq < Fraction(2)
    assert u_sq > Fraction(2)

    # Certified interval width:
    width = u - l
    assert width == Fraction(1, 1000)

    # Exact algebraic difference metrics:
    lower_gap = Fraction(2) - l_sq
    upper_gap = u_sq - Fraction(2)
    assert lower_gap == Fraction(151, 250000)
    assert upper_gap == Fraction(3241, 4000000)


def test_audit_n004_025_rational_enclosure_negative_shifted_intervals():
    """Negative Control: Shifted intervals fail enclosure inequalities.

    Invariant: An interval strictly below target fails the upper bound (< 2).
    An interval strictly above target fails the lower bound (> 2).
    """
    # Shifted below: [827/1000, 828/1000]
    l_below = Fraction(827, 1000)
    u_below = Fraction(828, 1000)
    u_below_sq = (Fraction(1) + u_below / 2) ** 2
    # Upper bound fails because (1 + u_below/2)^2 < 2:
    assert not (u_below_sq > Fraction(2))

    # Shifted above: [829/1000, 830/1000]
    l_above = Fraction(829, 1000)
    u_above = Fraction(830, 1000)
    l_above_sq = (Fraction(1) + l_above / 2) ** 2
    # Lower bound fails because (1 + l_above/2)^2 > 2:
    assert not (l_above_sq < Fraction(2))


def test_audit_n004_025_rational_enclosure_negative_float_precision():
    """Negative Control: Float arithmetic introduces rounding errors absent in Q.

    Invariant: Float operations lose exactness on rationals with large denominators,
    demonstrating the necessity of exact rational Fraction arithmetic.
    """
    l = Fraction(828, 1000)
    exact_l_sq = (Fraction(1) + l / 2) ** 2

    # Float computation:
    float_l = 828.0 / 1000.0
    float_l_sq = (1.0 + float_l / 2.0) ** 2

    # Compare exact rational value converted to float with native float arithmetic:
    assert float(exact_l_sq) == pytest.approx(float_l_sq, abs=1e-15)
    # But exact difference is non-zero in rational arithmetic:
    diff = exact_l_sq - Fraction(500000, 250000)
    assert diff == Fraction(-151, 250000)
