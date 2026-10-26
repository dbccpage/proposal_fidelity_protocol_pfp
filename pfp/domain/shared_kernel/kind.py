"""Shared Kernel: Kind Value Object and specialized taxonomy subtypes and enums."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar, Self

from ..exceptions import InvariantViolationError

_KIND_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.]{1,64}$")


@dataclass(frozen=True, slots=True, eq=False)
class Kind:
    """Enriched Value Object representing a domain category or kind identifier."""

    value: str

    PATTERN: ClassVar[re.Pattern[str]] = _KIND_REGEX

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError(
                f"{self.__class__.__name__} must be a string, got {type(self.value).__name__}"
            )
        val = self.value.strip().lower()
        if not self.PATTERN.match(val):
            raise InvariantViolationError(
                f"Invalid {self.__class__.__name__} {val!r}: must match pattern {self.PATTERN.pattern}"
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
        return f"{self.__class__.__name__}(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Kind) or type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))


class RoleKind(str, Enum):
    """Standard turn participant role enumeration."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    FENCE_ORACLE = "fence_oracle"


@dataclass(frozen=True, slots=True, eq=False)
class Role(Kind):
    """Specialized Kind subtype for participant roles."""

    VALID_ROLES: ClassVar[frozenset[str]] = frozenset(r.value for r in RoleKind)

    def __post_init__(self) -> None:
        # ``dataclass(slots=True)`` creates a replacement class object, so the
        # implicit ``__class__`` cell used by zero-argument super() can refer to
        # the pre-decoration class on supported Python versions.  Call the
        # base invariant explicitly so construction is portable.
        Kind.__post_init__(self)
        if self.value not in self.VALID_ROLES:
            raise InvariantViolationError(
                f"Invalid Role {self.value!r}: must be one of {sorted(self.VALID_ROLES)}"
            )

    @classmethod
    def user(cls) -> Role:
        return cls(RoleKind.USER.value)

    @classmethod
    def assistant(cls) -> Role:
        return cls(RoleKind.ASSISTANT.value)

    @classmethod
    def system(cls) -> Role:
        return cls(RoleKind.SYSTEM.value)

    @classmethod
    def operator(cls) -> Role:
        return cls(RoleKind.OPERATOR.value)

    @classmethod
    def reviewer(cls) -> Role:
        return cls(RoleKind.REVIEWER.value)

    @classmethod
    def fence_oracle(cls) -> Role:
        return cls(RoleKind.FENCE_ORACLE.value)

    @classmethod
    def from_str(cls: type[Self], val: str | Self | RoleKind) -> Self:
        if isinstance(val, cls):
            return val
        if isinstance(val, RoleKind):
            return cls(val.value)
        if type(val) is not str:
            raise InvariantViolationError(
                f"Role.from_str requires an exact str or RoleKind, got {type(val).__name__}"
            )
        return cls(val)
