"""Tests validating C011 reference solver and DDC tracer.

AuthorityEffect: None.
"""

from __future__ import annotations

from c011_cycle_rank_ladder_coboundary_repair.reference_solver.solver import (
    solve,
    solve_with_trace,
)


def test_diamond_worked_example_exact_solution():
    diamond_case = {
        "id": "diamond_test",
        "vertices": ["a", "b", "c", "d"],
        "edges": [
            {"id": "a->b", "u": "a", "v": "b", "claim": "1", "weight": "1"},
            {"id": "b->c", "u": "b", "v": "c", "claim": "2", "weight": "2"},
            {"id": "c->a", "u": "c", "v": "a", "claim": "3", "weight": "3"},
            {"id": "b->d", "u": "b", "v": "d", "claim": "1", "weight": "1"},
            {"id": "d->a", "u": "d", "v": "a", "claim": "2", "weight": "2"},
        ],
    }
    ans = solve(diamond_case)
    assert ans["status"] == "SOLVED"
    assert ans["phi1"] == "8"
    assert ans["potential"] == {"a": "0", "b": "-3", "c": "-3", "d": "-2"}
    assert ans["repair"] == {"a->b": "4", "b->c": "2"}
    assert ans["dual"]["a->b"] == "1"
    assert ans["dual"]["b->c"] == "2"
    assert ans["dual"]["c->a"] == "2"
    assert ans["dual"]["b->d"] == "-1"
    assert ans["dual"]["d->a"] == "-1"


def test_forest_zero_defect():
    tree_case = {
        "id": "tree_test",
        "vertices": ["1", "2", "3"],
        "edges": [
            {"id": "e12", "u": "1", "v": "2", "claim": "5", "weight": "1"},
            {"id": "e23", "u": "2", "v": "3", "claim": "-3", "weight": "2"},
        ],
    }
    ans = solve(tree_case)
    assert ans["status"] == "SOLVED"
    assert ans["phi1"] == "0"
    assert ans["repair"] == {}
    assert ans["dual"] == {}
    assert ans["potential"]["1"] == "0"
    assert ans["potential"]["2"] == "5"
    assert ans["potential"]["3"] == "2"


def test_already_exact_cycle():
    exact_case = {
        "id": "exact_c3",
        "vertices": ["x", "y", "z"],
        "edges": [
            {"id": "e_xy", "u": "x", "v": "y", "claim": "1", "weight": "1"},
            {"id": "e_yz", "u": "y", "v": "z", "claim": "2", "weight": "1"},
            {"id": "e_zx", "u": "z", "v": "x", "claim": "-3", "weight": "1"},
        ],
    }
    ans = solve(exact_case)
    assert ans["status"] == "SOLVED"
    assert ans["phi1"] == "0"
    assert ans["repair"] == {}
    assert ans["dual"] == {}


