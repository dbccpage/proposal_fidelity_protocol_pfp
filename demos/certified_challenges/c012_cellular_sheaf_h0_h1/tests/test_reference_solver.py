"""Tests for C012 Reference Solver.

Verifies:
1. Exact rational linear algebra and sheaf coboundary construction.
2. Rank-Nullity / Euler-Poincaré theorem dim H^0 - dim H^1 = dim C^0 - dim C^1.
3. Fredholm duality & gluing/obstruction certificates.
4. Closed refusal and out-of-scope detections.
5. DDC 8-letter operational trace valid transitions.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

from c012_cellular_sheaf_h0_h1.reference_solver.solver import (
    solve,
    solve_with_trace,
)

BASE_DIR = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = BASE_DIR / "participant_packet" / "examples"


def test_reference_solver_all_public_examples():
    """Asserts solver correctly processes all 20 public examples."""
    for p in sorted(EXAMPLES_DIR.glob("*.json")):
        import json

        data = json.loads(p.read_text(encoding="utf-8"))
        case = data.get("input", data)
        res, tracer = solve_with_trace(case)
        assert res.get("id") == case.get("id")
        assert res.get("status") in ("SOLVED", "UNKNOWN", "OUT_OF_SCOPE")
        # Check DDC trace
        assert len(tracer.steps) >= 2
        ok, msg = tracer.verify_integrity()
        assert ok is True, f"DDC tracer hash chain failed on {p.name}: {msg}"


def test_reference_solver_euler_poincare_exactness():
    """Asserts dim H^0 - dim H^1 == dim C^0 - dim C^1 across solved cases."""
    case = {
        "id": "test_triangle_q1",
        "vertices": [{"id": "v0", "dim": 1}, {"id": "v1", "dim": 1}, {"id": "v2", "dim": 1}],
        "edges": [
            {"id": "e0", "u": "v0", "v": "v1", "dim": 1, "F_u": [["1"]], "F_v": [["1"]]},
            {"id": "e1", "u": "v1", "v": "v2", "dim": 1, "F_u": [["1"]], "F_v": [["1"]]},
            {"id": "e2", "u": "v0", "v": "v2", "dim": 1, "F_u": [["1"]], "F_v": [["1"]]},
        ],
        "targets": [{"b": ["0", "0", "0"]}],
    }
    res = solve(case)
    assert res.get("status") == "SOLVED"
    h0 = int(res["h0_dim"])
    h1 = int(res["h1_dim"])
    dim_c0 = 3
    dim_c1 = 3
    assert (h0 - h1) == (dim_c0 - dim_c1)
    assert h0 == 1
    assert h1 == 1


def test_reference_solver_gluing_and_obstruction_duality():
    """Asserts Fredholm duality on a cycle: delta x = b iff <eta, b> = 0 for all eta in ker delta^T."""
    case = {
        "id": "test_duality_cycle",
        "vertices": [{"id": "v0", "dim": 1}, {"id": "v1", "dim": 1}],
        "edges": [
            {"id": "e0", "u": "v0", "v": "v1", "dim": 1, "F_u": [["1"]], "F_v": [["1"]]},
            {"id": "e1", "u": "v0", "v": "v1", "dim": 1, "F_u": [["1"]], "F_v": [["1"]]},
        ],
        "targets": [
            {"b": ["0", "0"]},  # solvable
            {"b": ["1", "0"]},  # obstructed
        ],
    }
    res = solve(case)
    assert res.get("status") == "SOLVED"
    t0 = res["targets"][0]
    assert t0["glues"] is True
    assert "x" in t0

    t1 = res["targets"][1]
    assert t1["glues"] is False
    assert "eta" in t1


def test_reference_solver_refusal_on_vertex_oob():
    """Asserts UNKNOWN refusal on vertex count > 30."""
    case = {
        "id": "test_vertex_oob",
        "vertices": [{"id": f"v{i}", "dim": 1} for i in range(35)],
        "edges": [],
        "targets": [],
    }
    res = solve(case)
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal") == "VERTEX_COUNT_OUT_OF_BOUNDS"


def test_reference_solver_oos_on_self_loop():
    """Asserts OUT_OF_SCOPE on self loop."""
    case = {
        "id": "test_self_loop",
        "vertices": [{"id": "v0", "dim": 1}],
        "edges": [{"id": "e0", "u": "v0", "v": "v0", "dim": 1, "F_u": [["1"]], "F_v": [["1"]]}],
        "targets": [],
    }
    res = solve(case)
    assert res.get("status") == "OUT_OF_SCOPE"
    assert res.get("witness", {}).get("reason") == "SELF_LOOP"
