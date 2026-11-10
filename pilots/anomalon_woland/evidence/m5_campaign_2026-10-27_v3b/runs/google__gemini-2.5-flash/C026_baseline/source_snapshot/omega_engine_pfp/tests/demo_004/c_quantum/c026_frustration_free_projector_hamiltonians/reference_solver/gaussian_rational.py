# AuthorityEffect: None.
"""
Exact Gaussian rational arithmetic over Q(i).

Elements are represented as pairs (real, imag) of fractions.Fraction.
Wire encoding: ["a", "b"] representing a + b*i.
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


class GaussianRat:
    """An exact Gaussian rational a + b*i with a, b in Q."""

    __slots__ = ("r", "i")

    def __init__(self, r: Union[Fraction, str, int] = 0, i: Union[Fraction, str, int] = 0):
        self.r: Fraction = parse_fraction(r)
        self.i: Fraction = parse_fraction(i)

    @classmethod
    def zero(cls) -> "GaussianRat":
        return cls(Fraction(0), Fraction(0))

    @classmethod
    def one(cls) -> "GaussianRat":
        return cls(Fraction(1), Fraction(0))

    @classmethod
    def from_wire(cls, wire: List[Union[str, int, Fraction]]) -> "GaussianRat":
        if len(wire) != 2:
            raise ValueError(f"Invalid Gaussian rational wire format: {wire}")
        return cls(wire[0], wire[1])

    def to_wire(self) -> List[str]:
        return [format_fraction(self.r), format_fraction(self.i)]

    def is_zero(self) -> bool:
        return self.r == 0 and self.i == 0

    def conjugate(self) -> "GaussianRat":
        return GaussianRat(self.r, -self.i)

    def abs_sq(self) -> Fraction:
        return self.r * self.r + self.i * self.i

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GaussianRat):
            return False
        return self.r == other.r and self.i == other.i

    def __add__(self, other: "GaussianRat") -> "GaussianRat":
        return GaussianRat(self.r + other.r, self.i + other.i)

    def __sub__(self, other: "GaussianRat") -> "GaussianRat":
        return GaussianRat(self.r - other.r, self.i - other.i)

    def __mul__(self, other: Union["GaussianRat", Fraction, int]) -> "GaussianRat":
        if isinstance(other, (Fraction, int)):
            f = parse_fraction(other)
            return GaussianRat(self.r * f, self.i * f)
        # (a + bi)(c + di) = (ac - bd) + (ad + bc)i
        return GaussianRat(
            self.r * other.r - self.i * other.i,
            self.r * other.i + self.i * other.r,
        )

    def __truediv__(self, other: Union["GaussianRat", Fraction, int]) -> "GaussianRat":
        if isinstance(other, (Fraction, int)):
            f = parse_fraction(other)
            return GaussianRat(self.r / f, self.i / f)
        # (a + bi) / (c + di) = (a + bi)(c - di) / (c^2 + d^2)
        denom = other.abs_sq()
        if denom == 0:
            raise ZeroDivisionError("Division by zero in Q(i)")
        return GaussianRat(
            (self.r * other.r + self.i * other.i) / denom,
            (self.i * other.r - self.r * other.i) / denom,
        )

    def __repr__(self) -> str:
        return f"({format_fraction(self.r)} + {format_fraction(self.i)}i)"
