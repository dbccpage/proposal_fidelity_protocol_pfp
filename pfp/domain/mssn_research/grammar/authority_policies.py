"""Domain Invariants for the Grammar Bounded Context."""

from __future__ import annotations

import hashlib
from fractions import Fraction

from omega_engine_pfp.domain.mssn_research.grammar.authority import (
    DialectContainer,
    HodgePacket,
    HorizonStatus,
    IndObjectPacket,
    IndObjectStageRecord,
    MasterAuthorityEffect,
    MasterHorizonPacket,
    PayloadEncoding,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Ok, Refusal, Result

from ..packets.value_objects import RefusalCode
from .errors import (
    AuthorityBoundaryError,
    DialectChecksumError,
    GrammarDomainError,
    HodgeDecompositionError,
    IndObjectMorphismError,
)


def check_master_horizon_authority(packet: MasterHorizonPacket) -> Result[bool, GrammarDomainError]:
    """Invariant 20 (Level 15): Master Horizon & Red-Blue-Green Authority Calculus.

    Enforces:
    1. Candidate proposal non-authority: Candidate proposals cannot self-certify green verdict.
    2. Missing verifier digest rejection.
    3. Receipt witness digest must match candidate proposal digest.
    4. Green verdict requires explicit scoped terminal authority token with matching proof digest.
    5. Terminal green packets cannot have authority effect NONE.
    6. Refused proposals (RED) cannot exert terminal authority.
    """
    # 1. Candidate proposals cannot self-certify green verdict without independent receipt
    if packet.proposal.requested_status == HorizonStatus.CERTIFIED_GREEN and packet.receipt is None:
        return Refusal(
            AuthorityBoundaryError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="REFUSED_CANDIDATE_AUTHORED_VERDICT: Candidate proposal cannot self-certify green verdict",
            )
        )

    if packet.receipt is None:
        return Ok(True)
    return _check_horizon_receipt(packet)


def _authority_refusal(message: str) -> Result[bool, GrammarDomainError]:
    return Refusal(
        AuthorityBoundaryError(
            code=RefusalCode.HOST_VERIFICATION_REQUIRED,
            message=message,
        )
    )


def _check_horizon_receipt(packet: MasterHorizonPacket) -> Result[bool, GrammarDomainError]:
    assert packet.receipt is not None
    if not packet.receipt.verifier_id or not packet.receipt.verifier_id.strip():
        return _authority_refusal(
            "REFUSED_MISSING_VERIFIER_DIGEST: Host verification receipt lacks valid verifier digest"
        )
    if packet.receipt.witness_digest != packet.proposal.proposal_digest:
        return _authority_refusal(
            "REFUSED_WITNESS_DIGEST_MISMATCH: Receipt witness digest does not match proposal digest"
        )
    if packet.receipt.eval_verdict == HorizonStatus.CERTIFIED_GREEN:
        return _check_green_authority(packet)
    if (
        packet.receipt.eval_verdict == HorizonStatus.REFUSAL_RED
        and packet.authority_effect != MasterAuthorityEffect.NONE
    ):
        return _authority_refusal(
            "REFUSED_INVALID_AUTHORITY_ON_RED: Refused proposal cannot exert terminal authority"
        )
    return Ok(True)


def _check_green_authority(packet: MasterHorizonPacket) -> Result[bool, GrammarDomainError]:
    assert packet.receipt is not None
    if packet.token is None:
        return _authority_refusal(
            "REFUSED_UNSCOPED_AUTHORITY: Green verdict requires explicit scoped terminal authority token"
        )
    if packet.authority_effect == MasterAuthorityEffect.NONE:
        return _authority_refusal(
            "REFUSED_AUTHORITY_EFFECT_MISMATCH: Terminal certified green packet cannot have authority effect NONE"
        )
    if packet.token.proof_digest != packet.receipt.witness_digest:
        return _authority_refusal(
            "REFUSED_TOKEN_DIGEST_MISMATCH: Terminal token proof digest must bind verification witness digest"
        )
    return Ok(True)


# ---------------------------------------------------------------------------
# Level 16: Infinite SymSys Filtered Ind-Object Packets
# ---------------------------------------------------------------------------


def check_ind_object_morphism(packet: IndObjectPacket) -> Result[bool, GrammarDomainError]:
    """Invariant 21 (Level 16): Filtered Ind-Object Diagram & Conservative Transition Morphisms.

    Enforces:
    1. Rejection of actively quarantined ind-objects.
    2. Strict forward staging: target_stage > source_stage for every transition morphism.
    3. Generator injectivity: morphism cannot collapse distinct source generators.
    4. Complete generator coverage: all source stage generators must be mapped.
    5. Relation preservation and non-empty conservativity witness.
    """
    if packet.quarantine_status:
        return Refusal(
            IndObjectMorphismError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message="REFUSED_QUARANTINED_IND_OBJECT: Ind-object packet is under active quarantine",
            )
        )

    # Index stage records
    stages_by_level: dict[int, IndObjectStageRecord] = {}
    for s in packet.stages:
        digits = "".join(ch for ch in s.stage_id if ch.isdigit())
        if digits:
            stages_by_level[int(digits)] = s

    for morphism in packet.morphisms:
        result = _check_one_morphism(morphism, stages_by_level.get(morphism.source_stage.level))
        if result.is_err():
            return result

    return Ok(True)


