"""
cases.py — Public example cases, hidden base cases, and relabel controls for Challenge C005.

Generates:
- 30 public example cases (15 consistency, 15 cycle repair)
- 100 hidden base cases (50 consistency, 50 cycle repair)
- 20 relabel controls (cycle rotations and vertex renamings)

AuthorityEffect: None.
"""

from __future__ import annotations

import random
from typing import Any


def generate_consistency_case(
    case_id: str, num_nodes: int = 5, is_consistent: bool = True, seed: int = 42
) -> dict[str, Any]:
    rng = random.Random(seed)
    nodes = [f"n{i}" for i in range(num_nodes)]

    # Ground truth potentials
    potentials = {node: rng.randint(-10, 10) for node in nodes}
    potentials[nodes[0]] = 0  # Gauge fixing

    edges: list[tuple[str, str, int]] = []
    # Spanning tree
    for i in range(num_nodes - 1):
        u, v = nodes[i], nodes[i + 1]
        delta = potentials[v] - potentials[u]
        edges.append((u, v, delta))

    # Additional chords
    defect_planted = False
    for _ in range(num_nodes // 2):
        u = rng.choice(nodes)
        v = rng.choice(nodes)
        if u != v and not any(e[0] == u and e[1] == v for e in edges):
            delta = potentials[v] - potentials[u]
            if not is_consistent and not defect_planted:
                delta += rng.choice([-3, -2, -1, 1, 2, 3])  # Plant defect
                defect_planted = True
            edges.append((u, v, delta))

    # If is_consistent is False but no chord was added, add at least one chord with defect
    if not is_consistent and not defect_planted:
        u, v = nodes[0], nodes[-1]
        delta = potentials[v] - potentials[u] + rng.choice([-3, -2, -1, 1, 2, 3])
        edges.append((u, v, delta))

    verdict = "CONSISTENT" if is_consistent else "INCONSISTENT"
    cert = {k: str(v) for k, v in potentials.items()} if is_consistent else {}

    prompt = (
        "Determine if the system of differences is CONSISTENT or INCONSISTENT. "
        "Relations: " + ", ".join(f"{u} -> {v} = {d}" for u, v, d in edges)
    )

    return {
        "case_id": case_id,
        "kind": "consistency",
        "prompt": prompt,
        "edges": edges,
        "expected_verdict": verdict,
        "expected_certificate": cert,
    }


def generate_cycle_repair_case(case_id: str, k: int = 3, seed: int = 42) -> dict[str, Any]:
    rng = random.Random(seed)
    nodes = [str(i) for i in range(k)]
    weights = [rng.choice([1, 2, 3]) for _ in range(k)]

    # Choose non-zero cycle sum s
    s = rng.choice([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5])

    # Generate claims summing to s
    claims = [rng.randint(-10, 10) for _ in range(k - 1)]
    claims.append(s - sum(claims))

    edges = [(nodes[i], nodes[(i + 1) % k], claims[i]) for i in range(k)]

    # Compute optimal repair: adjust the edge with minimum weight
    min_w = min(weights)
    min_idx = weights.index(min_w)
    optimal_cost = abs(s) * min_w

    repaired = list(claims)
    repaired[min_idx] -= s  # subtract sum so new sum = 0

    prompt = (
        f"Repair the cycle of length {k} to zero sum with minimum weighted L1 cost. "
        f"Claims: {claims}, Weights: {weights}."
    )

    return {
        "case_id": case_id,
        "kind": "cycle_repair",
        "prompt": prompt,
        "edges": edges,
        "weights": weights,
        "optimal_cost": optimal_cost,
        "expected_repaired": [str(c) for c in repaired],
        "expected_weighted_l1": str(optimal_cost),
    }


def get_public_examples() -> list[dict[str, Any]]:
    """Generate 30 public examples (15 consistency, 15 cycle repair)."""
    cases: list[dict[str, Any]] = []
    for i in range(15):
        cases.append(
            generate_consistency_case(
                f"pub_cons_{i + 1:02d}",
                num_nodes=4 + (i % 3),
                is_consistent=(i % 2 == 0),
                seed=100 + i,
            )
        )
    for i in range(15):
        cases.append(
            generate_cycle_repair_case(f"pub_repair_{i + 1:02d}", k=3 + (i % 4), seed=200 + i)
        )
    return cases


def get_hidden_base_cases() -> list[dict[str, Any]]:
    """Generate 100 hidden base cases (50 consistency, 50 cycle repair)."""
    cases: list[dict[str, Any]] = []
    for i in range(50):
        cases.append(
            generate_consistency_case(
                f"hidden_cons_{i + 1:02d}",
                num_nodes=4 + (i % 6),
                is_consistent=(i % 2 == 0),
                seed=1000 + i,
            )
        )
    for i in range(50):
        cases.append(
            generate_cycle_repair_case(f"hidden_repair_{i + 1:02d}", k=3 + (i % 4), seed=2000 + i)
        )
    return cases


def get_relabel_controls() -> list[dict[str, Any]]:
    """Generate 20 relabel controls (vertex renamings and cycle rotations)."""
    cases: list[dict[str, Any]] = []
    # 10 cycle rotations
    for i in range(10):
        base = generate_cycle_repair_case(f"relabel_rot_{i + 1:02d}", k=4, seed=3000 + i)
        # Rotate edges and weights by 1
        edges = base["edges"][1:] + base["edges"][:1]
        weights = base["weights"][1:] + base["weights"][:1]
        expected_rep = base["expected_repaired"][1:] + base["expected_repaired"][:1]
        cases.append(
            {
                "case_id": f"relabel_rot_{i + 1:02d}",
                "kind": "cycle_repair",
                "prompt": f"Rotated cycle: Claims {[e[2] for e in edges]}, Weights {weights}",
                "edges": edges,
                "weights": weights,
                "optimal_cost": base["optimal_cost"],
                "expected_repaired": expected_rep,
                "expected_weighted_l1": base["expected_weighted_l1"],
            }
        )
    # 10 node renamings for consistency
    renaming_map = {"n0": "alpha", "n1": "beta", "n2": "gamma", "n3": "delta", "n4": "epsilon"}
    for i in range(10):
        base = generate_consistency_case(
            f"relabel_name_{i + 1:02d}", num_nodes=4, is_consistent=True, seed=4000 + i
        )
        renamed_edges = [
            (renaming_map.get(u, u), renaming_map.get(v, v), d) for u, v, d in base["edges"]
        ]
        renamed_cert = {renaming_map.get(k, k): v for k, v in base["expected_certificate"].items()}
        cases.append(
            {
                "case_id": f"relabel_name_{i + 1:02d}",
                "kind": "consistency",
                "prompt": "Renamed system: "
                + ", ".join(f"{u} -> {v} = {d}" for u, v, d in renamed_edges),
                "edges": renamed_edges,
                "expected_verdict": "CONSISTENT",
                "expected_certificate": renamed_cert,
            }
        )
    return cases
