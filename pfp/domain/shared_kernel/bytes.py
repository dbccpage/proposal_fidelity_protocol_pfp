"""Shared Kernel: ByteCount Value Object for payload size metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError


@dataclass(frozen=True, slots=True, eq=False)
class ByteCount:
    """Strongly-typed byte count Value Object with non-negative integer validation."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise InvariantViolationError(
                f"ByteCount must be an integer, got {type(self.value).__name__}"
            )
        if self.value < 0:
            raise InvariantViolationError(
                f"ByteCount must be non-negative, got {self.value}"
            )

    @classmethod
    def from_int(cls: type[Self], val: int | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not int or isinstance(val, bool):
            raise InvariantViolationError(
                f"{cls.__name__}.from_int requires an exact int, got {type(val).__name__}"
            )
        return cls(val)

    @classmethod
    def from_bytes(cls: type[Self], b: bytes) -> Self:
        if type(b) is not bytes:
            raise InvariantViolationError(f"from_bytes requires exact bytes, got {type(b).__name__}")
        return cls(len(b))

    @classmethod
    def from_str(cls: type[Self], s: str, encoding: str = "utf-8") -> Self:
        if type(s) is not str:
            raise InvariantViolationError(f"from_str requires exact str, got {type(s).__name__}")
        return cls(len(s.encode(encoding)))

    def count(self) -> int:
        """Returns the raw integer count."""
        return self.value

    def is_within_limit(self, max_bytes: int) -> bool:
        """Asserts whether the count is within the declared ceiling."""
        return self.value <= max_bytes

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"ByteCount(value={self.value})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
