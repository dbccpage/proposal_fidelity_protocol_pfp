"""OpenRouter transport: the only place that holds the API key and does HTTP.

The key is found by `credential_source.resolve_credential` (explicit file, process
environment, then the checkout and main-checkout ``.env``). It is never written into
``os.environ``. A missing key is a typed ``Refusal``. AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.providers.types import CandidateRequest, Provider
from adversary.infrastructure.providers.credential_source import resolve_credential
from adversary.infrastructure.providers.openai_compat import (
    OPENROUTER_BASE_URL,
    build_openai_compat_body,
    build_openai_compat_headers,
)

Transport = Callable[[str, CandidateRequest, int], bytes]

KEY_NAME = "OPENROUTER_API_KEY"


def resolve_openrouter_key(
    env_file: Path | str | None, environ: Mapping[str, str] | None = None
) -> Result[str, Refusal]:
    """Explicit file, then the environment, then the checkout `.env` files; see credential_source."""
    found = resolve_credential(
        [KEY_NAME], missing_code="OPENROUTER_KEY_MISSING", explicit_file=env_file, environ=environ
    )
    if isinstance(found, Err):
        return found
    return Ok(found.value.value)


def _post(url: str, headers: Mapping[str, str], body: Mapping[str, Any], timeout: float) -> bytes:
    from adversary.infrastructure.providers.http import post_json
    return post_json(url, headers, body, timeout)


def openrouter_transport(
    env_file: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    timeout: float = 60.0,
) -> Result[Transport, Refusal]:
    key = resolve_openrouter_key(env_file, environ)
    if isinstance(key, Err):
        return key
    api_key = key.value

    def send(model: str, request: CandidateRequest, max_tokens: int) -> bytes:
        request.check_payload_ceiling()
        body = build_openai_compat_body(request, model=model, max_tokens=max_tokens)
        body["usage"] = {"include": True}
        headers = build_openai_compat_headers(api_key=api_key, provider=Provider.OPENROUTER)
        return _post(OPENROUTER_BASE_URL + "/chat/completions", headers, body, timeout)

    return Ok(send)
