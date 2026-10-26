"""Strict, deterministic JSON for the demo receipt schema (not a new reach codec)."""

from __future__ import annotations

import hashlib
import json

from omega_engine_pfp.domain.demos import DemoRefusal


def canonical(value: object) -> bytes:
    return (
        json.dumps(
            value, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False
        ).encode("ascii")
        + b"\n"
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DemoRefusal("DUPLICATE_JSON_KEY", key)
        result[key] = value
    return result


def _constant(value: str):
    raise DemoRefusal("NONFINITE_JSON", value)


def load(data: bytes | str) -> object:
    return json.loads(data, object_pairs_hook=_pairs, parse_constant=_constant)
