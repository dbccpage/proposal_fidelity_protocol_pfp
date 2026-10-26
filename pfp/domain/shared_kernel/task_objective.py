"""Shared Kernel: TaskObjective Value Object with length and safety invariants."""

from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import InvariantViolationError

MAX_OBJECTIVE_LENGTH: int = 16384  # 16 KB max for objective statement


@dataclass(frozen=True, slots=True, eq=False)
class TaskObjective:
    """Enriched Value Object encapsulating a verified task objective string."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value.strip():
            raise InvariantViolationError("TaskObjective must be a non-empty string")
        if len(self.value) > MAX_OBJECTIVE_LENGTH:
            raise InvariantViolationError(
                f"TaskObjective length ({len(self.value)}) exceeds maximum allowed ({MAX_OBJECTIVE_LENGTH})"
            )
        object.__setattr__(self, "value", self.value.strip())

    @classmethod
    def from_str(cls, val: str | TaskObjective) -> TaskObjective:
        if isinstance(val, cls):
            return val
        if type(val) is not str:
            raise InvariantViolationError(
                f"TaskObjective.from_str requires an exact str, got {type(val).__name__}"
            )
        return cls(val)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"TaskObjective(value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash((type(self), self.value))

    def __contains__(self, item: str) -> bool:
        return item in self.value
