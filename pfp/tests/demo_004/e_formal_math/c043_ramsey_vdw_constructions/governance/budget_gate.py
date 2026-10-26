"""Budget controller for C043 Ramsey and Van der Waerden Lower-Bound Constructions.

AuthorityEffect: None.

Accounting is exact: every amount is an integer number of micro-USD (default
ceiling 1,000,000, default target 50,000). Floats and booleans are refused
wherever an amount is expected, and a call that would exceed the ceiling is
refused before anything is recorded.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

MICROUSD_PER_USD = 1_000_000


def _require_microusd(name: str, value: Any) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative int number of micro-USD; got {value!r}")
    return value


class BudgetCeilingBreach(RuntimeError):
    """A call would take spending above the ceiling."""

    def __init__(self, message: str) -> None:
        self.code = "BUDGET_CEILING_BREACH"
        super().__init__(f"BUDGET_CEILING_BREACH: {message}")


class BudgetGateC043:
    """Pre-call budget gate preventing spend overruns, in integer micro-USD."""

    def __init__(self, ceiling_microusd: int = 1_000_000, target_microusd: int = 50_000) -> None:
        self.ceiling_microusd = _require_microusd("ceiling_microusd", ceiling_microusd)
        self.target_microusd = _require_microusd("target_microusd", target_microusd)
        if self.target_microusd > self.ceiling_microusd:
            raise ValueError("target_microusd cannot exceed ceiling_microusd")
        self.spent_microusd = 0
        self.call_count = 0

    @property
    def ceiling_usd(self) -> Fraction:
        return Fraction(self.ceiling_microusd, MICROUSD_PER_USD)

    @property
    def target_usd(self) -> Fraction:
        return Fraction(self.target_microusd, MICROUSD_PER_USD)

    @property
    def spent_usd(self) -> Fraction:
        return Fraction(self.spent_microusd, MICROUSD_PER_USD)

    def pre_call_check(self, estimated_cost_microusd: int) -> bool:
        cost = _require_microusd("estimated_cost_microusd", estimated_cost_microusd)
        if self.spent_microusd + cost > self.ceiling_microusd:
            raise BudgetCeilingBreach(
                f"a call of {cost} micro-USD would exceed the ceiling of {self.ceiling_microusd} micro-USD "
                f"(spent {self.spent_microusd})"
            )
        return True

    def record_call(self, cost_microusd: int) -> None:
        cost = _require_microusd("cost_microusd", cost_microusd)
        self.pre_call_check(cost)
        self.spent_microusd += cost
        self.call_count += 1
