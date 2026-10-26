"""Shared Kernel: ContentDigest Value Object with immutable SHA-256 validation."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import DigestFormatError

_SHA256_HEX_REGEX = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True, eq=False)
class ContentDigest:
    """Strongly-typed, immutable SHA-256 digest Value Object."""

    hex_digest: str

    PATTERN: ClassVar[re.Pattern[str]] = _SHA256_HEX_REGEX

    def __post_init__(self) -> None:
        if not isinstance(self.hex_digest, str):
            raise DigestFormatError(
                f"ContentDigest must be a string, got {type(self.hex_digest).__name__}"
            )
        val = self.hex_digest.strip().lower()
        if not self.PATTERN.match(val):
            raise DigestFormatError(
                f"Invalid SHA-256 hex digest {val!r}: must be a 64-character lowercase hex string"
            )
        if val != self.hex_digest:
            object.__setattr__(self, "hex_digest", val)

    @classmethod
    def from_str(cls: type[Self], val: str | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise DigestFormatError(
                f"{cls.__name__}.from_str requires an exact str, got {type(val).__name__}"
            )
        return cls(val)

    @classmethod
    def from_bytes(cls: type[Self], b: bytes) -> Self:
        if type(b) is not bytes:
            raise DigestFormatError(f"from_bytes requires exact bytes, got {type(b).__name__}")
        return cls(hashlib.sha256(b).hexdigest())

    @classmethod
    def from_string(cls: type[Self], s: str, encoding: str = "utf-8") -> Self:
        if type(s) is not str:
            raise DigestFormatError(f"from_string requires exact str, got {type(s).__name__}")
        return cls(hashlib.sha256(s.encode(encoding)).hexdigest())

    def __str__(self) -> str:
        return self.hex_digest

    def __repr__(self) -> str:
        return f"ContentDigest(hex_digest={self.hex_digest!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.hex_digest == other.hex_digest

    def __hash__(self) -> int:
        return hash((type(self), self.hex_digest))
