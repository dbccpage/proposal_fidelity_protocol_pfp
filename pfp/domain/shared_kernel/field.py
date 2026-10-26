"""Shared Kernel: Field and FieldName Value Objects for structured contract keys."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError

_FIELD_NAME_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")


@dataclass(frozen=True, slots=True, eq=False)
class FieldName:
    """Enriched Value Object representing a single validated contract field key."""

    value: str

    PATTERN: ClassVar[re.Pattern[str]] = _FIELD_NAME_REGEX

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"FieldName must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip()
        if not self.PATTERN.match(val):
            raise InvariantViolationError(
                f"Invalid FieldName {val!r}: must match pattern {self.PATTERN.pattern}"
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
        return f"FieldName(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
