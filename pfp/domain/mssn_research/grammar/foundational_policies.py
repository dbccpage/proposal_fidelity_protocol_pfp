"""Domain Invariants for the Grammar Bounded Context."""

from __future__ import annotations

from typing import Sequence

from omega_engine_pfp.domain.mssn_research.grammar.exact_structures import (
    ExactRationalTensor,
    HostFenceAudit,
    PontryaginKillFlags,
    QuarantinedShadowPacket,
    ReversalMap,
    TraceInvarianceDisposition,
)
from omega_engine_pfp.domain.mssn_research.grammar.lexical import (
    Alphabet,
    ProbabilityMass,
    QuantifierMask,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    Rational,
    StageLevel,
)

from ..packets.entities import Packet
from ..packets.value_objects import RefusalCode
from .errors import (
    AlphabetViolationError,
    AlternationDepthExceededError,
    DaggerInvolutionError,
    GrammarDomainError,
    OptimalityInvariantError,
    QuarantineViolationError,
    ScopeBoundaryViolationError,
    TensorInvariantError,
    ZeroRetainedMassError,
)


def check_alphabet_conformance(text: str, alphabet: Alphabet) -> Result[bool, GrammarDomainError]:
    """Invariant 1: Every character in text must belong to the active alphabet."""
    for idx, c in enumerate(text):
        if not alphabet.contains(c):
            return Refusal(AlphabetViolationError(
                code=RefusalCode.INACTIVE_SYMBOL,
                message=f"Character {c!r} at offset {idx} is outside declared alphabet"
            ))
    return Ok(True)


def check_zero_mass_fence(retained_mass: ProbabilityMass) -> Result[bool, GrammarDomainError]:
    """Invariant 2: Zero retained probability mass must trigger an immediate fail-stop refusal."""
    if retained_mass.is_zero():
        return Refusal(ZeroRetainedMassError(
            code=RefusalCode.ZERO_RETAINED_MASS,
            message="Zero probability mass; no valid tokens in frontier"
        ))
    return Ok(True)


def check_quantifier_mask_depth(mask: QuantifierMask, max_depth: int = 12) -> Result[bool, GrammarDomainError]:
    """Invariant 3: Alternation depth cannot exceed primitive recursive bound k <= 12."""
    depth = mask.alternation_depth
    if depth > max_depth:
        return Refusal(AlternationDepthExceededError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=f"Quantifier alternation depth {depth} exceeds bound {max_depth}"
        ))
    return Ok(True)


def check_stage_quantifier_alternation(mask: QuantifierMask, stage: StageLevel) -> Result[bool, GrammarDomainError]:
    """Invariant 3b: Alternation depth cannot exceed stage level budget ceiling D(n) = stage.level."""
    depth = mask.alternation_depth
    if depth > stage.level:
        return Refusal(AlternationDepthExceededError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=f"Quantifier alternation depth {depth} exceeds stage {stage.level} ceiling ({stage.level})"
        ))
    return Ok(True)


def check_wire_round_trip(packet: Packet) -> Result[bool, GrammarDomainError]:
    """Invariant 4: Serialization of the parsed AST must exactly equal the input wire string."""
    re_serialized = packet.node.serialize()
    if re_serialized != packet.wire.raw:
        return Err(AlphabetViolationError(
            code=RefusalCode.MALFORMED_PACKET,
            message=f"Round-trip mismatch: {re_serialized!r} != {packet.wire.raw!r}"
        ))
    return Ok(True)


def check_tensor_product_invariants(tensor: ExactRationalTensor) -> Result[bool, GrammarDomainError]:
    """Invariant 5: Higher-order tensor product must satisfy exact algebraic invariants.

    1. Dimension multiplicativity: dim(A (x) B) = dim(A) * dim(B)
    2. Trace multiplicativity: Tr(A (x) B) = Tr(A) * Tr(B)
    3. Associativity (for order >= 3): (A (x) B) (x) C == A (x) (B (x) C)
    """
    comp = tensor.evaluate_composite()
    expected_r, expected_c = tensor.total_dimension()
    if comp.rows != expected_r or comp.cols != expected_c:
        return Err(TensorInvariantError(
            code=RefusalCode.WRONG_ARITY,
            message=f"Tensor composite shape ({comp.rows}, {comp.cols}) != expected ({expected_r}, {expected_c})"
        ))

    # Trace multiplicativity for square factor tensor products
    all_square = all(f.rows == f.cols for f in tensor.factors)
    if all_square:
        comp_tr = comp.trace()
        prod_tr = tensor.trace_product()
        if comp_tr != prod_tr:
            return Err(TensorInvariantError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message=f"Trace multiplicativity violation: composite trace {comp_tr} != product of traces {prod_tr}"
            ))

    # Associativity check for 3-factor tensors: (A (x) B) (x) C == A (x) (B (x) C)
    if tensor.order == 3:
        a, b, c = tensor.factors
        ab_c = a.kronecker_product(b).kronecker_product(c)
        a_bc = a.kronecker_product(b.kronecker_product(c))
        if ab_c != a_bc:
            return Err(TensorInvariantError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="Tensor product associativity check failed: (A (x) B) (x) C != A (x) (B (x) C)"
            ))

    return Ok(True)


