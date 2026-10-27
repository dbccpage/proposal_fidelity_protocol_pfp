"""Sequence Number Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from .domain_invariant_error import DomainInvariantError


@dataclass(frozen=True, slots=True, eq=False)
class SequenceNumber:
    """Monotonic event sequence number value object."""

    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or isinstance(self.value, bool):
            raise DomainInvariantError("INVALID_SEQUENCE_TYPE", f"SequenceNumber must be int, got {type(self.value).__name__}")
        if self.value < 0:
            raise DomainInvariantError("NEGATIVE_SEQUENCE_NUMBER", f"SequenceNumber cannot be negative: {self.value}")

    @classmethod
    def from_int(cls, val: int | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not int or isinstance(val, bool):
            raise DomainInvariantError("INVALID_SEQUENCE_COERCION", f"SequenceNumber.from_int requires int, got {type(val).__name__}")
        return cls(val)

    def bump(self) -> SequenceNumber:
        return SequenceNumber(self.value + 1)

    def next(self) -> SequenceNumber:
        return self.bump()

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"SequenceNumber(value={self.value})"
