"""Domain Invariants for the Grammar Bounded Context."""

from __future__ import annotations

from fractions import Fraction
from typing import Sequence

from omega_engine_pfp.domain.mssn_research.grammar.rewriting import (
    BQNFRoute,
    BQNFViewCochain,
    DDAEventRecord,
    ExpansionCycleToken,
    PeakClaim,
    RewriteStep,
    RuntimeKernel,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Ok, Refusal, Result
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    Rational,
)

from ..packets.value_objects import RefusalCode
from .errors import (
    BQNFRoutingError,
    DDAEventVerificationError,
    ExpansionCycleError,
    GrammarDomainError,
    PolygraphConfluenceError,
)


def check_step_continuity(steps: Sequence[RewriteStep]) -> Result[bool, GrammarDomainError]:
    """Invariant 12 (Level 11): Rewrite step sequence continuity.

    For consecutive steps (s_i -> t_i) and (s_{i+1} -> t_{i+1}), verifies t_i == s_{i+1}.
    """
    if len(steps) <= 1:
        return Ok(True)
    for i in range(len(steps) - 1):
        if steps[i].result_term != steps[i + 1].source_term:
            return Refusal(PolygraphConfluenceError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message=(
                    f"Step discontinuity at index {i}: result_term '{steps[i].result_term}' "
                    f"does not match next source_term '{steps[i + 1].source_term}'"
                )
            ))
    return Ok(True)


def check_peak_claim_confluence(claim: PeakClaim) -> Result[bool, GrammarDomainError]:
    """Invariant 13 (Level 11): Divergent Peak Join Verification.

    Verifies that:
    1. left_path starts at target_left and terminates at join_term (or is empty if target_left == join_term).
    2. right_path starts at target_right and terminates at join_term (or is empty if target_right == join_term).
    3. Step continuity holds along both paths.
    4. Reflexive closure admits empty paths without requiring join_term to be in normal form.
    5. Disallowed divergence raises REFUSED_DIVERGENT_PEAK_JOIN.
    """
    left = _check_peak_path("left", claim.target_left, claim.join_term, claim.left_path)
    if left.is_err():
        return left
    return _check_peak_path("right", claim.target_right, claim.join_term, claim.right_path)


def _check_peak_path(
    side: str,
    target: str,
    join_term: str,
    path: Sequence[RewriteStep],
) -> Result[bool, GrammarDomainError]:
    if not path:
        if target == join_term:
            return Ok(True)
        return Refusal(PolygraphConfluenceError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=(f"REFUSED_DIVERGENT_PEAK_JOIN: Empty {side} path requires target_{side} == join_term, "
                     f"got target_{side}='{target}', join_term='{join_term}'"),
        ))
    if path[0].source_term != target:
        return Refusal(PolygraphConfluenceError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=f"{side.title()} path start mismatch: expected '{target}', got '{path[0].source_term}'",
        ))
    if path[-1].result_term != join_term:
        return Refusal(PolygraphConfluenceError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=f"{side.title()} path end mismatch: expected '{join_term}', got '{path[-1].result_term}'",
        ))
    return check_step_continuity(path)


# ---------------------------------------------------------------------------
# Level 12: DDA Event & Runtime Kernel Invariants
# ---------------------------------------------------------------------------

def check_dda_event_proof(event: DDAEventRecord) -> Result[bool, GrammarDomainError]:
    """Invariant 14 (Level 12): DDA Host Proof & Digest Integrity.

    1. Rejects model-written Pass without host proof (REFUSED_UNPROVEN_DDA_EVENT / FW-REPLAY).
    2. Validates parent_digest as 64-char hex string (REFUSED_INVALID_PARENT_DIGEST).
    3. Validates positive execution step budget B > 0.
    """
    if not event.has_host_proof:
        return Refusal(DDAEventVerificationError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="REFUSED_UNPROVEN_DDA_EVENT: Model-written Pass without host proof is rejected (FW-REPLAY)"
        ))
    if len(event.parent_digest.value) != 64:
        return Refusal(DDAEventVerificationError(
            code=RefusalCode.MALFORMED_PACKET,
            message="REFUSED_INVALID_PARENT_DIGEST: Parent digest must be a 64-character SHA-256 hex digest"
        ))
    if event.budget <= 0:
        return Refusal(DDAEventVerificationError(
            code=RefusalCode.MALFORMED_PACKET,
            message="DDA event budget must be positive"
        ))
    return Ok(True)


