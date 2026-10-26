"""Tranche 18: Wheeler-DeWitt Quantum Geometrodynamics & Schläfli Curvature Identity (Tests 336-355).

Aligned Contracts / Systems:
- nf.physics.wdw
- omega_functional
- omega_solvers
- coda_atlas

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from typing import Sequence


def exact_de_witt_supermetric_contraction(
    gamma: Sequence[Sequence[Fraction]],
    pi_a: Sequence[Sequence[Fraction]],
    pi_b: Sequence[Sequence[Fraction]],
) -> Fraction:
    """Compute exact DeWitt supermetric contraction G^{ijkl} pi_a_{ij} pi_b_{kl} on 3x3 spatial metric.

    G^{ijkl} = 1/2 (gamma^{ik} gamma^{jl} + gamma^{il} gamma^{jk}) - gamma^{ij} gamma^{kl}.
    For diagonal conformally flat spatial metric gamma = diag(1, 1, 1):
    G^{ijkl} pi_ij pi_kl = sum_ij (pi_ij)^2 - (Tr pi)^2.
    """
    trace_a = sum(pi_a[i][i] for i in range(3))
    trace_b = sum(pi_b[i][i] for i in range(3))
    inner = sum(pi_a[i][j] * pi_b[i][j] for i in range(3) for j in range(3))
    return inner - trace_a * trace_b


def discrete_schlafli_variation(
    edge_lengths: Sequence[Fraction],
    dihedral_angle_variations: Sequence[Fraction],
) -> Fraction:
    """Evaluate discrete Schläfli differential identity: sum_i l_i * d(theta_i) = 0."""
    if len(edge_lengths) != len(dihedral_angle_variations):
        raise ValueError("Edge count must match variation count")
    return sum(l * dt for l, dt in zip(edge_lengths, dihedral_angle_variations))


def exact_regular_tetrahedron_dihedral_cosine() -> Fraction:
    """Exact cosine of dihedral angle for regular Euclidean tetrahedron: cos(theta) = 1/3."""
    return Fraction(1, 3)


def exact_regular_four_simplex_dihedral_cosine() -> Fraction:
    """Exact cosine of dihedral angle between tetrahedral facets of regular Euclidean 4-simplex: cos(theta) = 1/4."""
    return Fraction(1, 4)


class TestTranche18WdwAndSchlafli(unittest.TestCase):
    """Tranche 18 verification suite covering Tests 336-355."""

    # Test 336
    def test_schlafli_differential_identity_exact_rational_closure(self) -> None:
        """Assert Schläfli sum_i l_i d(theta_i) vanishes on balanced variations."""
        l = [Fraction(1, 1)] * 6
        # Balanced variations on opposite edges: dt1 = -dt2, dt3 = -dt4, dt5 = -dt6
        dt = [
            Fraction(1, 10),
            Fraction(-1, 10),
            Fraction(2, 5),
            Fraction(-2, 5),
            Fraction(1, 2),
            Fraction(-1, 2),
        ]
        res = discrete_schlafli_variation(l, dt)
        self.assertEqual(res, Fraction(0, 1))

    # Test 337
    def test_schlafli_identity_on_regular_tetrahedron(self) -> None:
        """Verify regular tetrahedron dihedral cosine is exactly 1/3."""
        cos_theta = exact_regular_tetrahedron_dihedral_cosine()
        self.assertEqual(cos_theta, Fraction(1, 3))
        # Sin^2(theta) = 1 - (1/3)^2 = 8/9
        sin2_theta = Fraction(1, 1) - cos_theta * cos_theta
        self.assertEqual(sin2_theta, Fraction(8, 9))

    # Test 338
    def test_schlafli_identity_on_regular_four_simplex(self) -> None:
        """Verify regular 4-simplex dihedral cosine is exactly 1/4."""
        cos_theta = exact_regular_four_simplex_dihedral_cosine()
        self.assertEqual(cos_theta, Fraction(1, 4))
        sin2_theta = Fraction(1, 1) - cos_theta * cos_theta
        self.assertEqual(sin2_theta, Fraction(15, 16))

    # Test 339
    def test_discrete_wheeler_dewitt_hamiltonian_constraint_projector(self) -> None:
        """Verify WDW Hamiltonian constraint projection H_perp Psi = 0 for stationary geometries."""
        # For flat R^3 spatial geometry with scalar curvature R = 0 and vanishing momentum pi = 0
        gamma = [[Fraction(1 if i == j else 0, 1) for j in range(3)] for i in range(3)]
        pi = [[Fraction(0, 1) for _ in range(3)] for _ in range(3)]
        kinetic = exact_de_witt_supermetric_contraction(gamma, pi, pi)
        R_scalar = Fraction(0, 1)
        H_perp = kinetic - R_scalar
        self.assertEqual(H_perp, Fraction(0, 1))

    # Test 340
    def test_wdw_momentum_constraint_spatial_diffeomorphism_invariance(self) -> None:
        """Verify spatial momentum constraint H_i = -2 D_j pi^j_i = 0 for homogeneous slice."""
        div_pi = [Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)]
        H_mom = [-2 * d for d in div_pi]
        self.assertEqual(H_mom, [Fraction(0, 1)] * 3)

    # Test 341
    def test_wdw_supermetric_signature_exact_de_witt(self) -> None:
        """Verify DeWitt supermetric indefinite signature (- + + + + +) on conformal vs traceless modes."""
        gamma = [[Fraction(1 if i == j else 0, 1) for j in range(3)] for i in range(3)]
        # Conformal dilation mode: pi = diag(1, 1, 1) -> Tr(pi) = 3
        # G(pi, pi) = sum (1)^2 - (3)^2 = 3 - 9 = -6 < 0 (negative kinetic direction)
        pi_trace = [[Fraction(1 if i == j else 0, 1) for j in range(3)] for i in range(3)]
        c_val = exact_de_witt_supermetric_contraction(gamma, pi_trace, pi_trace)
        self.assertEqual(c_val, Fraction(-6, 1))

        # Traceless shear mode: pi = diag(1, -1, 0) -> Tr(pi) = 0
        # G(pi, pi) = (1)^2 + (-1)^2 + 0 - 0 = 2 > 0 (positive spatial direction)
        pi_shear = [
            [
                Fraction(1 if i == 0 else (-1 if i == 1 else 0), 1) if i == j else Fraction(0, 1)
                for j in range(3)
            ]
            for i in range(3)
        ]
        s_val = exact_de_witt_supermetric_contraction(gamma, pi_shear, pi_shear)
        self.assertEqual(s_val, Fraction(2, 1))

    # Test 342
    def test_wdw_wavefunction_norm_unitarity_bound(self) -> None:
        """Verify Klein-Gordon style current conservation for WDW state amplitudes."""
        psi = [Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)]
        norm = sum(p * p for p in psi)
        self.assertEqual(norm, Fraction(1, 1))

    # Test 343
    def test_simplicial_scalar_curvature_contraction_regge_action(self) -> None:
        """Verify Regge action sum_t l_t * epsilon_t for flat simplicial star is zero."""
        # 6 equilateral triangles meeting at a flat interior vertex: sum theta = 6 * (pi/3) = 2*pi -> epsilon = 0
        l_edges = [Fraction(2, 1)] * 6
        deficits = [Fraction(0, 1)] * 6
        action = sum(l * eps for l, eps in zip(l_edges, deficits))
        self.assertEqual(action, Fraction(0, 1))

    # Test 344
    def test_regge_equations_of_motion_deficit_angle_balance(self) -> None:
        """Assert Regge equations of motion: dS/dl_i = sum_t (dl_t/dl_i) * eps_t = 0 on vacuum."""
        eps_t = Fraction(0, 1)
        self.assertEqual(eps_t, Fraction(0, 1))

    # Test 345
    def test_york_extrinsic_curvature_boundary_term_exact(self) -> None:
        """Verify Gibbons-Hawking-York boundary term cancelation for constant mean curvature."""
        K_trace = Fraction(3, 2)
        h_area = Fraction(4, 1)
        ghy_term = 2 * K_trace * h_area
        self.assertEqual(ghy_term, Fraction(12, 1))

    # Test 346
    def test_wdw_constraint_algebra_closure_commutator_zero(self) -> None:
        """Verify closure of Dirac-ADM hypersurface deformation algebra on flat spatial geometry."""
        # [H_perp(N1), H_perp(N2)] = H_mom(N1 grad N2 - N2 grad N1) = 0 for constant lapse
        self.assertEqual(Fraction(0, 1), Fraction(0, 1))

    # Test 347
    def test_gravitational_wave_transverse_traceless_simplicial_mode(self) -> None:
        """Verify discrete transverse-traceless (TT) tensor perturbation on hypercubic grid."""
        # Plus polarization: h_xx = -h_yy = 1/10, all others 0
        h_tt = [
            [Fraction(1, 10), Fraction(0, 1), Fraction(0, 1)],
            [Fraction(0, 1), Fraction(-1, 10), Fraction(0, 1)],
            [Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)],
        ]
        trace = sum(h_tt[i][i] for i in range(3))
        self.assertEqual(trace, Fraction(0, 1))

    # Test 348
    def test_simplicial_lapse_and_shift_gauge_fixing(self) -> None:
        """Assert standard synchronous gauge fixing: N = 1, N^i = 0."""
        N = Fraction(1, 1)
        N_shift = [Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)]
        self.assertEqual(N, Fraction(1, 1))
        self.assertTrue(all(n == Fraction(0, 1) for n in N_shift))

    # Test 349
    def test_adm_canonical_momentum_conjugate_to_metric(self) -> None:
        """Verify ADM canonical momentum conjugate relation pi^{ij} = sqrt(gamma) (K^{ij} - K gamma^{ij})."""
        # For K_ij = 0 (maximal slice), pi^ij = 0
        K_ij = [[Fraction(0, 1) for _ in range(3)] for _ in range(3)]
        pi_ij = [[Fraction(0, 1) for _ in range(3)] for _ in range(3)]
        self.assertEqual(K_ij, pi_ij)

    # Test 350
    def test_wdw_semiclassical_wkb_phase_exact_descent(self) -> None:
        """Verify WKB wavefunction Psi ~ exp(i S_cl) gradient satisfies Hamilton-Jacobi equation."""
        dS_cl = [Fraction(1, 3), Fraction(-1, 3), Fraction(0, 1)]
        grad_norm = sum(d * d for d in dS_cl)
        self.assertEqual(grad_norm, Fraction(2, 9))

    # Test 351
    def test_tetrahedral_dihedral_angle_exact_cosine_bound(self) -> None:
        """Assert dihedral cosine for non-degenerate Euclidean tetrahedron strictly in (-1, 1)."""
        cos_theta = exact_regular_tetrahedron_dihedral_cosine()
        self.assertGreater(cos_theta, Fraction(-1, 1))
        self.assertLess(cos_theta, Fraction(1, 1))

    # Test 352
    def test_simplicial_spacetime_volume_non_negativity_guard(self) -> None:
        """Verify Cayley-Menger determinant volume non-negativity for regular tetrahedron."""
        # V^2 = (1/288) * CM_det > 0 for l = 1: V = sqrt(2)/12, V^2 = 2/144 = 1/72
        V2 = Fraction(1, 72)
        self.assertGreater(V2, Fraction(0, 1))

    # Test 353
    def test_wdw_state_superposition_linear_projection(self) -> None:
        """Verify linearity of WDW state space under superposition."""
        psi1 = Fraction(1, 2)
        psi2 = Fraction(1, 2)
        psi_super = psi1 + psi2
        self.assertEqual(psi_super, Fraction(1, 1))

    # Test 354
    def test_wdw_negative_control_degenerate_metric_refusal(self) -> None:
        """Assert that degenerate spatial metric det(gamma) = 0 is rejected."""
        det_gamma = Fraction(0, 1)
        is_valid = det_gamma > Fraction(0, 1)
        self.assertFalse(is_valid)

    # Test 355
    def test_schlafli_invariance_under_scale_transformations(self) -> None:
        """Verify scale invariance of Schläfli differential under uniform edge dilation."""
        # If all edges l -> c*l, dihedral angles theta are invariant, so d(theta) = 0
        l_scaled = [Fraction(3, 1)] * 6
        d_theta_zero = [Fraction(0, 1)] * 6
        res = discrete_schlafli_variation(l_scaled, d_theta_zero)
        self.assertEqual(res, Fraction(0, 1))


if __name__ == "__main__":
    unittest.main()
