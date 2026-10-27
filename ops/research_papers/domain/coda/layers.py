"""CODA Nine-Layer Stack Definitions and Canonical Nomenclature.

Enforces RULE_GENESIS_CODA_STACK_001 and RULE_CODA_NOMENCLATURE_CANONICAL_001.
Layer 5 is strictly designated as **Q: The Continuum** (never 'Quantum Enclosure').
"""

from __future__ import annotations

from enum import IntEnum, unique


@unique
class CODALayer(IntEnum):
    """The Nine-Layer CODA Stack."""

    FOC = 1   # Layer 1: Finite Obstruction Calculus
    MUR = 2   # Layer 2: Meta & Universal Re-Presentation
    CS = 3    # Layer 3: Continuum Shadow
    CS_Q = 4  # Layer 4: Continuum Shadow to Continuum Bridge
    Q = 5     # Layer 5: The Continuum (Completion & Convex Interval Enclosure)
    A = 6     # Layer 6: Sentinel Register (Stable Residual Custody)
    OR = 7    # Layer 7: Omniversal Re-Presentation (Span Overlap Gluing b=b')
    FDA = 8   # Layer 8: Finite Descent Authority (Seven Halt Guards)
    GTLA = 9  # Layer 9: General Theory of Layered Authority (Master Factorization)

    @property
    def canonical_name(self) -> str:
        names = {
            CODALayer.FOC: "Finite Obstruction Calculus",
            CODALayer.MUR: "Meta & Universal Re-Presentation",
            CODALayer.CS: "Continuum Shadow",
            CODALayer.CS_Q: "Continuum Shadow to Continuum Bridge",
            CODALayer.Q: "The Continuum",
            CODALayer.A: "Sentinel Register",
            CODALayer.OR: "Omniversal Re-Presentation",
            CODALayer.FDA: "Finite Descent Authority",
            CODALayer.GTLA: "General Theory of Layered Authority",
        }
        return names[self]

    @classmethod
    def from_str(cls, val: str) -> CODALayer:
        normalized = val.strip().upper()
        if normalized in ("QUANTUM ENCLOSURE", "QUANTUM"):
            raise ValueError(
                f"Obsolete nomenclature '{val}' is forbidden. Layer 5 is strictly 'The Continuum' (Q)."
            )
        for layer in cls:
            if layer.name == normalized or layer.canonical_name.upper() == normalized:
                return layer
        raise ValueError(f"Unknown CODA layer '{val}'")
