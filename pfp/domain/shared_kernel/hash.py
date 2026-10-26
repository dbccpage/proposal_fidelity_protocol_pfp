"""Shared Kernel: Hash and Sha256Hash Value Objects for cryptographic digests."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import DigestFormatError, InvariantViolationError

_SHA256_HEX_REGEX = re.compile(r"^[0-9a-f]{64}$")
_HEX_HASH_REGEX = re.compile(r"^[0-9a-f]{32,128}$")


@dataclass(frozen=True, slots=True, eq=False)
class Hash:
    """Base immutable cryptographic Hash Value Object."""

    value: str

    PATTERN: ClassVar[re.Pattern[str]] = _HEX_HASH_REGEX

    def __post_init__(self) -> None:
        cls_name = self.__class__.__name__
        if not isinstance(self.value, str):
            raise DigestFormatError(
                f"{cls_name} must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip().lower()
        if not self.PATTERN.match(val):
            raise DigestFormatError(
                f"Invalid {cls_name} {val!r}: must match pattern {self.PATTERN.pattern}"
            )
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def from_str(cls: type[Self], val: str | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise DigestFormatError(
                f"{cls.__name__}.from_str requires an exact str, got {type(val).__name__}"
            )
        return cls(val)

    @property
    def hex_digest(self) -> str:
        return self.value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))


@dataclass(frozen=True, slots=True, eq=False)
class Sha256Hash(Hash):
    """Strongly-typed 256-bit SHA-256 cryptographic Hash Value Object."""

    PATTERN: ClassVar[re.Pattern[str]] = _SHA256_HEX_REGEX

    @classmethod
    def from_bytes(cls: type[Self], b: bytes) -> Self:
        return cls(hashlib.sha256(b).hexdigest())

    @classmethod
    def from_string(cls: type[Self], s: str, encoding: str = "utf-8") -> Self:
        return cls(hashlib.sha256(s.encode(encoding)).hexdigest())

    @classmethod
    def compute(cls: type[Self], data: bytes | str, encoding: str = "utf-8") -> Self:
        if isinstance(data, str):
            return cls.from_string(data, encoding=encoding)
        return cls.from_bytes(data)


ContentHash = Sha256Hash
