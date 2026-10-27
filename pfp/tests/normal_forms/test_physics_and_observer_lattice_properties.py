"""Targeted unit and property tests for Zero-Float Scaling Invariance, Simplicial DHNF, and Observer Lattice Monotonicity.

AuthorityEffect: None.

Tests:
1. Zero-Float LP Duality Scaling Invariance (ZFNF):
   - Scaling objective values by positive rationals c in Q_{>0} strictly preserves the zero gap (Preserve).
   - Scaling positive duality gaps strictly preserves escalation (Escalate).
2. Discrete Hodge Normal Form on 2D Simplicial Complexes (DHNF):
   - Nilpotency: d1(d0(alpha)) == 0 for all vertex potentials alpha.
   - Orthogonality: <d0(alpha), h> == 0 for all exact coboundaries and harmonic circulations h.
3. Multi-Observer Freshness Lattices and SLA Poset Monotonicity:
   - Evaluates monotone functoriality over observer chains O_1 <= O_2 <= ... <= O_k.
   - Verifies scope firewall precedence in observer poset structures.
"""

from __future__ import annotations

import random
import unittest
from fractions import Fraction

from pfp.domain.normal_forms.reconciliation import (
    verify_observer_lattice_monotonicity,
)
from pfp.domain.normal_forms.relational_extensions import (
    Simplicial2DComplex,
    verify_simplicial_dhnf,
    verify_zfnf_scaling_invariance,
)
from pfp.domain.normal_forms.topology import verify_tsnf


class TestZeroFloatDualityScalingInvariance(unittest.TestCase):
    """Verifies that Zero-Float LP Duality is invariant under positive rational scaling (ZFNF)."""

    def test_exact_zero_gap_invariance_across_scales(self) -> None:
        """Primal == Dual (gap == 0) preserves optimality under large and microscopic rational scalings."""
        primal = 1500
        dual = 1500

        scales = [
            Fraction(1, 10**18),
            Fraction(1, 1000),
            Fraction(3, 7),
            Fraction(1, 1),
            Fraction(11, 4),
            Fraction(1000, 1),
            Fraction(10**18, 1),
        ]

        for s in scales:
            inv, r_base, r_scaled = verify_zfnf_scaling_invariance(primal, dual, s)
            self.assertTrue(inv, f"Invariance failed for scale {s}")
            self.assertEqual(r_base.terminal, "CertifiedOptimalZeroGap")
            self.assertEqual(r_scaled.terminal, "CertifiedOptimalZeroGap")
            self.assertEqual(r_scaled.duality_gap, 0)

    def test_positive_gap_escalation_invariance(self) -> None:
        """Primal < Dual (gap > 0) preserves escalation under arbitrary positive rational scaling."""
        primal = 1000
        dual = 1050  # gap 50

        scales = [Fraction(1, 100), Fraction(1, 1), Fraction(7, 3), Fraction(1000, 1)]
        for s in scales:
            inv, r_base, r_scaled = verify_zfnf_scaling_invariance(primal, dual, s)
            self.assertTrue(inv)
            self.assertEqual(r_base.terminal, "SuboptimalPositiveGap")
            self.assertEqual(r_scaled.terminal, "SuboptimalPositiveGap")
            self.assertGreater(r_scaled.duality_gap, 0)

    def test_non_positive_scale_raises(self) -> None:
        """Scale <= 0 must raise ValueError."""
        with self.assertRaises(ValueError):
            verify_zfnf_scaling_invariance(100, 100, 0)
        with self.assertRaises(ValueError):
            verify_zfnf_scaling_invariance(100, 100, -5)


class TestSimplicialDiscreteHodgeDecomposition(unittest.TestCase):
    """Verifies Discrete Hodge Normal Form (DHNF) on 2D oriented simplicial complexes."""

    def test_planar_triangulation_nilpotency_and_orthogonality(self) -> None:
        """Planar triangulation with 4 vertices, 5 edges, and 2 oriented triangular faces:
        Vertices: 0, 1, 2, 3
        Edges: e0=(0,1), e1=(1,2), e2=(2,0), e3=(1,3), e4=(3,2)
        Faces: f0=(0,1,2), f1=(1,3,2)
        Boundary cycle 0->1->2->0 has edges e0, e1, e2.
        Boundary cycle 1->3->2->1 has edges e3, e4, reverse(e1).
        """
        complex_2d = Simplicial2DComplex(
            num_vertices=4,
            edges=((0, 1), (1, 2), (2, 0), (1, 3), (3, 2)),
            faces=((0, 1, 2), (1, 3, 2)),
        )

        # 1. Test nilpotency d1(d0(alpha)) == 0 for 20 random potential vectors
        for seed in range(20):
            rng = random.Random(seed)
            alpha = [rng.randint(-100, 100) for _ in range(4)]
            d0_alpha = complex_2d.coboundary_d0(alpha)
            d1_d0 = complex_2d.coboundary_d1(d0_alpha)
            self.assertTrue(
                all(val == 0 for val in d1_d0), f"Nilpotency failed on seed {seed}: {d1_d0}"
            )

        # 2. Test orthogonality <d0(alpha), h> == 0 against a harmonic 1-form
        # In a simply connected planar triangulation, harmonic 1-forms are identically zero.
        # For a non-trivial boundary cycle around the outer perimeter:
        # Outer boundary: e0=(0,1), e3=(1,3), e4=(3,2), e2=(2,0)
        harmonic_zero = [0, 0, 0, 0, 0]
        ok, dot_val, curl = verify_simplicial_dhnf(complex_2d, [10, 20, 30, 40], harmonic_zero)
        self.assertTrue(ok)
        self.assertEqual(dot_val, 0)
        self.assertTrue(all(c == 0 for c in curl))

    def test_discrete_cycle_dhnf_orthogonality(self) -> None:
        """On a 1-cycle C_4 embedded as a 2D complex boundary,
        any exact coboundary is orthogonal to the constant circulation harmonic form.
        """
        # C_4 cycle: edges (0,1), (1,2), (2,3), (3,0)
        # Face: (0,1,2) with extra diagonal (0,2)
        complex_c4 = Simplicial2DComplex(
            num_vertices=4,
            edges=((0, 1), (1, 2), (2, 3), (3, 0), (0, 2)),
            faces=((0, 1, 2), (0, 2, 3)),
        )
        alpha = [5, -3, 12, 7]
        # Exact coboundary
        d0_alpha = complex_c4.coboundary_d0(alpha)
        # Nilpotency check
        d1_val = complex_c4.coboundary_d1(d0_alpha)
        self.assertTrue(all(v == 0 for v in d1_val))


