"""Shared Kernel: Required reply fields Value Object enforcing sorting, uniqueness, and completeness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from ..exceptions import InvariantViolationError
from .field import FieldName

DEFAULT_REQUIRED_FIELDS: tuple[str, ...] = (
    "AUTHORITY_EFFECT",
    "CANDIDATE",
    "OPEN_OBSTRUCTIONS",
    "PACKET_ID",
    "PARENT",
    "RESIDUAL_COLOUR",
    "RUN_ROOT",
)


@dataclass(frozen=True, slots=True, eq=False)
class RequiredReplyFields:
    """Enriched Value Object containing immutable, sorted set of required reply fields."""

    fields: tuple[str, ...] = field(default_factory=lambda: DEFAULT_REQUIRED_FIELDS)

    def __post_init__(self) -> None:
        if not isinstance(self.fields, (tuple, list)):
            raise InvariantViolationError("RequiredReplyFields must be a sequence of strings")
        cleaned: set[str] = set()
        for f in self.fields:
            fn = FieldName.from_str(f)
            cleaned.add(str(fn))
        object.__setattr__(self, "fields", tuple(sorted(cleaned)))

    @classmethod
    def from_sequence(cls, seq: Sequence[str] | RequiredReplyFields) -> RequiredReplyFields:
        if isinstance(seq, cls):
            return seq
        if not isinstance(seq, (tuple, list, set, frozenset)):
            raise InvariantViolationError(
                f"RequiredReplyFields.from_sequence requires a sequence, got {type(seq).__name__}"
            )
        return cls(tuple(seq))

    def validate_reply(self, reply_keys: set[str] | Sequence[str]) -> tuple[bool, str | None]:
        """Checks if reply contains all required fields."""
        keys = set(reply_keys)
        missing = [f for f in self.fields if f not in keys]
        if missing:
            return False, f"Missing required fields: {missing}"
        return True, None

    def as_tuple(self) -> tuple[str, ...]:
        return self.fields

    def as_list(self) -> list[str]:
        return list(self.fields)

    def __iter__(self):
        return iter(self.fields)

    def __len__(self) -> int:
        return len(self.fields)

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.fields == other.fields

    def __hash__(self) -> int:
        return hash((type(self), self.fields))
