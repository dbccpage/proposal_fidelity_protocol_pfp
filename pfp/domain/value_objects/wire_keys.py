"""Domain Value Objects for canonical wire dictionary keys and schema field contracts.

Defines strongly-typed WireKey enums and field constants for the Symbol Game bounded context.
AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum

from pfp.domain.shared_kernel import RegimeKind, ResidualColour


class PromptArtifactWireKey(str, Enum):
    """Canonical wire dictionary keys for PromptArtifactV1."""

    PROMPT_ARTIFACT_ID = "prompt_artifact_id"
    SCHEMA_VERSION = "schema_version"
    FAMILY = "family"
    REGIME_ID = "regime_id"
    REGIME_KIND = "regime_kind"
    ADMITTED_CONSTRUCTORS = "admitted_constructors"
    OPEN_OBSTRUCTIONS = "open_obstructions"
    DEMAND_SET = "demand_set"
    KILL_CONDITIONS = "kill_conditions"
    REQUIRED_REPLY_FIELDS = "required_reply_fields"
    OBJECTIVE_TYPED = "objective_typed"
    RESIDUAL_COLOUR = "residual_colour"
    DUAL_WITNESS_REQUIRED = "dual_witness_required"
    DUAL_WITNESS_REF = "dual_witness_ref"
    PROMPT_BODY_SHA256 = "prompt_body_sha256"
    PROMPT_BODY_BYTE_COUNT = "prompt_body_byte_count"
    PARENT_PACKET_ID = "parent_packet_id"
    CONVERSATION_ROOT_ID = "conversation_root_id"
    AUTHORITY_EFFECT = "authority_effect"


class EliminationReceiptWireKey(str, Enum):
    """Canonical wire dictionary keys for EliminationReceiptV1."""

    ELIMINATION_RECEIPT_ID = "elimination_receipt_id"
    SCHEMA_VERSION = "schema_version"
    FAMILY = "family"
    PACKET_ID = "packet_id"
    ELIMINATED_OBSTRUCTION_IDS = "eliminated_obstruction_ids"
    PRIOR_RESIDUAL_COLOUR = "prior_residual_colour"
    NEW_RESIDUAL_COLOUR = "new_residual_colour"
    EVIDENCE_ROOT = "evidence_root"
    DUAL_WITNESS_REF = "dual_witness_ref"
    AUTHORITY_EFFECT = "authority_effect"


class ObstructionHintWireKey(str, Enum):
    """Canonical wire dictionary keys for ObstructionHintV1."""

    OBSTRUCTION_ID = "obstruction_id"
    FAMILY = "family"
    RESIDUAL_COLOUR = "residual_colour"
    MAGNITUDE = "magnitude"
    DEMAND_ID = "demand_id"
    PRIOR_REPORT_DIGESTS = "prior_report_digests"


class DemandItemWireKey(str, Enum):
    """Canonical wire dictionary keys for DemandItemV1."""

    DEMAND_ID = "demand_id"
    KIND = "kind"
    NOTE = "note"


class ObjectiveTypedWireKey(str, Enum):
    """Canonical wire dictionary keys for ObjectiveTypedV1."""

    KIND = "kind"
    SUMMARY = "summary"
    TARGET_OBSTRUCTION_IDS = "target_obstruction_ids"
    TARGET_DEMAND_IDS = "target_demand_ids"


class CodeChangeWireKey(str, Enum):
    """Canonical wire dictionary keys for CodeChangeRunRootV1."""

    RUN_ROOT_ID = "run_root_id"
    SCHEMA_VERSION = "schema_version"
    FAMILY = "family"
    CARRIER_ID = "carrier_id"
    OWNED_PATHS = "owned_paths"
    PROTECTED_PATHS = "protected_paths"
    BASE_REVISION = "base_revision"
    PATH_MANIFEST_ROOT = "path_manifest_root"
    PROPOSALS = "proposals"
    AUTHORITY_EFFECT = "authority_effect"


class ResearchClaimWireKey(str, Enum):
    """Canonical wire dictionary keys for ResearchClaimEnvelopeV1."""

    PACKET_ID = "packet_id"
    SCHEMA_VERSION = "schema_version"
    FAMILY = "family"
    PRODUCER_ID = "producer_id"
    SOURCE_ROOT = "source_root"
    SOURCE_INTAKE_BUNDLE = "source_intake_bundle"
    INITIAL_STATE = "initial_state"
    DISPOSITION = "disposition"
    OBLIGATIONS = "obligations"
    AUTHORITY_EFFECT = "authority_effect"


PROMPT_ARTIFACT_WIRE_FIELDS: frozenset[str] = frozenset(k.value for k in PromptArtifactWireKey)
ELIMINATION_RECEIPT_WIRE_FIELDS: frozenset[str] = frozenset(k.value for k in EliminationReceiptWireKey)
OBSTRUCTION_HINT_WIRE_FIELDS: frozenset[str] = frozenset(k.value for k in ObstructionHintWireKey)
DEMAND_ITEM_WIRE_FIELDS: frozenset[str] = frozenset(k.value for k in DemandItemWireKey)
OBJECTIVE_TYPED_WIRE_FIELDS: frozenset[str] = frozenset(k.value for k in ObjectiveTypedWireKey)
CODE_CHANGE_WIRE_FIELDS: frozenset[str] = frozenset(k.value for k in CodeChangeWireKey)
RESEARCH_CLAIM_WIRE_FIELDS: frozenset[str] = frozenset(k.value for k in ResearchClaimWireKey)

RESIDUAL_COLOURS: frozenset[str] = frozenset({"Open", "Closed", "Exact"})
REGIME_KINDS: frozenset[str] = frozenset(k.value for k in RegimeKind) | frozenset(
    {"prose-regime", "code-diff-regime", "lean4-proof-regime", "hybrid-regime"}
)

__all__ = [
    "CODE_CHANGE_WIRE_FIELDS",
    "CodeChangeWireKey",
    "DEMAND_ITEM_WIRE_FIELDS",
    "DemandItemWireKey",
    "ELIMINATION_RECEIPT_WIRE_FIELDS",
    "EliminationReceiptWireKey",
    "OBJECTIVE_TYPED_WIRE_FIELDS",
    "OBSTRUCTION_HINT_WIRE_FIELDS",
    "ObjectiveTypedWireKey",
    "ObstructionHintWireKey",
    "PROMPT_ARTIFACT_WIRE_FIELDS",
    "PromptArtifactWireKey",
    "REGIME_KINDS",
    "RESEARCH_CLAIM_WIRE_FIELDS",
    "RESIDUAL_COLOURS",
    "ResearchClaimWireKey",
]
