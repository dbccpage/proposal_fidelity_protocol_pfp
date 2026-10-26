"""Budget gate and model admission for C041 (Lean 4 Proofs of Hidden Finite Lemmas).

AuthorityEffect: None.

All amounts are integer micro-USD. Configured limits: a target of 50,000
micro-USD and a hard ceiling of 1,000,000 micro-USD (Tier T3). Models are
admitted through ``ModelRegistry.admit_under_ceiling`` (open weights, at most
the registry's 70B ceiling), and ``allow_fallbacks`` must be false (SG-CP v1 §2).

Pre-call admission quotes the call with ``PriceTable.quote`` and charges the
quoted maximum with ``BudgetController.charge`` before the call, failing closed
with ``BudgetExceeded``. The controller has no settlement or refund operation,
so post-call settlement is refused with ``BudgetGateUnavailable`` instead of
being approximated.
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

CHALLENGE_ID = "c041_lean4_finite_lemma_proofs"
TARGET_BUDGET_MICROUSD: int = 50_000
HARD_CEILING_MICROUSD: int = 1_000_000
MODEL_PARAMETER_CEILING: int = OPEN_WEIGHT_CEILING_PARAMETERS
FALLBACK_NOT_ALLOWED: str = "MODEL_FALLBACK_NOT_ALLOWED"
POST_CALL_SETTLEMENT_UNAVAILABLE: str = "POST_CALL_SETTLEMENT_UNAVAILABLE"


class FallbackNotAllowedError(ModelNotAllowed):
    """Raised when allow_fallbacks is enabled contrary to SG-CP v1 protocol."""

    def __init__(self, message: str = "allow_fallbacks must be False under SG-CP v1 (§2)") -> None:
        self.code = FALLBACK_NOT_ALLOWED
        super().__init__(f"{FALLBACK_NOT_ALLOWED}: {message}")


class BudgetCeilingExceededError(ValueError):
    """Raised when a budget configuration declares a ceiling higher than the hard limit."""


class BudgetGateUnavailable(RuntimeError):
    """A budget operation that the provider budget API does not support; refused instead of approximated."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class C041BudgetGate:
    """Fail-closed pre-call budget and model gate for C041."""

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
                f"ceiling_microusd={ceiling_microusd} exceeds hard ceiling {HARD_CEILING_MICROUSD} micro-USD"
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
        self.receipts: list[BudgetReceipt] = []

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
    def is_within_target(self) -> bool:
        return self.spent_microusd <= self.target_microusd

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
        """Admit an open-weight model within the parameter ceiling; refuse fallbacks."""
        if allow_fallbacks is not False:
            raise FallbackNotAllowedError(
                f"allow_fallbacks is {allow_fallbacks!r}; SG-CP v1 mandates allow_fallbacks: false"
            )
        if type(provider) is str:
            provider_enum = Provider(provider.lower())
        elif type(provider) is Provider:
            provider_enum = provider
        else:
            raise TypeError(
                f"provider must be a Provider or its string value; got {type(provider).__name__}"
            )
        return self.registry.admit_under_ceiling(
            provider_enum,
            model_id,
            ceiling_parameters=MODEL_PARAMETER_CEILING,
        )

    def authorize_pre_call(
        self,
        provider: Provider | str,
        model_id: str,
        input_tokens: int,
        projected_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        *,
        allow_fallbacks: bool = False,
        at_utc: str | None = None,
    ) -> PriceQuoteV1:
        """Quote the call and charge the quoted maximum before it runs; refuse if it would exceed the ceiling."""
        self.validate_model(provider, model_id, allow_fallbacks=allow_fallbacks)
        if type(input_tokens) is not int or input_tokens < 0:
            raise ValueError("input_tokens must be a non-negative integer")
        if type(projected_output_tokens) is not int or projected_output_tokens < 0:
            raise ValueError("projected_output_tokens must be a non-negative integer")
        quote = self.price_table.quote(
            model_id,
            input_tokens,
            projected_output_tokens,
            at_utc=at_utc if at_utc is not None else utc_now(),
        )
        projected_total = self.spent_microusd + quote.cost_microusd
        if projected_total > self.limit_microusd:
            raise BudgetExceeded(requested=projected_total, limit=self.limit_microusd)
        self.receipts.append(self.controller.charge(model_id, quote))
        return quote

    def record_post_call(
        self,
        quote: PriceQuoteV1,
        actual_input_tokens: int,
        actual_output_tokens: int,
    ) -> BudgetReceipt:
        """Refused: the budget controller has no settlement API; the pre-call charge is the recorded cost."""
        raise BudgetGateUnavailable(
            POST_CALL_SETTLEMENT_UNAVAILABLE,
            "BudgetController has no settlement or refund operation; the quoted maximum charged by "
            "authorize_pre_call is the recorded cost. Settle through the governed provider gateway.",
        )

    def get_summary(self) -> dict[str, Any]:
        """Budget accounting in integer micro-USD."""
        return {
            "authority_effect": self.authority_effect,
            "call_count": len(self.receipts),
            "ceiling_microusd": self.ceiling_microusd,
            "challenge_id": CHALLENGE_ID,
            "remaining_microusd": self.remaining_microusd,
            "spent_microusd": self.spent_microusd,
            "target_microusd": self.target_microusd,
            "within_target": self.is_within_target,
        }
