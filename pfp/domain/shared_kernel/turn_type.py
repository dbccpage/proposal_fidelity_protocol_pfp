"""Shared Kernel: TurnType Value Object and classification enum."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError


class TurnTypeKind(str, Enum):
    """Canonical turn type categories."""

    PROMPT = "prompt"
    REPLY = "reply"
    CANDIDATE = "candidate"
    EVALUATION = "evaluation"
    RECEIPT = "receipt"
    PATCH = "patch"


@dataclass(frozen=True, slots=True)
class TurnType:
    """Value object representing a typed turn category."""

    value: str = TurnTypeKind.PROMPT.value

    VALID_TYPES: ClassVar[frozenset[str]] = frozenset(t.value for t in TurnTypeKind)

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"TurnType must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip().lower()
        if not val:
            raise InvariantViolationError("TurnType must not be empty")
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def from_str(cls: type[Self], val: str | Self | TurnTypeKind) -> Self:
        if isinstance(val, cls):
            return val
        if isinstance(val, TurnTypeKind):
            return cls(val.value)
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str or TurnTypeKind, got {type(val).__name__}"
            )
        return cls(val)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"TurnType(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
