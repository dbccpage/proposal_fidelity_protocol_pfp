"""DDC execution trace, transition steps, and step receipts."""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Optional, Tuple

from .alphabet import DDCRune


@dataclass(frozen=True)
class StepReceipt:
    """Cryptographic/computational step receipt for a DDC operational move."""

    step_index: int
    rune: DDCRune
    input_digest: str
    output_digest: str
    carrier_id: str
    witness_digest: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")
        if self.step_index < 0:
            raise ValueError("step_index must be non-negative")


@dataclass(frozen=True)
class TransitionStep:
    """Single operational transition in a DDC trace."""

    index: int
    rune: DDCRune
    pre_phi1: Fraction
    pre_gamma2: Fraction
    post_phi1: Fraction
    post_gamma2: Fraction
    receipt: Optional[StepReceipt] = None
    loss_ledger: Tuple[str, ...] = field(default_factory=tuple)
    details: str = ""

    def preserves_or_decreases_defect(self) -> bool:
        """Law 7: Exact repair monotonicity."""
        return (self.post_phi1 <= self.pre_phi1) and (self.post_gamma2 <= self.pre_gamma2)


@dataclass(frozen=True)
class Commutator:
    """Candidate deformation commutator between two runes."""

    left: DDCRune
    right: DDCRune
    commutes: bool
    obstruction_witness: Optional[str] = None


@dataclass(frozen=True)
class DDCTrace:
    """Immutable tape of DDC operational transitions."""

    steps: Tuple[TransitionStep, ...] = field(default_factory=tuple)

    def rune_sequence(self) -> Tuple[DDCRune, ...]:
        return tuple(s.rune for s in self.steps)

    def as_rune_str(self) -> str:
        return " -> ".join(s.rune.value for s in self.steps)

    def is_closed(self) -> bool:
        if not self.steps:
            return False
        return self.steps[-1].rune == DDCRune.T

    def has_refusal(self) -> bool:
        return any(s.rune == DDCRune.M for s in self.steps)

    def final_phi1(self) -> Fraction:
        if not self.steps:
            return Fraction(0, 1)
        return self.steps[-1].post_phi1

    def final_gamma2(self) -> Fraction:
        if not self.steps:
            return Fraction(0, 1)
        return self.steps[-1].post_gamma2
