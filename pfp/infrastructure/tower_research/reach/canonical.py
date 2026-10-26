"""Canonical bytes, strict parsing, digests and exact rationals.

AuthorityEffect: None.

Canonical bytes (W1-S07 section 7.1, W2-C05 section 4.1): sorted keys,
two-space indent, LF, ASCII, one final newline. No floats. JSON numbers are
nonnegative integer counts only; every signed or fractional quantity is a
``"num/den"`` string, reduced, with ``den >= 1`` and zero written ``0/1``.
Digests are ``sha256:<64 lowercase hex>``; git ids are 40 lowercase hex.
"""

from __future__ import annotations

import hashlib
import json
import re
from fractions import Fraction
from typing import Any

SIZE_CAP_BYTES = 1_048_576

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
RATIONAL_SHAPE_RE = re.compile(r"^[+-]?\d+/[+-]?\d+$")


class CanonicalError(ValueError):
    """A byte-level refusal. ``code`` is one of the RR-* codes of K1."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def canonical_bytes(obj: Any) -> bytes:
    """Serialize ``obj`` in the canonical profile."""
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True, separators=(",", ": "))
    return (text + "\n").encode("ascii")


def compact_line(obj: Any) -> bytes:
    """One canonical JSONL line: sorted keys, no whitespace, LF."""
    text = json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return (text + "\n").encode("ascii")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest(data: bytes) -> str:
    """The ``sha256:<hex>`` digest of raw bytes."""
    return "sha256:" + sha256_hex(data)


def digest_obj(obj: Any) -> str:
    """The digest of an object's canonical bytes."""
    return digest(canonical_bytes(obj))


def domain_digest(tag: str, obj: Any) -> str:
    """A domain-separated digest: ``sha256(tag || 0x00 || canonical(obj))``."""
    return digest(tag.encode("ascii") + b"\x00" + canonical_bytes(obj))


def _reject_float(text: str) -> Any:
    raise CanonicalError("RR-FLOAT", f"float literal {text!r}")


def _reject_constant(text: str) -> Any:
    raise CanonicalError("RR-FLOAT", f"non-finite literal {text!r}")


def _pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise CanonicalError("RR-DUP-KEY", f"repeated key {key!r}")
        out[key] = value
    return out


def strict_loads(data: bytes) -> Any:
    """Parse bytes, detecting duplicate keys before the dict collapses."""
    if len(data) > SIZE_CAP_BYTES:
        raise CanonicalError("RR-SIZE", f"{len(data)} bytes exceeds the cap of {SIZE_CAP_BYTES}")
    try:
        text = data.decode("ascii")
    except UnicodeDecodeError as exc:
        raise CanonicalError("RR-BYTES", f"not ASCII at byte {exc.start}") from None
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs_hook,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise CanonicalError("RR-BYTES", f"not JSON: {exc.msg} at {exc.pos}") from None


def check_numbers(obj: Any, path: str = "$") -> None:
    """Refuse floats, negative integers and non-canonical rational strings."""
    if isinstance(obj, bool) or obj is None:
        return
    if isinstance(obj, float):
        raise CanonicalError("RR-FLOAT", f"float at {path}")
    if isinstance(obj, int):
        if obj < 0:
            raise CanonicalError("RR-RATIONAL", f"negative integer at {path}; write a num/den string")
        return
    if isinstance(obj, str):
        if RATIONAL_SHAPE_RE.match(obj) and not is_canonical_rational(obj):
            raise CanonicalError("RR-RATIONAL", f"non-canonical rational {obj!r} at {path}")
        return
    if isinstance(obj, list):
        for index, item in enumerate(obj):
            check_numbers(item, f"{path}[{index}]")
        return
    if isinstance(obj, dict):
        for key, value in obj.items():
            check_numbers(value, f"{path}.{key}")


def is_canonical_rational(text: str) -> bool:
    try:
        value = parse_rational(text)
    except ValueError:
        return False
    return format_rational(value) == text


def parse_rational(text: str) -> Fraction:
    match = re.fullmatch(r"(-?)(0|[1-9]\d*)/([1-9]\d*)", text)
    if match is None:
        raise ValueError(f"not a num/den rational: {text!r}")
    sign, num, den = match.groups()
    value = Fraction(int(num), int(den))
    return -value if sign else value


def format_rational(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def parse_canonical(data: bytes) -> Any:
    """K1 in one call: parse strictly, then require canonical re-serialization."""
    obj = strict_loads(data)
    check_numbers(obj)
    if canonical_bytes(obj) != data:
        raise CanonicalError("RR-BYTES", "bytes are not their own canonical re-serialization")
    return obj
