"""
state_projector.py
==================

Deterministic text-to-state-vector projector for Swarm Quantum State Density Analysis.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

from .density_report import SBE_DIMENSION


class TextStateProjector:
    """
    Deterministic text -> normalized complex state-vector embedding in C^d.

    This is an engineered mathematical feature projection. It does not assert that
    text possesses an intrinsic physical quantum state.
    """

    def __init__(self, dim: int = SBE_DIMENSION):
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim

    def project(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            return np.ones(self.dim, dtype=complex) / math.sqrt(self.dim)

        vec = np.zeros(self.dim, dtype=float)
        for i, byte in enumerate(text.encode("utf-8")):
            vec[(byte + i * 31) % self.dim] += 1.0

        for i, word in enumerate(text.split()):
            digest = int(hashlib.sha256(word.encode("utf-8")).hexdigest()[:8], 16)
            vec[(digest + i * 17) % self.dim] += 2.0

        max_v = np.max(vec)
        exps = np.exp(vec - max_v)
        amplitudes = np.sqrt(exps / np.sum(exps))

        psi = np.zeros(self.dim, dtype=complex)
        for k in range(self.dim):
            phase = (2.0 * math.pi * k * len(text)) / (self.dim * 100.0)
            psi[k] = amplitudes[k] * complex(math.cos(phase), math.sin(phase))

        norm = np.linalg.norm(psi)
        if norm > 1e-12:
            return psi / norm
        return np.ones(self.dim, dtype=complex) / math.sqrt(self.dim)
