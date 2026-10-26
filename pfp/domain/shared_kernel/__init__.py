"""Shared Kernel package for common domain primitives across crates."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .canonical import CanonicalizationError, canonical_bytes, canonical_json, canonical_unwire, canonical_wire, domain_digest, freeze, thaw
    from .exact import REFUSAL_FLOAT_REFUSED, REFUSAL_NOT_EXACT, Exact, NotExactError, coerce_exact, is_exact_value, parse_exact, to_canonical_string
    from .result import Failure, Result, ResultError, Success
    from .authority_effect import AuthorityEffect, validate_authority_effect_none
    from .budget import MAX_CANDIDATE_BUDGET, MAX_EXECUTION_BUDGET, MAX_OPERATION_BUDGET, Budget, CandidateBudget, ExecutionBudget, OperationBudget, StepBudget, TimeBudget
    from .byte_payload import MAX_PAYLOAD_BYTES, MAX_STRING_LENGTH, BytePayload
    from .bytes import ByteCount
    from .coboundary_score import CandidateProposal, CoboundaryScoreResult
    from .code import Code, RefusalCode
    from .content_digest import ContentDigest
    from .data import DataRecord
    from .demand_item import DemandItemV1
    from .description import MAX_DESCRIPTION_LENGTH, Description
    from .disposition import Disposition, DispositionState
    from .field import FieldName
    from .gate import GateId
    from .hash import ContentHash, Hash, Sha256Hash
    from .id import DEFAULT_ID_REGEX, CandidateId, CarrierId, ClaimId, ContentArtifactId, CorpusId, DemandId, HypothesisId, Identifier, IntakeBundleId, ObstructionId, PacketId, PatchArtifactId, PolicyId, ProducerId, PromptArtifactId, ReceiptId, RunRootId, SampleId, TaskId, EventId
    from .key import ContextKey, Key, WireKey as WireKeyVO
    from .key_type import CommonWireKeyKind, KeyType, KeyTypeKind
    from .kill_condition import KILL_CONDITION_MAP, REGISTERED_KILL_CONDITIONS, KillConditionInfo
    from .kind import Kind, Role, RoleKind
    from .llm_payload import LLM_TURN_FAMILY, LLM_TURN_SCHEMA, LlmPayloadV1, LlmTurnPayloadV1
    from .media_type import MediaType
    from .objective_typed import ObjectiveTypedV1
    from .obstruction import ObstructionFamily, ObstructionFamilyKind, ObstructionHintV1
    from .patch import MAX_PATCH_BYTES, PatchText
    from .path import OwnedPath, ProtectedPath, RelativePath, validate_path_security
    from .path_manifest import PathManifest
    from .regime import REGIME_KINDS, Regime, RegimeKind
    from .required_reply_fields import DEFAULT_REQUIRED_FIELDS, RequiredReplyFields
    from .residual_colour import RESIDUAL_COLOURS, ResidualColour
    from .residual_drop import ResidualDrop, ResidualDropV1
    from .revision import Revision
    from .schema import SchemaVersion
    from .severity import Severity, SeverityKind
    from .summary import MAX_SUMMARY_LENGTH, Summary
    from .task_objective import MAX_OBJECTIVE_LENGTH, TaskObjective
    from .turn import TurnKind, TurnModality, TurnRole
    from .turn_type import TurnType, TurnTypeKind
    from .wire_key import WireKey

__all__ = ['AuthorityEffect', 'Budget', 'ByteCount', 'BytePayload', 'CandidateBudget', 'CandidateId', 'CandidateProposal', 'CanonicalizationError', 'CarrierId', 'ClaimId', 'CoboundaryScoreResult', 'Code', 'CommonWireKeyKind', 'ContentArtifactId', 'ContentDigest', 'ContentHash', 'ContextKey', 'CorpusId', 'DEFAULT_ID_REGEX', 'DEFAULT_REQUIRED_FIELDS', 'DataRecord', 'DemandId', 'DemandItemV1', 'Description', 'Disposition', 'DispositionState', 'EventId', 'Exact', 'ExecutionBudget', 'Failure', 'FieldName', 'GateId', 'Hash', 'HypothesisId', 'Identifier', 'IntakeBundleId', 'KILL_CONDITION_MAP', 'Key', 'KeyType', 'KeyTypeKind', 'KillConditionInfo', 'Kind', 'LLM_TURN_FAMILY', 'LLM_TURN_SCHEMA', 'LlmPayloadV1', 'LlmTurnPayloadV1', 'MAX_CANDIDATE_BUDGET', 'MAX_DESCRIPTION_LENGTH', 'MAX_EXECUTION_BUDGET', 'MAX_OBJECTIVE_LENGTH', 'MAX_OPERATION_BUDGET', 'MAX_PATCH_BYTES', 'MAX_PAYLOAD_BYTES', 'MAX_STRING_LENGTH', 'MAX_SUMMARY_LENGTH', 'MediaType', 'NotExactError', 'ObjectiveTypedV1', 'ObstructionFamily', 'ObstructionFamilyKind', 'ObstructionHintV1', 'ObstructionId', 'OperationBudget', 'OwnedPath', 'PacketId', 'PatchArtifactId', 'PatchText', 'PathManifest', 'PolicyId', 'ProducerId', 'PromptArtifactId', 'ProtectedPath', 'REFUSAL_FLOAT_REFUSED', 'REFUSAL_NOT_EXACT', 'REGIME_KINDS', 'REGISTERED_KILL_CONDITIONS', 'RESIDUAL_COLOURS', 'ReceiptId', 'RefusalCode', 'Regime', 'RegimeKind', 'RelativePath', 'RequiredReplyFields', 'ResidualColour', 'ResidualDrop', 'ResidualDropV1', 'Result', 'ResultError', 'Revision', 'Role', 'RoleKind', 'RunRootId', 'SampleId', 'SchemaVersion', 'Severity', 'SeverityKind', 'Sha256Hash', 'StepBudget', 'Success', 'Summary', 'TaskId', 'TaskObjective', 'TimeBudget', 'TurnKind', 'TurnModality', 'TurnRole', 'TurnType', 'TurnTypeKind', 'WireKey', 'WireKeyVO', 'canonical_bytes', 'canonical_json', 'canonical_unwire', 'canonical_wire', 'coerce_exact', 'domain_digest', 'freeze', 'is_exact_value', 'parse_exact', 'thaw', 'to_canonical_string', 'validate_authority_effect_none', 'validate_path_security']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'CanonicalizationError': ('.canonical', 'CanonicalizationError'),
    'canonical_bytes': ('.canonical', 'canonical_bytes'),
    'canonical_json': ('.canonical', 'canonical_json'),
    'canonical_unwire': ('.canonical', 'canonical_unwire'),
    'canonical_wire': ('.canonical', 'canonical_wire'),
    'domain_digest': ('.canonical', 'domain_digest'),
    'freeze': ('.canonical', 'freeze'),
    'thaw': ('.canonical', 'thaw'),
    'REFUSAL_FLOAT_REFUSED': ('.exact', 'REFUSAL_FLOAT_REFUSED'),
    'REFUSAL_NOT_EXACT': ('.exact', 'REFUSAL_NOT_EXACT'),
    'Exact': ('.exact', 'Exact'),
    'NotExactError': ('.exact', 'NotExactError'),
    'coerce_exact': ('.exact', 'coerce_exact'),
    'is_exact_value': ('.exact', 'is_exact_value'),
    'parse_exact': ('.exact', 'parse_exact'),
    'to_canonical_string': ('.exact', 'to_canonical_string'),
    'Failure': ('.result', 'Failure'),
    'Result': ('.result', 'Result'),
    'ResultError': ('.result', 'ResultError'),
    'Success': ('.result', 'Success'),
    'AuthorityEffect': ('.authority_effect', 'AuthorityEffect'),
    'validate_authority_effect_none': ('.authority_effect', 'validate_authority_effect_none'),
    'MAX_CANDIDATE_BUDGET': ('.budget', 'MAX_CANDIDATE_BUDGET'),
    'MAX_EXECUTION_BUDGET': ('.budget', 'MAX_EXECUTION_BUDGET'),
    'MAX_OPERATION_BUDGET': ('.budget', 'MAX_OPERATION_BUDGET'),
    'Budget': ('.budget', 'Budget'),
    'CandidateBudget': ('.budget', 'CandidateBudget'),
    'ExecutionBudget': ('.budget', 'ExecutionBudget'),
    'OperationBudget': ('.budget', 'OperationBudget'),
    'StepBudget': ('.budget', 'StepBudget'),
    'TimeBudget': ('.budget', 'TimeBudget'),
    'MAX_PAYLOAD_BYTES': ('.byte_payload', 'MAX_PAYLOAD_BYTES'),
    'MAX_STRING_LENGTH': ('.byte_payload', 'MAX_STRING_LENGTH'),
    'BytePayload': ('.byte_payload', 'BytePayload'),
    'ByteCount': ('.bytes', 'ByteCount'),
    'CandidateProposal': ('.coboundary_score', 'CandidateProposal'),
    'CoboundaryScoreResult': ('.coboundary_score', 'CoboundaryScoreResult'),
    'Code': ('.code', 'Code'),
    'RefusalCode': ('.code', 'RefusalCode'),
    'ContentDigest': ('.content_digest', 'ContentDigest'),
    'DataRecord': ('.data', 'DataRecord'),
    'DemandItemV1': ('.demand_item', 'DemandItemV1'),
    'MAX_DESCRIPTION_LENGTH': ('.description', 'MAX_DESCRIPTION_LENGTH'),
    'Description': ('.description', 'Description'),
    'Disposition': ('.disposition', 'Disposition'),
    'DispositionState': ('.disposition', 'DispositionState'),
    'FieldName': ('.field', 'FieldName'),
    'GateId': ('.gate', 'GateId'),
    'ContentHash': ('.hash', 'ContentHash'),
    'Hash': ('.hash', 'Hash'),
    'Sha256Hash': ('.hash', 'Sha256Hash'),
    'DEFAULT_ID_REGEX': ('.id', 'DEFAULT_ID_REGEX'),
    'CandidateId': ('.id', 'CandidateId'),
    'CarrierId': ('.id', 'CarrierId'),
    'ClaimId': ('.id', 'ClaimId'),
    'ContentArtifactId': ('.id', 'ContentArtifactId'),
    'CorpusId': ('.id', 'CorpusId'),
    'DemandId': ('.id', 'DemandId'),
    'HypothesisId': ('.id', 'HypothesisId'),
    'Identifier': ('.id', 'Identifier'),
    'IntakeBundleId': ('.id', 'IntakeBundleId'),
    'ObstructionId': ('.id', 'ObstructionId'),
    'PacketId': ('.id', 'PacketId'),
    'PatchArtifactId': ('.id', 'PatchArtifactId'),
    'PolicyId': ('.id', 'PolicyId'),
    'ProducerId': ('.id', 'ProducerId'),
    'PromptArtifactId': ('.id', 'PromptArtifactId'),
    'ReceiptId': ('.id', 'ReceiptId'),
    'RunRootId': ('.id', 'RunRootId'),
    'SampleId': ('.id', 'SampleId'),
    'TaskId': ('.id', 'TaskId'),
    'EventId': ('.id', 'EventId'),
    'ContextKey': ('.key', 'ContextKey'),
    'Key': ('.key', 'Key'),
    'WireKeyVO': ('.key', 'WireKey'),
    'CommonWireKeyKind': ('.key_type', 'CommonWireKeyKind'),
    'KeyType': ('.key_type', 'KeyType'),
    'KeyTypeKind': ('.key_type', 'KeyTypeKind'),
    'KILL_CONDITION_MAP': ('.kill_condition', 'KILL_CONDITION_MAP'),
    'REGISTERED_KILL_CONDITIONS': ('.kill_condition', 'REGISTERED_KILL_CONDITIONS'),
    'KillConditionInfo': ('.kill_condition', 'KillConditionInfo'),
    'Kind': ('.kind', 'Kind'),
    'Role': ('.kind', 'Role'),
    'RoleKind': ('.kind', 'RoleKind'),
    'LLM_TURN_FAMILY': ('.llm_payload', 'LLM_TURN_FAMILY'),
    'LLM_TURN_SCHEMA': ('.llm_payload', 'LLM_TURN_SCHEMA'),
    'LlmPayloadV1': ('.llm_payload', 'LlmPayloadV1'),
    'LlmTurnPayloadV1': ('.llm_payload', 'LlmTurnPayloadV1'),
    'MediaType': ('.media_type', 'MediaType'),
    'ObjectiveTypedV1': ('.objective_typed', 'ObjectiveTypedV1'),
    'ObstructionFamily': ('.obstruction', 'ObstructionFamily'),
    'ObstructionFamilyKind': ('.obstruction', 'ObstructionFamilyKind'),
    'ObstructionHintV1': ('.obstruction', 'ObstructionHintV1'),
    'MAX_PATCH_BYTES': ('.patch', 'MAX_PATCH_BYTES'),
    'PatchText': ('.patch', 'PatchText'),
    'OwnedPath': ('.path', 'OwnedPath'),
    'ProtectedPath': ('.path', 'ProtectedPath'),
    'RelativePath': ('.path', 'RelativePath'),
    'validate_path_security': ('.path', 'validate_path_security'),
    'PathManifest': ('.path_manifest', 'PathManifest'),
    'REGIME_KINDS': ('.regime', 'REGIME_KINDS'),
    'Regime': ('.regime', 'Regime'),
    'RegimeKind': ('.regime', 'RegimeKind'),
    'DEFAULT_REQUIRED_FIELDS': ('.required_reply_fields', 'DEFAULT_REQUIRED_FIELDS'),
    'RequiredReplyFields': ('.required_reply_fields', 'RequiredReplyFields'),
    'RESIDUAL_COLOURS': ('.residual_colour', 'RESIDUAL_COLOURS'),
    'ResidualColour': ('.residual_colour', 'ResidualColour'),
    'ResidualDrop': ('.residual_drop', 'ResidualDrop'),
    'ResidualDropV1': ('.residual_drop', 'ResidualDropV1'),
    'Revision': ('.revision', 'Revision'),
    'SchemaVersion': ('.schema', 'SchemaVersion'),
    'Severity': ('.severity', 'Severity'),
    'SeverityKind': ('.severity', 'SeverityKind'),
    'MAX_SUMMARY_LENGTH': ('.summary', 'MAX_SUMMARY_LENGTH'),
    'Summary': ('.summary', 'Summary'),
    'MAX_OBJECTIVE_LENGTH': ('.task_objective', 'MAX_OBJECTIVE_LENGTH'),
    'TaskObjective': ('.task_objective', 'TaskObjective'),
    'TurnKind': ('.turn', 'TurnKind'),
    'TurnModality': ('.turn', 'TurnModality'),
    'TurnRole': ('.turn', 'TurnRole'),
    'TurnType': ('.turn_type', 'TurnType'),
    'TurnTypeKind': ('.turn_type', 'TurnTypeKind'),
    'WireKey': ('.wire_key', 'WireKey'),
}


def __getattr__(name: str) -> Any:
    target = _LAZY_IMPORTS.get(name)
    if target is not None:
        mod_name, attr_name = target
        mod = importlib.import_module(mod_name, __name__)
        val = getattr(mod, attr_name)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
