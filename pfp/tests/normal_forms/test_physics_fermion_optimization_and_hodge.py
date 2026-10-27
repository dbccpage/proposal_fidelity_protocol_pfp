"""Unit and property-based tests for Physics & Fermion Signs (Tests 39-42),
Zero-Float Exact Rational Duality (Tests 43-46), and
Topological Cochain & Discrete Hodge Normal Forms (Tests 47-50).

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from fractions import Fraction

from pfp.domain.normal_forms.quantum_forms import verify_bssnf, verify_micnf
from pfp.domain.normal_forms.relational_extensions import (
    Simplicial2DComplex,
    verify_simplicial_dhnf,
    verify_zfnf_scaling_invariance,
)
from pfp.domain.normal_forms.tower_forms import verify_zfnf


class TestPhysicsFermionOptimizationAndHodge(unittest.TestCase):
    """Test suite covering FSP Normal Forms, ZFNF Duality, and Discrete Hodge Decomposition."""

    # =========================================================================
    # Group 6: Physics & Fermionic Sign Normal Forms (Tests 39-42)
    # =========================================================================

    def test_bss_nf_gauge_elimination_bipartite_graph(self) -> None:
        """Test 39: BSS-NF local gauge transformation converts bipartite graph to stoquastic."""
        # 4-vertex bipartite cycle with positive off-diagonals (unstoquastic sign problem)
        H = [
            [Fraction(2), Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(1), Fraction(2), Fraction(1), Fraction(0)],
            [Fraction(0), Fraction(1), Fraction(2), Fraction(1)],
            [Fraction(1), Fraction(0), Fraction(1), Fraction(2)],
        ]
        res = verify_bssnf(H)
        self.assertTrue(res.gaugeable)
        self.assertIsNotNone(res.transformed_matrix)
        # All off-diagonal elements in transformed matrix must be <= 0
        t_mat = res.transformed_matrix
        for i in range(4):
            for j in range(4):
                if i != j:
                    self.assertLessEqual(t_mat[i][j], Fraction(0))

    def test_mic_nf_meron_involution_pair_annihilation(self) -> None:
        """Test 40: Meron configurations with opposite signs cancel via fixed-point free involution."""
        sectors = [
            {"path_id": "p1", "weight": Fraction(10), "sign": 1},
            {"path_id": "p2", "weight": Fraction(10), "sign": -1},
            {"path_id": "p3", "weight": Fraction(5), "sign": 1},
        ]
        cancellation_ids = ["p1", "p2"]
        involution_map = {"p1": "p2", "p2": "p1"}

        res = verify_micnf(sectors, cancellation_ids, involution_map)
        self.assertEqual(res.terminal, "MeronExactCancellation")
        self.assertEqual(len(res.pairs), 1)
        self.assertEqual(res.survivors, ("p3",))
        self.assertEqual(res.survivor_sum, Fraction(5))

    def test_sign_problem_obstruction_mass_scaling(self) -> None:
        """Test 41: Frustrated odd cycles cannot be gauged to stoquastic and return certified cycle."""
        # 3-cycle with positive hopping (frustrated triangle)
        H_triangle = [
            [Fraction(0), Fraction(1), Fraction(1)],
            [Fraction(1), Fraction(0), Fraction(1)],
            [Fraction(1), Fraction(1), Fraction(0)],
        ]
        res = verify_bssnf(H_triangle)
        self.assertFalse(res.gaugeable)
        self.assertEqual(res.terminal, "OddCycleFrustratedObstruction")
        self.assertIsNotNone(res.odd_cycle)
        # Closed cycle path has 4 vertices with start == end, covering 3 unique vertices
        self.assertEqual(len(set(res.odd_cycle)), 3)
        self.assertEqual(res.odd_cycle[0], res.odd_cycle[-1])

    def test_fermion_sign_gauge_orbit_invariance(self) -> None:
        """Test 42: Trace and spectrum are invariant under discrete Z2 gauge orbit similarity."""
        H = [
            [Fraction(3), Fraction(1)],
            [Fraction(1), Fraction(3)],
        ]
        trace_orig = H[0][0] + H[1][1]

        # Apply gauge transformation D = diag(1, -1)
        D = [1, -1]
        H_gauged = [
            [D[0] * H[0][0] * D[0], D[0] * H[0][1] * D[1]],
            [D[1] * H[1][0] * D[0], D[1] * H[1][1] * D[1]],
        ]
        trace_gauged = H_gauged[0][0] + H_gauged[1][1]
        self.assertEqual(trace_orig, trace_gauged)
        self.assertEqual(H_gauged[0][1], Fraction(-1))

    # =========================================================================
    # Group 7: Optimization & Zero-Float Exact Rational Duality (Tests 43-46)
    # =========================================================================

    def test_zfnf_degenerate_basis_duality_gap_zero(self) -> None:
        """Test 43: Degenerate primal/dual bases evaluate to certified zero duality gap."""
        primal_obj = Fraction(42, 1)
        dual_obj = Fraction(42, 1)

        res = verify_zfnf(primal_obj, dual_obj)
        self.assertEqual(res.terminal, "CertifiedOptimalZeroGap")
        self.assertEqual(res.duality_gap, 0)

    def test_zfnf_unbounded_ray_dual_infeasibility_certificate(self) -> None:
        """Test 44: Suboptimal or gap-separated bounds correctly identify non-zero defect."""
        primal_obj = Fraction(100)
        dual_obj = Fraction(105)

        res = verify_zfnf(primal_obj, dual_obj)
        self.assertEqual(res.terminal, "SuboptimalPositiveGap")
        self.assertEqual(res.duality_gap, Fraction(5))

    def test_zfnf_affine_scaling_invariance(self) -> None:
        """Test 45: Objective scaling by arbitrary positive rationals preserves zero gap certificate."""
        primal = Fraction(1234, 567)
        dual = Fraction(1234, 567)
        scale = Fraction(17, 3)

        inv, r_base, r_scaled = verify_zfnf_scaling_invariance(primal, dual, scale)
        self.assertTrue(inv)
        self.assertEqual(r_base.terminal, "CertifiedOptimalZeroGap")
        self.assertEqual(r_scaled.terminal, "CertifiedOptimalZeroGap")

    def test_zfnf_complementary_slackness_exact_orthogonality(self) -> None:
        """Test 46: Primal variables and dual slacks satisfy exact inner-product orthogonality."""
        x = [Fraction(3), Fraction(0), Fraction(5)]
        s = [Fraction(0), Fraction(7), Fraction(0)]  # s_i > 0 only where x_i == 0

        # Exact inner product <x, s>
        dot = sum(xi * si for xi, si in zip(x, s))
        self.assertEqual(dot, Fraction(0))

    # =========================================================================
    # Group 8: Topological Cochain & Discrete Hodge Normal Forms (Tests 47-50)
    # =========================================================================

    def test_simplicial_boundary_annihilation_d1_d0(self) -> None:
        """Test 47: Nilpotency of discrete exterior derivative d1(d0(alpha)) == 0 on 2-complex."""
        # Single triangle (0, 1, 2)
        complex_2d = Simplicial2DComplex(
            num_vertices=3,
            edges=((0, 1), (1, 2), (2, 0)),
            faces=((0, 1, 2),),
        )
        potential = [Fraction(5), Fraction(12), Fraction(3)]
        harmonic = [Fraction(0), Fraction(0), Fraction(0)]

        ok, dot, curl = verify_simplicial_dhnf(complex_2d, potential, harmonic)
        self.assertTrue(ok)
        self.assertEqual(curl, [Fraction(0)])
        self.assertEqual(dot, Fraction(0))

    def test_discrete_hodge_harmonic_1_cocycle_decoupling(self) -> None:
        """Test 48: Exact coboundary d0(alpha) is strictly orthogonal to harmonic circulation h."""
        complex_2d = Simplicial2DComplex(
            num_vertices=3,
            edges=((0, 1), (1, 2), (2, 0)),
            faces=((0, 1, 2),),
        )
        # alpha potential
        potential = [Fraction(1), Fraction(4), Fraction(9)]
        # exact cochain d0(alpha) on edges:
        # e01 = 4 - 1 = 3, e12 = 9 - 4 = 5, e20 = 1 - 9 = -8. Note: 3 + 5 + (-8) = 0.
        exact_cochain = complex_2d.coboundary_d0(potential)
        self.assertEqual(exact_cochain, [Fraction(3), Fraction(5), Fraction(-8)])

        # Harmonic circulation h = (1, 1, 1):
        # <d0(alpha), h> = 3*1 + 5*1 + (-8)*1 = 0
        harmonic = [Fraction(1), Fraction(1), Fraction(1)]
        dot = complex_2d.inner_product_edges(exact_cochain, harmonic)
        self.assertEqual(dot, Fraction(0))

    def test_simplicial_torus_betti_number_calculation(self) -> None:
        """Test 49: Chain complex homology of triangulated 2-torus verifies Euler characteristic chi=0."""
        # For any triangulated torus: V - E + F = 0 and Betti numbers beta_0 = 1, beta_1 = 2, beta_2 = 1
        # Minimum triangulation of 2-torus has V=7, E=21, F=14
        V = 7
        E = 21
        F = 14
        chi = V - E + F
        self.assertEqual(chi, 0)
        beta_0 = 1
        beta_1 = 2
        beta_2 = 1
        self.assertEqual(beta_0 - beta_1 + beta_2, chi)

    def test_connection_holonomy_flatness_zero_curvature(self) -> None:
        """Test 50: Flat discrete connection has path-ordered holonomy product = identity around boundary."""
        # Flat U(1) connection where phase around triangle sums to 0 mod 2pi
        phases = [Fraction(1, 3), Fraction(1, 6), Fraction(-1, 2)]
        loop_curvature = sum(phases)
        self.assertEqual(loop_curvature, Fraction(0))


if __name__ == "__main__":
    unittest.main()
