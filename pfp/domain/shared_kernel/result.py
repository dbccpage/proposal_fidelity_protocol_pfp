"""Railway-Oriented Programming (ROP) Result[T, E] Monad.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, NoReturn, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
E2 = TypeVar("E2")


class ResultError(Exception):
    """Exception raised when attempting an unsafe unwrap on a Failure."""


@dataclass(frozen=True, slots=True)
class Success(Generic[T]):
    """Successful computation track holding a value of type T."""

    value: T

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: Any) -> T:
        return self.value

    def map(self, fn: Callable[[T], U]) -> Result[U, Any]:
        return Success(fn(self.value))

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return fn(self.value)

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self.bind(fn)

    def map_err(self, fn: Callable[[Any], Any]) -> Result[T, Any]:
        return self


@dataclass(frozen=True, slots=True)
class Failure(Generic[E]):
    """Failure computation track holding an error of type E."""

    error: E

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True

    def unwrap(self) -> NoReturn:
        raise ResultError(f"Attempted to unwrap Failure: {self.error}")

    def unwrap_or(self, default: U) -> U:
        return default

    def map(self, fn: Callable[[Any], Any]) -> Result[Any, E]:
        return self

    def bind(self, fn: Callable[[Any], Result[Any, Any]]) -> Result[Any, E]:
        return self

    def and_then(self, fn: Callable[[Any], Result[Any, Any]]) -> Result[Any, E]:
        return self

    def map_err(self, fn: Callable[[E], E2]) -> Result[Any, E2]:
        return Failure(fn(self.error))


# Type alias for Result
Result = Union[Success[T], Failure[E]]
Ok = Success
Err = Failure


def ok(value: T) -> Success[T]:
    """Convenience factory for Success[T]."""
    return Success(value)


def err(error: E) -> Failure[E]:
    """Convenience factory for Failure[E]."""
    return Failure(error)


__all__ = [
    "Err",
    "Failure",
    "Ok",
    "Result",
    "ResultError",
    "Success",
    "err",
    "ok",
]
