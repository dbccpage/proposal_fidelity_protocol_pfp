"""OpenAI-compatible chat-completions KVP.

Providers: OpenAI/Grok/Groq/Local/OpenRouter/DeepSeek/Gemini.
No sockets in fixture path. Live keys never logged.
AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

from operations.domain.rop.result import Err
from adversary.domain.providers.attempt import ProviderUsageObservation
from adversary.domain.providers.types import (
    CandidateRequest,
    CandidateResponse,
    Provider,
    ProviderConfigError,
    ProviderError,
    thaw_json,
)
from adversary.infrastructure.providers.credential_source import resolve_credential
from adversary.infrastructure.providers.wire import reported_cost, usage_count

OPENAI_BASE_URL = "https://api.openai.com/v1"
GROK_BASE_URL = "https://api.x.ai/v1"
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Single source of truth for the LOCAL (Ollama) endpoint.
#
# ``ollama_local`` imports both names rather than restating the host, so the
# probe (``GET {host}/api/tags``) and the OpenAI-compat transport
# (``{host}/v1/chat/completions``) can never name different hosts. Before this
# was shared, LOCAL_BASE_URL said ``localhost`` while DEFAULT_OLLAMA_HOST said
# ``127.0.0.1``; those are not the same endpoint when ``localhost`` resolves to
# ::1 first (common on Windows) or is overridden in the hosts file, so the probe
# could report Ollama down while the transport would have reached it.
#
# 127.0.0.1 is the kept value because ``ollama serve`` binds the IPv4 loopback
# by default. Override with OEARS_OLLAMA_HOST (see ollama_local.ollama_host).
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
# Path suffix that turns an Ollama host into its OpenAI-compat base.
LOCAL_OPENAI_COMPAT_SUFFIX = "/v1"
# The no-override value. Kept as a module constant because callers import it,
# but it is NOT the resolver: with OEARS_OLLAMA_HOST set this constant is stale
# by construction, because it is computed once at import. Use local_base_url().
LOCAL_BASE_URL = f"{DEFAULT_OLLAMA_HOST}{LOCAL_OPENAI_COMPAT_SUFFIX}"

# Operator override for the Ollama endpoint. Declared here, beside the host it
# overrides, so there is one name for it rather than one per module.
ENV_OLLAMA_HOST = "OEARS_OLLAMA_HOST"


def ollama_host() -> str:
    """The Ollama host, honouring OEARS_OLLAMA_HOST, normalised.

    Collapsing the two host *literals* was not enough: resolution was still
    split. This function read the override while ``default_base_url(LOCAL)``
    returned the import-time constant, so with the override set the probe
    targeted one host and the transport base another -- the same divergence the
    shared literal was meant to end, one layer up.

    A trailing ``/v1`` is stripped. The override names a HOST, but an operator
    who copies an OpenAI-compat base URL into it would otherwise make the native
    probe build ``{host}/v1/api/tags``, which is not an Ollama endpoint.
    """
    raw = os.environ.get(ENV_OLLAMA_HOST, DEFAULT_OLLAMA_HOST).strip().rstrip("/")
    if raw.endswith(LOCAL_OPENAI_COMPAT_SUFFIX):
        raw = raw[: -len(LOCAL_OPENAI_COMPAT_SUFFIX)].rstrip("/")
    return raw or DEFAULT_OLLAMA_HOST


def local_base_url() -> str:
    """OpenAI-compat base for Ollama, override-aware.

    Equals ``LOCAL_BASE_URL`` exactly when OEARS_OLLAMA_HOST is unset.
    """
    return f"{ollama_host()}{LOCAL_OPENAI_COMPAT_SUFFIX}"


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
# Google AI OpenAI-compat surface (SCALE-003 S3)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GROK_MODEL = "grok-2-latest"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
DEFAULT_LOCAL_MODEL = "qwen2.5:0.5b"
DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
# OpenRouter slug for Gemini Flash (alternate path)
DEFAULT_OPENROUTER_GEMINI_MODEL = "google/gemini-2.5-flash"
DEFAULT_NVIDIA_MODEL = "meta/llama-3.3-70b-instruct"

# Operator-confirmed env names (root .env); never log values.
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
NVIDIA_API_KEY_ENV = "NVIDIA_API_KEY"

CHAT_COMPLETIONS_PATH = "/chat/completions"


def default_base_url(provider: Provider) -> str:
    if provider == Provider.OPENAI:
        return OPENAI_BASE_URL
    if provider == Provider.GROK:
        return GROK_BASE_URL
    if provider == Provider.GROQ:
        return GROQ_BASE_URL
    if provider == Provider.LOCAL:
        # Resolved, not the import-time constant: the operator override has to
        # reach the transport base too, or it only moves the probe.
        return local_base_url()
    if provider == Provider.OPENROUTER:
        return OPENROUTER_BASE_URL
    if provider == Provider.DEEPSEEK:
        return DEEPSEEK_BASE_URL
    if provider == Provider.GEMINI:
        return GEMINI_BASE_URL
    if provider == Provider.NVIDIA:
        return NVIDIA_BASE_URL
    raise ProviderConfigError(
        f"provider {provider.value} is not OpenAI-compatible in this adapter"
    )


def default_model(provider: Provider) -> str:
    if provider == Provider.OPENAI:
        return DEFAULT_OPENAI_MODEL
    if provider == Provider.GROK:
        return DEFAULT_GROK_MODEL
    if provider == Provider.GROQ:
        return DEFAULT_GROQ_MODEL
    if provider == Provider.LOCAL:
        return DEFAULT_LOCAL_MODEL
    if provider == Provider.OPENROUTER:
        return DEFAULT_OPENROUTER_MODEL
    if provider == Provider.DEEPSEEK:
        return DEFAULT_DEEPSEEK_MODEL
    if provider == Provider.GEMINI:
        return DEFAULT_GEMINI_MODEL
    if provider == Provider.NVIDIA:
        return DEFAULT_NVIDIA_MODEL
    raise ProviderConfigError(f"no default model for {provider.value}")


_KEY_NAMES: dict[Provider, tuple[tuple[str, ...], str]] = {
    Provider.OPENROUTER: ((OPENROUTER_API_KEY_ENV,), "OpenRouter"),
    Provider.DEEPSEEK: ((DEEPSEEK_API_KEY_ENV,), "DeepSeek"),
    Provider.GEMINI: ((GEMINI_API_KEY_ENV,), "Gemini"),
    Provider.NVIDIA: ((NVIDIA_API_KEY_ENV,), "NVIDIA"),
    Provider.OPENAI: (("OPENAI_API_KEY",), "OpenAI"),
    Provider.GROK: (("XAI_API_KEY", "GROK_API_KEY"), "Grok"),
    Provider.GROQ: (("GROQ_API_KEY",), "Groq"),
}


def resolve_openai_compat_api_key(provider: Provider) -> str:
    """Live API key for an OpenAI-compatible provider, from `credential_source`.

    Order: process environment, then the checkout and main-checkout ``.env``. A missing key is a
    ProviderConfigError that names the variable and never a value.
    """
    if provider == Provider.LOCAL:
        return os.environ.get("LOCAL_LLM_API_KEY", "ollama").strip() or "ollama"
    entry = _KEY_NAMES.get(provider)
    if entry is None:
        raise ProviderConfigError(
            f"provider {provider.value} has no OpenAI-compat key resolver"
        )
    names, label = entry
    found = resolve_credential(names, missing_code="CREDENTIAL_MISSING")
    if isinstance(found, Err):
        raise ProviderConfigError(f"{' or '.join(names)} required for live {label}")
    return found.value.value


def build_openai_compat_headers(
    *,
    api_key: str,
    provider: Provider | None = None,
) -> dict[str, str]:
    if not api_key.strip():
        raise ProviderConfigError("api_key required for OpenAI-compat live call")
    headers: dict[str, str] = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    # Optional OpenRouter metadata (no secrets).
    if provider == Provider.OPENROUTER:
        headers.setdefault("HTTP-Referer", "https://github.com/dbccpage/sentinel")
        headers.setdefault("X-Title", "OEARS")
    return headers


def build_openai_compat_body(
    request: CandidateRequest,
    *,
    model: str,
    max_tokens: int = 1024,
    provider: Provider | None = None,
) -> dict[str, Any]:
    if not model.strip():
        raise ProviderConfigError("model required")
    if type(max_tokens) is not int or max_tokens < 1:
        raise ProviderConfigError("max_tokens must be >= 1")

    request.check_payload_ceiling()
    messages = [{"role": m.role, "content": m.content} for m in request.conversation()]

    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    if request.decoding is not None:
        dec = request.decoding
        if dec.thinking == "disabled" and provider in (None, Provider.OPENROUTER):
            body["reasoning"] = {"enabled": False}
        elif dec.thinking is not None:
            raise ProviderConfigError("thinking policy is not supported by this codec")
        if dec.effort is not None:
            raise ProviderConfigError("effort is not supported by this codec")
        if dec.seed is not None:
            body["seed"] = dec.seed
        if dec.temperature is not None:
            body["temperature"] = float(dec.temperature)
        if dec.top_p is not None:
            body["top_p"] = float(dec.top_p)
        if dec.response_format is not None:
            fmt = thaw_json(dec.response_format)
            if (provider in (None, Provider.OPENROUTER) and isinstance(fmt, dict)
                    and fmt.get("type") == "json_schema" and isinstance(fmt.get("json_schema"), dict)
                    and isinstance(fmt["json_schema"].get("schema"), dict)):
                from adversary.infrastructure.providers.anthropic_messages import (
                    provider_output_schema,
                )

                fmt = {**fmt, "json_schema": {**fmt["json_schema"],
                    "schema": provider_output_schema(fmt["json_schema"]["schema"])}}
            body["response_format"] = fmt
        if dec.logit_bias is not None:
            body["logit_bias"] = thaw_json(dec.logit_bias)
        if dec.grammar is not None:
            body["grammar"] = dec.grammar
        if provider in (None, Provider.OPENROUTER):
            body["provider"] = {
                "allow_fallbacks": dec.allow_fallbacks,
                "require_parameters": dec.require_parameters,
            }
        elif dec.allow_fallbacks or dec.grammar is not None:
            raise ProviderConfigError("provider routing/grammar controls are unsupported by this deployment")

    return body


def parse_openai_compat_response(
    data: Mapping[str, Any],
    *,
    provider: Provider,
    fallback_model: str,
    transport: str = "live",
) -> CandidateResponse:
    if not isinstance(data, Mapping) or "error" in data:
        raise ProviderError("provider returned an error envelope")
    choices = data.get("choices")
    if type(choices) is not list or not choices or not isinstance(choices[0], Mapping):
        raise ProviderError("provider reply requires a nonempty choices array")
    msg = choices[0].get("message")
    if not isinstance(msg, Mapping):
        raise ProviderError("provider reply requires an assistant message")
    content = msg.get("content")
    if content is None and choices[0].get("finish_reason") == "content_filter":
        content = "[PROVIDER_CONTENT_FILTER]"
    if type(content) is not str:
        raise ProviderError("provider assistant content must be a string")
    usage = data.get("usage", {})
    if not isinstance(usage, Mapping):
        raise ProviderError("provider usage must be an object")
    cost_raw = usage.get("cost") if usage.get("cost") is not None else usage.get("total_cost")
    if "total_tokens" in usage:
        usage_count(usage, "total_tokens")
    raw_model = data.get("model", fallback_model)
    if (
        provider == Provider.OPENROUTER
        and isinstance(raw_model, str)
        and isinstance(fallback_model, str)
        and raw_model.startswith(f"{fallback_model}-")
    ):
        raw_model = fallback_model
    return CandidateResponse(
        content=content.strip(),
        model=raw_model,
        provider=provider.value,
        input_tokens=usage_count(usage, "prompt_tokens"),
        output_tokens=usage_count(usage, "completion_tokens"),
        transport=transport,
        generation_id=data.get("id", ""),
        cost_usd=reported_cost(cost_raw),
    )


def observe_openai_compat_usage(
    data: Mapping[str, Any], *, provider: Provider, model: str, transport: str,
) -> ProviderUsageObservation:
    """Observe a refused completion's billing without repairing its content.

    Explicit deployment identity and both usage counts are required. Missing
    cost remains unknown; no default zero cost or invented generation is added.
    """
    raw_model = data.get("model") if isinstance(data, Mapping) else None
    if (
        provider == Provider.OPENROUTER
        and isinstance(raw_model, str)
        and isinstance(model, str)
        and raw_model.startswith(f"{model}-")
    ):
        raw_model = model
    if not isinstance(data, Mapping) or raw_model != model:
        raise ProviderError("provider billing deployment identity unavailable")
    usage = data.get("usage")
    if not isinstance(usage, Mapping) or not all(
            key in usage for key in ("prompt_tokens", "completion_tokens")):
        raise ProviderError("provider billing usage unavailable")
    if "total_tokens" in usage:
        usage_count(usage, "total_tokens")
    cost = usage.get("cost") if usage.get("cost") is not None else usage.get("total_cost")
    return ProviderUsageObservation(model=model, provider=provider.value,
        input_tokens=usage_count(usage, "prompt_tokens"),
        output_tokens=usage_count(usage, "completion_tokens"),
        generation_id=data.get("id", ""), cost_usd=reported_cost(cost), transport=transport)


def fixture_openai_compat_payload(
    request: CandidateRequest,
    *,
    provider: Provider,
    model: str,
) -> dict[str, Any]:
    body = (
        f"[FIXTURE {provider.value}] "
        f"sys_len={len(request.system)} user_len={len(request.user)}"
    )
    # A PFP task turn is only usable when the fixture returns the bound envelope.
    # The answer stays synthetic prose; it is not an oracle or a live result.
    try:
        task = json.loads(request.user)
    except (TypeError, ValueError):
        task = None
    prompt = task.get("input") if type(task) is dict else None
    if (
        type(task) is dict
        and type(task.get("objective")) is str
        and type(prompt) is dict
        and type(prompt.get("prompt")) is str
        and all(type(task.get(key)) is str for key in ("task_id", "attempt_id", "input_sha256"))
    ):
        body = json.dumps({
            "task_id": task["task_id"],
            "attempt_id": task["attempt_id"],
            "input_sha256": task["input_sha256"],
            "answer": (
                f"[FIXTURE {provider.value}] sys_len={len(task['objective'])} "
                f"user_len={len(prompt['prompt'])}"
            ),
        })
    return {
        "id": "chatcmpl_fixture",
        "object": "chat.completion",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": body},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 11, "completion_tokens": 22, "total_tokens": 33},
    }


class OpenAiCompatTransport:
    """Raw response transport for the traced gateway. Credentials are explicit.

    No dotenv discovery, automatic retries, or parsing before durable custody.
    """
    provenance = "live"
    def __init__(self, provider: Provider, *, max_tokens: int = 1024, timeout: float = 30.0, api_key: str | None = None, base_url: str | None = None):
        self.provider = provider
        self._key = resolve_openai_compat_api_key(provider) if api_key is None else api_key
        if not self._key.strip():
            raise ProviderConfigError("explicit live API key must be nonempty")
        self._url = (base_url or default_base_url(provider)).rstrip("/") + CHAT_COMPLETIONS_PATH
        self.max_tokens = max_tokens
        self.timeout = timeout

    def __call__(self, provider: Provider, model: str, request: CandidateRequest) -> bytes:
        return self._send(provider, model, request, self.max_tokens)

    def maximum_liability(self, provider, model, request, max_output_tokens, quote):
        # Observed per-token prices and a heuristic input count are estimates,
        # not a vendor-enforced maximum bill (reasoning/routing can add cost).
        return None

    def dispatch(self, admitted) -> bytes:
        return self._send(admitted.provider, admitted.model, admitted.request, admitted.max_output_tokens)

    def _send(self, provider: Provider, model: str, request: CandidateRequest, max_tokens: int) -> bytes:
        from adversary.infrastructure.providers.http import post_json
        if provider != self.provider:
            raise ProviderConfigError("transport provider differs from configured provider")
        request.check_payload_ceiling()
        body = build_openai_compat_body(request, model=model, max_tokens=max_tokens, provider=provider)
        if provider == Provider.OPENROUTER:
            body["usage"] = {"include": True}
        headers = build_openai_compat_headers(api_key=self._key, provider=provider)
        return post_json(self._url, headers, body, self.timeout)
