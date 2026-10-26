"""Quorum Threshold Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QuorumThreshold:
    """Rigorous mathematical threshold specification for council deliberation voting."""

    total_eligible_members: int = 3
    min_participating_members: int = 2
    required_aye_fraction: float = 0.66

    def __post_init__(self) -> None:
        if self.total_eligible_members <= 0:
            raise ValueError("total_eligible_members must be > 0")
        if self.min_participating_members <= 0 or self.min_participating_members > self.total_eligible_members:
            raise ValueError("min_participating_members must be between 1 and total_eligible_members")
        if self.required_aye_fraction <= 0.5 or self.required_aye_fraction > 1.0:
            raise ValueError("required_aye_fraction must be strictly greater than 0.5 and <= 1.0")
