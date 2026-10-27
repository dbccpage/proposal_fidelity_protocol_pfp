"""Adversary engineering profile for the pure Adversary stage kernel."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .adjudication import adjudicate_adversary_scene
    from .anti_skill import TRUTH_BOUNDARY_TRIO, evaluate_adversary_anti_skill_gate
    from .factory_phi import ADVERSARY_ENGINEERING_PROBES, CohomologyImportBundleV1, CohomologyValuationReceiptV1, AdversaryEngineeringResidualV1, AdversaryFactoryPhiV1, freeze_adversary_evaluator_epoch_v1
    from .models import ANTI_SKILL_STAGE_ORDER, AntiSkillGateReceiptV1, CalibrationReceiptV1, InertMinedProposalV1, PredictionReceiptV1, AdversarySealPacketV1, AdversarySeatBindingV1, AdversarySeatResultV1, calibrate_prediction
    from .qualification import QUALIFICATION_LEVELS, ParallelCriticFindingV1, QualificationLadderV1, QualificationReceiptV1, SupervisedEngineeringPacketV1, aggregate_parallel_findings, build_supervised_engineering_packet_v1, qualification_receipt_v1
    from .render import RenderedAdversarySealV1, render_adversary_seal_packet, verify_rendered_adversary_seal
    from .selection import REQUIRED_HARD_GATES, CandidateProductivityAssessmentV1, HardGateResultV1, candidate_may_advance, select_adversary_candidate
    from .topology import AdversaryProfileAssemblyV1, build_adversary_engineering_profile_v1, adversary_scene_graph_v1, adversary_seat_requirements_v1

__all__ = ['ANTI_SKILL_STAGE_ORDER', 'QUALIFICATION_LEVELS', 'REQUIRED_HARD_GATES', 'TRUTH_BOUNDARY_TRIO', 'ADVERSARY_ENGINEERING_PROBES', 'AntiSkillGateReceiptV1', 'CalibrationReceiptV1', 'CandidateProductivityAssessmentV1', 'CohomologyImportBundleV1', 'CohomologyValuationReceiptV1', 'HardGateResultV1', 'InertMinedProposalV1', 'ParallelCriticFindingV1', 'PredictionReceiptV1', 'QualificationLadderV1', 'QualificationReceiptV1', 'RenderedAdversarySealV1', 'SupervisedEngineeringPacketV1', 'AdversaryEngineeringResidualV1', 'AdversaryFactoryPhiV1', 'AdversaryProfileAssemblyV1', 'AdversarySealPacketV1', 'AdversarySeatBindingV1', 'AdversarySeatResultV1', 'adjudicate_adversary_scene', 'aggregate_parallel_findings', 'build_supervised_engineering_packet_v1', 'build_adversary_engineering_profile_v1', 'calibrate_prediction', 'candidate_may_advance', 'evaluate_adversary_anti_skill_gate', 'freeze_adversary_evaluator_epoch_v1', 'qualification_receipt_v1', 'render_adversary_seal_packet', 'select_adversary_candidate', 'verify_rendered_adversary_seal', 'adversary_scene_graph_v1', 'adversary_seat_requirements_v1']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'adjudicate_adversary_scene': ('.adjudication', 'adjudicate_adversary_scene'),
    'TRUTH_BOUNDARY_TRIO': ('.anti_skill', 'TRUTH_BOUNDARY_TRIO'),
    'evaluate_adversary_anti_skill_gate': ('.anti_skill', 'evaluate_adversary_anti_skill_gate'),
    'ADVERSARY_ENGINEERING_PROBES': ('.factory_phi', 'ADVERSARY_ENGINEERING_PROBES'),
    'CohomologyImportBundleV1': ('.factory_phi', 'CohomologyImportBundleV1'),
    'CohomologyValuationReceiptV1': ('.factory_phi', 'CohomologyValuationReceiptV1'),
    'AdversaryEngineeringResidualV1': ('.factory_phi', 'AdversaryEngineeringResidualV1'),
    'AdversaryFactoryPhiV1': ('.factory_phi', 'AdversaryFactoryPhiV1'),
    'freeze_adversary_evaluator_epoch_v1': ('.factory_phi', 'freeze_adversary_evaluator_epoch_v1'),
    'ANTI_SKILL_STAGE_ORDER': ('.models', 'ANTI_SKILL_STAGE_ORDER'),
    'AntiSkillGateReceiptV1': ('.models', 'AntiSkillGateReceiptV1'),
    'CalibrationReceiptV1': ('.models', 'CalibrationReceiptV1'),
    'InertMinedProposalV1': ('.models', 'InertMinedProposalV1'),
    'PredictionReceiptV1': ('.models', 'PredictionReceiptV1'),
    'AdversarySealPacketV1': ('.models', 'AdversarySealPacketV1'),
    'AdversarySeatBindingV1': ('.models', 'AdversarySeatBindingV1'),
    'AdversarySeatResultV1': ('.models', 'AdversarySeatResultV1'),
    'calibrate_prediction': ('.models', 'calibrate_prediction'),
    'QUALIFICATION_LEVELS': ('.qualification', 'QUALIFICATION_LEVELS'),
    'ParallelCriticFindingV1': ('.qualification', 'ParallelCriticFindingV1'),
    'QualificationLadderV1': ('.qualification', 'QualificationLadderV1'),
    'QualificationReceiptV1': ('.qualification', 'QualificationReceiptV1'),
    'SupervisedEngineeringPacketV1': ('.qualification', 'SupervisedEngineeringPacketV1'),
    'aggregate_parallel_findings': ('.qualification', 'aggregate_parallel_findings'),
    'build_supervised_engineering_packet_v1': ('.qualification', 'build_supervised_engineering_packet_v1'),
    'qualification_receipt_v1': ('.qualification', 'qualification_receipt_v1'),
    'RenderedAdversarySealV1': ('.render', 'RenderedAdversarySealV1'),
    'render_adversary_seal_packet': ('.render', 'render_adversary_seal_packet'),
    'verify_rendered_adversary_seal': ('.render', 'verify_rendered_adversary_seal'),
    'REQUIRED_HARD_GATES': ('.selection', 'REQUIRED_HARD_GATES'),
    'CandidateProductivityAssessmentV1': ('.selection', 'CandidateProductivityAssessmentV1'),
    'HardGateResultV1': ('.selection', 'HardGateResultV1'),
    'candidate_may_advance': ('.selection', 'candidate_may_advance'),
    'select_adversary_candidate': ('.selection', 'select_adversary_candidate'),
    'AdversaryProfileAssemblyV1': ('.topology', 'AdversaryProfileAssemblyV1'),
    'build_adversary_engineering_profile_v1': ('.topology', 'build_adversary_engineering_profile_v1'),
    'adversary_scene_graph_v1': ('.topology', 'adversary_scene_graph_v1'),
    'adversary_seat_requirements_v1': ('.topology', 'adversary_seat_requirements_v1'),
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
