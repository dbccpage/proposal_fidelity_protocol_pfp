"""Tier T4 budget gate for Challenge C040 (M-Theory Toroidal Cremmer-Julia Scalar Count).

Declares the cost ceiling ($2.00 = 2,000,000 micro-USD), the target
($0.20 = 200,000 micro-USD) and allow_fallbacks: false, and audits a
participant accounting.json against them. Spend is accumulated in exact integer
micro-USD: check_pre_call and record_call_cost take int micro-USD and refuse
float and bool amounts with TypeError. Declared USD limits are converted to
exact micro-USD; a limit that is not a whole number of micro-USD is refused.
The 70B parameter ceiling is recorded here; no model is admitted by this gate.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping


class BudgetCeilingExceededError(RuntimeError):
    """Raised when accumulated or estimated billed inference exceeds the ceiling."""


class FallbackNotAllowedError(RuntimeError):
    """Raised when a fallback provider or model route is attempted."""


class ModelParameterCeilingError(RuntimeError):
    """Raised when candidate model exceeds the 70B parameter ceiling."""


MICROUSD_PER_USD = 1_000_000


def usd_config_to_microusd(name: str, value: object) -> int:
    """Convert a declared USD limit to exact micro-USD.

    int and Fraction are exact. A float is read through its shortest decimal
    representation (0.05 becomes 50,000 micro-USD), which is the literal the
    caller wrote. A value that is not a non-negative whole number of micro-USD
    is refused rather than truncated; booleans and other types are refused.
    """
    if type(value) is int or type(value) is Fraction:
        exact = Fraction(value)
    elif type(value) is float:
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite; got {value!r}")
        exact = Fraction(repr(value))
    else:
        raise TypeError(
            f"{name} must be an int, Fraction or float USD amount; got {type(value).__name__}"
        )
    micro = exact * MICROUSD_PER_USD
    if micro.denominator != 1 or micro < 0:
        raise ValueError(f"{name} must be a non-negative whole number of micro-USD; got {value!r}")
    return int(micro)


def require_microusd(name: str, value: object) -> int:
    """Return an amount in integer micro-USD; floats and bools raise TypeError, negatives ValueError."""
    if type(value) is not int:
        raise TypeError(f"{name} must be an int number of micro-USD; got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{name} must be non-negative; got {value}")
    return value


class BudgetGate:
    """Governance gate enforcing Tier T4 compute bounds."""

    TIER = "T4"
    MAX_CEILING_USD = 2.00
    TARGET_COST_USD = 0.20
    ALLOW_FALLBACKS = False
    MODEL_PARAMETER_CEILING = 70_000_000_000
    MAX_CEILING_MICROUSD = 2_000_000
    TARGET_COST_MICROUSD = 200_000

    def __init__(
        self,
        ceiling_usd: float = 2.00,
        target_usd: float = 0.20,
        allow_fallbacks: bool = False,
        model_parameter_ceiling: int = 70_000_000_000,
    ) -> None:
        ceiling_microusd = usd_config_to_microusd("ceiling_usd", ceiling_usd)
        target_microusd = usd_config_to_microusd("target_usd", target_usd)
        if ceiling_microusd > self.MAX_CEILING_MICROUSD:
            raise BudgetCeilingExceededError(
                f"Declared ceiling {ceiling_microusd} uUSD exceeds Tier T4 max {self.MAX_CEILING_MICROUSD} uUSD"
            )
        if allow_fallbacks is not False:
            raise FallbackNotAllowedError("Fallbacks are strictly disallowed under Tier T4")

        self.ceiling_usd = ceiling_usd
        self.target_usd = target_usd
        self.ceiling_microusd = ceiling_microusd
        self.target_microusd = target_microusd
        self.allow_fallbacks = allow_fallbacks
        self.model_parameter_ceiling = model_parameter_ceiling
        self.accumulated_microusd = 0

    @property
    def accumulated_cost_usd(self) -> Fraction:
        """Recorded spend in USD, exact (micro-USD over 10**6)."""
        return Fraction(self.accumulated_microusd, MICROUSD_PER_USD)

    def check_pre_call(self, estimated_cost_microusd: int) -> None:
        """Fail-closed check before a call; the estimate is an int number of micro-USD."""
        estimate = require_microusd("estimated_cost_microusd", estimated_cost_microusd)
        if self.accumulated_microusd + estimate > self.ceiling_microusd:
            raise BudgetCeilingExceededError(
                f"Call cost {estimate} uUSD would breach ceiling {self.ceiling_microusd} uUSD "
                f"(accumulated: {self.accumulated_microusd} uUSD)"
            )

    def record_call_cost(self, billed_cost_microusd: int) -> None:
        """Record the billed cost of a call as an int number of micro-USD."""
        self.accumulated_microusd += require_microusd("billed_cost_microusd", billed_cost_microusd)

    def audit_accounting_config(self, accounting_data: Mapping[str, Any]) -> dict[str, Any]:
        """Audits participant accounting.json against Tier T4 requirements."""
        tier = accounting_data.get("tier")
        ceiling = accounting_data.get("cost_ceiling_usd")
        target = accounting_data.get("target_cost_usd")
        fallbacks = accounting_data.get("allow_fallbacks")
        model_param = accounting_data.get("model_ceiling_parameters")

        violations = []
        if tier != "T4":
            violations.append(f"Invalid tier: {tier} (expected T4)")
        if ceiling is None or ceiling > self.MAX_CEILING_USD:
            violations.append(f"Ceiling exceeds ${self.MAX_CEILING_USD:.2f}: {ceiling}")
        if target is None or target > self.TARGET_COST_USD:
            violations.append(f"Target exceeds ${self.TARGET_COST_USD:.2f}: {target}")
        if fallbacks is not False:
            violations.append(f"allow_fallbacks must be false, got: {fallbacks}")
        if model_param is not None and model_param > self.MODEL_PARAMETER_CEILING:
            violations.append(
                f"model_ceiling_parameters {model_param} exceeds {self.MODEL_PARAMETER_CEILING}"
            )

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "tier": tier,
            "ceiling_usd": ceiling,
            "target_usd": target,
        }
