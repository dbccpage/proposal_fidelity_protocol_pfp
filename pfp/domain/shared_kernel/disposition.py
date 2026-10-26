"""Shared Kernel: Disposition Value Object for lifecycle and gate verification status.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ..exceptions import InvariantViolationError


class DispositionState(str, Enum):
    """Canonical disposition states."""

    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    PASS = "PASS"
    FAIL = "FAIL"
    CLOSED = "CLOSED"


@dataclass(frozen=True, slots=True, eq=False)
class Disposition:
    """Enriched Value Object representing a run or gate disposition."""

    value: str = DispositionState.OPEN.value

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise InvariantViolationError("Disposition value must be a string")
        upper = self.value.strip().upper()
        object.__setattr__(self, "value", upper)

    @classmethod
    def open_state(cls) -> Disposition:
        return cls(DispositionState.OPEN.value)

    @classmethod
    def accepted(cls) -> Disposition:
        return cls(DispositionState.ACCEPTED.value)

    @classmethod
    def rejected(cls) -> Disposition:
        return cls(DispositionState.REJECTED.value)

    @classmethod
    def pass_state(cls) -> Disposition:
        return cls(DispositionState.PASS.value)

    @classmethod
    def fail_state(cls) -> Disposition:
        return cls(DispositionState.FAIL.value)

    @classmethod
    def from_str(cls, val: str | Disposition | DispositionState) -> Disposition:
        if isinstance(val, cls):
            return val
        if isinstance(val, DispositionState):
            return cls(val.value)
        if type(val) is not str:
            raise InvariantViolationError(
                f"Disposition.from_str requires an exact str or DispositionState, got {type(val).__name__}"
            )
        return cls(val)

    def is_terminal(self) -> bool:
        return self.value in (
            DispositionState.ACCEPTED.value,
            DispositionState.REJECTED.value,
            DispositionState.CLOSED.value,
            DispositionState.PASS.value,
            DispositionState.FAIL.value,
        )

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Disposition(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))
