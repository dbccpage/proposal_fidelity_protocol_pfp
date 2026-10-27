"""Strict integer/string subset of the domain JCS-style encoder.

This is not the ``core-canonical-v1`` packet sealer. The sealer is
``pfp.domain.shared_kernel.canonical.canonical_json``, which
emits the tagged wire ``["core-canonical-v1", tag, body]``. This function
must not be called as that sealer.

The supported subset is JSON null, booleans, integers, strings, arrays, and
objects with exact string keys. Integers are limited to 2**53 - 1 in magnitude;
strings preserve Unicode scalars without normalization. Domain encoding provides
UTF-16 key ordering and compact output. Floats are refused; subset compatibility
does not certify full binary64/ECMAScript conformance or Rust byte parity.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pfp.domain.canonical import JcsError, rfc8785_canonical_json

RFC8785_FORMAT_NAME = "rfc8785"


@dataclass(frozen=True, slots=True)
class Rfc8785Encoding:
    """One RFC 8785 encoding. ``format_name`` is never ``core-canonical-v1``."""

    format_name: str
    text: str


def _reject_unsupported(value: Any) -> None:
    if value is None or type(value) in {bool, str, int}:
        return
    if type(value) is list:
        for item in value:
            _reject_unsupported(item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("rfc8785 object keys must be strings")
            _reject_unsupported(item)
        return
    raise TypeError(
        f"rfc8785_canonicalize does not encode {type(value).__name__}"
    )


def rfc8785_canonicalize(value: Any) -> Rfc8785Encoding:
    """Encode the exact-built-in, safe-integer, no-float subset as ``rfc8785``.

    Invalid input is refused with TypeError; no tagged packet bytes are emitted.
    """

    _reject_unsupported(value)
    try:
        text = rfc8785_canonical_json(
            value, strict_no_floats=True, allow_bigint=False
        )
    except JcsError as exc:
        raise TypeError(str(exc)) from exc
    return Rfc8785Encoding(RFC8785_FORMAT_NAME, text)


__all__ = [
    "RFC8785_FORMAT_NAME",
    "Rfc8785Encoding",
    "rfc8785_canonicalize",
]
