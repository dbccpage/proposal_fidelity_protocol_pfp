"""Kinetic Proofreading Delay Engine (U16).

Enforces Hopfield-Ninio kinetic delay: candidate defects must persist across
tau observation steps before triggering permanent quarantine or punitive rollback.

AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class KineticProofreader:
    """Delays irreversible immune actions until signal persists over tau steps."""

    required_delay_steps: int = 2
    observations: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.required_delay_steps, int) or self.required_delay_steps < 1:
            raise ValueError("required_delay_steps must be integer >= 1")

    def record_observation(self, finding_id: str) -> bool:
        """Record an occurrence. Returns True iff the finding has persisted >= required_delay_steps."""
        current = self.observations.get(finding_id, 0) + 1
        self.observations[finding_id] = current
        return current >= self.required_delay_steps

    def dissociate(self, finding_id: str) -> None:
        self.observations.pop(finding_id, None)

    def is_confirmed(self, finding_id: str) -> bool:
        return self.observations.get(finding_id, 0) >= self.required_delay_steps
