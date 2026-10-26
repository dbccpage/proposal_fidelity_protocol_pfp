"""Railway-Oriented Programming (ROP) Result Monad for DDD domain kernels.

Enforces RULE_ROP_RESULT_MONAD_001: Pure monadic returns over bare exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def is_refusal(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return Ok(fn(self.value))

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return fn(self.value)

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self.bind(fn)

    def map_err(self, fn: Callable[[E], object]) -> Result[T, E]:
        return self


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def is_refusal(self) -> bool:
        return False

    def unwrap(self) -> T:
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return self

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self

    def map_err(self, fn: Callable[[E], U]) -> Result[T, U]:
        return Err(fn(self.error))


@dataclass(frozen=True)
class Refusal(Generic[E]):
    """Typed domain refusal for boundary violations and unadmitted requests."""
    refusal: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def is_refusal(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise ValueError(f"Called unwrap on Refusal: {self.refusal}")

    def unwrap_or(self, default: T) -> T:
        return default

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return self

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self

    def map_err(self, fn: Callable[[E], U]) -> Result[T, U]:
        return Refusal(fn(self.refusal))


Result = Union[Ok[T], Err[E], Refusal[E]]
