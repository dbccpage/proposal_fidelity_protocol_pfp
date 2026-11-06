"""
Sorting Network Synthesis & 0-1 Principle Verification Engine.

Provides exact bit-parallel 0-1 principle evaluation, known optimal sorting
networks for n in [4, 12], Batcher's odd-even merge networks, greedy repair,
redundancy pruning, and guided beam search.
"""

from typing import Dict, List, Optional, Set, Tuple

KNOWN_OPTIMAL: Dict[int, List[Tuple[int, int]]] = {
    4: [(0, 2), (1, 3), (0, 1), (2, 3), (1, 2)],
    5: [(0, 3), (1, 4), (0, 2), (1, 3), (0, 1), (2, 4), (1, 2), (3, 4), (2, 3)],
    6: [
        (0, 5),
        (1, 3),
        (2, 4),
        (1, 2),
        (3, 4),
        (0, 3),
        (2, 5),
        (0, 1),
        (2, 3),
        (4, 5),
        (1, 2),
        (3, 4),
    ],
    7: [
        (0, 6),
        (2, 3),
        (4, 5),
        (0, 2),
        (1, 4),
        (3, 6),
        (0, 1),
        (2, 5),
        (3, 4),
        (1, 2),
        (4, 6),
        (2, 3),
        (4, 5),
        (1, 2),
        (3, 4),
        (5, 6),
    ],
    8: [
        (0, 2),
        (1, 3),
        (4, 6),
        (5, 7),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
        (0, 1),
        (2, 3),
        (4, 5),
        (6, 7),
        (2, 4),
        (3, 5),
        (1, 4),
        (3, 6),
        (1, 2),
        (3, 4),
        (5, 6),
    ],
    9: [
        (0, 3),
        (1, 7),
        (2, 5),
        (4, 8),
        (0, 7),
        (2, 4),
        (3, 8),
        (5, 6),
        (0, 2),
        (1, 3),
        (4, 5),
        (7, 8),
        (1, 4),
        (3, 6),
        (5, 7),
        (0, 1),
        (2, 4),
        (3, 5),
        (6, 8),
        (2, 3),
        (4, 5),
        (6, 7),
        (1, 2),
        (3, 4),
        (5, 6),
    ],
    10: [
        (0, 8),
        (1, 9),
        (2, 7),
        (3, 5),
        (4, 6),
        (0, 2),
        (1, 4),
        (5, 8),
        (7, 9),
        (0, 3),
        (2, 4),
        (5, 7),
        (6, 9),
        (0, 1),
        (3, 6),
        (8, 9),
        (1, 5),
        (2, 3),
        (4, 8),
        (6, 7),
        (1, 2),
        (3, 5),
        (4, 6),
        (7, 8),
        (2, 3),
        (4, 5),
        (6, 7),
        (3, 4),
        (5, 6),
    ],
    11: [
        (0, 9),
        (1, 6),
        (2, 4),
        (3, 7),
        (5, 8),
        (0, 1),
        (3, 5),
        (4, 10),
        (6, 9),
        (7, 8),
        (1, 3),
        (2, 5),
        (4, 7),
        (8, 10),
        (0, 4),
        (1, 2),
        (3, 7),
        (5, 9),
        (6, 8),
        (0, 1),
        (2, 6),
        (4, 5),
        (7, 8),
        (9, 10),
        (2, 4),
        (3, 6),
        (5, 7),
        (8, 9),
        (1, 2),
        (3, 4),
        (5, 6),
        (7, 8),
        (2, 3),
        (4, 5),
        (6, 7),
    ],
    12: [
        (0, 8),
        (1, 7),
        (2, 6),
        (3, 11),
        (4, 10),
        (5, 9),
        (0, 1),
        (2, 5),
        (3, 4),
        (6, 9),
        (7, 8),
        (10, 11),
        (0, 2),
        (1, 6),
        (5, 10),
        (9, 11),
        (0, 3),
        (1, 2),
        (4, 6),
        (5, 7),
        (8, 11),
        (9, 10),
        (1, 4),
        (3, 5),
        (6, 8),
        (7, 10),
        (1, 3),
        (2, 5),
        (6, 9),
        (8, 10),
        (2, 3),
        (4, 5),
        (6, 7),
        (8, 9),
        (4, 6),
        (5, 7),
        (3, 4),
        (5, 6),
        (7, 8),
    ],
}

