"""Railway-Oriented Result Monad Base Interface.

AuthorityEffect: None.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Generic, TypeVar

T = TypeVar("T", covariant=True)
E = TypeVar("E", covariant=True)
U = TypeVar("U")
F = TypeVar("F")


class Result(ABC, Generic[T, E]):
    """Abstract Result base class representing success (Ok) or failure (Err)."""

    @abstractmethod
    def is_ok(self) -> bool:
        """Return True if Result is Ok."""

    @abstractmethod
    def is_err(self) -> bool:
        """Return True if Result is Err."""

    @abstractmethod
    def unwrap(self) -> T:
        """Return contained Ok value or raise ValueError if Err."""

    @abstractmethod
    def unwrap_err(self) -> E:
        """Return contained Err value or raise ValueError if Ok."""

    @abstractmethod
    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        """Apply fn to contained Ok value, leaving Err untouched."""

    @abstractmethod
    def map_err(self, fn: Callable[[E], F]) -> Result[T, F]:
        """Apply fn to contained Err value, leaving Ok untouched."""

    @abstractmethod
    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        """Monadic bind: apply fn returning Result to contained Ok value."""
