"""Infrastructure adapters for finite quantum systems.

Provides numerical verification tools (e.g. dense matrix eigensolvers)
isolated from pure domain models.
AuthorityEffect: None.
"""

from __future__ import annotations

from .dense_checker import build_dense_hamiltonian, pauli_to_matrix, verify_dense_spectrum

__all__ = [
    "build_dense_hamiltonian",
    "pauli_to_matrix",
    "verify_dense_spectrum",
]
