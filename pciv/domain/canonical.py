"""Canonical and exact-type helpers for the pure OEWOLAND kernel."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from enum import Enum
from typing import Any, Mapping, cast

AUTHORITY_EFFECT_NONE = "None"
MAX_ITEMS = 256
MAX_TEXT_BYTES = 16 * 1024
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


def exact_object(value: Any, fields: frozenset[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ValueError(f"{label} must be an exact string-keyed object")
    wire = cast(dict[str, Any], value)
    missing = fields - set(wire)
    unknown = set(wire) - fields
    if missing:
        raise ValueError(f"{label} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{label} unknown fields: {', '.join(sorted(unknown))}")
    return wire


def text(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be an exact string")
    if len(value.encode("utf-8")) > MAX_TEXT_BYTES:
        raise ValueError(f"{label} exceeds the text limit")
    if not allow_empty and (not value or value.strip() != value):
        raise ValueError(f"{label} must be normalized and nonempty")
    if allow_empty and value and value.strip() != value:
        raise ValueError(f"{label} must be normalized")
    return value


def identifier(value: Any, label: str) -> str:
    parsed = text(value, label)
    if IDENTIFIER.fullmatch(parsed) is None:
        raise ValueError(f"{label} must be a canonical identifier")
    return parsed


def digest(value: Any, label: str, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    if type(value) is not str or DIGEST.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase sha256 digest")
    return value


def integer(
    value: Any, label: str, *, minimum: int = 0, maximum: int = 1_000_000
) -> int:
    if type(value) is not int or value < minimum or value > maximum:
        raise ValueError(f"{label} must be an exact integer in [{minimum}, {maximum}]")
    return value


def exact_bool(value: Any, label: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{label} must be an exact boolean")
    return value


def string_tuple(
    value: Any,
    label: str,
    *,
    identifiers: bool = False,
    digests: bool = False,
    allow_empty: bool = False,
    unique: bool = True,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{label} must be an exact tuple")
    if len(value) > MAX_ITEMS:
        raise ValueError(f"{label} exceeds the item limit")
    parsed: list[str] = []
    for index, item in enumerate(value):
        item_label = f"{label}[{index}]"
        if identifiers:
            parsed.append(identifier(item, item_label))
        elif digests:
            parsed.append(digest(item, item_label))
        else:
            parsed.append(text(item, item_label, allow_empty=allow_empty))
    if unique and len(parsed) != len(set(parsed)):
        raise ValueError(f"{label} must not contain duplicates")
    return tuple(parsed)


def wire_tuple(
    value: Any,
    label: str,
    *,
    identifiers: bool = False,
    digests: bool = False,
    unique: bool = True,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must be an exact JSON array")
    return string_tuple(
        tuple(value),
        label,
        identifiers=identifiers,
        digests=digests,
        unique=unique,
    )


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    if type(value) is not dict:
        raise TypeError("canonical JSON input must be an exact dictionary")
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return _canonical_value(value.value)
    if value is None or isinstance(value, (bool, int)):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, Mapping):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical maps require string keys")
            canonical_key = unicodedata.normalize("NFC", key)
            if canonical_key in normalized:
                raise ValueError(f"canonical key collision: {canonical_key!r}")
            normalized[canonical_key] = _canonical_value(item)
        return normalized
    if isinstance(value, (tuple, list)):
        return [_canonical_value(item) for item in value]
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def semantic_id(schema: str, payload: Mapping[str, Any]) -> str:
    """Digest `payload` under `schema` as the retired kernel's `canonical_id` did.

    Byte-identical to `omega_engine.kernel.higher_operad.canonical.canonical_id`
    (removed in f4c6fcf3), so identifiers already recorded in transcripts keep
    verifying: the domain is stripped and NFC-normalized, then must match
    IDENTIFIER.
    """
    if not isinstance(schema, str) or not schema.strip():
        raise ValueError("domain must be a non-empty string")
    domain = unicodedata.normalize("NFC", schema.strip())
    if IDENTIFIER.fullmatch(domain) is None:
        raise ValueError("domain must be a canonical identifier")
    envelope = {"domain": domain, "payload": _canonical_value(dict(payload))}
    encoded = json.dumps(
        envelope,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def strict_json_loads(raw: bytes) -> Any:
    if type(raw) is not bytes:
        raise TypeError("JSON input must be exact bytes")
    if len(raw) > 4 * 1024 * 1024:
        raise ValueError("JSON input exceeds 4 MiB")

    def exact_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number is forbidden: {value}")

    return json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=exact_pairs,
        parse_constant=reject_constant,
    )


__all__ = [
    "AUTHORITY_EFFECT_NONE",
    "canonical_json_bytes",
    "digest",
    "exact_bool",
    "exact_object",
    "identifier",
    "integer",
    "semantic_id",
    "strict_json_loads",
    "string_tuple",
    "text",
    "wire_tuple",
]