INFO_THEORETIC_LOWER_BOUND: Dict[int, int] = {
    4: 5,
    5: 7,
    6: 10,
    7: 13,
    8: 16,
    9: 19,
    10: 22,
    11: 26,
    12: 29,
}

PROVEN_OPTIMAL_SIZE: Dict[int, int] = {
    4: 5,
    5: 9,
    6: 12,
    7: 16,
    8: 19,
    9: 25,
    10: 29,
    11: 35,
    12: 39,
}


def build_initial_state(n: int) -> List[int]:
    """Construct bit-parallel representation of all 2^n binary inputs."""
    num_cases = 1 << n
    w = [0] * n
    for c in range(n):
        val = 0
        for m in range(num_cases):
            if (m >> c) & 1:
                val |= 1 << m
        w[c] = val
    return w


def verify_01(n: int, network: List[Tuple[int, int]]) -> Tuple[bool, Optional[int]]:
    """
    Verify network using the 0-1 principle via bit-parallel simulation.
    Returns (True, None) if network sorts all 2^n inputs,
    or (False, failing_vector_index) if not.
    """
    num_cases = 1 << n
    mask = (1 << num_cases) - 1
    w = build_initial_state(n)
    for i, j in network:
        wi, wj = w[i], w[j]
        w[i] = wi & wj
        w[j] = wi | wj
    for c in range(n - 1):
        unsorted = (w[c] & ~w[c + 1]) & mask
        if unsorted:
            # First failing input index
            failing_m = (unsorted & -unsorted).bit_length() - 1
            return False, failing_m
    return True, None


def total_inversions(state: List[int], n: int) -> int:
    """Calculate total number of unsorted pairs across all 2^n inputs."""
    inv = 0
    for a in range(n):
        wa = state[a]
        for b in range(a + 1, n):
            inv += (wa & ~state[b]).bit_count()
    return inv


def batcher_odd_even_sort(n: int) -> List[Tuple[int, int]]:
    """Generate Batcher's odd-even mergesort network for n channels."""
    network: List[Tuple[int, int]] = []
    p = 1
    while p < n:
        k = p
        while k >= 1:
            for j in range(k % p, n - k, 2 * k):
                for i in range(0, min(k, n - j - k)):
                    if (i + j) // (2 * p) == (i + j + k) // (2 * p):
                        network.append((i + j, i + j + k))
            k //= 2
        p *= 2
    return network


def prune_network(
    n: int, network: List[Tuple[int, int]], prefix_len: int = 0
) -> List[Tuple[int, int]]:
    """Remove redundant comparators after prefix_len."""
    pruned = list(network)
    i = prefix_len
    while i < len(pruned):
        trial = pruned[:i] + pruned[i + 1 :]
        valid, _ = verify_01(n, trial)
        if valid:
            pruned.pop(i)
        else:
            i += 1
    return pruned


def greedy_repair(
    n: int,
    base_network: List[Tuple[int, int]],
    forbidden_set: Set[Tuple[int, int]],
    max_steps: int = 25,
) -> Optional[List[Tuple[int, int]]]:
    """Greedily add non-forbidden comparators that maximally reduce inversions."""
    w = build_initial_state(n)
    for i, j in base_network:
        wi, wj = w[i], w[j]
        w[i] = wi & wj
        w[j] = wi | wj

    cur_net = list(base_network)
    cur_inv = total_inversions(w, n)
    if cur_inv == 0:
        return cur_net

    for _ in range(max_steps):
        best_c = None
        best_inv = cur_inv
        best_w = None
        for i in range(n):
            for j in range(i + 1, n):
                if (i, j) in forbidden_set:
                    continue
                if (w[i] & ~w[j]) == 0:
                    continue
                nw_i = w[i] & w[j]
                nw_j = w[i] | w[j]
                trial_w = list(w)
                trial_w[i] = nw_i
                trial_w[j] = nw_j
                inv = total_inversions(trial_w, n)
                if inv < best_inv:
                    best_inv = inv
                    best_c = (i, j)
                    best_w = trial_w

        if best_c is None:
            break
        cur_net.append(best_c)
        w = best_w
        cur_inv = best_inv
        if cur_inv == 0:
            return cur_net

    return None if cur_inv > 0 else cur_net


