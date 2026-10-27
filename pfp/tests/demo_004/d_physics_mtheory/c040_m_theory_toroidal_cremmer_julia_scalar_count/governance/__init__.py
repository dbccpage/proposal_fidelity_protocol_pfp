"""Governance Gates and Protocols for Challenge C040.

AuthorityEffect: None.
"""

from __future__ import annotations

from .budget_gate import (
    BudgetCeilingExceededError,
    BudgetGate,
    FallbackNotAllowedError,
    ModelParameterCeilingError,
)
from .commit_reveal_runner import (
    phase1_commit_judge,
    phase2_freeze_solver,
    phase3_reveal_and_score,
    verify_commitments,
)
from .adversary_gate import AdversaryGate

__all__ = [
    "BudgetCeilingExceededError",
    "BudgetGate",
    "FallbackNotAllowedError",
    "ModelParameterCeilingError",
    "AdversaryGate",
    "phase1_commit_judge",
    "phase2_freeze_solver",
    "phase3_reveal_and_score",
    "verify_commitments",
]
