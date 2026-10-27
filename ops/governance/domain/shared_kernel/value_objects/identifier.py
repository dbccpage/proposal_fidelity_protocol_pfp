"""Strongly Typed Domain Identifier Value Object.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import ClassVar, Pattern, Self

from .domain_invariant_error import DomainInvariantError
from .id_kind import IdKind

_DEFAULT_ID_REGEX = re.compile(r"^[a-zA-Z0-9_\-\.:/]{1,256}$")
_HEX_ID_REGEX = re.compile(r"^[0-9a-f]{64}$|^[a-zA-Z0-9_\-\.:/]{1,256}$")


@dataclass(frozen=True, slots=True, eq=False)
class Identifier:
    """Strongly-typed domain identifier Value Object parameterized by IdKind."""

    value: str
    kind: IdKind = IdKind.GENERIC

    PATTERN: ClassVar[Pattern[str]] = _DEFAULT_ID_REGEX

    def __post_init__(self) -> None:
        if type(self.value) is not str:
            raise DomainInvariantError(
                "INVALID_ID_TYPE",
                f"Identifier value must be str, got {type(self.value).__name__}",
            )
        val = self.value.strip()
        if not val:
            raise DomainInvariantError(
                "EMPTY_IDENTIFIER", "Identifier must not be empty or whitespace only"
            )

        pat = (
            _HEX_ID_REGEX
            if self.kind
            in (IdKind.DECISION, IdKind.RECEIPT, IdKind.EVENT, IdKind.TOKEN)
            else self.PATTERN
        )
        if not pat.match(val):
            raise DomainInvariantError(
                "INVALID_IDENTIFIER_PATTERN",
                f"Invalid {self.kind.value} identifier {val!r}: must match pattern {pat.pattern}",
            )

        if val != self.value:
            object.__setattr__(self, "value", val)

    @classmethod
    def from_str(
        cls: type[Self], val: str | Self, kind: IdKind = IdKind.GENERIC
    ) -> Self:
        if isinstance(val, cls):
            if val.kind != kind and kind != IdKind.GENERIC:
                raise DomainInvariantError(
                    "ID_KIND_MISMATCH", f"Expected kind {kind}, got {val.kind}"
                )
            return val
        if type(val) is not str:
            raise DomainInvariantError(
                "INVALID_ID_COERCION",
                f"Identifier.from_str requires an exact str, got {type(val).__name__}",
            )
        return cls(value=val, kind=kind)

    # Factory constructors
    @classmethod
    def decision(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.DECISION)

    @classmethod
    def problem(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.PROBLEM)

    @classmethod
    def proposal(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.PROPOSAL)

    @classmethod
    def candidate(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.CANDIDATE)

    @classmethod
    def evidence(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.EVIDENCE)

    @classmethod
    def packet(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.PACKET)

    @classmethod
    def lease(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.LEASE)

    @classmethod
    def owner(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.OWNER)

    @classmethod
    def principal(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.PRINCIPAL)

    @classmethod
    def receipt(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.RECEIPT)

    @classmethod
    def event(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.EVENT)

    @classmethod
    def repo_worktree(cls, val: str | Self) -> Self:
        return cls.from_str(val, IdKind.REPO_WORKTREE)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.kind == other.kind and self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.kind, self.value))

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Identifier({self.value!r}, kind={self.kind.value})"
