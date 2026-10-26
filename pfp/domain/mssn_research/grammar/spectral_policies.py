"""Domain Invariants for the Grammar Bounded Context."""

from __future__ import annotations

from fractions import Fraction

from omega_engine_pfp.domain.mssn_research.grammar.spectral_geometry import (
    AutopoieticExpansionCyclePacket,
    Regge4DPacket,
    ZetaShadowPacket,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Ok, Refusal, Result

from ..packets.invariants import _exact_det
from ..packets.value_objects import RefusalCode
from .errors import (
    AutopoieticCycleError,
    GrammarDomainError,
    ReggeSimplicialError,
    ZetaSpectralQuarantineError,
)


def check_zeta_spectral_quarantine(packet: ZetaShadowPacket) -> Result[bool, GrammarDomainError]:
    """Invariant 24 (Level 19): Zeta Spectral Shadow Quarantine & Integer Polynomial Preservation.

    Enforces:
    1. Exact rational/integer orbit polynomial preservation (rejecting rounded floating-point laundering).
    2. Epistemic quarantine fence status requirement: 'FENCED_COMBINATORIAL_MODEL'.
    3. Normalization condition: constant term P(0) == 1.
    """
    # 1. Exact integer/rational polynomial representation check
    if not packet.is_exact_rational_poly:
        return Refusal(ZetaSpectralQuarantineError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="REFUSED_INEXACT_ZETA_ROUNDING: Non-rational or floating-point rounded pole laundering rejected",
        ))

    # 2. Epistemic quarantine fence status
    if packet.quarantine_fence_status != "FENCED_COMBINATORIAL_MODEL":
        return Refusal(ZetaSpectralQuarantineError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="REFUSED_UNFENCED_SPECTRAL_SHADOW: Zeta spectral shadow requires FENCED_COMBINATORIAL_MODEL fence status",
        ))

    # 3. Polynomial normalization P(0) == 1
    if len(packet.orbit_polynomial_coefficients) == 0 or packet.orbit_polynomial_coefficients[0] != 1:
        return Refusal(ZetaSpectralQuarantineError(
            code=RefusalCode.MALFORMED_PACKET,
            message="REFUSED_INVALID_CHARACTERISTIC_POLY: Orbit polynomial must satisfy P(0) = 1",
        ))

    return Ok(True)


# ---------------------------------------------------------------------------
# Level 20: Autopoietic Reflection & Expansion Cycle Detection
# ---------------------------------------------------------------------------

def check_autopoietic_expansion_cycle(packet: AutopoieticExpansionCyclePacket) -> Result[bool, GrammarDomainError]:
    """Invariant 25 (Level 20): Autopoietic Reflection & Expansion Cycle Detection.

    Enforces:
    1. Productive recursion preservation: Strictly decreasing measure cannot be misclassified as a cycle.
    2. Exact state digest repetition (s_t == s_{t-k}).
    3. Positive step distance (k > 0).
    4. Non-negative progress delta (Delta mu >= 0).
    """
    # 1. Productive recursion distinction
    if packet.is_strictly_decreasing or packet.progress_delta < 0:
        return Refusal(AutopoieticCycleError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="REFUSED_DECREASING_CYCLE_MISCLASSIFICATION: Productive recursive descent with strictly decreasing measure cannot be classified as expansion cycle",
        ))

    # 2. State digest repetition
    if packet.state_digest_initial != packet.state_digest_repeated:
        return Refusal(AutopoieticCycleError(
            code=RefusalCode.WRONG_ARITY,
            message="REFUSED_NON_REPEATED_STATE: Cycle detection requires identical initial and repeated state digests",
        ))

    # 3. Positive step distance
    if packet.step_distance <= 0:
        return Refusal(AutopoieticCycleError(
            code=RefusalCode.WRONG_ARITY,
            message="REFUSED_ZERO_STEP_CYCLE: Cycle step distance must be positive integer",
        ))

    return Ok(True)


# ---------------------------------------------------------------------------
# Level 21: Discrete 4D Regge Metric Deficit & Simplicial Curvature
# ---------------------------------------------------------------------------

def check_regge_4d_simplicial_curvature(packet: Regge4DPacket) -> Result[bool, GrammarDomainError]:
    """Invariant 26 (Level 21): Discrete 4D Regge Metric Deficit & Simplicial Curvature.

    Enforces:
    1. 4D Cayley-Menger determinant sign convention: det(CM) = -9216 V_4^2 < 0.
    2. Gram matrix positive-definiteness via Sylvester's criterion.
    3. Rejection of linear scalar deficit angle sums in place of non-linear Bianchi holonomy closure.
    4. Exact non-linear Bianchi holonomy closure: product of rotation matrices around 3-cell boundary is Identity.
    """
    # 1. 4D Cayley-Menger determinant sign convention: must be strictly negative for Euclidean 4-simplex
    if packet.cayley_menger_det.numerator >= 0:
        return Refusal(ReggeSimplicialError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="REFUSED_INVALID_4D_CAYLEY_MENGER: In 4D Euclidean Regge calculus, Cayley-Menger det must be strictly negative (-9216 V_4^2 < 0)",
        ))

    # 2. Linear scalar sum substitution rejection
    if packet.uses_scalar_sum_only:
        return Refusal(ReggeSimplicialError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="REFUSED_SCALAR_DEFICIT_SUBSTITUTION: Linear scalar deficit sum substitution rejected; requires non-linear SO(4) holonomy closure",
        ))

    # 3. Bianchi holonomy closure
    if not packet.bianchi_closure_satisfied:
        return Refusal(ReggeSimplicialError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="REFUSED_BIANCHI_HOLONOMY_OPEN: 4D simplicial Bianchi identity fails; holonomy around 3-cell boundary is not identity",
        ))

    # 4. Gram matrix positive-definiteness
    if packet.gram_matrix is None:
        return Ok(True)
    return _check_positive_gram(packet)


def _check_positive_gram(packet: Regge4DPacket) -> Result[bool, GrammarDomainError]:
    matrix = packet.gram_matrix
    assert matrix is not None
    if matrix.rows != matrix.cols:
        return Refusal(ReggeSimplicialError(
            code=RefusalCode.WRONG_ARITY,
            message=f"Gram matrix must be square, got {matrix.rows}x{matrix.cols}",
        ))
    fractions = [[Fraction(matrix.get(row, column).numerator, matrix.get(row, column).denominator)
                  for column in range(matrix.cols)] for row in range(matrix.rows)]
    invalid = next(((order, determinant) for order in range(1, matrix.rows + 1)
                    if (determinant := _exact_det([row[:order] for row in fractions[:order]])) <= 0), None)
    if invalid is None:
        return Ok(True)
    order, determinant = invalid
    return Refusal(ReggeSimplicialError(
        code=RefusalCode.HOST_VERIFICATION_REQUIRED,
        message=(f"REFUSED_NON_POSITIVE_GRAM: Gram matrix leading minor of order {order} "
                 f"is non-positive ({determinant})"),
    ))
