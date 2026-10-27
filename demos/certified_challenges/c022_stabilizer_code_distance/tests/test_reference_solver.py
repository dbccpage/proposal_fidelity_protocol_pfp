"""Tests for C022 Reference Solver."""

from __future__ import annotations

from c022_stabilizer_code_distance.reference_solver.ddc_tracer import (
    DDCTracer,
)
from c022_stabilizer_code_distance.reference_solver.pauli import (
    PauliString,
)
from c022_stabilizer_code_distance.reference_solver.solver import (
    in_span_f2,
    rank_f2,
    solve,
)


def test_pauli_basics():
    p1 = PauliString("XIZ")
    p2 = PauliString("ZIX")
    assert p1.weight == 2
    assert p2.weight == 2
    # X and Z anticommute on qubit 0 and qubit 2 -> total 2 anticommutations -> commute!
    assert p1.commutes_with(p2)

    p3 = PauliString("XII")
    p4 = PauliString("ZII")
    assert not p3.commutes_with(p4)


def test_f2_linear_algebra():
    mat = [
        [1, 0, 1],
        [0, 1, 1],
        [1, 1, 0],
    ]
    # Row 0 + Row 1 = Row 2 over F_2, rank should be 2
    assert rank_f2(mat) == 2
    assert in_span_f2(mat[:2], [1, 1, 0])
    assert not in_span_f2(mat[:2], [1, 0, 0])


def test_five_qubit_code():
    # [[5, 1, 3]] code
    case = {
        "id": "five_qubit",
        "num_qubits": 5,
        "generators": [
            "+XZZXI",
            "+IXZZX",
            "+XIXZZ",
            "+ZXIXZ",
        ],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["distance"] == 3
    assert len(res["logical"]) == 5
    assert res["lower_bound"] is None


def test_solver_emits_no_synthetic_refutation():
    """The former one-line "LRAT" trace was not a derivation; nothing replaces it."""
    case = {
        "id": "five_qubit_deterministic",
        "num_qubits": 5,
        "generators": ["+XZZXI", "+IXZZX", "+XIXZZ", "+ZXIXZ"],
    }
    assert solve(case)["lower_bound"] is None


def test_steane_code():
    # [[7, 1, 3]] Steane code
    case = {
        "id": "steane",
        "num_qubits": 7,
        "generators": [
            "+IIIXXXX",
            "+IXXIIXX",
            "+XIXIXIX",
            "+IIIZZZZ",
            "+IZZIIZZ",
            "+ZIZIZIZ",
        ],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["distance"] == 3
    assert len(res["logical"]) == 7
    assert res["lower_bound"] is None


def test_out_of_scope_anticommuting():
    case = {
        "id": "anticomm",
        "num_qubits": 2,
        "generators": ["+XI", "+ZI"],
    }
    res = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["kind"] == "anticommuting"


def test_out_of_scope_dependent():
    case = {
        "id": "dep",
        "num_qubits": 2,
        "generators": ["+XX", "+ZZ", "+YY"],  # XX * ZZ = -YY
    }
    res = solve(case)
    assert res["status"] == "OUT_OF_SCOPE"
    assert res["witness"]["kind"] == "dependent"


def test_ddc_tracer():
    tracer = DDCTracer("test_run")
    s1 = tracer.record_step("E", "ExactRepair", {"key": "val1"})
    s2 = tracer.record_step("C", "ContextExposure", {"key": "val2"})
    assert tracer.verify_integrity()
    assert s2["prev_step_hash"] == s1["step_hash"]
