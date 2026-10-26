"""Generation cost reconciler for OpenRouter and governed providers (U06).

AuthorityEffect: None.
Queries generation receipts by generation ID, parses exact micro-USD,
reconciles against estimated pre-charges, and updates BudgetController.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
from typing import Any

from omega_engine_woland.domain.providers.budget import BudgetController
from omega_engine_woland.domain.providers.ports import budget_runtime
from omega_engine_woland.domain.providers.types import ProviderConfigError, ProviderError


@dataclass(frozen=True)
class CostReconciliationV1:
    """One cost reconciliation record."""

    generation_id: str
    precharge_micro_usd: int
    response_cost_micro_usd: int | None
    billed_cost_micro_usd: int | None
    delta_micro_usd: int | None
    status: str  # "RECONCILED" | "UNRECONCILED"
    tokens_prompt: int = 0
    tokens_completion: int = 0

    @property
    def billed_cost_usd(self) -> Fraction | None:
        return None if self.billed_cost_micro_usd is None else Fraction(self.billed_cost_micro_usd, 1_000_000)

    @property
    def cost_microusd(self) -> int | None:
        return self.billed_cost_micro_usd


class GenerationReconciler:
    """Reconciles estimated charges against provider generation receipts."""

    def __init__(
        self,
        budget_controller: BudgetController | None = None,
        fetch_generation_fn: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> None:
        self.budget_controller = budget_controller
        self._fetch_fn = fetch_generation_fn
        # Parsing-only reconciliation still uses an atomic identity register.
        self._records = {}

    def parse_micro_usd(self, cost_value: float | str | Decimal | None) -> int | None:
        """Parse cost into exact integer micro-USD, rounding up."""
        if cost_value is None or type(cost_value) not in (int, float, str, Decimal):
            return None
        try:
            return budget_runtime().invoke("parse_cost", cost=str(cost_value))
        except ProviderConfigError:
            raise
        except ValueError:
            return None

    def reconcile(
        self,
        api_payload: dict[str, Any],
        *,
        precharge_micro_usd: int = 0,
        response_cost_micro_usd: int | None = None,
        expected_generation_id: str | None = None,
        provider: str = "openrouter",
        attempt_id: str = "",
    ) -> CostReconciliationV1:
        """Reconcile directly from OpenRouter generation API response payload."""
        data = api_payload.get("data", {}) if type(api_payload) is dict else {}
        data = data if type(data) is dict else {}
        gen_id = data.get("id", "")
        tokens_prompt = data.get("tokens_prompt", 0)
        tokens_completion = data.get("tokens_completion", 0)
        billed_micro_usd = self.parse_micro_usd(data.get("total_cost"))
        valid = (
            type(gen_id) is str and bool(gen_id) and
            (expected_generation_id is None or gen_id == expected_generation_id) and
            all(type(v) is int and v >= 0 for v in (tokens_prompt, tokens_completion, precharge_micro_usd)) and
            (response_cost_micro_usd is None or (type(response_cost_micro_usd) is int and response_cost_micro_usd >= 0))
        )
        if not valid or billed_micro_usd is None:
            return CostReconciliationV1(expected_generation_id or (gen_id if type(gen_id) is str else ""),
                precharge_micro_usd, response_cost_micro_usd, None, None, "UNRECONCILED")
        if self.budget_controller is not None:
            outcome = self.budget_controller.settle_once(gen_id, billed_micro_usd, provider=provider,
                attempt_id=attempt_id, precharge_microusd=precharge_micro_usd)
        else:
            if precharge_micro_usd or attempt_id:
                raise ProviderError("settlement requires the reservation's budget controller")
            outcome = {"delta_microusd": billed_micro_usd}
        record = CostReconciliationV1(
            generation_id=gen_id,
            precharge_micro_usd=precharge_micro_usd,
            response_cost_micro_usd=response_cost_micro_usd,
            billed_cost_micro_usd=billed_micro_usd,
            delta_micro_usd=outcome["delta_microusd"],
            status="RECONCILED",
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
        )
        key = (provider, gen_id)
        if key in self._records and self._records[key] != record:
            raise ProviderError("generation reconciliation conflict")
        self._records[key] = record
        return record

    def reconcile_generation(
        self,
        generation_id: str,
        *,
        precharge_micro_usd: int,
        response_cost_micro_usd: int | None = None,
        provider: str = "openrouter",
        attempt_id: str = "",
    ) -> CostReconciliationV1:
        """Query generation metadata and reconcile against precharge."""
        if not generation_id or not self._fetch_fn:
            return CostReconciliationV1(
                generation_id=generation_id,
                precharge_micro_usd=precharge_micro_usd,
                response_cost_micro_usd=response_cost_micro_usd,
                billed_cost_micro_usd=None,
                delta_micro_usd=None,
                status="UNRECONCILED",
            )

        gen_data = self._fetch_fn(generation_id)
        if type(gen_data) is not dict or "data" not in gen_data:
            return CostReconciliationV1(
                generation_id=generation_id,
                precharge_micro_usd=precharge_micro_usd,
                response_cost_micro_usd=response_cost_micro_usd,
                billed_cost_micro_usd=None,
                delta_micro_usd=None,
                status="UNRECONCILED",
            )

        return self.reconcile(
            gen_data,
            precharge_micro_usd=precharge_micro_usd,
            response_cost_micro_usd=response_cost_micro_usd,
            expected_generation_id=generation_id,
            provider=provider,
            attempt_id=attempt_id,
        )


__all__ = [
    "CostReconciliationV1",
    "GenerationReconciler",
]
