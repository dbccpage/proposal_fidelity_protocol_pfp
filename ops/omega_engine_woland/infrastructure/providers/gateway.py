"""OEARS LLM gateway: allowlist → budget → transport. AuthorityEffect: None."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from omega_engine_operations.domain.rop.result import Err
from omega_engine_woland.domain.providers.allowlist import ModelAllowlist
from omega_engine_woland.domain.providers.budget import (
    BUILTIN_OBSERVED_AT_UTC,
    DEFAULT_BUDGET_MICROUSD,
    DEFAULT_MAX_OUTPUT_TOKENS,
    BudgetController,
    GatewayPolicy,
    PriceTable,
    utc_now,
)
from omega_engine_woland.domain.providers.types import (
    AdmitResult,
    BudgetReceipt,
    CandidateRequest,
    CandidateResponse,
    Provider,
    ProviderConfigError,
    ProviderError,
    ReplyTooLarge,
)
from omega_engine_woland.infrastructure.providers.anthropic_messages import (
    DEFAULT_ANTHROPIC_MODEL,
    build_anthropic_body,
    fixture_anthropic_payload,
    parse_anthropic_response,
    observe_anthropic_usage,
)
from omega_engine_woland.infrastructure.providers.openai_compat import (
    build_openai_compat_body,
    default_model,
    fixture_openai_compat_payload,
    observe_openai_compat_usage,
    parse_openai_compat_response,
)
from omega_engine_woland.infrastructure.providers.wire import decode_reply
from omega_engine_woland.use_cases.providers.completion import CompletionService

RawProviderReply = bytes | bytearray | memoryview
TransportFn = Callable[[Provider, str, CandidateRequest], RawProviderReply]

__all__ = ["OearsLlmGateway", "ReplyTooLarge", "fixture_transport", "enclosing_accounted_gateway"]


def fixture_transport(
    provider: Provider, model: str, request: CandidateRequest
) -> bytes:
    if provider == Provider.ANTHROPIC:
        payload = fixture_anthropic_payload(request, model=model)
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if provider in (
        Provider.OPENAI,
        Provider.GROK,
        Provider.GROQ,
        Provider.LOCAL,
        Provider.OPENROUTER,
        Provider.DEEPSEEK,
        Provider.GEMINI,
        Provider.NVIDIA,
        Provider.FIXTURE,
    ):
        p = provider if provider != Provider.FIXTURE else Provider.OPENAI
        payload = fixture_openai_compat_payload(request, provider=p, model=model)
        return json.dumps(payload, separators=(",", ":")).encode("utf-8")
    raise ProviderConfigError(f"no fixture transport for {provider.value}")


@dataclass
class OearsLlmGateway:
    allowlist: ModelAllowlist
    policy: GatewayPolicy | None
    transport: TransportFn = fixture_transport
    default_provider: Provider = Provider.FIXTURE
    default_model: str = "fixture-model"
    unbudgeted_max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS

    @classmethod
    def builtin(
        cls,
        *,
        budget_microusd: int = DEFAULT_BUDGET_MICROUSD,
        max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS,
        transport: TransportFn | None = None,
    ) -> OearsLlmGateway:
        return cls(
            allowlist=ModelAllowlist.builtin(),
            policy=GatewayPolicy(
                prices=PriceTable.builtin(),
                budget=BudgetController(budget_microusd),
                max_output_tokens=max_output_tokens,
                pricing_clock=(lambda: BUILTIN_OBSERVED_AT_UTC) if transport is None or transport is fixture_transport else utc_now,
            ),
            transport=transport or fixture_transport,
        )

    def admit(
        self,
        provider: Provider,
        model: str,
        request: CandidateRequest,
    ) -> AdmitResult:
        admitted = self._service().admit(provider, model, request)
        return AdmitResult(receipt=admitted.receipt, provider=provider, model=model)

    def _service(self) -> CompletionService:
        transport = self.transport
        def liability(p, m, r, limit, quote):
            if transport is fixture_transport or p == Provider.FIXTURE:
                return quote.cost_microusd
            maximum = getattr(transport, "maximum_liability", None)
            return None if maximum is None or not callable(getattr(transport, "dispatch", None)) else maximum(p, m, r, limit, quote)

        def validate(p, m, r, limit):
            if p == Provider.ANTHROPIC:
                build_anthropic_body(r, model=m, max_tokens=limit)
            else:
                build_openai_compat_body(r, model=m, max_tokens=limit, provider=p)

        def dispatch(admitted):
            send = getattr(transport, "dispatch", None)
            if send is not None:
                return send(admitted)
            return transport(admitted.provider, admitted.model, admitted.request)

        def observe_failure(p, m, decoded):
            if p == Provider.ANTHROPIC:
                return observe_anthropic_usage(decoded, model=m,
                    transport=getattr(transport, "provenance", "custom"))
            if p != Provider.OPENROUTER:
                raise ProviderError("failed-answer usage observation unavailable for this provider")
            label = "fixture" if transport is fixture_transport else getattr(transport, "provenance", "custom")
            return observe_openai_compat_usage(decoded, provider=p, model=m, transport=label)

        return CompletionService(allowlist=self.allowlist, policy=self.policy,
            dispatch=dispatch, decode=self._decode_reply, parse=self._parse,
            new_id=lambda: uuid.uuid4().hex, maximum_liability=liability,
            validate_capabilities=validate, max_output_tokens=self.unbudgeted_max_output_tokens,
            observe_failure=observe_failure)

    def complete_result(self, request: CandidateRequest, *, provider: Provider | None = None, model: str | None = None):
        p = provider or self.default_provider
        m = model or (self.default_model if p == self.default_provider else self._resolve_model(p))
        return self._service().complete(p, m, request)

    def complete(
        self,
        request: CandidateRequest,
        *,
        provider: Provider | None = None,
        model: str | None = None,
    ) -> tuple[CandidateResponse, BudgetReceipt | None]:
        result = self.complete_result(request, provider=provider, model=model)
        if isinstance(result, Err):
            raise result.error.cause
        return result.value.candidate, result.value.admitted.receipt



    @staticmethod
    def _decode_reply(raw: RawProviderReply) -> Mapping[str, Any]:
        """Bound the provider's exact bytes before JSON decoding or parsing.

        The wire body, not the eventual ``content`` field, is the resource being
        admitted.  This rejects whitespace and metadata bombs at the same byte
        boundary and prevents a decoded mapping from masquerading as raw
        evidence.
        """
        return decode_reply(raw)

    def _resolve_model(self, provider: Provider) -> str:
        if provider == Provider.FIXTURE:
            return "fixture-model"
        if provider == Provider.ANTHROPIC:
            return DEFAULT_ANTHROPIC_MODEL
        if provider in (
            Provider.OPENAI,
            Provider.GROK,
            Provider.GROQ,
            Provider.LOCAL,
            Provider.OPENROUTER,
            Provider.DEEPSEEK,
            Provider.GEMINI,
            Provider.NVIDIA,
        ):
            return default_model(provider)
        raise ProviderConfigError(f"no default model for {provider.value}")

    def _parse(
        self, provider: Provider, model: str, raw: Mapping[str, Any]
    ) -> CandidateResponse:
        transport_label = "fixture" if self.transport is fixture_transport else getattr(self.transport, "provenance", "custom")
        if provider == Provider.ANTHROPIC:
            return parse_anthropic_response(
                raw, fallback_model=model, transport=transport_label
            )
        if provider == Provider.FIXTURE:
            resp = parse_openai_compat_response(
                raw,
                provider=Provider.OPENAI,
                fallback_model=model,
                transport=transport_label,
            )
            return CandidateResponse(
                content=resp.content,
                model=resp.model,
                provider=Provider.FIXTURE.value,
                input_tokens=resp.input_tokens,
                output_tokens=resp.output_tokens,
                transport=transport_label,
                generation_id=resp.generation_id,
                cost_usd=resp.cost_usd,
            )
        if provider in (
            Provider.OPENAI,
            Provider.GROK,
            Provider.GROQ,
            Provider.LOCAL,
            Provider.OPENROUTER,
            Provider.DEEPSEEK,
            Provider.GEMINI,
            Provider.NVIDIA,
        ):
            return parse_openai_compat_response(
                raw,
                provider=provider,
                fallback_model=model,
                transport=transport_label,
            )
        raise ProviderError(f"cannot parse provider {provider.value}")


def enclosing_accounted_gateway(gateway: object) -> bool:
    """True for the run's budgeted gateway, or an estimated or durable wrapper."""
    from omega_engine_pfp.infrastructure.estimated_gateway import (
        DurableRunGateway,
        EstimatedBudgetGateway,
    )

    if isinstance(gateway, (DurableRunGateway, EstimatedBudgetGateway)):
        return True
    return isinstance(gateway, OearsLlmGateway) and gateway.policy is not None


def unbudgeted_gateway(*, provider: Provider, model: str, transport, max_output_tokens: int):
    """Explicit caller-selected deployment, with no financial ceiling promise."""
    return OearsLlmGateway(allowlist=ModelAllowlist.empty().allow(provider, model), policy=None,
        transport=transport, default_provider=provider, default_model=model,
        unbudgeted_max_output_tokens=max_output_tokens)
