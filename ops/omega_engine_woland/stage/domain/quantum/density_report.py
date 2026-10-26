"""
density_report.py
=================

Domain Value Object representing Quantum Density Matrix observables and SBE metrics.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict

SBE_DIMENSION: int = 28


@dataclass(frozen=True)
class SBEDensityReport:
    """Quantum density matrix observables across a multi-agent swarm ensemble."""

    purity: float
    entropy_bits: float
    l1_coherence: float
    nonzero_eigenvalues: int
    top_eigenvalue: float
    spectral_gap: float
    dim: int = SBE_DIMENSION
    authority_effect: str = "None"

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.purity == other.purity
            and self.entropy_bits == other.entropy_bits
            and self.l1_coherence == other.l1_coherence
            and self.nonzero_eigenvalues == other.nonzero_eigenvalues
            and self.top_eigenvalue == other.top_eigenvalue
            and self.spectral_gap == other.spectral_gap
            and self.dim == other.dim
            and self.authority_effect == other.authority_effect
        )

    def __hash__(self) -> int:
        return hash(
            (
                type(self),
                self.purity,
                self.entropy_bits,
                self.l1_coherence,
                self.nonzero_eigenvalues,
                self.top_eigenvalue,
                self.spectral_gap,
                self.dim,
                self.authority_effect,
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
