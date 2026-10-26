"""Numerical density diagnostics for deterministic text feature vectors.

The text embedding below uses character counts and indexed complex phases. It
is an engineered feature map, not the Rust `phi_binning` map or a physical
quantum state. Density observables are approximate floating-point diagnostics.
AuthorityEffect: None.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional, Sequence

import numpy as np

# Default dimension for the local character feature map (a-z, space, other).
SBE_DIMENSION: int = 28


@dataclass(frozen=True)
class SBEDensityReport:
    """Quantum density matrix observables across a reasoning ensemble.

    Values describe the engineered text embedding and have no physical authority.
    AuthorityEffect is strictly None.
    """

    purity: float = 1.0
    entropy_bits: float = 0.0
    l1_coherence: float = 0.0
    nonzero_eigenvalues: int = 1
    top_eigenvalue: float = 1.0
    spectral_gap: float = 1.0
    dim: int = SBE_DIMENSION
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        observables = (
            self.purity, self.entropy_bits, self.l1_coherence,
            self.top_eigenvalue, self.spectral_gap,
        )
        if not all(math.isfinite(value) for value in observables):
            raise ValueError("density observables must be finite")
        if type(self.dim) is not int or self.dim <= 0:
            raise ValueError("density dimension must be a positive integer")
        if type(self.nonzero_eigenvalues) is not int or not (0 <= self.nonzero_eigenvalues <= self.dim):
            raise ValueError("nonzero eigenvalue count is out of range")
        if self.authority_effect != "None":
            raise ValueError("density diagnostics cannot mint authority")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SBEDensityReport)
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


class TextStateProjector:
    """Projects raw text deterministically into a normalized state vector in C^d.

    Uses character frequencies and fixed indexed phases; this is a local
    feature map and does not implement Rust `phi_binning`.
    """

    def __init__(self, dim: int = SBE_DIMENSION) -> None:
        if type(dim) is not int or dim <= 0:
            raise ValueError("dim must be a positive integer")
        self.dim = dim

    def project(self, text: str) -> np.ndarray:
        """Map text to a complex unit state vector psi with ||psi||_2 = 1."""
        if not text:
            psi = np.zeros(self.dim, dtype=np.complex128)
            psi[0] = 1.0 + 0.0j
            return psi

        # Character unigram frequency count over canonical alphabet (a-z, space, other)
        counts = np.zeros(self.dim, dtype=np.float64)
        for i in range(len(text)):
            c = text[i].lower()
            idx = (ord(c) - ord("a")) if "a" <= c <= "z" else (26 if c == " " else 27)
            counts[idx % self.dim] += 1.0

        total = np.sum(counts)
        if total <= 0:
            probs = np.ones(self.dim, dtype=np.float64) / self.dim
        else:
            probs = counts / total

        # Phase encoding: theta_k = 2 * pi * (k / dim)
        phases = 2.0 * np.pi * np.arange(self.dim) / float(self.dim)
        psi = np.sqrt(probs) * np.exp(1j * phases)
        norm = np.linalg.norm(psi)
        if norm > 0:
            psi = psi / norm
        else:
            psi[0] = 1.0 + 0.0j

        return psi

    def project_text(self, text: str) -> np.ndarray:
        return self.project(text)


class SBEAnalyzer:
    """Analyze deterministic text embeddings with density-matrix observables.

    Computes numerical observables for pure and mixed engineered text states.
    """

    def __init__(
        self,
        dim: int = SBE_DIMENSION,
        projector: Optional[TextStateProjector] = None,
    ) -> None:
        if type(dim) is not int or dim <= 0:
            raise ValueError("dim must be a positive integer")
        self.dim = dim
        self.projector = projector if projector is not None else TextStateProjector(dim)
        if self.projector.dim != dim:
            raise ValueError("projector dimension must match analyzer dimension")

    def text_to_state_vector(self, text: str) -> np.ndarray:
        return self.projector.project(text)

    def analyze_text(self, text: str) -> SBEDensityReport:
        """Compute density observables for a single text input (pure state rho = |psi><psi|)."""
        psi = self.text_to_state_vector(text)
        rho = np.outer(psi, np.conj(psi))
        return self._compute_report(rho)

    def analyze_dialogue_ensemble(
        self,
        dialogue_beats: Sequence[str],
        weights: Optional[Sequence[float]] = None,
    ) -> SBEDensityReport:
        """Compute density observables for an ensemble mixture rho = sum w_k |psi_k><psi_k|."""
        if weights is not None and len(weights) != len(dialogue_beats):
            raise ValueError("weights must match dialogue beats")
        if len(dialogue_beats) == 0:
            # Maximally mixed state: rho = (1/d) * I
            rho = np.eye(self.dim, dtype=np.complex128) / float(self.dim)
            return self._compute_report(rho)

        n = len(dialogue_beats)
        if weights is None:
            normalized = np.ones(n, dtype=np.float64) / float(n)
        else:
            w_arr = np.asarray(weights, dtype=np.float64)
            if w_arr.ndim != 1 or not np.all(np.isfinite(w_arr)) or np.any(w_arr < 0):
                raise ValueError("weights must be finite and nonnegative")
            w_sum = float(np.sum(w_arr))
            if not math.isfinite(w_sum) or w_sum <= 0:
                raise ValueError("weights must have a finite positive sum")
            normalized = w_arr / w_sum

        rho = np.zeros((self.dim, self.dim), dtype=np.complex128)
        for text, w in zip(dialogue_beats, normalized):
            psi = self.text_to_state_vector(text)
            rho += float(w) * np.outer(psi, np.conj(psi))

        # Remove any small floating-point trace drift.
        tr = np.trace(rho).real
        if tr > 0:
            rho = rho / tr

        return self._compute_report(rho)

    def analyze(self, *args: Any, **kwargs: Any) -> Any:
        if len(args) == 1 and isinstance(args[0], str) and not kwargs:
            return self.analyze_text(args[0])
        raise TypeError("analyze expects one text string")

    def _compute_report(self, rho: np.ndarray) -> SBEDensityReport:
        """Validate a density matrix, then compute numerical observables."""
        if rho.shape != (self.dim, self.dim) or not np.all(np.isfinite(rho)):
            raise ValueError("density matrix must be finite and match analyzer dimension")
        rho_h = 0.5 * (rho + rho.conj().T)
        if not np.allclose(rho, rho_h, atol=1e-10, rtol=0):
            raise ValueError("density matrix must be Hermitian")
        if not math.isclose(float(np.trace(rho_h).real), 1.0, abs_tol=1e-9):
            raise ValueError("density matrix must have unit trace")
        eigenvalues = np.linalg.eigvalsh(rho_h).real
        if np.min(eigenvalues) < -1e-10:
            raise ValueError("density matrix must be positive semidefinite")
        # Purity P = Tr(rho^2)
        rho_sq = rho_h @ rho_h
        purity = float(np.trace(rho_sq).real)

        # Off-diagonal elements for L1 coherence
        diag_mask = np.eye(self.dim, dtype=bool)
        off_diagonals = np.abs(rho_h[~diag_mask])
        l1_coherence = float(np.sum(off_diagonals))

        # Clamp only tiny negative eigenvalues caused by numerical roundoff.
        eigenvalues = np.sort(np.maximum(eigenvalues, 0.0))[::-1]

        # Von Neumann entropy S(rho) = -sum p_i log2(p_i) in bits
        nonzero_evs = [ev for ev in eigenvalues if ev > 1e-12]
        entropy_bits = -float(sum(ev * math.log2(ev) for ev in nonzero_evs)) if nonzero_evs else 0.0

        top = float(eigenvalues[0]) if len(eigenvalues) > 0 else 1.0
        second = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0
        spectral_gap = float(top - second)

        return SBEDensityReport(
            purity=purity,
            entropy_bits=entropy_bits,
            l1_coherence=l1_coherence,
            nonzero_eigenvalues=len(nonzero_evs),
            top_eigenvalue=top,
            spectral_gap=spectral_gap,
            dim=self.dim,
            authority_effect="None",
        )


__all__ = [
    "SBEAnalyzer",
    "SBE_DIMENSION",
    "SBEDensityReport",
    "TextStateProjector",
]
