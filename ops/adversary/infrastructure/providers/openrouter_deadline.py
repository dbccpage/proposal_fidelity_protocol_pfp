"""One attempt in a killable worker, bounded by an absolute parent deadline."""

import json
import subprocess
import sys

from operations.domain.rop.result import Err
from adversary.domain.providers.types import CandidateRequest, DecodingParamsV1
from adversary.infrastructure.providers.openrouter_transport import openrouter_transport


def dispatch_deadline(model, request, max_tokens, timeout):
    decoding = request.decoding
    document = dict(
        model=model,
        system=request.system,
        user=request.user,
        max_tokens=max_tokens,
        timeout=timeout,
        decoding=dict(
            seed=decoding.seed,
            temperature=decoding.temperature,
            allow_fallbacks=decoding.allow_fallbacks,
            require_parameters=decoding.require_parameters,
            thinking=decoding.thinking,
        ),
    )
    process = subprocess.run(
        [sys.executable, "-m", __name__],
        input=json.dumps(document).encode(),
        capture_output=True,
        timeout=timeout,
    )
    if process.returncode:
        raise ValueError("PROVIDER_WORKER_FAILED")
    return process.stdout


def main():
    document = json.load(sys.stdin)
    transport = openrouter_transport(timeout=document["timeout"])
    if isinstance(transport, Err):
        raise ValueError("CREDENTIAL_UNAVAILABLE")
    request = CandidateRequest(
        document["system"], document["user"], decoding=DecodingParamsV1(**document["decoding"])
    )
    raw = transport.value(document["model"], request, document["max_tokens"])
    sys.stdout.buffer.write(raw)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(1)
