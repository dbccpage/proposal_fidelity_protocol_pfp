"""Domain Value Objects package for the Symbol Game bounded context.

Pure, immutable value objects with invariant validation, zero naked primitives,
and strict size and authority ceilings re-exported from shared_kernel and wire_keys.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    LlmPayloadV1 = LlmTurnPayloadV1
    from pfp.domain.shared_kernel import DEFAULT_REQUIRED_FIELDS, KILL_CONDITION_MAP, LLM_TURN_FAMILY, LLM_TURN_SCHEMA, MAX_CANDIDATE_BUDGET, MAX_OBJECTIVE_LENGTH, MAX_OPERATION_BUDGET, MAX_PAYLOAD_BYTES, MAX_STRING_LENGTH, REGISTERED_KILL_CONDITIONS, AuthorityEffect, Budget, BytePayload, CandidateBudget, CandidateId, CandidateProposal, CarrierId, CoboundaryScoreResult, ContentDigest, DemandId, DemandItemV1, Disposition, DispositionState, ExecutionBudget, FieldName, KillConditionInfo, LlmTurnPayloadV1, ObstructionFamily, ObstructionFamilyKind, ObstructionHintV1, ObstructionId, OperationBudget, OwnedPath, PathManifest, ProducerId, PromptArtifactId, ProtectedPath, ReceiptId, Regime, RegimeKind, RequiredReplyFields, ResidualColour, ResidualDropV1, Role, RoleKind, RunRootId, StepBudget, TaskId, TaskObjective, TimeBudget, TurnKind, TurnModality, TurnRole, TurnType, TurnTypeKind, WireKey
    from .wire_keys import CODE_CHANGE_WIRE_FIELDS, CodeChangeWireKey, DEMAND_ITEM_WIRE_FIELDS, DemandItemWireKey, ELIMINATION_RECEIPT_WIRE_FIELDS, EliminationReceiptWireKey, OBJECTIVE_TYPED_WIRE_FIELDS, OBSTRUCTION_HINT_WIRE_FIELDS, ObjectiveTypedWireKey, ObstructionHintWireKey, PROMPT_ARTIFACT_WIRE_FIELDS, PromptArtifactWireKey, REGIME_KINDS, RESEARCH_CLAIM_WIRE_FIELDS, RESIDUAL_COLOURS, ResearchClaimWireKey
    from pfp.domain.aggregates.prompt_artifact import ObjectiveTypedV1
    from pfp.domain.value_objects.base import ValueObject
    from pfp.domain.value_objects.identifiers import CANONICAL_CHECKERS
    from pfp.domain.value_objects.identifiers import CaseId
    from pfp.domain.value_objects.identifiers import CheckerIdVO
    from pfp.domain.value_objects.identifiers import NormalFormId
    from pfp.domain.value_objects.identifiers import PilotId
    from pfp.domain.value_objects.identifiers import ProblemId
    from pfp.domain.value_objects.identifiers import PromptId
    from pfp.domain.value_objects.identifiers import RequestId
    from pfp.domain.value_objects.identifiers import Sha256Digest
    from pfp.domain.value_objects.identifiers import VerifierId
    from pfp.domain.value_objects.numerics import BoundedTemperature
    from pfp.domain.value_objects.numerics import DifficultyRung
    from pfp.domain.value_objects.numerics import MicroUsdSpend
    from pfp.domain.value_objects.numerics import StageNumber
    from pfp.domain.value_objects.numerics import StratumLevel
    from pfp.domain.value_objects.taxonomy import VALID_ARITHMETIC_DOMAINS
    from pfp.domain.value_objects.taxonomy import VALID_CLAIMED_MOVES
    from pfp.domain.value_objects.taxonomy import VALID_EVALUATION_STATUSES
    from pfp.domain.value_objects.taxonomy import VALID_EXECUTION_MODES
    from pfp.domain.value_objects.taxonomy import VALID_SPAN_ROLES
    from pfp.domain.value_objects.taxonomy import VALID_TASK_FAMILIES
    from pfp.domain.value_objects.taxonomy import VALID_TRIAL_STATUSES
    from pfp.domain.value_objects.taxonomy import VALID_VERIFICATION_RULES
    from pfp.domain.value_objects.taxonomy import VALID_VERIFICATION_STATUSES
    from pfp.domain.value_objects.taxonomy import ArithmeticDomainVO
    from pfp.domain.value_objects.taxonomy import ClaimedMoveVO
    from pfp.domain.value_objects.taxonomy import EvaluationStatusVO
    from pfp.domain.value_objects.taxonomy import ExecutionModeVO
    from pfp.domain.value_objects.taxonomy import SpanRoleVO
    from pfp.domain.value_objects.taxonomy import TaskFamilyVO
    from pfp.domain.value_objects.taxonomy import TrialStatusVO
    from pfp.domain.value_objects.taxonomy import VerificationRuleVO
    from pfp.domain.value_objects.taxonomy import VerificationStatusVO
    from pfp.domain.value_objects.topology import ByteSpanVO
    from pfp.domain.value_objects.topology import EdgeVO
    from pfp.domain.value_objects.topology import MatrixShape
    from pfp.domain.value_objects.topology import VertexId
    from pfp.domain.value_objects.cycle_balance import ActiveObstructionVO
    from pfp.domain.value_objects.cycle_balance import BoundaryMatricesVO
    from pfp.domain.value_objects.cycle_balance import CarrierEdgeVO
    from pfp.domain.value_objects.cycle_balance import CarrierFaceVO
    from pfp.domain.value_objects.cycle_balance import CarrierVO
    from pfp.domain.value_objects.cycle_balance import ClaimHygieneVO
    from pfp.domain.value_objects.cycle_balance import StaticCellBoundsVO


__all__ = [
    "LlmPayloadV1",
    "DEFAULT_REQUIRED_FIELDS",
    "KILL_CONDITION_MAP",
    "LLM_TURN_FAMILY",
    "LLM_TURN_SCHEMA",
    "MAX_CANDIDATE_BUDGET",
    "MAX_OBJECTIVE_LENGTH",
    "MAX_OPERATION_BUDGET",
    "MAX_PAYLOAD_BYTES",
    "MAX_STRING_LENGTH",
    "REGISTERED_KILL_CONDITIONS",
    "AuthorityEffect",
    "Budget",
    "BytePayload",
    "CandidateBudget",
    "CandidateId",
    "CandidateProposal",
    "CarrierId",
    "CoboundaryScoreResult",
    "ContentDigest",
    "DemandId",
    "DemandItemV1",
    "Disposition",
    "DispositionState",
    "ExecutionBudget",
    "FieldName",
    "KillConditionInfo",
    "LlmTurnPayloadV1",
    "ObstructionFamily",
    "ObstructionFamilyKind",
    "ObstructionHintV1",
    "ObstructionId",
    "OperationBudget",
    "OwnedPath",
    "PathManifest",
    "ProducerId",
    "PromptArtifactId",
    "ProtectedPath",
    "ReceiptId",
    "Regime",
    "RegimeKind",
    "RequiredReplyFields",
    "ResidualColour",
    "ResidualDropV1",
    "Role",
    "RoleKind",
    "RunRootId",
    "StepBudget",
    "TaskId",
    "TaskObjective",
    "TimeBudget",
    "TurnKind",
    "TurnModality",
    "TurnRole",
    "TurnType",
    "TurnTypeKind",
    "WireKey",
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
    "ObjectiveTypedV1",
    "ValueObject",
    "CANONICAL_CHECKERS",
    "CaseId",
    "CheckerIdVO",
    "NormalFormId",
    "PilotId",
    "ProblemId",
    "PromptId",
    "RequestId",
    "Sha256Digest",
    "VerifierId",
    "BoundedTemperature",
    "DifficultyRung",
    "MicroUsdSpend",
    "StageNumber",
    "StratumLevel",
    "VALID_ARITHMETIC_DOMAINS",
    "VALID_CLAIMED_MOVES",
    "VALID_EVALUATION_STATUSES",
    "VALID_EXECUTION_MODES",
    "VALID_SPAN_ROLES",
    "VALID_TASK_FAMILIES",
    "VALID_TRIAL_STATUSES",
    "VALID_VERIFICATION_RULES",
    "VALID_VERIFICATION_STATUSES",
    "ArithmeticDomainVO",
    "ClaimedMoveVO",
    "EvaluationStatusVO",
    "ExecutionModeVO",
    "SpanRoleVO",
    "TaskFamilyVO",
    "TrialStatusVO",
    "VerificationRuleVO",
    "VerificationStatusVO",
    "ByteSpanVO",
    "EdgeVO",
    "MatrixShape",
    "VertexId",
    "ActiveObstructionVO",
    "BoundaryMatricesVO",
    "CarrierEdgeVO",
    "CarrierFaceVO",
    "CarrierVO",
    "ClaimHygieneVO",
    "StaticCellBoundsVO",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'LlmPayloadV1': ('pfp.domain.shared_kernel', 'LlmTurnPayloadV1'),
    'DEFAULT_REQUIRED_FIELDS': ('pfp.domain.shared_kernel', 'DEFAULT_REQUIRED_FIELDS'),
    'KILL_CONDITION_MAP': ('pfp.domain.shared_kernel', 'KILL_CONDITION_MAP'),
    'LLM_TURN_FAMILY': ('pfp.domain.shared_kernel', 'LLM_TURN_FAMILY'),
    'LLM_TURN_SCHEMA': ('pfp.domain.shared_kernel', 'LLM_TURN_SCHEMA'),
    'MAX_CANDIDATE_BUDGET': ('pfp.domain.shared_kernel', 'MAX_CANDIDATE_BUDGET'),
    'MAX_OBJECTIVE_LENGTH': ('pfp.domain.shared_kernel', 'MAX_OBJECTIVE_LENGTH'),
    'MAX_OPERATION_BUDGET': ('pfp.domain.shared_kernel', 'MAX_OPERATION_BUDGET'),
    'MAX_PAYLOAD_BYTES': ('pfp.domain.shared_kernel', 'MAX_PAYLOAD_BYTES'),
    'MAX_STRING_LENGTH': ('pfp.domain.shared_kernel', 'MAX_STRING_LENGTH'),
    'REGISTERED_KILL_CONDITIONS': ('pfp.domain.shared_kernel', 'REGISTERED_KILL_CONDITIONS'),
    'AuthorityEffect': ('pfp.domain.shared_kernel', 'AuthorityEffect'),
    'Budget': ('pfp.domain.shared_kernel', 'Budget'),
    'BytePayload': ('pfp.domain.shared_kernel', 'BytePayload'),
    'CandidateBudget': ('pfp.domain.shared_kernel', 'CandidateBudget'),
    'CandidateId': ('pfp.domain.shared_kernel', 'CandidateId'),
    'CandidateProposal': ('pfp.domain.shared_kernel', 'CandidateProposal'),
    'CarrierId': ('pfp.domain.shared_kernel', 'CarrierId'),
    'CoboundaryScoreResult': ('pfp.domain.shared_kernel', 'CoboundaryScoreResult'),
    'ContentDigest': ('pfp.domain.shared_kernel', 'ContentDigest'),
    'DemandId': ('pfp.domain.shared_kernel', 'DemandId'),
    'DemandItemV1': ('pfp.domain.shared_kernel', 'DemandItemV1'),
    'Disposition': ('pfp.domain.shared_kernel', 'Disposition'),
    'DispositionState': ('pfp.domain.shared_kernel', 'DispositionState'),
    'ExecutionBudget': ('pfp.domain.shared_kernel', 'ExecutionBudget'),
    'FieldName': ('pfp.domain.shared_kernel', 'FieldName'),
    'KillConditionInfo': ('pfp.domain.shared_kernel', 'KillConditionInfo'),
    'LlmTurnPayloadV1': ('pfp.domain.shared_kernel', 'LlmTurnPayloadV1'),
    'ObstructionFamily': ('pfp.domain.shared_kernel', 'ObstructionFamily'),
    'ObstructionFamilyKind': ('pfp.domain.shared_kernel', 'ObstructionFamilyKind'),
    'ObstructionHintV1': ('pfp.domain.shared_kernel', 'ObstructionHintV1'),
    'ObstructionId': ('pfp.domain.shared_kernel', 'ObstructionId'),
    'OperationBudget': ('pfp.domain.shared_kernel', 'OperationBudget'),
    'OwnedPath': ('pfp.domain.shared_kernel', 'OwnedPath'),
    'PathManifest': ('pfp.domain.shared_kernel', 'PathManifest'),
    'ProducerId': ('pfp.domain.shared_kernel', 'ProducerId'),
    'PromptArtifactId': ('pfp.domain.shared_kernel', 'PromptArtifactId'),
    'ProtectedPath': ('pfp.domain.shared_kernel', 'ProtectedPath'),
    'ReceiptId': ('pfp.domain.shared_kernel', 'ReceiptId'),
    'Regime': ('pfp.domain.shared_kernel', 'Regime'),
    'RegimeKind': ('pfp.domain.shared_kernel', 'RegimeKind'),
    'RequiredReplyFields': ('pfp.domain.shared_kernel', 'RequiredReplyFields'),
    'ResidualColour': ('pfp.domain.shared_kernel', 'ResidualColour'),
    'ResidualDropV1': ('pfp.domain.shared_kernel', 'ResidualDropV1'),
    'Role': ('pfp.domain.shared_kernel', 'Role'),
    'RoleKind': ('pfp.domain.shared_kernel', 'RoleKind'),
    'RunRootId': ('pfp.domain.shared_kernel', 'RunRootId'),
    'StepBudget': ('pfp.domain.shared_kernel', 'StepBudget'),
    'TaskId': ('pfp.domain.shared_kernel', 'TaskId'),
    'TaskObjective': ('pfp.domain.shared_kernel', 'TaskObjective'),
    'TimeBudget': ('pfp.domain.shared_kernel', 'TimeBudget'),
    'TurnKind': ('pfp.domain.shared_kernel', 'TurnKind'),
    'TurnModality': ('pfp.domain.shared_kernel', 'TurnModality'),
    'TurnRole': ('pfp.domain.shared_kernel', 'TurnRole'),
    'TurnType': ('pfp.domain.shared_kernel', 'TurnType'),
    'TurnTypeKind': ('pfp.domain.shared_kernel', 'TurnTypeKind'),
    'WireKey': ('pfp.domain.shared_kernel', 'WireKey'),
    'CODE_CHANGE_WIRE_FIELDS': ('.wire_keys', 'CODE_CHANGE_WIRE_FIELDS'),
    'CodeChangeWireKey': ('.wire_keys', 'CodeChangeWireKey'),
    'DEMAND_ITEM_WIRE_FIELDS': ('.wire_keys', 'DEMAND_ITEM_WIRE_FIELDS'),
    'DemandItemWireKey': ('.wire_keys', 'DemandItemWireKey'),
    'ELIMINATION_RECEIPT_WIRE_FIELDS': ('.wire_keys', 'ELIMINATION_RECEIPT_WIRE_FIELDS'),
    'EliminationReceiptWireKey': ('.wire_keys', 'EliminationReceiptWireKey'),
    'OBJECTIVE_TYPED_WIRE_FIELDS': ('.wire_keys', 'OBJECTIVE_TYPED_WIRE_FIELDS'),
    'OBSTRUCTION_HINT_WIRE_FIELDS': ('.wire_keys', 'OBSTRUCTION_HINT_WIRE_FIELDS'),
    'ObjectiveTypedWireKey': ('.wire_keys', 'ObjectiveTypedWireKey'),
    'ObstructionHintWireKey': ('.wire_keys', 'ObstructionHintWireKey'),
    'PROMPT_ARTIFACT_WIRE_FIELDS': ('.wire_keys', 'PROMPT_ARTIFACT_WIRE_FIELDS'),
    'PromptArtifactWireKey': ('.wire_keys', 'PromptArtifactWireKey'),
    'REGIME_KINDS': ('.wire_keys', 'REGIME_KINDS'),
    'RESEARCH_CLAIM_WIRE_FIELDS': ('.wire_keys', 'RESEARCH_CLAIM_WIRE_FIELDS'),
    'RESIDUAL_COLOURS': ('.wire_keys', 'RESIDUAL_COLOURS'),
    'ResearchClaimWireKey': ('.wire_keys', 'ResearchClaimWireKey'),
    'ObjectiveTypedV1': ('pfp.domain.aggregates.prompt_artifact', 'ObjectiveTypedV1'),
    'ValueObject': ('pfp.domain.value_objects.base', 'ValueObject'),
    'CANONICAL_CHECKERS': ('pfp.domain.value_objects.identifiers', 'CANONICAL_CHECKERS'),
    'CaseId': ('pfp.domain.value_objects.identifiers', 'CaseId'),
    'CheckerIdVO': ('pfp.domain.value_objects.identifiers', 'CheckerIdVO'),
    'NormalFormId': ('pfp.domain.value_objects.identifiers', 'NormalFormId'),
    'PilotId': ('pfp.domain.value_objects.identifiers', 'PilotId'),
    'ProblemId': ('pfp.domain.value_objects.identifiers', 'ProblemId'),
    'PromptId': ('pfp.domain.value_objects.identifiers', 'PromptId'),
    'RequestId': ('pfp.domain.value_objects.identifiers', 'RequestId'),
    'Sha256Digest': ('pfp.domain.value_objects.identifiers', 'Sha256Digest'),
    'VerifierId': ('pfp.domain.value_objects.identifiers', 'VerifierId'),
    'BoundedTemperature': ('pfp.domain.value_objects.numerics', 'BoundedTemperature'),
    'DifficultyRung': ('pfp.domain.value_objects.numerics', 'DifficultyRung'),
    'MicroUsdSpend': ('pfp.domain.value_objects.numerics', 'MicroUsdSpend'),
    'StageNumber': ('pfp.domain.value_objects.numerics', 'StageNumber'),
    'StratumLevel': ('pfp.domain.value_objects.numerics', 'StratumLevel'),
    'VALID_ARITHMETIC_DOMAINS': ('pfp.domain.value_objects.taxonomy', 'VALID_ARITHMETIC_DOMAINS'),
    'VALID_CLAIMED_MOVES': ('pfp.domain.value_objects.taxonomy', 'VALID_CLAIMED_MOVES'),
    'VALID_EVALUATION_STATUSES': ('pfp.domain.value_objects.taxonomy', 'VALID_EVALUATION_STATUSES'),
    'VALID_EXECUTION_MODES': ('pfp.domain.value_objects.taxonomy', 'VALID_EXECUTION_MODES'),
    'VALID_SPAN_ROLES': ('pfp.domain.value_objects.taxonomy', 'VALID_SPAN_ROLES'),
    'VALID_TASK_FAMILIES': ('pfp.domain.value_objects.taxonomy', 'VALID_TASK_FAMILIES'),
    'VALID_TRIAL_STATUSES': ('pfp.domain.value_objects.taxonomy', 'VALID_TRIAL_STATUSES'),
    'VALID_VERIFICATION_RULES': ('pfp.domain.value_objects.taxonomy', 'VALID_VERIFICATION_RULES'),
    'VALID_VERIFICATION_STATUSES': ('pfp.domain.value_objects.taxonomy', 'VALID_VERIFICATION_STATUSES'),
    'ArithmeticDomainVO': ('pfp.domain.value_objects.taxonomy', 'ArithmeticDomainVO'),
    'ClaimedMoveVO': ('pfp.domain.value_objects.taxonomy', 'ClaimedMoveVO'),
    'EvaluationStatusVO': ('pfp.domain.value_objects.taxonomy', 'EvaluationStatusVO'),
    'ExecutionModeVO': ('pfp.domain.value_objects.taxonomy', 'ExecutionModeVO'),
    'SpanRoleVO': ('pfp.domain.value_objects.taxonomy', 'SpanRoleVO'),
    'TaskFamilyVO': ('pfp.domain.value_objects.taxonomy', 'TaskFamilyVO'),
    'TrialStatusVO': ('pfp.domain.value_objects.taxonomy', 'TrialStatusVO'),
    'VerificationRuleVO': ('pfp.domain.value_objects.taxonomy', 'VerificationRuleVO'),
    'VerificationStatusVO': ('pfp.domain.value_objects.taxonomy', 'VerificationStatusVO'),
    'ByteSpanVO': ('pfp.domain.value_objects.topology', 'ByteSpanVO'),
    'EdgeVO': ('pfp.domain.value_objects.topology', 'EdgeVO'),
    'MatrixShape': ('pfp.domain.value_objects.topology', 'MatrixShape'),
    'VertexId': ('pfp.domain.value_objects.topology', 'VertexId'),
    'ActiveObstructionVO': ('pfp.domain.value_objects.cycle_balance', 'ActiveObstructionVO'),
    'BoundaryMatricesVO': ('pfp.domain.value_objects.cycle_balance', 'BoundaryMatricesVO'),
    'CarrierEdgeVO': ('pfp.domain.value_objects.cycle_balance', 'CarrierEdgeVO'),
    'CarrierFaceVO': ('pfp.domain.value_objects.cycle_balance', 'CarrierFaceVO'),
    'CarrierVO': ('pfp.domain.value_objects.cycle_balance', 'CarrierVO'),
    'ClaimHygieneVO': ('pfp.domain.value_objects.cycle_balance', 'ClaimHygieneVO'),
    'StaticCellBoundsVO': ('pfp.domain.value_objects.cycle_balance', 'StaticCellBoundsVO'),
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
