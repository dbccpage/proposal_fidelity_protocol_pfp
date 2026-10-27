"""Adversarial stress tests for Milestone 1: Zero-Float & Retraction Loop.

Written by Challenger (challenger_m1_1) to empirically verify:
1. compute_obstruction_score with degenerate cycle inputs never casts to float.
2. Q and ObstructionScore reject float comparisons and float inputs.
3. Strict descent and zero-float invariants on discrete manifold retraction.

Examiner Test Structure:
- Invariant: Exact rational typing, non-coercion, and type rejection.
- Break: Attempted injection of floats into Q comparisons, ObstructionScore fields, and degenerate cycles.
- Witness: Concrete exception codes ('RR-FLOAT') and type certificates.
- Mutation: Verification that float coercion fails-closed.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
import pytest

from pfp.domain.exact.q import Q
from pfp.domain.exact.errors import ExactError
from pfp.domain.models import ObstructionScore
from pfp.domain.solvers import (
    AdmitDatum,
    HolonomyLoopClosed,
    HomologyBoundaryClosed,
    RegimeK,
    compute_obstruction_score,
    host,
)


# =============================================================================
# 1. DEGENERATE CYCLE STRESS TESTS FOR compute_obstruction_score
# =============================================================================

def test_compute_obstruction_score_empty_faces() -> None:
    """Degenerate input: HomologyBoundaryClosed with empty faces tuple ()."""
    q = HomologyBoundaryClosed("h_empty", ())
    r = host(base_history=(AdmitDatum(0),), claim_forms=frozenset(), reqs=(q,))
    score = compute_obstruction_score(r)

    assert score.phi_1 == Fraction(0, 1)
    assert isinstance(score.phi_1, Fraction)
    assert not isinstance(score.phi_1, float)
    assert score.gamma_2 == Fraction(0, 1)
    assert isinstance(score.gamma_2, Fraction)
    assert not isinstance(score.gamma_2, float)
    assert score.active_count == 0


def test_compute_obstruction_score_empty_terms_in_face() -> None:
    """Degenerate input: HomologyBoundaryClosed with a face having empty terms ((),)."""
    q = HomologyBoundaryClosed("h_empty_face", ((),))
    r = host(base_history=(AdmitDatum(0),), claim_forms=frozenset(), reqs=(q,))
    score = compute_obstruction_score(r)

    assert score.phi_1 == Fraction(0, 1)
    assert isinstance(score.phi_1, Fraction)
    assert not isinstance(score.phi_1, float)


def test_compute_obstruction_score_self_loop_edge() -> None:
    """Degenerate input: Self-loop edge (0->0 with sign +1). Net boundary is 0."""
    q = HomologyBoundaryClosed("h_self_loop", (((0, 0, 1),),))
    r = host(base_history=(AdmitDatum(0),), claim_forms=frozenset(), reqs=(q,))
    score = compute_obstruction_score(r)

    assert score.phi_1 == Fraction(0, 1)
    assert isinstance(score.phi_1, Fraction)
    assert not isinstance(score.phi_1, float)


def test_compute_obstruction_score_canceling_edges() -> None:
    """Degenerate input: Two opposite edges between nodes 0 and 1 that cancel to zero."""
    q = HomologyBoundaryClosed("h_canceling", (((0, 1, 1), (0, 1, -1)),))
    r = host(base_history=(AdmitDatum(0), AdmitDatum(1)), claim_forms=frozenset(), reqs=(q,))
    score = compute_obstruction_score(r)

    assert score.phi_1 == Fraction(0, 1)
    assert isinstance(score.phi_1, Fraction)
    assert not isinstance(score.phi_1, float)


def test_compute_obstruction_score_open_chain_large_violation() -> None:
    """Open 1-chain with 50 sequential edges. Net boundary is +1 at 50, -1 at 0."""
    edges = tuple((i, i + 1, 1) for i in range(50))
    q = HomologyBoundaryClosed("h_large_chain", (edges,))
    r = host(
        base_history=tuple(AdmitDatum(i) for i in range(51)),
        claim_forms=frozenset(),
        reqs=(q,),
    )
    score = compute_obstruction_score(r)

    assert score.phi_1 == Fraction(1, 1)
    assert isinstance(score.phi_1, Fraction)
    assert not isinstance(score.phi_1, float)


def test_compute_obstruction_score_star_topology_weighted() -> None:
    """Star topology with multiple weighted edges producing violation > 1."""
    edges = ((0, 1, 3), (0, 2, 5), (0, 3, 7))
    q = HomologyBoundaryClosed("h_star", (edges,))
    r = host(
        base_history=tuple(AdmitDatum(i) for i in range(4)),
        claim_forms=frozenset(),
        reqs=(q,),
    )
    score = compute_obstruction_score(r)

    assert score.phi_1 == Fraction(15, 1)
    assert isinstance(score.phi_1, Fraction)
    assert not isinstance(score.phi_1, float)


def test_compute_obstruction_score_holonomy_fractional_defect() -> None:
    """Holonomy loop with fractional matrix entries producing non-integer curvature distance."""
    t_frac = ((Q(1, 3), Q(2, 3)), (Q(2, 3), Q(1, 3)))
    q = HolonomyLoopClosed("h_frac_loop", (t_frac,), ((0, False),))
    r = host(
        base_history=(AdmitDatum(0), AdmitDatum(1)),
        claim_forms=frozenset(),
        reqs=(q,),
    )
    score = compute_obstruction_score(r)

    assert score.gamma_2 == Fraction(8, 3)
    assert isinstance(score.gamma_2, Fraction)
    assert not isinstance(score.gamma_2, float)


# =============================================================================
# 2. FLOAT REJECTION IN Q COMPARISONS
# =============================================================================

@pytest.mark.parametrize("op", ["__lt__", "__le__", "__gt__", "__ge__"])
def test_q_rejects_float_comparisons(op: str) -> None:
    """Verify Q raises ExactError('RR-FLOAT') on floating point comparisons.

    Invariant: Zero-Float Law and PROJECT.md:
      'Rejections: float raises ExactError(\"RR-FLOAT\")'
      'There is no float path: a float ... is refused by name.'
    """
    q = Q(1, 2)
    comparator = getattr(q, op)
    with pytest.raises(ExactError) as exc_info:
        comparator(0.5)
    assert exc_info.value.code == "RR-FLOAT"


def test_q_exact_type_equality_rejects_float() -> None:
    """Verify Q == float returns False under exact-type equality."""
    q = Q(1, 2)
    assert (q == 0.5) is False
    assert (0.5 == q) is False


# =============================================================================
# 3. FLOAT REJECTION IN ObstructionScore
# =============================================================================

def test_obstruction_score_rejects_float_arguments() -> None:
    """Verify ObstructionScore rejects floating point inputs for gamma_2 and phi_1.

    Invariant: Zero-Float Invariant in PROJECT.md:
      'All discrete state evaluation ... and obstruction scoring operate on
      exact rationals (Q, Fraction) or F_2. Floating-point arithmetic is forbidden.'
    """
    with pytest.raises((TypeError, ExactError)):
        ObstructionScore(gamma_2=0.5, phi_1=Fraction(0, 1), active_count=0)

    with pytest.raises((TypeError, ExactError)):
        ObstructionScore(gamma_2=Fraction(0, 1), phi_1=0.5, active_count=0)
