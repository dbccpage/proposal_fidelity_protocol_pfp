"""Sealed causal witnesses. A caller dict is not a witness.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

PLACEHOLDER_WITNESS = "sha256:causal_witness_ok"
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def is_sealed_digest(digest: Any) -> bool:
    return isinstance(digest, str) and _SHA256.fullmatch(digest) is not None and digest != PLACEHOLDER_WITNESS


def canonical_witness_body(body: Mapping[str, Any]) -> str:
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


@dataclass(frozen=True)
class SealedCausalWitness:
    """Digest bound to canonical JSON. Construction refuses a mismatched or placeholder digest."""

    receipt_sha256: str
    canonical_body: str

    def __post_init__(self) -> None:
        if not is_sealed_digest(self.receipt_sha256):
            raise ValueError("CAUSAL_WITNESS_REQUIRED: witness digest is not a sealed sha256")
        expected = "sha256:" + hashlib.sha256(self.canonical_body.encode("utf-8")).hexdigest()
        if self.receipt_sha256 != expected:
            raise ValueError("CAUSAL_WITNESS_REQUIRED: witness digest does not match its body")


def seal_causal_witness(body: Mapping[str, Any]) -> SealedCausalWitness:
    canonical = canonical_witness_body(body)
    digest = "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return SealedCausalWitness(digest, canonical)
