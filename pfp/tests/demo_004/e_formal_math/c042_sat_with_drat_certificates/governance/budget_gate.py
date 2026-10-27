"""Budget gate for C042 SAT Encodings with DRAT Certificates.

AuthorityEffect: None.

Accounting is exact: every amount is an integer number of micro-USD. The limit
and target are read from participant_packet/accounting.json
(``budget_limit_usd``, ``optimization_target_usd``) as exact decimal literals
(the JSON is parsed with ``Decimal``, never through a binary float) and must be
whole micro-USD. Missing configuration is refused, not defaulted. Floats and
booleans are refused wherever an amount is expected. USD values are reported as
exact ``Fraction`` objects.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

from adversary.domain.providers.types import BudgetExceeded

MICROUSD_PER_USD = 1_000_000
BUDGET_CONFIG_INVALID = "BUDGET_CONFIG_INVALID"


class BudgetConfigError(ValueError):
    """The accounting configuration is missing a field or holds an inexact amount."""

    def __init__(self, message: str) -> None:
        self.code = BUDGET_CONFIG_INVALID
        super().__init__(f"{BUDGET_CONFIG_INVALID}: {message}")


def _require_microusd(name: str, value: Any) -> int:
    if type(value) is not int or value < 0:
        raise TypeError(f"{name} must be a non-negative int number of micro-USD; got {value!r}")
    return value


def usd_literal_to_microusd(name: str, value: Any) -> int:
    """Convert an exact USD literal (int or Decimal parsed from JSON) to whole micro-USD; refuse anything else."""
    if type(value) is int:
        exact = Decimal(value)
    elif type(value) is Decimal:
        exact = value
    else:
        raise BudgetConfigError(
            f"{name} must be an exact decimal amount; got {type(value).__name__}"
        )
    micro = exact * MICROUSD_PER_USD
    if micro != micro.to_integral_value() or micro < 0:
        raise BudgetConfigError(f"{name}={value} is not a non-negative whole number of micro-USD")
    return int(micro)


@dataclass(frozen=True)
class BudgetReceipt:
    call_id: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    billed_cost_microusd: int
    timestamp: str

    def __post_init__(self) -> None:
        for name in ("call_id", "model", "timestamp"):
            if type(getattr(self, name)) is not str:
                raise TypeError(f"{name} must be a str")
        for name in ("prompt_tokens", "completion_tokens"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise TypeError(f"{name} must be a non-negative int; got {value!r}")
        _require_microusd("billed_cost_microusd", self.billed_cost_microusd)


class C042BudgetGate:
    """Fail-closed budget checks under SG-CP v1 Tier T2, in integer micro-USD."""

    def __init__(self, accounting_file: Path | None = None) -> None:
        self.accounting_path = accounting_file or (
            Path(__file__).resolve().parent.parent / "participant_packet" / "accounting.json"
        )
        self.config = json.loads(
            self.accounting_path.read_text(encoding="utf-8"), parse_float=Decimal
        )
        for key in ("budget_limit_usd", "optimization_target_usd", "parameter_ceiling"):
            if key not in self.config:
                raise BudgetConfigError(f"{self.accounting_path.name} has no {key!r}")

        self.limit_microusd: int = usd_literal_to_microusd(
            "budget_limit_usd", self.config["budget_limit_usd"]
        )
        self.target_microusd: int = usd_literal_to_microusd(
            "optimization_target_usd", self.config["optimization_target_usd"]
        )
        if self.target_microusd > self.limit_microusd:
            raise BudgetConfigError("optimization_target_usd exceeds budget_limit_usd")
        if type(self.config["parameter_ceiling"]) is not str:
            raise BudgetConfigError("parameter_ceiling must be a string such as '70B'")
        self.parameter_ceiling: str = self.config["parameter_ceiling"]

        self.spent_microusd: int = 0
        self.receipts: list[BudgetReceipt] = []

    @property
    def limit_usd(self) -> Fraction:
        return Fraction(self.limit_microusd, MICROUSD_PER_USD)

    @property
    def target_usd(self) -> Fraction:
        return Fraction(self.target_microusd, MICROUSD_PER_USD)

    def check_pre_call(self, model: str, estimated_cost_microusd: int = 1_000) -> bool:
        """Pre-call check in micro-USD; raises BudgetExceeded if the call could exceed the limit."""
        cost = _require_microusd("estimated_cost_microusd", estimated_cost_microusd)
        projected = self.spent_microusd + cost
        if projected > self.limit_microusd:
            raise BudgetExceeded(requested=projected, limit=self.limit_microusd)
        return True

    def record_call(self, receipt: BudgetReceipt) -> None:
        """Record a billed call; refuses (without recording) a call that would exceed the limit."""
        if type(receipt) is not BudgetReceipt:
            raise TypeError("receipt must be exactly BudgetReceipt")
        projected = self.spent_microusd + receipt.billed_cost_microusd
        if projected > self.limit_microusd:
            raise BudgetExceeded(requested=projected, limit=self.limit_microusd)
        self.spent_microusd = projected
        self.receipts.append(receipt)

    def total_spent_microusd(self) -> int:
        return self.spent_microusd

    def total_spent_usd(self) -> Fraction:
        return Fraction(self.spent_microusd, MICROUSD_PER_USD)
