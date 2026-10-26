"""Idle-run counter for detector rules.

What this module does, and no more:

- `stimulate` records that a rule matched in a screening run: its idle counter
  returns to zero, the rule is active, and `affinity_score` is increased by the
  caller-supplied amount (a tally; nothing in this package reads it).
- `apply_decay` records an unmatched screening run: the idle counter increases
  by one, and the rule is deactivated once the counter reaches
  `half_life_runs`. Despite the field name this is a linear idle limit, not an
  exponential half-life.
- `mutate_rule` derives a child rule with a caller-supplied pattern and the
  same matcher binding; the child must pass the thymus like any new rule.
- `filter_active_repertoire` drops deactivated rules.

Nothing here selects among rules by affinity, and the counter state is only as
durable as the caller makes it: `screen` returns the updated rules so the caller
can persist them.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Sequence

from .value_objects import DetectorRule


class ClonalSelectionEngine:
    """Idle counters for a detector repertoire (see module docstring)."""

    @staticmethod
    def mutate_rule(parent_rule: DetectorRule, mutation_variant: str, new_rule_id: str) -> DetectorRule:
        """A child rule with a new pattern, the parent's matcher binding and generation + 1."""
        return DetectorRule(
            rule_id=new_rule_id,
            target_epitope=parent_rule.target_epitope,
            match_pattern=mutation_variant,
            generation=parent_rule.generation + 1,
            affinity_score=parent_rule.affinity_score,
            half_life_runs=parent_rule.half_life_runs,
            runs_idle=0,
            is_active=True,
            matcher_id=parent_rule.matcher_id,
        )

    @staticmethod
    def stimulate(rule: DetectorRule, affinity_boost: Any = 1) -> DetectorRule:
        """Record a matched run: reset the idle counter and add to the affinity tally."""
        return replace(
            rule,
            affinity_score=rule.affinity_score + affinity_boost,
            runs_idle=0,
            is_active=True,
        )

    @staticmethod
    def apply_decay(rule: DetectorRule) -> DetectorRule:
        """Record an unmatched run: count it, and deactivate at the idle limit."""
        new_idle = rule.runs_idle + 1
        is_active = new_idle < rule.half_life_runs
        return replace(
            rule,
            runs_idle=new_idle,
            is_active=is_active,
        )

    @classmethod
    def filter_active_repertoire(cls, repertoire: Sequence[DetectorRule]) -> Sequence[DetectorRule]:
        """Return only the rules that are still active."""
        return tuple(rule for rule in repertoire if rule.is_active)


class GuardInstance:
    """Guard instance protected against autonomous decay."""

    def __init__(self, initial_active: bool = True) -> None:
        self.is_active = initial_active

    def apply_autonomous_decay(self, elapsed_cycles: int = 0) -> None:
        raise PermissionError("EXTERNAL_EPOCH_DECISION_REQUIRED: Autonomous idle-counter decay cannot flip is_active without epoch decision")


class ClonalSelectorV1:
    """Clonal selector enforcing exact rational affinity boosts and external epoch decisions."""

    def stimulate(self, *, affinity_boost: Any = 1, rule: Any = None) -> Any:
        if isinstance(affinity_boost, float):
            raise TypeError("EXACT_RATIONAL_REQUIRED: Float affinity boost is prohibited")
        return rule

    def create_guard(self, initial_active: bool = True) -> GuardInstance:
        return GuardInstance(initial_active=initial_active)

