"""Exact rational wire serialization and duality gap verification (Prompt 12, 34, 43).

AuthorityEffect: None.
ZERO-FLOAT Law: Pure exact rational arithmetic in Fraction.
Canonical wire serialization: Integer rationals with unit denominators serialize
WITHOUT slash (e.g. '1', '-5', '0'), never as '1/1', preserving strict canonical
parsing under omega_kernel::parse_exact. Non-integer rationals serialize as 'p/q'.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import re


@dataclass(frozen=True)
class RationalWire:
    """Canonical exact rational wire representation."""

    val: Fraction

    def __post_init__(self) -> None:
        if isinstance(self.val, float):
            raise TypeError("ZERO-FLOAT Law: RationalWire val must be Fraction, not float")
        if not isinstance(self.val, Fraction):
            raise TypeError("ZERO-FLOAT Law: RationalWire val must be Fraction instance")

    def to_wire(self) -> str:
        """Serializes to canonical wire format: integers without slash, fractions as p/q."""
        if self.val.denominator == 1:
            return str(self.val.numerator)
        return f"{self.val.numerator}/{self.val.denominator}"

    @classmethod
    def from_wire(cls, text: str) -> RationalWire:
        """Parses canonical wire format string into RationalWire. Rejects floats."""
        s = text.strip()
        if "." in s:
            raise ValueError(f"ZERO-FLOAT Law: Decimal float string '{s}' rejected on wire")

        if "/" in s:
            parts = s.split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid rational wire format: '{s}'")
            num = int(parts[0])
            den = int(parts[1])
            if den == 0:
                raise ZeroDivisionError("Zero denominator in rational wire")
            return cls(Fraction(num, den))

        # Integer format
        return cls(Fraction(int(s), 1))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.val == other.val


@dataclass(frozen=True)
class RationalDualityGap:
    """Primal-dual optimality certificate over Q."""

    primal_objective: Fraction
    dual_objective: Fraction
    duality_gap: Fraction
    is_optimal: bool

    def __post_init__(self) -> None:
        for val in (self.primal_objective, self.dual_objective, self.duality_gap):
            if isinstance(val, float):
                raise TypeError("ZERO-FLOAT Law: objectives and gap must be Fraction, not float")
            if not isinstance(val, Fraction):
                raise TypeError("ZERO-FLOAT Law: objectives and gap must be Fraction instances")

    @classmethod
    def compute(cls, primal: Fraction, dual: Fraction) -> RationalDualityGap:
        """Computes duality gap = |primal - dual| and determines exact optimality."""
        gap = abs(primal - dual)
        return cls(
            primal_objective=primal,
            dual_objective=dual,
            duality_gap=gap,
            is_optimal=(gap == Fraction(0, 1)),
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.primal_objective,
            self.dual_objective,
            self.duality_gap,
            self.is_optimal,
        ) == (
            other.primal_objective,
            other.dual_objective,
            other.duality_gap,
            other.is_optimal,
        )
