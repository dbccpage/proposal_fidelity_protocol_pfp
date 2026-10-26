"""Generator for the 24 C011 Public Examples.

Generates the full 24-case public test set under examples/ per C011 Specification Section 5.
Uses canonical rational wire format.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

EXAMPLES_DIR = Path(__file__).parent / "examples"
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def generate_all_public_examples() -> list[dict]:
    cases = []

    # 1. Round-4e Diamond (b1 = 2, Phi1 = 8)
    cases.append(
        {
            "id": "c011_ex01_round4e_diamond",
            "title": "Round-4e Diamond Public Example",
            "nodes": ["a", "b", "c", "d"],
            "edges": [["a", "b"], ["b", "c"], ["c", "a"], ["b", "d"], ["d", "a"]],
            "claims": {"a->b": "1", "b->c": "2", "c->a": "3", "b->d": "1", "d->a": "2"},
            "weights": {"a->b": "1", "b->c": "2", "c->a": "3", "b->d": "1", "d->a": "2"},
            "expected_status": "SOLVED",
            "expected_phi1": "8",
        }
    )

    # 2. Round-5 K4 with unit weights (b1 = 3)
    cases.append(
        {
            "id": "c011_ex02_k4_unit_weights",
            "title": "Round-5 K4 Complete Graph (Unit Weights)",
            "nodes": ["0", "1", "2", "3"],
            "edges": [["0", "1"], ["1", "2"], ["2", "0"], ["0", "3"], ["1", "3"], ["2", "3"]],
            "claims": {
                "0->1": "1",
                "1->2": "2",
                "2->0": "3",
                "0->3": "1",
                "1->3": "2",
                "2->3": "4",
            },
            "weights": {
                "0->1": "1",
                "1->2": "1",
                "2->0": "1",
                "0->3": "1",
                "1->3": "1",
                "2->3": "1",
            },
            "expected_status": "SOLVED",
        }
    )

    # 3. Round-5 K4 with claim weights (b1 = 3)
    cases.append(
        {
            "id": "c011_ex03_k4_claim_weights",
            "title": "Round-5 K4 Complete Graph (Claim Weights)",
            "nodes": ["0", "1", "2", "3"],
            "edges": [["0", "1"], ["1", "2"], ["2", "0"], ["0", "3"], ["1", "3"], ["2", "3"]],
            "claims": {
                "0->1": "1",
                "1->2": "2",
                "2->0": "3",
                "0->3": "1",
                "1->3": "2",
                "2->3": "4",
            },
            "weights": {
                "0->1": "1",
                "1->2": "2",
                "2->0": "3",
                "0->3": "1",
                "1->3": "2",
                "2->3": "4",
            },
            "expected_status": "SOLVED",
        }
    )

    # 4 to 15: One case per b1 from 1 to 12
    for b1 in range(1, 13):
        # Spanning tree path 0->1->...->(b1+1) plus b1 return chords to 0
        n_vertices = b1 + 2
        nodes = [str(i) for i in range(n_vertices)]
        edges = []
        claims = {}
        weights = {}

        # Tree edges
        for i in range(n_vertices - 1):
            e = [str(i), str(i + 1)]
            e_str = f"{i}->{i + 1}"
            edges.append(e)
            claims[e_str] = str(i + 1)
            weights[e_str] = "1"

        # b1 chords back to 0 or across
        for c in range(b1):
            target = c + 2
            e = [str(target), "0"]
            e_str = f"{target}->0"
            edges.append(e)
            claims[e_str] = str((c + 1) * 2)
            weights[e_str] = "1"

        cases.append(
            {
                "id": f"c011_ex{b1 + 3:02d}_b1_{b1:02d}",
                "title": f"Cycle-Rank Ladder Step b1={b1}",
                "nodes": nodes,
                "edges": edges,
                "claims": claims,
                "weights": weights,
                "cycle_rank": b1,
                "expected_status": "SOLVED",
            }
        )

    # 16. Already Exact Cochain (Phi1 = 0)
    cases.append(
        {
            "id": "c011_ex16_already_exact",
            "title": "Already Exact Cochain (Coboundary with Zero Obstruction)",
            "nodes": ["u0", "u1", "u2", "u3"],
            "edges": [["u0", "u1"], ["u1", "u2"], ["u2", "u3"], ["u0", "u3"]],
            # Potential: u0=0, u1=3, u2=7, u3=10
            # Claims: 0->1: 3, 1->2: 4, 2->3: 3, 0->3: 10 (exact!)
            "claims": {"u0->u1": "3", "u1->u2": "4", "u2->u3": "3", "u0->u3": "10"},
            "weights": {"u0->u1": "1", "u1->u2": "1", "u2->u3": "1", "u0->u3": "1"},
            "expected_status": "SOLVED",
            "expected_phi1": "0",
        }
    )

    # 17. Disconnected graph with 2 components (b1 = 2)
    cases.append(
        {
            "id": "c011_ex17_disconnected",
            "title": "Disconnected Graph with Two Cyclic Components",
            "nodes": ["c1_a", "c1_b", "c1_c", "c2_x", "c2_y", "c2_z"],
            "edges": [
                ["c1_a", "c1_b"],
                ["c1_b", "c1_c"],
                ["c1_c", "c1_a"],
                ["c2_x", "c2_y"],
                ["c2_y", "c2_z"],
                ["c2_z", "c2_x"],
            ],
            "claims": {
                "c1_a->c1_b": "2",
                "c1_b->c1_c": "3",
                "c1_c->c1_a": "5",
                "c2_x->c2_y": "1",
                "c2_y->c2_z": "1",
                "c2_z->c2_x": "1",
            },
            "weights": {
                "c1_a->c1_b": "1",
                "c1_b->c1_c": "1",
                "c1_c->c1_a": "1",
                "c2_x->c2_y": "1",
                "c2_y->c2_z": "1",
                "c2_z->c2_x": "1",
            },
            "expected_status": "SOLVED",
        }
    )

    # 18. Parallel edges between same pair
    cases.append(
        {
            "id": "c011_ex18_parallel_edges_1",
            "title": "Graph with Two Parallel Edges with Conflicting Claims",
            "nodes": ["x", "y"],
            "edges": [["x", "y"], ["x", "y"]],
            "claims": {"x->y": "3"},
            "weights": {"x->y": "1"},
            "expected_status": "SOLVED",
        }
    )

    # 19. Parallel edges in cycle
    cases.append(
        {
            "id": "c011_ex19_parallel_edges_2",
            "title": "Triangle with Parallel Chord",
            "nodes": ["p", "q", "r"],
            "edges": [["p", "q"], ["q", "r"], ["r", "p"], ["p", "r"]],
            "claims": {"p->q": "2", "q->r": "2", "r->p": "-4", "p->r": "3"},
            "weights": {"p->q": "1", "q->r": "1", "r->p": "1", "p->r": "2"},
            "expected_status": "SOLVED",
        }
    )

    # 20. OUT_OF_SCOPE: Self loop
    cases.append(
        {
            "id": "c011_ex20_out_of_scope_loop",
            "title": "Self-Loop Graph (Out of Scope)",
            "nodes": ["v0", "v1"],
            "edges": [["v0", "v0"], ["v0", "v1"]],
            "claims": {"v0->v0": "5", "v0->v1": "1"},
            "weights": {"v0->v0": "1", "v0->v1": "1"},
            "expected_status": "OUT_OF_SCOPE",
        }
    )

    # 21. OUT_OF_SCOPE: Nonpositive weight
    cases.append(
        {
            "id": "c011_ex21_out_of_scope_nonpos_weight",
            "title": "Non-Positive Edge Weight (Out of Scope)",
            "nodes": ["w0", "w1"],
            "edges": [["w0", "w1"]],
            "claims": {"w0->w1": "4"},
            "weights": {"w0->w1": "0"},
            "expected_status": "OUT_OF_SCOPE",
        }
    )

    # 22. OUT_OF_SCOPE: Unknown endpoint
    cases.append(
        {
            "id": "c011_ex22_out_of_scope_unknown_endpoint",
            "title": "Edge with Unknown Endpoint (Out of Scope)",
            "nodes": ["z0"],
            "edges": [["z0", "z_missing"]],
            "claims": {"z0->z_missing": "1"},
            "weights": {"z0->z_missing": "1"},
            "expected_status": "OUT_OF_SCOPE",
        }
    )

    # 23. Spanning Forest (b1 = 0, exact)
    cases.append(
        {
            "id": "c011_ex23_spanning_forest",
            "title": "Spanning Forest (Acyclic Two Trees)",
            "nodes": ["t1_a", "t1_b", "t2_a", "t2_b"],
            "edges": [["t1_a", "t1_b"], ["t2_a", "t2_b"]],
            "claims": {"t1_a->t1_b": "7", "t2_a->t2_b": "-3"},
            "weights": {"t1_a->t1_b": "1", "t2_a->t2_b": "1"},
            "expected_status": "SOLVED",
            "expected_phi1": "0",
        }
    )

    # 24. Tie with Multiple Optimal Repairs
    cases.append(
        {
            "id": "c011_ex24_tie_multiple_optima",
            "title": "Symmetric Cycle with Degenerate Optimal Basis",
            "nodes": ["m0", "m1", "m2", "m3"],
            "edges": [["m0", "m1"], ["m1", "m2"], ["m2", "m3"], ["m3", "m0"]],
            "claims": {"m0->m1": "1", "m1->m2": "1", "m2->m3": "1", "m3->m0": "1"},
            "weights": {"m0->m1": "1", "m1->m2": "1", "m2->m3": "1", "m3->m0": "1"},
            "expected_status": "SOLVED",
            "expected_phi1": "4",
        }
    )

    expected_dir = EXAMPLES_DIR / "expected"
    expected_dir.mkdir(parents=True, exist_ok=True)
    for c in cases:
        # Expected answers stay out of the input object that solvers and models read.
        expected = {
            k.removeprefix("expected_"): c.pop(k)
            for k in ("expected_status", "expected_phi1")
            if k in c
        }
        file_path = EXAMPLES_DIR / f"{c['id']}.json"
        file_path.write_text(
            json.dumps(c, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
        )
        record = {"id": c["id"], **expected}
        (expected_dir / f"{c['id']}.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
        )

    return cases


if __name__ == "__main__":
    generated = generate_all_public_examples()
    print(f"Generated {len(generated)} public examples in {EXAMPLES_DIR}")
