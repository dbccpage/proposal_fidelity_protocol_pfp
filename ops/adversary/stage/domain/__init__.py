"""Pure domain surface for Engine Agentic Swarm.

The DDC alphabet is bound by the composition root. Importing this package does not read the disk.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .canonical import (
        AUTHORITY_EFFECT_NONE,
        canonical_json_bytes,
        semantic_id,
        strict_json_loads,
    )
    from .cochain import (
        DEFAULT_CLEAN_ARCH_LAYERS,
        ASTCochainExtractor,
        ASTDefect,
        ASTDependencyComplex,
        ASTEvaluationReport,
        ASTMetricsEvaluator,
        ASTSourceParser,
    )
    from .colour_projection import (
        SEAT_CAPABILITY_COLOURS,
        TURN_REPLY_RESIDUAL_COLOURS,
        project_residuals_to_codes,
        validate_seat_capabilities,
    )
    from .ddc import (
        DdaStepReceipt,
        DdaStepV1,
        DdcStepReceipt,
        DdcStepV1,
        validate_dda_purity,
        validate_ddc_purity,
    )
    from .evaluation import (
        EvaluatorEpochV1,
        ProgressMeasureV1,
        StopConditionV1,
        ValuationReceiptV1,
    )
    from .genealogy import (
        AntibodyEntryV1,
        CemeteryHeadstoneV1,
        GenealogyEntryV1,
    )
    from .immune import (
        DEFAULT_ANTIBODY_TEMPLATES,
        Antibody,
        ConstraintType,
        Operatorizability,
        PharmacyCatalogRepository,
        PharmacySeeder,
        PharmacyStatus,
        RuntimeAction,
        Severity,
    )
    from .packets import (
        AgentResultV1,
        CandidateProposalV1,
        ChallengeV1,
        LicensedWorkflowPlanV1,
        MetaSkillPolicyV1,
        WorkPacketV1,
    )
    from .ports import (
        AntibodyStorePort,
        CemeterySink,
        ContinuationPortV1,
        ContinueDecisionKindV1,
        ContinueDecisionV1,
        DdaSink,
        DdcSink,
        EventPortV1,
        GenealogyStorePort,
        HostPortV1,
        MemoryPortV1,
        ModelPortV1,
        RunStateStorePort,
        SchedulerPortV1,
        SeatPortV1,
        SgtSink,
        SkillPortV1,
        ToolPortV1,
        UnsSink,
        UtsSink,
        ValuatorPortV1,
    )
    from .quantum import (
        SBE_DIMENSION,
        SBEAnalyzer,
        SBEDensityReport,
        TextStateProjector,
    )
    from .run import (
        CandidateSelectionProposalV1,
        SceneVisitV1,
        SwarmRunReceiptV1,
        SwarmRunStateV1,
    )
    from .topology import (
        NodeAssignmentV1,
        SceneGraphV1,
        SceneSpecV1,
        SceneTransitionV1,
        SeatRequirementV1,
        SwarmDefinitionV1,
        SwarmProfileV1,
    )

__all__ = [
    "AUTHORITY_EFFECT_NONE",
    "AgentResultV1",
    "AntibodyEntryV1",
    "CandidateProposalV1",
    "CandidateSelectionProposalV1",
    "CemeteryHeadstoneV1",
    "ChallengeV1",
    "DdaLetter",
    "DdaStepReceipt",
    "DdaStepV1",
    "DdcLetter",
    "DdcStepReceipt",
    "DdcStepV1",
    "EvaluatorEpochV1",
    "GenealogyEntryV1",
    "LicensedWorkflowPlanV1",
    "MetaSkillPolicyV1",
    "NodeAssignmentV1",
    "ProgressMeasureV1",
    "SEAT_CAPABILITY_COLOURS",
    "SceneGraphV1",
    "SceneSpecV1",
    "SceneTransitionV1",
    "SceneVisitV1",
    "SeatRequirementV1",
    "StopConditionV1",
    "SwarmDefinitionV1",
    "SwarmProfileV1",
    "SwarmRunReceiptV1",
    "SwarmRunStateV1",
    "TURN_REPLY_RESIDUAL_COLOURS",
    "ValuationReceiptV1",
    "WorkPacketV1",
    "canonical_json_bytes",
    "project_residuals_to_codes",
    "semantic_id",
    "strict_json_loads",
    "validate_dda_purity",
    "validate_ddc_purity",
    "validate_seat_capabilities",
    # Quantum
    "SBE_DIMENSION",
    "SBEDensityReport",
    "TextStateProjector",
    "SBEAnalyzer",
    # Immune / Pharmacy
    "Antibody",
    "ConstraintType",
    "Operatorizability",
    "RuntimeAction",
    "Severity",
    "PharmacyStatus",
    "PharmacyCatalogRepository",
    "PharmacySeeder",
    "DEFAULT_ANTIBODY_TEMPLATES",
    # AST Cochain
    "ASTDefect",
    "ASTEvaluationReport",
    "ASTSourceParser",
    "ASTDependencyComplex",
    "DEFAULT_CLEAN_ARCH_LAYERS",
    "ASTMetricsEvaluator",
    "ASTCochainExtractor",
    # Domain Ports & Sinks
    "AntibodyStorePort",
    "CemeterySink",
    "ContinuationPortV1",
    "ContinueDecisionKindV1",
    "ContinueDecisionV1",
    "DdaSink",
    "DdcSink",
    "EventPortV1",
    "GenealogyStorePort",
    "HostPortV1",
    "MemoryPortV1",
    "ModelPortV1",
    "RunStateStorePort",
    "SchedulerPortV1",
    "SeatPortV1",
    "SgtSink",
    "SkillPortV1",
    "ToolPortV1",
    "UnsSink",
    "UtsSink",
    "ValuatorPortV1",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "AUTHORITY_EFFECT_NONE": (".canonical", "AUTHORITY_EFFECT_NONE"),
    "canonical_json_bytes": (".canonical", "canonical_json_bytes"),
    "semantic_id": (".canonical", "semantic_id"),
    "strict_json_loads": (".canonical", "strict_json_loads"),
    "DEFAULT_CLEAN_ARCH_LAYERS": (".cochain", "DEFAULT_CLEAN_ARCH_LAYERS"),
    "ASTCochainExtractor": (".cochain", "ASTCochainExtractor"),
    "ASTDefect": (".cochain", "ASTDefect"),
    "ASTDependencyComplex": (".cochain", "ASTDependencyComplex"),
    "ASTEvaluationReport": (".cochain", "ASTEvaluationReport"),
    "ASTMetricsEvaluator": (".cochain", "ASTMetricsEvaluator"),
    "ASTSourceParser": (".cochain", "ASTSourceParser"),
    "SEAT_CAPABILITY_COLOURS": (".colour_projection", "SEAT_CAPABILITY_COLOURS"),
    "TURN_REPLY_RESIDUAL_COLOURS": (".colour_projection", "TURN_REPLY_RESIDUAL_COLOURS"),
    "project_residuals_to_codes": (".colour_projection", "project_residuals_to_codes"),
    "validate_seat_capabilities": (".colour_projection", "validate_seat_capabilities"),
    "DdaStepReceipt": (".ddc", "DdaStepReceipt"),
    "DdaStepV1": (".ddc", "DdaStepV1"),
    "DdcStepReceipt": (".ddc", "DdcStepReceipt"),
    "DdcStepV1": (".ddc", "DdcStepV1"),
    "validate_dda_purity": (".ddc", "validate_dda_purity"),
    "validate_ddc_purity": (".ddc", "validate_ddc_purity"),
    "EvaluatorEpochV1": (".evaluation", "EvaluatorEpochV1"),
    "ProgressMeasureV1": (".evaluation", "ProgressMeasureV1"),
    "StopConditionV1": (".evaluation", "StopConditionV1"),
    "ValuationReceiptV1": (".evaluation", "ValuationReceiptV1"),
    "AntibodyEntryV1": (".genealogy", "AntibodyEntryV1"),
    "CemeteryHeadstoneV1": (".genealogy", "CemeteryHeadstoneV1"),
    "GenealogyEntryV1": (".genealogy", "GenealogyEntryV1"),
    "DEFAULT_ANTIBODY_TEMPLATES": (".immune", "DEFAULT_ANTIBODY_TEMPLATES"),
    "Antibody": (".immune", "Antibody"),
    "ConstraintType": (".immune", "ConstraintType"),
    "Operatorizability": (".immune", "Operatorizability"),
    "PharmacyCatalogRepository": (".immune", "PharmacyCatalogRepository"),
    "PharmacySeeder": (".immune", "PharmacySeeder"),
    "PharmacyStatus": (".immune", "PharmacyStatus"),
    "RuntimeAction": (".immune", "RuntimeAction"),
    "Severity": (".immune", "Severity"),
    "AgentResultV1": (".packets", "AgentResultV1"),
    "CandidateProposalV1": (".packets", "CandidateProposalV1"),
    "ChallengeV1": (".packets", "ChallengeV1"),
    "LicensedWorkflowPlanV1": (".packets", "LicensedWorkflowPlanV1"),
    "MetaSkillPolicyV1": (".packets", "MetaSkillPolicyV1"),
    "WorkPacketV1": (".packets", "WorkPacketV1"),
    "AntibodyStorePort": (".ports", "AntibodyStorePort"),
    "CemeterySink": (".ports", "CemeterySink"),
    "ContinuationPortV1": (".ports", "ContinuationPortV1"),
    "ContinueDecisionKindV1": (".ports", "ContinueDecisionKindV1"),
    "ContinueDecisionV1": (".ports", "ContinueDecisionV1"),
    "DdaSink": (".ports", "DdaSink"),
    "DdcSink": (".ports", "DdcSink"),
    "EventPortV1": (".ports", "EventPortV1"),
    "GenealogyStorePort": (".ports", "GenealogyStorePort"),
    "HostPortV1": (".ports", "HostPortV1"),
    "MemoryPortV1": (".ports", "MemoryPortV1"),
    "ModelPortV1": (".ports", "ModelPortV1"),
    "RunStateStorePort": (".ports", "RunStateStorePort"),
    "SchedulerPortV1": (".ports", "SchedulerPortV1"),
    "SeatPortV1": (".ports", "SeatPortV1"),
    "SgtSink": (".ports", "SgtSink"),
    "SkillPortV1": (".ports", "SkillPortV1"),
    "ToolPortV1": (".ports", "ToolPortV1"),
    "UnsSink": (".ports", "UnsSink"),
    "UtsSink": (".ports", "UtsSink"),
    "ValuatorPortV1": (".ports", "ValuatorPortV1"),
    "SBE_DIMENSION": (".quantum", "SBE_DIMENSION"),
    "SBEAnalyzer": (".quantum", "SBEAnalyzer"),
    "SBEDensityReport": (".quantum", "SBEDensityReport"),
    "TextStateProjector": (".quantum", "TextStateProjector"),
    "CandidateSelectionProposalV1": (".run", "CandidateSelectionProposalV1"),
    "SceneVisitV1": (".run", "SceneVisitV1"),
    "SwarmRunReceiptV1": (".run", "SwarmRunReceiptV1"),
    "SwarmRunStateV1": (".run", "SwarmRunStateV1"),
    "NodeAssignmentV1": (".topology", "NodeAssignmentV1"),
    "SceneGraphV1": (".topology", "SceneGraphV1"),
    "SceneSpecV1": (".topology", "SceneSpecV1"),
    "SceneTransitionV1": (".topology", "SceneTransitionV1"),
    "SeatRequirementV1": (".topology", "SeatRequirementV1"),
    "SwarmDefinitionV1": (".topology", "SwarmDefinitionV1"),
    "SwarmProfileV1": (".topology", "SwarmProfileV1"),
}


def __getattr__(name: str) -> Any:
    # Bound after this package is first imported. A module-level name would stay None.
    if name == "DdaLetter" or name == "DdcLetter":
        from . import ddc as ddc_module

        return getattr(ddc_module, name)
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
