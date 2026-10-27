"""JCS-style JSON encoding and separate core-canonical-v1 wire aliases.

Provides JCS-style encoding and the separate core-canonical-v1 wire aliases.
Shared integer/string subset compatibility does not certify every binary64
rendering or byte parity with the Rust implementations. ``allow_bigint=True``
is an arbitrary-integer extension outside the bounded JCS integer policy.

AuthorityEffect: None.
"""

from __future__ import annotations

import decimal
import hashlib
import json
import math
from collections.abc import Mapping
from typing import Any

from pfp.domain.exceptions import CanonicalizationError
from pfp.domain.shared_kernel.canonical import (
    canonical_bytes as core_canonical_bytes,
)
from pfp.domain.shared_kernel.canonical import (
    canonical_json as core_canonical_json,
)
from pfp.domain.shared_kernel.canonical import (
    canonical_unwire,
    canonical_wire,
    domain_digest,
    freeze,
    thaw,
)

MAX_SAFE_INTEGER: int = 9_007_199_254_740_991  # 2^53 - 1

_ES_ESCAPE_MAP: dict[str, str] = {
    '"': r"\"",
    "\\": r"\\",
    "\b": r"\b",
    "\t": r"\t",
    "\n": r"\n",
    "\f": r"\f",
    "\r": r"\r",
}


class JcsError(ValueError):
    """Raised when RFC 8785 JSON canonicalization invariants are violated."""


def _extract_es_digits_and_exp(s_rep: str) -> tuple[str, int]:
    if "e" in s_rep or "E" in s_rep:
        mantissa, exp_s = s_rep.lower().split("e")
        exp = int(exp_s)
        if "." in mantissa:
            int_p, frac_p = mantissa.split(".")
            return int_p + frac_p, len(int_p) + exp
        return mantissa, len(mantissa) + exp
    if "." in s_rep:
        int_part, frac_part = s_rep.split(".")
        frac_trimmed = frac_part.rstrip("0")
        if int_part == "0":
            leading_zeros = len(frac_part) - len(frac_part.lstrip("0"))
            return frac_trimmed[leading_zeros:], -leading_zeros
        return int_part + frac_trimmed, len(int_part)
    return s_rep, len(s_rep)


def _render_es_mantissa(digits: str, n: int) -> str:
    k = len(digits)
    if k <= n <= 21:
        return digits + "0" * (n - k)
    if 0 < n <= 21:
        return digits[:n] + "." + digits[n:]
    if -6 < n <= 0:
        return "0." + "0" * (-n) + digits
    exp = n - 1
    sign = "+" if exp >= 0 else "-"
    if k == 1:
        return digits + "e" + sign + str(abs(exp))
    return digits[0] + "." + digits[1:] + "e" + sign + str(abs(exp))


def format_es_number(
    val: float | int | decimal.Decimal,
    *,
    strict_no_floats: bool = False,
    allow_bigint: bool = False,
) -> str:
    """Format a number strictly according to ECMAScript 7.1.12.1 and RFC 8785 §3.2.2.3."""
    if isinstance(val, bool):
        raise JcsError(f"Boolean {val!r} is not a valid number")

    if isinstance(val, int):
        if not allow_bigint and abs(val) > MAX_SAFE_INTEGER:
            raise JcsError("integer magnitude exceeds 2^53 - 1 safe limit")
        return str(val)

    if strict_no_floats:
        raise JcsError(f"floating-point numbers are forbidden in strict mode: {val!r}")

    if isinstance(val, decimal.Decimal):
        val = float(val)

    if not isinstance(val, float):
        raise JcsError(f"Unsupported number type: {type(val).__name__}")

    if math.isnan(val) or math.isinf(val):
        raise JcsError(f"non-finite numbers are forbidden in JCS: {val}")

    if val == 0.0:
        return "0"

    prefix = "-" if math.copysign(1.0, val) < 0 else ""
    digits, n = _extract_es_digits_and_exp(repr(abs(val)))
    return prefix + _render_es_mantissa(digits, n)


def _require_scalar_string(value: Any) -> str:
    if type(value) is not str:
        raise JcsError("JCS strings and object keys must be exact strings")
    if any(0xD800 <= ord(char) <= 0xDFFF for char in value):
        raise JcsError("surrogate code points are forbidden in JCS strings")
    return value


