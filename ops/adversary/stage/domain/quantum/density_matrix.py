"""
density_matrix.py
=================

Canonical Numerical Density Matrix and Quantum State Tomography operators
conforming to core_linear_algebra/src/linear_algebra/density.rs.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


@dataclass(frozen=True)
class DensityMatrixConfig:
    trace_tol: float = 1e-8
    hermitian_tol: float = 1e-8
    psd_tol: float = 1e-8
    unitary_tol: float = 1e-8
    weight_sum_tol: float = 1e-8
    zero_norm_tol: float = 1e-12
    channel_tol: float = 1e-8

    @classmethod
    def default(cls) -> DensityMatrixConfig:
        return cls()


class NumericalDensityMatrix:
    """Numerical density matrix representation for SBE and quantum observables."""

    def __init__(self, rho: np.ndarray):
        self._rho = np.asarray(rho, dtype=complex)
        self._dim = self._rho.shape[0]

    def rho(self) -> np.ndarray:
        return self._rho

    def dim(self) -> int:
        return self._dim

    def approximate_eigenvalues(self) -> list[float]:
        evals = np.linalg.eigvalsh(self._rho)
        return [float(x) for x in sorted(evals, reverse=True)]

    def purity(self) -> float:
        prod = self._rho @ self._rho
        return float(np.real(np.trace(prod)))

    def von_neumann_entropy(self) -> float:
        return self.entropy_bits()

    def entropy_bits(self) -> float:
        evals = self.approximate_eigenvalues()
        ent = 0.0
        for ev in evals:
            if ev > 1e-12:
                ent -= ev * math.log2(ev)
        return float(ent)

    def l1_coherence(self) -> float:
        off_diagonals = np.abs(self._rho[~np.eye(self._dim, dtype=bool)])
        return float(np.sum(off_diagonals))

    @classmethod
    def try_maximally_mixed(cls, dim: int) -> NumericalDensityMatrix:
        rho = np.eye(dim, dtype=complex) / float(dim)
        return cls(rho)

    @classmethod
    def from_diagonal_probs(
        cls, probs: Sequence[float], config: Any = None
    ) -> NumericalDensityMatrix:
        dim = len(probs)
        rho = np.diag(probs).astype(complex)
        return cls(rho)

    @classmethod
    def try_mixture(
        cls,
        components: Sequence[tuple[NumericalDensityMatrix, float]],
        config: Any = None,
    ) -> NumericalDensityMatrix:
        if not components:
            raise ValueError("no components provided for mixture")
        dim = components[0][0].dim()
        rho_sum = np.zeros((dim, dim), dtype=complex)
        weight_sum = 0.0
        for dm, w in components:
            rho_sum += float(w) * dm.rho()
            weight_sum += float(w)
        if weight_sum > 0:
            rho_sum /= weight_sum
        return cls(rho_sum)


class DensityMatrixCandidate:
    """Pre-validation density matrix candidate."""

    def __init__(self, rho: np.ndarray):
        self._rho = np.asarray(rho, dtype=complex)

    @classmethod
    def from_rho(cls, rho: np.ndarray) -> DensityMatrixCandidate:
        return cls(rho)

    def validate(self, config: Any = None) -> NumericalDensityMatrix:
        rho_herm = (self._rho + self._rho.conj().T) / 2.0
        tr = np.trace(rho_herm)
        if abs(tr) > 1e-12:
            rho_norm = rho_herm / tr
        else:
            dim = rho_herm.shape[0]
            rho_norm = np.eye(dim, dtype=complex) / float(dim)
        return NumericalDensityMatrix(rho_norm)


class DensityMatrixConstructionError(ValueError):
    """State ensemble could not be turned into a density matrix."""


class QuantumDensityEngine:
    """Density construction engine matching core_linear_algebra/src/linear_algebra/density.rs."""

    @staticmethod
    def from_states(states: list[list[float]]) -> NumericalDensityMatrix | None:
        if not states:
            return None
        try:
            dim = len(states[0])
            rho_acc = np.zeros((dim, dim), dtype=complex)
            valid = 0
            for s in states:
                v = np.asarray(s, dtype=complex)
                norm = np.linalg.norm(v)
                if norm > 1e-9:
                    v = v / norm
                    rho_acc += np.outer(v, v.conj())
                    valid += 1
            if valid > 0:
                rho_acc /= float(valid)
                return NumericalDensityMatrix(rho_acc)
            return NumericalDensityMatrix.try_maximally_mixed(dim)
        except (TypeError, ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
            raise DensityMatrixConstructionError(
                f"density matrix construction failed: {type(exc).__name__}"
            ) from exc


__all__ = [
    "DensityMatrixConfig",
    "DensityMatrixConstructionError",
    "NumericalDensityMatrix",
    "DensityMatrixCandidate",
    "QuantumDensityEngine",
]
