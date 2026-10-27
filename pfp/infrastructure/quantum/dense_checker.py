"""Independent numerical dense matrix verification checker for quantum stabilizer solver.

Constructs the dense 2^n x 2^n Hamiltonian matrix directly from Pauli Kronecker products,
diagonalizes via standard Hermitian eigensolver, and verifies that the solver's
ground state energy and ground eigenspace dimension match the physical spectrum.

AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

import numpy as np

from pfp.domain.quantum.hamiltonian import parse_challenge


# Standard Pauli matrices
_SIGMA = {
    "I": np.array([[1.0, 0.0], [0.0, 1.0]], dtype=complex),
    "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=complex),
    "Y": np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex),
    "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=complex),
}


def pauli_to_matrix(word: str) -> np.ndarray:
    """Builds the 2^n x 2^n dense matrix for an n-qubit Pauli string."""
    word = word.strip().upper()
    mat = _SIGMA[word[0]]
    for char in word[1:]:
        mat = np.kron(mat, _SIGMA[char])
    return mat


def build_dense_hamiltonian(case: Mapping[str, Any]) -> tuple[np.ndarray, int]:
    """Constructs the dense matrix H = sum_i w_i * (I - s_i * P_i) / 2.

    Weights come from the exact challenge parser. The float matrix is only the
    numerical cross-check of that rational.
    """
    parsed = parse_challenge(case)
    num_qubits = parsed.num_qubits
    dim = 1 << num_qubits
    if not parsed.hamiltonian.terms:
        return np.zeros((dim, dim), dtype=complex), num_qubits

    h_mat = np.zeros((dim, dim), dtype=complex)
    eye = np.eye(dim, dtype=complex)
    for term in parsed.hamiltonian.terms:
        proj = 0.5 * (eye - term.target_sign * pauli_to_matrix(term.pauli.word))
        h_mat += float(term.weight) * proj
    return h_mat, num_qubits


def verify_dense_spectrum(case: Mapping[str, Any], solver_result: Mapping[str, Any]) -> dict[str, Any]:
    """Verifies that the solver's ground state energy and eigenspace dimension

    agree with the exact numerical diagonalization of the physical Hamiltonian.
    Restricted to num_qubits <= 6 for dense tractability.
    """
    if solver_result.get("status") != "SOLVED":
        return {
            "evidence_class": "SECONDARY_NUMERIC",
            "dense_check": "SKIPPED",
            "reason": "Case was not solved (e.g. out of scope)",
        }

    h_mat, num_qubits = build_dense_hamiltonian(case)
    if num_qubits > 6:
        return {
            "evidence_class": "SECONDARY_NUMERIC",
            "dense_check": "SKIPPED",
            "reason": f"num_qubits {num_qubits} > 6 exceeds dense limit",
        }

    eigenvalues = np.sort(np.linalg.eigvalsh(h_mat))
    min_eig = float(eigenvalues[0])

    # Extract solver energy safely across all representations
    if "energy" in solver_result and isinstance(solver_result["energy"], (list, tuple)):
        solver_energy_frac = Fraction(int(solver_result["energy"][0]), int(solver_result["energy"][1]))
    elif "ground_state_energy_rational" in solver_result and isinstance(solver_result["ground_state_energy_rational"], dict):
        rat = solver_result["ground_state_energy_rational"]
        solver_energy_frac = Fraction(int(rat["numerator"]), int(rat["denominator"]))
    elif "ground_state_energy" in solver_result:
        solver_energy_frac = Fraction(str(solver_result["ground_state_energy"]))
    elif "E" in solver_result:
        if isinstance(solver_result["E"], (list, tuple)):
            solver_energy_frac = Fraction(int(solver_result["E"][0]), int(solver_result["E"][1]))
        else:
            solver_energy_frac = Fraction(str(solver_result["E"]))
    else:
        return {
            "evidence_class": "SECONDARY_NUMERIC",
            "dense_check": "FAILED",
            "reason": "No ground state energy found in solver result",
        }

    solver_energy = float(solver_energy_frac)
    solver_dim = int(solver_result.get("degeneracy", solver_result.get("ground_eigenspace_dimension", solver_result.get("deg", 1))))

    # eigvalsh is backward stable, so its round-off is O(eps * ||H||). The noise floor is
    # relative to the spectral norm (not floored at 1), which keeps a genuinely tiny
    # Hamiltonian's gap distinguishable from round-off.
    spectral_norm = float(np.max(np.abs(eigenvalues)))
    deltas = eigenvalues - min_eig

    noise_floor = 1e-12 * spectral_norm
    excited_deltas = deltas[deltas > noise_floor]

    if len(excited_deltas) > 0:
        gap = float(excited_deltas[0])
        if gap < 1e-6:
            return {
                "evidence_class": "SECONDARY_NUMERIC",
                "dense_check": "INCONCLUSIVE",
                "reason": f"Spectral gap {gap:.2e} < 1e-6 is unresolved within floating-point tolerance",
                "dense_min_eigenvalue": round(min_eig, 7),
                "solver_energy": round(solver_energy, 7),
                "spectral_gap": gap,
                "solver_dimension": solver_dim,
            }

    # Every eigenvalue is now either round-off-degenerate with the minimum or >= 1e-6 above
    # it, so a multiplicity mismatch is a real disagreement, never an unresolved gap.
    multiplicity = int(np.sum(deltas <= noise_floor))

    energy_match = bool(np.isclose(min_eig, solver_energy, atol=1e-6, rtol=1e-8))
    dim_match = bool(multiplicity == solver_dim)

    return {
        "evidence_class": "SECONDARY_NUMERIC",
        "dense_check": "PASSED" if (energy_match and dim_match) else "FAILED",
        "dense_min_eigenvalue": round(min_eig, 7),
        "solver_energy": round(solver_energy, 7),
        "dense_multiplicity": multiplicity,
        "solver_dimension": solver_dim,
        "energy_match": energy_match,
        "dimension_match": dim_match,
    }
