"""PFP Fixtures and Long-Horizon Task Packet Envelopes.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from .base import AuthorityEffect, PfpBaseModel


class PfpAllowedTransform(str, Enum):
    EDIT_SCOPED_PATHS = "edit_scoped_paths"
    EMIT_CONTENT_ADDRESSED_ARTIFACT = "emit_content_addressed_artifact"
    EMIT_DDA_RECEIPT = "emit_dda_receipt"
    RENDER_PROSE_FROM_ROOT = "render_prose_from_root"
    TEST = "test"


class PfpFramingMode(str, Enum):
    STRICT = "strict"
    PERMISSIVE = "permissive"


class PfpEvidenceCeiling(str, Enum):
    REPLAYABLE_LAB_EVIDENCE = "ReplayableLabEvidence"
    MACHINE_CHECKED_PROOF = "MachineCheckedProof"
    THEORETICAL_CONJECTURE = "TheoreticalConjecture"


class PfpOraclePolicy(str, Enum):
    INDEPENDENT_GATE_RECEIPTS_REQUIRED = "IndependentGateReceiptsRequired"
    INDEPENDENT_GATE_RECEIPTS_AND_EXTERNAL_PROMOTION_REQUIRED = "IndependentGateReceiptsAndExternalPromotionRequired"


class PfpPacketKind(str, Enum):
    PROBLEM = "problem"
    CANDIDATE = "candidate"
    EVALUATION = "evaluation"
    RECEIPT = "receipt"


class PfpNextWorkItem(PfpBaseModel):
    order: int
    target: str
    work_id: str


class PfpFableLongHorizonTaskPacket(PfpBaseModel):
    schema_version: str = Field(default="core.symbol-game.packet-envelope.v2")
    task_id: str
    packet_id: str
    packet_family: str
    packet_kind: PfpPacketKind
    parent_event_id: str | None = None
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    evidence_ceiling: PfpEvidenceCeiling
    oracle_policy: PfpOraclePolicy
    framing_mode: PfpFramingMode
    carrier_id: str
    initial_state_hash: str
    source_digest: str
    step_budget: int = Field(ge=1)
    terminal_target: str
    allowed_transforms: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    protected_boundaries: list[str] = Field(default_factory=list)
    payload: list[Any] = Field(default_factory=list)


# Aliases
AllowedTransform = PfpAllowedTransform
FramingMode = PfpFramingMode
EvidenceCeiling = PfpEvidenceCeiling
OraclePolicy = PfpOraclePolicy
PacketKind = PfpPacketKind
NextWorkItem = PfpNextWorkItem
FableLongHorizonTaskPacket = PfpFableLongHorizonTaskPacket
