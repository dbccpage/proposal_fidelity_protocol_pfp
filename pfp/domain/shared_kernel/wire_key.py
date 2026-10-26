"""Shared Kernel: Typed wire dictionary keys eliminating raw magic strings across the bounded contexts.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum


class WireKey(str, Enum):
    """Wire dictionary keys for all Symbol Game packet, artifact, and receipt types."""

    SCHEMA_VERSION = "schema_version"
    PROMPT_ARTIFACT_ID = "prompt_artifact_id"
    REGIME_KIND = "regime_kind"
    REGIME_SHA256 = "regime_sha256"
    PROMPT_BODY_SHA256 = "prompt_body_sha256"
    ADMITTED_CONSTRUCTORS = "admitted_constructors"
    OPEN_OBSTRUCTIONS = "open_obstructions"
    DEMAND_SET = "demand_set"
    KILL_CONDITIONS = "kill_conditions"
    REQUIRED_REPLY_FIELDS = "required_reply_fields"
    OBJECTIVE = "objective"
    RESIDUAL_COLOUR = "residual_colour"
    DUAL_WITNESS_REQUIRED = "dual_witness_required"
    DUAL_WITNESS_REF = "dual_witness_ref"
    PARENT_PACKET_ID = "parent_packet_id"
    CONVERSATION_ROOT_ID = "conversation_root_id"
    AUTHORITY_EFFECT = "authority_effect"
    TASK_ID = "task_id"
    ROLE = "role"
    TURN_KIND = "turn_kind"
    CANDIDATE_BUDGET = "candidate_budget"
    OPERATION_BUDGET = "operation_budget"
    CARRIER_ID = "carrier_id"
    OWNED_PATHS = "owned_paths"
    PROTECTED_PATHS = "protected_paths"
    BASE_REVISION = "base_revision"
    PATH_MANIFEST_ROOT = "path_manifest_root"
    STATUS = "status"
    STEP_CLAIMS = "step_claims"
    OBSTRUCTION_RECEIPTS = "obstruction_receipts"
    GATE_RECEIPTS = "gate_receipts"
    DISPOSITION = "disposition"
    SCORE = "score"
    PAYLOAD = "payload"
    PAYLOAD_SCHEMA = "payload_schema"
    PACKET_ID = "packet_id"
    FAMILY = "family"
    PRODUCER_ID = "producer_id"
    CONTENT_ARTIFACT_ID = "content_artifact_id"
    CONTENT_SHA256 = "content_sha256"
    CONTENT_BYTES_LEN = "content_bytes_len"
