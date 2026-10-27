"""Text-only Anthropic campaign transport composed through PFP's existing admission path."""

import json
from dataclasses import dataclass

from operads.domain.autopoiesis.learning import canonical
from operations.domain.rop.result import Err
from pfp.infrastructure.adapters.harness_budget import HarnessBudgetLedger
from adversary.domain.providers.allowlist import ModelAllowlist
from adversary.domain.providers.budget import (
    BudgetController,
    GatewayPolicy,
    PriceTable,
    ModelPricingObservationV1,
    utc_now,
)
from adversary.domain.providers.types import (
    CandidateRequest,
    DecodingParamsV1,
    Provider,
    ProviderError,
)
from adversary.infrastructure.providers.anthropic_messages import (
    AnthropicTransport,
    build_anthropic_body,
    observe_anthropic_usage,
)
from adversary.infrastructure.providers.credential_source import resolve_credential
from adversary.infrastructure.providers.gateway import OearsLlmGateway


@dataclass(frozen=True)
class ModelCall:
    content: str
    status: str
    cost: int
    input_tokens: int
    output_tokens: int
    evidence: str


class RecordedTransport:
    provenance = "live"

    def __init__(self, transport, store, occurrence):
        self.transport, self.store, self.occurrence = transport, store, occurrence

    def maximum_liability(self, *args):
        return self.transport.maximum_liability(*args)

    def dispatch(self, admitted):
        self.store.record(
            self.occurrence + "/admitted",
            {
                "attempt": admitted.attempt_id,
                "request_digest": admitted.request_digest,
                "body": build_anthropic_body(
                    admitted.request, model=admitted.model, max_tokens=admitted.max_output_tokens
                ),
                "reservation": admitted.receipt.to_dict(),
            },
        )
        try:
            raw = self.transport.dispatch(admitted)
        except ProviderError as exc:
            raw = getattr(exc, "reply_bytes", b"") or b""
            self.store.record(
                self.occurrence + "/transport-failure",
                {
                    "code": getattr(exc, "code", "PROVIDER_ERROR"),
                    "raw": self.store.put(raw),
                    "attempt": admitted.attempt_id,
                },
            )
            # A transport refusal can still contain identifiable billed usage.
            # Let the common completion service bind that usage to the attempt;
            # the caller below retains the transport-refusal outcome.
            try:
                observe_anthropic_usage(json.loads(raw), model=admitted.model)
            except (ValueError, TypeError, UnicodeError):
                raise exc
            return raw
        self.store.record(
            self.occurrence + "/wire", {"raw": self.store.put(raw), "attempt": admitted.attempt_id}
        )
        return raw


