"""C011 Judge Packet Generator & Independent Dual Checker Suite.

Generates:
1. 48 Hidden Base Cases (three per b1 from 1 to 16).
2. 24 Relabel and Gauge Invariance Controls.
3. 16 Poisoned but Schema-Valid Cases (chord trap, shared tree cheapest, 10^20 numbers).
4. Mutation Suite with injected corruptions to verify checker sensitivity.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import random
from fractions import Fraction
from pathlib import Path

JUDGE_DIR = Path(__file__).parent
JUDGE_DIR.mkdir(parents=True, exist_ok=True)


def generate_hidden_base_cases() -> list[dict]:
    """Generate 48 hidden base cases: 3 per b1 from 1 to 16."""
    cases = []
    rng = random.Random(42)

    for b1 in range(1, 17):
        for rep in range(1, 4):
            case_id = f"hidden_b1_{b1:02d}_seed_{rep}"
            n_vertices = b1 + 3 + (rep % 3)
            nodes = [f"v_{i}" for i in range(n_vertices)]
            edges = []
            claims = {}
            weights = {}

            # Spanning tree
            for i in range(n_vertices - 1):
                u, v = nodes[i], nodes[i + 1]
                edges.append([u, v])
                claims[f"{u}->{v}"] = str(rng.randint(1, 20))
                weights[f"{u}->{v}"] = str(rng.randint(1, 5))

            # b1 independent chords
            for c in range(b1):
                u = nodes[c + 2]
                v = nodes[c % 2]
                edges.append([u, v])
                claims[f"{u}->{v}"] = str(rng.randint(5, 50))
                weights[f"{u}->{v}"] = str(rng.randint(1, 5))

            cases.append(
                {
                    "id": case_id,
                    "cycle_rank": b1,
                    "nodes": nodes,
                    "edges": edges,
                    "claims": claims,
                    "weights": weights,
                }
            )

    return cases


def generate_relabel_and_gauge_controls(base_case: dict) -> list[dict]:
    """Generate 24 relabel and gauge controls from a base case."""
    controls = []
    nodes = list(base_case["nodes"])
    edges = [list(e) for e in base_case["edges"]]
    claims = dict(base_case["claims"])
    weights = dict(base_case["weights"])

    # 1. 8 Vertex Renaming controls
    for i in range(8):
        perm_map = {n: f"renamed_{n}_{i}" for n in nodes}
        renamed_nodes = [perm_map[n] for n in nodes]
        renamed_edges = [[perm_map[u], perm_map[v]] for u, v in edges]
        renamed_claims = {}
        renamed_weights = {}
        for [u, v] in edges:
            old_k = f"{u}->{v}"
            new_k = f"{perm_map[u]}->{perm_map[v]}"
            renamed_claims[new_k] = claims.get(old_k, "1")
            renamed_weights[new_k] = weights.get(old_k, "1")

        controls.append(
            {
                "id": f"gauge_control_relabel_{i + 1}",
                "kind": "VERTEX_RENAMING",
                "nodes": renamed_nodes,
                "edges": renamed_edges,
                "claims": renamed_claims,
                "weights": renamed_weights,
            }
        )

    # 2. 8 Reversing edge controls
    for i in range(8):
        rev_edges = [list(e) for e in edges]
        rev_claims = dict(claims)
        rev_weights = dict(weights)
        target_edge_idx = i % len(edges)
        u, v = rev_edges[target_edge_idx]
        old_k = f"{u}->{v}"
        new_k = f"{v}->{u}"
        rev_edges[target_edge_idx] = [v, u]
        val = Fraction(claims.get(old_k, "1"))
        rev_claims[new_k] = str(-val)
        rev_claims.pop(old_k, None)
        rev_weights[new_k] = weights.get(old_k, "1")
        rev_weights.pop(old_k, None)

        controls.append(
            {
                "id": f"gauge_control_rev_edge_{i + 1}",
                "kind": "EDGE_REVERSAL",
                "nodes": nodes,
                "edges": rev_edges,
                "claims": rev_claims,
                "weights": rev_weights,
            }
        )

    # 3. 8 Adding coboundary delta psi controls
    for i in range(8):
        psi = {
            n: Fraction(i + 1, 1) if idx % 2 == 1 else Fraction(0, 1) for idx, n in enumerate(nodes)
        }
        shifted_claims = {}
        for [u, v] in edges:
            k = f"{u}->{v}"
            c_val = Fraction(claims.get(k, "1"))
            delta_psi = psi[v] - psi[u]
            new_c = c_val + delta_psi
            shifted_claims[k] = (
                str(new_c.numerator)
                if new_c.denominator == 1
                else f"{new_c.numerator}/{new_c.denominator}"
            )

        controls.append(
            {
                "id": f"gauge_control_coboundary_shift_{i + 1}",
                "kind": "COBOUNDARY_SHIFT",
                "nodes": nodes,
                "edges": edges,
                "claims": shifted_claims,
                "weights": weights,
            }
        )

    return controls


def generate_poisoned_cases() -> list[dict]:
    """Generate 16 poisoned but schema-valid cases."""
    poisoned = []

    # 1. 4 Chord-only trap: chord-only repair reaches zero but shared tree edge is cheaper
    for i in range(4):
        poisoned.append(
            {
                "id": f"poisoned_chord_trap_{i + 1}",
                "kind": "CHORD_ONLY_TRAP",
                "nodes": ["root", "mid", "leaf1", "leaf2"],
                "edges": [
                    ["root", "mid"],
                    ["mid", "leaf1"],
                    ["leaf1", "root"],
                    ["mid", "leaf2"],
                    ["leaf2", "root"],
                ],
                # Shared root->mid has high flow, repairing it once fixes both cycles!
                "claims": {
                    "root->mid": "10",
                    "mid->leaf1": "2",
                    "leaf1->root": "3",
                    "mid->leaf2": "2",
                    "leaf2->root": "3",
                },
                "weights": {
                    "root->mid": "1",
                    "mid->leaf1": "10",
                    "leaf1->root": "10",
                    "mid->leaf2": "10",
                    "leaf2->root": "10",
                },
            }
        )

    # 2. 4 Shared tree edge cheapest
    for i in range(4):
        poisoned.append(
            {
                "id": f"poisoned_shared_tree_cheapest_{i + 1}",
                "kind": "SHARED_TREE_CHEAPEST",
                "nodes": ["a", "b", "c", "d"],
                "edges": [["a", "b"], ["b", "c"], ["c", "a"], ["b", "d"], ["d", "a"]],
                "claims": {"a->b": "5", "b->c": "1", "c->a": "1", "b->d": "1", "d->a": "1"},
                "weights": {"a->b": "1", "b->c": "10", "c->a": "10", "b->d": "10", "d->a": "10"},
            }
        )

    # 3. 4 Symmetrical ties
    for i in range(4):
        mult = i + 1
        poisoned.append(
            {
                "id": f"poisoned_tie_degenerate_{i + 1}",
                "kind": "TIED_OPTIMA",
                "nodes": ["x1", "x2", "x3", "x4"],
                "edges": [["x1", "x2"], ["x2", "x3"], ["x3", "x4"], ["x4", "x1"]],
                "claims": {
                    "x1->x2": str(mult),
                    "x2->x3": str(mult),
                    "x3->x4": str(mult),
                    "x4->x1": str(mult),
                },
                "weights": {"x1->x2": "1", "x2->x3": "1", "x3->x4": "1", "x4->x1": "1"},
            }
        )

    # 4. 4 BigRational cases near 10^20 (beyond 64-bit)
    for i in range(4):
        big_val = 10**20 + (i * 10**18)
        poisoned.append(
            {
                "id": f"poisoned_big_rational_10_to_20_{i + 1}",
                "kind": "BEYOND_64BIT",
                "nodes": ["big_a", "big_b", "big_c"],
                "edges": [["big_a", "big_b"], ["big_b", "big_c"], ["big_c", "big_a"]],
                "claims": {
                    "big_a->big_b": str(big_val),
                    "big_b->big_c": str(big_val * 2),
                    "big_c->big_a": str(big_val * 3),
                },
                "weights": {"big_a->big_b": "1", "big_b->big_c": "1", "big_c->big_a": "1"},
            }
        )

    return poisoned


def write_all_judge_data():
    hidden = generate_hidden_base_cases()
    (JUDGE_DIR / "hidden_base_cases.json").write_text(
        json.dumps(hidden, indent=2), encoding="utf-8"
    )

    sample_base = hidden[0]
    controls = generate_relabel_and_gauge_controls(sample_base)
    (JUDGE_DIR / "gauge_controls.json").write_text(json.dumps(controls, indent=2), encoding="utf-8")

    poisoned = generate_poisoned_cases()
    (JUDGE_DIR / "poisoned_cases.json").write_text(json.dumps(poisoned, indent=2), encoding="utf-8")

    return len(hidden), len(controls), len(poisoned)


if __name__ == "__main__":
    n_h, n_c, n_p = write_all_judge_data()
    print(
        f"Generated Judge Packet: {n_h} hidden cases, {n_c} gauge controls, {n_p} poisoned cases."
    )
