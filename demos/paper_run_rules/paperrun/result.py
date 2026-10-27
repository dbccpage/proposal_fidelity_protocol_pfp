"""Immutable railway result and typed refusal values.

Canonical Railway-Oriented Programming (ROP) result monad and typed refusal records
for domain operations across the Engine.
Refusal is a (code, message, locus, details) record carried as Err(Refusal(...)),
is_ok / is_err are properties, unwrap_err() returns the error, and sequence/traverse
accumulate Results into tuples.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Callable, Generic, Iterable, List, NoReturn, Tuple, TypeVar, Union, cast

T = TypeVar("T")
U = TypeVar("U")
E = TypeVar("E")
F = TypeVar("F")

_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/@-]*$")


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return unicodedata.normalize("NFC", value.strip())


def _require_identifier(value: Any, field: str) -> str:
    normalized = _require_text(value, field)
    if _IDENTIFIER.fullmatch(normalized) is None:
        raise ValueError(f"{field} must be a canonical identifier")
    return normalized


@dataclass(frozen=True)
class Refusal:
    code: str
    message: str
    locus: str = ""
    details: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _require_identifier(self.code, "code"))
        object.__setattr__(self, "message", _require_text(self.message, "message"))
        if self.locus:
            object.__setattr__(self, "locus", _require_text(self.locus, "locus"))
        normalized = tuple((_require_text(k, "detail key"), str(v)) for k, v in self.details)
        if len({key for key, _ in normalized}) != len(normalized):
            raise ValueError("refusal detail keys must be unique")
        object.__setattr__(self, "details", tuple(sorted(normalized)))

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "locus": self.locus,
            "details": {key: value for key, value in self.details},
        }


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

    def unwrap_err(self) -> NoReturn:
        raise ValueError("cannot unwrap_err from Ok")

    def map(self, function: Callable[[T], U]) -> "Ok[U]":
        return Ok(function(self.value))

    def map_error(self, function: Callable[[E], F]) -> "Ok[T]":
        del function
        return self

    def bind(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return function(self.value)

    def and_then(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        return function(self.value)

    def recover(self, function: Callable[[E], "Result[T, F]"]) -> "Ok[T]":
        del function
        return self


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True

    def unwrap(self) -> NoReturn:
        raise ValueError(f"cannot unwrap Err: {self.error}")

    def unwrap_err(self) -> E:
        return self.error

    def map(self, function: Callable[[T], U]) -> "Err[E]":
        del function
        return self

    def map_error(self, function: Callable[[E], F]) -> "Err[F]":
        return Err(function(self.error))

    def bind(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        del function
        return cast("Result[U, E]", self)

    def and_then(self, function: Callable[[T], "Result[U, E]"]) -> "Result[U, E]":
        del function
        return cast("Result[U, E]", self)

    def recover(self, function: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        return function(self.error)


Result = Union[Ok[T], Err[E]]


def sequence(results: Iterable[Result[T, E]]) -> Result[Tuple[T, ...], E]:
    """Combine an iterable of Results into a Result containing a tuple of values."""
    values: List[T] = []
    for r in results:
        if r.is_err:
            return cast(Err[E], r)
        values.append(r.unwrap())
    return Ok(tuple(values))


def traverse(items: Iterable[T], function: Callable[[T], Result[U, E]]) -> Result[Tuple[U, ...], E]:
    """Map each item to a Result and accumulate into a tuple."""
    values: List[U] = []
    for item in items:
        r = function(item)
        if r.is_err:
            return cast(Err[E], r)
        values.append(r.unwrap())
    return Ok(tuple(values))


__all__ = ["Err", "Ok", "Refusal", "Result", "sequence", "traverse"]
