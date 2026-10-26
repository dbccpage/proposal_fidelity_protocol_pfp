"""Shared Kernel: PatchText Value Object representing diff text."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError
from .bytes import ByteCount
from .content_digest import ContentDigest

MAX_PATCH_BYTES: int = 16 * 1024 * 1024  # 16 MB maximum single diff patch


@dataclass(frozen=True, slots=True, eq=False)
class PatchText:
    """Enriched Value Object representing a unified diff patch payload."""

    value: str

    MAX_BYTES: ClassVar[int] = MAX_PATCH_BYTES

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"PatchText must be a string, got {type(self.value).__name__}"
            )
        byte_len = len(self.value.encode("utf-8"))
        if byte_len > self.MAX_BYTES:
            raise InvariantViolationError(
                f"PatchText byte length {byte_len} exceeds maximum {self.MAX_BYTES}"
            )

    @classmethod
    def from_str(cls: type[Self], val: str | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str, got {type(val).__name__}"
            )
        return cls(val)

    def line_count(self) -> int:
        return len(self.value.splitlines())

    def byte_count(self) -> ByteCount:
        return ByteCount.from_str(self.value)

    def compute_sha256(self) -> ContentDigest:
        return ContentDigest.from_string(self.value)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"PatchText(lines={self.line_count()}, bytes={self.byte_count().count()})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
