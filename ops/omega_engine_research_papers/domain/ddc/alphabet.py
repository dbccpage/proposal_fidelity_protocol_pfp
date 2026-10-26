"""Discrete Deformation Calculus (DDC) 8-Letter Operational Alphabet.

A typed algebra of what a computation did to an obstruction:
records how an obstruction was handled, not whether the world is true.
"""

from __future__ import annotations

from enum import Enum


class DDCRune(str, Enum):
    """The 8 operational runes of the DDC alphabet A_DDC."""

    C = "C"  # Context Exposure: Declares or splits carrier, window, and boundary complex
    R = "R"  # Residual Projection: Projects unresolved boundary tension into quotient tracking (Phi_1 > 0)
    E = "E"  # Exact Repair: Eliminates local boundary tension under declared rules
    I = "I"  # noqa: E741  # Integration: Appends verified transition to Merkle tape with deterministic step receipt
    LIFT = "Λ"  # Structural Lift: Extends carrier capacity under Licensed Context Extension (LCE)
    D = "D"  # Descent: Scale descent lowering from rich to coarse carriers with loss ledger
    M = "M"  # Typed Refusal: Mutation block halting untyped, unwitnessed, or out-of-budget moves
    T = "T"  # Terminalization: Closes execution trace under a routing terminal

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
