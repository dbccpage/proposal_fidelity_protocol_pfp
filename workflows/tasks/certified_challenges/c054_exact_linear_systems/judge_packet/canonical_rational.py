"""Canonical rational strings for answer fields (C053, C054).

A canonical rational is one of:

- an integer ``"n"``: optional ``-``, then ``0`` or a digit string without a
  leading zero; ``"-0"`` is not canonical;
- a reduced fraction ``"p/q"`` with ``q >= 2`` and ``gcd(|p|, q) == 1``;
  ``p != 0``.

No whitespace, no ``+``, no decimal point or exponent, ASCII digits only, and
the value must be a ``str`` (a JSON number, Boolean or null is refused).
``"4/1"`` and ``"0/1"`` are not canonical: write ``"4"`` and ``"0"``.

Both checkers of a package use this one parser, so the grammar cannot drift
between them; it is a pure syntax check and computes nothing about the answer.
The C053 and C054 copies are byte-identical (a test enforces this).
"""

from __future__ import annotations

import re
from fractions import Fraction
from math import gcd

_CANONICAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:/[1-9][0-9]*)?")


class NonCanonicalRational(ValueError):
    """The value is not a canonical rational string."""


def parse_canonical_rational(value: object) -> Fraction:
    if type(value) is not str:
        raise NonCanonicalRational(f"expected a string, got {type(value).__name__}")
    if not value.isascii() or _CANONICAL.fullmatch(value) is None:
        raise NonCanonicalRational(f"not a canonical rational: {value!r}")
    numerator_text, _, denominator_text = value.partition("/")
    if numerator_text == "-0":
        raise NonCanonicalRational("'-0' is not canonical; write '0'")
    numerator = int(numerator_text)
    if not denominator_text:
        return Fraction(numerator)
    denominator = int(denominator_text)
    if denominator == 1:
        raise NonCanonicalRational(f"{value!r} is not canonical; write {numerator_text!r}")
    if numerator == 0 or gcd(abs(numerator), denominator) != 1:
        raise NonCanonicalRational(f"{value!r} is not in lowest terms")
    return Fraction(numerator, denominator)


def canonical_rational(value: Fraction) -> str:
    if type(value) is not Fraction:
        raise TypeError("expected a Fraction")
    return str(value)