def check_level7_orbit_primitivity(
    period: int,
    is_primitive: bool,
    vertices: Sequence[str]
) -> Result[bool, GrammarDomainError]:
    """Invariant 6 (Level 7): Primitivity verification law for periodic orbits.

    If is_primitive is declared True (<1>), vertex sequence cannot be generated
    by repeating a strictly shorter block divisor d < period.
    """
    if len(vertices) != period:
        return Refusal(AlphabetViolationError(
            code=RefusalCode.WRONG_ARITY,
            message=f"Declared period {period} does not match vertex sequence length {len(vertices)}"
        ))

    n = len(vertices)
    divisor = next((size for size in range(1, n)
                    if n % size == 0
                    and list(vertices) == list(vertices[:size]) * (n // size)), None)
    if divisor is not None and is_primitive:
        return Refusal(AlphabetViolationError(
            code=RefusalCode.MALFORMED_PACKET,
            message=(f"Primitivity contradiction: orbit of length {n} is generated by "
                     f"repeating sub-block of length {divisor}"),
        ))

    return Ok(True)


def check_level8_primal_dual_gap(
    primal_mass: Rational,
    dual_mass: Rational
) -> Result[bool, GrammarDomainError]:
    """Invariant 7 (Level 8): Primal-Dual LP Optimality Invariant.

    A valid DualCertReceipt strictly requires primal_mass == dual_mass (zero duality gap).
    """
    if primal_mass != dual_mass:
        return Refusal(OptimalityInvariantError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=f"Duality gap contradiction: primal mass {primal_mass.to_wire()} != dual mass {dual_mass.to_wire()}"
        ))
    return Ok(True)


def check_dagger_involution_law(reversal_map: ReversalMap) -> Result[bool, GrammarDomainError]:
    """Invariant 8 (Level 9): Involution Law for Dagger profunctors.

    Verifies ((e)^dag)^dag == e for all non-obstructed edge mappings.
    Missing edges mapped to 'bot' assign zero support and pass vacuously.
    """
    if not reversal_map.satisfies_involution_law():
        return Refusal(DaggerInvolutionError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message="Dagger involution law violation: ((e)^dag)^dag != e in reversal map"
        ))
    return Ok(True)


def check_dagger_trace_invariance(
    claimed_trace: Rational,
    computed_trace: Rational,
    asserted_invariance: bool
) -> Result[TraceInvarianceDisposition, GrammarDomainError]:
    """Invariant 9 (Level 9): Trace Invariance Verification & Claim Discipline.

    Enforces that candidate-asserted invariance flag (<1>) cannot self-certify.
    If computed_trace == claimed_trace, host emits INVARIANT_VERIFIED (<1>).
    If computed_trace != claimed_trace, host computes ASYMMETRIC (<0>).
    If candidate asserted invariance (<1>) while asymmetric, host refuses candidate.
    """
    is_symmetric = (claimed_trace == computed_trace)

    if not is_symmetric and asserted_invariance:
        return Refusal(DaggerInvolutionError(
            code=RefusalCode.UNSUPPORTED_INTERPRETATION,
            message=(
                f"Candidate claimed trace invariance (<1>) with value {claimed_trace.to_wire()}, "
                f"but host computed asymmetric trace {computed_trace.to_wire()} (receipt <0>)"
            )
        ))

    if is_symmetric:
        return Ok(TraceInvarianceDisposition.INVARIANT_VERIFIED)
    return Ok(TraceInvarianceDisposition.ASYMMETRIC)


def check_pontryagin_firewall(assertion: PontryaginKillFlags) -> Result[HostFenceAudit, GrammarDomainError]:
    """Invariant 10 (Level 10): Pontryagin Boundary Kill Firewall.

    Inspects candidate promotion assertions against the 4 structural firewalls:
    1. flag_pi: PI_FROM_EXACT_Q (prohibits deriving continuous pi from Q)
    2. flag_u1: U1_FROM_L1_MASS_ALONE (prohibits continuous U(1) from L1 mass)
    3. flag_zn: ZN_SOLD_AS_FREE_U1_WITHOUT_UNBOUNDED_DECL (prohibits Z_n as free U(1))
    4. flag_alpha: ALPHA_AS_CERTIFIED_EXACT (prohibits fine-structure alpha from combinatorics)

    If any kill fence is breached, the host issues ViolatedKillFence (receipt <0>)
    and refuses the packet.
    """
    audit = HostFenceAudit.evaluate(assertion)
    if not audit.quarantine_verdict:
        breaches: list[str] = []
        if assertion.flag_pi:
            breaches.append("PI_FROM_EXACT_Q")
        if assertion.flag_u1:
            breaches.append("U1_FROM_L1_MASS_ALONE")
        if assertion.flag_zn:
            breaches.append("ZN_SOLD_AS_FREE_U1_WITHOUT_UNBOUNDED_DECL")
        if assertion.flag_alpha:
            breaches.append("ALPHA_AS_CERTIFIED_EXACT")
        return Refusal(QuarantineViolationError(
            code=RefusalCode.NONCONSERVATIVE_LIFT,
            message=f"Pontryagin boundary firewall breach: {', '.join(breaches)}; host audit verdict <0>"
        ))
    return Ok(audit)


def check_permanent_quarantine_isolation(
    packet: QuarantinedShadowPacket,
    target_stage: StageLevel
) -> Result[bool, GrammarDomainError]:
    """Invariant 11 (Level 10): Permanent Quarantine Law & Zero Scope Leakage.

    A Level 10 quarantined packet remains strictly quarantined forever.
    It carries AuthorityEffect: None and can NEVER serve as a premise or axiom
    for Level 0-9 core structural lifts. Smuggling quarantined conclusions into
    core stages raises FW-SCOPE.
    """
    if target_stage.level <= 9:
        return Refusal(ScopeBoundaryViolationError(
            code=RefusalCode.NONCONSERVATIVE_LIFT,
            message=(
                f"Permanent Quarantine Law violation: packet for target theorem '{packet.target_theorem}' "
                f"cannot be promoted or imported into core stage {target_stage.level} (FW-SCOPE)"
            )
        ))
    return Ok(True)
