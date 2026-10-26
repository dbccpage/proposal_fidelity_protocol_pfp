# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Exact rationals as a native fraction type.

``Q(num, den)`` holds a reduced fraction with ``den > 0``.  Equality and order
are decided by cross-multiplication of integers, never by conversion.  There
is no float path: a float, a bool, or a non-reduced pair is refused by name.

Serialized form is always ``"p/q"`` (zero is ``"0/1"``, five is ``"5/1"``).

AuthorityEffect: None
"""

from __future__ import annotations

import re
from math import gcd

from ..errors import ExactError

_Q_TEXT = re.compile(r"^(0|-?[1-9][0-9]*)/([1-9][0-9]*)$")


def _int(x: object, what: str) -> int:
    if isinstance(x, float):
        raise ExactError("RR-FLOAT", f"{what} is a float")
    if isinstance(x, bool) or not isinstance(x, int):
        raise ExactError("RR-NOT-INTEGER", f"{what} is not an integer")
    return x


class Q:
    """A reduced fraction ``num/den`` with ``den > 0``."""

    __slots__ = ("num", "den")
    num: int
    den: int

    def __init__(self, num: int, den: int = 1) -> None:
        n = _int(num, "numerator")
        d = _int(den, "denominator")
        if d <= 0:
            raise ExactError("RR-DENOMINATOR", "denominator must be positive")
        if gcd(n, d) != 1:
            raise ExactError("RR-NOT-REDUCED", f"{n}/{d} is not reduced")
        object.__setattr__(self, "num", n)
        object.__setattr__(self, "den", d)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("Q is immutable")

    @staticmethod
    def of(num: int, den: int = 1) -> "Q":
        """Normalise any integer pair with ``den != 0``."""
        n = _int(num, "numerator")
        d = _int(den, "denominator")
        if d == 0:
            raise ExactError("RR-DENOMINATOR", "zero denominator")
        if d < 0:
            n, d = -n, -d
        g = gcd(n, d)
        return Q(n // g, d // g)

    # -- comparison by cross-multiplication --------------------------------
    def _cmp(self, other: "Q") -> int:
        left = self.num * other.den
        right = other.num * self.den
        return (left > right) - (left < right)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Q):
            return NotImplemented
        return self.num * other.den == other.num * self.den

    def __hash__(self) -> int:
        return hash((self.num, self.den))

    def __lt__(self, other: "Q") -> bool:
        return self._cmp(other) < 0

    def __le__(self, other: "Q") -> bool:
        return self._cmp(other) <= 0

    def __gt__(self, other: "Q") -> bool:
        return self._cmp(other) > 0

    def __ge__(self, other: "Q") -> bool:
        return self._cmp(other) >= 0

    # -- field operations ---------------------------------------------------
    def __add__(self, other: "Q") -> "Q":
        return Q.of(self.num * other.den + other.num * self.den, self.den * other.den)

    def __sub__(self, other: "Q") -> "Q":
        return Q.of(self.num * other.den - other.num * self.den, self.den * other.den)

    def __mul__(self, other: "Q") -> "Q":
        return Q.of(self.num * other.num, self.den * other.den)

    def __neg__(self) -> "Q":
        return Q(-self.num, self.den)

    def inv(self) -> "Q":
        if self.num == 0:
            raise ExactError("RR-DIVISION-BY-ZERO", "zero has no inverse")
        return Q.of(self.den, self.num)

    def __truediv__(self, other: "Q") -> "Q":
        return self * other.inv()

    def sign(self) -> int:
        return (self.num > 0) - (self.num < 0)

    def is_zero(self) -> bool:
        return self.num == 0

    def __repr__(self) -> str:
        return f"Q({self.num}, {self.den})"

    def __str__(self) -> str:
        return fmt_q(self)


ZERO = Q(0)
ONE = Q(1)


def parse_q(text: object) -> Q:
    """Parse the canonical ``"p/q"`` form.  Refuses floats, bare integers,
    exponents, a leading ``+``, and non-reduced pairs."""
    if isinstance(text, float):
        raise ExactError("RR-FLOAT", "a float where an exact value was expected")
    if not isinstance(text, str):
        raise ExactError("RR-PARSE", f"exact values are 'p/q' strings, got {type(text).__name__}")
    m = _Q_TEXT.match(text)
    if m is None:
        raise ExactError("RR-PARSE", f"not a canonical 'p/q' value: {text!r}")
    return Q(int(m.group(1)), int(m.group(2)))


def fmt_q(x: Q) -> str:
    if not isinstance(x, Q):
        raise ExactError("RR-FLOAT" if isinstance(x, float) else "RR-PARSE", "not a Q")
    return f"{x.num}/{x.den}"
