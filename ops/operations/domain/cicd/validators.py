"""Shared domain validation helper functions."""

from __future__ import annotations

import unicodedata
from pathlib import PurePosixPath
from typing import Any

from operations.domain.cicd.constants import (
    _IDENTIFIER_RE,
    _LOWER_GIT_OID_RE,
    _LOWER_SHA256_RE,
)


def _canonical_text(value: Any, *, field: str, allow_empty: bool = False) -> str:
    """Validate that text is canonical, NFC-normalized, and free of control characters."""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    if (not value and not allow_empty) or value != value.strip():
        raise ValueError(f"{field} must not be empty or have edge whitespace")
    if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        raise ValueError(f"{field} must contain Unicode scalar values")
    if unicodedata.normalize("NFC", value) != value:
        raise ValueError(f"{field} must be NFC-normalized")
    if any(unicodedata.category(character) == "Cc" for character in value):
        raise ValueError(f"{field} must not contain control characters")
    return value


def _identifier(value: Any, *, field: str) -> str:
    """Validate that value is a lowercase stable identifier."""
    text = _canonical_text(value, field=field)
    if _IDENTIFIER_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a lowercase stable identifier")
    return text


def _sha256(value: Any, *, field: str) -> str:
    """Validate that value is a 64-character lowercase hexadecimal SHA-256 digest."""
    text = _canonical_text(value, field=field)
    if _LOWER_SHA256_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a lowercase SHA-256 digest")
    return text


def _git_oid(value: Any, *, field: str) -> str:
    """Validate that value is a 40-character lowercase hexadecimal Git commit OID."""
    text = _canonical_text(value, field=field)
    if _LOWER_GIT_OID_RE.fullmatch(text) is None:
        raise ValueError(f"{field} must be a full lowercase Git commit OID")
    return text


def _repo_path(value: Any, *, field: str, allow_dot: bool = False) -> str:
    """Validate that value is a normalized repository-relative POSIX path."""
    text = _canonical_text(value, field=field)
    if text == ".":
        if allow_dot:
            return text
        raise ValueError(f"{field} must name a repository-relative path")
    if text.startswith("/") or "\\" in text or ":" in text:
        raise ValueError(f"{field} must be a relative POSIX path")
    path = PurePosixPath(text)
    if any(part in {"", ".", ".."} for part in path.parts) or str(path) != text:
        raise ValueError(f"{field} must already be normalized")
    return text


def _argv_item(value: Any, *, field: str) -> str:
    """Validate an individual argument vector item as canonical text."""
    return _canonical_text(value, field=field)


def _sorted_unique(
    values: list[str] | tuple[str, ...], *, field: str, casefold_unique: bool = False
) -> tuple[str, ...]:
    """Validate that a sequence of strings is strictly sorted by UTF-8 bytes and unique."""
    result = tuple(values)
    if result != tuple(sorted(result, key=lambda item: item.encode("utf-8"))):
        raise ValueError(f"{field} must be sorted by UTF-8 ordinal bytes")
    if len(result) != len(set(result)):
        raise ValueError(f"{field} must be unique")
    if casefold_unique and len({item.casefold() for item in result}) != len(result):
        raise ValueError(f"{field} must be casefold collision-free")
    return result
