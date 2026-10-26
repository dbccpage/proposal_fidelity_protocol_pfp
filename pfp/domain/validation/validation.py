"""Shared fail-closed validation primitives for symbol_game domain.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from omega_engine_pfp.domain.shared_kernel.path import is_normalized_relative_posix
import re
from typing import Any, Mapping, Sequence

from omega_engine_pfp.domain.errors import (
    CanonicalizationError,
    FORBIDDEN_WIRE_KEYS,
    REFUSAL_FORBIDDEN_AUTHORITY_FIELD,
)

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STABLE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")

MAX_STRING_LENGTH = 8192
MAX_ID_LENGTH = 128
MAX_ARRAY_LENGTH = 256
MAX_CONSTRUCTORS = 64
MAX_OBSTRUCTIONS = 256
MAX_DEMANDS = 64
MAX_KILL_CONDITIONS = 32
MAX_DIGEST_REFS = 64
MAX_BODY_BYTES = 1024 * 1024
MAX_PATH_LENGTH = 2048


def _fail(message: str) -> None:
    """Raise CanonicalizationError unconditionally."""
    raise CanonicalizationError(message)


def is_valid_hex64(digest: str) -> bool:
    """Return True iff digest is a 64-character lowercase hex string."""
    return bool(_SHA256.fullmatch(digest))


def normalize_utf8_lf(data: bytes) -> bytes:
    """Convert CRLF or bare CR line endings to LF, strictly preserving UTF-8 encoding."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def raw_content_sha256(data: bytes) -> tuple[str, int]:
    """Compute Layer B (raw content) SHA-256 and byte length."""
    return hashlib.sha256(data).hexdigest(), len(data)


def _require_exact_dict(value: Any, label: str) -> dict[str, Any]:
    """Ensure value is a pure string-keyed dictionary with no forbidden authority keys."""
    if type(value) is not dict or any(type(key) is not str for key in value):
        _fail(f"{label} must be an exact string-keyed object")
    bad = FORBIDDEN_WIRE_KEYS & frozenset(value)
    if bad:
        _fail(f"{REFUSAL_FORBIDDEN_AUTHORITY_FIELD}: {label} carries forbidden authority fields: {', '.join(sorted(bad))}")
    return value


