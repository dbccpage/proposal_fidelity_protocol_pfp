"""Executable verification for Note 003: Degree-Wise Obstruction Calculus and Symbolic DSL.

Derivations verified:
- AUDIT-N003-002: Degree separation on the triangle (ATL-N003-002)
- AUDIT-N003-003: Projection invariant admission (ATL-N003-003)
- AUDIT-N003-004: Rewrite rules as consequences of admitted invariants (ATL-N003-004)
- AUDIT-N003-005: Sign loss under magnitude aggregation (ATL-N003-005)

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
import itertools
from typing import List, Sequence, Tuple
import pytest


# ---------------------------------------------------------------------------
# Discrete Cochain Complex and Exact Arithmetic Helpers
# ---------------------------------------------------------------------------

Matrix = List[List[Fraction]]
Vector = Tuple[Fraction, ...]


def mat_mul_vec(m: Matrix, v: Sequence[Fraction]) -> Vector:
    """Multiply rational matrix m by rational vector v."""
    return tuple(
        sum((m[r][c] * v[c] for c in range(len(v))), Fraction(0, 1))
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
            val = sum((a[r][k] * b[k][c] for k in range(cols_a)), Fraction(0, 1))
            row.append(val)
        res.append(row)
    return res


def mat_equal(a: Matrix, b: Matrix) -> bool:
    """Check exact equality of rational matrices."""
    if len(a) != len(b) or len(a[0]) != len(b[0]):
        return False
    return all(a[r][c] == b[r][c] for r in range(len(a)) for c in range(len(a[0])))


def mat_is_zero(m: Matrix) -> bool:
    """Check if rational matrix is entirely zero."""
    return all(m[r][c] == Fraction(0, 1) for r in range(len(m)) for c in range(len(m[0])))


class MissingComplex2Error(RuntimeError):
    """Raised when 2-cell boundary d1 is requested but C^2 is absent."""


class C3Complex:
    """Exact discrete cell complex on the oriented 3-cycle C_3.

    Vertices: 0, 1, 2
    Edges: e0 = (0, 1), e1 = (1, 2), e2 = (2, 0)
    Optional 2-cell: sigma = (0, 1, 2) with oriented boundary e0 + e1 + e2.
    """

    def __init__(self, with_two_cell: bool = False) -> None:
        self.num_vertices = 3
        self.num_edges = 3
        self.with_two_cell = with_two_cell

        # d0 matrix: 3 edges x 3 vertices
        # (d0 f)_e0 = f1 - f0
        # (d0 f)_e1 = f2 - f1
        # (d0 f)_e2 = f0 - f2
        self.d0_matrix: Matrix = [
            [Fraction(-1), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(-1), Fraction(1)],
            [Fraction(1), Fraction(0), Fraction(-1)],
        ]

        if with_two_cell:
            # d1 matrix: 1 two-cell x 3 edges
            # (d1 omega)_sigma = omega_0 + omega_1 + omega_2
            self.d1_matrix: Matrix = [
                [Fraction(1), Fraction(1), Fraction(1)],
            ]
        else:
            self.d1_matrix = []

    def d0(self, f: Sequence[int | Fraction]) -> Vector:
        """Evaluate discrete coboundary d0: C^0 -> C^1."""
        if len(f) != self.num_vertices:
            raise ValueError(f"Expected 0-cochain of length {self.num_vertices}")
        f_frac = [Fraction(x) for x in f]
        return mat_mul_vec(self.d0_matrix, f_frac)

    def d1(self, omega: Sequence[int | Fraction]) -> Vector:
        """Evaluate discrete coboundary d1: C^1 -> C^2."""
        if not self.with_two_cell:
            raise MissingComplex2Error("Cannot evaluate d1: C^2 is absent (no 2-cell declared)")
        if len(omega) != self.num_edges:
            raise ValueError(f"Expected 1-cochain of length {self.num_edges}")
        omega_frac = [Fraction(x) for x in omega]
        return mat_mul_vec(self.d1_matrix, omega_frac)

    def compute_phi1(self, omega: Sequence[int | Fraction], search_radius: int | None = None) -> Fraction:
        """Compute exact integer l1 distance Phi_1(omega) = min_{f in Z^V} ||omega - d0 f||_1."""
        omega_frac = tuple(Fraction(x) for x in omega)
        if search_radius is None:
            max_val = max(abs(x) for x in omega_frac)
            search_radius = int(max_val) + 2

        best_val: Fraction | None = None

        # Search grid over integer potentials f with gauge f0 = 0 (since constant shifts leave d0 f unchanged)
        for f1 in range(-search_radius, search_radius + 1):
            for f2 in range(-search_radius, search_radius + 1):
                f_cand = (Fraction(0), Fraction(f1), Fraction(f2))
                d0_f = self.d0(f_cand)
                dist = sum(abs(omega_frac[i] - d0_f[i]) for i in range(self.num_edges))
                if best_val is None or dist < best_val:
                    best_val = dist
        assert best_val is not None
        return best_val

    def compute_gamma2(self, omega: Sequence[int | Fraction]) -> Fraction | None:
        """Compute closure defect Gamma_2 = ||d1 omega||_1 if C^2 is present, else None."""
        if not self.with_two_cell:
            return None
        d1_omega = self.d1(omega)
        return sum(abs(x) for x in d1_omega)


def check_projection_admission(pi_matrix: Matrix, d0_matrix: Matrix) -> Tuple[bool, bool]:
    """Verify exact rational matrix identities for projection admission:

    1. Idempotence: pi^2 == pi
    2. Exact-killing: pi * d0 == 0
    """
    pi_sq = mat_mul_mat(pi_matrix, pi_matrix)
    is_idempotent = mat_equal(pi_sq, pi_matrix)

    pi_d0 = mat_mul_mat(pi_matrix, d0_matrix)
    kills_exact = mat_is_zero(pi_d0)

    return (is_idempotent, kills_exact)


# ---------------------------------------------------------------------------
# Verification Tests
# ---------------------------------------------------------------------------

class TestAuditN003002DegreeSeparation:
    """Verifies AUDIT-N003-002: Degree separation on the triangle."""

    def test_cycle_sum_lower_bound_and_attainment(self) -> None:
        """Verifies that circulation sum of (1, 0, 0) is 1, so integer distance to im d0 is >= 1 and attained."""
        c3_without = C3Complex(with_two_cell=False)
        omega = (Fraction(1), Fraction(0), Fraction(0))

        # 1. Circulation sum on C3: for any d0 f, sum_e (d0 f)_e = (f1-f0)+(f2-f1)+(f0-f2) = 0
        for f in itertools.product(range(-2, 3), repeat=3):
            d0_f = c3_without.d0(f)
            assert sum(d0_f) == Fraction(0)

        # 2. Triangle inequality lower bound:
        # ||omega - d0 f||_1 = sum |omega_e - (d0 f)_e| >= |sum (omega_e - (d0 f)_e)| = |1 - 0| = 1
        phi1 = c3_without.compute_phi1(omega)
        assert phi1 == Fraction(1)

        # 3. Attainment at f = (0, 0, 0)
        d0_zero = c3_without.d0((0, 0, 0))
        assert sum(abs(omega[i] - d0_zero[i]) for i in range(3)) == Fraction(1)

    def test_two_cell_independence_and_gamma2_divergence(self) -> None:
        """Verifies Phi_1 is identical with or without 2-cell, while Gamma_2 is undefined without 2-cell and 1 with it."""
        omega = (Fraction(1), Fraction(0), Fraction(0))

        # Model 1: Graph-only (without 2-cell)
        c3_graph = C3Complex(with_two_cell=False)
        assert c3_graph.compute_phi1(omega) == Fraction(1)
        assert c3_graph.compute_gamma2(omega) is None
        with pytest.raises(MissingComplex2Error):
            c3_graph.d1(omega)

        # Model 2: Cell complex (with 2-cell attached)
        c3_cell = C3Complex(with_two_cell=True)
        # 2-cell attachment does not alter vertices, edges, or d0, so Phi_1 is identical
        assert c3_cell.compute_phi1(omega) == Fraction(1)
        # With 2-cell, d1 is defined and maps (1, 0, 0) to 1
        d1_omega = c3_cell.d1(omega)
        assert d1_omega == (Fraction(1),)
        gamma2 = c3_cell.compute_gamma2(omega)
        assert gamma2 == Fraction(1)

        # Cross-validation across varied integer cochains: Phi_1 never reads d1
        for test_cochain in [
            (Fraction(0), Fraction(1), Fraction(0)),
            (Fraction(1), Fraction(1), Fraction(1)),
            (Fraction(2), Fraction(-1), Fraction(3)),
        ]:
            assert c3_graph.compute_phi1(test_cochain) == c3_cell.compute_phi1(test_cochain)

    def test_negative_control_mutated_boundary(self) -> None:
        """Negative control: mutating 2-cell orientation changes d1 readout."""
        c3_cell = C3Complex(with_two_cell=True)
        # Mutate d1 boundary signs: e0 - e1 + e2 instead of e0 + e1 + e2
        mutated_d1 = [[Fraction(1), Fraction(-1), Fraction(1)]]
        omega = (Fraction(1), Fraction(0), Fraction(0))
        val = mat_mul_vec(mutated_d1, omega)
        assert val == (Fraction(1),)
        # On (0, 1, 0), original gives 1, mutated gives -1
        assert mat_mul_vec(c3_cell.d1_matrix, (Fraction(0), Fraction(1), Fraction(0))) == (Fraction(1),)
        assert mat_mul_vec(mutated_d1, (Fraction(0), Fraction(1), Fraction(0))) == (Fraction(-1),)


class TestAuditN003003ProjectionInvariantAdmission:
    """Verifies AUDIT-N003-003: Projection invariant admission."""

    def test_harmonic_projection_admission(self) -> None:
        """Checks that the standard rational harmonic projector Pi = (1/3) 1 1^T is admitted."""
        c3 = C3Complex(with_two_cell=True)
        one_third = Fraction(1, 3)
        pi_harmonic: Matrix = [
            [one_third, one_third, one_third],
            [one_third, one_third, one_third],
            [one_third, one_third, one_third],
        ]

        is_idempotent, kills_exact = check_projection_admission(pi_harmonic, c3.d0_matrix)
        assert is_idempotent is True
        assert kills_exact is True

    def test_non_canonical_admitted_projection_family(self) -> None:
        """Verifies that pi_Z is non-unique: any matrix v 1^T with sum(v) == 1 satisfies both identities."""
        c3 = C3Complex(with_two_cell=True)

        # Candidate 1: v = (1, 0, 0)^T
        pi_v1: Matrix = [
            [Fraction(1), Fraction(1), Fraction(1)],
            [Fraction(0), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(0)],
        ]
        is_idempotent, kills_exact = check_projection_admission(pi_v1, c3.d0_matrix)
        assert is_idempotent is True
        assert kills_exact is True

        # Candidate 2: v = (1/2, 1/2, 0)^T
        pi_v2: Matrix = [
            [Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)],
            [Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)],
            [Fraction(0), Fraction(0), Fraction(0)],
        ]
        is_idempotent, kills_exact = check_projection_admission(pi_v2, c3.d0_matrix)
        assert is_idempotent is True
        assert kills_exact is True

    def test_negative_controls_rejection_of_unadmitted_matrices(self) -> None:
        """Negative controls: candidate operators violating idempotence or exact-killing are refused."""
        c3 = C3Complex(with_two_cell=True)
        one_third = Fraction(1, 3)
        pi_harmonic: Matrix = [
            [one_third, one_third, one_third],
            [one_third, one_third, one_third],
            [one_third, one_third, one_third],
        ]

        # 1. Scale violation: 2 * Pi is not idempotent ((2Pi)^2 = 4Pi != 2Pi)
        pi_scaled: Matrix = [[2 * c for c in row] for row in pi_harmonic]
        is_idem, kills_ex = check_projection_admission(pi_scaled, c3.d0_matrix)
        assert is_idem is False  # Refused by idempotence
        assert kills_ex is True

        # 2. Identity matrix: I^2 == I, but I d0 = d0 != 0
        i3: Matrix = [
            [Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(1)],
        ]
        is_idem, kills_ex = check_projection_admission(i3, c3.d0_matrix)
        assert is_idem is True
        assert kills_ex is False  # Refused by exact-killing failure

        # 3. Nilpotent matrix: N^2 == 0 != N
        n_mat: Matrix = [
            [Fraction(0), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(0)],
        ]
        is_idem, kills_ex = check_projection_admission(n_mat, c3.d0_matrix)
        assert is_idem is False  # Refused


class TestAuditN003004RewriteRulesContract:
    """Verifies AUDIT-N003-004: Rewrite rules as consequences of admitted invariants."""

    def test_rule_1_exactness_kills_closure(self) -> None:
        """Rule 1: d1(d0 f) == 0 for any 0-cochain f."""
        c3 = C3Complex(with_two_cell=True)
        # Check nilpotency d1 d0 == 0 exactly
        d1_d0 = mat_mul_mat(c3.d1_matrix, c3.d0_matrix)
        assert mat_is_zero(d1_d0)

        for f in itertools.product((Fraction(-5), Fraction(0), Fraction(7)), repeat=3):
            d0_f = c3.d0(f)
            d1_d0_f = c3.d1(d0_f)
            assert d1_d0_f == (Fraction(0),)

    def test_rule_2_and_3_projection_contracts(self) -> None:
        """Rule 2 (idempotence) and Rule 3 (exact-killing) on admitted projection."""
        c3 = C3Complex(with_two_cell=True)
        one_third = Fraction(1, 3)
        pi_z: Matrix = [
            [one_third, one_third, one_third],
            [one_third, one_third, one_third],
            [one_third, one_third, one_third],
        ]

        # Rule 2: pi_Z(pi_Z(omega)) == pi_Z(omega)
        for omega in [(Fraction(2), Fraction(-1), Fraction(5)), (Fraction(1), Fraction(0), Fraction(0))]:
            proj1 = mat_mul_vec(pi_z, omega)
            proj2 = mat_mul_vec(pi_z, proj1)
            assert proj1 == proj2

        # Rule 3: pi_Z(d0 f) == 0
        for f in [(Fraction(10), Fraction(4), Fraction(-1)), (Fraction(-3), Fraction(8), Fraction(2))]:
            d0_f = c3.d0(f)
            proj_exact = mat_mul_vec(pi_z, d0_f)
            assert proj_exact == (Fraction(0), Fraction(0), Fraction(0))

    def test_quotient_defect_invariance_under_exact_shift(self) -> None:
        """Verifies Phi_1(omega + d0 f) == Phi_1(omega)."""
        c3 = C3Complex(with_two_cell=True)
        omega = (Fraction(1), Fraction(0), Fraction(0))
        phi1_orig = c3.compute_phi1(omega)
        assert phi1_orig == Fraction(1)

        for f in [(1, 2, 3), (-2, 0, 4), (5, -3, 1)]:
            d0_f = c3.d0(f)
            omega_shifted = tuple(omega[i] + d0_f[i] for i in range(3))
            phi1_shifted = c3.compute_phi1(omega_shifted)
            assert phi1_shifted == phi1_orig

    def test_negative_control_unadmitted_projection_fails_rule_3(self) -> None:
        """Negative control: unadmitted operator fails Rule 3 (exact cochain does not vanish)."""
        c3 = C3Complex(with_two_cell=True)
        # Identity matrix I is not admitted (fails exact-killing)
        i3: Matrix = [
            [Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(0), Fraction(1)],
        ]
        f = (Fraction(1), Fraction(2), Fraction(0))
        d0_f = c3.d0(f)
        proj_unadmitted = mat_mul_vec(i3, d0_f)
        # Rule 3 fails because proj_unadmitted == d0_f != 0
        assert proj_unadmitted != (Fraction(0), Fraction(0), Fraction(0))
        assert proj_unadmitted == d0_f


class TestAuditN003005SignLossUnderMagnitudeAggregation:
    """Verifies AUDIT-N003-005: Sign loss under magnitude aggregation."""

    def test_triangle_inequality_and_equality_condition(self) -> None:
        """Verifies |sum x_i| <= sum |x_i| with equality iff all nonzero elements share sign."""
        # 1. All positive: equality holds
        x_pos = (Fraction(2), Fraction(3), Fraction(5))
        assert abs(sum(x_pos)) == sum(abs(x) for x in x_pos) == Fraction(10)

        # 2. All negative: equality holds
        x_neg = (Fraction(-1), Fraction(-4), Fraction(-2))
        assert abs(sum(x_neg)) == sum(abs(x) for x in x_neg) == Fraction(7)

        # 3. Nonzero elements share sign with interspersed zeros: equality holds
        x_zeros = (Fraction(0), Fraction(4), Fraction(0), Fraction(7))
        assert abs(sum(x_zeros)) == sum(abs(x) for x in x_zeros) == Fraction(11)

        # 4. Mixed signs: strict inequality
        x_mixed = (Fraction(1), Fraction(-2), Fraction(3))
        assert abs(sum(x_mixed)) == Fraction(2)
        assert sum(abs(x) for x in x_mixed) == Fraction(6)
        assert abs(sum(x_mixed)) < sum(abs(x) for x in x_mixed)

        # 5. Boundary case: single element
        x_single = (Fraction(-5),)
        assert abs(sum(x_single)) == sum(abs(x) for x in x_single) == Fraction(5)

    def test_collision_witness_non_invertibility(self) -> None:
        """Verifies two-element collision witness c1=(1, -1) and c2=(1, 1)."""
        c1 = (Fraction(1), Fraction(-1))
        c2 = (Fraction(1), Fraction(1))

        # l1 magnitude aggregate
        l1_agg1 = sum(abs(x) for x in c1)
        l1_agg2 = sum(abs(x) for x in c2)
        assert l1_agg1 == l1_agg2 == Fraction(2)

        # l2 squared aggregate
        l2_agg1 = sum(x * x for x in c1)
        l2_agg2 = sum(x * x for x in c2)
        assert l2_agg1 == l2_agg2 == Fraction(2)

        # But signed orientation sums differ, establishing non-invertibility
        sum_c1 = sum(c1)
        sum_c2 = sum(c2)
        assert sum_c1 == Fraction(0)
        assert sum_c2 == Fraction(2)
        assert sum_c1 != sum_c2
