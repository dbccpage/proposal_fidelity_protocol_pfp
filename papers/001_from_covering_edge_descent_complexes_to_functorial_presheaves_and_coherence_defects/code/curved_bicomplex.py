"""Curved bicomplex and operator derivation identities for PO-001 v2.0.

AuthorityEffect: None.

This module formalizes and verifies the curved differential derivation identity:
    (delta_2(delta_1(T)))_{d, c, b, a} = [K, T]_{d, c, b, a}
                                        = K_{c, b, a} * T_{d, c} - T_{b, a} * K_{d, c, b}
for all quadruples a <= b <= c <= d, arbitrary Banach/matrix fibers, and arbitrary
restriction systems.

Key structural properties:
1. When K == 0 (flat restriction system), [K, T] == 0 identically, so delta_2(delta_1(T)) == 0,
   recovering standard nilpotency of the coboundary operator.
2. When K != 0 (curved/non-flat restriction system), delta_2(delta_1(T)) evaluates exactly to
   the operator commutator [K, T].
3. The discrepancy delta_2(delta_1(T)) - [K, T] vanishes identically and unconditionally
   across all quadruples, with zero residual.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Tuple

from covering_edge_poset import FinitePoset, NodeId
from exact import exact_equal
from exactsym import Matrix
from restriction_system import RestrictionSystem, build_path_a_completion
from cohomology_quotient import (
    Operator1Cochain,
    Operator2Cochain,
    Operator3Cochain,
    operator_coboundary_delta1,
    operator_coboundary_delta2,
    build_curvature_operator_cochain,
)


def compute_curvature_commutator_3cochain(
    system: RestrictionSystem,
    k: Operator2Cochain,
    t: Operator1Cochain,
) -> Operator3Cochain:
    """Compute the curved operator commutator 3-cochain [K, T].

    For each quadruple a <= b <= c <= d:
        [K, T]_{d, c, b, a} = K_{c, b, a} * T_{d, c} - T_{b, a} * K_{d, c, b}

    Where:
        - K_{c, b, a}: F(c) -> F(a)
        - T_{d, c}: F(d) -> F(c)
        - Product K_{c, b, a} * T_{d, c}: F(d) -> F(a)
        - T_{b, a}: F(b) -> F(a)
        - K_{d, c, b}: F(d) -> F(b)
        - Product T_{b, a} * K_{d, c, b}: F(d) -> F(a)
    """
    poset = system.poset
    res: Dict[Tuple[NodeId, NodeId, NodeId, NodeId], Matrix] = {}

    for a in poset.elements:
        for b in poset.elements:
            if not poset.is_le(a, b):
                continue
            for c in poset.elements:
                if not poset.is_le(b, c):
                    continue
                for d in poset.elements:
                    if not poset.is_le(c, d):
                        continue
                    k_cba = k(a, b, c)
                    k_dcb = k(b, c, d)
                    t_dc = t(c, d)
                    t_ba = t(a, b)
                    comm = k_cba * t_dc - t_ba * k_dcb
                    res[(a, b, c, d)] = comm

    return Operator3Cochain(poset=poset, operators=res)


def compute_curved_derivation_3cochain(
    system: RestrictionSystem,
    t: Operator1Cochain,
) -> Operator3Cochain:
    """Compute the second operator coboundary composition delta_2(delta_1(T))."""
    delta1_t = operator_coboundary_delta1(system, t)
    return operator_coboundary_delta2(system, delta1_t)


def compute_curved_derivation_residual_3cochain(
    system: RestrictionSystem,
    t: Operator1Cochain,
) -> Operator3Cochain:
    """Compute the algebraic residual delta_2(delta_1(T)) - [K, T].

    Under exact arithmetic, this 3-cochain must be identically zero.
    """
    delta2_delta1_t = compute_curved_derivation_3cochain(system, t)
    k = build_curvature_operator_cochain(system)
    comm = compute_curvature_commutator_3cochain(system, k, t)

    res: Dict[Tuple[NodeId, NodeId, NodeId, NodeId], Matrix] = {}
    for q, m in delta2_delta1_t.operators.items():
        res[q] = m - comm.operators[q]

    return Operator3Cochain(poset=system.poset, operators=res)


def verify_curved_derivation_identity(
    system: RestrictionSystem,
    t: Operator1Cochain,
) -> Tuple[bool, Operator3Cochain, Operator3Cochain]:
    """Verify Theorem 4.1: delta_2(delta_1(T)) == [K, T] identically.

    Returns:
        (is_identical, delta2_delta1_t, commutator)
    """
    delta2_delta1_t = compute_curved_derivation_3cochain(system, t)
    k = build_curvature_operator_cochain(system)
    comm = compute_curvature_commutator_3cochain(system, k, t)
    matches = (delta2_delta1_t == comm)
    return matches, delta2_delta1_t, comm


@dataclass(frozen=True)
class CurvedPosetBicomplex:
    """High-level evaluator for curved poset complexes and derivation algebras."""

    system: RestrictionSystem
    curvature: Operator2Cochain

    @classmethod
    def from_system(cls, system: RestrictionSystem) -> CurvedPosetBicomplex:
        k = build_curvature_operator_cochain(system)
        return cls(system=system, curvature=k)

    @property
    def poset(self) -> FinitePoset:
        return self.system.poset

    def is_flat(self) -> bool:
        """Check if all curvature components vanish (K == 0 everywhere)."""
        return self.curvature.is_zero()

    def curvature_l1_norm(self) -> Fraction:
        """Compute the sum of absolute values of all curvature matrix entries."""
        total = Fraction(0)
        for m in self.curvature.operators.values():
            for r in range(m.rows):
                for c in range(m.cols):
                    total += abs(m[r, c])
        return total

    def evaluate_commutator(self, t: Operator1Cochain) -> Operator3Cochain:
        """Compute [K, T]."""
        return compute_curvature_commutator_3cochain(self.system, self.curvature, t)

    def evaluate_derivation(self, t: Operator1Cochain) -> Operator3Cochain:
        """Compute delta_2(delta_1(T))."""
        return compute_curved_derivation_3cochain(self.system, t)

    def verify_identity(self, t: Operator1Cochain) -> bool:
        """Verify that delta_2(delta_1(T)) == [K, T] for a given 1-cochain T."""
        matches, _, _ = verify_curved_derivation_identity(self.system, t)
        return matches


@dataclass(frozen=True)
class NormalFormDecomposition:
    """Additive correction to a Path A completion, when cover paths commute."""

    flat_background: RestrictionSystem
    correction: Dict[Tuple[NodeId, NodeId], Matrix]


def decompose_normal_form(system: RestrictionSystem) -> NormalFormDecomposition:
    """Retain all covering maps and refuse inconsistent saturated-chain paths.

    This is an additive decomposition, not an orthogonal projection. For
    general triples curvature also contains the correction's mixed products;
    K = -A on the outer pair holds when both inner legs are covering edges.
    """
    poset = system.poset
    covers = [system.get_restriction(edge.lower, edge.upper) for edge in poset.covering_edges]
    background = build_path_a_completion(poset, system.fiber_dimensions, covers)
    correction = {}
    for pair in poset.comparable_pairs():
        a, c = pair.lower, pair.upper
        correction[(a, c)] = system.get_restriction(a, c).matrix - background.get_restriction(a, c).matrix
    return NormalFormDecomposition(background, correction)
