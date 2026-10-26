"""Budget Gate and Model Registry Governance for C011 (Cycle-Rank Ladder: Minimum-L1 Coboundary Repair).

AuthorityEffect: None.

Enforces:
1. Pre-call fail-closed budget checks via BudgetController (in micro-USD):
   - Target: < $0.05 (50,000 micro-USD)
   - Hard Ceiling: <= $0.50 (500,000 micro-USD) [Tier T2]
   - Raises BudgetExceeded before execution if projected cost exceeds limit.
2. Model parameter ceiling <= 70B open weights via ModelRegistry.
3. Strict allow_fallbacks: false mandate under SG-CP v1 (§2).
"""

from __future__ import annotations

from typing import Any

from omega_engine_woland.domain.providers.budget import (
    DEFAULT_MAX_OUTPUT_TOKENS,
    BudgetController,
    PriceQuoteV1,
    PriceTable,
    utc_now,
)
from omega_engine_woland.domain.providers.model_registry import (
    OPEN_WEIGHT_CEILING_PARAMETERS,
    ModelNotAllowed,
    ModelRegistry,
    ModelSpecV1,
)
from omega_engine_woland.domain.providers.types import (
    BudgetExceeded,
    BudgetReceipt,
    Provider,
)

TARGET_BUDGET_USD: float = 0.05
HARD_CEILING_USD: float = 0.50
TARGET_BUDGET_MICROUSD: int = 50_000
HARD_CEILING_MICROUSD: int = 500_000
MODEL_PARAMETER_CEILING: int = OPEN_WEIGHT_CEILING_PARAMETERS  # 70B
FALLBACK_NOT_ALLOWED: str = "MODEL_FALLBACK_NOT_ALLOWED"


class FallbackNotAllowedError(ModelNotAllowed):
    """Raised when allow_fallbacks is enabled contrary to SG-CP v1 protocol."""

    def __init__(self, message: str = "allow_fallbacks must be False under SG-CP v1 (§2)") -> None:
        self.code = FALLBACK_NOT_ALLOWED
        super().__init__(f"{FALLBACK_NOT_ALLOWED}: {message}")


class BudgetCeilingExceededError(ValueError):
    """Raised when a budget configuration declares a ceiling higher than the hard limit."""


class BudgetGate:
    """Pre-call fail-closed cost controller and model registry admission gate.

    AuthorityEffect: None.
    """

    def __init__(
        self,
        ceiling_microusd: int = HARD_CEILING_MICROUSD,
        target_microusd: int | None = None,
        registry: ModelRegistry | None = None,
        price_table: PriceTable | None = None,
    ) -> None:
        if type(ceiling_microusd) is not int or ceiling_microusd < 0:
            raise ValueError("ceiling_microusd must be a non-negative integer")
        if ceiling_microusd > HARD_CEILING_MICROUSD:
            raise BudgetCeilingExceededError(
                f"Declared ceiling {ceiling_microusd} uUSD (${ceiling_microusd / 1_000_000:.2f}) "
                f"exceeds hard challenge ceiling of {HARD_CEILING_MICROUSD} uUSD (${HARD_CEILING_USD:.2f})"
            )

        effective_target = (
            target_microusd
            if target_microusd is not None
            else min(TARGET_BUDGET_MICROUSD, ceiling_microusd)
        )
        if type(effective_target) is not int or effective_target <= 0:
            raise ValueError("target_microusd must be a positive integer")
        if effective_target > ceiling_microusd:
            raise ValueError("target_microusd cannot exceed ceiling_microusd")

        self.ceiling_microusd: int = ceiling_microusd
        self.target_microusd: int = effective_target
        self.controller: BudgetController = BudgetController(limit_microusd=ceiling_microusd)
        self.registry: ModelRegistry = registry if registry is not None else ModelRegistry.builtin()
        self.price_table: PriceTable = (
            price_table if price_table is not None else PriceTable.builtin()
        )
        self.authority_effect: str = "None"

    @property
    def spent_microusd(self) -> int:
        return self.controller.spent_microusd

    @property
    def remaining_microusd(self) -> int:
        return self.controller.remaining_microusd

    @property
    def limit_microusd(self) -> int:
        return self.controller.limit_microusd

    @property
    def spent_usd(self) -> float:
        return round(self.spent_microusd / 1_000_000, 6)

    @property
    def is_within_target(self) -> bool:
        """Checks if current spend satisfies the optimization target (< $0.05)."""
        return self.spent_microusd < self.target_microusd

    @property
    def is_within_hard_ceiling(self) -> bool:
        """Checks if current spend satisfies the hard ceiling (<= $0.50)."""
        return self.spent_microusd <= self.limit_microusd

    def validate_model(
        self,
        provider: Provider | str,
        model_id: str,
        *,
        allow_fallbacks: bool = False,
    ) -> ModelSpecV1:
        """Validates that model parameters do not exceed 70B and fallbacks are disabled."""
        if allow_fallbacks is not False:
            raise FallbackNotAllowedError(
                f"allow_fallbacks is {allow_fallbacks!r}; SG-CP v1 mandates allow_fallbacks: false"
            )

        provider_enum = Provider(provider.lower()) if isinstance(provider, str) else provider
        if not isinstance(provider_enum, Provider):
            raise TypeError(f"Invalid provider: {provider}")

        return self.registry.admit_under_ceiling(
            provider_enum,
            model_id,
            ceiling_parameters=MODEL_PARAMETER_CEILING,
        )

    def pre_call_check(self, projected_cost_microusd: int) -> None:
        """Verifies fail-closed whether projected cost would exceed the budget limit."""
        if type(projected_cost_microusd) is not int or projected_cost_microusd < 0:
            raise ValueError("projected_cost_microusd must be a non-negative integer")

        projected_total = self.spent_microusd + projected_cost_microusd
        if projected_total > self.limit_microusd:
            raise BudgetExceeded(requested=projected_total, limit=self.limit_microusd)

    def quote_and_charge_pre_call(
        self,
        provider: Provider | str,
        model_id: str,
        input_tokens: int,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        *,
        at_utc: str | None = None,
        allow_fallbacks: bool = False,
    ) -> BudgetReceipt:
        """Quotes request and pre-charges budget fail-closed before execution."""
        self.validate_model(provider, model_id, allow_fallbacks=allow_fallbacks)

        if type(input_tokens) is not int or input_tokens < 0:
            raise ValueError("input_tokens must be a non-negative integer")
        if type(max_output_tokens) is not int or max_output_tokens < 0:
            raise ValueError("max_output_tokens must be a non-negative integer")

        timestamp = at_utc if at_utc is not None else utc_now()
        quote: PriceQuoteV1 = self.price_table.quote(
            model_id,
            input_tokens=input_tokens,
            output_tokens=max_output_tokens,
            at_utc=timestamp,
        )

        self.pre_call_check(quote.cost_microusd)
        return self.controller.charge(model_id, quote)

    def to_accounting_dict(self) -> dict[str, Any]:
        """Emits standard accounting dictionary complying with SG-CP v1 (§3)."""
        return {
            "budget_ceiling_usd": round(self.limit_microusd / 1_000_000, 4),
            "budget_target_usd": round(self.target_microusd / 1_000_000, 4),
            "total_billed_cost_usd": self.spent_usd,
            "spent_microusd": self.spent_microusd,
            "remaining_microusd": self.remaining_microusd,
            "within_budget": self.is_within_hard_ceiling,
            "within_target": self.is_within_target,
            "model_parameter_ceiling": "70B",
            "allow_fallbacks": False,
            "authority_effect": self.authority_effect,
        }
