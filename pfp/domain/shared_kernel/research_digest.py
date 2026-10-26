"""Dependency-light canonical JSON digest used by research packet boundaries.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def digest_payload(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


__all__ = ["canonical_bytes", "digest_payload"]