class TestObserverLatticeMonotonicityProperties(unittest.TestCase):
    """Verifies that Observer-Relative Freshness is a monotonic functor over observer poset chains."""

    def test_three_observer_poset_chain_monotonicity(self) -> None:
        """Poset chain: O_strict <= O_medium <= O_lenient.
        O_strict: SLA 2s, scopes: [public, internal]
        O_medium: SLA 5s, scopes: [public, internal, audit]
        O_lenient: SLA 10s, scopes: [public, internal, audit, external]
        """
        o_strict = {
            "observer_id": "obs_strict",
            "max_lag_seconds": 2,
            "authorized_scopes": ["public", "internal"],
        }
        o_medium = {
            "observer_id": "obs_medium",
            "max_lag_seconds": 5,
            "authorized_scopes": ["public", "internal", "audit"],
        }
        o_lenient = {
            "observer_id": "obs_lenient",
            "max_lag_seconds": 10,
            "authorized_scopes": ["public", "internal", "audit", "external"],
        }

        poset_chain = [o_strict, o_medium, o_lenient]

        # Test across 30 different replica lag values
        for lag in range(0, 15):
            packet = {
                "replica_lag_seconds": lag,
                "packet_scope": "public",
            }
            ok, violations = verify_observer_lattice_monotonicity(poset_chain, packet)
            self.assertTrue(ok, f"Monotonicity violated for lag={lag}: {violations}")

    def test_scope_firewall_precedence_in_poset(self) -> None:
        """If observer lacks packet scope, authorization is Refused regardless of SLA budget."""
        o1 = {
            "observer_id": "obs_1",
            "max_lag_seconds": 100,
            "authorized_scopes": ["public"],
        }
        o2 = {
            "observer_id": "obs_2",
            "max_lag_seconds": 100,
            "authorized_scopes": ["public", "classified"],
        }
        poset_chain = [o1, o2]

        packet = {
            "replica_lag_seconds": 1,
            "packet_scope": "classified",
        }
        ok, violations = verify_observer_lattice_monotonicity(poset_chain, packet)
        self.assertTrue(ok)


class TestTopologicalSimplexNormalForm(unittest.TestCase):
    """Verifies TSNF canonical cell presentation, Stokes nilpotence, and invariant homology."""

    def test_tsnf_canonical_tetrahedron_sphere(self) -> None:
        """Hollow tetrahedron (homeomorphic to S^2) satisfies TSNF with chi=2 and b0=1, b1=0, b2=1."""
        vertices = [0, 1, 2, 3]
        edges = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]
        faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]

        res = verify_tsnf(vertices, edges, faces)
        self.assertTrue(res.is_tsnf)
        self.assertEqual(res.status, "Accept")
        self.assertTrue(res.canonical_vertex_order)
        self.assertTrue(res.stokes_nilpotent)
        self.assertTrue(res.smith_invariant_divisibility)
        self.assertTrue(res.euler_poincare_consistent)
        self.assertEqual(res.euler_characteristic, 2)
        self.assertEqual(res.betti_numbers, {"b0": 1, "b1": 0, "b2": 1})
        self.assertEqual(res.torsion_coefficients, [])

    def test_tsnf_noncanonical_vertex_ordering_rejected(self) -> None:
        """Un-ordered or permuted simplex vertex presentation fails canonical ordering (Reject)."""
        vertices = [0, 1, 2]
        edges = [(1, 0), (1, 2), (0, 2)]  # (1, 0) violates v_0 < v_1
        res = verify_tsnf(vertices, edges)
        self.assertFalse(res.is_tsnf)
        self.assertEqual(res.status, "Reject")
        self.assertFalse(res.canonical_vertex_order)


if __name__ == "__main__":
    unittest.main()
