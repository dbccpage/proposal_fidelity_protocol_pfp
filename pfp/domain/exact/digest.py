"""Digests as exact values: SHA-256 over a declared serialization profile.

A digest is 32 bytes, compared byte for byte. The serialization is a
declared convention, never inferred: the sorted-key compact ASCII JSON
profile (sorted keys, no white space, ASCII escapes), the form the receiving
side's checkers use. This profile is not RFC 8785 (JCS). Binary floats, NaN
and the infinities are refused, so a digest never depends on a float's
decimal rendering, and every mapping key must be a ``str``, so ``{1: "a"}``
and ``{"1": "a"}`` cannot share a digest. What a level hashes (which hosted content, in which shape)
is stated in its restatement; this module only fixes the two operations.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from .errors import ExactError


def _refuse_floats(value: object, where: str = "$") -> None:
    if isinstance(value, float):
        raise ExactError(
            "FLOAT_NOT_DIGESTIBLE",
            f"float {value!r} at {where} is not admitted in a digested value",
        )
    if isinstance(value, Mapping):
        for key, item in value.items():
            # json.dumps would render 1 and "1" as the same key, and turn 1.5 or
            # True into a string, so only str keys are digestible.
            if type(key) is not str:
                raise ExactError(
                    "NON_STRING_KEY",
                    f"mapping key {key!r} ({type(key).__name__}) at {where} is not a str",
                )
            _refuse_floats(item, f"{where}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _refuse_floats(item, f"{where}[{index}]")


def canonical_json(value: object) -> bytes:
    """Sorted keys, separators without white space, ASCII only; floats and
    non-str mapping keys refused."""
    _refuse_floats(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def digest_of(value: object) -> bytes:
    """The digest of a value in the sorted-key compact ASCII JSON profile."""
    return sha256(canonical_json(value))


__all__ = [
    "canonical_json",
    "digest_of",
    "sha256",
]
