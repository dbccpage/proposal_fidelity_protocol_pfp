"""Independent Second Checker for C023.

Verifies candidate circuit independently:
1. For n <= 5: Constructs dense 2^n x 2^n matrix representation in complex field
   and asserts exact matrix equality: U P U^dagger == Target_P for all 2n generators.
2. For n > 5: Uses column-wise backward propagation of images through the inverse circuit.
3. Asserts gate count <= gate_budget.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ...reference_solver.tableau import Tableau
from .exact_checker import check_certificate as exact_check
from .schema_guard import validate_certificate

# Single-qubit Pauli matrices
_I = np.array([[1, 0], [0, 1]], dtype=complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
_PAULI_MAP = {"I": _I, "X": _X, "Y": _Y, "Z": _Z}

# Elementary gate matrices
_H = np.array([[1, 1], [1, -1]], dtype=complex) / np.sqrt(2)
_S = np.array([[1, 0], [0, 1j]], dtype=complex)
_CNOT = np.array(
    [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ],
    dtype=complex,
)


def _build_n_qubit_gate(n: int, name: str, *qubits: int) -> np.ndarray:
    """Builds 2^n x 2^n matrix for elementary gate."""
    if name == "H":
        q = qubits[0]
        curr = np.array([[1]], dtype=complex)
        for i in range(n):
            curr = np.kron(curr, _H if i == q else _I)
        return curr
    elif name == "S":
        q = qubits[0]
        curr = np.array([[1]], dtype=complex)
        for i in range(n):
            curr = np.kron(curr, _S if i == q else _I)
        return curr
    elif name == "CNOT":
        c, t = qubits[0], qubits[1]
        # |0><0|_c (x) I_t + |1><1|_c (x) X_t
        P0 = np.array([[1, 0], [0, 0]], dtype=complex)
        P1 = np.array([[0, 0], [0, 1]], dtype=complex)

        term0 = np.array([[1]], dtype=complex)
        for i in range(n):
            term0 = np.kron(term0, P0 if i == c else _I)

        term1 = np.array([[1]], dtype=complex)
        for i in range(n):
            if i == c:
                term1 = np.kron(term1, P1)
            elif i == t:
                term1 = np.kron(term1, _X)
            else:
                term1 = np.kron(term1, _I)
        return term0 + term1
    else:
        raise ValueError(f"Unknown gate: {name}")


def _build_n_qubit_pauli(pauli_str: str) -> np.ndarray:
    """Builds signed 2^n x 2^n matrix from Pauli string, e.g. '+XYZ'."""
    s = pauli_str.strip()
    sign = -1.0 if s.startswith("-") else 1.0
    word = s[1:] if s.startswith(("+", "-")) else s
    mat = np.array([[sign]], dtype=complex)
    for c in word:
        mat = np.kron(mat, _PAULI_MAP[c])
    return mat


def independent_check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    """Independent verification using dense spectral algebra for n <= 5 or backward propagation."""
    schema_error = validate_certificate(case, cert)
    if schema_error:
        return {"verdict": "FAIL", "reason": schema_error}
    status = cert.get("status")
    if status in ("OUT_OF_SCOPE", "UNKNOWN"):
        return exact_check(case, cert)

    if status != "SOLVED":
        return {"verdict": "FAIL", "reason": f"Unexpected status: {status}"}

    circuit = cert.get("circuit", [])
    if not isinstance(circuit, list):
        return {"verdict": "FAIL", "reason": "Circuit is not a list"}

    n = case.get("num_qubits", 0)
    gate_budget = case.get("gate_budget")
    if gate_budget is not None and len(circuit) > gate_budget:
        return {
            "verdict": "FAIL",
            "reason": f"Circuit length {len(circuit)} exceeds budget {gate_budget}",
        }

    target_images = case.get("images", {})

    # Dense matrix path for n <= 5
    if n <= 5:
        dim = 1 << n
        U = np.eye(dim, dtype=complex)
        # Apply gates left-to-right: U = G_k ... G_1
        for gate in circuit:
            if not isinstance(gate, (list, tuple)) or len(gate) < 2:
                return {"verdict": "FAIL", "reason": f"Malformed gate: {gate}"}
            name = gate[0]
            if name not in ("H", "S", "CNOT"):
                return {"verdict": "FAIL", "reason": f"Unknown gate name: {name}"}
            qubits = gate[1:]
            if name in ("H", "S"):
                if (
                    len(qubits) != 1
                    or not isinstance(qubits[0], int)
                    or qubits[0] < 0
                    or qubits[0] >= n
                ):
                    return {
                        "verdict": "FAIL",
                        "reason": f"Invalid qubit index for {name}: {qubits}",
                    }
            elif name == "CNOT":
                if (
                    len(qubits) != 2
                    or not isinstance(qubits[0], int)
                    or not isinstance(qubits[1], int)
                    or qubits[0] < 0
                    or qubits[0] >= n
                    or qubits[1] < 0
                    or qubits[1] >= n
                    or qubits[0] == qubits[1]
                ):
                    return {"verdict": "FAIL", "reason": f"Invalid qubits for CNOT: {qubits}"}
            try:
                G = _build_n_qubit_gate(n, name, *qubits)
            except Exception as e:
                return {"verdict": "FAIL", "reason": f"Failed to construct gate {name}: {e}"}
            U = G @ U

        U_dag = U.conj().T

        for j in range(n):
            # Check X_j
            x_in = "+" + "".join("X" if i == j else "I" for i in range(n))
            X_mat = _build_n_qubit_pauli(x_in)
            target_X_str = target_images.get(f"X{j}", "")
            target_X_mat = _build_n_qubit_pauli(target_X_str)

            conj_X = U @ X_mat @ U_dag
            if not np.allclose(conj_X, target_X_mat, atol=1e-6):
                return {
                    "verdict": "FAIL",
                    "reason": f"Dense unitary conjugation failed for X{j}: mismatch with {target_X_str}",
                }

            # Check Z_j
            z_in = "+" + "".join("Z" if i == j else "I" for i in range(n))
            Z_mat = _build_n_qubit_pauli(z_in)
            target_Z_str = target_images.get(f"Z{j}", "")
            target_Z_mat = _build_n_qubit_pauli(target_Z_str)

            conj_Z = U @ Z_mat @ U_dag
            if not np.allclose(conj_Z, target_Z_mat, atol=1e-6):
                return {
                    "verdict": "FAIL",
                    "reason": f"Dense unitary conjugation failed for Z{j}: mismatch with {target_Z_str}",
                }

        return {"verdict": "PASS", "details": f"Dense unitary verified across all 2^{n} dimensions"}

    # Backward propagation path for n > 5
    # Apply inverse gates in reverse order to target images; must result in identity tableau
    tab = Tableau.from_images_dict(n, target_images)
    for gate in reversed(circuit):
        if not isinstance(gate, (list, tuple)) or len(gate) < 2:
            return {"verdict": "FAIL", "reason": f"Malformed gate: {gate}"}
        name = gate[0]
        if name not in ("H", "S", "CNOT"):
            return {"verdict": "FAIL", "reason": f"Unknown gate name: {name}"}
        qubits = gate[1:]
        if name == "H":
            if (
                len(qubits) != 1
                or not isinstance(qubits[0], int)
                or qubits[0] < 0
                or qubits[0] >= n
            ):
                return {"verdict": "FAIL", "reason": f"Invalid qubit for H: {qubits}"}
            tab.apply_H(qubits[0])
        elif name == "CNOT":
            if (
                len(qubits) != 2
                or not isinstance(qubits[0], int)
                or not isinstance(qubits[1], int)
                or qubits[0] < 0
                or qubits[0] >= n
                or qubits[1] < 0
                or qubits[1] >= n
                or qubits[0] == qubits[1]
            ):
                return {"verdict": "FAIL", "reason": f"Invalid qubits for CNOT: {qubits}"}
            tab.apply_CNOT(qubits[0], qubits[1])
        elif name == "S":
            if (
                len(qubits) != 1
                or not isinstance(qubits[0], int)
                or qubits[0] < 0
                or qubits[0] >= n
            ):
                return {"verdict": "FAIL", "reason": f"Invalid qubit for S: {qubits}"}
            tab.apply_S(qubits[0])
            tab.apply_S(qubits[0])
            tab.apply_S(qubits[0])

    # Check that tab is identity tableau
    for j in range(n):
        for q in range(n):
            exp_x = 1 if q == j else 0
            exp_z = 0
            if tab.x[j][q] != exp_x or tab.z[j][q] != exp_z:
                return {
                    "verdict": "FAIL",
                    "reason": f"Backward propagation failed: row X{j} not identity",
                }

        for q in range(n):
            exp_x = 0
            exp_z = 1 if q == j else 0
            if tab.x[n + j][q] != exp_x or tab.z[n + j][q] != exp_z:
                return {
                    "verdict": "FAIL",
                    "reason": f"Backward propagation failed: row Z{j} not identity",
                }

        if tab.r[j] != 0 or tab.r[n + j] != 0:
            return {
                "verdict": "FAIL",
                "reason": f"Backward propagation failed: sign on generator {j} not +1",
            }

    return {
        "verdict": "PASS",
        "details": "Backward propagation verified all generators to identity",
    }
