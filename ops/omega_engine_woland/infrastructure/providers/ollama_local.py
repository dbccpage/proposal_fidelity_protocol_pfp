"""Ollama optional local propose (SCALE-001 S3).

Probe the loopback Ollama host; refuse live local propose when not running.
Fixture/gateway paths do not require Ollama. AuthorityEffect: None.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from omega_engine_governance.domain.ingress.limits import (
    MAX_PROVIDER_REPLY_BYTES,
    REFUSAL_PROVIDER_REPLY_TOO_LARGE,
    read_bounded,
)
from omega_engine_woland.domain.providers.types import Provider, ProviderConfigError
from omega_engine_woland.infrastructure.providers.openai_compat import (
    DEFAULT_LOCAL_MODEL,
    DEFAULT_OLLAMA_HOST,
    ENV_OLLAMA_HOST,
    LOCAL_BASE_URL,
    LOCAL_OPENAI_COMPAT_SUFFIX,
)
from omega_engine_woland.infrastructure.providers.openai_compat import (
    local_base_url as _local_base_url,
)
from omega_engine_woland.infrastructure.providers.openai_compat import (
    ollama_host as _ollama_host,
)

AUTHORITY_EFFECT = "None"
SCHEMA_VERSION = "urn:omega:oears:ollama_local:v1"

# Env
# ENV_OLLAMA_HOST is imported from openai_compat, not restated here. Restating
# it would reintroduce the two-literals defect one level down: the name and the
# resolver have to come from the same place or they can drift again.
ENV_USE_LOCAL_PROPOSE = "OEARS_USE_LOCAL_PROPOSE"  # 1/true → prefer local for propose
ENV_LOCAL_MODEL = "OEARS_LOCAL_MODEL"  # override default local model
ENV_PROBE_TIMEOUT = "OEARS_OLLAMA_PROBE_TIMEOUT_S"  # default 1.5

# DEFAULT_OLLAMA_HOST is imported, not restated: openai_compat owns the one host
# literal so the probe here and LOCAL_BASE_URL there cannot drift apart. Re-exported
# below for callers that already import this name from this module.
DEFAULT_PROBE_TIMEOUT_S = 1.5

#: Read size for the bounded probe reader. Small on purpose: the probe expects a
#: modest JSON object, so a large chunk would only make the overshoot past the
#: ceiling bigger before the reader notices.
_PROBE_CHUNK_BYTES = 8 * 1024


class OllamaNotRunning(ProviderConfigError):
    """Live local propose requested but Ollama is not reachable."""


def ollama_host() -> str:
    """Delegates: openai_compat owns resolution, not just the literal.

    This module used to read the environment itself, which left
    ``default_base_url(Provider.LOCAL)`` returning the import-time constant
    while the probe followed the override. One resolver, one answer.
    """
    return _ollama_host()


def ollama_openai_base_url() -> str:
    """OpenAI-compat base for Ollama (…/v1), override-aware.

    With OEARS_OLLAMA_HOST unset this equals LOCAL_BASE_URL by construction.
    With it set, this and ``default_base_url(Provider.LOCAL)`` are the same call.
    """
    return _local_base_url()


def local_model_name() -> str:
    return (
        os.environ.get(ENV_LOCAL_MODEL, DEFAULT_LOCAL_MODEL).strip()
        or DEFAULT_LOCAL_MODEL
    )


def use_local_propose_env() -> bool:
    raw = os.environ.get(ENV_USE_LOCAL_PROPOSE, "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def _probe_timeout_s() -> float:
    raw = os.environ.get(ENV_PROBE_TIMEOUT, "").strip()
    if not raw:
        return DEFAULT_PROBE_TIMEOUT_S
    try:
        return max(0.2, float(raw))
    except ValueError as exc:
        raise ProviderConfigError(f"invalid {ENV_PROBE_TIMEOUT}={raw!r}") from exc


@dataclass(frozen=True)
class OllamaProbeResult:
    running: bool
    host: str
    models: list[str]
    error: str | None = None
    authority_effect: str = AUTHORITY_EFFECT

    def to_receipt(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "running": self.running,
            "host": self.host,
            "models": list(self.models),
            "error": self.error,
            "authority_effect": self.authority_effect,
            "claims_global_green": False,
        }


ProbeFn = Callable[[str, float], OllamaProbeResult]


def _read_bounded_response(resp: Any, limit: int) -> bytes:
    """Read at most ``limit + 1`` bytes from an open HTTP response.

    `resp.read()` with no argument reads to EOF, which means a host that
    streams without end is a hang and a host that streams a gigabyte is a
    gigabyte in memory. Neither needs to be hostile on purpose -- a
    misconfigured local endpoint will do -- and the probe has no use for more
    than a small JSON object either way.
    """
    return read_bounded(
        iter(lambda: resp.read(_PROBE_CHUNK_BYTES), b""),
        limit=limit,
        refusal_code=REFUSAL_PROVIDER_REPLY_TOO_LARGE,
    )


def _http_get_json(url: str, timeout_s: float) -> dict[str, Any]:
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:
        raw = _read_bounded_response(resp, MAX_PROVIDER_REPLY_BYTES)
    body = raw.decode("utf-8")
    data = json.loads(body) if body else {}
    if not isinstance(data, dict):
        raise ProviderConfigError("ollama probe: expected JSON object")
    return data


def probe_ollama(
    *,
    host: str | None = None,
    timeout_s: float | None = None,
    get_json: Callable[[str, float], dict[str, Any]] | None = None,
) -> OllamaProbeResult:
    """GET {host}/api/tags. Does not raise on connection failure — running=False."""
    h = (host or ollama_host()).rstrip("/")
    t = timeout_s if timeout_s is not None else _probe_timeout_s()
    fetcher = get_json or _http_get_json
    tags_url = f"{h}/api/tags"
    try:
        data = fetcher(tags_url, t)
        models: list[str] = []
        for row in data.get("models") or []:
            if isinstance(row, dict) and row.get("name"):
                models.append(str(row["name"]))
        return OllamaProbeResult(running=True, host=h, models=models, error=None)
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        OSError,
        json.JSONDecodeError,
        ProviderConfigError,
        ValueError,
    ) as exc:
        return OllamaProbeResult(
            running=False,
            host=h,
            models=[],
            error=f"{type(exc).__name__}: {exc}",
        )


def require_ollama_running(
    *,
    host: str | None = None,
    timeout_s: float | None = None,
    get_json: Callable[[str, float], dict[str, Any]] | None = None,
    require_model: str | None = None,
) -> OllamaProbeResult:
    """Refuse with OllamaNotRunning if probe fails or model missing (when required)."""
    result = probe_ollama(host=host, timeout_s=timeout_s, get_json=get_json)
    if not result.running:
        raise OllamaNotRunning(
            f"Ollama not running at {result.host} "
            f"(set {ENV_OLLAMA_HOST} or start ollama serve). "
            f"detail={result.error}"
        )
    if require_model:
        want = require_model.strip()
        names = result.models
        # An omitted tag means exactly :latest; model family prefixes do not
        # establish that a requested deployment is installed.
        normalized = want if ":" in want.rsplit("/", 1)[-1] else want + ":latest"
        ok = any((n if ":" in n.rsplit("/", 1)[-1] else n + ":latest") == normalized for n in names)
        if not ok:
            raise OllamaNotRunning(
                f"Ollama running but model {want!r} not in tags "
                f"(have {names[:8]}{'…' if len(names) > 8 else ''}). "
                f"pull model or set {ENV_LOCAL_MODEL}."
            )
    return result


def assert_local_propose_ready(
    *,
    model: str | None = None,
    get_json: Callable[[str, float], dict[str, Any]] | None = None,
) -> OllamaProbeResult:
    """Gate live LOCAL propose: Ollama up (+ optional model presence)."""
    m = model or local_model_name()
    return require_ollama_running(require_model=m, get_json=get_json)


def local_propose_provider_model() -> tuple[Provider, str]:
    """Provider.LOCAL + configured model (does not probe)."""
    return Provider.LOCAL, local_model_name()


# Re-export the shared host/base constants owned by openai_compat, so the public
# names this module has always exposed keep resolving from here.
__all__ = [
    "DEFAULT_LOCAL_MODEL",
    "DEFAULT_OLLAMA_HOST",
    "ENV_LOCAL_MODEL",
    "ENV_OLLAMA_HOST",
    "ENV_USE_LOCAL_PROPOSE",
    "LOCAL_BASE_URL",
    "LOCAL_OPENAI_COMPAT_SUFFIX",
    "OllamaNotRunning",
    "OllamaProbeResult",
    "assert_local_propose_ready",
    "local_model_name",
    "local_propose_provider_model",
    "ollama_host",
    "ollama_openai_base_url",
    "probe_ollama",
    "require_ollama_running",
    "use_local_propose_env",
]
