"""Tests for Clifford Circuit Synthesis reference solver (C023)."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.reference_solver.synthesis import (
    simplify_circuit,
    solve,
    synthesize_clifford_circuit,
)
from projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.reference_solver.tableau import (
    Tableau,
)


def test_synthesis_identity():
    tab = Tableau(2)
    circuit = synthesize_clifford_circuit(tab)
    assert len(circuit) == 0


def test_synthesis_swap():
    # Build SWAP tableau on 2 qubits
    tab = Tableau(2)
    tab.apply_CNOT(0, 1)
    tab.apply_CNOT(1, 0)
    tab.apply_CNOT(0, 1)

    circuit = synthesize_clifford_circuit(tab)
    # Circuit applied to identity should reproduce tab
    sim = Tableau(2)
    for gate in circuit:
        if gate[0] == "H":
            sim.apply_H(gate[1])
        elif gate[0] == "S":
            sim.apply_S(gate[1])
        elif gate[0] == "CNOT":
            sim.apply_CNOT(gate[1], gate[2])

    assert sim.x == tab.x
    assert sim.z == tab.z
    assert sim.r == tab.r


def test_synthesis_peephole():
    circuit = [
        ["H", 0],
        ["H", 0],
        ["CNOT", 0, 1],
        ["CNOT", 0, 1],
        ["S", 1],
        ["S", 1],
        ["S", 1],
        ["S", 1],
    ]
    optimized = simplify_circuit(circuit)
    assert len(optimized) == 0


def test_solve_entry_point():
    case = {
        "id": "test_cnot",
        "num_qubits": 2,
        "gate_budget": 10,
        "images": {
            "X0": "+XX",
            "X1": "+IX",
            "Z0": "+ZI",
            "Z1": "+ZZ",
        },
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert "circuit" in res
    assert len(res["circuit"]) <= 10


def test_solve_out_of_scope_anticommuting():
    case = {
        "id": "test_bad",
        "num_qubits": 2,
        "gate_budget": 10,
        "images": {
            "X0": "+XX",
            "X1": "+XX",
            "Z0": "+ZI",
            "Z1": "+ZZ",
        },
    }
    res = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert "witness" in res


def test_solve_budget_not_met():
    case = {
        "id": "test_tight",
        "num_qubits": 2,
        "gate_budget": 0,  # Impossible for CNOT
        "images": {
            "X0": "+XX",
            "X1": "+IX",
            "Z0": "+ZI",
            "Z1": "+ZZ",
        },
    }
    res = solve(case)
    assert res["status"] == "UNKNOWN"
    assert res["refusal_code"] == "GATE_BUDGET_NOT_MET"
