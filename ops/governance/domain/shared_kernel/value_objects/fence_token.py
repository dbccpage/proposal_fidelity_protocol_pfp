"""Strongly typed FenceToken Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from .domain_invariant_error import DomainInvariantError


@dataclass(frozen=True, slots=True, eq=False)
class FenceToken:
    """Monotonic fencing token value object."""

    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int or isinstance(self.value, bool):
            raise DomainInvariantError("INVALID_FENCE_TOKEN_TYPE", f"FenceToken must be int, got {type(self.value).__name__}")
        if self.value < 0:
            raise DomainInvariantError("NEGATIVE_FENCE_TOKEN", f"FenceToken cannot be negative: {self.value}")

    @classmethod
    def from_int(cls, val: int | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not int or isinstance(val, bool):
            raise DomainInvariantError("INVALID_FENCE_TOKEN_COERCION", f"FenceToken.from_int requires int, got {type(val).__name__}")
        return cls(val)

    def next_token(self) -> FenceToken:
        return FenceToken(self.value + 1)

    def next(self) -> FenceToken:
        return self.next_token()

    def is_stale_compared_to(self, current: FenceToken | int) -> bool:
        curr_val = current.value if isinstance(current, FenceToken) else current
        return self.value < curr_val

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
        return f"FenceToken(value={self.value})"