def _require_fields(
    wire: Mapping[str, Any], required: frozenset[str], label: str
) -> None:
    """Ensure exact match of wire keys against required key set."""
    keys = frozenset(wire)
    missing = required - keys
    unknown = keys - required
    if missing:
        _fail(f"{label} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        _fail(f"{label} has unknown fields: {', '.join(sorted(unknown))}")


def _require_string(value: Any, label: str, *, nonempty: bool = False) -> str:
    """Ensure value is an exact string within resource limits."""
    if type(value) is not str:
        _fail(f"{label} must be an exact string")
    if len(value.encode("utf-8")) > MAX_STRING_LENGTH:
        _fail(f"{label} exceeds the string resource limit")
    if nonempty and (not value or value.strip() != value):
        _fail(f"{label} must be a nonempty normalized string")
    return value


def _require_stable_id(value: Any, label: str) -> str:
    """Ensure value is a valid stable identifier."""
    value = _require_string(value, label, nonempty=True)
    if len(value) > MAX_ID_LENGTH or not _STABLE_ID.fullmatch(value):
        _fail(f"{label} contains invalid identifier characters or exceeds limit")
    return value


def _require_digest(value: Any, label: str) -> str:
    """Ensure value is a valid lowercase 64-hex SHA-256 digest."""
    value = _require_string(value, label, nonempty=True)
    if not is_valid_hex64(value):
        _fail(f"{label} must be a lowercase 64-character hex digest")
    return value


def _require_digest_or_none(value: Any, label: str) -> str | None:
    """Ensure value is either None or a valid lowercase 64-hex SHA-256 digest."""
    if value is None:
        return None
    return _require_digest(value, label)


def _require_int(
    value: Any,
    label: str,
    *,
    min_value: int | None = None,
    max_value: int | None = None,
) -> int:
    """Ensure value is an exact int within bounds."""
    if type(value) is not int or type(value) is bool:
        _fail(f"{label} must be an integer")
    if min_value is not None and value < min_value:
        _fail(f"{label} must be >= {min_value}")
    if max_value is not None and value > max_value:
        _fail(f"{label} must be <= {max_value}")
    return value


def _require_nonnegative_int(value: Any, label: str) -> int:
    """Ensure value is a nonnegative integer."""
    return _require_int(value, label, min_value=0)


def _require_positive_int(value: Any, label: str, *, maximum: int | None = None) -> int:
    """Ensure value is a positive integer (>= 1) with optional maximum."""
    return _require_int(value, label, min_value=1, max_value=maximum)


def _require_optional_digest(value: Any, label: str) -> str | None:
    """Ensure value is either None or a valid lowercase 64-hex SHA-256 digest."""
    return _require_digest_or_none(value, label)


def _require_bool(value: Any, label: str) -> bool:
    """Ensure value is an exact bool."""
    if type(value) is not bool:
        _fail(f"{label} must be a boolean")
    return value


def _require_bool_or_none(value: Any, label: str) -> bool | None:
    """Ensure value is either None or an exact bool."""
    if value is None:
        return None
    return _require_bool(value, label)


def _require_optional_bool(value: Any, label: str) -> bool | None:
    """Ensure value is either None or an exact bool."""
    return _require_bool_or_none(value, label)


def _require_float_or_none(value: Any, label: str) -> float | None:
    """Ensure value is either None or an exact float."""
    if value is None:
        return None
    if type(value) is not float:
        _fail(f"{label} must be a float or null")
    return value


def _require_optional_nonnegative_int(value: Any, label: str) -> int | None:
    """Ensure value is either None or a nonnegative integer."""
    if value is None:
        return None
    return _require_nonnegative_int(value, label)


def _validate_ordered_unique_strings(value: Any, label: str) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str for item in value):
        _fail(f"{label} must be an exact tuple of strings")
    if any(not item or item.strip() != item for item in value):
        _fail(f"{label} entries must be nonempty normalized strings")
    if len(value) > MAX_ARRAY_LENGTH:
        _fail(f"{label} exceeds the array resource limit")
    for index, item in enumerate(value):
        _require_string(item, f"{label}[{index}]", nonempty=True)
    if tuple(sorted(value)) != value or len(value) != len(set(value)):
        _fail(f"{label} must be unique and sorted")
    return value


def _string_tuple_from_wire(value: Any, label: str) -> tuple[str, ...]:
    if type(value) is not list:
        _fail(f"{label} must be an array")
    if len(value) > MAX_ARRAY_LENGTH:
        _fail(f"{label} exceeds the array resource limit")
    result = tuple(
        _require_string(item, f"{label}[{index}]", nonempty=True)
        for index, item in enumerate(value)
    )
    _validate_ordered_unique_strings(result, label)
    return result


def _validate_repo_relative_path(value: Any, label: str) -> str:
    value = _require_string(value, label, nonempty=True)
    if len(value) > MAX_PATH_LENGTH or "\\" in value or "\x00" in value:
        _fail(f"{label} must be a normalized relative POSIX path")
    if not is_normalized_relative_posix(value):
        _fail(f"{label} must be a normalized relative POSIX path")
    return value


__all__ = [
    "MAX_ARRAY_LENGTH",
    "MAX_BODY_BYTES",
    "MAX_CONSTRUCTORS",
    "MAX_DEMANDS",
    "MAX_DIGEST_REFS",
    "MAX_ID_LENGTH",
    "MAX_KILL_CONDITIONS",
    "MAX_OBSTRUCTIONS",
    "MAX_PATH_LENGTH",
    "MAX_STRING_LENGTH",
    "_fail",
    "_require_bool",
    "_require_bool_or_none",
    "_require_digest",
    "_require_digest_or_none",
    "_require_exact_dict",
    "_require_fields",
    "_require_float_or_none",
    "_require_int",
    "_require_nonnegative_int",
    "_require_optional_bool",
    "_require_optional_digest",
    "_require_optional_nonnegative_int",
    "_require_positive_int",
    "_require_stable_id",
    "_require_string",
    "_string_tuple_from_wire",
    "_validate_ordered_unique_strings",
    "_validate_repo_relative_path",
    "is_valid_hex64",
    "normalize_utf8_lf",
    "raw_content_sha256",
]
