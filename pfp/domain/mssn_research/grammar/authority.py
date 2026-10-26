"""Value Objects for the Grammar Bounded Context.

Enforces:
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Immutability and Pure Python language types
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import (
    ContentDigest,
    Rational,
    StageLevel,
)

from .exact_structures import ExactRationalMatrix


class HorizonStatus(int, Enum):
    """The Red-Blue-Green master horizon trichotomy status."""
    REFUSAL_RED = 0     # <0>: Format violation or failure stop
    PENDING_BLUE = 1    # <1>: Valid proposal pending evaluation
    CERTIFIED_GREEN = 2 # <2>: Fully certified terminal receipt

    def to_wire_atom(self) -> str:
        return f"<{self.value}>"


class MasterAuthorityEffect(str, Enum):
    """Authority effect for Level 15 horizon terminalization."""
    NONE = "None"
    CERTIFIED_TERMINAL = "CertifiedTerminal"


@dataclass(frozen=True)
class CandidateProposal:
    """Level 15: Generative candidate proposal record."""
    proposal_id: str
    target_carrier: str
    requested_status: HorizonStatus
    proposal_digest: ContentDigest
    author: str = "candidate"

    def __post_init__(self) -> None:
        if not isinstance(self.proposal_id, str) or not self.proposal_id:
            raise ValueError("proposal_id must be a non-empty str")
        if not isinstance(self.target_carrier, str):
            raise TypeError("target_carrier must be a str")
        if not isinstance(self.requested_status, HorizonStatus):
            raise TypeError("requested_status must be a HorizonStatus")
        if not isinstance(self.proposal_digest, ContentDigest):
            raise TypeError("proposal_digest must be a ContentDigest")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, CandidateProposal)
        return (
            self.proposal_id == other.proposal_id
            and self.target_carrier == other.target_carrier
            and self.requested_status == other.requested_status
            and self.proposal_digest == other.proposal_digest
            and self.author == other.author
        )

    def __hash__(self) -> int:
        return hash((type(self), self.proposal_id, self.target_carrier, self.requested_status, self.proposal_digest, self.author))


@dataclass(frozen=True)
class HostVerificationReceipt:
    """Level 15: Independent host verification receipt."""
    verifier_id: str
    witness_digest: ContentDigest
    referenced_rule: str
    eval_verdict: HorizonStatus

    def __post_init__(self) -> None:
        if not isinstance(self.verifier_id, str) or not self.verifier_id:
            raise ValueError("verifier_id must be a non-empty str")
        if not isinstance(self.witness_digest, ContentDigest):
            raise TypeError("witness_digest must be a ContentDigest")
        if not isinstance(self.referenced_rule, str):
            raise TypeError("referenced_rule must be a str")
        if not isinstance(self.eval_verdict, HorizonStatus):
            raise TypeError("eval_verdict must be a HorizonStatus")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, HostVerificationReceipt)
        return (
            self.verifier_id == other.verifier_id
            and self.witness_digest == other.witness_digest
            and self.referenced_rule == other.referenced_rule
            and self.eval_verdict == other.eval_verdict
        )

    def __hash__(self) -> int:
        return hash((type(self), self.verifier_id, self.witness_digest, self.referenced_rule, self.eval_verdict))


@dataclass(frozen=True)
class TerminalAuthorityToken:
    """Level 15: Scoped terminal authority token."""
    scoped_authority_mask: str
    terminal_code: str
    proof_digest: ContentDigest

    def __post_init__(self) -> None:
        if not isinstance(self.scoped_authority_mask, str) or not self.scoped_authority_mask:
            raise ValueError("scoped_authority_mask must be a non-empty str")
        if not isinstance(self.terminal_code, str):
            raise TypeError("terminal_code must be a str")
        if not isinstance(self.proof_digest, ContentDigest):
            raise TypeError("proof_digest must be a ContentDigest")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TerminalAuthorityToken)
        return (
            self.scoped_authority_mask == other.scoped_authority_mask
            and self.terminal_code == other.terminal_code
            and self.proof_digest == other.proof_digest
        )

    def __hash__(self) -> int:
        return hash((type(self), self.scoped_authority_mask, self.terminal_code, self.proof_digest))


@dataclass(frozen=True)
class MasterHorizonPacket:
    """Level 15: Master horizon packet binding proposal, receipt, and scoped authority token."""
    proposal: CandidateProposal
    receipt: Optional[HostVerificationReceipt] = None
    token: Optional[TerminalAuthorityToken] = None
    authority_effect: MasterAuthorityEffect = MasterAuthorityEffect.NONE

    def __post_init__(self) -> None:
        if not isinstance(self.proposal, CandidateProposal):
            raise TypeError("proposal must be a CandidateProposal")
        if self.receipt is not None and not isinstance(self.receipt, HostVerificationReceipt):
            raise TypeError("receipt must be a HostVerificationReceipt")
        if self.token is not None and not isinstance(self.token, TerminalAuthorityToken):
            raise TypeError("token must be a TerminalAuthorityToken")
        if not isinstance(self.authority_effect, MasterAuthorityEffect):
            raise TypeError("authority_effect must be a MasterAuthorityEffect")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, MasterHorizonPacket)
        return (
            self.proposal == other.proposal
            and self.receipt == other.receipt
            and self.token == other.token
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash((type(self), self.proposal, self.receipt, self.token, self.authority_effect))


# ---------------------------------------------------------------------------
# Level 16: Infinite SymSys Filtered Ind-Object Packets
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IndObjectStageRecord:
    """Level 16: Presentation specification for a discrete stage in an ind-object diagram."""
    stage_id: str
    generator_set: tuple[str, ...]
    relation_set: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.stage_id, str):
            raise TypeError("stage_id must be a str")
        if not isinstance(self.generator_set, tuple):
            object.__setattr__(self, "generator_set", tuple(self.generator_set))
        if not isinstance(self.relation_set, tuple):
            object.__setattr__(self, "relation_set", tuple(self.relation_set))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, IndObjectStageRecord)
        return (
            self.stage_id == other.stage_id
            and self.generator_set == other.generator_set
            and self.relation_set == other.relation_set
        )

    def __hash__(self) -> int:
        return hash((type(self), self.stage_id, self.generator_set, self.relation_set))


@dataclass(frozen=True)
class StageMorphism:
    """Level 16: Conservative inclusion morphism u_{i, j} between stages in an ind-object diagram."""
    source_stage: StageLevel
    target_stage: StageLevel
    generator_map: tuple[tuple[str, str], ...]  # (src_gen, target_image)
    conservativity_witness: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_stage, StageLevel) or not isinstance(self.target_stage, StageLevel):
            raise TypeError("source_stage and target_stage must be StageLevel")
        if not isinstance(self.generator_map, tuple):
            object.__setattr__(self, "generator_map", tuple(self.generator_map))
        if not isinstance(self.conservativity_witness, str):
            raise TypeError("conservativity_witness must be a str")

    def as_dict(self) -> dict[str, str]:
        return dict(self.generator_map)

    def is_injective(self) -> bool:
        images = [img for _, img in self.generator_map]
        return len(images) == len(set(images))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, StageMorphism)
        return (
            self.source_stage == other.source_stage
            and self.target_stage == other.target_stage
            and self.generator_map == other.generator_map
            and self.conservativity_witness == other.conservativity_witness
        )

    def __hash__(self) -> int:
        return hash((type(self), self.source_stage, self.target_stage, self.generator_map, self.conservativity_witness))


@dataclass(frozen=True)
class IndObjectPacket:
    """Level 16: Ind-object packet recording filtered diagram stages and transition morphisms."""
    stages: tuple[IndObjectStageRecord, ...]
    morphisms: tuple[StageMorphism, ...]
    quarantine_status: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.stages, tuple):
            object.__setattr__(self, "stages", tuple(self.stages))
        if not isinstance(self.morphisms, tuple):
            object.__setattr__(self, "morphisms", tuple(self.morphisms))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, IndObjectPacket)
        return (
            self.stages == other.stages
            and self.morphisms == other.morphisms
            and self.quarantine_status == other.quarantine_status
        )

    def __hash__(self) -> int:
        return hash((type(self), self.stages, self.morphisms, self.quarantine_status))


# ---------------------------------------------------------------------------
# Level 17: Per-Lift Dialect Languages
# ---------------------------------------------------------------------------

class DialectTag(int, Enum):
    """Parent-local field value allocating specialized dialect sub-languages (Level 17)."""
    SYM_BIN = 0   # <0>: Raw binary carrier cuts
    SYM_LFT = 1   # <1>: Lift contracts and conservative inclusions
    SYM_PAR = 2   # <2>: Parser certificates and proof streams
    SYM_GODEL = 3 # <3>: Diagonal self-reference and cycle markers

    def to_wire_atom(self) -> str:
        return f"<{self.value}>"


class PayloadEncoding(int, Enum):
    """Wire payload encoding format for dialect containers."""
    RAW_UTF8 = 0  # <0>: Raw Gamma_38 wire string
    AST_SEXPR = 1 # <1>: Canonical AST S-expressions


@dataclass(frozen=True)
class DialectContainer:
    """Level 17: Multi-dialect encapsulation container with checksum integrity."""
    dialect_tag: DialectTag
    dialect_version: str
    payload_encoding: PayloadEncoding
    dialect_body: str
    checksum: ContentDigest

    def __post_init__(self) -> None:
        if not isinstance(self.dialect_tag, DialectTag):
            raise TypeError("dialect_tag must be a DialectTag")
        if not isinstance(self.dialect_version, str):
            raise TypeError("dialect_version must be a str")
        if not isinstance(self.payload_encoding, PayloadEncoding):
            raise TypeError("payload_encoding must be a PayloadEncoding")
        if not isinstance(self.dialect_body, str):
            raise TypeError("dialect_body must be a str")
        if not isinstance(self.checksum, ContentDigest):
            raise TypeError("checksum must be a ContentDigest")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DialectContainer)
        return (
            self.dialect_tag == other.dialect_tag
            and self.dialect_version == other.dialect_version
            and self.payload_encoding == other.payload_encoding
            and self.dialect_body == other.dialect_body
            and self.checksum == other.checksum
        )

    def __hash__(self) -> int:
        return hash((type(self), self.dialect_tag, self.dialect_version, self.payload_encoding, self.dialect_body, self.checksum))


# ---------------------------------------------------------------------------
# Level 18: Discrete Hodge Decomposition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HodgeComponents:
    """Level 18: The 3 orthogonal components c = d_0 p + h + d_1^* q."""
    exact_potential_p: tuple[Rational, ...]
    harmonic_cycle_h: tuple[Rational, ...]
    coexact_stream_q: tuple[Rational, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.exact_potential_p, tuple):
            object.__setattr__(self, "exact_potential_p", tuple(self.exact_potential_p))
        if not isinstance(self.harmonic_cycle_h, tuple):
            object.__setattr__(self, "harmonic_cycle_h", tuple(self.harmonic_cycle_h))
        if not isinstance(self.coexact_stream_q, tuple):
            object.__setattr__(self, "coexact_stream_q", tuple(self.coexact_stream_q))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, HodgeComponents)
        return (
            self.exact_potential_p == other.exact_potential_p
            and self.harmonic_cycle_h == other.harmonic_cycle_h
            and self.coexact_stream_q == other.coexact_stream_q
        )

    def __hash__(self) -> int:
        return hash((type(self), self.exact_potential_p, self.harmonic_cycle_h, self.coexact_stream_q))


@dataclass(frozen=True)
class HodgePacket:
    """Level 18: Discrete l^2 Hodge decomposition packet."""
    input_cochain: tuple[Rational, ...]
    components: HodgeComponents
    d0_matrix: ExactRationalMatrix
    d1_matrix: ExactRationalMatrix
    inner_prod_m0: Optional[ExactRationalMatrix] = None
    inner_prod_m1: Optional[ExactRationalMatrix] = None
    inner_prod_m2: Optional[ExactRationalMatrix] = None

    def __post_init__(self) -> None:
        if not isinstance(self.input_cochain, tuple):
            object.__setattr__(self, "input_cochain", tuple(self.input_cochain))
        if not isinstance(self.components, HodgeComponents):
            raise TypeError("components must be HodgeComponents")
        if not isinstance(self.d0_matrix, ExactRationalMatrix) or not isinstance(self.d1_matrix, ExactRationalMatrix):
            raise TypeError("d0_matrix and d1_matrix must be ExactRationalMatrix")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, HodgePacket)
        return (
            self.input_cochain == other.input_cochain
            and self.components == other.components
            and self.d0_matrix == other.d0_matrix
            and self.d1_matrix == other.d1_matrix
            and self.inner_prod_m0 == other.inner_prod_m0
            and self.inner_prod_m1 == other.inner_prod_m1
            and self.inner_prod_m2 == other.inner_prod_m2
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.input_cochain,
            self.components,
            self.d0_matrix,
            self.d1_matrix,
            self.inner_prod_m0,
            self.inner_prod_m1,
            self.inner_prod_m2,
        ))
