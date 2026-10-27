"""
model_backends.py — model-agnostic `complete(prompt) -> str` backends for the
head-to-head benchmark. API keys are read from the environment; key **values** are never logged, printed, or committed.

Live OpenRouter requires an injected accounted PFP gateway. Anthropic is an
unsupported legacy route; explicit `mock` remains offline. Select with
`get_backend(provider=...)` or the `SENTINEL_LLM_PROVIDER` environment variable.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence, runtime_checkable
from urllib.error import URLError
from uuid import uuid4

from operations.domain.rop.result import Err
from adversary.domain.providers.types import ProviderError
from adversary.domain.providers.budget import (
    DEFAULT_BUDGET_LIMIT_MICROUSD as DEFAULT_BUDGET_LIMIT_MICROUSD,
)
from adversary.infrastructure.providers.credential_source import resolve_credential
from adversary.infrastructure.providers.openai_compat import OPENROUTER_BASE_URL


@runtime_checkable
class Backend(Protocol):
    name: str

    def complete(self, prompt: str) -> str: ...


class MockBackend:
    """Deterministic offline backend. Returns a fixed verdict word (for pipeline tests)."""

    def __init__(self, answer: str = "CONSISTENT") -> None:
        self._answer = answer
        self.name = f"mock:{answer}"
        self.call_history: list[OpenRouterReceipt] = []

    def complete(self, prompt: str) -> str:  # noqa: ARG002 - deterministic
        return self._answer

    def complete_with_receipt(self, prompt: str | list[dict[str, str]]) -> OpenRouterReceipt:
        text = json.dumps(prompt) if isinstance(prompt, list) else prompt
        p_tok = len(text) // 4
        c_tok = len(self._answer) // 4
        receipt = OpenRouterReceipt(
            content=self._answer,
            model="mock-model",
            generation_id=f"mock-gen-{len(self.call_history) + 1}",
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            total_tokens=p_tok + c_tok,
            cost_usd=0.0001,
            raw_usage={
                "prompt_tokens": p_tok,
                "completion_tokens": c_tok,
                "total_tokens": p_tok + c_tok,
            },
        )
        self.call_history.append(receipt)
        return receipt


class AnthropicBackend:
    """Retained public name for an unsupported direct live route."""

    def __init__(
        self, model: str = "claude-sonnet-5", max_tokens: int = 2048, style: str = "direct"
    ) -> None:
        from adversary.domain.providers.types import ProviderConfigError
        self.model, self.max_tokens, self.style = model, max_tokens, style
        self.name = f"anthropic:{model}:{style}"
        raise ProviderConfigError("ANTHROPIC_LIVE_UNSUPPORTED: use an accounted OpenRouter PFP gateway")

    def complete(self, prompt: str) -> str:
        from adversary.domain.providers.types import ProviderConfigError
        raise ProviderConfigError("ANTHROPIC_LIVE_UNSUPPORTED: use an accounted OpenRouter PFP gateway")


def _optional_float(value: object) -> float | None:
    """Read a provider-reported cost; invalid values refuse rather than become zero."""
    from adversary.infrastructure.providers.wire import reported_cost
    return reported_cost(value)


COST_PROVIDER_REPORTED = "provider_reported"
COST_UNREPORTED = "unreported"


@dataclass(frozen=True)
class OpenRouterReceipt:
    """One completion's usage. ``cost_usd`` is None when the provider reported no cost.

    An unreported cost is unknown, not zero: budget checks must treat it as
    unbounded spend (fail closed) or reconcile it through the generation endpoint.
    """

    content: str
    model: str
    generation_id: str
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    cost_usd: float | None
    raw_usage: dict[str, object] = field(default_factory=dict)
    cost_status: str = COST_PROVIDER_REPORTED


# Cheap OpenRouter default. Same model as bench/matrix Phase-1. Override with
# OPENROUTER_MODEL or get_backend(..., model=...).
CHEAP_OPENROUTER_MODEL = "openai/gpt-4o-mini"


DEFAULT_CASCADE_MODELS: tuple[str, ...] = (
    "stealth/space-bunny-alpha",
    "thudm/glm-5.3",
    "nvidia/nemotron-4-340b-instruct",
)



def resolve_openrouter_api_key(explicit_key: str | None = None) -> str:
    """The caller's explicit key, else the canonical `credential_source` resolution."""
    if explicit_key is not None:
        if not isinstance(explicit_key, str) or not explicit_key.strip():
            raise KeyError("OPENROUTER_API_KEY")
        return explicit_key
    found = resolve_credential(["OPENROUTER_API_KEY"], missing_code="OPENROUTER_KEY_MISSING")
    if isinstance(found, Err):
        raise KeyError("OPENROUTER_API_KEY")
    return found.value.value


