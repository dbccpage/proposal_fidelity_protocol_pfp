"""Tests validating reference solver, Pauli algebra, and mathematical invariants.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from c021_q40_r.reference_solver.ddc_tracer import (
    VALID_DDC_LETTERS,
)
from c021_q40_r.reference_solver.pauli import (
    _SINGLE_PAULI_MUL,
    PauliString,
)
from c021_q40_r.reference_solver.solver import (
    solve,
    solve_with_trace,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = ROOT_DIR / "participant_packet" / "examples"


# ---------------------------------------------------------------------------
# 1. Pauli Algebra & Symplectic Phase Tracking Tests
# ---------------------------------------------------------------------------


def test_pauli_single_qubit_multiplication_table():
    # Y = iXZ
    # Check identities
    for c in ("I", "X", "Y", "Z"):
        assert _SINGLE_PAULI_MUL[(c, c)][0] == 0
        assert _SINGLE_PAULI_MUL[(c, c)][1] == "I"

    # X * Y = i Z (phase 1)
    assert _SINGLE_PAULI_MUL[("X", "Y")] == (1, "Z")
    # Y * X = -i Z (phase 3)
    assert _SINGLE_PAULI_MUL[("Y", "X")] == (3, "Z")

    # X * Z = -i Y (phase 3)
    assert _SINGLE_PAULI_MUL[("X", "Z")] == (3, "Y")
    # Z * X = i Y (phase 1)
    assert _SINGLE_PAULI_MUL[("Z", "X")] == (1, "Y")

    # Y * Z = i X (phase 1)
    assert _SINGLE_PAULI_MUL[("Y", "Z")] == (1, "X")
    # Z * Y = -i X (phase 3)
    assert _SINGLE_PAULI_MUL[("Z", "Y")] == (3, "X")


def test_pauli_string_multiplication_phase_tracking():
    # XY * YZ = (X*Y) (Y*Z) = (iZ) (iX) = i^2 ZX = -ZX
    p1 = PauliString("XY")
    p2 = PauliString("YZ")
    phase, prod = p1.multiply(p2)
    assert phase == 2  # i^2 = -1
    assert prod.word == "ZX"

    # Test commutativity of Bell stabilizers XX and ZZ:
    # XX * ZZ = (X*Z) (X*Z) = (-iY) (-iY) = (-i)^2 YY = -YY (phase 2)
    # ZZ * XX = (Z*X) (Z*X) = (iY) (iY) = i^2 YY = -YY (phase 2)
    xx = PauliString("XX")
    zz = PauliString("ZZ")
    phase_xz, prod_xz = xx.multiply(zz)
    phase_zx, prod_zx = zz.multiply(xx)
    assert phase_xz == phase_zx == 2
    assert prod_xz.word == prod_zx.word == "YY"


def test_pauli_commutation_and_symplectic_roundtrip():
    # XX and ZZ commute (2 anticommuting positions: even)
    xx = PauliString("XX")
    zz = PauliString("ZZ")
    assert xx.commutes_with(zz)
    assert zz.commutes_with(xx)

    # X and Z anticommute (1 anticommuting position: odd)
    x = PauliString("X")
    z = PauliString("Z")
    assert not x.commutes_with(z)

    # Symplectic roundtrip
    for word in ("I", "X", "Y", "Z", "XYZI", "ZZXX", "YYYY"):
        p = PauliString(word)
        vec = p.to_symplectic_vector()
        assert len(vec) == 2 * len(word)
        reconstructed = PauliString.from_symplectic_vector(vec, len(word))
        assert reconstructed == p


# ---------------------------------------------------------------------------
# 2. Public Examples Verification
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("ex_num", range(1, 13))
def test_solve_public_example(ex_num: int):
    prefix = f"ex{ex_num:02d}_"
    matches = list(EXAMPLES_DIR.glob(f"{prefix}*.json"))
    assert len(matches) == 1, f"Could not find example file with prefix {prefix}"

    ex_file = matches[0]
    data = json.loads(ex_file.read_text(encoding="utf-8"))
    inp = data["input"]
    expected = data["expected_output"]

    actual = solve(inp)
    assert actual == expected, (
        f"Mismatch on {ex_file.name}:\nActual:   {actual}\nExpected: {expected}"
    )


# ---------------------------------------------------------------------------
# 3. Frustration & Degeneracy Invariant Tests
# ---------------------------------------------------------------------------


def test_frustration_opposing_signs_invariant():
    # Opposing target signs on same generator
    case = {
        "id": "case_frustration_test",
        "n": 2,
        "terms": [
            {"id": "t_pos", "P": "ZZ", "w": [3, 2], "target": 1},
            {"id": "t_neg", "P": "ZZ", "w": [3, 2], "target": -1},
        ],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    # For b = +1: penalty is 0 + 3/2 = 3/2
    # For b = -1: penalty is 3/2 + 0 = 3/2
    # E0 must be [3, 2]
    assert res["energy"] == [3, 2]
    # Both assignments are minimizers
    assert res["minimizers"] == [0, 1]
    # k = 1 generator, n = 2 -> subspace factor = 2^(2-1) = 2
    # Total degeneracy = 2 minimizers * 2 = 4
    assert res["degeneracy"] == 4


def test_degeneracy_scaling_with_unused_qubits():
    # n = 4, but only 1 generator on qubit 0
    case = {
        "id": "case_unused_qubits",
        "n": 4,
        "terms": [
            {"id": "t_z", "P": "ZIII", "w": [1, 1], "target": 1},
        ],
    }
    res = solve(case)
    assert res["status"] == "SOLVED"
    assert res["energy"] == [0, 1]
    assert res["minimizers"] == [0]
    # k = 1, n = 4 -> degeneracy = 1 * 2^(4-1) = 8
    assert res["degeneracy"] == 8


# ---------------------------------------------------------------------------
# 4. DDC 8-Letter Operational Trace Invariant Tests
# ---------------------------------------------------------------------------


def test_ddc_tracer_trace_integrity_and_letters():
    # Test on solved case
    case_solved = {
        "id": "case_ddc_solved",
        "n": 2,
        "terms": [
            {"id": "t_xx", "P": "XX", "w": [1, 1], "target": 1},
            {"id": "t_zz", "P": "ZZ", "w": [1, 1], "target": 1},
        ],
    }
    result_s, tracer_s = solve_with_trace(case_solved)
    assert result_s["status"] == "SOLVED"

    # Verify cryptographic receipt chain
    ok, msg = tracer_s.verify_integrity()
    assert ok, f"Trace integrity verification failed: {msg}"

    # Verify 8-letter alphabet transitions: C -> R -> E -> I -> T
    letters = [step["letter"] for step in tracer_s.steps]
    for letter in letters:
        assert letter in VALID_DDC_LETTERS
    assert letters == ["C", "R", "E", "I", "T"]

    # Test on OUT_OF_SCOPE case: C -> R -> M -> T
    case_oos = {
        "id": "case_ddc_oos",
        "n": 1,
        "terms": [
            {"id": "t_x", "P": "X", "w": [1, 1], "target": 1},
            {"id": "t_z", "P": "Z", "w": [1, 1], "target": 1},
        ],
    }
    result_o, tracer_o = solve_with_trace(case_oos)
    assert result_o["status"] == "OUT_OF_SCOPE"
    ok, msg = tracer_o.verify_integrity()
    assert ok
    letters_o = [step["letter"] for step in tracer_o.steps]
    assert letters_o == ["C", "R", "M", "T"]

    # Test on UNKNOWN case: C -> M -> T
    case_unk = {"id": "case_ddc_unk", "n": 9, "terms": []}
    result_u, tracer_u = solve_with_trace(case_unk)
    assert result_u["status"] == "UNKNOWN"
    ok, msg = tracer_u.verify_integrity()
    assert ok
    letters_u = [step["letter"] for step in tracer_u.steps]
    assert letters_u == ["C", "M", "T"]


# ---------------------------------------------------------------------------
# 5. Closed Refusal List Validation Tests
# ---------------------------------------------------------------------------


def test_closed_refusal_qubit_bounds():
    # n = 0
    res0 = solve({"id": "c", "n": 0, "terms": []})
    assert res0["status"] == "UNKNOWN" and res0["refusal_code"] == "NUM_QUBITS_OUT_OF_BOUNDS"

    # n = 9
    res9 = solve({"id": "c", "n": 9, "terms": []})
    assert res9["status"] == "UNKNOWN" and res9["refusal_code"] == "NUM_QUBITS_OUT_OF_BOUNDS"

    # n = float
    res_fl = solve({"id": "c", "n": 2.0, "terms": []})
    assert res_fl["status"] == "UNKNOWN" and res_fl["refusal_code"] == "NUM_QUBITS_OUT_OF_BOUNDS"

    # n = bool
    res_b = solve({"id": "c", "n": True, "terms": []})
    assert res_b["status"] == "UNKNOWN" and res_b["refusal_code"] == "NUM_QUBITS_OUT_OF_BOUNDS"


def test_closed_refusal_term_count_bounds():
    terms_25 = [{"id": f"t_{i}", "P": "Z", "w": [1, 1], "target": 1} for i in range(25)]
    res = solve({"id": "c", "n": 1, "terms": terms_25})
    assert res["status"] == "UNKNOWN" and res["refusal_code"] == "TERM_COUNT_OUT_OF_BOUNDS"


def test_closed_refusal_duplicate_term_ids():
    case = {
        "id": "c",
        "n": 1,
        "terms": [
            {"id": "t_dup", "P": "Z", "w": [1, 1], "target": 1},
            {"id": "t_dup", "P": "I", "w": [1, 1], "target": 1},
        ],
    }
    res = solve(case)
    assert res["status"] == "UNKNOWN" and res["refusal_code"] == "DUPLICATE_TERM_ID"


def test_closed_refusal_malformed_pauli_words():
    # Wrong length
    res_len = solve({"id": "c", "n": 2, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 1}]})
    assert res_len["status"] == "UNKNOWN" and res_len["refusal_code"] == "MALFORMED_PAULI_WORD"

    # Invalid character
    res_char = solve(
        {"id": "c", "n": 2, "terms": [{"id": "t", "P": "ZA", "w": [1, 1], "target": 1}]}
    )
    assert res_char["status"] == "UNKNOWN" and res_char["refusal_code"] == "MALFORMED_PAULI_WORD"


def test_closed_refusal_invalid_weights():
    # Non-positive numerator
    res_0 = solve({"id": "c", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [0, 1], "target": 1}]})
    assert res_0["status"] == "UNKNOWN" and res_0["refusal_code"] == "INVALID_WEIGHT"

    # Negative denominator
    res_neg = solve(
        {"id": "c", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, -2], "target": 1}]}
    )
    assert res_neg["status"] == "UNKNOWN" and res_neg["refusal_code"] == "INVALID_WEIGHT"

    # Float weight
    res_fl = solve(
        {"id": "c", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1.5, 2], "target": 1}]}
    )
    assert res_fl["status"] == "UNKNOWN" and res_fl["refusal_code"] == "INVALID_WEIGHT"

    # Single number instead of pair
    res_num = solve({"id": "c", "n": 1, "terms": [{"id": "t", "P": "Z", "w": 1, "target": 1}]})
    assert res_num["status"] == "UNKNOWN" and res_num["refusal_code"] == "INVALID_WEIGHT"


def test_closed_refusal_invalid_targets():
    # Target 0
    res_0 = solve({"id": "c", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": 0}]})
    assert res_0["status"] == "UNKNOWN" and res_0["refusal_code"] == "INVALID_TARGET_SIGN"

    # Target bool True
    res_b = solve(
        {"id": "c", "n": 1, "terms": [{"id": "t", "P": "Z", "w": [1, 1], "target": True}]}
    )
    assert res_b["status"] == "UNKNOWN" and res_b["refusal_code"] == "INVALID_TARGET_SIGN"


def test_closed_refusal_malformed_structure():
    # Not a dict
    assert solve("not_a_dict")["status"] == "UNKNOWN"

    # Missing case id
    assert solve({"n": 1, "terms": []})["refusal_code"] == "MALFORMED_CASE_STRUCTURE"

    # Terms not a list
    assert (
        solve({"id": "c", "n": 1, "terms": "not_list"})["refusal_code"]
        == "MALFORMED_CASE_STRUCTURE"
    )
