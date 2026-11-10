# AuthorityEffect: None.
"""
Exact quadratic field arithmetic over Q(sqrt(2)) for C027.

Elements are represented as a + b*sqrt(2) where a, b in Q are fractions.Fraction.
Wire encoding for coordinates: [a_str, b_str] or integers [a, b].
Conforms to exact wire canonical form (unit denominators serialized without /1).
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Union


def format_fraction(f: Fraction) -> str:
    """Format Fraction to exact wire canonical form (e.g. '1', '-3', '2/3')."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def parse_fraction(val: Union[str, int, Fraction]) -> Fraction:
    """Parse string, integer, or Fraction into Fraction."""
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val, 1)
    return Fraction(val)


class QuadRat:
    """An exact element a + b*sqrt(2) in Q(sqrt(2))."""

    __slots__ = ("a", "b")

    def __init__(
        self,
        a: Union[Fraction, str, int] = 0,
        b: Union[Fraction, str, int] = 0,
    ) -> None:
        self.a: Fraction = parse_fraction(a)
        self.b: Fraction = parse_fraction(b)

    @classmethod
    def zero(cls) -> "QuadRat":
        return cls(Fraction(0), Fraction(0))

    @classmethod
    def one(cls) -> "QuadRat":
        return cls(Fraction(1), Fraction(0))

    @classmethod
    def sqrt2(cls) -> "QuadRat":
        return cls(Fraction(0), Fraction(1))

    @classmethod
    def from_wire(cls, wire: List[Union[str, int, Fraction]]) -> "QuadRat":
        if len(wire) != 2:
            raise ValueError(f"Invalid QuadRat wire format: {wire}")
        return cls(wire[0], wire[1])

    def to_wire(self) -> List[str]:
        return [format_fraction(self.a), format_fraction(self.b)]

    def is_zero(self) -> bool:
        return self.a == 0 and self.b == 0

    def is_one(self) -> bool:
        return self.a == 1 and self.b == 0

    def conjugate(self) -> "QuadRat":
        """Galois conjugate a - b*sqrt(2)."""
        return QuadRat(self.a, -self.b)

    def norm(self) -> Fraction:
        """Field norm N(a + b*sqrt(2)) = a^2 - 2*b^2 in Q."""
        return self.a * self.a - Fraction(2, 1) * self.b * self.b

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QuadRat):
            return False
        return self.a == other.a and self.b == other.b

    def __hash__(self) -> int:
        return hash((self.a, self.b))

    def __add__(self, other: "QuadRat") -> "QuadRat":
        return QuadRat(self.a + other.a, self.b + other.b)

    def __sub__(self, other: "QuadRat") -> "QuadRat":
        return QuadRat(self.a - other.a, self.b - other.b)

    def __mul__(self, other: Union["QuadRat", Fraction, int]) -> "QuadRat":
        if isinstance(other, (Fraction, int)):
            f = parse_fraction(other)
            return QuadRat(self.a * f, self.b * f)
        # (a + b*sqrt(2))(c + d*sqrt(2)) = (ac + 2bd) + (ad + bc)*sqrt(2)
        return QuadRat(
            self.a * other.a + Fraction(2, 1) * self.b * other.b,
            self.a * other.b + self.b * other.a,
        )

    def __truediv__(self, other: Union["QuadRat", Fraction, int]) -> "QuadRat":
        if isinstance(other, (Fraction, int)):
            f = parse_fraction(other)
            return QuadRat(self.a / f, self.b / f)
        n = other.norm()
        if n == 0:
            raise ZeroDivisionError("Division by zero in Q(sqrt(2))")
        # (a + b*sqrt(2)) / (c + d*sqrt(2)) = (a + b*sqrt(2))(c - d*sqrt(2)) / (c^2 - 2d^2)
        num = self * other.conjugate()
        return QuadRat(num.a / n, num.b / n)

    def __neg__(self) -> "QuadRat":
        return QuadRat(-self.a, -self.b)

    def __repr__(self) -> str:
        return f"({format_fraction(self.a)} + {format_fraction(self.b)}*sqrt(2))"
