"""
analyzer.py
===========

Quantum Density Matrix & Symmetry Breaking Engine (SBE) analyzer for Swarm multi-agent ensembles.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Optional, Sequence

import numpy as np

from .density_matrix import (
    DensityMatrixCandidate,
    DensityMatrixConfig,
    NumericalDensityMatrix,
)
from .density_report import SBE_DIMENSION, SBEDensityReport
from .state_projector import TextStateProjector


class SBEAnalyzer:
    """Analyze deterministic text embeddings with density-matrix observables."""

    def __init__(
        self,
        dim: int = SBE_DIMENSION,
        config: Optional[DensityMatrixConfig] = None,
        projector: Optional[TextStateProjector] = None,
    ):
        self.dim = dim
        self.config = config or DensityMatrixConfig.default()
        self.projector = projector or TextStateProjector(dim)
        if self.projector.dim != dim:
            raise ValueError("projector dimension must match analyzer dimension")

    def text_to_state_vector(self, text: str) -> np.ndarray:
        return self.projector.project(text)

    def analyze_text(self, text: str) -> SBEDensityReport:
        psi = self.text_to_state_vector(text)
        rho_arr = np.outer(psi, psi.conj())
        dm = DensityMatrixCandidate.from_rho(rho_arr).validate(self.config)
        return self._compute_report(dm)

    def analyze_dialogue_ensemble(
        self,
        dialogue_beats: Sequence[str],
        weights: Optional[Sequence[float]] = None,
    ) -> SBEDensityReport:
        if not dialogue_beats:
            return self._compute_report(NumericalDensityMatrix.try_maximally_mixed(self.dim))

        n = len(dialogue_beats)
        if weights is None or len(weights) != n:
            normalized = np.ones(n) / float(n)
        else:
            weight_sum = sum(weights)
            normalized = np.asarray(weights, dtype=float) / (weight_sum if weight_sum > 0 else 1.0)

        components = []
        for text, weight in zip(dialogue_beats, normalized):
            psi = self.text_to_state_vector(text)
            rho_arr = np.outer(psi, psi.conj())
            dm = DensityMatrixCandidate.from_rho(rho_arr).validate(self.config)
            components.append((dm, float(weight)))

        return self._compute_report(NumericalDensityMatrix.try_mixture(components, self.config))

    def _compute_report(self, dm: NumericalDensityMatrix) -> SBEDensityReport:
        rho = dm.rho()
        off_diagonals = np.abs(rho[~np.eye(self.dim, dtype=bool)])
        eigenvalues = dm.approximate_eigenvalues()
        top = float(eigenvalues[0]) if eigenvalues else 1.0
        second = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
        nonzero_evs = len([ev for ev in eigenvalues if ev > 1e-6])

        return SBEDensityReport(
            purity=float(dm.purity()),
            entropy_bits=float(dm.entropy_bits()),
            l1_coherence=float(np.sum(off_diagonals)),
            nonzero_eigenvalues=int(nonzero_evs),
            top_eigenvalue=top,
            spectral_gap=float(top - second),
            dim=self.dim,
            authority_effect="None",
        )
