"""Anthropic Messages request/response builders. No sockets. AuthorityEffect: None."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from adversary.domain.providers.types import (
    CandidateRequest,
    CandidateResponse,
    Provider,
    ProviderConfigError,
    ProviderError,
    thaw_json,
)
from adversary.infrastructure.providers.wire import usage_count
from adversary.domain.providers.attempt import ProviderUsageObservation

DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_MESSAGES_PATH = "/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
CAMPAIGN_MODELS = frozenset({"claude-haiku-5-5", "claude-sonnet-5-5"})

# Structured-output keywords outside the Messages API's documented support. The provider
# receives a copy without them; callers keep validating replies against their full schema,
# so nothing is loosened. Live 2026-10-21: maxItems returned HTTP 400, and a learning
# schema with four string patterns returned "Schema is too complex."
UNSUPPORTED_SCHEMA_KEYWORDS = frozenset({
    "minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
    "minLength", "maxLength", "maxItems", "uniqueItems", "minProperties", "maxProperties",
    "pattern", "$id",
})
SUPPORTED_STRING_FORMATS = frozenset({
    "date-time", "time", "date", "duration", "email", "hostname", "uri", "ipv4", "ipv6", "uuid",
})


def provider_output_schema(schema: Any) -> Any:
    """Copy a JSON schema without keywords Anthropic structured outputs do not accept."""
    if isinstance(schema, list):
        return [provider_output_schema(item) for item in schema]
    if not isinstance(schema, Mapping):
        return schema
    copied = {}
    for key, value in schema.items():
        if key in UNSUPPORTED_SCHEMA_KEYWORDS:
            continue
        if key == "minItems" and not (type(value) is int and value in (0, 1)):
            continue
        if key == "format" and value not in SUPPORTED_STRING_FORMATS:
            continue
        if key in ("properties", "$defs", "definitions") and isinstance(value, Mapping):
            copied[key] = {name: provider_output_schema(item) for name, item in value.items()}
        else:
            copied[key] = provider_output_schema(value)
    return copied


def build_anthropic_headers(*, api_key: str) -> dict[str, str]:
    if not api_key.strip():
        raise ProviderConfigError("ANTHROPIC_API_KEY required for live anthropic")
    return {
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }


def build_anthropic_body(
    request: CandidateRequest,
    *,
    model: str = DEFAULT_ANTHROPIC_MODEL,
    max_tokens: int = 1024,
) -> dict[str, Any]:
    if not model.strip():
        raise ProviderConfigError("model required")
    if type(max_tokens) is not int or max_tokens < 1:
        raise ProviderConfigError("max_tokens must be >= 1")
    request.check_payload_ceiling()
    system = []
    messages = []
    for message in request.conversation():
        if message.role == "system" and not messages:
            system.append(message.content)
        elif message.role in ("user", "assistant"):
            messages.append({"role": message.role, "content": message.content})
        else:
            raise ProviderConfigError("Anthropic cannot preserve this conversation role/order")
    if not messages:
        raise ProviderConfigError("Anthropic requires a user or assistant message")
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "system": "\n".join(system),
        "messages": messages,
    }
    dec = request.decoding
    if dec is not None:
        if model in CAMPAIGN_MODELS and (dec.temperature is not None or dec.top_p is not None):
            raise ProviderConfigError("ANTHROPIC_55_SAMPLING_UNSUPPORTED")
        if any(v is not None for v in (dec.seed, dec.logit_bias, dec.grammar)) or dec.allow_fallbacks:
            raise ProviderConfigError("Anthropic does not support the requested decoding capabilities")
        if dec.response_format is not None:
            fmt = thaw_json(dec.response_format)
            declared = fmt.get("json_schema", {})
            if fmt.get("type") != "json_schema" or type(declared.get("schema")) is not dict:
                raise ProviderConfigError("ANTHROPIC_STRUCTURED_SCHEMA_REQUIRED")
            body["output_config"] = {"format": {"type": "json_schema",
                "schema": provider_output_schema(declared["schema"])}}
        if dec.effort is not None:
            body.setdefault("output_config", {})["effort"] = dec.effort
        if dec.temperature is not None:
            body["temperature"] = float(dec.temperature)
        if dec.top_p is not None:
            body["top_p"] = float(dec.top_p)
        if dec.thinking is not None:
            body["thinking"] = {"type": dec.thinking}
    return body


def observe_anthropic_usage(data, *, model, transport="live"):
    """Retain billable usage even when answer content is unusable. No answer is minted."""
    if not isinstance(data, Mapping) or data.get("model") != model:
        raise ProviderError("ANTHROPIC_USAGE_MODEL_MISMATCH")
    usage = data.get("usage")
    if not isinstance(usage, Mapping):
        raise ProviderError("ANTHROPIC_USAGE_MISSING")
    if any(k not in usage for k in ("input_tokens", "output_tokens")):
        raise ProviderError("ANTHROPIC_USAGE_MISSING")
    # This adapter never requests caching or server tools. Unknown extra billing
    # cannot be reconciled at the uncached text rate.
    for name in ("cache_creation_input_tokens", "cache_read_input_tokens"):
        if type(usage.get(name, 0)) is not int or usage.get(name, 0) != 0:
            raise ProviderError("ANTHROPIC_UNSUPPORTED_BILLING")
    if usage.get("server_tool_use") not in (None, {}):
        raise ProviderError("ANTHROPIC_UNSUPPORTED_BILLING")
    generation = data.get("id")
    if type(generation) is not str or not generation:
        raise ProviderError("ANTHROPIC_GENERATION_ID_MISSING")
    return ProviderUsageObservation(model, Provider.ANTHROPIC.value,
        usage_count(usage, "input_tokens"), usage_count(usage, "output_tokens"),
        generation, None, transport)


def parse_anthropic_response(
    data: Mapping[str, Any],
    *,
    fallback_model: str = DEFAULT_ANTHROPIC_MODEL,
    transport: str = "live",
) -> CandidateResponse:
    if not isinstance(data, Mapping) or "error" in data or data.get("type") == "error":
        raise ProviderError("Anthropic returned an error envelope")
    content_blocks = data.get("content")
    if type(content_blocks) is not list:
        raise ProviderError("Anthropic reply requires a content array")
    texts: list[str] = []
    for block in content_blocks:
        if isinstance(block, Mapping) and block.get("type") == "text":
            if type(block.get("text")) is not str:
                raise ProviderError("Anthropic text blocks require a string")
            texts.append(block["text"])
        elif isinstance(block, Mapping) and block.get("type") == "thinking" and type(block.get("thinking")) is str:
            continue
        else:
            raise ProviderError("Anthropic reply contains unsupported content blocks")
    text = "\n".join(t for t in texts if t).strip()
    usage = data.get("usage", {})
    if not isinstance(usage, Mapping):
        raise ProviderError("Anthropic usage must be an object")
    stop_reason = str(data.get("stop_reason") or "")
    if stop_reason == "refusal" and not text:
        text = "[PROVIDER_REFUSAL]"
    elif not texts:
        raise ProviderError("Anthropic reply has no text content")
    return CandidateResponse(
        content=text,
        model=data.get("model", fallback_model),
        provider=Provider.ANTHROPIC.value,
        input_tokens=usage_count(usage, "input_tokens"),
        output_tokens=usage_count(usage, "output_tokens"),
        transport=transport,
        generation_id=data.get("id", ""),
    )


def fixture_anthropic_payload(
    request: CandidateRequest,
    *,
    model: str = DEFAULT_ANTHROPIC_MODEL,
) -> dict[str, Any]:
    body = f"[FIXTURE anthropic] sys_len={len(request.system)} user_len={len(request.user)}"
    return {
        "id": "msg_fixture",
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": [{"type": "text", "text": body}],
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 10, "output_tokens": 20},
    }


class AnthropicTransport:
    provenance = "live"
    def __init__(self, *, api_key: str, timeout: float = 90, base_url: str = "https://api.anthropic.com"):
        self._headers = build_anthropic_headers(api_key=api_key)
        self._url = base_url.rstrip("/") + ANTHROPIC_MESSAGES_PATH
        self.timeout = timeout

    def dispatch(self, admitted):
        from adversary.infrastructure.providers.http import post_json
        body = build_anthropic_body(admitted.request, model=admitted.model, max_tokens=admitted.max_output_tokens)
        return post_json(self._url, self._headers, body, self.timeout)

    def maximum_liability(self, provider, model, request, limit, quote):
        from adversary.domain.providers.budget import PriceTable
        if provider != Provider.ANTHROPIC or model not in CAMPAIGN_MODELS:
            return None
        body = build_anthropic_body(request, model=model, max_tokens=limit)
        import json
        # Text-only serialized bytes plus a conservative framing allowance. The
        # campaign uses a stricter byte ceiling than its 8,000-token allowance.
        # No caching, tools, images, extended-context tier or provider fallback.
        if len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 1024 > 8000:
            raise ProviderConfigError("ANTHROPIC_INPUT_BOUND_EXCEEDED")
        table = PriceTable.empty().with_observation(quote.observation)
        return table.quote(model, 8000, limit,
            at_utc=quote.observation.observed_at_utc).cost_microusd