class OpenRouterBackend:
    """Compatibility facade over the existing accounted PFP turn boundary.

    ``api_key`` is retained for explicit generation-cost lookup only. Chat
    credentials, transport, continuing allowance and raw custody belong to the
    injected gateway. Rejected replies remain in history, never usable returns.
    """

    def __init__(
        self,
        model: str | None = None,
        models: Sequence[str] | None = None,
        max_tokens: int = 2048,
        style: str = "direct",
        api_key: str | None = None,
        budget_controller: Any | None = None,
        *,
        gateway=None,
        temperature: float | None = None,
    ) -> None:
        if gateway is not None:
            from pfp.infrastructure.estimated_gateway import (
                DurableRunGateway,
                EstimatedBudgetGateway,
            )
            from adversary.domain.providers.types import ProviderConfigError
            if not isinstance(gateway, (EstimatedBudgetGateway, DurableRunGateway)):
                raise ProviderConfigError("PFP_ACCOUNTED_GATEWAY_REQUIRED")
        self._api_key = api_key
        self.gateway, self.temperature = gateway, temperature
        self._run_id = uuid4().hex
        if models:
            self.cascade_models = tuple(models)
            self.model = self.cascade_models[0]
        elif model:
            self.cascade_models = (model,)
            self.model = model
        else:
            default_env_models = os.environ.get("OPENROUTER_CASCADE_MODELS")
            if default_env_models:
                self.cascade_models = tuple(m.strip() for m in default_env_models.split(",") if m.strip())
                self.model = self.cascade_models[0]
            else:
                default_env_model = os.environ.get("OPENROUTER_MODEL")
                if default_env_model:
                    self.cascade_models = (default_env_model,)
                    self.model = default_env_model
                else:
                    self.cascade_models = (CHEAP_OPENROUTER_MODEL,)
                    self.model = CHEAP_OPENROUTER_MODEL

        self.max_tokens = max_tokens
        self.style = style
        self.name = f"openrouter:{self.model}:{style}"
        self.call_history: list[OpenRouterReceipt] = []
        self.last_receipt: OpenRouterReceipt | None = None
        self.budget_controller = budget_controller
        self.last_turn: dict | None = None
        self.turn_history: list[dict] = []

    def complete_with_receipt(self, prompt: str | list[dict[str, str]]) -> OpenRouterReceipt:
        from adversary.domain.providers.types import (
            BudgetExceeded,
            ProviderConfigError,
            ProviderError,
        )

        # A post-hoc debit cannot enforce a caller's maximum billed spend.
        if self.budget_controller is not None and self.budget_controller is not getattr(self.gateway, "budget", None):
            raise BudgetExceeded(
                requested=self.budget_controller.spent_microusd,
                limit=self.budget_controller.limit_microusd,
                message="Session budget ceiling cannot be guaranteed: "
                "BUDGET_ENFORCEMENT_UNAVAILABLE before provider dispatch",
            )
        if self.gateway is None:
            raise ProviderConfigError("PFP_ACCOUNTED_GATEWAY_REQUIRED: inject an existing PFP run gateway")

        from pfp.infrastructure.pilot_matrix import complete_pilot_turn
        from adversary.domain.providers.types import (
            CandidateRequest,
            ChatMessage,
            DecodingParamsV1,
        )
        decoding = DecodingParamsV1(temperature=self.temperature)
        request = (CandidateRequest(messages=tuple(ChatMessage(m["role"], m["content"]) for m in prompt),
                                   decoding=decoding)
                   if isinstance(prompt, list) else CandidateRequest(user=prompt, decoding=decoding))
        candidate_model = self.cascade_models[0]
        attempt_id = f"legacy-backend:{self._run_id}:{len(self.turn_history)}"
        try:
            turn = complete_pilot_turn(self.gateway, request, model=candidate_model,
                task_id=f"legacy-backend:{self._run_id}", attempt_id=attempt_id, max_tokens=self.max_tokens)
        except BaseException as cancellation:
            self._retain_cancellation(attempt_id, cancellation)
            raise
        claim = None
        action = getattr(self.gateway, "action", None)
        if callable(action):
            try:
                claim = action(attempt_id)
            except KeyError:
                pass
        turn["attempted"] = bool(turn["provider_wire"] or
            claim is not None and claim["state"] != "refused_before_dispatch")
        turn["attempt_claim"] = claim
        self.last_turn = turn
        self.turn_history.append(turn)
        receipt = self._retain_receipt(turn, candidate_model)
        if not turn["ok"] or turn["stop"]:
            raise ProviderError(turn["error"] or turn["attempt_state"] or "PFP_UNAVAILABLE")
        if receipt is None:
            raise ProviderError("PFP_RECEIPT_UNAVAILABLE")
        return receipt

    def _retain_cancellation(self, attempt_id: str, cancellation: BaseException) -> None:
        """Observe existing custody without masking or retrying a cancellation."""
        turn = dict(ok=False, stop=True, content=None, pfp=None, usage={},
            attempt_state=None, provider_wire=None, attempt_claim=None,
            attempted=False, error=type(cancellation).__name__, custody_error=None)
        try:
            claim = self.gateway.action(attempt_id)
            turn["attempt_claim"] = claim
            turn["attempt_state"] = claim["state"]
            turn["attempted"] = claim["state"] != "refused_before_dispatch"
            if "wire_file" in claim:
                raw = self.gateway.raw_reply(attempt_id)
                turn["provider_wire"] = dict(raw_reply_base64=base64.b64encode(raw).decode("ascii"),
                    raw_reply_sha256=claim["wire_sha256"], raw_reply_bytes=len(raw))
        except KeyError:
            pass  # Cancellation before claiming an action has no dispatched attempt.
        except Exception as custody_error:
            # Preserve the original cancellation; unavailable custody is not zero cost.
            turn["custody_error"] = type(custody_error).__name__
        self.last_turn = turn
        self.turn_history.append(turn)

    def _retain_receipt(self, turn: dict, model: str) -> OpenRouterReceipt | None:
        """Retain actual received usage, including a rejected completion's cost."""
        if not turn["attempt_state"] or turn["provider_wire"] is None:
            return None
        from adversary.infrastructure.providers.wire import decode_reply
        body = decode_reply(base64.b64decode(turn["provider_wire"]["raw_reply_base64"]))
        raw_usage=body.get('usage',{})
        if type(raw_usage) is not dict:
            raise ProviderError('OPENROUTER_USAGE_MALFORMED')
        usage = dict(raw_usage)
        observed = turn["usage"]
        # Parsed candidate defaults are not evidence that the vendor reported usage.
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if any(value is not None and (type(value) is not int or value<0)
                for value in (prompt_tokens,completion_tokens,total_tokens)):
            raise ProviderError('OPENROUTER_USAGE_MALFORMED')
        if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
            total_tokens = prompt_tokens + completion_tokens
        try:
            raw_completion = body["choices"][0]["message"]["content"]
        except (KeyError,IndexError,TypeError):
            raise ProviderError('OPENROUTER_COMPLETION_MALFORMED') from None
        if type(raw_completion) is not str:
            raise ProviderError('OPENROUTER_COMPLETION_MALFORMED')
        cost = observed.get("cost")
        receipt = OpenRouterReceipt(content=turn["content"] if turn["ok"] else raw_completion,
            model=body.get("model", model), generation_id=observed.get("generation_id", ""),
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost, raw_usage=usage,
            cost_status=COST_PROVIDER_REPORTED if cost is not None else COST_UNREPORTED)
        self.last_receipt = receipt
        self.call_history.append(receipt)
        return receipt

    def complete(self, prompt: str) -> str:
        receipt = self.complete_with_receipt(prompt)
        return receipt.content

    @property
    def total_tokens(self) -> int | None:
        if any(r.total_tokens is None for r in self.call_history):
            return None
        return sum(r.total_tokens for r in self.call_history)

    @property
    def total_cost_usd(self) -> float | None:
        """Summed reported cost, or None when an attempted call's cost is unknown."""
        if self.unreported_cost_generation_ids or any(
                turn.get("custody_error") or turn["attempted"] and turn["usage"].get("cost") is None
                for turn in self.turn_history):
            return None
        return sum(r.cost_usd for r in self.call_history if r.cost_usd is not None)

    @property
    def unreported_cost_generation_ids(self) -> tuple[str, ...]:
        """Generation ids whose cost must be reconciled before spend is known."""
        return tuple(r.generation_id for r in self.call_history if r.cost_usd is None)

    def fetch_generation_cost(self, generation_id: str) -> float | None:
        """Fetch verified billed cost from OpenRouter's generation endpoint."""
        api_key = getattr(self, "_api_key", None)
        if api_key is None:
            found = resolve_credential(["OPENROUTER_API_KEY"], missing_code="OPENROUTER_KEY_MISSING")
            api_key = None if isinstance(found, Err) else found.value.value
        if not api_key or not generation_id:
            return None
        url = f"{OPENROUTER_BASE_URL}/generation?id={generation_id}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "SymbolGame",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0) as response:
                from governance.domain.ingress.limits import MAX_PROVIDER_REPLY_BYTES
                from adversary.infrastructure.providers.wire import decode_reply
                data = decode_reply(response.read(MAX_PROVIDER_REPLY_BYTES + 1))
        except (
            URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
            UnicodeDecodeError,
            ValueError,
        ):
            return None
        if not isinstance(data, dict):
            return None
        gen_data = data.get("data")
        if not isinstance(gen_data, dict) or gen_data.get("id") != generation_id or "total_cost" not in gen_data:
            return None
        return _optional_float(gen_data.get("total_cost"))


