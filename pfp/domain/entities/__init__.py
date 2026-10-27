"""Domain Entities package for the Symbol Game bounded context."""

from .candidate_artifact import CandidateArtifactV1
from .coboundary_score import (
    AUTHORITY_EFFECT,
    COBOUNDARY_SCORE_FAMILY,
    COBOUNDARY_SCORE_SCHEMA,
    CandidateProposal,
    CoboundaryScoreResult,
    REFUSAL_AUTHORITY,
    REFUSAL_EXACT_WITHOUT_DUAL,
    REFUSAL_EXACT_WITHOUT_DUAL_WITNESS,
    REFUSAL_ILLEGAL_PROPOSAL,
    REFUSAL_NEGATIVE_MAGNITUDE,
    ResidualDropV1,
)
from .gate_receipt import GateReceiptV1
from .obstruction import ObstructionLedger, ProcessEventLog, verify_event_chain
from .obstruction_ledger_event import ObstructionLedgerEvent
from .packet_envelope import (
    CANDIDATE_SCHEMA,
    EVALUATION_SCHEMA,
    LAB_TERMINAL_STATUSES,
    PACKET_SCHEMA,
    AttemptEvidenceV1,
    EvaluationReceiptV1,
    PacketEnvelopeV2,
)
from .process_event import ProcessEvent
from .research_packets import (
    ClaimKind,
    CorpusFileRef,
    EvidenceCeiling,
    ResearchClaim,
    ResearchMode,
    ResearchProposal,
    ResearchSeedPacket,
    ResearchStepPacket,
    StepRealization,
    SymbolGameResearchPacket,
    digest_payload,
)

__all__ = [
    "AUTHORITY_EFFECT",
    "AttemptEvidenceV1",
    "CANDIDATE_SCHEMA",
    "COBOUNDARY_SCORE_FAMILY",
    "COBOUNDARY_SCORE_SCHEMA",
    "CandidateArtifactV1",
    "CandidateProposal",
    "ClaimKind",
    "CoboundaryScoreResult",
    "CorpusFileRef",
    "EVALUATION_SCHEMA",
    "EvaluationReceiptV1",
    "EvidenceCeiling",
    "GateReceiptV1",
    "LAB_TERMINAL_STATUSES",
    "ObstructionLedger",
    "ObstructionLedgerEvent",
    "PACKET_SCHEMA",
    "PacketEnvelopeV2",
    "ProcessEvent",
    "ProcessEventLog",
    "REFUSAL_AUTHORITY",
    "REFUSAL_EXACT_WITHOUT_DUAL",
    "REFUSAL_EXACT_WITHOUT_DUAL_WITNESS",
    "REFUSAL_ILLEGAL_PROPOSAL",
    "REFUSAL_NEGATIVE_MAGNITUDE",
    "ResearchClaim",
    "ResearchMode",
    "ResearchProposal",
    "ResearchSeedPacket",
    "ResearchStepPacket",
    "ResidualDropV1",
    "StepRealization",
    "SymbolGameResearchPacket",
    "digest_payload",
    "verify_event_chain",
]


_PFP_EXPORTS = {'Entity': ('pfp.domain.entities.base', 'Entity'), 'CandidateEntity': ('pfp.domain.entities.cycle_balance', 'CandidateEntity'), 'ProblemEntity': ('pfp.domain.entities.cycle_balance', 'ProblemEntity'), 'ReceiptEntity': ('pfp.domain.entities.cycle_balance', 'ReceiptEntity'), 'VerifierEntity': ('pfp.domain.entities.cycle_balance', 'VerifierEntity')}
__all__ = list(dict.fromkeys([*__all__, *_PFP_EXPORTS]))

def __getattr__(name: str):
    from importlib import import_module
    if name not in _PFP_EXPORTS:
        raise AttributeError(name)
    module, attribute = _PFP_EXPORTS[name]
    value = getattr(import_module(module), attribute)
    globals()[name] = value
    return value
