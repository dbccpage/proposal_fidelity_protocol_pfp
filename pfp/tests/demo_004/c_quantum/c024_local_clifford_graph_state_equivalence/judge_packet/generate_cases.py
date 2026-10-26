"""Case Generator for C024 (Local Clifford Graph State Equivalence).

Generates:
- 30 hidden base cases (15 equivalent, 15 non-equivalent)
- 10 controls (permutation, LC gauge, swapped pairs)
- 6 poisoned schema-valid cases (isomorphism traps, self loops, out of bounds)
- 10 public examples for participant_packet/examples/

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from typing import Any

# Ensure repository root is in sys.path
_p = Path(__file__).resolve()
for _par in _p.parents:
    if (_par / "omega_engine_projects").exists():
        if str(_par) not in sys.path:
            sys.path.insert(0, str(_par))
        break

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.graph import (
    SimpleGraph,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c024_local_clifford_graph_state_equivalence.reference_solver.solver import (
    solve,
)


def random_connected_graph(
    n: int, edge_prob: float = 0.35, rng: random.Random | None = None
) -> SimpleGraph:
    """Generates a random connected simple graph on n vertices."""
    if rng is None:
        rng = random.Random()

    edges: list[list[int]] = []
    # Spanning tree first to ensure connectedness
    nodes = list(range(n))
    rng.shuffle(nodes)
    for i in range(1, n):
        parent = rng.choice(nodes[:i])
        edges.append([min(nodes[i], parent), max(nodes[i], parent)])

    # Add extra random edges
    for u in range(n):
        for v in range(u + 1, n):
            if [u, v] not in edges and rng.random() < edge_prob:
                edges.append([u, v])

    return SimpleGraph(n, edges)


def generate_all_cases() -> None:
    rng = random.Random(20260928)

    base_dir = Path(__file__).resolve().parent / "cases"
    examples_dir = Path(__file__).resolve().parent.parent / "participant_packet" / "examples"
    base_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Generate 30 Base Cases (15 equivalent, 15 non-equivalent)
    # ---------------------------------------------------------
    base_cases: list[dict[str, Any]] = []

    # 15 Equivalent cases across various n: 4, 5, 6, 7, 8, 9, 10, 12, 14, 16
    eq_ns = [4, 4, 5, 5, 6, 6, 7, 8, 8, 9, 10, 10, 12, 14, 16]
    for idx, n in enumerate(eq_ns):
        case_id = f"c024_base_{idx + 1:02d}_eq"
        g = random_connected_graph(n, edge_prob=0.30, rng=rng)
        curr = g.copy()
        num_moves = rng.randint(1, min(2 * n, 10))
        for _ in range(num_moves):
            v = rng.randint(0, n - 1)
            curr = curr.local_complementation(v)

        case_obj = {
            "id": case_id,
            "num_vertices": n,
            "g": g.to_edge_list(),
            "g_prime": curr.to_edge_list(),
        }
        sol = solve(case_obj)
        assert sol["status"] == "SOLVED" and sol["equivalent"] is True
        base_cases.append(case_obj)

    # 15 Non-Equivalent cases (5 differing by single edge, 10 random non-equivalent)
    neq_ns = [4, 4, 5, 5, 6, 6, 7, 8, 8, 9, 10, 10, 12, 14, 16]
    for idx, n in enumerate(neq_ns):
        case_id = f"c024_base_{idx + 16:02d}_neq"
        if idx < 5:
            # Differ by single edge toggle
            found = False
            for _ in range(50):
                g = random_connected_graph(n, edge_prob=0.35, rng=rng)
                gp = g.copy()
                u, v = rng.sample(range(n), 2)
                gp.adj[u][v] ^= 1
                gp.adj[v][u] ^= 1
                case_cand = {
                    "id": case_id,
                    "num_vertices": n,
                    "g": g.to_edge_list(),
                    "g_prime": gp.to_edge_list(),
                }
                sol = solve(case_cand)
                if sol["status"] == "SOLVED" and sol["equivalent"] is False:
                    base_cases.append(case_cand)
                    found = True
                    break
            assert found, f"Failed to generate single edge non-equiv for n={n}"
        else:
            # Distinct random graphs with cut-rank separation
            found = False
            for _ in range(50):
                g1 = random_connected_graph(n, edge_prob=0.25, rng=rng)
                g2 = random_connected_graph(n, edge_prob=0.45, rng=rng)
                case_cand = {
                    "id": case_id,
                    "num_vertices": n,
                    "g": g1.to_edge_list(),
                    "g_prime": g2.to_edge_list(),
                }
                sol = solve(case_cand)
                if sol["status"] == "SOLVED" and sol["equivalent"] is False:
                    base_cases.append(case_cand)
                    found = True
                    break
            assert found, f"Failed to generate distinct non-equiv for n={n}"

    assert len(base_cases) == 30

    # Write base cases
    for case in base_cases:
        p = base_dir / f"{case['id']}.json"
        p.write_text(json.dumps({"input": case}, indent=2, sort_keys=True), encoding="utf-8")

    # ---------------------------------------------------------
    # 2. Generate 10 Controls (permutation, LC gauge, swapped)
    # ---------------------------------------------------------
    control_cases: list[dict[str, Any]] = []

    # 5 Permutation controls (apply same pi to both G and G')
    for i in range(5):
        base = base_cases[i]
        n = base["num_vertices"]
        pi = list(range(n))
        rng.shuffle(pi)

        def permute_edges(edges: list[list[int]], perm: list[int]) -> list[list[int]]:
            new_edges = []
            for u, v in edges:
                pu, pv = perm[u], perm[v]
                new_edges.append([min(pu, pv), max(pu, pv)])
            return sorted(new_edges)

        ctrl = {
            "id": f"c024_ctrl_{i + 1:02d}_perm",
            "num_vertices": n,
            "g": permute_edges(base["g"], pi),
            "g_prime": permute_edges(base["g_prime"], pi),
        }
        control_cases.append(ctrl)

    # 3 LC Gauge controls (G replaced by G * u)
    for i in range(3):
        base = base_cases[5 + i]
        n = base["num_vertices"]
        u = rng.randint(0, n - 1)
        g_obj = SimpleGraph(n, base["g"]).local_complementation(u)
        ctrl = {
            "id": f"c024_ctrl_{i + 6:02d}_gauge",
            "num_vertices": n,
            "g": g_obj.to_edge_list(),
            "g_prime": base["g_prime"],
        }
        control_cases.append(ctrl)

    # 2 Swapped pair controls (g <-> g_prime)
    for i in range(2):
        base = base_cases[8 + i]
        ctrl = {
            "id": f"c024_ctrl_{i + 9:02d}_swap",
            "num_vertices": base["num_vertices"],
            "g": base["g_prime"],
            "g_prime": base["g"],
        }
        control_cases.append(ctrl)

    assert len(control_cases) == 10
    for case in control_cases:
        p = base_dir / f"{case['id']}.json"
        p.write_text(json.dumps({"input": case}, indent=2, sort_keys=True), encoding="utf-8")

    # ---------------------------------------------------------
    # 3. Generate 6 Poisoned Cases (Isomorphism traps, self-loops, out of bounds)
    # ---------------------------------------------------------
    poisoned_cases: list[dict[str, Any]] = []

    # Poison 1: Isomorphism trap on P4
    # P4 edges: 0-1-2-3. Permute to 0-2-1-3.
    # Are 0-1-2-3 and 0-2-1-3 LC-equivalent?
    # Let's verify:
    p4_a = [[0, 1], [1, 2], [2, 3]]
    p4_b = [[0, 2], [1, 2], [1, 3]]  # isomorphic path P4 with different labelling
    poison1 = {
        "id": "c024_poison_01_isomorphism_trap_p4",
        "num_vertices": 4,
        "g": p4_a,
        "g_prime": p4_b,
    }
    poisoned_cases.append(poison1)

    # Poison 2: Isomorphism trap on 5 vertices (cycle C5 with relabelled vertices)
    c5_a = [[0, 1], [1, 2], [2, 3], [3, 4], [0, 4]]
    # Relabelled cycle: 0-2-4-1-3-0
    c5_b = [[0, 2], [2, 4], [1, 4], [1, 3], [0, 3]]
    poison2 = {
        "id": "c024_poison_02_isomorphism_trap_c5",
        "num_vertices": 5,
        "g": c5_a,
        "g_prime": c5_b,
    }
    poisoned_cases.append(poison2)

    # Poison 3: Self-loop in G
    poison3 = {
        "id": "c024_poison_03_self_loop_g",
        "num_vertices": 4,
        "g": [[0, 1], [1, 1], [2, 3]],
        "g_prime": [[0, 1], [1, 2], [2, 3]],
    }
    poisoned_cases.append(poison3)

    # Poison 4: Self-loop in G'
    poison4 = {
        "id": "c024_poison_04_self_loop_gp",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [2, 2], [2, 3]],
    }
    poisoned_cases.append(poison4)

    # Poison 5: Vertex out of bounds in G
    poison5 = {
        "id": "c024_poison_05_vertex_out_of_bounds",
        "num_vertices": 4,
        "g": [[0, 1], [1, 4]],  # vertex 4 on 4-vertex graph
        "g_prime": [[0, 1], [1, 2]],
    }
    poisoned_cases.append(poison5)

    # Poison 6: num_vertices out of bounds (n = 17)
    poison6 = {
        "id": "c024_poison_06_num_vertices_out_of_bounds",
        "num_vertices": 17,
        "g": [[0, 1]],
        "g_prime": [[0, 1]],
    }
    poisoned_cases.append(poison6)

    assert len(poisoned_cases) == 6
    for case in poisoned_cases:
        p = base_dir / f"{case['id']}.json"
        p.write_text(json.dumps({"input": case}, indent=2, sort_keys=True), encoding="utf-8")

    # ---------------------------------------------------------
    # 4. Generate 10 Public Examples
    # ---------------------------------------------------------
    # 1: Identity / Equal graphs
    ex01 = {
        "id": "c024_ex01_identical",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2], [2, 3]],
        "g_prime": [[0, 1], [1, 2], [2, 3]],
    }
    # 2: P4 and complementation at vertex 1
    p4_g = SimpleGraph(4, [[0, 1], [1, 2], [2, 3]])
    ex02 = {
        "id": "c024_ex02_p4_comp_1",
        "num_vertices": 4,
        "g": p4_g.to_edge_list(),
        "g_prime": p4_g.local_complementation(1).to_edge_list(),
    }
    # 3: Star S5 and Complete K5 (center vertex 0: star has edges [0, 1], [0, 2], [0, 3], [0, 4])
    # K5 has all 10 pairs. S5 * 0 complements N(0) = {1, 2, 3, 4}, adding all edges between them!
    s5_edges = [[0, 1], [0, 2], [0, 3], [0, 4]]
    s5_g = SimpleGraph(5, s5_edges)
    k5_g = s5_g.local_complementation(0)
    ex03 = {
        "id": "c024_ex03_star_complete_ghz",
        "num_vertices": 5,
        "g": s5_edges,
        "g_prime": k5_g.to_edge_list(),
    }
    # 4: Triangle with tail (n=4)
    tri_g = SimpleGraph(4, [[0, 1], [1, 2], [0, 2], [2, 3]])
    ex04 = {
        "id": "c024_ex04_paw_graph",
        "num_vertices": 4,
        "g": tri_g.to_edge_list(),
        "g_prime": tri_g.local_complementation(2).to_edge_list(),
    }
    # 5: Random 6-qubit equivalent
    g6 = random_connected_graph(6, 0.4, rng=random.Random(111))
    g6_prime = g6.local_complementation(2).local_complementation(4)
    ex05 = {
        "id": "c024_ex05_random_6q_equiv",
        "num_vertices": 6,
        "g": g6.to_edge_list(),
        "g_prime": g6_prime.to_edge_list(),
    }
    # 6: Cut-rank separated pair (isolated vertex vs edge)
    ex06 = {
        "id": "c024_ex06_cut_rank_separated",
        "num_vertices": 4,
        "g": [[0, 1], [1, 2]],
        "g_prime": [[0, 1]],
    }
    # 7: Single edge difference non-equivalent
    ex07 = base_cases[15]  # first single-edge non-equiv
    ex07_copy = dict(ex07)
    ex07_copy["id"] = "c024_ex07_single_edge_neq"

    # 8: Isomorphism trap non-equivalent
    ex08 = dict(poison1)
    ex08["id"] = "c024_ex08_isomorphism_trap"

    # 9: Self-loop malformed
    ex09 = dict(poison3)
    ex09["id"] = "c024_ex09_self_loop"

    # 10: Out of bounds
    ex10 = dict(poison6)
    ex10["id"] = "c024_ex10_out_of_bounds"

    examples = [ex01, ex02, ex03, ex04, ex05, ex06, ex07_copy, ex08, ex09, ex10]
    for ex in examples:
        p = examples_dir / f"{ex['id']}.json"
        p.write_text(json.dumps(ex, indent=2, sort_keys=True), encoding="utf-8")

    print(
        f"Generated {len(base_cases)} base cases, {len(control_cases)} controls, {len(poisoned_cases)} poisoned cases."
    )
    print(f"Generated {len(examples)} public examples.")


if __name__ == "__main__":
    generate_all_cases()
