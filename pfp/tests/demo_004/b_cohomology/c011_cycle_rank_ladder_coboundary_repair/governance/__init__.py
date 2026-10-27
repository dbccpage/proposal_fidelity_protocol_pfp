"""Governance package for C011 (Cycle-Rank Ladder: Minimum-L1 Coboundary Repair).

AuthorityEffect: None.
"""

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
from .commit_reveal_runner import CommitRevealRunner
from .adversary_gate import (
    RUN_FOLDER_EXISTS,
    TERMINAL_OPEN_RESIDUAL,
    TERMINAL_REFERENCE_SELF_CONSISTENT,
    TERMINAL_REFUSE,
    TERMINAL_VERDICTS,
    RunFolderExistsError,
    AdversaryGate,
    generate_c011_novella,
    persist_adversary_run_bundle,
)

__all__ = [
    "BudgetGate",
    "BudgetCeilingExceededError",
    "FallbackNotAllowedError",
    "FALLBACK_NOT_ALLOWED",
    "HARD_CEILING_USD",
    "HARD_CEILING_MICROUSD",
    "TARGET_BUDGET_USD",
    "TARGET_BUDGET_MICROUSD",
    "MODEL_PARAMETER_CEILING",
    "AdversaryGate",
    "CommitRevealRunner",
    "generate_c011_novella",
    "persist_adversary_run_bundle",
    "RunFolderExistsError",
    "RUN_FOLDER_EXISTS",
    "TERMINAL_REFERENCE_SELF_CONSISTENT",
    "TERMINAL_REFUSE",
    "TERMINAL_OPEN_RESIDUAL",
    "TERMINAL_VERDICTS",
]
