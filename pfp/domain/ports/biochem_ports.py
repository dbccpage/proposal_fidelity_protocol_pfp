"""Domain ports (protocols) for biochemical consensus and kinetic proofreading.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping, Protocol, Sequence, runtime_checkable

from omega_engine_pfp.domain.biochem.allostery import AllostericDecision
from omega_engine_pfp.domain.biochem.proofreading import DissociationReceipt


@runtime_checkable
class IAllostericGate(Protocol):
    """Port interface for allosteric sigmoidal consensus evaluation."""

    def compute_hill(self, theta: Fraction | int) -> Fraction:
        """Compute exact rational Hill value H(theta)."""
        ...

    def evaluate_signals(
        self, signals: Sequence[Fraction | int]
    ) -> AllostericDecision:
        """Aggregate inspector signals into sigmoidal consensus decision."""
        ...


@runtime_checkable
class IKineticProofreader(Protocol):
    """Port interface for Hopfield-Ninio kinetic proofreading state machine."""

    def proofread(
        self,
        candidate_id: str,
        content: str | Mapping[str, Any],
        initial_phi1: Fraction = Fraction(0, 1),
        deformation_factor: Fraction = Fraction(1, 1),
    ) -> DissociationReceipt:
        """Execute 3-stage kinetic proofreading over candidate move."""
        ...


__all__ = [
    "IAllostericGate",
    "IKineticProofreader",
]
