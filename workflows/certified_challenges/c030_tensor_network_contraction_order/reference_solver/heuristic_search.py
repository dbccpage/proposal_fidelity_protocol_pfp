# AuthorityEffect: None.
"""
Heuristic and Stochastic Search for Tensor Network Contraction Order (C030).

Implements:
1. Multi-strategy greedy planners:
   - MinCost: minimizes immediate contraction step cost.
   - MinSize: minimizes intermediate tensor size.
   - MaxBond: prioritizes contracting edges with largest dimension.
   - Connectedness-first: defers outer products until components are contracted.
2. Randomized priority beam / multi-start search:
   - Explores diverse greedy trajectories with soft-softmax / randomized top-k selection.
3. Size-bound filtering:
   - Discards intermediate contractions exceeding size_bound S.
"""

from __future__ import annotations

import random
from typing import Dict, List, Optional, Set, Tuple

from .tensor_network import compute_step_cost_and_size


def _greedy_pass(
    tensors: Dict[str, List[str]],
    dims: Dict[str, int],
    cost_bound: Optional[int] = None,
    size_bound: Optional[int] = None,
    strategy: str = "min_cost",
    random_seed: Optional[int] = None,
    randomness: float = 0.0,
) -> Tuple[bool, int, int, List[List[str]]]:
    """
    Executes a single greedy contraction pass.
    Returns:
        (meets_bounds, total_cost, max_size, order)
    """
    rng = random.Random(random_seed)

    live: Dict[str, Set[str]] = {name: set(idxs) for name, idxs in tensors.items()}
    order: List[List[str]] = []
    total_cost = 0
    max_size = 0

    while len(live) > 1:
        names = list(live.keys())
        candidates: List[Tuple[float, int, int, str, str, Set[str]]] = []

        # Find candidate pairs
        for i in range(len(names)):
            t1 = names[i]
            idx1 = live[t1]
            for j in range(i + 1, len(names)):
                t2 = names[j]
                idx2 = live[t2]

                shared = idx1 & idx2
                step_cost, step_size, new_idx = compute_step_cost_and_size(idx1, idx2, dims)

                # Skip if size bound is exceeded
                if size_bound is not None and step_size > size_bound and len(live) > 2:
                    continue

                # Preference score (lower is better)
                shared_dim = 1
                for e in shared:
                    shared_dim *= dims[e]

                is_outer = 1 if len(shared) == 0 else 0

                if strategy == "min_cost":
                    # Heavy penalty for outer products while connected pairs exist
                    score = step_cost * (1000 if is_outer else 1)
                elif strategy == "min_size":
                    score = step_size * (1000 if is_outer else 1)
                elif strategy == "max_bond":
                    # Lower score for higher shared bond
                    score = step_cost / max(shared_dim, 1)
                else:
                    score = float(step_cost)

                candidates.append((score, step_cost, step_size, t1, t2, new_idx))

        if not candidates:
            # Fallback: if all candidate contractions exceed size_bound, pick min size
            for i in range(len(names)):
                t1 = names[i]
                idx1 = live[t1]
                for j in range(i + 1, len(names)):
                    t2 = names[j]
                    idx2 = live[t2]
                    step_cost, step_size, new_idx = compute_step_cost_and_size(idx1, idx2, dims)
                    candidates.append((float(step_size), step_cost, step_size, t1, t2, new_idx))

        # Sort candidates by score
        candidates.sort(key=lambda x: x[0])

        # Pick best or sample from top candidates if randomness > 0
        if randomness > 0 and len(candidates) > 1:
            pool_sz = min(len(candidates), 3)
            chosen = rng.choice(candidates[:pool_sz])
        else:
            chosen = candidates[0]

        _, step_cost, step_size, t1, t2, new_idx = chosen
        total_cost += step_cost
        if step_size > max_size:
            max_size = step_size

        step_id = len(order)
        order.append([t1, t2])
        del live[t1]
        del live[t2]
        live[f"@step:{step_id}"] = new_idx

    meets_cost = cost_bound is None or total_cost <= cost_bound
    meets_size = size_bound is None or max_size <= size_bound
    return (meets_cost and meets_size), total_cost, max_size, order


def solve_heuristic_search(
    tensors: Dict[str, List[str]],
    dims: Dict[str, int],
    cost_bound: Optional[int] = None,
    size_bound: Optional[int] = None,
    num_restarts: int = 50,
) -> Tuple[bool, int, List[List[str]]]:
    """
    Searches for a contraction order satisfying cost_bound and size_bound.
    Returns:
        (meets_bounds, best_cost, best_order)
    """
    best_cost = float("inf")
    best_order: List[List[str]] = []
    found_valid = False

    # 1. Deterministic baseline passes across strategies
    strategies = ["min_cost", "min_size", "max_bond"]
    for strat in strategies:
        meets, cost, sz, order = _greedy_pass(
            tensors,
            dims,
            cost_bound=cost_bound,
            size_bound=size_bound,
            strategy=strat,
            randomness=0.0,
        )
        if cost < best_cost:
            best_cost = cost
            best_order = order
        if meets:
            found_valid = True
            if cost_bound is not None and cost <= cost_bound:
                return True, int(cost), order

    # 2. Randomized multi-start passes
    for i in range(num_restarts):
        strat = strategies[i % len(strategies)]
        meets, cost, sz, order = _greedy_pass(
            tensors,
            dims,
            cost_bound=cost_bound,
            size_bound=size_bound,
            strategy=strat,
            random_seed=i + 42,
            randomness=0.5,
        )
        if cost < best_cost:
            best_cost = cost
            best_order = order
        if meets:
            found_valid = True
            if cost_bound is not None and cost <= cost_bound:
                return True, int(cost), order

    return found_valid, int(best_cost), best_order
