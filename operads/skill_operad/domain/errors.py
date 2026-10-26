"""Domain errors and Railway-Oriented Programming (ROP) result primitives.

Single Result monad for the operad package. Root modules must re-export these
symbols rather than defining parallel Success/Failure types.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")
U = TypeVar("U")


class DomainError(Exception):
    """Base class for all domain errors.

    Accepts either DomainError("message") or DomainError("CODE", "message")
    so registry dispatch and aggregate composition share one type.
    """

    def __init__(self, code_or_message: str, message: str | None = None) -> None:
        if message is None:
            self.code = "DOMAIN_ERROR"
            self.message = code_or_message
            super().__init__(code_or_message)
        else:
            self.code = code_or_message
            self.message = message
            super().__init__(f"{code_or_message}: {message}")


class InvalidColourError(DomainError):
    """Raised when an un-admitted colour is referenced."""

    def __init__(self, message: str) -> None:
        super().__init__("INVALID_COLOUR", message)


class IllTypedCompositionError(DomainError):
    """Raised when operadic substitution o_i violates source/target colour matching."""

    def __init__(self, message: str) -> None:
        super().__init__("ILL_TYPED_COMPOSITION", message)


class ArityMismatchError(DomainError):
    """Raised when operation arity does not match source colour tuple length."""

    def __init__(self, message: str) -> None:
        super().__init__("ARITY_MISMATCH", message)


class MissingUnitError(DomainError):
    """Raised when an identity unit id_C is missing for an admitted colour."""

    def __init__(self, message: str) -> None:
        super().__init__("MISSING_UNIT", message)


class SliceViolationError(DomainError):
    """Raised when an agent capability slice references unauthorized operations."""

    def __init__(self, message: str) -> None:
        super().__init__("SLICE_VIOLATION", message)


class InvariantViolationError(DomainError):
    """Raised when a mathematical or grading invariant is violated."""

    def __init__(self, message: str) -> None:
        super().__init__("INVARIANT_VIOLATION", message)


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def map(self, fn: Callable[[T], U]) -> Result[U, Any]:
        return Ok(fn(self.value))

    def and_then(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return fn(self.value)


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True

    def unwrap(self) -> None:
        if isinstance(self.error, Exception):
            raise self.error
        raise DomainError(str(self.error))

    def unwrap_err(self) -> E:
        return self.error

    def map(self, fn: Callable[[Any], Any]) -> Result[Any, E]:
        return self

    def and_then(self, fn: Callable[[Any], Any]) -> Result[Any, E]:
        return self


Result = Union[Ok[T], Err[E]]

# Compatibility aliases — prefer Ok/Err in new code.
Success = Ok
Failure = Err
