"""Cross-context shared kernel Value Objects.

Enforces RULE_VO_EXACT_TYPE_EQUALITY_001: Strict exact-type equality rejecting
cross-class comparison and type confusion.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from enum import Enum

from .result import Ok, Refusal, Result


class ValueParseCode(str, Enum):
    """Stable refusal codes for untrusted value-object wire input."""

    TYPE = "TYPE"
    FORMAT = "FORMAT"
    TOO_LONG = "TOO_LONG"


@dataclass(frozen=True)
class ValueParseRefusal:
    """Bounded diagnostic returned when a wire value is not admitted."""

    code: ValueParseCode
    message: str


class AuthorityEffect(str, Enum):
    """Authority ceiling invariant. In MSS-N, domain packets carry strictly None."""
    NONE = "None"


@dataclass(frozen=True)
class StageLevel:
    """Discrete stratum level in the MSS-N tower (0 to 21+)."""
    level: int

    def __post_init__(self) -> None:
        if not isinstance(self.level, int) or isinstance(self.level, bool):
            raise TypeError("StageLevel must be an integer")
        if self.level < 0:
            raise ValueError(f"StageLevel cannot be negative, got {self.level}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, StageLevel)
        return self.level == other.level

    def __hash__(self) -> int:
        return hash((type(self), self.level))

    def __lt__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, StageLevel)
        return self.level < other.level

    def __le__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        assert isinstance(other, StageLevel)
        return self.level <= other.level

    def __repr__(self) -> str:
        return f"StageLevel({self.level})"


@dataclass(frozen=True)
class Rational:
    """Canonical exact rational p/q in lowest terms (q > 0, gcd(|p|, q) = 1)."""
    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if not isinstance(self.numerator, int) or isinstance(self.numerator, bool):
            raise TypeError("Numerator must be an integer")
        if not isinstance(self.denominator, int) or isinstance(self.denominator, bool):
            raise TypeError("Denominator must be an integer")
        if self.denominator <= 0:
            raise ValueError(f"Denominator must be strictly positive, got {self.denominator}")
        g = math.gcd(abs(self.numerator), self.denominator)
        if g > 1:
            object.__setattr__(self, "numerator", self.numerator // g)
            object.__setattr__(self, "denominator", self.denominator // g)

    @classmethod
    def parse_wire(cls, raw: object) -> Result[Rational, ValueParseRefusal]:
        """Parse an untrusted rational without throwing across the boundary."""
        if not isinstance(raw, str):
            return Refusal(ValueParseRefusal(ValueParseCode.TYPE, "rational wire value must be a string"))
        if len(raw) > 256:
            return Refusal(ValueParseRefusal(ValueParseCode.TOO_LONG, "rational wire value exceeds 256 characters"))
        match = re.fullmatch(r"(-?[0-9]+)/([1-9][0-9]*)", raw.strip())
        if not match:
            return Refusal(ValueParseRefusal(ValueParseCode.FORMAT, "rational wire value must match p/q with q > 0"))
        num = int(match.group(1))
        den = int(match.group(2))
        return Ok(cls(num, den))

    def to_wire(self) -> str:
        return f"{self.numerator}/{self.denominator}"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Rational)
        return self.numerator == other.numerator and self.denominator == other.denominator

    def __hash__(self) -> int:
        return hash((type(self), self.numerator, self.denominator))

    def __repr__(self) -> str:
        return f"Rational({self.numerator}/{self.denominator})"


@dataclass(frozen=True)
class ContentDigest:
    """Immutable 64-hex SHA-256 or BLAKE3 content digest."""
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("ContentDigest must be a string")
        cleaned = self.value.strip().lower()
        if not re.fullmatch(r"^[0-9a-f]{64}$", cleaned):
            raise ValueError(f"ContentDigest must be a 64-character lowercase hex string, got {self.value!r}")
        object.__setattr__(self, "value", cleaned)

    @classmethod
    def parse_wire(cls, raw: object) -> Result[ContentDigest, ValueParseRefusal]:
        """Parse an untrusted digest with bounded, non-reflective diagnostics."""
        if not isinstance(raw, str):
            return Refusal(ValueParseRefusal(ValueParseCode.TYPE, "digest wire value must be a string"))
        if len(raw) > 64:
            return Refusal(ValueParseRefusal(ValueParseCode.TOO_LONG, "digest wire value exceeds 64 characters"))
        if not re.fullmatch(r"[0-9a-fA-F]{64}", raw):
            return Refusal(ValueParseRefusal(ValueParseCode.FORMAT, "digest wire value must be 64 hexadecimal characters"))
        return Ok(cls(raw))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ContentDigest)
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))

    @property
    def digest_hex(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ContentDigest({self.value[:8]}...)"
