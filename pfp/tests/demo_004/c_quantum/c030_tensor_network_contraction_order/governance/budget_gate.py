# AuthorityEffect: None.
"""Budget Gate and Model Registry Governance for C030 (Tensor-Network Contraction Order).

Enforces:
1. Pre-call fail-closed budget checks via BudgetController (in micro-USD):
   - Target: < $0.05 (50,000 micro-USD)
   - Hard Ceiling: <= $1.00 (1,000,000 micro-USD for Tier T3)
   - Raises BudgetExceeded before execution if projected cost exceeds limit.
2. Model parameter ceiling <= 70B open weights via ModelRegistry.
3. Strict allow_fallbacks: false mandate under SG-CP v1 (§2).
"""

from __future__ import annotations

from typing import NoReturn

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
    Provider,
)

TARGET_BUDGET_USD: float = 0.05
HARD_CEILING_USD: float = 1.00
TARGET_BUDGET_MICROUSD: int = 50_000
HARD_CEILING_MICROUSD: int = 1_000_000
MODEL_PARAMETER_CEILING: int = OPEN_WEIGHT_CEILING_PARAMETERS  # 70B
FALLBACK_NOT_ALLOWED: str = "MODEL_FALLBACK_NOT_ALLOWED"
BUDGET_GATE_UNAVAILABLE: str = "BUDGET_GATE_UNAVAILABLE"


class FallbackNotAllowedError(ModelNotAllowed):
    """Raised when allow_fallbacks is enabled contrary to SG-CP v1 protocol."""

    def __init__(self, message: str = "allow_fallbacks must be False under SG-CP v1 (§2)") -> None:
        self.code = FALLBACK_NOT_ALLOWED
        super().__init__(f"{FALLBACK_NOT_ALLOWED}: {message}")


class BudgetCeilingExceededError(ValueError):
    """Raised when a budget configuration declares a ceiling higher than the hard limit."""


class BudgetGateUnavailable(RuntimeError):
    """A budget operation with no counterpart in omega_engine_providers; it fails closed."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class C030BudgetGate:
    """Fail-closed pre-call budget and model gate for C030."""

    def __init__(
        self,
        ceiling_microusd: int = HARD_CEILING_MICROUSD,
        target_microusd: int | None = None,
        registry: ModelRegistry | None = None,
        price_table: PriceTable | None = None,
    ) -> None:
        if type(ceiling_microusd) is not int or ceiling_microusd <= 0:
            raise ValueError("ceiling_microusd must be a positive integer")
        if ceiling_microusd > HARD_CEILING_MICROUSD:
            raise BudgetCeilingExceededError(
                f"ceiling_microusd={ceiling_microusd} exceeds hard ceiling {HARD_CEILING_MICROUSD} ($1.00)"
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
    def current_spend_usd(self) -> float:
        return self.spent_usd

    @property
    def is_within_target(self) -> bool:
        return self.spent_microusd < self.target_microusd

    @property
    def is_within_hard_ceiling(self) -> bool:
        return self.spent_microusd <= self.limit_microusd

    def validate_model(
        self,
        provider: Provider | str,
        model_id: str,
        *,
        allow_fallbacks: bool = False,
    ) -> ModelSpecV1:
        if allow_fallbacks is not False:
            raise FallbackNotAllowedError(
                f"allow_fallbacks is {allow_fallbacks!r}; SG-CP v1 mandates allow_fallbacks: false"
            )

        provider_enum = Provider(provider.lower()) if isinstance(provider, str) else provider
        if not isinstance(provider_enum, Provider):
            raise TypeError(f"Invalid provider: {provider}")

        # Registry admission: open weights and total parameters at most the ceiling, else a typed refusal.
        return self.registry.admit_under_ceiling(
            provider_enum,
            model_id,
            ceiling_parameters=MODEL_PARAMETER_CEILING,
        )

    def pre_call_check(self, projected_cost_microusd: int) -> None:
        """Raise BudgetExceeded before any call if spent + projected would exceed the ceiling."""
        if type(projected_cost_microusd) is not int or projected_cost_microusd < 0:
            raise ValueError("projected_cost_microusd must be a non-negative integer")

        projected_total = self.spent_microusd + projected_cost_microusd
        if projected_total > self.limit_microusd:
            raise BudgetExceeded(requested=projected_total, limit=self.limit_microusd)

    def authorize_pre_call(
        self,
        provider: Provider | str,
        model_id: str,
        input_tokens: int,
        projected_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        *,
        allow_fallbacks: bool = False,
    ) -> PriceQuoteV1:
        """Quote the worst-case cost and reserve it in integer micro-USD before any call."""
        self.validate_model(provider, model_id, allow_fallbacks=allow_fallbacks)
        if type(input_tokens) is not int or input_tokens < 0:
            raise ValueError("input_tokens must be a non-negative integer")
        if type(projected_output_tokens) is not int or projected_output_tokens < 0:
            raise ValueError("projected_output_tokens must be a non-negative integer")

        quote = self.price_table.quote(
            model_id,
            input_tokens=input_tokens,
            output_tokens=projected_output_tokens,
            at_utc=utc_now(),
        )
        self.pre_call_check(quote.cost_microusd)
        self.controller.charge(model_id, quote)
        return quote

    def record_post_call(
        self,
        quote: PriceQuoteV1,
        actual_input_tokens: int,
        actual_output_tokens: int,
    ) -> NoReturn:
        """Fail closed: the provider budget domain has no post-call settlement API.

        The pre-call reservation made by authorize_pre_call stands as the charge.
        (This method previously called price_table.compute_cost_microusd and
        controller.settle_post_call, which do not exist.)
        """
        raise BudgetGateUnavailable(
            BUDGET_GATE_UNAVAILABLE,
            "post-call settlement is not provided by omega_engine_woland.domain.providers.budget.BudgetController; "
            "the pre-call reservation stands",
        )


def make_c030_budget_gate(ceiling_microusd: int = HARD_CEILING_MICROUSD) -> C030BudgetGate:
    return C030BudgetGate(ceiling_microusd=ceiling_microusd)
