"""Shared Kernel: Description Value Object enforcing length and non-empty bounds."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError

MAX_DESCRIPTION_LENGTH: int = 4096


@dataclass(frozen=True, slots=True)
class Description:
    """Enriched Value Object representing a domain description string."""

    value: str

    MAX_LENGTH: ClassVar[int] = MAX_DESCRIPTION_LENGTH

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"Description must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip()
        if not val:
            raise InvariantViolationError("Description must not be empty or whitespace only")
        if len(val) > self.MAX_LENGTH:
            raise InvariantViolationError(
                f"Description length ({len(val)}) exceeds maximum limit of {self.MAX_LENGTH} characters"
            )
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
        return f"Description(value={self.value!r})"

    def __len__(self) -> int:
        return len(self.value)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
