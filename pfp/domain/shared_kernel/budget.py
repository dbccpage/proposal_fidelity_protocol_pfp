"""Shared Kernel: Base Budget Value Object and its specialized domain variations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Self

from ..exceptions import BudgetExhaustedError, InvariantViolationError

MAX_CANDIDATE_BUDGET: int = 1024
MAX_OPERATION_BUDGET: int = 65536
MAX_EXECUTION_BUDGET: int = 100000


@dataclass(frozen=True, slots=True, eq=False)
class Budget:
    """Generic strongly-typed integer Budget Value Object base class.

    Enforces non-boolean integer type checking and range [MIN_VALUE, MAX_VALUE].
    """

    value: int

    MIN_VALUE: ClassVar[int] = 1
    MAX_VALUE: ClassVar[int] = MAX_OPERATION_BUDGET

    def __post_init__(self) -> None:
        cls_name = self.__class__.__name__
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise InvariantViolationError(
                f"{cls_name} must be an integer, got {type(self.value).__name__}"
            )
        if not (self.MIN_VALUE <= self.value <= self.MAX_VALUE):
            raise InvariantViolationError(
                f"{cls_name} {self.value} out of declared range [{self.MIN_VALUE}, {self.MAX_VALUE}]"
            )

    @classmethod
    def from_int(cls: type[Self], val: int | Self) -> Self:
        if isinstance(val, cls):
            return val
        if type(val) is not int or isinstance(val, bool):
            raise InvariantViolationError(
                f"{cls.__name__}.from_int requires an exact int, got {type(val).__name__}"
            )
        return cls(val)

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(value={self.value})"

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self.value == other.value

    def __lt__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.value <= other.value
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.value > other.value
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.value >= other.value
        return NotImplemented

    def __hash__(self) -> int:
        return hash((type(self), self.value))


@dataclass(frozen=True, slots=True, eq=False)
class CandidateBudget(Budget):
    """Bounded candidate generation budget value object."""

    value: int = 4

    MIN_VALUE: ClassVar[int] = 1
    MAX_VALUE: ClassVar[int] = MAX_CANDIDATE_BUDGET

    def check_capacity(self, current_count: int) -> None:
        """Asserts that candidate capacity is not exceeded."""
        if current_count >= self.value:
            raise BudgetExhaustedError(
                f"Candidate count ({current_count}) has reached or exceeded candidate budget ({self.value})"
            )


@dataclass(frozen=True, slots=True, eq=False)
class OperationBudget(Budget):
    """Bounded operation / step execution budget value object."""

    value: int = 16

    MIN_VALUE: ClassVar[int] = 1
    MAX_VALUE: ClassVar[int] = MAX_OPERATION_BUDGET


@dataclass(frozen=True, slots=True, eq=False)
class StepBudget(Budget):
    """Bounded single-turn step budget value object."""

    value: int = 1

    MIN_VALUE: ClassVar[int] = 1
    MAX_VALUE: ClassVar[int] = MAX_OPERATION_BUDGET


@dataclass(frozen=True, slots=True, eq=False)
class ExecutionBudget(Budget):
    """Bounded overall workflow execution budget value object."""

    value: int = 100

    MIN_VALUE: ClassVar[int] = 1
    MAX_VALUE: ClassVar[int] = MAX_EXECUTION_BUDGET


@dataclass(frozen=True, slots=True, eq=False)
class TimeBudget(Budget):
    """Bounded timeout in seconds value object."""

    value: int = 60

    MIN_VALUE: ClassVar[int] = 1
    MAX_VALUE: ClassVar[int] = 86400
