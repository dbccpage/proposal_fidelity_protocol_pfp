"""Exact rational values and their canonical wire form.

The Python mirror of ``core_symbol_game_runtime::rational``. ``Fraction`` is
used here for the same reason ``BigRational`` is used there: so that "the
residual has vanished" is a **decision** rather than a tolerance.

Exact values cross the wire as **strings** (``"3/4"``, ``"-5"``, ``"0"``),
never as JSON numbers. A JSON number is a float in most readers, which would
silently undo the exactness, and the canonicalization profile
``core-sorted-json-no-float-v1`` refuses floats outright.

A ``float`` is not an exact value and is never coerced into one silently. Every
finite float *is* a dyadic rational, so the conversion would succeed -- and
that is precisely the danger: it would preserve an already-accumulated error
exactly, moving the defect one layer up rather than removing it. Callers that
hold a float must either obtain the exact value from upstream or record a
refusal.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Final

Exact = Fraction

REFUSAL_NOT_EXACT: Final = "NOT_EXACT"
REFUSAL_FLOAT_REFUSED: Final = "FLOAT_REFUSED"


class NotExactError(ValueError):
    """A value was required to be exact over Q and was not."""

    def __init__(self, value: Any, reason: str, *, code: str = REFUSAL_NOT_EXACT) -> None:
        self.value = value
        self.reason = reason
        self.code = code
        super().__init__(f"{code}: {value!r} ({reason})")


def is_exact_value(value: Any) -> bool:
    """True when ``value`` carries an exact rational, not a float.

    ``bool`` is excluded even though it is an ``int`` subclass: a flag is not a
    magnitude, and admitting it here would let ``True`` score as 1.
    """
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, Fraction))


def coerce_exact(value: Any, *, field: str) -> Exact:
    """Return ``value`` as an ``Exact``, refusing anything inexact.

    Accepts ``int``, ``Fraction``, and the canonical string form. Refuses
    ``float`` and ``bool`` outright, and refuses decimal or exponent strings
    (``"0.1"``, ``"1e-9"``) -- accepting those would mean accepting a value
    that is not exactly representable and pretending otherwise.
    """
    if isinstance(value, bool):
        raise NotExactError(value, f"{field} is a bool, not a magnitude")
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, float):
        raise NotExactError(
            value,
            f"{field} arrived as a float; supply an exact rational upstream",
            code=REFUSAL_FLOAT_REFUSED,
        )
    if isinstance(value, str):
        return parse_exact(value, field=field)
    raise NotExactError(value, f"{field} is {type(value).__name__}, not an exact rational")


def parse_exact(text: str, *, field: str = "value") -> Exact:
    """Parse the canonical string form. Inverse of :func:`to_canonical_string`.

    Deliberately narrow: an integer, or ``numer/denom``. No decimal point, no
    exponent, no whitespace tolerance.
    """
    if not isinstance(text, str) or not text:
        raise NotExactError(text, f"{field} is empty")
    numer_text, slash, denom_text = text.partition("/")
    if not slash:
        denom_text = "1"
    try:
        numer = int(numer_text)
        denom = int(denom_text)
    except ValueError:
        raise NotExactError(text, f"{field} is not an integer or numer/denom pair") from None
    if denom == 0:
        raise NotExactError(text, f"{field} has a zero denominator")
    exact = Fraction(numer, denom)
    # Parsing is part of the wire boundary, not a convenience parser.  Accepting
    # e.g. ``01``, ``-0``, ``1/02``, or whitespace would give one rational more
    # than one byte representation and therefore more than one digestable wire
    # value.  Round-trip through the renderer to make the documented canonical
    # grammar load-bearing.
    if text != to_canonical_string(exact):
        raise NotExactError(text, f"{field} is not in canonical rational form")
    return exact


def to_canonical_string(value: Exact) -> str:
    """Render an exact value as its canonical string: ``"3/4"``, ``"-5"``, ``"0"``.

    ``Fraction`` keeps itself in lowest terms, so this form is canonical: one
    value has exactly one spelling, and string equality is value equality.
    """
    if not is_exact_value(value):
        raise NotExactError(
            value,
            "canonical exact wire values must be int or Fraction, never float/bool",
        )
    exact = value if isinstance(value, Fraction) else Fraction(value)
    if exact.denominator == 1:
        return str(exact.numerator)
    return f"{exact.numerator}/{exact.denominator}"


__all__ = [
    "Exact",
    "NotExactError",
    "REFUSAL_FLOAT_REFUSED",
    "REFUSAL_NOT_EXACT",
    "coerce_exact",
    "is_exact_value",
    "parse_exact",
    "to_canonical_string",
]
