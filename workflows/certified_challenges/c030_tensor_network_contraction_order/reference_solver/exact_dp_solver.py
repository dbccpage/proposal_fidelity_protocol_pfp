# AuthorityEffect: None.
"""
Exact Dynamic Programming Contraction Order Solver for C030.

Computes the provably optimal contraction order for networks with at most 12 tensors
using subset dynamic programming over the 2^N subsets and 3^N submask splits.
Arithmetic is in exact arbitrary-precision integers (Python int).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Set, Tuple


def solve_exact_subset_dp(
    tensors: Dict[str, List[str]],
    dims: Dict[str, int],
    size_bound: Optional[int] = None,
) -> Tuple[bool, int, List[List[str]]]:
    """
    Computes exact minimum-cost contraction tree using subset DP.
    Returns:
        (is_feasible, optimal_cost, optimal_order)
    """
    tensor_names = sorted(list(tensors.keys()))
    n = len(tensor_names)
    if n <= 1:
        return True, 0, []

    # Map name -> bitmask
    {name: i for i, name in enumerate(tensor_names)}
    idx_to_name = {i: name for i, name in enumerate(tensor_names)}

    # Precompute indices and sizes for each subset mask
    mask_indices: List[Set[str]] = [set() for _ in range(1 << n)]
    mask_sizes: List[int] = [1 for _ in range(1 << n)]

    for mask in range(1, 1 << n):
        # Sym diff of all tensors in mask
        idxs: Set[str] = set()
        for i in range(n):
            if (mask >> i) & 1:
                idxs ^= set(tensors[idx_to_name[i]])
        mask_indices[mask] = idxs

        sz = 1
        for idx in idxs:
            sz *= dims[idx]
        mask_sizes[mask] = sz

    # dp_cost[mask] = (min_cost, best_left_submask)
    dp_cost: Dict[int, Tuple[int, int]] = {}

    # Base cases: single tensors have 0 contraction cost
    for i in range(n):
        dp_cost[1 << i] = (0, 0)

    # Fill DP table by subset size
    for sz in range(2, n + 1):
        for mask in range(1, 1 << n):
            if bin(mask).count("1") != sz:
                continue

            # If intermediate size bound is exceeded (for proper subsets), skip
            if size_bound is not None and sz < n:
                if mask_sizes[mask] > size_bound:
                    continue

            best_cost = float("inf")
            best_sub = 0

            # Fix least significant bit in submask to eliminate symmetric duplicate splits
            lowest_bit = mask & -mask
            sub = (mask - 1) & mask
            while sub > 0:
                if sub & lowest_bit:
                    other = mask ^ sub
                    if sub in dp_cost and other in dp_cost:
                        c1 = dp_cost[sub][0]
                        c2 = dp_cost[other][0]
                        if c1 != float("inf") and c2 != float("inf"):
                            # Step cost = prod_{e in I(sub) union I(other)} dim(e)
                            union_idx = mask_indices[sub] | mask_indices[other]
                            step_cost = 1
                            for idx in union_idx:
                                step_cost *= dims[idx]

                            total = c1 + c2 + step_cost
                            if total < best_cost:
                                best_cost = total
                                best_sub = sub
                sub = (sub - 1) & mask

            if best_cost != float("inf"):
                dp_cost[mask] = (int(best_cost), best_sub)

    full_mask = (1 << n) - 1
    if full_mask not in dp_cost:
        return False, 0, []

    optimal_cost, _ = dp_cost[full_mask]

    # Reconstruct contraction order
    next_step_id = 0

    def reconstruct(mask: int) -> Tuple[str, List[List[str]]]:
        nonlocal next_step_id
        if bin(mask).count("1") == 1:
            i = (mask).bit_length() - 1
            return idx_to_name[i], []

        _, sub = dp_cost[mask]
        other = mask ^ sub
        name1, steps1 = reconstruct(sub)
        name2, steps2 = reconstruct(other)

        step = [name1, name2]
        output_name = f"@step:{next_step_id}"
        next_step_id += 1
        return output_name, steps1 + steps2 + [step]

    _, optimal_order = reconstruct(full_mask)
    return True, optimal_cost, optimal_order
