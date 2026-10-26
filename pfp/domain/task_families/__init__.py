"""Task Families module initialization.

AuthorityEffect: None.
"""

from __future__ import annotations

from .task_family_types import (
    DomainCategory,
    EvaluationStrategy,
    GroundTruthProvider,
    InputModality,
    SolutionModality,
    TaskFamilyDefinition,
    TaskFamilyRegister,
)

__all__ = [
    "DomainCategory",
    "EvaluationStrategy",
    "GroundTruthProvider",
    "InputModality",
    "SolutionModality",
    "TaskFamilyDefinition",
    "TaskFamilyRegister",
]
