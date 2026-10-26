"""Use Cases Layer for the Symbol Game Bounded Context.

Orchestrates thin application workflows across Domain aggregates and value objects.
Zero dependencies on infrastructure or UI.
"""

from __future__ import annotations

import importlib
from typing import Any

__all__ = [
    "BoundCandidate",
    "CodeChangeSession",
    "CompilePromptUseCase",
    "CreateCodeChangeProposalUseCase",
    "CreateTurnUseCase",
    "EliminateObstructionUseCase",
    "EvaluateCandidateUseCase",
    "EvaluateCecMetricUseCase",
    "EvaluateCoboundaryScoreUseCase",
    "EvaluatePatchGatesUseCase",
    "EvaluatePolicyUseCase",
    "FinalizeCodeChangeRunUseCase",
    "FreezeCorpusUseCase",
    "IntakeResearchSourcesUseCase",
    "KILL_CONDITION_MAP",
    "ParseMachineBlockUseCase",
    "ProblemRunnerUseCase",
    "SubmitCandidateUseCase",
    "SubmitPatchCandidateUseCase",
    "SymbolGameExecutionService",
    "ValidateReplyResidualUseCase",
    "VerifyResearchClaimUseCase",
    "magnitudes_from_ledger_active",
    "rank_by_efficiency",
    "rank_candidate_proposals",
    "residual_drop_from_ids",
    "residual_drop_from_ledger_maps",
    "score_cochain_proposal",
    "score_discrete_proposal",
]

_EXPORT_MODULES: dict[str, tuple[str, ...]] = {
    "cec_bridge": ("EvaluateCecMetricUseCase",),
    "code_change": (
        "BoundCandidate",
        "CodeChangeSession",
        "CreateCodeChangeProposalUseCase",
        "EvaluatePatchGatesUseCase",
        "FinalizeCodeChangeRunUseCase",
        "SubmitPatchCandidateUseCase",
    ),
    "learning": ("EvaluatePolicyUseCase", "FreezeCorpusUseCase"),
    "llm_turn": (
        "CreateTurnUseCase",
        "EvaluateCandidateUseCase",
        "ParseMachineBlockUseCase",
        "SubmitCandidateUseCase",
    ),
    "problem_runner": ("ProblemRunnerUseCase",),
    "prompt_artifact": (
        "CompilePromptUseCase",
        "EliminateObstructionUseCase",
        "ValidateReplyResidualUseCase",
    ),
    "research": ("IntakeResearchSourcesUseCase", "VerifyResearchClaimUseCase"),
    "scoring": (
        "EvaluateCoboundaryScoreUseCase",
        "KILL_CONDITION_MAP",
        "magnitudes_from_ledger_active",
        "rank_by_efficiency",
        "rank_candidate_proposals",
        "residual_drop_from_ids",
        "residual_drop_from_ledger_maps",
        "score_cochain_proposal",
        "score_discrete_proposal",
    ),
    "symbol_turn_service": ("SymbolGameExecutionService",),
}
_EXPORTS = {name: module for module, names in _EXPORT_MODULES.items() for name in names}


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(importlib.import_module(f".{module_name}", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))


_EXPORTS.update(
    {
        "AssemblePromptUseCase": "assemble_prompt",
        "EvaluateCertifiedLadderUseCase": "evaluate_certified_ladder",
        "EvaluateWolandGatesUseCase": "evaluate_gates",
        "EvaluatePilotUseCase": "evaluate_pilot",
        "EvaluatePilotSuiteUseCase": "evaluate_pilot_suite",
        "ExecuteStagePipelineUseCase": "execute_stage_pipeline",
        "PipelineExecutionReceipt": "execute_stage_pipeline",
        "RewritePromptUseCase": "rewrite_prompt",
        "RunDemoUseCase": "run_demo",
        "VerifyPfpContractsUseCase": "verify_contracts",
    }
)
__all__ = list(dict.fromkeys([*__all__, *_EXPORTS]))
