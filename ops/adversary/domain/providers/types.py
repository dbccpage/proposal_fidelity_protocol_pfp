"""OEARS provider types. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from fractions import Fraction
from types import MappingProxyType
from typing import Any

from governance.domain.ingress.limits import (
    MAX_PROVIDER_PROMPT_BYTES,
    MAX_PROVIDER_REPLY_BYTES,
    REFUSAL_PROVIDER_PROMPT_TOO_LARGE,
    REFUSAL_PROVIDER_REPLY_TOO_LARGE,
    IngressRefusal,
    OversizeReceipt,
    bounded_utf8_prefix,
)

_SHA256_DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
_UTC_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z\Z"
)


class ProviderError(ValueError):
    """Base provider/gateway error."""


class ModelNotAllowed(ProviderError):
    """(provider, model) not on the allowlist or unpriced."""


class BudgetExceeded(ProviderError):
    """Worst-case cost would exceed remaining budget."""

    def __init__(self, *, requested: int, limit: int, message: str = "") -> None:
        self.requested = requested
        self.limit = limit
        super().__init__(
            message or f"budget exceeded: requested={requested} limit={limit} micro-USD"
        )


class ProviderConfigError(ProviderError):
    """Bad provider configuration."""
    code = "PROVIDER_CONFIG_INVALID"


class BudgetEnforcementUnavailable(ProviderConfigError):
    code = "BUDGET_ENFORCEMENT_UNAVAILABLE"

    def __init__(self) -> None:
        super().__init__("BUDGET_ENFORCEMENT_UNAVAILABLE: maximum liability cannot be enforced before dispatch")


class PromptTooLarge(ProviderError):
    """Combined system + user prompt exceeds the provider prompt ceiling.

    Distinct from `BudgetExceeded` on purpose. Both refuse a request that is too
    big, and they refuse it for unrelated reasons: budget is about money already
    spent, this is about bytes never sent. The campaign's rule that a refusal
    must name a *stable mechanism* is not satisfied by two causes sharing one
    terminal, so they do not share one.
    """

    def __init__(self, receipt: OversizeReceipt) -> None:
        self.receipt = receipt
        self.code = receipt.refusal_code
        super().__init__(
            f"{receipt.refusal_code}: prompt is at least {receipt.observed_bytes} "
            f"bytes against a limit of {receipt.limit_bytes}"
        )


class ReplyTooLarge(ProviderError):
    """Provider reply exceeds the reply ceiling; the transport is abandoned."""

    def __init__(self, receipt: OversizeReceipt) -> None:
        self.receipt = receipt
        self.code = receipt.refusal_code
        super().__init__(
            f"{receipt.refusal_code}: reply is at least {receipt.observed_bytes} "
            f"bytes against a limit of {receipt.limit_bytes}"
        )


class PromptInvalidUtf8(ProviderError):
    """A provider prompt contains a code point strict UTF-8 cannot encode."""

    def __init__(self, receipt: OversizeReceipt) -> None:
        self.receipt = receipt
        self.code = receipt.refusal_code
        super().__init__(
            f"{receipt.refusal_code}: prompt is not valid strict UTF-8 "
            f"within the first {receipt.observed_bytes} observed bytes"
        )


def check_reply_bytes(
    raw: bytes | bytearray | memoryview,
    *,
    limit: int = MAX_PROVIDER_REPLY_BYTES,
) -> None:
    """Refuse a raw provider body over ``limit`` before it is consumed.

    This check deliberately accepts only octets.  Checking parsed ``content``
    lets an attacker hide an arbitrarily large body in JSON whitespace or
    metadata, after the decoder has already allocated it.  On overflow only the
    first ``limit + 1`` bytes are hashed for the bounded receipt; the complete
    hostile body is never copied or hashed here.
    """
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise TypeError(
            "provider transport must return exact response bytes, not a decoded "
            f"{type(raw).__name__}"
        )
    view = memoryview(raw)
    if not view.c_contiguous:
        raise TypeError("provider response bytes must be C-contiguous")
    # A memoryview slice counts *elements*, not bytes.  Cast first so a view
    # over ``array('I')`` cannot hash four times the admitted prefix.
    octets = view.cast("B")
    if octets.nbytes <= limit:
        return
    prefix = octets[: limit + 1]
    raise ReplyTooLarge(
        OversizeReceipt(
            refusal_code=REFUSAL_PROVIDER_REPLY_TOO_LARGE,
            limit_bytes=limit,
            observed_bytes=limit + 1,
            observed_truncated=True,
            observed_prefix_sha256=hashlib.sha256(prefix).hexdigest(),
        )
    )


class Provider(str, Enum):
    FIXTURE = "fixture"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GROK = "grok"
    GROQ = "groq"
    LOCAL = "local"
    OPENROUTER = "openrouter"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    NVIDIA = "nvidia"


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str

    def __post_init__(self) -> None:
        if type(self.role) is not str or not self.role:
            raise ValueError("role must be non-empty str")
        if type(self.content) is not str:
            raise TypeError("content must be str")


@dataclass(frozen=True)
class DecodingParamsV1:
    seed: int | None = None
    temperature: Fraction | float | None = None
    top_p: Fraction | float | None = None
    response_format: Mapping[str, Any] | None = None
    logit_bias: Mapping[str, int] | None = None
    grammar: str | None = None
    allow_fallbacks: bool = False
    require_parameters: bool = True
    thinking: str | None = None
    effort: str | None = None

    def __post_init__(self) -> None:
        if self.seed is not None and type(self.seed) is not int:
            raise ProviderConfigError("seed must be an exact integer")
        for name in ("allow_fallbacks", "require_parameters"):
            if type(getattr(self, name)) is not bool:
                raise ProviderConfigError(f"{name} must be exactly bool")
        for name in ("temperature", "top_p"):
            value = getattr(self, name)
            if value is not None and (type(value) not in (float, int, Fraction) or not math.isfinite(value)):
                raise ProviderConfigError(f"{name} must be finite")
        if self.temperature is not None and not 0 <= self.temperature <= 2:
            raise ProviderConfigError("temperature must be between zero and two")
        if self.top_p is not None and not 0 < self.top_p <= 1:
            raise ProviderConfigError("top_p must be between zero (exclusive) and one")
        if self.grammar is not None and type(self.grammar) is not str:
            raise ProviderConfigError("grammar must be an exact string")
        if self.thinking not in (None, "disabled", "adaptive"):
            raise ProviderConfigError("unsupported thinking policy")
        if self.effort not in (None, "low", "medium", "high", "xhigh", "max"):
            raise ProviderConfigError("unsupported effort level")
        for name in ("response_format", "logit_bias"):
            value = getattr(self, name)
            if value is not None:
                if not isinstance(value, Mapping):
                    raise ProviderConfigError(f"{name} must be a mapping")
                object.__setattr__(self, name, freeze_json(value))
        if self.logit_bias is not None and any(
            type(v) is not int or not -100 <= v <= 100 for v in self.logit_bias.values()
        ):
            raise ProviderConfigError("logit biases must be exact integers between -100 and 100")


def freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(type(k) is not str for k in value):
            raise ProviderConfigError("JSON keys must be strings")
        return MappingProxyType({k: freeze_json(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(v) for v in value)
    if value is None or type(value) in (str, bool, int) or (type(value) is float and math.isfinite(value)):
        return value
    raise ProviderConfigError("decoding parameters must contain finite JSON values")


def thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {k: thaw_json(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(v) for v in value]
    return value


@dataclass(frozen=True)
class CandidateRequest:
    system: str = ""
    user: str = ""
    messages: tuple[ChatMessage, ...] = ()
    decoding: DecodingParamsV1 | None = None

    def __post_init__(self) -> None:
        if type(self.system) is not str or type(self.user) is not str:
            raise ProviderConfigError("system and user must be exact strings")
        object.__setattr__(self, "messages", tuple(self.messages))
        if any(type(m) is not ChatMessage for m in self.messages):
            raise ProviderConfigError("messages must contain exactly ChatMessage values")
        if self.messages and (self.system or self.user):
            raise ProviderConfigError("choose messages or system/user, not both")
        if self.decoding is not None and type(self.decoding) is not DecodingParamsV1:
            raise ProviderConfigError("decoding must be exactly DecodingParamsV1")

    def conversation(self) -> tuple[ChatMessage, ...]:
        return self.messages or (ChatMessage("system", self.system), ChatMessage("user", self.user))

    def estimated_payload_bytes(self) -> int:
        """Exact combined UTF-8 size.

        Unbounded by nature: it encodes strings in full. That is acceptable
        only because `check_payload_ceiling` runs first at every admission path,
        so by the time this is called the payload is known to be under the
        ceiling. Calling it on unchecked input walks the whole bomb.
        """
        if self.messages:
            return sum(len(m.role.encode("utf-8")) + len(m.content.encode("utf-8")) for m in self.messages)
        return len(self.system.encode("utf-8")) + len(self.user.encode("utf-8"))

    def check_payload_ceiling(self, *, limit: int = MAX_PROVIDER_PROMPT_BYTES) -> None:
        """Refuse a combined prompt over `limit` bytes, without encoding it all."""
        if self.messages:
            accum = b""
            for m in self.messages:
                remaining = limit - len(accum)
                try:
                    role_prefix, r_overflow = bounded_utf8_prefix(m.role, remaining)
                except IngressRefusal as exc:
                    raise PromptInvalidUtf8(exc.receipt) from None
                accum += role_prefix
                if r_overflow:
                    raise PromptTooLarge(_prompt_receipt(accum, limit))
                remaining = limit - len(accum)
                try:
                    c_prefix, c_overflow = bounded_utf8_prefix(m.content, remaining)
                except IngressRefusal as exc:
                    raise PromptInvalidUtf8(exc.receipt) from None
                accum += c_prefix
                if c_overflow:
                    raise PromptTooLarge(_prompt_receipt(accum, limit))
            return

        try:
            system_prefix, system_overflows = bounded_utf8_prefix(self.system, limit)
        except IngressRefusal as exc:
            raise PromptInvalidUtf8(exc.receipt) from None
        if system_overflows:
            raise PromptTooLarge(_prompt_receipt(system_prefix, limit))

        remaining = limit - len(system_prefix)
        try:
            user_prefix, user_overflows = bounded_utf8_prefix(self.user, remaining)
        except IngressRefusal as exc:
            raise PromptInvalidUtf8(exc.receipt) from None
        if user_overflows:
            raise PromptTooLarge(_prompt_receipt(system_prefix + user_prefix, limit))


def _prompt_receipt(prefix: bytes, limit: int) -> OversizeReceipt:
    bounded = prefix[: limit + 1]
    return OversizeReceipt(
        refusal_code=REFUSAL_PROVIDER_PROMPT_TOO_LARGE,
        limit_bytes=limit,
        observed_bytes=len(bounded),
        observed_truncated=True,
        observed_prefix_sha256=hashlib.sha256(bounded).hexdigest(),
    )


@dataclass(frozen=True)
class CandidateResponse:
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    authority_effect: str = "None"
    claims_global_green: bool = False
    transport: str = "fixture"
    generation_id: str = ""
    cost_usd: float | None = None

    def __post_init__(self) -> None:
        if type(self.content) is not str:
            raise ProviderError("content must be an exact string")
        for name in ("model", "provider", "transport"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                raise ProviderError(f"{name} must be a non-empty exact string")
        if type(self.generation_id) is not str:
            raise ProviderError("generation_id must be an exact string")
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ProviderError(f"{name} must be a non-negative exact integer")
        if self.cost_usd is not None and (
            type(self.cost_usd) not in (int, float) or not math.isfinite(self.cost_usd) or self.cost_usd < 0
        ):
            raise ProviderError("cost_usd must be finite and non-negative, or unknown")
        if type(self.claims_global_green) is not bool:
            raise ProviderError("claims_global_green must be exactly bool")
        if self.authority_effect != "None":
            raise ProviderError("authority_effect must be None")
        if self.claims_global_green:
            raise ProviderError("candidates must not claim GlobalGreen")


@dataclass(frozen=True)
class BudgetReceipt:
    model: str
    cost_microusd: int
    spent_after_microusd: int
    limit_microusd: int
    pricing_observation_digest: str
    pricing_effective_from_utc: str
    pricing_observed_at_utc: str
    pricing_stale_after_utc: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if type(self.model) is not str or not self.model:
            raise ProviderError("model must be a non-empty exact string")
        for name in ("cost_microusd", "spent_after_microusd", "limit_microusd"):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise ProviderError(f"{name} must be a non-negative exact integer")
        if self.cost_microusd > self.spent_after_microusd:
            raise ProviderError("cost cannot exceed cumulative spend")
        if self.spent_after_microusd > self.limit_microusd:
            raise ProviderError("cumulative spend cannot exceed budget limit")
        if self.authority_effect != "None":
            raise ProviderError("authority_effect must be None")
        if (
            type(self.pricing_observation_digest) is not str
            or _SHA256_DIGEST.fullmatch(self.pricing_observation_digest) is None
        ):
            raise ProviderError("budget receipt requires a pricing observation digest")
        parsed = []
        for name in (
            "pricing_effective_from_utc",
            "pricing_observed_at_utc",
            "pricing_stale_after_utc",
        ):
            value = getattr(self, name)
            if type(value) is not str or _UTC_TIMESTAMP.fullmatch(value) is None:
                raise ProviderError(f"{name} must be canonical UTC")
            try:
                timestamp = datetime.fromisoformat(value[:-1] + "+00:00")
            except ValueError as exc:
                raise ProviderError(f"{name} is invalid") from exc
            if timestamp.tzinfo != timezone.utc:
                raise ProviderError(f"{name} must be UTC")
            parsed.append(timestamp)
        if not parsed[0] <= parsed[1] < parsed[2]:
            raise ProviderError("pricing receipt timestamps are inconsistent")

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "cost_microusd": self.cost_microusd,
            "spent_after_microusd": self.spent_after_microusd,
            "limit_microusd": self.limit_microusd,
            "pricing_observation_digest": self.pricing_observation_digest,
            "pricing_effective_from_utc": self.pricing_effective_from_utc,
            "pricing_observed_at_utc": self.pricing_observed_at_utc,
            "pricing_stale_after_utc": self.pricing_stale_after_utc,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class AdmitResult:
    receipt: BudgetReceipt
    provider: Provider
    model: str
