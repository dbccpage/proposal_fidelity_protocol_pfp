"""One bounded experiment attempt, preserving the complete provider request.

The historical PO035 worker remains unchanged. This codec carries conversation
messages and every decoding field through the worker before using the canonical
transport. AuthorityEffect: None.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from dataclasses import fields
from fractions import Fraction

from operations.domain.rop.result import Err
from adversary.domain.providers.types import (
    CandidateRequest,
    ChatMessage,
    DecodingParamsV1,
    ProviderConfigError,
    freeze_json,
    thaw_json,
)
from adversary.infrastructure.providers.openai_compat import build_openai_compat_body
from adversary.infrastructure.providers.openrouter_transport import openrouter_transport

_SCHEMA = "providers.openrouter-experiment-worker.v1"
_REQUEST_FIELDS = {"system", "user", "messages", "decoding"}


def _require_keys(value, expected):
    if type(value) is not dict or set(value) != expected:
        raise ProviderConfigError("INVALID_EXPERIMENT_WORKER_FIELDS")


def _validate_attempt(model, max_tokens, timeout):
    if type(model) is not str or not model.strip():
        raise ProviderConfigError("MODEL_REQUIRED")
    if type(max_tokens) is not int or max_tokens < 1:
        raise ProviderConfigError("INVALID_MAX_TOKENS")
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ProviderConfigError("INVALID_EXPERIMENT_TIMEOUT")


def _serialize_request(request):
    if type(request) is not CandidateRequest:
        raise ProviderConfigError("EXACT_CANDIDATE_REQUEST_REQUIRED")
    if {field.name for field in fields(CandidateRequest)} != _REQUEST_FIELDS:
        raise ProviderConfigError("UNSUPPORTED_CANDIDATE_REQUEST_FIELDS")
    request.check_payload_ceiling()
    decoding = None
    if request.decoding is not None:
        decoding = {}
        for field in fields(DecodingParamsV1):
            value = getattr(request.decoding, field.name)
            if field.name in {"temperature", "top_p"} and type(value) is Fraction:
                decoding[field.name] = {"fraction": [value.numerator, value.denominator]}
            else:
                decoding[field.name] = thaw_json(freeze_json(value))
    return {
        "system": request.system,
        "user": request.user,
        "messages": [
            {"role": message.role, "content": message.content} for message in request.messages
        ],
        "decoding": decoding,
    }


def _deserialize_request(document):
    _require_keys(document, _REQUEST_FIELDS)
    if type(document["messages"]) is not list:
        raise ProviderConfigError("INVALID_EXPERIMENT_MESSAGES")
    messages = []
    for message in document["messages"]:
        _require_keys(message, {"role", "content"})
        messages.append(ChatMessage(**message))
    decoding = document["decoding"]
    if decoding is not None:
        _require_keys(decoding, {field.name for field in fields(DecodingParamsV1)})
        decoding = dict(decoding)
        for name in ("temperature", "top_p"):
            value = decoding[name]
            if type(value) is dict:
                _require_keys(value, {"fraction"})
                pair = value["fraction"]
                if (
                    type(pair) is not list
                    or len(pair) != 2
                    or any(type(x) is not int for x in pair)
                ):
                    raise ProviderConfigError("INVALID_EXPERIMENT_FRACTION")
                if pair[1] <= 0:
                    raise ProviderConfigError("INVALID_EXPERIMENT_FRACTION")
                decoding[name] = Fraction(*pair)
        decoding = DecodingParamsV1(**decoding)
    request = CandidateRequest(
        system=document["system"],
        user=document["user"],
        messages=tuple(messages),
        decoding=decoding,
    )
    request.check_payload_ceiling()
    return request


def dispatch_deadline(model, request, max_tokens, timeout):
    """Dispatch once; subprocess.run kills and waits for an expired worker."""
    _validate_attempt(model, max_tokens, timeout)
    deadline = time.monotonic() + timeout
    request_document = _serialize_request(request)
    # Validate the same canonical wire codec before creating a worker.
    build_openai_compat_body(request, model=model, max_tokens=max_tokens)
    document = {
        "schema": _SCHEMA,
        "model": model,
        "request": request_document,
        "max_tokens": max_tokens,
        "timeout": timeout,
    }
    payload = json.dumps(document, ensure_ascii=False, allow_nan=False).encode("utf-8")
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise subprocess.TimeoutExpired([sys.executable, "-m", __name__], timeout)
    process = subprocess.run(
        [sys.executable, "-m", __name__],
        input=payload,
        capture_output=True,
        timeout=remaining,
    )
    if process.returncode:
        raise ValueError("PROVIDER_WORKER_FAILED")
    if type(process.stdout) is not bytes:
        raise ValueError("PROVIDER_WORKER_INVALID_OUTPUT")
    return process.stdout


def main():
    document = json.load(sys.stdin)
    _require_keys(document, {"schema", "model", "request", "max_tokens", "timeout"})
    if document["schema"] != _SCHEMA:
        raise ProviderConfigError("UNSUPPORTED_EXPERIMENT_WORKER_SCHEMA")
    _validate_attempt(document["model"], document["max_tokens"], document["timeout"])
    request = _deserialize_request(document["request"])
    build_openai_compat_body(request, model=document["model"], max_tokens=document["max_tokens"])
    transport = openrouter_transport(timeout=document["timeout"])
    if isinstance(transport, Err):
        raise ValueError("CREDENTIAL_UNAVAILABLE")
    raw = transport.value(document["model"], request, document["max_tokens"])
    if type(raw) is not bytes:
        raise ValueError("PROVIDER_WORKER_INVALID_OUTPUT")
    sys.stdout.buffer.write(raw)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
