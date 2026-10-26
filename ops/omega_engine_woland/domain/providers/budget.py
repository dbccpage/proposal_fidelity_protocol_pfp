"""Versioned price observations and fail-closed budgets. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime

from omega_engine_woland.domain.providers.ledger import BudgetLedger, MemoryBudgetLedger
from omega_engine_woland.domain.providers.ports import budget_runtime
from omega_engine_woland.domain.providers.types import (
    BudgetReceipt,
    CandidateRequest,
    ModelNotAllowed,
    ProviderError,
)

MICROUSD_PER_MTOK = 1_000_000
BYTES_PER_TOKEN_ESTIMATE = 3
REQUEST_FRAMING_TOKENS = 8
DEFAULT_BUDGET_MICROUSD = 1_000_000
DEFAULT_BUDGET_LIMIT_MICROUSD = 17_480_000  # Retained legacy benchmark default.
DEFAULT_MAX_OUTPUT_TOKENS = 1_024
PRICING_SCHEMA_V1 = "omega.provider.model-pricing-observation.v1"

# The historical table was introduced by this commit. It is evidence of what
# the repository believed then, not a live-price assertion.
BUILTIN_PRICING_SOURCE = "anomalonpy:6def5ba1b3:omega_engine_providers/domain/budget.py"
BUILTIN_EFFECTIVE_FROM_UTC = "2026-08-20T00:00:00.000000Z"
BUILTIN_OBSERVED_AT_UTC = "2026-08-21T02:48:45.000000Z"
BUILTIN_STALE_AFTER_UTC = "2027-09-21T02:48:45.000000Z"

# OpenRouter's billed cost for meta-llama/llama-3.3-70b-instruct, reconciled per
# generation id in the Q40 synthesis trial. Observed, not published list price.
LLAMA_33_70B_OPENROUTER_PRICING_SOURCE = (
    "the_symbol_game:145c6de8c:omega_engine_projects/mssn_sn_symgam/demos/"
    "demo_q40_quantum_solver/synthesis_trial_receipt.json:reconciled_generation_costs"
)
LLAMA_33_70B_OPENROUTER_OBSERVED_AT_UTC = "2026-09-26T21:48:36.984053Z"
LLAMA_33_70B_OPENROUTER_STALE_AFTER_UTC = "2027-09-26T21:48:36.984053Z"

# Fixture pricing is not an observation about a vendor market and therefore
# remains valid for deterministic replay. Its source says exactly that.
FIXTURE_EFFECTIVE_FROM_UTC = "2000-01-01T00:00:00.000000Z"
FIXTURE_OBSERVED_AT_UTC = "2000-01-01T00:00:00.000000Z"
FIXTURE_STALE_AFTER_UTC = "9999-12-31T23:59:59.999999Z"


class PricingObservationUnavailable(ModelNotAllowed):
    """No usable observation exists at the caller's explicit decision time."""

    def __init__(self, code: str, model: str, at_utc: str) -> None:
        self.code = code
        self.model = model
        self.at_utc = at_utc
        super().__init__(f"{code}:{model}:price unavailable at {at_utc}")


def _native(operation: str, **payload: object) -> object:
    return budget_runtime().invoke(operation, **payload)


def utc_now() -> str:
    return budget_runtime().utc_now()


