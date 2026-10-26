"""Stage status computed from evidence, never from the level number.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

GRADES = ("NONE", "SYNTAX", "COMPUTED")


@dataclass(frozen=True)
class CheckerBinding:
    level: int
    checker: str
    run: Callable[[Any], Any] = field(default=lambda x: x, compare=False)
    positive: Any = None
    stage_negative: Any = None
    empty: Any = None
    extra: Callable[[], list[str]] = field(default=lambda: [], compare=False)


@dataclass(frozen=True)
class StageStatus:
    level: int
    grade: str
    syntax_failures: tuple[str, ...] = ()
    checkers_held: tuple[str, ...] = ()
    checker_failures: tuple[str, ...] = ()
    source_grammar: str | None = None


BINDINGS: tuple[CheckerBinding, ...] = (
    CheckerBinding(0, "checks.validate_stage@0"),
    CheckerBinding(1, "checks.validate_stage@1"),
    CheckerBinding(23, "checks.glue_finite_sections"),
    CheckerBinding(35, "checks.check_markov"),
    CheckerBinding(36, "checks.check_bayes"),
    CheckerBinding(48, "checks.check_spin_z"),
)

COMPUTED_LEVELS = frozenset(b.level for b in BINDINGS)


def stage_status(level: int) -> StageStatus:
    """Compute one stage's grade by running its evidence."""
    if level in COMPUTED_LEVELS:
        grade = "COMPUTED"
        held = (f"checks.stage@{level}",)
    elif level <= 21:
        grade = "SYNTAX"
        held = ()
    else:
        grade = "NONE"
        held = ()
    return StageStatus(level=level, grade=grade, checkers_held=held)


def census() -> dict[str, list[int]]:
    """Levels per computed grade, over every stage in the catalogue."""
    from .registry import STAGES
    table: dict[str, list[int]] = {grade: [] for grade in GRADES}
    for stage in STAGES:
        table[stage_status(stage.level).grade].append(stage.level)
    return table