def test_closed_refusals():
    # 1. VERTEX_COUNT_OUT_OF_BOUNDS (empty or > 60)
    ans1 = solve({"id": "t1", "vertices": [], "edges": []})
    assert ans1["status"] == "UNKNOWN"
    assert ans1["refusal_code"] == "VERTEX_COUNT_OUT_OF_BOUNDS"

    ans1_large = solve({"id": "t1_l", "vertices": [f"v{i}" for i in range(65)], "edges": []})
    assert ans1_large["status"] == "UNKNOWN"
    assert ans1_large["refusal_code"] == "VERTEX_COUNT_OUT_OF_BOUNDS"

    # 2. EDGE_COUNT_OUT_OF_BOUNDS (> 200)
    ans2 = solve(
        {
            "id": "t2",
            "vertices": ["a", "b"],
            "edges": [
                {"id": f"e{i}", "u": "a", "v": "b", "claim": "1", "weight": "1"} for i in range(205)
            ],
        }
    )
    assert ans2["status"] == "UNKNOWN"
    assert ans2["refusal_code"] == "EDGE_COUNT_OUT_OF_BOUNDS"

    # 3. INVALID_CAPACITY
    ans3 = solve(
        {
            "id": "t3",
            "vertices": ["a", "b"],
            "edges": [{"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "bad_weight"}],
        }
    )
    assert ans3["status"] == "UNKNOWN"
    assert ans3["refusal_code"] == "INVALID_CAPACITY"

    # 4. NEGATIVE_WEIGHT (when refusal expected)
    ans4 = solve(
        {
            "id": "t4",
            "expect_refusal": True,
            "vertices": ["a", "b"],
            "edges": [{"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "-2"}],
        }
    )
    assert ans4["status"] == "UNKNOWN"
    assert ans4["refusal_code"] == "NEGATIVE_WEIGHT"

    # 5. DISCONNECTED_GRAPH (when require_connected: true)
    ans5 = solve(
        {
            "id": "t5",
            "require_connected": True,
            "vertices": ["a", "b", "c", "d"],
            "edges": [
                {"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "1"},
                {"id": "e2", "u": "c", "v": "d", "claim": "1", "weight": "1"},
            ],
        }
    )
    assert ans5["status"] == "UNKNOWN"
    assert ans5["refusal_code"] == "DISCONNECTED_GRAPH"

    # 6. MALFORMED_EDGE_SPEC
    ans6 = solve(
        {
            "id": "t6",
            "vertices": ["a", "b"],
            "edges": [{"id": "e1", "u": 123, "v": "b", "claim": "1", "weight": "1"}],
        }
    )
    assert ans6["status"] == "UNKNOWN"
    assert ans6["refusal_code"] == "MALFORMED_EDGE_SPEC"

    # 7. INVALID_TARGET_DEFECT
    ans7 = solve(
        {
            "id": "t7",
            "target_defect": "-5",
            "vertices": ["a", "b"],
            "edges": [{"id": "e1", "u": "a", "v": "b", "claim": "1", "weight": "1"}],
        }
    )
    assert ans7["status"] == "UNKNOWN"
    assert ans7["refusal_code"] == "INVALID_TARGET_DEFECT"

    # 8. MALFORMED_CASE_STRUCTURE
    ans8 = solve("not_a_dict")  # type: ignore
    assert ans8["status"] == "UNKNOWN"
    assert ans8["refusal_code"] == "MALFORMED_CASE_STRUCTURE"


def test_out_of_scope_triggers():
    # 1. Nonpositive weight
    ans_np = solve(
        {
            "id": "oos_np",
            "allow_out_of_scope": True,
            "vertices": ["a", "b"],
            "edges": [{"id": "e_np", "u": "a", "v": "b", "claim": "1", "weight": "0"}],
        }
    )
    assert ans_np["status"] == "OUT_OF_SCOPE"
    assert ans_np["witness"]["edge"] == "e_np"
    assert ans_np["witness"]["reason"] == "NONPOSITIVE_WEIGHT"

    # 2. Self loop
    ans_sl = solve(
        {
            "id": "oos_sl",
            "vertices": ["a"],
            "edges": [{"id": "e_sl", "u": "a", "v": "a", "claim": "1", "weight": "1"}],
        }
    )
    assert ans_sl["status"] == "OUT_OF_SCOPE"
    assert ans_sl["witness"]["edge"] == "e_sl"
    assert ans_sl["witness"]["reason"] == "SELF_LOOP"

    # 3. Unknown endpoint
    ans_ue = solve(
        {
            "id": "oos_ue",
            "vertices": ["a"],
            "edges": [{"id": "e_ue", "u": "a", "v": "ghost", "claim": "1", "weight": "1"}],
        }
    )
    assert ans_ue["status"] == "OUT_OF_SCOPE"
    assert ans_ue["witness"]["edge"] == "e_ue"
    assert ans_ue["witness"]["reason"] == "UNKNOWN_ENDPOINT"


def test_ddc_tracer_hash_chain_and_tamper():
    diamond_case = {
        "id": "diamond_ddc",
        "vertices": ["a", "b", "c", "d"],
        "edges": [
            {"id": "a->b", "u": "a", "v": "b", "claim": "1", "weight": "1"},
            {"id": "b->c", "u": "b", "v": "c", "claim": "2", "weight": "2"},
            {"id": "c->a", "u": "c", "v": "a", "claim": "3", "weight": "3"},
            {"id": "b->d", "u": "b", "v": "d", "claim": "1", "weight": "1"},
            {"id": "d->a", "u": "d", "v": "a", "claim": "2", "weight": "2"},
        ],
    }
    ans, tracer = solve_with_trace(diamond_case)
    assert ans["status"] == "SOLVED"
    ok, msg = tracer.verify_integrity()
    assert ok is True
    assert msg == "VALID_CHAIN"

    # Test tamper detection
    tracer.steps[2]["payload"]["tampered"] = True
    ok_tamper, msg_tamper = tracer.verify_integrity()
    assert ok_tamper is False
    assert "Hash verification failed" in msg_tamper


def test_cycle_rank_ladder_b1_to_16():
    """Verifies that solver succeeds on all cycle ranks from 1 to 16."""
    for b1 in range(1, 17):
        n_verts = b1 + 2
        verts = [f"v{i}" for i in range(n_verts)]
        edges = []
        for i in range(n_verts - 1):
            edges.append(
                {
                    "id": f"t_{i}",
                    "u": verts[i],
                    "v": verts[i + 1],
                    "claim": str(i + 1),
                    "weight": "1",
                }
            )
        for j in range(b1):
            s = j
            t = (j + 2) % n_verts
            edges.append(
                {
                    "id": f"c_{j}",
                    "u": verts[s],
                    "v": verts[t],
                    "claim": str(j * 3 + 2),
                    "weight": "1",
                }
            )

        case = {"id": f"ladder_b{b1}", "vertices": verts, "edges": edges}
        ans = solve(case)
        assert ans["status"] == "SOLVED"
        assert int(ans["phi1"]) >= 0
