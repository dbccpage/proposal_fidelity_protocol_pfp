"""
tasks.py — generator for carrier-expressible consistency instances.

Each instance declares integer "rank difference" relations `r(v) - r(u) = d` over a
finite carrier of items. A *clean* instance is built from a real hidden potential
(so a global assignment exists — CONSISTENT). A *poisoned* instance injects one
contradictory relation on a cycle (so no assignment exists — CONTRADICTION). Ground
truth is fixed by construction and verified with the exact host, re-perturbing if a
perturbation happened to land on a bridge (which stays consistent).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .host import host_verdict


@dataclass
class Instance:
    items: List[str]
    edges: List[Tuple[str, str, int]]          # (u, v, weight)
    claims: Dict[Tuple[str, str], int]         # declared r(v) - r(u)
    poisoned: bool
    ground_truth: str                          # "CONSISTENT" | "CONTRADICTION"
    seed: int


def generate_instance(n_items: int = 8, n_relations: int = 14, poisoned: bool = False,
                      seed: int = 0) -> Instance:
    if n_items < 1:
        raise ValueError("n_items must be positive")
    if not 0 <= n_relations <= n_items * (n_items - 1) // 2:
        raise ValueError("n_relations must fit the number of distinct item pairs")
    if poisoned and (n_items < 3 or n_relations < 3):
        raise ValueError("a poisoned instance needs at least three items and relations")
    rng = random.Random(seed)
    items = [chr(ord("A") + i % 26) + (str(i // 26) if i >= 26 else "")
             for i in range(n_items)]
    ranks = {it: rng.randint(0, 4 * n_items) for it in items}   # a real potential

    edges: List[Tuple[str, str, int]] = []
    claims: Dict[Tuple[str, str], int] = {}
    seen = set()
    while len(edges) < n_relations:
        u, v = rng.sample(items, 2)
        if (u, v) in seen or (v, u) in seen:
            continue
        seen.add((u, v))
        w = rng.choice([1, 1, 1, 2])
        edges.append((u, v, w))
        claims[(u, v)] = ranks[v] - ranks[u]                     # consistent by construction

    inst = Instance(items, edges, claims, False, "CONSISTENT", seed)
    if not poisoned:
        return inst

    # Inject exactly one contradiction on a cycle; verify with the exact host and retry
    # if we happened to perturb a bridge (which no cycle detects).
    order = list(range(len(edges)))
    rng.shuffle(order)
    for idx in order:
        for delta in (2, 3, -2, -3, 4, -4):
            trial = dict(claims)
            u, v, _w = edges[idx]
            trial[(u, v)] = claims[(u, v)] + delta
            cand = Instance(items, edges, trial, True, "CONTRADICTION", seed)
            if host_verdict(cand) == "CONTRADICTION":
                return cand
    raise ValueError(
        f"seed {seed} produced a forest; cannot plant a contradiction. "
        "Use n_relations >= n_items to ensure a cycle."
    )


def generate_batch(n_instances: int, n_items: int = 8, n_relations: int = 14,
                   base_seed: int = 0) -> List[Instance]:
    """Half clean, half poisoned, deterministic by seed."""
    if n_instances < 1:
        raise ValueError("n_instances must be positive")
    out: List[Instance] = []
    for i in range(n_instances):
        out.append(generate_instance(n_items, n_relations, poisoned=(i % 2 == 1),
                                      seed=base_seed + i))
    return out
