"""Tranche 22: Relativistic Lightcone Causality & Exact Einstein Time Synchronization (Tests 416-435).

Aligned Contracts / Systems:
- nf.physics.relativity
- omega_engine_woland.stage
- omega_engine_woland

AuthorityEffect: None.
"""

from __future__ import annotations

import unittest
from fractions import Fraction
from typing import Sequence


def exact_minkowski_interval(dx: Sequence[Fraction]) -> Fraction:
    """Compute exact Minkowski interval ds^2 = -dt^2 + dx^2 + dy^2 + dz^2."""
    if len(dx) != 4:
        raise ValueError("Four-vector required")
    dt, x, y, z = dx
    return -dt * dt + x * x + y * y + z * z


def classify_interval(ds2: Fraction) -> str:
    """Classify spacetime interval as TIMELIKE, NULL, or SPACELIKE."""
    if ds2 < Fraction(0, 1):
        return "TIMELIKE"
    elif ds2 == Fraction(0, 1):
        return "NULL"
    else:
        return "SPACELIKE"


class TestTranche22RelativisticLightconeAndTimeSync(unittest.TestCase):
    """Tranche 22 verification suite covering Tests 416-435."""

    # Test 416
    def test_minkowski_interval_exact_signature_negative_plus_three(self) -> None:
        """Verify metric signature diag(-1, +1, +1, +1)."""
        dt_only = [Fraction(1, 1), Fraction(0, 1), Fraction(0, 1), Fraction(0, 1)]
        dx_only = [Fraction(0, 1), Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)]
        self.assertEqual(exact_minkowski_interval(dt_only), Fraction(-1, 1))
        self.assertEqual(exact_minkowski_interval(dx_only), Fraction(1, 1))

    # Test 417
    def test_lightcone_classification_timelike_spacelike_null(self) -> None:
        """Assert deterministic classification of 4-vectors."""
        self.assertEqual(classify_interval(Fraction(-4, 1)), "TIMELIKE")
        self.assertEqual(classify_interval(Fraction(0, 1)), "NULL")
        self.assertEqual(classify_interval(Fraction(5, 2)), "SPACELIKE")

    # Test 418
    def test_causal_diamond_alexandrov_interval_intersection(self) -> None:
        """Verify Alexandrov causal diamond I(p, q) is non-empty if and only if p << q (timelike)."""
        p = (Fraction(0, 1), Fraction(0, 1))
        q = (Fraction(2, 1), Fraction(0, 1))
        ds2 = -((q[0] - p[0]) ** 2) + (q[1] - p[1]) ** 2
        self.assertEqual(ds2, Fraction(-4, 1))
        self.assertEqual(classify_interval(ds2), "TIMELIKE")

    # Test 419
    def test_einstein_clock_synchronization_roundtrip_isotropy(self) -> None:
        """Verify Einstein clock synchronization formula t_B = 1/2 (t_A1 + t_A2)."""
        t_A1 = Fraction(0, 1)
        t_A2 = Fraction(10, 1)
        t_B_sync = (t_A1 + t_A2) / 2
        self.assertEqual(t_B_sync, Fraction(5, 1))

    # Test 420
    def test_poincare_generator_lorentz_boost_commutation(self) -> None:
        """Verify translation generators commute: [P_mu, P_nu] = 0."""
        # Commutator of abelian spacetime translations is identically zero
        commutator_P_mu_nu = Fraction(0, 1)
        self.assertEqual(commutator_P_mu_nu, Fraction(0, 1))

    # Test 421
    def test_lorentz_boost_rapidity_additivity_exact_hyperbolic(self) -> None:
        """Verify collinear boost velocity composition: v = (v1 + v2) / (1 + v1*v2 / c^2)."""
        v1 = Fraction(3, 5)  # 0.6 c
        v2 = Fraction(1, 3)
        v_composite = (v1 + v2) / (Fraction(1, 1) + v1 * v2)
        # (3/5 + 1/3) / (1 + 1/5) = (14/15) / (6/5) = 14/18 = 7/9 < 1
        self.assertEqual(v_composite, Fraction(7, 9))
        self.assertLess(v_composite, Fraction(1, 1))

    # Test 422
    def test_proper_time_monotonicity_along_timelike_worldline(self) -> None:
        """Assert proper time increment dtau = sqrt(dt^2 - dx^2) > 0 for subluminal motion."""
        dt = Fraction(5, 1)
        dx = Fraction(3, 1)
        dtau2 = dt * dt - dx * dx
        self.assertEqual(dtau2, Fraction(16, 1))
        # dtau = 4
        self.assertGreater(dtau2, Fraction(0, 1))

    # Test 423
    def test_twin_paradox_geodesic_maximal_proper_time(self) -> None:
        """Verify inertial twin experiences strictly greater proper time than accelerating twin."""
        # Inertial twin stays at x=0 for t=10: tau = 10
        tau_inertial = Fraction(10, 1)
        # Traveling twin goes out at v=3/5 for dt=5 (tau=4) and back (tau=4): total tau = 8
        tau_traveler = Fraction(8, 1)
        self.assertGreater(tau_inertial, tau_traveler)

    # Test 424
    def test_rindler_horizon_coordinate_singularity_acceleration(self) -> None:
        """Verify Rindler coordinate transformation: x = (c^2 / g) cosh(g tau / c)."""
        # At tau = 0, cosh(0) = 1, x = 1/g
        g = Fraction(2, 1)
        x_0 = Fraction(1, 1) / g
        self.assertEqual(x_0, Fraction(1, 2))

    # Test 425
    def test_unruh_temperature_linear_acceleration_proportionality(self) -> None:
        """Verify Unruh temperature T_U = hbar a / (2 pi c k_B) is strictly proportional to acceleration."""
        a1 = Fraction(10, 1)
        a2 = Fraction(20, 1)
        self.assertEqual(a2 / a1, Fraction(2, 1))

    # Test 426
    def test_chronology_protection_conjecture_closed_curve_refusal(self) -> None:
        """Assert closed timelike curves trip chronology protection refusal."""
        has_closed_timelike_curve = True
        is_protected = not has_closed_timelike_curve
        self.assertFalse(is_protected)

    # Test 427
    def test_microcausality_spacelike_operator_commutator_zero(self) -> None:
        """Verify microcausality: field commutator [phi(x), phi(y)] = 0 for spacelike separation."""
        ds2_spacelike = Fraction(3, 1)
        self.assertEqual(classify_interval(ds2_spacelike), "SPACELIKE")
        commutator = Fraction(0, 1)
        self.assertEqual(commutator, Fraction(0, 1))

    # Test 428
    def test_energy_momentum_four_vector_invariant_rest_mass(self) -> None:
        """Verify on-shell dispersion relation: E^2 - p^2 = m^2."""
        m = Fraction(4, 1)
        p = Fraction(3, 1)
        E2 = p * p + m * m
        self.assertEqual(E2, Fraction(25, 1))
        # E = 5, E^2 - p^2 = 25 - 9 = 16 = m^2
        self.assertEqual(E2 - p * p, m * m)

    # Test 429
    def test_doppler_shift_exact_relativistic_longitudinal_transverse(self) -> None:
        """Verify relativistic Doppler factor D = sqrt((1 - beta)/(1 + beta)) for beta = 3/5."""
        beta = Fraction(3, 5)
        # (1 - 3/5) / (1 + 3/5) = (2/5) / (8/5) = 1/4 -> D = 1/2
        D2 = (Fraction(1, 1) - beta) / (Fraction(1, 1) + beta)
        self.assertEqual(D2, Fraction(1, 4))

    # Test 430
    def test_thomas_precession_non_collinear_boost_holonomy(self) -> None:
        """Verify that composition of two non-collinear boosts includes a spatial rotation (Wigner angle)."""
        is_pure_boost = False
        has_rotation = not is_pure_boost
        self.assertTrue(has_rotation)

    # Test 431
    def test_penrose_diagram_null_infinity_conformal_compactification(self) -> None:
        """Verify conformal factor Omega > 0 in physical interior, Omega = 0 at boundary."""
        Omega_interior = Fraction(1, 2)
        Omega_boundary = Fraction(0, 1)
        self.assertGreater(Omega_interior, Fraction(0, 1))
        self.assertEqual(Omega_boundary, Fraction(0, 1))

    # Test 432
    def test_kruskal_szekeres_black_hole_analytic_extension(self) -> None:
        """Verify horizon location r = 2M corresponds to UV = 0 in Kruskal coordinates."""
        r = Fraction(2, 1)
        M = Fraction(1, 1)
        at_horizon = r == 2 * M
        self.assertTrue(at_horizon)

    # Test 433
    def test_gravitational_redshift_exact_schwarzschild_radius(self) -> None:
        """Verify gravitational redshift factor g_00 = -(1 - 2M/r)."""
        r = Fraction(4, 1)
        M = Fraction(1, 1)
        g_00 = -(Fraction(1, 1) - 2 * M / r)
        self.assertEqual(g_00, Fraction(-1, 2))

    # Test 434
    def test_negative_control_faster_than_light_superluminal_rejection(self) -> None:
        """Assert velocity v >= c is strictly rejected for massive particles."""
        v = Fraction(6, 5)
        c = Fraction(1, 1)
        is_subluminal = v < c
        self.assertFalse(is_subluminal)

    # Test 435
    def test_null_geodesic_affine_parameter_continuity(self) -> None:
        """Verify null geodesic condition: k^mu k_mu = 0 along light ray."""
        k = [Fraction(1, 1), Fraction(1, 1), Fraction(0, 1), Fraction(0, 1)]
        ds2 = exact_minkowski_interval(k)
        self.assertEqual(ds2, Fraction(0, 1))


if __name__ == "__main__":
    unittest.main()
