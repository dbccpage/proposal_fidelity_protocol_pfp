"""Orbit Search and Equivalence Decider for C024.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections import deque
from typing import Any

try:
    from .cut_rank import find_cut_rank_separation
    from .graph import SimpleGraph
except (ImportError, ValueError):
    try:
        from reference_solver.cut_rank import find_cut_rank_separation
        from reference_solver.graph import SimpleGraph
    except (ImportError, ValueError):
        from cut_rank import find_cut_rank_separation
        from graph import SimpleGraph


def decide_local_equivalence(
    g1: SimpleGraph,
    g2: SimpleGraph,
    max_orbit_states: int = 25000,
) -> tuple[bool | None, list[int] | None, dict[str, Any] | None]:
    """Decides whether g1 and g2 are local-Clifford equivalent.

    Returns:
        (True, sequence, None) if equivalent.
        (False, None, separating_witness) if not equivalent.
        (None, None, refusal_witness) if the search budget is exhausted before
        either equivalence or non-equivalence is certified.
    """
    if g1 == g2:
        return True, [], None

    n = g1.n

    # First, quick invariant check: cut-rank separation on singletons and pairs
    sep = find_cut_rank_separation(g1, g2, max_search_subsets=500)
    if sep is not None:
        return False, None, sep

    # Bidirectional BFS on local complementation orbit
    # States are represented by canonical tuples
    t1 = g1.to_canonical_tuple()
    t2 = g2.to_canonical_tuple()

    fwd_queue: deque[tuple[SimpleGraph, tuple[int, ...]]] = deque([(g1, t1)])
    bwd_queue: deque[tuple[SimpleGraph, tuple[int, ...]]] = deque([(g2, t2)])

    fwd_paths: dict[tuple[int, ...], list[int]] = {t1: []}
    bwd_paths: dict[tuple[int, ...], list[int]] = {t2: []}

    states_visited = 2

    while fwd_queue and bwd_queue and states_visited < max_orbit_states:
        # Expand smaller frontier
        if len(fwd_queue) <= len(bwd_queue):
            curr_g, curr_t = fwd_queue.popleft()
            curr_path = fwd_paths[curr_t]

            for v in range(n):
                # Optimization: local complementation at isolated vertex does nothing
                if not any(curr_g.adj[v]):
                    continue

                nxt_g = curr_g.local_complementation(v)
                nxt_t = nxt_g.to_canonical_tuple()

                if nxt_t in bwd_paths:
                    # Found intersection!
                    full_seq = curr_path + [v] + list(reversed(bwd_paths[nxt_t]))
                    return True, full_seq, None

                if nxt_t not in fwd_paths:
                    fwd_paths[nxt_t] = curr_path + [v]
                    fwd_queue.append((nxt_g, nxt_t))
                    states_visited += 1
                    if states_visited >= max_orbit_states:
                        break
        else:
            curr_g, curr_t = bwd_queue.popleft()
            curr_path = bwd_paths[curr_t]

            for v in range(n):
                if not any(curr_g.adj[v]):
                    continue

                nxt_g = curr_g.local_complementation(v)
                nxt_t = nxt_g.to_canonical_tuple()

                if nxt_t in fwd_paths:
                    # Found intersection!
                    full_seq = fwd_paths[nxt_t] + [v] + list(reversed(curr_path))
                    return True, full_seq, None

                if nxt_t not in bwd_paths:
                    bwd_paths[nxt_t] = curr_path + [v]
                    bwd_queue.append((nxt_g, nxt_t))
                    states_visited += 1
                    if states_visited >= max_orbit_states:
                        break

    # A drained frontier has explored one complete LC orbit.  With no
    # intersection, the two orbits are disjoint and non-equivalence is proved.
    if not fwd_queue or not bwd_queue:
        exhausted_side = "g" if not fwd_queue else "g_prime"
        orbit_states = len(fwd_paths) if exhausted_side == "g" else len(bwd_paths)
        return (
            False,
            None,
            {
                "kind": "orbit_exhaustion",
                "exhausted_side": exhausted_side,
                "orbit_states": orbit_states,
                "states_visited": states_visited,
            },
        )

    # The state budget was reached.  A cut-rank separation can still prove
    # non-equivalence, but failure to find one is not a proof: distinct LC
    # orbits can share every cut-rank value checked here.
    sep = find_cut_rank_separation(g1, g2, max_search_subsets=10000)
    if sep is not None:
        return False, None, sep

    return (
        None,
        None,
        {
            "kind": "orbit_search_budget_exhausted",
            "states_visited": states_visited,
            "max_orbit_states": max_orbit_states,
        },
    )


__all__ = [
    "decide_local_equivalence",
]
