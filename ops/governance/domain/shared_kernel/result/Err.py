"""Railway-Oriented Result Err Variant.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from .result import Result

T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)
U = TypeVar("U")
F = TypeVar("F")


@dataclass(frozen=True, slots=True, eq=True)
class Err(Result[T, E], Generic[T, E]):
    """Failed computation holding error of type E."""

    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise ValueError(f"Called unwrap on Err: {self.error!r}")

    def unwrap_err(self) -> E:
        return self.error

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return Err(self.error)

    def map_err(self, fn: Callable[[E], F]) -> Result[T, F]:
        return Err(fn(self.error))

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return Err(self.error)
