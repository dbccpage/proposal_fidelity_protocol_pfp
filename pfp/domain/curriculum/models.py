"""Curriculum and ladder domain models (U23).

Defines certified progression ladders, failure frontiers, and fixed-judge invariants.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


class CurriculumException(Exception):
    """Base exception for curriculum domain."""


class JudgeChangedError(CurriculumException):
    """Raised when checker digest changes mid-ladder evaluation."""


@dataclass(frozen=True)
class LevelSummary:
    """Summary of proposer performance at a specific ladder difficulty level."""

    axis_value: int
    trials: int
    passes: int
    pass_rate: str
    passed: bool


@dataclass(frozen=True)
class LadderResult:
    """Result of evaluating a proposer across an ordered difficulty axis."""

    ladder_name: str
    axis_name: str
    checker_digest: str
    frontier_axis_value: int | None
    level_summaries: Sequence[LevelSummary] = field(default_factory=list)
    all_passed: bool = False
    authority_effect: str = "None"