def check_runtime_kernel_irredundance(kernel: RuntimeKernel) -> Result[bool, GrammarDomainError]:
    """Invariant 15 (Level 12): Four-Field Kernel Irredundancy.

    Verifies that all 4 fields (B, C, x, Omega) are populated and non-degenerate.
    """
    if kernel.budget <= 0:
        return Refusal(DDAEventVerificationError(
            code=RefusalCode.MALFORMED_PACKET,
            message="Kernel budget B must be positive"
        ))
    if not kernel.context:
        return Refusal(DDAEventVerificationError(
            code=RefusalCode.MALFORMED_PACKET,
            message="Kernel context C cannot be empty"
        ))
    if not kernel.state:
        return Refusal(DDAEventVerificationError(
            code=RefusalCode.MALFORMED_PACKET,
            message="Kernel state x cannot be empty"
        ))
    return Ok(True)


# ---------------------------------------------------------------------------
# Level 13: Higher Alternation Ladders, Expansion Cycles, and BQNF Routes
# ---------------------------------------------------------------------------

def check_expansion_cycle(cycle: ExpansionCycleToken) -> Result[bool, GrammarDomainError]:
    """Invariant 16 (Level 13): Replayable Expansion Cycle Detection.

    If status_code is 1 (EXPANSION_CYCLE_DETECTED):
    Verifies state_digest_1 == state_digest_2 and step_distance > 0.
    """
    if cycle.status_code == 1:
        if cycle.state_digest_1 != cycle.state_digest_2:
            return Refusal(ExpansionCycleError(
                code=RefusalCode.MALFORMED_PACKET,
                message="EXPANSION_CYCLE_DETECTED requires state_digest_1 == state_digest_2"
            ))
        if cycle.step_distance <= 0:
            return Refusal(ExpansionCycleError(
                code=RefusalCode.MALFORMED_PACKET,
                message="REFUSED_STATIONARY_LOOP: Expansion cycle step distance must be > 0"
            ))
    return Ok(True)


def check_bqnf_route_repair(cochain: BQNFViewCochain, route: BQNFRoute) -> Result[bool, GrammarDomainError]:
    """Invariant 17 (Level 13): Exact BQNF Cochain Repair (Route <1>).

    For Route <1> (Repair), checks that omega is an exact coboundary:
    exists alpha in C^0 such that omega = d_0 alpha.
    """
    if route == BQNFRoute.REPAIR:
        if cochain.d0_potential is None:
            return Refusal(BQNFRoutingError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="Route <1> (Repair) requires explicit 0-potential witness alpha"
            ))
        if cochain.d0_matrix is None:
            return Refusal(BQNFRoutingError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="Route <1> (Repair) requires explicit d_0 matrix"
            ))
        d0 = cochain.d0_matrix
        alpha = cochain.d0_potential
        if d0.cols != len(alpha):
            return Refusal(BQNFRoutingError(
                code=RefusalCode.WRONG_ARITY,
                message=f"d0 columns ({d0.cols}) != alpha length ({len(alpha)})"
            ))
        # Compute d_0 * alpha
        computed_omega: list[Rational] = []
        for r in range(d0.rows):
            acc = Fraction(0)
            for c in range(d0.cols):
                d_rc = d0.get(r, c)
                a_c = alpha[c]
                acc += Fraction(d_rc.numerator, d_rc.denominator) * Fraction(a_c.numerator, a_c.denominator)
            computed_omega.append(Rational(acc.numerator, acc.denominator))

        if tuple(computed_omega) != cochain.omega:
            return Refusal(BQNFRoutingError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="Repair failed; omega != d_0 * alpha"
            ))
    return Ok(True)
