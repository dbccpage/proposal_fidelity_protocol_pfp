"""Pure domain-separated digests for local-CI value objects."""

from __future__ import annotations

import hashlib
import json

from operations.domain.cicd.constants import _RESOLUTION_DOMAIN


def resolved_invocation_digest(
    gate_id: str,
    resolved_argv: tuple[str, ...],
    resolved_inputs: tuple[str, ...],
) -> str:
    """Bind the exact resolved command and ordered input paths."""

    value = {
        "gate_id": gate_id,
        "resolved_argv": resolved_argv,
        "resolved_inputs": resolved_inputs,
    }
    canonical = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    return hashlib.sha256(_RESOLUTION_DOMAIN + canonical).hexdigest()