class CascadingOpenRouterBackend(OpenRouterBackend):
    """Configured model preferences; failures do not authorize automatic retries."""

    def __init__(
        self,
        models: Sequence[str] = DEFAULT_CASCADE_MODELS,
        budget_controller: Any | None = None,
        max_tokens: int = 2048,
        style: str = "direct",
        api_key: str | None = None,
        *,
        gateway=None,
        temperature: float | None = None,
    ) -> None:
        super().__init__(
            models=models,
            max_tokens=max_tokens,
            style=style,
            api_key=api_key,
            budget_controller=budget_controller,
            gateway=gateway,
            temperature=temperature,
        )


def get_backend(provider: str | None = None, **kwargs) -> Backend:
    provider = (provider or os.environ.get("SENTINEL_LLM_PROVIDER") or "anthropic").lower()
    if provider in ("anthropic", "claude"):
        return AnthropicBackend(**kwargs)
    if provider in ("openrouter", "or"):
        return OpenRouterBackend(**kwargs)
    if provider in ("openrouter_cascade", "cascade"):
        return CascadingOpenRouterBackend(**kwargs)
    if provider in ("mock", "offline"):
        return MockBackend(**{k: v for k, v in kwargs.items() if k == "answer"})
    if provider in ("sakana", "fugu", "sakana_openrouter"):
        from adversary.infrastructure.providers.adapters.sakana_adapter import (
            SakanaOpenRouterAdapter,
        )

        return SakanaOpenRouterAdapter(**kwargs)
    raise ValueError(f"unknown provider {provider!r}")