@dataclass(frozen=True)
class ModelPricingObservationV1:
    """One evidence-bound price observation for one model deployment."""

    model_deployment_id: str
    input_microusd_per_mtok: int
    output_microusd_per_mtok: int
    effective_from_utc: str
    observed_at_utc: str
    stale_after_utc: str
    evidence_digest: str
    schema: str = PRICING_SCHEMA_V1
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.model_deployment_id) is not str or not self.model_deployment_id:
            raise ValueError("model_deployment_id must be a non-empty exact string")
        for name in ("input_microusd_per_mtok", "output_microusd_per_mtok"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ValueError(f"{name} must be a non-negative exact integer")
        timestamps = []
        for name in ("effective_from_utc", "observed_at_utc", "stale_after_utc"):
            value = getattr(self, name)
            if type(value) is not str or re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z", value) is None:
                raise ValueError(f"{name} must be canonical UTC")
            timestamps.append(datetime.fromisoformat(value[:-1] + "+00:00"))
        if not timestamps[0] <= timestamps[1] < timestamps[2]:
            raise ValueError("pricing timestamps must satisfy effective <= observed < stale")
        if type(self.evidence_digest) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", self.evidence_digest) is None:
            raise ValueError("evidence_digest must be a canonical sha256 digest")
        if self.schema != PRICING_SCHEMA_V1 or self.authority_effect != "None":
            raise ValueError("invalid pricing schema or authority effect")

    def to_canonical(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "model_deployment_id": self.model_deployment_id,
            "input_microusd_per_mtok": self.input_microusd_per_mtok,
            "output_microusd_per_mtok": self.output_microusd_per_mtok,
            "effective_from_utc": self.effective_from_utc,
            "observed_at_utc": self.observed_at_utc,
            "stale_after_utc": self.stale_after_utc,
            "evidence_digest": self.evidence_digest,
            "authority_effect": self.authority_effect,
        }

    @property
    def observation_digest(self) -> str:
        wire = json.dumps(self.to_canonical(), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return "sha256:" + hashlib.sha256(wire.encode("ascii")).hexdigest()


@dataclass(frozen=True)
class PriceQuoteV1:
    observation: ModelPricingObservationV1
    cost_microusd: int


def pricing_observation(
    model_deployment_id: str,
    input_microusd_per_mtok: int,
    output_microusd_per_mtok: int,
    *,
    source: str = BUILTIN_PRICING_SOURCE,
    effective_from_utc: str = BUILTIN_EFFECTIVE_FROM_UTC,
    observed_at_utc: str = BUILTIN_OBSERVED_AT_UTC,
    stale_after_utc: str = BUILTIN_STALE_AFTER_UTC,
) -> ModelPricingObservationV1:
    if type(source) is not str or not source:
        raise ValueError("source must be a non-empty exact string")
    evidence_digest = "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest()
    return ModelPricingObservationV1(
        model_deployment_id=model_deployment_id,
        input_microusd_per_mtok=input_microusd_per_mtok,
        output_microusd_per_mtok=output_microusd_per_mtok,
        effective_from_utc=effective_from_utc,
        observed_at_utc=observed_at_utc,
        stale_after_utc=stale_after_utc,
        evidence_digest=evidence_digest,
    )


def fixture_pricing_observation(
    model_deployment_id: str,
    input_microusd_per_mtok: int,
    output_microusd_per_mtok: int,
) -> ModelPricingObservationV1:
    return pricing_observation(
        model_deployment_id,
        input_microusd_per_mtok,
        output_microusd_per_mtok,
        source=f"deterministic-fixture-pricing:{model_deployment_id}:v1",
        effective_from_utc=FIXTURE_EFFECTIVE_FROM_UTC,
        observed_at_utc=FIXTURE_OBSERVED_AT_UTC,
        stale_after_utc=FIXTURE_STALE_AFTER_UTC,
    )


def _leg_cost_microusd(tokens: int, price_per_mtok: int) -> int:
    return _native("leg_cost", tokens=tokens, price=price_per_mtok)


def estimate_input_tokens(request: CandidateRequest) -> int:
    return _native("estimate", payload_bytes=request.estimated_payload_bytes())


class PriceTable:
    def __init__(
        self,
        rows: Mapping[str, Sequence[ModelPricingObservationV1]] | None = None,
    ) -> None:
        admitted: dict[str, tuple[ModelPricingObservationV1, ...]] = {}
        for model, observations in (rows or {}).items():
            if type(model) is not str or not model:
                raise ValueError("price-table keys must be non-empty exact strings")
            values = tuple(observations)
            if not values:
                raise ValueError(f"price-table row {model!r} has no observations")
            if any(
                type(item) is not ModelPricingObservationV1 or item.model_deployment_id != model
                for item in values
            ):
                raise ValueError("price-table observations must exactly match their key")
            admitted[model] = values
        for model, values in admitted.items():
            if len({v.effective_from_utc for v in values}) != len(values):
                raise ValueError("pricing observations cannot share an effective time")
            admitted[model] = tuple(sorted(values, key=lambda v: v.effective_from_utc))
        self._rows = admitted

    @classmethod
    def empty(cls) -> PriceTable:
        return cls({})

    @classmethod
    def builtin(cls) -> PriceTable:
        rows = {
            "claude-sonnet-4-20250514": (3_000_000, 15_000_000),
            "gpt-4o-mini": (150_000, 600_000),
            "openai/gpt-4o-mini": (150_000, 600_000),
            "grok-2-latest": (2_000_000, 10_000_000),
            "llama-3.1-8b-instant": (50_000, 80_000),
            "qwen2.5:0.5b": (0, 0),
            "deepseek/deepseek-v4-flash": (140_000, 280_000),
            "deepseek-v4-flash": (140_000, 280_000),
            "gemini-2.5-flash": (150_000, 600_000),
            "google/gemini-2.5-flash": (150_000, 600_000),
            "meta/llama-3.3-70b-instruct": (0, 0),
            "nvidia/llama-3.1-nemotron-70b-instruct": (0, 0),
            "deepseek-ai/deepseek-r1": (0, 0),
        }
        table = cls.empty()
        for model, (input_price, output_price) in rows.items():
            table = table.with_observation(pricing_observation(model, input_price, output_price))
        # Derived exactly from three reconciled OpenRouter generation costs in the
        # Q40 synthesis receipt: every turn equals $0.10/M input + $0.32/M output.
        table = table.with_observation(
            pricing_observation(
                "meta-llama/llama-3.3-70b-instruct",
                100_000,
                320_000,
                source=LLAMA_33_70B_OPENROUTER_PRICING_SOURCE,
                effective_from_utc=LLAMA_33_70B_OPENROUTER_OBSERVED_AT_UTC,
                observed_at_utc=LLAMA_33_70B_OPENROUTER_OBSERVED_AT_UTC,
                stale_after_utc=LLAMA_33_70B_OPENROUTER_STALE_AFTER_UTC,
            )
        )
        return table.with_observation(fixture_pricing_observation("fixture-model", 1_000, 1_000))

    def with_observation(self, observation: ModelPricingObservationV1) -> PriceTable:
        if type(observation) is not ModelPricingObservationV1:
            raise TypeError("observation must be exactly ModelPricingObservationV1")
        rows = dict(self._rows)
        current = rows.get(observation.model_deployment_id, ())
        rows[observation.model_deployment_id] = (*current, observation)
        return PriceTable(rows)

    def observation_at(self, model: str, *, at_utc: str) -> ModelPricingObservationV1:
        observation = _native(
            "select", model=model, at_utc=at_utc, observations=self._observations()
        )
        return self._original(observation)

    def _observations(self) -> list[dict[str, object]]:
        return [item.to_canonical() for values in self._rows.values() for item in values]

    def _original(self, observation: Mapping[str, object]) -> ModelPricingObservationV1:
        return next(
            item
            for item in self._rows[observation["model_deployment_id"]]
            if item.effective_from_utc == observation["effective_from_utc"]
        )

    def quote(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        *,
        at_utc: str,
    ) -> PriceQuoteV1:
        quote = _native(
            "quote",
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            at_utc=at_utc,
            observations=self._observations(),
        )
        return PriceQuoteV1(self._original(quote["observation"]), quote["cost_microusd"])

    def cost_microusd(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        *,
        at_utc: str = BUILTIN_OBSERVED_AT_UTC,
    ) -> int:
        """Return a historical cost; live admission uses an injected clock."""
        return self.quote(model, input_tokens, output_tokens, at_utc=at_utc).cost_microusd


class BudgetController:
    def __init__(self, limit_microusd: int, *, ledger: BudgetLedger | None = None,
                 reservation_guard: Callable | None = None) -> None:
        _native("state", limit_microusd=limit_microusd, spent_microusd=0)
        self._limit = limit_microusd
        self._ledger = ledger if ledger is not None else MemoryBudgetLedger()
        self._reservation_guard = reservation_guard
        with self._ledger.transaction(self._limit) as state:
            _native("state", limit_microusd=self._limit, spent_microusd=state["spent"])

    @property
    def limit_microusd(self) -> int:
        return self._limit

    @property
    def spent_microusd(self) -> int:
        with self._ledger.transaction(self._limit) as state:
            return state["spent"]

    @property
    def remaining_microusd(self) -> int:
        return _native("state", limit_microusd=self._limit, spent_microusd=self.spent_microusd)[
            "remaining_microusd"
        ]

    def debit_microusd(self, microusd: int) -> int:
        with self._ledger.transaction(self._limit) as state:
            outcome = _native("debit", limit_microusd=self._limit, spent_microusd=state["spent"], cost_microusd=microusd)
            state["spent"] = outcome["spent_microusd"]
            return state["spent"]

    def spend_estimate(self, microusd: int) -> int:
        return self.debit_microusd(microusd)

    def charge(self, model: str, quote: PriceQuoteV1) -> BudgetReceipt:
        with self._ledger.transaction(self._limit) as state:
            return self._charge(state, model, quote)

    def _charge(self, state: dict, model: str, quote: PriceQuoteV1) -> BudgetReceipt:
        if type(quote) is not PriceQuoteV1:
            raise TypeError("quote must be exactly PriceQuoteV1")
        outcome = _native(
            "receipt",
            model=model,
            observation=quote.observation.to_canonical(),
            cost_microusd=quote.cost_microusd,
            limit_microusd=self._limit,
            spent_microusd=state["spent"],
        )
        receipt = BudgetReceipt(**outcome)
        state["spent"] = receipt.spent_after_microusd
        return receipt

    def reserve(self, identity: dict, quote: PriceQuoteV1) -> BudgetReceipt:
        with self._ledger.transaction(self._limit) as state:
            identity = dict(identity)
            if self._reservation_guard is not None:
                self._reservation_guard(state, identity, quote)
            attempt_id = identity["attempt_id"]
            if attempt_id in state["attempts"]:
                raise ProviderError("attempt identity has already been reserved")
            receipt = self._charge(state, identity["model"], quote)
            state["attempts"][attempt_id] = {**identity, "state": "Reserved", "receipt": receipt.to_dict(), "generation_id": ""}
            return receipt

    def record_attempt(self, attempt_id: str, status: str, **evidence: object) -> None:
        allowed = {
            "Reserved": {"Dispatched", "RefusedBeforeDispatch"},
            "Dispatched": {"CompletedPendingSettlement", "OutcomeUnknown"},
            "CompletedPendingSettlement": {"Settled"},
        }
        with self._ledger.transaction(self._limit) as state:
            attempt = state["attempts"][attempt_id]
            if status not in allowed.get(attempt["state"], set()):
                raise ProviderError("invalid provider attempt transition")
            if set(evidence) - {"generation_id", "wire_sha256", "reported_cost_usd"}:
                raise ProviderError("unsupported attempt evidence")
            attempt.update(evidence)
            attempt["state"] = status

    def attempt(self, attempt_id: str) -> dict:
        with self._ledger.transaction(self._limit) as state:
            return deepcopy(state["attempts"][attempt_id])

    def pending_attempts(self) -> tuple[dict, ...]:
        with self._ledger.transaction(self._limit) as state:
            return tuple(deepcopy(a) for a in state["attempts"].values() if a["state"] != "Settled")

    def settle_once(
        self, generation_id: str, billed_microusd: int, *, provider: str = "openrouter",
        attempt_id: str = "", precharge_microusd: int = 0,
    ) -> dict:
        if type(generation_id) is not str or not generation_id or type(provider) is not str or not provider:
            raise ProviderError("settlement requires provider and generation identity")
        for value in (billed_microusd, precharge_microusd):
            if type(value) is not int or value < 0:
                raise ProviderError("settlement costs must be nonnegative exact integers")
        key = json.dumps([provider, generation_id], separators=(",", ":"))
        binding = {"provider": provider, "generation_id": generation_id, "attempt_id": attempt_id,
                   "billed_microusd": billed_microusd, "precharge_microusd": precharge_microusd}
        with self._ledger.transaction(self._limit) as state:
            previous = state["settlements"].get(key)
            if previous is not None:
                if previous["binding"] != binding:
                    raise ProviderError("generation settlement identity or cost conflict")
                return dict(previous["outcome"])
            if attempt_id:
                attempt = state["attempts"].get(attempt_id)
                if attempt is None or attempt["provider"] != provider or attempt["generation_id"] != generation_id:
                    raise ProviderError("generation does not match reserved attempt")
                if attempt["state"] != "CompletedPendingSettlement" or attempt["receipt"]["cost_microusd"] != precharge_microusd:
                    raise ProviderError("reservation cannot be settled in this state")
                if billed_microusd > precharge_microusd:
                    raise ProviderError("billed cost exceeds admitted maximum liability")
            elif precharge_microusd:
                raise ProviderError("precharge requires a bound reservation")
            outcome = _native("settle", limit_microusd=self._limit, spent_microusd=state["spent"],
                              precharge_microusd=precharge_microusd, billed_microusd=billed_microusd)
            state["spent"] = outcome["spent_microusd"]
            state["settlements"][key] = {"binding": binding, "outcome": outcome}
            if attempt_id:
                state["attempts"][attempt_id]["state"] = "Settled"
            return dict(outcome)


class GatewayPolicy:
    def __init__(
        self,
        prices: PriceTable,
        budget: BudgetController,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        *,
        pricing_clock: Callable[[], str] = utc_now,
    ) -> None:
        if type(prices) is not PriceTable:
            raise TypeError("prices must be exactly PriceTable")
        if type(budget) is not BudgetController:
            raise TypeError("budget must be exactly BudgetController")
        if type(max_output_tokens) is not int or max_output_tokens < 0:
            raise ValueError("max_output_tokens must be a non-negative exact integer")
        if not callable(pricing_clock):
            raise TypeError("pricing_clock must be callable")
        self.prices = prices
        self.budget = budget
        self.max_output_tokens = max_output_tokens
        self._pricing_clock = pricing_clock

    def quote_for_request(self, model: str, request: CandidateRequest) -> PriceQuoteV1:
        return self.prices.quote(
            model,
            estimate_input_tokens(request),
            self.max_output_tokens,
            at_utc=self._pricing_clock(),
        )

    def cost_for_request(self, model: str, request: CandidateRequest) -> int:
        return self.quote_for_request(model, request).cost_microusd

    def charge_request(self, model: str, request: CandidateRequest) -> BudgetReceipt:
        return self.budget.charge(model, self.quote_for_request(model, request))
