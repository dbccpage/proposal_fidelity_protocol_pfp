"""Polarity classification for the Polarized Operadic Triad.

AuthorityEffect: None.
"""

from __future__ import annotations

import enum


@enum.unique
class Polarity(str, enum.Enum):
    r"""Polarity of an operadic morphism family.

    Decomposition: O = O^+ (constructive) \sqcup O^- (interrogative) \sqcup O_repair (corrective).
    A_gate represents the host-side deterministic reality gate.
    """

    CONSTRUCTIVE = "CONSTRUCTIVE"
    INTERROGATIVE = "INTERROGATIVE"
    CORRECTIVE = "CORRECTIVE"
    GATE = "GATE"

    @property
    def is_constructive(self) -> bool:
        return self is Polarity.CONSTRUCTIVE

    @property
    def is_interrogative(self) -> bool:
        return self is Polarity.INTERROGATIVE

    @property
    def is_corrective(self) -> bool:
        return self is Polarity.CORRECTIVE

    @property
    def is_gate(self) -> bool:
        return self is Polarity.GATE


__all__ = ["Polarity"]
