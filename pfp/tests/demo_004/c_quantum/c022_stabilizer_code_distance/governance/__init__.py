"""Governance package for C022 (Stabilizer Code Distance): budget gate, reference self-consistency gate, runner.

AuthorityEffect: None.
"""

from __future__ import annotations

from .budget_gate import (
    FALLBACK_NOT_ALLOWED,
    HARD_CEILING_MICROUSD,
    HARD_CEILING_USD,
    MODEL_PARAMETER_CEILING,
    TARGET_BUDGET_MICROUSD,
    TARGET_BUDGET_USD,
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
)
from .commit_reveal_runner import (
    CommitRevealRunner,
    ManifestCustodyError,
    run_commit_reveal_pipeline,
    run_phase1_judge_commitment,
    run_phase2_freeze_record,
    run_phase3_reveal_and_score,
)
from .woland_gate import (
    GATE_SCOPE,
    RUN_FOLDER_EXISTS,
    TERMINAL_OPEN_RESIDUAL,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    TERMINAL_VERDICTS,
    RunFolderExistsError,
    WolandGate,
    persist_woland_run_bundle,
)

__all__ = [
    "BudgetCeilingExceededError",
    "BudgetGate",
    "CommitRevealRunner",
    "FALLBACK_NOT_ALLOWED",
    "FallbackNotAllowedError",
    "GATE_SCOPE",
    "HARD_CEILING_MICROUSD",
    "HARD_CEILING_USD",
    "MODEL_PARAMETER_CEILING",
    "ManifestCustodyError",
    "RUN_FOLDER_EXISTS",
    "RunFolderExistsError",
    "TARGET_BUDGET_MICROUSD",
    "TARGET_BUDGET_USD",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_VERDICTS",
    "WolandGate",
    "persist_woland_run_bundle",
    "run_commit_reveal_pipeline",
    "run_phase1_judge_commitment",
    "run_phase2_freeze_record",
    "run_phase3_reveal_and_score",
]
