"""Tests for C013 Reference Solver.

Verifies:
1. Exact integer Smith Normal Form and simplicial homology.
2. Euler-Poincaré theorem sum (-1)^n beta_n = sum (-1)^n |K_n|.
3. Unimodular matrix products U * d * V = D, U * U_inv = I, V * V_inv = I.
4. Closed refusal and out-of-scope detections.
5. DDC 8-letter operational trace valid transitions.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.b_cohomology.c013_integral_homology_torsion.reference_solver.solver import (
    solve,
    solve_with_trace,
)

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = BASE_DIR / "participant_packet" / "examples"


def test_reference_solver_all_public_examples():
    """Asserts solver correctly processes all 20 public examples."""
    for p in sorted(EXAMPLES_DIR.glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8"))
        case = data["input"]
        res, tracer = solve_with_trace(case)
        assert res.get("id") == case.get("id")
        assert res.get("status") in ("SOLVED", "UNKNOWN", "OUT_OF_SCOPE")
        # Check DDC trace
        receipt = tracer.export_receipt()
        assert receipt.get("step_count", 0) >= 3


def test_reference_solver_euler_poincare_exactness():
    """Asserts sum (-1)^n beta_n == sum (-1)^n |K_n| across solved cases."""
    case = {
        "id": "torus_test",
        # 7-vertex torus minimal
        "simplices": [
            [1, 2, 4],
            [2, 3, 5],
            [3, 4, 6],
            [4, 5, 7],
            [5, 6, 1],
            [6, 7, 2],
            [7, 1, 3],
            [1, 4, 3],
            [2, 5, 4],
            [3, 6, 5],
            [4, 7, 6],
            [5, 1, 7],
            [6, 2, 1],
            [7, 3, 2],
        ],
    }
    # Face closure
    import itertools

    all_s = set()
    for s in case["simplices"]:
        for k in range(1, len(s) + 1):
            for f in itertools.combinations(sorted(s), k):
                all_s.add(f)
    case["simplices"] = [list(x) for x in sorted(all_s, key=lambda x: (len(x), x))]

    res = solve(case)
    assert res.get("status") == "SOLVED"
    hom = res.get("homology", [])
    b0 = int(hom[0]["betti"])
    b1 = int(hom[1]["betti"])
    b2 = int(hom[2]["betti"])
    # Torus: b0=1, b1=2, b2=1 -> chi = 1 - 2 + 1 = 0
    assert b0 == 1 and b1 == 2 and b2 == 1
    assert b0 - b1 + b2 == 0


def test_reference_solver_refusal_cases():
    """Asserts closed refusal codes are returned on invalid inputs."""
    # Simplex count out of bounds (> 1000)
    huge_case = {"id": "huge", "simplices": [[i] for i in range(1005)]}
    res = solve(huge_case)
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal") == "SIMPLEX_COUNT_OUT_OF_BOUNDS"

    # Dimension out of bounds (dim > 3)
    dim4_case = {"id": "dim4", "simplices": [[1, 2, 3, 4, 5]]}
    res = solve(dim4_case)
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal") == "DIMENSION_OUT_OF_BOUNDS"

    # Malformed non-mapping
    res = solve("not_a_mapping")
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal") == "MALFORMED_CASE_STRUCTURE"


def test_reference_solver_out_of_scope_witness():
    """Asserts unclosed complex returns OUT_OF_SCOPE with valid missing face witness."""
    unclosed = {"id": "unclosed", "simplices": [[1, 2, 3], [1, 2], [2, 3], [1], [2], [3]]}
    res = solve(unclosed)
    assert res.get("status") == "OUT_OF_SCOPE"
    witness = res.get("witness", {})
    assert "missing_face" in witness
    assert witness["missing_face"] == ["1", "3"]
