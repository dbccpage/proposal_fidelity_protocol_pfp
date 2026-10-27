"""Canonical pure Engine Agentic Swarm kernel.

The Adversary stage owns typed swarm state and orchestration. Host effects remain behind
ports implemented by Operations/OEOS. AuthorityEffect: None.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

from . import profiles

if TYPE_CHECKING:
    from .application import AntibodySink, AntibodyStorePort, CemeterySink, ContinuationPortV1, ContinueDecisionKindV1, ContinueDecisionV1, DdaSink, DeterministicSchedulerV1, EmitterSuiteV1, EventPortV1, GenealogySink, GenealogyStorePort, HostPortV1, IntelligenceEventV1, MemoryPortV1, ModelPortV1, SchedulerPortV1, SeatPortV1, SgtSink, SkillPortV1, SwarmRuntimeV1, SymbolGamePacketSink, ToolPortV1, UnsSink, UtsSink, ValuatorPortV1, build_intelligence_event, build_swarm_run_receipt, compute_sbe_metrics, emit_event, parse_swarm_run_receipt, run_swarm, validate_swarm_composition, verify_swarm_run_receipt
    from .domain import AUTHORITY_EFFECT_NONE, AgentResultV1, CandidateProposalV1, CandidateSelectionProposalV1, ChallengeV1, EvaluatorEpochV1, LicensedWorkflowPlanV1, MetaSkillPolicyV1, NodeAssignmentV1, ProgressMeasureV1, SceneGraphV1, SceneSpecV1, SceneTransitionV1, SceneVisitV1, SeatRequirementV1, StopConditionV1, SwarmDefinitionV1, SwarmProfileV1, SwarmRunReceiptV1, SwarmRunStateV1, ValuationReceiptV1, WorkPacketV1, canonical_json_bytes, strict_json_loads

__all__ = ['AUTHORITY_EFFECT_NONE', 'AgentResultV1', 'AntibodySink', 'AntibodyStorePort', 'CandidateProposalV1', 'CandidateSelectionProposalV1', 'CemeterySink', 'ChallengeV1', 'ContinuationPortV1', 'ContinueDecisionKindV1', 'ContinueDecisionV1', 'DdaSink', 'DeterministicSchedulerV1', 'EmitterSuiteV1', 'EvaluatorEpochV1', 'EventPortV1', 'GenealogySink', 'GenealogyStorePort', 'HostPortV1', 'IntelligenceEventV1', 'LicensedWorkflowPlanV1', 'MemoryPortV1', 'MetaSkillPolicyV1', 'ModelPortV1', 'NodeAssignmentV1', 'ProgressMeasureV1', 'SceneGraphV1', 'SceneSpecV1', 'SceneTransitionV1', 'SceneVisitV1', 'SchedulerPortV1', 'SeatPortV1', 'SeatRequirementV1', 'SgtSink', 'SkillPortV1', 'StopConditionV1', 'SwarmDefinitionV1', 'SwarmProfileV1', 'SwarmRunReceiptV1', 'SwarmRunStateV1', 'SwarmRuntimeV1', 'SymbolGamePacketSink', 'ToolPortV1', 'UnsSink', 'UtsSink', 'ValuationReceiptV1', 'ValuatorPortV1', 'WorkPacketV1', 'build_intelligence_event', 'build_swarm_run_receipt', 'canonical_json_bytes', 'compute_sbe_metrics', 'emit_event', 'parse_swarm_run_receipt', 'profiles', 'run_swarm', 'strict_json_loads', 'validate_swarm_composition', 'verify_swarm_run_receipt']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'AntibodySink': ('.application', 'AntibodySink'),
    'AntibodyStorePort': ('.application', 'AntibodyStorePort'),
    'CemeterySink': ('.application', 'CemeterySink'),
    'ContinuationPortV1': ('.application', 'ContinuationPortV1'),
    'ContinueDecisionKindV1': ('.application', 'ContinueDecisionKindV1'),
    'ContinueDecisionV1': ('.application', 'ContinueDecisionV1'),
    'DdaSink': ('.application', 'DdaSink'),
    'DeterministicSchedulerV1': ('.application', 'DeterministicSchedulerV1'),
    'EmitterSuiteV1': ('.application', 'EmitterSuiteV1'),
    'EventPortV1': ('.application', 'EventPortV1'),
    'GenealogySink': ('.application', 'GenealogySink'),
    'GenealogyStorePort': ('.application', 'GenealogyStorePort'),
    'HostPortV1': ('.application', 'HostPortV1'),
    'IntelligenceEventV1': ('.application', 'IntelligenceEventV1'),
    'MemoryPortV1': ('.application', 'MemoryPortV1'),
    'ModelPortV1': ('.application', 'ModelPortV1'),
    'SchedulerPortV1': ('.application', 'SchedulerPortV1'),
    'SeatPortV1': ('.application', 'SeatPortV1'),
    'SgtSink': ('.application', 'SgtSink'),
    'SkillPortV1': ('.application', 'SkillPortV1'),
    'SwarmRuntimeV1': ('.application', 'SwarmRuntimeV1'),
    'SymbolGamePacketSink': ('.application', 'SymbolGamePacketSink'),
    'ToolPortV1': ('.application', 'ToolPortV1'),
    'UnsSink': ('.application', 'UnsSink'),
    'UtsSink': ('.application', 'UtsSink'),
    'ValuatorPortV1': ('.application', 'ValuatorPortV1'),
    'build_intelligence_event': ('.application', 'build_intelligence_event'),
    'build_swarm_run_receipt': ('.application', 'build_swarm_run_receipt'),
    'compute_sbe_metrics': ('.application', 'compute_sbe_metrics'),
    'emit_event': ('.application', 'emit_event'),
    'parse_swarm_run_receipt': ('.application', 'parse_swarm_run_receipt'),
    'run_swarm': ('.application', 'run_swarm'),
    'validate_swarm_composition': ('.application', 'validate_swarm_composition'),
    'verify_swarm_run_receipt': ('.application', 'verify_swarm_run_receipt'),
    'AUTHORITY_EFFECT_NONE': ('.domain', 'AUTHORITY_EFFECT_NONE'),
    'AgentResultV1': ('.domain', 'AgentResultV1'),
    'CandidateProposalV1': ('.domain', 'CandidateProposalV1'),
    'CandidateSelectionProposalV1': ('.domain', 'CandidateSelectionProposalV1'),
    'ChallengeV1': ('.domain', 'ChallengeV1'),
    'EvaluatorEpochV1': ('.domain', 'EvaluatorEpochV1'),
    'LicensedWorkflowPlanV1': ('.domain', 'LicensedWorkflowPlanV1'),
    'MetaSkillPolicyV1': ('.domain', 'MetaSkillPolicyV1'),
    'NodeAssignmentV1': ('.domain', 'NodeAssignmentV1'),
    'ProgressMeasureV1': ('.domain', 'ProgressMeasureV1'),
    'SceneGraphV1': ('.domain', 'SceneGraphV1'),
    'SceneSpecV1': ('.domain', 'SceneSpecV1'),
    'SceneTransitionV1': ('.domain', 'SceneTransitionV1'),
    'SceneVisitV1': ('.domain', 'SceneVisitV1'),
    'SeatRequirementV1': ('.domain', 'SeatRequirementV1'),
    'StopConditionV1': ('.domain', 'StopConditionV1'),
    'SwarmDefinitionV1': ('.domain', 'SwarmDefinitionV1'),
    'SwarmProfileV1': ('.domain', 'SwarmProfileV1'),
    'SwarmRunReceiptV1': ('.domain', 'SwarmRunReceiptV1'),
    'SwarmRunStateV1': ('.domain', 'SwarmRunStateV1'),
    'ValuationReceiptV1': ('.domain', 'ValuationReceiptV1'),
    'WorkPacketV1': ('.domain', 'WorkPacketV1'),
    'canonical_json_bytes': ('.domain', 'canonical_json_bytes'),
    'strict_json_loads': ('.domain', 'strict_json_loads'),
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
