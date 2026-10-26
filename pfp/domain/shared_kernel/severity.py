"""Shared Kernel: Severity Value Object and Enumeration for conditions and alerts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError


class SeverityKind(str, Enum):
    """Canonical severity levels."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    BLOCKING = "BLOCKING"
    FATAL = "FATAL"


@dataclass(frozen=True, slots=True)
class Severity:
    """Enriched Value Object representing a condition severity rating."""

    value: str = SeverityKind.INFO.value

    VALID_LEVELS: ClassVar[frozenset[str]] = frozenset(k.value for k in SeverityKind)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"Severity must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip().upper()
        if val not in self.VALID_LEVELS:
            raise InvariantViolationError(
                f"Invalid Severity {val!r}: must be one of {sorted(self.VALID_LEVELS)}"
            )
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def info(cls) -> Severity:
        return cls(SeverityKind.INFO.value)

    @classmethod
    def low(cls) -> Severity:
        return cls(SeverityKind.LOW.value)

    @classmethod
    def high(cls) -> Severity:
        return cls(SeverityKind.HIGH.value)

    @classmethod
    def critical(cls) -> Severity:
        return cls(SeverityKind.CRITICAL.value)

    @classmethod
    def blocking(cls) -> Severity:
        return cls(SeverityKind.BLOCKING.value)

    @classmethod
    def fatal(cls) -> Severity:
        return cls(SeverityKind.FATAL.value)

    @classmethod
    def from_str(cls: type[Self], val: str | Self | SeverityKind) -> Self:
        if isinstance(val, cls):
            return val
        if isinstance(val, SeverityKind):
            return cls(val.value)
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str or SeverityKind, got {type(val).__name__}"
            )
        return cls(val)

    def is_blocking_or_higher(self) -> bool:
        return self.value in (
            SeverityKind.CRITICAL.value,
            SeverityKind.BLOCKING.value,
            SeverityKind.FATAL.value,
        )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Severity(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