class HarnessProvider:
    def __init__(self, *, spec, store, prices, transport=None, clock=utc_now):
        self.spec, self.store, self.clock = spec, store, clock
        self.prices = PriceTable(
            {m: (ModelPricingObservationV1(**row),) for m, row in prices.items()}
        )
        self.transport = transport

    def call(self, system, user, *, role, phase, occurrence):
        if role not in ("inner", "outer"):
            raise ProviderError("UNKNOWN_CAMPAIGN_ROLE")
        if phase == "retry":
            raise ProviderError("RETRY_REQUIRES_SEPARATELY_REVIEWED_INFRASTRUCTURE_RECEIPT")
        model = self.spec.outer_model if role == "outer" else self.spec.inner_model
        cap = 3000 if role == "outer" else 2000
        request = CandidateRequest(
            system=system,
            user=user,
            decoding=DecodingParamsV1(
                thinking="adaptive", effort="high" if role == "outer" else "medium"
            ),
        )
        body = build_anthropic_body(request, model=model, max_tokens=cap)
        previous = self.store.lookup(occurrence + "/settled")
        admitted = self.store.lookup(occurrence + "/admitted")
        if previous:
            if (
                admitted["body"] != body
                or previous["phase"] != phase
                or previous["budget_id"] != self.spec.budget_id
            ):
                raise ProviderError("ASSIGNED_OCCURRENCE_CHANGED")
            # Resume the same assigned trial; this is never counted as a fresh call.
            self.store.get(previous["raw"])
            return ModelCall(
                previous["content"],
                previous["status"],
                previous["cost"],
                previous["usage"]["input_tokens"],
                previous["usage"]["output_tokens"],
                self.store.put(canonical(previous)),
            )
        if admitted is not None:
            raise ProviderError("ASSIGNED_OCCURRENCE_REQUIRES_RECONCILIATION")
        ledger = HarnessBudgetLedger(self.store.root / "budget.sqlite", spec=self.spec, phase=phase)
        budget = BudgetController(self.spec.ceiling, ledger=ledger, reservation_guard=ledger.guard)
        # Sequential dispatcher: any leftover hold is ambiguous after a restart.
        if budget.pending_attempts():
            raise ProviderError("UNRECONCILED_COST")
        transport = self.transport
        if transport is None:
            credential = resolve_credential(("ANTHROPIC_API_KEY",))
            if isinstance(credential, Err):
                raise ProviderError(credential.error.code)
            transport = AnthropicTransport(api_key=credential.value.value)
        gateway = OearsLlmGateway(
            ModelAllowlist.empty().allow(Provider.ANTHROPIC, model),
            GatewayPolicy(self.prices, budget, cap, pricing_clock=self.clock),
            RecordedTransport(transport, self.store, occurrence),
            Provider.ANTHROPIC,
            model,
        )
        result = gateway.complete_result(request)
        wire = self.store.lookup(occurrence + "/wire")
        if wire is None:
            wire = self.store.lookup(occurrence + "/transport-failure")
        if wire is None:
            code = result.error.code if isinstance(result, Err) else "MISSING_RAW_REPLY"
            raise ProviderError(code)
        raw = self.store.get(wire["raw"])
        try:
            decoded = json.loads(raw)
        except (ValueError, UnicodeError) as exc:
            raise ProviderError("UNRECONCILED_RESPONSE_BYTES") from exc
        usage = observe_anthropic_usage(decoded, model=model)
        attempt = budget.attempt(wire["attempt"])
        if usage.input_tokens > 8000 or usage.output_tokens > cap:
            raise ProviderError("PROVIDER_TOKEN_BOUND_VIOLATION")
        quote = self.prices.quote(
            model, usage.input_tokens, usage.output_tokens, at_utc=self.clock()
        )
        settlement = budget.settle_once(
            usage.generation_id,
            quote.cost_microusd,
            provider="anthropic",
            attempt_id=wire["attempt"],
            precharge_microusd=attempt["receipt"]["cost_microusd"],
        )
        failed_transport = self.store.lookup(occurrence + "/transport-failure") is not None
        status = (
            "TYPED_REFUSAL"
            if failed_transport
            or isinstance(result, Err)
            or decoded.get("stop_reason") == "refusal"
            else "INCOMPLETE"
            if decoded.get("stop_reason") == "max_tokens"
            else "PROVIDER_COMPLETED"
        )
        content = (
            "" if failed_transport or isinstance(result, Err) else result.value.candidate.content
        )
        evidence = self.store.record(
            occurrence + "/settled",
            {
                "raw": wire["raw"],
                "usage": usage.metadata(),
                "settlement": settlement,
                "cost": quote.cost_microusd,
                "status": status,
                "content": content,
                "transport": getattr(transport, "provenance", "unknown"),
                "model": model,
                "budget_id": self.spec.budget_id,
                "phase": phase,
                "input_bytes": len(
                    canonical(build_anthropic_body(request, model=model, max_tokens=cap))
                ),
            },
        )
        return ModelCall(
            content, status, quote.cost_microusd, usage.input_tokens, usage.output_tokens, evidence
        )
