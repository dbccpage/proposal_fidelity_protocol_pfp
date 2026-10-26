"""Exact Allosteric Quorum Gate with Integer Hill Coefficient (U16/U20).

H(theta) = theta^n / (Kd^n + theta^n)
Evaluated over exact Fraction arithmetic. Zero floating-point operations.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any


def _assert_zero_float(val: Any, field_name: str) -> None:
    if isinstance(val, float):
        raise TypeError(
            f"ZERO-FLOAT Invariant violated on {field_name}: float values are strictly forbidden; "
            "use fractions.Fraction"
        )


class QuorumState(str, Enum):
    QUIESCENT = "QUIESCENT"
    INDETERMINATE = "INDETERMINATE"
    ACTIVE = "ACTIVE"


@dataclass(frozen=True, slots=True)
class AllostericQuorumGate:
    """Exact rational sigmoidal quorum gate."""

    hill_coefficient: int = 4  # n >= 1
    kd: int = 2               # Kd >= 1
    quiescent_ceiling: Fraction = Fraction(1, 4)
    active_floor: Fraction = Fraction(3, 4)

    def __post_init__(self) -> None:
        if not isinstance(self.hill_coefficient, int) or isinstance(self.hill_coefficient, bool) or self.hill_coefficient < 1:
            raise ValueError("hill_coefficient n must be integer >= 1")
        if not isinstance(self.kd, int) or isinstance(self.kd, bool) or self.kd < 1:
            raise ValueError("kd must be integer >= 1")
        _assert_zero_float(self.quiescent_ceiling, "quiescent_ceiling")
        _assert_zero_float(self.active_floor, "active_floor")

    def compute_response(self, theta: int) -> Fraction:
        """H(theta) = theta^n / (Kd^n + theta^n)."""
        if not isinstance(theta, int) or isinstance(theta, bool) or theta < 0:
            raise ValueError("theta must be a non-negative integer")
        if theta == 0:
            return Fraction(0, 1)
        theta_n = theta ** self.hill_coefficient
        kd_n = self.kd ** self.hill_coefficient
        return Fraction(theta_n, kd_n + theta_n)

    def evaluate(self, theta: int) -> tuple[QuorumState, Fraction]:
        resp = self.compute_response(theta)
        if resp <= self.quiescent_ceiling:
            state = QuorumState.QUIESCENT
        elif resp >= self.active_floor:
            state = QuorumState.ACTIVE
        else:
            state = QuorumState.INDETERMINATE
        return state, resp
