"""Budget gate for C034 (Calabi-Yau Hodge Numbers).

AuthorityEffect: None.

Declares the Tier T2 limits (ceiling $0.50 = 500,000 micro-USD,
target $0.05 = 50,000 micro-USD), the 70B open-weight parameter ceiling and
allow_fallbacks: false (SG-CP v1 section 2), and audits a participant
accounting.json against them. Declared USD limits are converted to exact
micro-USD; a limit that is not a whole number of micro-USD is refused.

check_pre_call and record_usage were written against provider APIs that do not
exist (ModelRegistry.get, BudgetController.quote_cost and
BudgetController.record_spend). They fail closed with BudgetGateUnavailable
(code BUDGET_API_UNAVAILABLE): no call is admitted and no spend is recorded.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any, Mapping, NoReturn

from omega_engine_woland.domain.providers.budget import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    BudgetController,
)
from omega_engine_woland.domain.providers.model_registry import (
    OPEN_WEIGHT_CEILING_PARAMETERS,
    ModelNotAllowed,
    ModelRegistry,
)
from omega_engine_woland.domain.providers.types import Provider

TARGET_BUDGET_USD: float = 0.05
HARD_CEILING_USD: float = 0.50
TARGET_BUDGET_MICROUSD: int = 50_000
HARD_CEILING_MICROUSD: int = 500_000
MODEL_PARAMETER_CEILING: int = OPEN_WEIGHT_CEILING_PARAMETERS  # 70B
FALLBACK_NOT_ALLOWED: str = "MODEL_FALLBACK_NOT_ALLOWED"
MICROUSD_PER_USD: int = 1_000_000
BUDGET_API_UNAVAILABLE: str = "BUDGET_API_UNAVAILABLE"


class FallbackNotAllowedError(ModelNotAllowed):
    """Raised when allow_fallbacks is enabled contrary to SG-CP v1 protocol."""

    def __init__(self, message: str = "allow_fallbacks must be False under SG-CP v1 (§2)") -> None:
        self.code = FALLBACK_NOT_ALLOWED
        super().__init__(f"{FALLBACK_NOT_ALLOWED}: {message}")


class BudgetCeilingExceededError(ValueError):
    """Raised when a budget configuration declares a ceiling higher than the hard limit."""


class BudgetGateUnavailable(RuntimeError):
    """Raised instead of calling a provider API that omega_engine_providers does not offer."""

    def __init__(self, operation: str, missing_api: str) -> None:
        self.code = BUDGET_API_UNAVAILABLE
        self.operation = operation
        self.missing_api = missing_api
        super().__init__(
            f"{BUDGET_API_UNAVAILABLE}: {operation} needs {missing_api}, which omega_engine_providers "
            "does not provide; nothing was admitted or recorded"
        )


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


class BudgetGate:
    """Declared budget limits and accounting audit; the pre-call and usage paths fail closed.

    AuthorityEffect: None.
    """

    def __init__(
        self,
        ceiling_usd: float = HARD_CEILING_USD,
        target_usd: float = TARGET_BUDGET_USD,
        allow_fallbacks: bool = False,
    ) -> None:
        ceiling_microusd = usd_config_to_microusd("ceiling_usd", ceiling_usd)
        target_microusd = usd_config_to_microusd("target_usd", target_usd)
        if ceiling_microusd > HARD_CEILING_MICROUSD:
            raise BudgetCeilingExceededError(
                f"Declared ceiling {ceiling_microusd} uUSD exceeds Tier T2 limit {HARD_CEILING_MICROUSD} uUSD"
            )
        if allow_fallbacks is not False:
            raise FallbackNotAllowedError()

        self.ceiling_usd = ceiling_usd
        self.target_usd = target_usd
        self.ceiling_microusd = ceiling_microusd
        self.target_microusd = target_microusd
        self.allow_fallbacks = False

        self.budget_controller = BudgetController(limit_microusd=self.ceiling_microusd)
        self.model_registry = ModelRegistry()

    def audit_accounting_config(self, accounting_cfg: Mapping[str, Any]) -> dict[str, Any]:
        """Audits an accounting.json configuration against Tier T2 constraints."""
        declared_tier = accounting_cfg.get("tier")
        declared_ceiling = accounting_cfg.get("cost_ceiling_usd")
        declared_target = accounting_cfg.get("target_cost_usd")
        declared_params = accounting_cfg.get("model_ceiling_parameters")
        declared_fallbacks = accounting_cfg.get("allow_fallbacks")

        violations: list[str] = []

        if declared_tier != "T2":
            violations.append(f"tier must be 'T2', got {declared_tier!r}")
        if declared_ceiling is None or float(declared_ceiling) > HARD_CEILING_USD:
            violations.append(f"cost_ceiling_usd {declared_ceiling} exceeds ${HARD_CEILING_USD}")
        if declared_target is None or float(declared_target) > TARGET_BUDGET_USD:
            violations.append(
                f"target_cost_usd {declared_target} exceeds target ${TARGET_BUDGET_USD}"
            )

        # Parameter ceiling check supporting "70B" string or integer
        if declared_params is not None:
            if isinstance(declared_params, str) and declared_params.upper().endswith("B"):
                try:
                    num_b = int(declared_params[:-1])
                    if num_b * 1_000_000_000 > MODEL_PARAMETER_CEILING:
                        violations.append(f"model_ceiling_parameters {declared_params} exceeds 70B")
                except ValueError:
                    violations.append(f"invalid model_ceiling_parameters format: {declared_params}")
            elif int(declared_params) > MODEL_PARAMETER_CEILING:
                violations.append(
                    f"model_ceiling_parameters {declared_params} exceeds {MODEL_PARAMETER_CEILING}"
                )
        else:
            violations.append("model_ceiling_parameters is required")

        if declared_fallbacks is not False:
            violations.append("allow_fallbacks must be strictly False")

        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "tier": declared_tier,
            "ceiling_usd": declared_ceiling,
            "target_usd": declared_target,
            "max_params": declared_params,
        }

    def check_pre_call(
        self,
        model_id: str,
        input_tokens: int,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
    ) -> NoReturn:
        """Refuse: this check relied on ModelRegistry.get and BudgetController.quote_cost.

        Neither exists. Admission in omega_engine_providers needs a provider
        (ModelRegistry.admit_under_ceiling) and a pricing time (PriceTable.quote),
        which this signature does not carry, so no call is admitted.
        """
        raise BudgetGateUnavailable(
            "check_pre_call", "ModelRegistry.get and BudgetController.quote_cost"
        )

    def record_usage(
        self,
        provider: Provider,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> NoReturn:
        """Refuse: this relied on BudgetController.record_spend, which does not exist. Nothing is recorded."""
        raise BudgetGateUnavailable("record_usage", "BudgetController.record_spend")

    @property
    def spent_usd(self) -> Fraction:
        """Spend so far in USD, exact (micro-USD over 10**6)."""
        return Fraction(self.budget_controller.spent_microusd, MICROUSD_PER_USD)

    @property
    def is_within_target(self) -> bool:
        return self.budget_controller.spent_microusd <= self.target_microusd
