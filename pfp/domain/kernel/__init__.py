"""PFP Core Kernel: Ports, Result Monad, and Refusal Codes.

AuthorityEffect: None.
"""

from __future__ import annotations

from .ports import (
    GenesisCycleSolverPort,
    PfpDemoCatalogPort,
    PfpDemoRunnerPort,
    PfpGateEvaluatorPort,
    PfpHostVerifierPort,
    PfpJudgeAuditPort,
    PfpLlmProviderPort,
    PfpSolverPort,
    PfpStoragePort,
)
from .result import (
    DomainError,
    EvaluationVerdict,
    GenesisCycleVerdict,
    RefusalCode,
    Result,
    TerminalStatus,
    collect_results,
    refuse_if,
)

__all__ = [
    "DomainError",
    "EvaluationVerdict",
    "GenesisCycleSolverPort",
    "GenesisCycleVerdict",
    "PfpDemoCatalogPort",
    "PfpDemoRunnerPort",
    "PfpGateEvaluatorPort",
    "PfpHostVerifierPort",
    "PfpJudgeAuditPort",
    "PfpLlmProviderPort",
    "PfpSolverPort",
    "PfpStoragePort",
    "RefusalCode",
    "Result",
    "TerminalStatus",
    "collect_results",
    "refuse_if",
]
