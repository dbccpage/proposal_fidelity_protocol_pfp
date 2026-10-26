"""Domain Value Objects package for the Symbol Game bounded context.

Pure, immutable value objects with invariant validation, zero naked primitives,
and strict size and authority ceilings re-exported from shared_kernel and wire_keys.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    LlmPayloadV1 = LlmTurnPayloadV1
    from omega_engine_pfp.domain.shared_kernel import DEFAULT_REQUIRED_FIELDS, KILL_CONDITION_MAP, LLM_TURN_FAMILY, LLM_TURN_SCHEMA, MAX_CANDIDATE_BUDGET, MAX_OBJECTIVE_LENGTH, MAX_OPERATION_BUDGET, MAX_PAYLOAD_BYTES, MAX_STRING_LENGTH, REGISTERED_KILL_CONDITIONS, AuthorityEffect, Budget, BytePayload, CandidateBudget, CandidateId, CandidateProposal, CarrierId, CoboundaryScoreResult, ContentDigest, DemandId, DemandItemV1, Disposition, DispositionState, ExecutionBudget, FieldName, KillConditionInfo, LlmTurnPayloadV1, ObstructionFamily, ObstructionFamilyKind, ObstructionHintV1, ObstructionId, OperationBudget, OwnedPath, PathManifest, ProducerId, PromptArtifactId, ProtectedPath, ReceiptId, Regime, RegimeKind, RequiredReplyFields, ResidualColour, ResidualDropV1, Role, RoleKind, RunRootId, StepBudget, TaskId, TaskObjective, TimeBudget, TurnKind, TurnModality, TurnRole, TurnType, TurnTypeKind, WireKey
    from .wire_keys import CODE_CHANGE_WIRE_FIELDS, CodeChangeWireKey, DEMAND_ITEM_WIRE_FIELDS, DemandItemWireKey, ELIMINATION_RECEIPT_WIRE_FIELDS, EliminationReceiptWireKey, OBJECTIVE_TYPED_WIRE_FIELDS, OBSTRUCTION_HINT_WIRE_FIELDS, ObjectiveTypedWireKey, ObstructionHintWireKey, PROMPT_ARTIFACT_WIRE_FIELDS, PromptArtifactWireKey, REGIME_KINDS, RESEARCH_CLAIM_WIRE_FIELDS, RESIDUAL_COLOURS, ResearchClaimWireKey
    from omega_engine_pfp.domain.aggregates.prompt_artifact import ObjectiveTypedV1
    from omega_engine_pfp.domain.value_objects.base import ValueObject
    from omega_engine_pfp.domain.value_objects.identifiers import CANONICAL_CHECKERS
    from omega_engine_pfp.domain.value_objects.identifiers import CaseId
    from omega_engine_pfp.domain.value_objects.identifiers import CheckerIdVO
    from omega_engine_pfp.domain.value_objects.identifiers import NormalFormId
    from omega_engine_pfp.domain.value_objects.identifiers import PilotId
    from omega_engine_pfp.domain.value_objects.identifiers import ProblemId
    from omega_engine_pfp.domain.value_objects.identifiers import PromptId
    from omega_engine_pfp.domain.value_objects.identifiers import RequestId
    from omega_engine_pfp.domain.value_objects.identifiers import Sha256Digest
    from omega_engine_pfp.domain.value_objects.identifiers import VerifierId
    from omega_engine_pfp.domain.value_objects.numerics import BoundedTemperature
    from omega_engine_pfp.domain.value_objects.numerics import DifficultyRung
    from omega_engine_pfp.domain.value_objects.numerics import MicroUsdSpend
    from omega_engine_pfp.domain.value_objects.numerics import StageNumber
    from omega_engine_pfp.domain.value_objects.numerics import StratumLevel
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_ARITHMETIC_DOMAINS
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_CLAIMED_MOVES
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_EVALUATION_STATUSES
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_EXECUTION_MODES
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_SPAN_ROLES
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_TASK_FAMILIES
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_TRIAL_STATUSES
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_VERIFICATION_RULES
    from omega_engine_pfp.domain.value_objects.taxonomy import VALID_VERIFICATION_STATUSES
    from omega_engine_pfp.domain.value_objects.taxonomy import ArithmeticDomainVO
    from omega_engine_pfp.domain.value_objects.taxonomy import ClaimedMoveVO
    from omega_engine_pfp.domain.value_objects.taxonomy import EvaluationStatusVO
    from omega_engine_pfp.domain.value_objects.taxonomy import ExecutionModeVO
    from omega_engine_pfp.domain.value_objects.taxonomy import SpanRoleVO
    from omega_engine_pfp.domain.value_objects.taxonomy import TaskFamilyVO
    from omega_engine_pfp.domain.value_objects.taxonomy import TrialStatusVO
    from omega_engine_pfp.domain.value_objects.taxonomy import VerificationRuleVO
    from omega_engine_pfp.domain.value_objects.taxonomy import VerificationStatusVO
    from omega_engine_pfp.domain.value_objects.topology import ByteSpanVO
    from omega_engine_pfp.domain.value_objects.topology import EdgeVO
    from omega_engine_pfp.domain.value_objects.topology import MatrixShape
    from omega_engine_pfp.domain.value_objects.topology import VertexId
    from omega_engine_pfp.domain.value_objects.cycle_balance import ActiveObstructionVO
    from omega_engine_pfp.domain.value_objects.cycle_balance import BoundaryMatricesVO
    from omega_engine_pfp.domain.value_objects.cycle_balance import CarrierEdgeVO
    from omega_engine_pfp.domain.value_objects.cycle_balance import CarrierFaceVO
    from omega_engine_pfp.domain.value_objects.cycle_balance import CarrierVO
    from omega_engine_pfp.domain.value_objects.cycle_balance import ClaimHygieneVO
    from omega_engine_pfp.domain.value_objects.cycle_balance import StaticCellBoundsVO


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
    'LlmPayloadV1': ('omega_engine_pfp.domain.shared_kernel', 'LlmTurnPayloadV1'),
    'DEFAULT_REQUIRED_FIELDS': ('omega_engine_pfp.domain.shared_kernel', 'DEFAULT_REQUIRED_FIELDS'),
    'KILL_CONDITION_MAP': ('omega_engine_pfp.domain.shared_kernel', 'KILL_CONDITION_MAP'),
    'LLM_TURN_FAMILY': ('omega_engine_pfp.domain.shared_kernel', 'LLM_TURN_FAMILY'),
    'LLM_TURN_SCHEMA': ('omega_engine_pfp.domain.shared_kernel', 'LLM_TURN_SCHEMA'),
    'MAX_CANDIDATE_BUDGET': ('omega_engine_pfp.domain.shared_kernel', 'MAX_CANDIDATE_BUDGET'),
    'MAX_OBJECTIVE_LENGTH': ('omega_engine_pfp.domain.shared_kernel', 'MAX_OBJECTIVE_LENGTH'),
    'MAX_OPERATION_BUDGET': ('omega_engine_pfp.domain.shared_kernel', 'MAX_OPERATION_BUDGET'),
    'MAX_PAYLOAD_BYTES': ('omega_engine_pfp.domain.shared_kernel', 'MAX_PAYLOAD_BYTES'),
    'MAX_STRING_LENGTH': ('omega_engine_pfp.domain.shared_kernel', 'MAX_STRING_LENGTH'),
    'REGISTERED_KILL_CONDITIONS': ('omega_engine_pfp.domain.shared_kernel', 'REGISTERED_KILL_CONDITIONS'),
    'AuthorityEffect': ('omega_engine_pfp.domain.shared_kernel', 'AuthorityEffect'),
    'Budget': ('omega_engine_pfp.domain.shared_kernel', 'Budget'),
    'BytePayload': ('omega_engine_pfp.domain.shared_kernel', 'BytePayload'),
    'CandidateBudget': ('omega_engine_pfp.domain.shared_kernel', 'CandidateBudget'),
    'CandidateId': ('omega_engine_pfp.domain.shared_kernel', 'CandidateId'),
    'CandidateProposal': ('omega_engine_pfp.domain.shared_kernel', 'CandidateProposal'),
    'CarrierId': ('omega_engine_pfp.domain.shared_kernel', 'CarrierId'),
    'CoboundaryScoreResult': ('omega_engine_pfp.domain.shared_kernel', 'CoboundaryScoreResult'),
    'ContentDigest': ('omega_engine_pfp.domain.shared_kernel', 'ContentDigest'),
    'DemandId': ('omega_engine_pfp.domain.shared_kernel', 'DemandId'),
    'DemandItemV1': ('omega_engine_pfp.domain.shared_kernel', 'DemandItemV1'),
    'Disposition': ('omega_engine_pfp.domain.shared_kernel', 'Disposition'),
    'DispositionState': ('omega_engine_pfp.domain.shared_kernel', 'DispositionState'),
    'ExecutionBudget': ('omega_engine_pfp.domain.shared_kernel', 'ExecutionBudget'),
    'FieldName': ('omega_engine_pfp.domain.shared_kernel', 'FieldName'),
    'KillConditionInfo': ('omega_engine_pfp.domain.shared_kernel', 'KillConditionInfo'),
    'LlmTurnPayloadV1': ('omega_engine_pfp.domain.shared_kernel', 'LlmTurnPayloadV1'),
    'ObstructionFamily': ('omega_engine_pfp.domain.shared_kernel', 'ObstructionFamily'),
    'ObstructionFamilyKind': ('omega_engine_pfp.domain.shared_kernel', 'ObstructionFamilyKind'),
    'ObstructionHintV1': ('omega_engine_pfp.domain.shared_kernel', 'ObstructionHintV1'),
    'ObstructionId': ('omega_engine_pfp.domain.shared_kernel', 'ObstructionId'),
    'OperationBudget': ('omega_engine_pfp.domain.shared_kernel', 'OperationBudget'),
    'OwnedPath': ('omega_engine_pfp.domain.shared_kernel', 'OwnedPath'),
    'PathManifest': ('omega_engine_pfp.domain.shared_kernel', 'PathManifest'),
    'ProducerId': ('omega_engine_pfp.domain.shared_kernel', 'ProducerId'),
    'PromptArtifactId': ('omega_engine_pfp.domain.shared_kernel', 'PromptArtifactId'),
    'ProtectedPath': ('omega_engine_pfp.domain.shared_kernel', 'ProtectedPath'),
    'ReceiptId': ('omega_engine_pfp.domain.shared_kernel', 'ReceiptId'),
    'Regime': ('omega_engine_pfp.domain.shared_kernel', 'Regime'),
    'RegimeKind': ('omega_engine_pfp.domain.shared_kernel', 'RegimeKind'),
    'RequiredReplyFields': ('omega_engine_pfp.domain.shared_kernel', 'RequiredReplyFields'),
    'ResidualColour': ('omega_engine_pfp.domain.shared_kernel', 'ResidualColour'),
    'ResidualDropV1': ('omega_engine_pfp.domain.shared_kernel', 'ResidualDropV1'),
    'Role': ('omega_engine_pfp.domain.shared_kernel', 'Role'),
    'RoleKind': ('omega_engine_pfp.domain.shared_kernel', 'RoleKind'),
    'RunRootId': ('omega_engine_pfp.domain.shared_kernel', 'RunRootId'),
    'StepBudget': ('omega_engine_pfp.domain.shared_kernel', 'StepBudget'),
    'TaskId': ('omega_engine_pfp.domain.shared_kernel', 'TaskId'),
    'TaskObjective': ('omega_engine_pfp.domain.shared_kernel', 'TaskObjective'),
    'TimeBudget': ('omega_engine_pfp.domain.shared_kernel', 'TimeBudget'),
    'TurnKind': ('omega_engine_pfp.domain.shared_kernel', 'TurnKind'),
    'TurnModality': ('omega_engine_pfp.domain.shared_kernel', 'TurnModality'),
    'TurnRole': ('omega_engine_pfp.domain.shared_kernel', 'TurnRole'),
    'TurnType': ('omega_engine_pfp.domain.shared_kernel', 'TurnType'),
    'TurnTypeKind': ('omega_engine_pfp.domain.shared_kernel', 'TurnTypeKind'),
    'WireKey': ('omega_engine_pfp.domain.shared_kernel', 'WireKey'),
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
    'ObjectiveTypedV1': ('omega_engine_pfp.domain.aggregates.prompt_artifact', 'ObjectiveTypedV1'),
    'ValueObject': ('omega_engine_pfp.domain.value_objects.base', 'ValueObject'),
    'CANONICAL_CHECKERS': ('omega_engine_pfp.domain.value_objects.identifiers', 'CANONICAL_CHECKERS'),
    'CaseId': ('omega_engine_pfp.domain.value_objects.identifiers', 'CaseId'),
    'CheckerIdVO': ('omega_engine_pfp.domain.value_objects.identifiers', 'CheckerIdVO'),
    'NormalFormId': ('omega_engine_pfp.domain.value_objects.identifiers', 'NormalFormId'),
    'PilotId': ('omega_engine_pfp.domain.value_objects.identifiers', 'PilotId'),
    'ProblemId': ('omega_engine_pfp.domain.value_objects.identifiers', 'ProblemId'),
    'PromptId': ('omega_engine_pfp.domain.value_objects.identifiers', 'PromptId'),
    'RequestId': ('omega_engine_pfp.domain.value_objects.identifiers', 'RequestId'),
    'Sha256Digest': ('omega_engine_pfp.domain.value_objects.identifiers', 'Sha256Digest'),
    'VerifierId': ('omega_engine_pfp.domain.value_objects.identifiers', 'VerifierId'),
    'BoundedTemperature': ('omega_engine_pfp.domain.value_objects.numerics', 'BoundedTemperature'),
    'DifficultyRung': ('omega_engine_pfp.domain.value_objects.numerics', 'DifficultyRung'),
    'MicroUsdSpend': ('omega_engine_pfp.domain.value_objects.numerics', 'MicroUsdSpend'),
    'StageNumber': ('omega_engine_pfp.domain.value_objects.numerics', 'StageNumber'),
    'StratumLevel': ('omega_engine_pfp.domain.value_objects.numerics', 'StratumLevel'),
    'VALID_ARITHMETIC_DOMAINS': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_ARITHMETIC_DOMAINS'),
    'VALID_CLAIMED_MOVES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_CLAIMED_MOVES'),
    'VALID_EVALUATION_STATUSES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_EVALUATION_STATUSES'),
    'VALID_EXECUTION_MODES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_EXECUTION_MODES'),
    'VALID_SPAN_ROLES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_SPAN_ROLES'),
    'VALID_TASK_FAMILIES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_TASK_FAMILIES'),
    'VALID_TRIAL_STATUSES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_TRIAL_STATUSES'),
    'VALID_VERIFICATION_RULES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_VERIFICATION_RULES'),
    'VALID_VERIFICATION_STATUSES': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VALID_VERIFICATION_STATUSES'),
    'ArithmeticDomainVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'ArithmeticDomainVO'),
    'ClaimedMoveVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'ClaimedMoveVO'),
    'EvaluationStatusVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'EvaluationStatusVO'),
    'ExecutionModeVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'ExecutionModeVO'),
    'SpanRoleVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'SpanRoleVO'),
    'TaskFamilyVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'TaskFamilyVO'),
    'TrialStatusVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'TrialStatusVO'),
    'VerificationRuleVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VerificationRuleVO'),
    'VerificationStatusVO': ('omega_engine_pfp.domain.value_objects.taxonomy', 'VerificationStatusVO'),
    'ByteSpanVO': ('omega_engine_pfp.domain.value_objects.topology', 'ByteSpanVO'),
    'EdgeVO': ('omega_engine_pfp.domain.value_objects.topology', 'EdgeVO'),
    'MatrixShape': ('omega_engine_pfp.domain.value_objects.topology', 'MatrixShape'),
    'VertexId': ('omega_engine_pfp.domain.value_objects.topology', 'VertexId'),
    'ActiveObstructionVO': ('omega_engine_pfp.domain.value_objects.cycle_balance', 'ActiveObstructionVO'),
    'BoundaryMatricesVO': ('omega_engine_pfp.domain.value_objects.cycle_balance', 'BoundaryMatricesVO'),
    'CarrierEdgeVO': ('omega_engine_pfp.domain.value_objects.cycle_balance', 'CarrierEdgeVO'),
    'CarrierFaceVO': ('omega_engine_pfp.domain.value_objects.cycle_balance', 'CarrierFaceVO'),
    'CarrierVO': ('omega_engine_pfp.domain.value_objects.cycle_balance', 'CarrierVO'),
    'ClaimHygieneVO': ('omega_engine_pfp.domain.value_objects.cycle_balance', 'ClaimHygieneVO'),
    'StaticCellBoundsVO': ('omega_engine_pfp.domain.value_objects.cycle_balance', 'StaticCellBoundsVO'),
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
