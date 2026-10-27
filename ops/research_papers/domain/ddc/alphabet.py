"""Discrete Deformation Calculus (DDC) 8-Letter Operational Alphabet.

A typed algebra of what a computation did to an obstruction:
records how an obstruction was handled, not whether the world is true.
"""

from __future__ import annotations

from enum import Enum

from operads.canon import DDC_LETTER


class _DDCRuneMethods(str):
    """Behaviour of a DDC rune; the runes themselves come from the operad canon."""

    @classmethod
    def from_str(cls, val: str) -> DDCRune:
        """Parse string or ascii/unicode rune."""
        val = val.strip()
        if val in ("Λ", "LAMBDA", "L"):
            return cls.LIFT
        for rune in cls:
            if rune.value == val or rune.name == val:
                return rune
        raise ValueError(f"Unknown DDC rune '{val}'. Must be one of {list(cls)}")

    def is_terminal(self) -> bool:
        return self == DDCRune.T

    def is_refusal(self) -> bool:
        return self == DDCRune.M


# The eight runes of A_DDC, from code/rust/core_operad_canon; the lift rune is named LIFT here.
DDCRune = Enum("DDCRune", [("LIFT" if letter == "Λ" else letter, letter) for letter in DDC_LETTER], type=_DDCRuneMethods)
