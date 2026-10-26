"""Shared helpers for estate probes.

A probe passes only on an effect it read back from the estate's own store; the receipt's
digest is the SHA-256 of those observed bytes. Any exception becomes a disconnected
receipt that names it.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from typing import Any

from omega_engine_operations.domain.rop.result import Refusal
from omega_engine_woland.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from omega_engine_woland.domain.specialization import PortName


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def observed(
    estate: EstateName, port: PortName, adapter_id: str, effect: bytes, detail: str
) -> ConnectionReceiptV1:
    return ConnectionReceiptV1(
        estate, port, adapter_id, True, hashlib.sha256(effect).hexdigest(), detail
    )


def run_probe(
    estate: EstateName,
    port: PortName,
    adapter_id: str,
    body: Callable[[], ConnectionReceiptV1],
) -> ConnectionReceiptV1:
    """Run ``body``; an exception is reported as a disconnected receipt, never raised."""
    try:
        return body()
    except Exception as exc:  # noqa: BLE001 - a probe reports every failure as data
        return disconnected(estate, port, adapter_id, f"{type(exc).__name__}: {exc}")


def refusal(code: str, exc: BaseException, locus: str) -> Refusal:
    return Refusal(code, f"{type(exc).__name__}: {exc}", locus)


__all__ = ["canonical_bytes", "observed", "refusal", "run_probe"]
