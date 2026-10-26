"""
Domain Errors and Railway-Oriented Programming (ROP) Result Monad for Operads.
=============================================================================

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E", bound="DomainError")
U = TypeVar("U")


class DomainError(Exception):
    """Base class for all domain errors."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r})"


class OperadDomainError(DomainError):
    """Base error for operadic domain violations."""
    pass


class InvalidColourError(OperadDomainError):
    """Raised when an unadmitted colour is used."""
    pass


class ArityMismatchError(OperadDomainError):
    """Raised when operation inputs do not match declared arity."""
    pass


class IllTypedCompositionError(OperadDomainError):
    """Raised when partial composition circle_i is ill-typed."""
    pass


class OperadAssociativityError(OperadDomainError):
    """Raised when operadic composition fails associativity axioms."""
    pass


class SliceViolationError(OperadDomainError):
    """Raised when an agent invokes an unlicensed operad operation."""
    pass


class MissingUnitError(OperadDomainError):
    """Raised when identity operations id_C are missing for admitted colours."""
    pass


SKILL_SIGNATURE_REFUSAL_CODES: tuple[str, ...] = (
    "UNREADABLE_SKILL_FILE",
    "MISSING_FRONTMATTER",
    "FRONTMATTER_YAML_ERROR",
    "FRONTMATTER_NOT_A_MAPPING",
    "SOURCE_COLOURS_NOT_A_LIST",
    "UNADMITTED_TARGET_COLOUR",
    "UNADMITTED_SOURCE_COLOUR",
    "DUPLICATE_OPERATION_ID",
    "OPERATION_NOT_ADMITTED",
)


class SkillSignatureRefusal(OperadDomainError):
    """A skill whose operad signature was not admitted, typed by cause.

    ``locus`` names the skill file. The message carries the code and locus so a
    caller that only keeps the string still knows which file failed and why.
    """

    def __init__(self, code: str, locus: str, detail: str) -> None:
        if code not in SKILL_SIGNATURE_REFUSAL_CODES:
            raise ValueError(f"unknown skill signature refusal code: {code!r}")
        super().__init__(f"{locus}: [{code}] {detail}")
        self.code = code
        self.locus = locus
        self.detail = detail


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    @property
    def is_ok(self) -> bool:
        return True

    @property
    def is_err(self) -> bool:
        return False

    def unwrap(self) -> T:
        return self.value

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return fn(self.value)

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return Ok(fn(self.value))

    def match(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_ok(self.value)


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True

    def unwrap(self) -> T:
        raise self.error

    def bind(self, fn: Callable[[T], Result[U, E]]) -> Result[U, E]:
        return self  # type: ignore

    def map(self, fn: Callable[[T], U]) -> Result[U, E]:
        return self  # type: ignore

    def match(self, on_ok: Callable[[T], U], on_err: Callable[[E], U]) -> U:
        return on_err(self.error)


Result = Union[Ok[T], Err[E]]