def _morphism_refusal(message: str, code: RefusalCode = RefusalCode.NONCONSERVATIVE_LIFT):
    return Refusal(IndObjectMorphismError(code=code, message=message))


def _check_one_morphism(morphism, source_stage) -> Result[bool, GrammarDomainError]:
    if morphism.target_stage.level <= morphism.source_stage.level:
        return _morphism_refusal(
            "REFUSED_NON_FORWARD_STAGING: Ind-object morphism must advance stage "
            f"(got S{morphism.source_stage.level} -> S{morphism.target_stage.level})"
        )
    if not morphism.is_injective():
        return _morphism_refusal(
            "REFUSED_COLLAPSED_GENERATOR: Ind-object morphism collapses distinct generators"
        )
    if source_stage is not None and not set(source_stage.generator_set).issubset(
        morphism.as_dict()
    ):
        return _morphism_refusal(
            "REFUSED_INCOMPLETE_GENERATOR_MAP: Morphism does not map all source generators",
            RefusalCode.WRONG_ARITY,
        )
    if not morphism.conservativity_witness or not morphism.conservativity_witness.strip():
        return _morphism_refusal(
            "REFUSED_MISSING_CONSERVATIVITY_WITNESS: Morphism lacks explicit conservativity witness"
        )
    return Ok(True)


# ---------------------------------------------------------------------------
# Level 17: Per-Lift Dialect Languages
# ---------------------------------------------------------------------------


def check_dialect_container_integrity(
    container: DialectContainer,
) -> Result[bool, GrammarDomainError]:
    """Invariant 22 (Level 17): Dialect Encapsulation & Checksum Verification.

    Enforces:
    1. Cryptographic SHA-256 digest match against declared UTF-8 dialect body.
    2. Syntax validation of AST S-expression dialect payloads (balanced parentheses).
    """
    # 1. SHA-256 Checksum validation
    computed_digest = hashlib.sha256(container.dialect_body.encode("utf-8")).hexdigest()
    if container.checksum.digest_hex != computed_digest:
        return Refusal(
            DialectChecksumError(
                code=RefusalCode.MALFORMED_PACKET,
                message=f"FW-CHECKSUM: Dialect container checksum mismatch (computed {computed_digest[:16]}... != declared {container.checksum.digest_hex[:16]}...)",
            )
        )

    # 2. AST S-expression syntax balance check
    if container.payload_encoding == PayloadEncoding.AST_SEXPR:
        return _check_sexpr_balance(container.dialect_body)

    return Ok(True)


def _check_sexpr_balance(body: str) -> Result[bool, GrammarDomainError]:
    depth = 0
    for index, character in enumerate(body):
        depth += (character == "(") - (character == ")")
        if depth < 0:
            return Refusal(
                DialectChecksumError(
                    code=RefusalCode.MALFORMED_PACKET,
                    message=f"FW-SYNTAX: AST S-expression dialect body has unbalanced parentheses at offset {index}",
                )
            )
    if depth != 0:
        return Refusal(
            DialectChecksumError(
                code=RefusalCode.MALFORMED_PACKET,
                message=f"FW-SYNTAX: AST S-expression dialect body has unclosed parentheses (depth={depth})",
            )
        )
    return Ok(True)


# ---------------------------------------------------------------------------
# Level 18: Discrete l^2 Hodge Decomposition
# ---------------------------------------------------------------------------


def check_hodge_decomposition(packet: HodgePacket) -> Result[bool, GrammarDomainError]:
    """Invariant 23 (Level 18): Discrete l^2 Hodge Decomposition & Mutual Orthogonality over Q.

    Enforces:
    1. Dimension conformity between cochains and differential operators d_0 and d_1.
    2. Exact reconstruction over Q: c = d_0 p + h + d_1^* q.
    3. Harmonic component annihilation: d_1 h == 0 and d_0^* h == 0.
    4. Mutual orthogonality: <d_0 p, h> == 0, <d_0 p, d_1^* q> == 0, <h, d_1^* q> == 0.
    """
    dimension_result = _check_hodge_dimensions(packet)
    if dimension_result.is_err():
        return dimension_result
    exact = _matrix_vector(packet.d0_matrix, packet.components.exact_potential_p)
    coexact = _transpose_matrix_vector(packet.d1_matrix, packet.components.coexact_stream_q)
    harmonic = [_as_fraction(value) for value in packet.components.harmonic_cycle_h]
    reconstruction = _check_hodge_reconstruction(packet, exact, harmonic, coexact)
    if reconstruction.is_err():
        return reconstruction
    harmonic_result = _check_harmonic(packet, harmonic)
    if harmonic_result.is_err():
        return harmonic_result
    return _check_hodge_orthogonality(exact, harmonic, coexact)


