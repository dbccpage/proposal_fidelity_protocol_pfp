"""Canonical identifiers for the anti-skill domain.

`canonical_id` is carried over from the retired Python higher-operad kernel
(`omega_engine/kernel/higher_operad/canonical.py`, removed in f4c6fcf3) and is
byte-identical to it, so anti-skill spec, registry and profile identifiers
recorded before the relocation still recompute.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from enum import Enum
from typing import Any, Dict, Mapping

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")


def _require_identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    normalized = unicodedata.normalize("NFC", value.strip())
    if _IDENTIFIER.fullmatch(normalized) is None:
        raise ValueError(f"{field} must be a canonical identifier")
    return normalized


def _canonicalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return _canonicalize(value.value)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        normalized: Dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical maps require string keys")
            canonical_key = unicodedata.normalize("NFC", key)
            if canonical_key in normalized:
                raise ValueError(f"canonical key collision: {canonical_key!r}")
            normalized[canonical_key] = _canonicalize(item)
        return normalized
    if isinstance(value, (tuple, list)):
        return [_canonicalize(item) for item in value]
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_id(domain: str, payload: Any) -> str:
    envelope = {
        "domain": _require_identifier(domain, "domain"),
        "payload": _canonicalize(payload),
    }
    encoded = json.dumps(
        envelope,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


__all__ = ["canonical_id"]
