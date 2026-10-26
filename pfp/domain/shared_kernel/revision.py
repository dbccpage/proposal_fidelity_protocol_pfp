"""Shared Kernel: Revision Value Object for VCS revisions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError


@dataclass(frozen=True, slots=True, eq=False)
class Revision:
    """Strongly-typed VCS Revision / Git Commit / Branch identifier."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"Revision must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip()
        if not val:
            raise InvariantViolationError("Revision must not be empty or whitespace only")
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def from_str(cls: type[Self], val: str | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str, got {type(val).__name__}"
            )
        return cls(val)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Revision(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
