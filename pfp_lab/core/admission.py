"""Admission of integers, rationals and names, and the core's typed failures.

AuthorityEffect: None.
Contract: urn:pfp-lab:core:admission:v1

Profile: Exact. This is the single place values enter the core. Rationals
travel as canonical strings ("3", "-2", "3/2") and become ``Fraction`` values
built from integer pairs (RULE_PY_004). Booleans are refused wherever an
integer is expected (RULE_PY_002). Floats are never admitted.

Governor refusals are verdicts, not exceptions. The exceptions here are the
only failures the core raises on purpose; each carries a stable ``ErrorCode``
that the CLI, HTTP and JSON-RPC front ends translate into their own vocabulary.
"""

from __future__ import annotations

import re
from enum import StrEnum
from fractions import Fraction

MAX_RATIONAL_CHARS = 64
NAME_PATTERN = re.compile(r"[A-Za-z0-9_.\-]{1,32}")
_RATIONAL_PATTERN = re.compile(r"(-?)(0|[1-9][0-9]*)(?:/([1-9][0-9]*))?")


class ErrorCode(StrEnum):
    """Stable failure codes shared by every front end."""

    ADMISSION = "ADMISSION"
    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    UNKNOWN_PACK = "UNKNOWN_PACK"


class LabError(Exception):
    """Base class: a failure with a stable code and a human-readable message."""

    code: ErrorCode = ErrorCode.ADMISSION

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AdmissionError(LabError, ValueError):
    """An input was refused at the boundary before any computation ran.

    It is a ``ValueError`` so that Pydantic validators report it as a
    validation failure rather than letting it escape unwrapped.
    """

    code = ErrorCode.ADMISSION


class BudgetExceededError(LabError):
    """A bounded search reached its declared step budget."""

    code = ErrorCode.BUDGET_EXCEEDED


class UnknownPackError(LabError):
    """A scenario pack identifier is not in the catalog."""

    code = ErrorCode.UNKNOWN_PACK


def admit_int(value: object, *, minimum: int, maximum: int, field: str) -> int:
    """Admit an exact integer in ``[minimum, maximum]``; refuse bool and every other type."""
    if type(value) is not int:
        raise AdmissionError(f"{field} must be an integer, got {type(value).__name__}")
    if value < minimum or value > maximum:
        raise AdmissionError(f"{field} must be between {minimum} and {maximum}, got {value}")
    return value


def admit_name(value: object, *, field: str) -> str:
    """Admit a vertex or step name: 1 to 32 characters from ``[A-Za-z0-9_.-]``."""
    if type(value) is not str:
        raise AdmissionError(f"{field} must be a string, got {type(value).__name__}")
    if NAME_PATTERN.fullmatch(value) is None:
        raise AdmissionError(f"{field} must match {NAME_PATTERN.pattern}, got {value!r}")
    return value


def parse_rational(text: object, *, field: str) -> Fraction:
    """Parse a canonical rational string into an exact ``Fraction``.

    Canonical means: an optional minus sign, no leading zeros, no "-0", and a
    denominator only when it is greater than one and coprime to the numerator.
    Exactly one spelling is admitted for every rational value, so receipts that
    hash the spelling hash the value.
    """
    if type(text) is not str:
        raise AdmissionError(f"{field} must be a rational string, got {type(text).__name__}")
    if len(text) > MAX_RATIONAL_CHARS:
        raise AdmissionError(f"{field} exceeds {MAX_RATIONAL_CHARS} characters")
    match = _RATIONAL_PATTERN.fullmatch(text)
    if match is None:
        raise AdmissionError(f"{field} is not a rational of the form p or p/q: {text!r}")
    sign, numerator_text, denominator_text = match.groups()
    numerator = int(numerator_text)
    denominator = 1 if denominator_text is None else int(denominator_text)
    value = Fraction(-numerator if sign else numerator, denominator)
    if format_rational(value) != text:
        raise AdmissionError(f"{field} is not in lowest terms or canonical form: {text!r}")
    return value


def format_rational(value: Fraction) -> str:
    """The canonical spelling of an exact rational."""
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


__all__ = [
    "MAX_RATIONAL_CHARS",
    "NAME_PATTERN",
    "AdmissionError",
    "BudgetExceededError",
    "ErrorCode",
    "LabError",
    "UnknownPackError",
    "admit_int",
    "admit_name",
    "format_rational",
    "parse_rational",
]
