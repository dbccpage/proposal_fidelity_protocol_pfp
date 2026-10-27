"""Application Use Cases and Swarm Orchestration Layer."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .channel_e_verification import ChannelEVerificationUseCase, E04AdversarialReceipt, E05TamperRejectionReceipt
    from .claim_hygiene_auditor import ClaimHygieneAuditor
    from .deposit_packaging import DepositPackagingService
    from .deposit_preflight import DepositPreflightReceipt, check_paper_deposit_preflight, check_self_consistency
    from .hand_waving_lint import HandWavingLint
    from .paper_generation_pipeline import PaperGenerationPipeline
    from .paper_review_swarm import StageResult, SwarmReviewReceipt, run_stage_0, run_stage_1, run_stage_2, run_stage_3, run_stage_4, run_stage_5, run_stage_6, run_stage_final, run_swarm_review
    from .six_step_harmonization import SixStepHarmonizationEngine
    from .swarm_orchestrator import SwarmOrchestrator
    from .unstated_premise_questions import UnstatedPremiseQuestions
    from .verification_52_gate import Gate52Report, GateItemResult, Verification52Gate, resolve_paper_paths

__all__ = ['SwarmOrchestrator', 'PaperGenerationPipeline', 'SixStepHarmonizationEngine', 'Verification52Gate', 'Gate52Report', 'GateItemResult', 'resolve_paper_paths', 'ChannelEVerificationUseCase', 'E04AdversarialReceipt', 'E05TamperRejectionReceipt', 'ClaimHygieneAuditor', 'HandWavingLint', 'UnstatedPremiseQuestions', 'DepositPackagingService', 'DepositPreflightReceipt', 'check_paper_deposit_preflight', 'check_self_consistency', 'StageResult', 'SwarmReviewReceipt', 'run_stage_0', 'run_stage_1', 'run_stage_2', 'run_stage_3', 'run_stage_4', 'run_stage_5', 'run_stage_6', 'run_stage_final', 'run_swarm_review']

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    'ChannelEVerificationUseCase': ('.channel_e_verification', 'ChannelEVerificationUseCase'),
    'E04AdversarialReceipt': ('.channel_e_verification', 'E04AdversarialReceipt'),
    'E05TamperRejectionReceipt': ('.channel_e_verification', 'E05TamperRejectionReceipt'),
    'ClaimHygieneAuditor': ('.claim_hygiene_auditor', 'ClaimHygieneAuditor'),
    'DepositPackagingService': ('.deposit_packaging', 'DepositPackagingService'),
    'DepositPreflightReceipt': ('.deposit_preflight', 'DepositPreflightReceipt'),
    'check_paper_deposit_preflight': ('.deposit_preflight', 'check_paper_deposit_preflight'),
    'check_self_consistency': ('.deposit_preflight', 'check_self_consistency'),
    'HandWavingLint': ('.hand_waving_lint', 'HandWavingLint'),
    'PaperGenerationPipeline': ('.paper_generation_pipeline', 'PaperGenerationPipeline'),
    'StageResult': ('.paper_review_swarm', 'StageResult'),
    'SwarmReviewReceipt': ('.paper_review_swarm', 'SwarmReviewReceipt'),
    'run_stage_0': ('.paper_review_swarm', 'run_stage_0'),
    'run_stage_1': ('.paper_review_swarm', 'run_stage_1'),
    'run_stage_2': ('.paper_review_swarm', 'run_stage_2'),
    'run_stage_3': ('.paper_review_swarm', 'run_stage_3'),
    'run_stage_4': ('.paper_review_swarm', 'run_stage_4'),
    'run_stage_5': ('.paper_review_swarm', 'run_stage_5'),
    'run_stage_6': ('.paper_review_swarm', 'run_stage_6'),
    'run_stage_final': ('.paper_review_swarm', 'run_stage_final'),
    'run_swarm_review': ('.paper_review_swarm', 'run_swarm_review'),
    'SixStepHarmonizationEngine': ('.six_step_harmonization', 'SixStepHarmonizationEngine'),
    'SwarmOrchestrator': ('.swarm_orchestrator', 'SwarmOrchestrator'),
    'UnstatedPremiseQuestions': ('.unstated_premise_questions', 'UnstatedPremiseQuestions'),
    'Gate52Report': ('.verification_52_gate', 'Gate52Report'),
    'GateItemResult': ('.verification_52_gate', 'GateItemResult'),
    'Verification52Gate': ('.verification_52_gate', 'Verification52Gate'),
    'resolve_paper_paths': ('.verification_52_gate', 'resolve_paper_paths'),
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
