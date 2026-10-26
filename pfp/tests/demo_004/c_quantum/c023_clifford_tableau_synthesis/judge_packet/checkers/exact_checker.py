"""Exact Algebraic Clifford Tableau Simulation Checker for C023.

Verifies candidate circuit through forward row-wise F2 simulation with sign tracking:
1. Validates gate formatting and qubit indices.
2. Enforces gate count <= gate_budget.
3. Propagates canonical generators X_0..X_{n-1} and Z_0..Z_{n-1} through circuit.
4. Verifies 100% agreement with target tableau images (including exact signs).
5. For OUT_OF_SCOPE certificates, validates the symplectic defect witness.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

from ...reference_solver.synthesis import solve as ref_solve
from ...reference_solver.tableau import Tableau
from .schema_guard import validate_certificate


def check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    """Verifies candidate solution against case specification."""
    schema_error = validate_certificate(case, cert)
    if schema_error:
        return {"verdict": "FAIL", "reason": schema_error}
    status = cert.get("status")
    expected = ref_solve(case)
    expected_status = expected.get("status")

    if status != expected_status:
        return {
            "verdict": "FAIL",
            "reason": f"Status mismatch: expected {expected_status}, got {status}",
        }

    # Handle OUT_OF_SCOPE
    if status == "OUT_OF_SCOPE":
        act_w = cert.get("witness", {})
        exp_w = expected.get("witness", {})
        if act_w != exp_w:
            return {"verdict": "FAIL", "reason": f"Witness mismatch: expected {exp_w}, got {act_w}"}
        return {"verdict": "PASS", "details": "Canonical structural defect witness verified"}

    # Handle UNKNOWN (e.g. GATE_BUDGET_NOT_MET)
    if status == "UNKNOWN":
        ref_code = cert.get("refusal_code")
        exp_code = expected.get("refusal_code")
        if ref_code != exp_code:
            return {
                "verdict": "FAIL",
                "reason": f"Refusal code mismatch: expected {exp_code}, got {ref_code}",
            }
        return {"verdict": "PASS", "details": "Legitimate refusal code verified"}

    if status != "SOLVED":
        return {"verdict": "FAIL", "reason": f"Unsupported certificate status: {status}"}

    # Verify circuit
    circuit = cert.get("circuit")
    if not isinstance(circuit, list):
        return {"verdict": "FAIL", "reason": "Certificate circuit is not a list"}

    n = case.get("num_qubits", 0)
    gate_budget = case.get("gate_budget")
    if gate_budget is not None and len(circuit) > gate_budget:
        return {
            "verdict": "FAIL",
            "reason": f"Circuit length {len(circuit)} exceeds gate budget {gate_budget}",
        }

    # Simulate circuit on identity tableau
    sim = Tableau(n)
    for idx, gate in enumerate(circuit):
        if not isinstance(gate, (list, tuple)) or len(gate) < 2:
            return {"verdict": "FAIL", "reason": f"Gate {idx} is malformed: {gate}"}
        name = gate[0]
        if name in ("H", "S"):
            if len(gate) != 2:
                return {
                    "verdict": "FAIL",
                    "reason": f"Gate {idx} ({name}) expects 1 qubit, got {gate}",
                }
            q = gate[1]
            if not isinstance(q, int) or q < 0 or q >= n:
                return {"verdict": "FAIL", "reason": f"Invalid qubit index {q} in gate {idx}"}
            sim.apply_gate(name, q)
        elif name == "CNOT":
            if len(gate) != 3:
                return {
                    "verdict": "FAIL",
                    "reason": f"Gate {idx} (CNOT) expects 2 qubits, got {gate}",
                }
            c, t = gate[1], gate[2]
            if (
                not isinstance(c, int)
                or not isinstance(t, int)
                or c < 0
                or c >= n
                or t < 0
                or t >= n
                or c == t
            ):
                return {
                    "verdict": "FAIL",
                    "reason": f"Invalid control/target ({c}, {t}) in gate {idx}",
                }
            sim.apply_gate("CNOT", c, t)
        else:
            return {"verdict": "FAIL", "reason": f"Unknown gate type {name!r} in gate {idx}"}

    # Check simulated tableau against target images
    target_images = case.get("images", {})
    for j in range(n):
        x_key = f"X{j}"
        z_key = f"Z{j}"
        sim_x = sim.row_to_pauli_str(j)
        sim_z = sim.row_to_pauli_str(n + j)
        tgt_x = target_images.get(x_key)
        tgt_z = target_images.get(z_key)

        if sim_x != tgt_x:
            return {
                "verdict": "FAIL",
                "reason": f"Tableau image mismatch on {x_key}: simulated {sim_x}, expected {tgt_x}",
            }
        if sim_z != tgt_z:
            return {
                "verdict": "FAIL",
                "reason": f"Tableau image mismatch on {z_key}: simulated {sim_z}, expected {tgt_z}",
            }

    return {"verdict": "PASS", "details": f"Circuit verified with {len(circuit)} gates"}