def _hodge_refusal(message: str, code: RefusalCode = RefusalCode.HOST_VERIFICATION_REQUIRED):
    return Refusal(HodgeDecompositionError(code=code, message=message))


def _as_fraction(value) -> Fraction:
    return Fraction(value.numerator, value.denominator)


def _check_hodge_dimensions(packet: HodgePacket) -> Result[bool, GrammarDomainError]:
    d0, d1 = packet.d0_matrix, packet.d1_matrix
    checks = (
        (
            len(packet.input_cochain) == d0.rows,
            f"Input cochain length ({len(packet.input_cochain)}) != d0 rows ({d0.rows})",
        ),
        (d1.cols == d0.rows, f"d1 columns ({d1.cols}) != d0 rows ({d0.rows})"),
        (
            len(packet.components.exact_potential_p) == d0.cols,
            f"Exact potential p length ({len(packet.components.exact_potential_p)}) != d0 columns ({d0.cols})",
        ),
        (
            len(packet.components.harmonic_cycle_h) == d0.rows,
            f"Harmonic component h length ({len(packet.components.harmonic_cycle_h)}) != 1-cochain dimension ({d0.rows})",
        ),
        (
            len(packet.components.coexact_stream_q) == d1.rows,
            f"Coexact stream q length ({len(packet.components.coexact_stream_q)}) != d1 rows ({d1.rows})",
        ),
    )
    invalid = next((message for valid, message in checks if not valid), None)
    return Ok(True) if invalid is None else _hodge_refusal(invalid, RefusalCode.WRONG_ARITY)


def _matrix_vector(matrix, vector) -> list[Fraction]:
    return [
        sum(
            (
                _as_fraction(matrix.get(row, column)) * _as_fraction(vector[column])
                for column in range(matrix.cols)
            ),
            Fraction(0),
        )
        for row in range(matrix.rows)
    ]


def _transpose_matrix_vector(matrix, vector) -> list[Fraction]:
    return [
        sum(
            (
                _as_fraction(matrix.get(row, column)) * _as_fraction(vector[row])
                for row in range(matrix.rows)
            ),
            Fraction(0),
        )
        for column in range(matrix.cols)
    ]


def _check_hodge_reconstruction(packet, exact, harmonic, coexact):
    input_values = [_as_fraction(value) for value in packet.input_cochain]
    invalid = next(
        (
            (index, exact[index] + harmonic[index] + coexact[index], expected)
            for index, expected in enumerate(input_values)
            if exact[index] + harmonic[index] + coexact[index] != expected
        ),
        None,
    )
    if invalid is None:
        return Ok(True)
    index, actual, expected = invalid
    return _hodge_refusal(
        f"REFUSED_HODGE_RECONSTRUCTION: Cochain c != d_0 p + h + d_1^* q at index {index} ({actual} != {expected})"
    )


def _check_harmonic(packet, harmonic):
    closed = _matrix_vector(packet.d1_matrix, packet.components.harmonic_cycle_h)
    invalid_closed = next(
        ((index, value) for index, value in enumerate(closed) if value != 0), None
    )
    if invalid_closed is not None:
        index, value = invalid_closed
        return _hodge_refusal(
            f"REFUSED_NON_HARMONIC: Harmonic component h is not closed; (d_1 h)[{index}] = {value} != 0"
        )
    coclosed = _transpose_matrix_vector(packet.d0_matrix, packet.components.harmonic_cycle_h)
    invalid_coclosed = next(
        ((index, value) for index, value in enumerate(coclosed) if value != 0), None
    )
    if invalid_coclosed is None:
        return Ok(True)
    index, value = invalid_coclosed
    return _hodge_refusal(
        f"REFUSED_NON_HARMONIC: Harmonic component h is not coclosed; (d_0^* h)[{index}] = {value} != 0"
    )


def _check_hodge_orthogonality(exact, harmonic, coexact):
    dot_eh = sum(left * right for left, right in zip(exact, harmonic))
    dot_ek = sum(left * right for left, right in zip(exact, coexact))
    dot_hk = sum(left * right for left, right in zip(harmonic, coexact))
    if dot_eh == dot_ek == dot_hk == 0:
        return Ok(True)
    return _hodge_refusal(
        "REFUSED_NON_ORTHOGONAL_HODGE: Components not mutually orthogonal over Q "
        f"(<e,h>={dot_eh}, <e,k>={dot_ek}, <h,k>={dot_hk})"
    )
