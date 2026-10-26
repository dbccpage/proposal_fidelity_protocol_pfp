"""Canonical Clifford Circuit Synthesis from Tableaux (Aaronson-Gottesman 2004).

Produces exact H, S, and CNOT circuits implementing target Clifford tableaux
within gate budget, with machine-verifiable operational traces and refusal witnesses.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any

try:
    from .ddc_tracer import DDCTracer
    from .tableau import Tableau
except (ImportError, ValueError):
    try:
        from reference_solver.ddc_tracer import DDCTracer
        from reference_solver.tableau import Tableau
    except (ImportError, ValueError):
        from tableau import Tableau


def simplify_circuit(gates: list[list[Any]]) -> list[list[Any]]:
    """Peephole optimization canceling adjacent inverse and identity gates."""
    changed = True
    while changed:
        changed = False
        new_gates: list[list[Any]] = []
        i = 0
        n_gates = len(gates)
        while i < n_gates:
            g1 = gates[i]
            # Check 4 consecutive S on same qubit: S^4 = I
            if (
                i + 3 < n_gates
                and g1[0] == "S"
                and gates[i + 1][0] == "S"
                and gates[i + 2][0] == "S"
                and gates[i + 3][0] == "S"
                and g1[1] == gates[i + 1][1] == gates[i + 2][1] == gates[i + 3][1]
            ):
                i += 4
                changed = True
                continue

            # Check 2 consecutive H on same qubit: H^2 = I
            if (
                i + 1 < n_gates
                and g1[0] == "H"
                and gates[i + 1][0] == "H"
                and g1[1] == gates[i + 1][1]
            ):
                i += 2
                changed = True
                continue

            # Check 2 consecutive CNOT on same (c, t): CNOT^2 = I
            if (
                i + 1 < n_gates
                and g1[0] == "CNOT"
                and gates[i + 1][0] == "CNOT"
                and g1[1] == gates[i + 1][1]
                and g1[2] == gates[i + 1][2]
            ):
                i += 2
                changed = True
                continue

            new_gates.append(g1)
            i += 1
        gates = new_gates
    return gates


def synthesize_clifford_circuit(tab: Tableau) -> list[list[Any]]:
    """Synthesizes exact Clifford circuit from target tableau.

    Returns list of gates, each formatted as ["H", q], ["S", q], or ["CNOT", c, t].
    """
    n = tab.n
    t = tab.copy()
    red_gates: list[list[Any]] = []

    def add_red(name: str, *qubits: int) -> None:
        t.apply_gate(name, *qubits)
        red_gates.append([name, *qubits])

    for j in range(n):
        # Step 1: ensure x[j][j] == 1
        k_found = None
        for k in range(j, n):
            if t.x[j][k] == 1:
                k_found = k
                break
        if k_found is None:
            for k in range(j, n):
                if t.z[j][k] == 1:
                    add_red("H", k)
                    k_found = k
                    break
        assert k_found is not None, f"Symplectic defect at j={j}"
        if k_found != j:
            add_red("CNOT", j, k_found)
            add_red("CNOT", k_found, j)
            add_red("CNOT", j, k_found)

        # Step 2: Clear x[j][k] for k > j
        for k in range(j + 1, n):
            if t.x[j][k] == 1:
                add_red("CNOT", j, k)

        # Step 3: Clear z[j][j]
        if t.z[j][j] == 1:
            add_red("S", j)

        # Step 4: Clear z[j][k] for k > j
        for k in range(j + 1, n):
            if t.z[j][k] == 1:
                add_red("H", k)
                add_red("CNOT", j, k)
                add_red("H", k)

        # Step 5: Clear z[n+j][k] for k > j
        for k in range(j + 1, n):
            if t.z[n + j][k] == 1:
                add_red("CNOT", k, j)

        # Step 6: Clear x[n+j][k] for k > j
        for k in range(j + 1, n):
            if t.x[n + j][k] == 1:
                add_red("H", k)
                add_red("CNOT", k, j)
                add_red("H", k)

        # Step 7: Clear x[n+j][j] if 1 using H S H
        if t.x[n + j][j] == 1:
            add_red("H", j)
            add_red("S", j)
            add_red("H", j)

    # Step 8: Fix signs!
    # X_k sign fix: conjugate by Z_k = S_k^2
    for k in range(n):
        if t.r[k] == 1:
            add_red("S", k)
            add_red("S", k)

    # Z_k sign fix: conjugate by X_k = H_k S_k^2 H_k
    for k in range(n):
        if t.r[n + k] == 1:
            add_red("H", k)
            add_red("S", k)
            add_red("S", k)
            add_red("H", k)

    # Invert and reverse red_gates to get synthesis circuit
    synth_gates: list[list[Any]] = []
    for g in reversed(red_gates):
        name = g[0]
        qubits = g[1:]
        if name == "H":
            synth_gates.append(["H", *qubits])
        elif name == "CNOT":
            synth_gates.append(["CNOT", *qubits])
        elif name == "S":
            # S^dagger = S S S
            synth_gates.append(["S", *qubits])
            synth_gates.append(["S", *qubits])
            synth_gates.append(["S", *qubits])

    # Simplify
    synth_gates = simplify_circuit(synth_gates)
    return synth_gates


def solve(case: dict[str, Any]) -> dict[str, Any]:
    """C023 Solver entry point.

    Exposes def solve(case: dict) -> dict per SG-CP v1.
    """
    case_id = str(case.get("id") or case.get("case_id", "unknown"))
    n = case.get("num_qubits", 0)

    # Check bounds: 1 <= n <= 12
    if type(n) is not int:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "invalid_num_qubits_type", "actual_type": type(n).__name__},
        }
    if n < 1 or n > 12:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "qubit_count_out_of_bounds", "num_qubits": n},
        }

    gate_budget = case.get("gate_budget")
    if type(gate_budget) is not int or gate_budget < 0:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "invalid_gate_budget", "actual_type": type(gate_budget).__name__},
        }

    images = case.get("images", {})
    if not isinstance(images, dict):
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "invalid_images_type", "actual_type": type(images).__name__},
        }
    if not images:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "empty_images"},
        }

    # Parse tableau
    try:
        tab = Tableau.from_images_dict(n, images)
    except Exception as e:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"kind": "malformed_images", "error": str(e)},
        }

    # Verify symplecticity
    is_symplectic, witness = tab.check_symplecticity()
    if not is_symplectic:
        return {
            "id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": witness,
        }

    # Synthesize circuit
    circuit = synthesize_clifford_circuit(tab)
    gate_count = len(circuit)

    # Verify against gate budget if specified
    if gate_count > gate_budget:
        return {
            "id": case_id,
            "status": "UNKNOWN",
            "refusal_code": "GATE_BUDGET_NOT_MET",
            "best_gate_count": gate_count,
        }

    return {
        "id": case_id,
        "status": "SOLVED",
        "circuit": circuit,
    }
