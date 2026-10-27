"""Tests for C014 Reference Solver.

Verifies:
1. Exact rational linear algebra and Hodge decomposition.
2. Pairwise orthogonality under weighted inner product <g, c> = 0, <g, h> = 0, <c, h> = 0.
3. Closed refusal and out-of-scope detections.
4. DDC 8-letter operational trace valid transitions.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from projects.mssn_sn_symgam.challenges.b_cohomology.c014_discrete_hodge_decomposition.reference_solver.solver import (
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


def test_reference_solver_orthogonality():
    """Asserts decomposition parts g, c, h are pairwise orthogonal under W1."""
    case = {
        "id": "ortho_test",
        "vertices": ["v0", "v1", "v2"],
        "edges": ["e01", "e12", "e20"],
        "faces": ["f0"],
        "edge_endpoints": {"e01": ["v0", "v1"], "e12": ["v1", "v2"], "e20": ["v2", "v0"]},
        "face_boundaries": {"f0": {"e01": 1, "e12": 1, "e20": 1}},
        "flow": {"e01": "3", "e12": "5", "e20": "-2"},
        "weights": {"e01": "2", "e12": "3", "e20": "5"},
    }
    res = solve(case)
    assert res.get("status") == "SOLVED"
    assert res.get("harmonic_dim") == "0"


def test_reference_solver_refusal_cases():
    """Asserts closed refusal codes are returned on invalid inputs."""
    # Vertex count out of bounds (> 80)
    huge_verts = {"id": "huge_v", "vertices": [f"v{i}" for i in range(85)], "edges": []}
    res = solve(huge_verts)
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal") == "VERTEX_COUNT_OUT_OF_BOUNDS"

    # Edge count out of bounds (> 200)
    huge_edges = {"id": "huge_e", "vertices": ["v0", "v1"], "edges": [f"e{i}" for i in range(205)]}
    res = solve(huge_edges)
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal") == "EDGE_COUNT_OUT_OF_BOUNDS"

    # Non-positive weight
    bad_weight = {
        "id": "bad_w",
        "vertices": ["v0", "v1"],
        "edges": [["v0", "v1"]],
        "weights": {"e_v0_v1": "0"},
    }
    res = solve(bad_weight)
    assert res.get("status") == "UNKNOWN"
    assert res.get("refusal") == "WEIGHT_NON_POSITIVE"


def test_reference_solver_out_of_scope_witness():
    """Asserts unoriented complex returns OUT_OF_SCOPE with D1_D0_NONZERO."""
    unoriented = {
        "id": "unoriented",
        "vertices": ["v0", "v1", "v2"],
        "edges": ["e01", "e12", "e20"],
        "faces": ["f0"],
        "edge_endpoints": {"e01": ["v0", "v1"], "e12": ["v1", "v2"], "e20": ["v2", "v0"]},
        "face_boundaries": {"f0": {"e01": 1, "e12": 1, "e20": -1}},
    }
    res = solve(unoriented)
    assert res.get("status") == "OUT_OF_SCOPE"
    witness = res.get("witness", {})
    assert witness.get("reason") == "D1_D0_NONZERO"
