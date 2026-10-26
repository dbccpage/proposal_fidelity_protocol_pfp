"""Shared Kernel: MediaType Value Object for MIME/content types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError


@dataclass(frozen=True, slots=True)
class MediaType:
    """Strongly-typed MIME Media Type Value Object."""

    value: str = "text/plain; charset=utf-8"

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"MediaType must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip().lower()
        if not val or "/" not in val:
            raise InvariantViolationError(
                f"Invalid MediaType {self.value!r}: must be a valid MIME type"
            )
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def diff(cls) -> MediaType:
        return cls("text/x-diff; charset=utf-8")

    @classmethod
    def plain_text(cls) -> MediaType:
        return cls("text/plain; charset=utf-8")

    @classmethod
    def json(cls) -> MediaType:
        return cls("application/json")

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
        return f"MediaType(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