def beam_search(
    n: int,
    max_k: int,
    prefix: List[Tuple[int, int]],
    forbidden_set: Set[Tuple[int, int]],
    beam_width: int = 120,
) -> Optional[List[Tuple[int, int]]]:
    """Guided beam search using total inversions heuristic."""
    w = build_initial_state(n)
    for i, j in prefix:
        wi, wj = w[i], w[j]
        w[i] = wi & wj
        w[j] = wi | wj

    inv0 = total_inversions(w, n)
    if inv0 == 0:
        return list(prefix)

    beam = [(inv0, list(prefix), tuple(w))]
    visited = {tuple(w)}

    for step in range(len(prefix), max_k):
        next_beam = []
        for score, path, state in beam:
            for i in range(n):
                for j in range(i + 1, n):
                    if (i, j) in forbidden_set:
                        continue
                    if (state[i] & ~state[j]) == 0:
                        continue
                    new_state = list(state)
                    new_state[i] = state[i] & state[j]
                    new_state[j] = state[i] | state[j]
                    st_tup = tuple(new_state)
                    if st_tup in visited:
                        continue
                    visited.add(st_tup)
                    sc = total_inversions(new_state, n)
                    if sc == 0:
                        return path + [(i, j)]
                    next_beam.append((sc, path + [(i, j)], st_tup))
        next_beam.sort(key=lambda x: x[0])
        beam = next_beam[:beam_width]
        if not beam:
            break
    return None


def synthesize_sorting_network(
    n: int, k: int, prefix: List[Tuple[int, int]], forbidden: List[Tuple[int, int]]
) -> Optional[List[Tuple[int, int]]]:
    """
    Synthesize a valid sorting network on n channels of length <= k
    starting with prefix and containing no forbidden comparators.
    """
    forbidden_set = set(forbidden)
    # Check if prefix already sorts
    valid, _ = verify_01(n, prefix)
    if valid and len(prefix) <= k:
        return list(prefix)

    # Strategy 1: Known optimal network completion & pruning
    if n in KNOWN_OPTIMAL:
        opt = KNOWN_OPTIMAL[n]
        combined = list(prefix)
        for c in opt:
            if c not in forbidden_set:
                combined.append(c)
        repaired = greedy_repair(n, combined, forbidden_set, max_steps=20)
        if repaired is not None:
            pruned = prune_network(n, repaired, prefix_len=len(prefix))
            if len(pruned) <= k:
                valid, _ = verify_01(n, pruned)
                if valid:
                    return pruned

    # Strategy 1b: mirror image of the known optimal network. The map
    # (i, j) -> (n-1-j, n-1-i) sends sorting networks to sorting networks.
    if n in KNOWN_OPTIMAL:
        mirrored = [(n - 1 - j, n - 1 - i) for i, j in KNOWN_OPTIMAL[n]]
        if (
            len(mirrored) <= k
            and mirrored[: len(prefix)] == list(prefix)
            and not (set(mirrored) & forbidden_set)
            and verify_01(n, mirrored)[0]
        ):
            return mirrored

    # Strategy 2: Batcher's construction completion & pruning
    batcher = batcher_odd_even_sort(n)
    combined = list(prefix)
    for c in batcher:
        if c not in forbidden_set:
            combined.append(c)
    repaired = greedy_repair(n, combined, forbidden_set, max_steps=25)
    if repaired is not None:
        pruned = prune_network(n, repaired, prefix_len=len(prefix))
        if len(pruned) <= k:
            valid, _ = verify_01(n, pruned)
            if valid:
                return pruned

    # Strategy 3: Guided Beam Search
    sol = beam_search(n, k, prefix, forbidden_set, beam_width=120)
    if sol is not None and len(sol) <= k:
        valid, _ = verify_01(n, sol)
        if valid:
            return sol

    return None
