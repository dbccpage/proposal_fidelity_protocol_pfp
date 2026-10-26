"""Q(i): pairs of exact rationals with conjugation.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import ExactError
from .q import ZERO, Q, fmt_q, parse_q


@dataclass(frozen=True)
class QI:
    re: Q
    im: Q

    def __post_init__(self) -> None:
        if not isinstance(self.re, Q) or not isinstance(self.im, Q):
            raise ExactError("RR-FLOAT", "QI parts must be exact rationals")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.re == other.re and self.im == other.im

    def __add__(self, o: "QI") -> "QI":
        if not isinstance(o, QI):
            return NotImplemented
        return QI(self.re + o.re, self.im + o.im)

    def __sub__(self, o: "QI") -> "QI":
        if not isinstance(o, QI):
            return NotImplemented
        return QI(self.re - o.re, self.im - o.im)

    def __mul__(self, o: "QI") -> "QI":
        if not isinstance(o, QI):
            return NotImplemented
        return QI(self.re * o.re - self.im * o.im, self.re * o.im + self.im * o.re)

    def __neg__(self) -> "QI":
        return QI(-self.re, -self.im)

    def conj(self) -> "QI":
        return QI(self.re, -self.im)

    def norm2(self) -> Q:
        return self.re * self.re + self.im * self.im

    def inv(self) -> "QI":
        n = self.norm2()
        if n.is_zero():
            raise ExactError("RR-DIVISION-BY-ZERO", "zero has no inverse")
        c = self.conj()
        return QI(c.re / n, c.im / n)

    def is_zero(self) -> bool:
        return self.re.is_zero() and self.im.is_zero()


def qi_from_q(x: Q) -> QI:
    return QI(x, ZERO)


def fmt_qi(z: QI) -> list[str]:
    return [fmt_q(z.re), fmt_q(z.im)]


def parse_qi(v: object) -> QI:
    if not isinstance(v, list) or len(v) != 2:
        raise ExactError("RR-PARSE", "a Q(i) value is a pair of 'p/q' strings")
    return QI(parse_q(v[0]), parse_q(v[1]))


__all__ = [
    "QI",
    "fmt_qi",
    "parse_qi",
    "qi_from_q",
]
