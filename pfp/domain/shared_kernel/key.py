"""Shared Kernel: Key and WireKey Value Objects with polymorphic equality.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
import re
from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError
from .key_type import KeyType

_KEY_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.:/@]{1,128}$")


@dataclass(frozen=True, slots=True, eq=False)
class Key:
    """Enriched Value Object representing a domain or wire key."""

    value: str

    PATTERN: ClassVar[re.Pattern[str]] = _KEY_REGEX

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"{self.__class__.__name__} must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip()
        if not self.PATTERN.match(val):
            raise InvariantViolationError(
                f"Invalid {self.__class__.__name__} {val!r}: must match pattern {self.PATTERN.pattern}"
            )
        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def from_str(cls: type[Self], val: str | Self | Enum) -> Self:
        if isinstance(val, cls):
            return val
        if isinstance(val, Enum):
            val = val.value
        if type(val) is not str:
            raise InvariantViolationError(
                f"{cls.__name__}.from_str requires an exact str or Enum, got {type(val).__name__}"
            )
        return cls(val)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))


@dataclass(frozen=True, slots=True, eq=False)
class WireKey(Key):
    """Specialized Key Value Object representing a wire serialization key."""

    @property
    def key_type(self) -> KeyType:
        return KeyType.WIRE


@dataclass(frozen=True, slots=True, eq=False)
class ContextKey(Key):
    """Specialized Key Value Object representing an evaluation context key."""

    @property
    def key_type(self) -> KeyType:
        return KeyType.CONTEXT
