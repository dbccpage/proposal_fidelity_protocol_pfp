"""Hostile Mutation Generator for C023 Dual Checkers.

Generates 40 corrupted certificates targeting specific failure modes:
- Dropping gates (phase and basis errors).
- Inverting CNOT control/target.
- Sign-only corruptions (appending S^2 or H S^2 H).
- Exceeding declared gate budget.
- False OUT_OF_SCOPE claims on valid cases.
- Malformed gate structures and out-of-bounds qubit indices.
- Reversing circuit order.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from c023_clifford_tableau_synthesis.reference_solver.synthesis import solve


def main():
    root = Path(__file__).resolve().parent
    cases_dir = root / "judge_packet" / "cases"
    mut_dir = root / "judge_packet" / "mutation_suite" / "mutations"

    # Load base cases
    base_cases = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(cases_dir.glob("c023_base_[0-9][0-9].json"))
    ]

    rng = random.Random(999)
    mutations: list[dict[str, Any]] = []

    # 1-10: Drop one gate
    for i in range(10):
        case = base_cases[i]
        cert = solve(case)
        circuit = [list(g) for g in cert["circuit"]]
        if len(circuit) > 1:
            drop_idx = rng.randint(0, len(circuit) - 1)
            dropped_gate = circuit.pop(drop_idx)
            desc = f"Dropped gate {dropped_gate} at index {drop_idx}"
        else:
            circuit.append(["H", 0])
            desc = "Appended superfluous gate"

        corrupted = dict(cert)
        corrupted["circuit"] = circuit
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": desc,
                "case": case,
                "certificate": corrupted,
            }
        )

    # 11-18: Swap control and target on a CNOT
    for i in range(8):
        case = base_cases[10 + i]
        cert = solve(case)
        circuit = [list(g) for g in cert["circuit"]]
        # Find first CNOT
        cnot_swapped = False
        for g in circuit:
            if g[0] == "CNOT":
                g[1], g[2] = g[2], g[1]
                cnot_swapped = True
                break
        if not cnot_swapped:
            circuit.append(["CNOT", 1, 0])

        corrupted = dict(cert)
        corrupted["circuit"] = circuit
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Inverted CNOT control and target",
                "case": case,
                "certificate": corrupted,
            }
        )

    # 19-26: Sign-only error (append Pauli Z = S^2)
    for i in range(8):
        case = base_cases[18 + i]
        cert = solve(case)
        circuit = [list(g) for g in cert["circuit"]]
        q = rng.randint(0, case["num_qubits"] - 1)
        circuit.append(["S", q])
        circuit.append(["S", q])  # Z_q flips sign of X_q

        corrupted = dict(cert)
        corrupted["circuit"] = circuit
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": f"Appended Z_{q} gate (sign-only corruption on X_{q})",
                "case": case,
                "certificate": corrupted,
            }
        )

    # 27-32: Reverse gate order
    for i in range(6):
        case = base_cases[i]
        cert = solve(case)
        circuit = [list(g) for g in reversed(cert["circuit"])]
        corrupted = dict(cert)
        corrupted["circuit"] = circuit
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Reversed gate order",
                "case": case,
                "certificate": corrupted,
            }
        )

    # 33-36: Exceed gate budget by 1
    for i in range(4):
        case = dict(base_cases[i])
        cert = solve(case)
        circuit = [list(g) for g in cert["circuit"]]
        circuit.append(["H", 0])
        circuit.append(["H", 0])  # identity but +2 gates
        case["gate_budget"] = len(cert["circuit"])

        corrupted = dict(cert)
        corrupted["circuit"] = circuit
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Exceeded gate budget by 2 gates",
                "case": case,
                "certificate": corrupted,
            }
        )

    # 37-38: Falsely claim OUT_OF_SCOPE on a valid case
    for i in range(2):
        case = base_cases[i]
        corrupted = {
            "id": case["id"],
            "status": "OUT_OF_SCOPE",
            "witness": {"pair": ["X0", "X1"], "expected": "anticommute"},
        }
        mutations.append(
            {
                "id": f"mut_{len(mutations) + 1:02d}",
                "description": "Falsely claimed OUT_OF_SCOPE on valid case",
                "case": case,
                "certificate": corrupted,
            }
        )

    # 39-40: Malformed gate or out-of-bounds qubit index
    case_39 = base_cases[0]
    cert_39 = solve(case_39)
    circ_39 = [list(g) for g in cert_39["circuit"]]
    circ_39.append(["CNOT", 0, 999])  # qubit index 999 out of bounds
    mutations.append(
        {
            "id": "mut_39",
            "description": "Out-of-bounds qubit index in gate",
            "case": case_39,
            "certificate": {"id": case_39["id"], "status": "SOLVED", "circuit": circ_39},
        }
    )

    case_40 = base_cases[1]
    mutations.append(
        {
            "id": "mut_40",
            "description": "Malformed gate name",
            "case": case_40,
            "certificate": {"id": case_40["id"], "status": "SOLVED", "circuit": [["BAD_GATE", 0]]},
        }
    )

    assert len(mutations) == 40
    for m in mutations:
        with (mut_dir / f"{m['id']}.json").open("w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)

    print(f"Generated {len(mutations)} hostile checker mutations.")


if __name__ == "__main__":
    main()