def format_es_string(s: str) -> str:
    """Format a JSON string according to RFC 8785 §3.2.2.2."""
    s = _require_scalar_string(s)
    out: list[str] = ['"']
    for c in s:
        escaped = _ES_ESCAPE_MAP.get(c)
        if escaped is not None:
            out.append(escaped)
        elif ord(c) < 0x20:
            out.append(f"\\u{ord(c):04x}")
        else:
            out.append(c)
    out.append('"')
    return "".join(out)


def _format_jcs_mapping(
    value: Mapping[Any, Any],
    *,
    strict_no_floats: bool = False,
    allow_bigint: bool = False,
) -> str:
    keys = [_require_scalar_string(key) for key in value.keys()]
    sorted_keys = sorted(keys, key=lambda key: key.encode("utf-16-be"))
    seen: set[str] = set()
    props: list[str] = []
    for k in sorted_keys:
        str_key = k
        if str_key in seen:
            raise JcsError(f"duplicate object key detected: {str_key!r}")
        seen.add(str_key)
        key_repr = format_es_string(str_key)
        val_repr = rfc8785_canonical_json(
            value[k],
            strict_no_floats=strict_no_floats,
            allow_bigint=allow_bigint,
        )
        props.append(f"{key_repr}:{val_repr}")
    return "{" + ",".join(props) + "}"


def rfc8785_canonical_json(
    value: Any,
    *,
    strict_no_floats: bool = False,
    allow_bigint: bool = False,
) -> str:
    """Serialize a Python data structure into RFC 8785 Canonical JSON."""
    match value:
        case None:
            return "null"
        case bool():
            return "true" if value else "false"
        case int() | float():
            return format_es_number(
                value,
                strict_no_floats=strict_no_floats,
                allow_bigint=allow_bigint,
            )
        case str():
            return format_es_string(value)
        case list() | tuple():
            items = [
                rfc8785_canonical_json(
                    item,
                    strict_no_floats=strict_no_floats,
                    allow_bigint=allow_bigint,
                )
                for item in value
            ]
            return "[" + ",".join(items) + "]"
        case dict() | Mapping():
            return _format_jcs_mapping(
                value,
                strict_no_floats=strict_no_floats,
                allow_bigint=allow_bigint,
            )
        case _:
            raise JcsError(f"Unsupported JCS value type: {type(value).__name__}")


def rfc8785_canonical_bytes(
    value: Any,
    *,
    strict_no_floats: bool = False,
    allow_bigint: bool = False,
) -> bytes:
    """Return RFC 8785 Canonical JSON as UTF-8 bytes."""
    return rfc8785_canonical_json(
        value,
        strict_no_floats=strict_no_floats,
        allow_bigint=allow_bigint,
    ).encode("utf-8")


def rfc8785_digest_sha256(value: Any) -> str:
    """Compute SHA-256 hex digest of RFC 8785 canonical bytes."""
    return hashlib.sha256(rfc8785_canonical_bytes(value)).hexdigest()


def _unique_object_hook(pairs: list[tuple[Any, Any]]) -> dict[str, Any]:
    res: dict[str, Any] = {}
    for k, v in pairs:
        if k in res:
            raise JcsError(f"duplicate object key detected: {k!r}")
        res[k] = v
    return res


def canonicalize_json_str(raw_json: str) -> str:
    """Parse raw JSON string, validate duplicate keys and safe integers, and canonicalize per RFC 8785."""
    try:
        parsed = json.loads(
            raw_json,
            object_pairs_hook=_unique_object_hook,
            parse_constant=lambda c: (_ for _ in ()).throw(
                JcsError(f"non-finite numbers are forbidden in JCS: {c}")
            ),
        )
    except JcsError:
        raise
    except Exception as exc:
        raise JcsError(f"invalid JSON syntax: {exc}") from exc

    return rfc8785_canonical_json(parsed)


# Aliases for core-canonical-v1 compatibility
canonical_json = core_canonical_json
canonical_bytes = core_canonical_bytes

__all__ = [
    "MAX_SAFE_INTEGER",
    "CanonicalizationError",
    "JcsError",
    "canonical_bytes",
    "canonical_json",
    "canonical_unwire",
    "canonical_wire",
    "canonicalize_json_str",
    "domain_digest",
    "format_es_number",
    "format_es_string",
    "freeze",
    "rfc8785_canonical_bytes",
    "rfc8785_canonical_json",
    "rfc8785_digest_sha256",
    "thaw",
]
