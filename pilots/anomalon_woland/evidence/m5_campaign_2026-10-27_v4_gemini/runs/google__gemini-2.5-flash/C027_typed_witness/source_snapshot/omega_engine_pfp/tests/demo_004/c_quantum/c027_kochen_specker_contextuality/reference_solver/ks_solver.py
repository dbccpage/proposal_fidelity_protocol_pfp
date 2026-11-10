# AuthorityEffect: None.
"""
Exact Kochen-Specker contextuality decider and parity certificate finder for C027.

Solves the non-contextual {0, 1} colouring problem:
1. Orthogonality constraints: for each orthogonal pair (u, v), not both 1.
2. Context constraints: for each complete orthogonal basis C of size d, sum_{r in C} x_r == 1.

If colourable: returns a valid {0, 1} colouring.
If uncolourable: searches for a parity certificate (odd number of contexts with even ray degrees)
via exact F2 Gaussian elimination, or emits an uncolourable subset certificate.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple


def solve_f2_parity_certificate(
    n_rays: int,
    contexts: List[List[int]],
) -> Optional[List[List[int]]]:
    r"""
    Searches for an odd number of contexts such that every ray appears an even number of times.
    This corresponds to solving over F_2:
        A * y = 0 (mod 2)   for each ray r
        sum_j y_j = 1 (mod 2)
    where A_{r, j} = 1 iff ray r in context C_j.
    """
    m = len(contexts)
    if m == 0:
        return None

    # Equations:
    # rows 0..n_rays-1: incidence of ray r
    # row n_rays: sum of y_j = 1
    # Augmented matrix with m columns + 1 RHS column
    n_eqs = n_rays + 1
    aug: List[List[int]] = [[0] * (m + 1) for _ in range(n_eqs)]

    for j, ctx in enumerate(contexts):
        for r in ctx:
            if r < n_rays:
                aug[r][j] = 1
        aug[n_rays][j] = 1  # sum equation

    aug[n_rays][m] = 1  # RHS = 1 for odd sum

    # F_2 Gaussian elimination
    pivot_cols: List[int] = []
    pivot_row = 0

    for col in range(m):
        if pivot_row >= n_eqs:
            break
        sel_row = None
        for r in range(pivot_row, n_eqs):
            if aug[r][col] == 1:
                sel_row = r
                break
        if sel_row is None:
            continue

        if sel_row != pivot_row:
            aug[pivot_row], aug[sel_row] = aug[sel_row], aug[pivot_row]

        # Eliminate other rows
        for r in range(n_eqs):
            if r != pivot_row and aug[r][col] == 1:
                for c in range(col, m + 1):
                    aug[r][c] ^= aug[pivot_row][c]

        pivot_cols.append(col)
        pivot_row += 1

    # Check for inconsistency: row with 0 ... 0 | 1
    for r in range(n_eqs):
        if all(aug[r][c] == 0 for c in range(m)) and aug[r][m] == 1:
            return None  # No parity certificate

    # Back-substitute to find a solution
    y = [0] * m
    for p_idx, col in enumerate(pivot_cols):
        y[col] = aug[p_idx][m]

    # Verify solution
    selected_contexts = [contexts[j] for j in range(m) if y[j] == 1]
    if len(selected_contexts) % 2 != 1:
        return None

    ray_counts: Dict[int, int] = {}
    for ctx in selected_contexts:
        for r in ctx:
            ray_counts[r] = ray_counts.get(r, 0) + 1

    if any(count % 2 != 0 for count in ray_counts.values()):
        return None

    return selected_contexts


class KSBacktracker:
    """Exact constraint satisfaction solver for Kochen-Specker contextuality."""

    def __init__(
        self,
        n_rays: int,
        adj: List[Set[int]],
        contexts: List[List[int]],
    ) -> None:
        self.n_rays = n_rays
        self.adj = adj
        self.contexts = contexts

        # Context lookup per ray
        self.ray_to_contexts: List[List[int]] = [[] for _ in range(n_rays)]
        for c_idx, ctx in enumerate(contexts):
            for r in ctx:
                self.ray_to_contexts[r].append(c_idx)

    def propagate(self, assignment: List[Optional[int]]) -> Optional[List[Optional[int]]]:
        """
        Applies unit propagation on orthogonality and context constraints.
        Returns updated assignment or None on contradiction.
        """
        curr = list(assignment)
        changed = True

        while changed:
            changed = False

            # 1. Orthogonality constraints: if x_u == 1, all neighbors v must be 0
            for u in range(self.n_rays):
                if curr[u] == 1:
                    for v in self.adj[u]:
                        if curr[v] == 1:
                            return None  # Direct orthogonality violation
                        if curr[v] is None:
                            curr[v] = 0
                            changed = True

            # 2. Context constraints: sum_{r in C} x_r == 1
            for ctx in self.contexts:
                ones = sum(1 for r in ctx if curr[r] == 1)
                unassigned = [r for r in ctx if curr[r] is None]

                if ones > 1:
                    return None  # More than one 1 in a context

                if ones == 1:
                    # All remaining unassigned must be 0
                    for r in unassigned:
                        curr[r] = 0
                        changed = True

                elif ones == 0:
                    if len(unassigned) == 0:
                        return None  # Context has zero ones
                    if len(unassigned) == 1:
                        # Exactly one left, must be 1
                        curr[unassigned[0]] = 1
                        changed = True

        return curr

    def search(self, assignment: List[Optional[int]]) -> Optional[List[int]]:
        """Backtracking search for a valid colouring."""
        prop = self.propagate(assignment)
        if prop is None:
            return None

        # Check if complete
        unassigned = [i for i, val in enumerate(prop) if val is None]
        if not unassigned:
            return [val if val is not None else 0 for val in prop]

        # Heuristic: pick unassigned variable involved in the most contexts
        best_var = max(unassigned, key=lambda v: len(self.ray_to_contexts[v]))

        # Try 1 first, then 0
        branch1 = list(prop)
        branch1[best_var] = 1
        sol1 = self.search(branch1)
        if sol1 is not None:
            return sol1

        branch0 = list(prop)
        branch0[best_var] = 0
        return self.search(branch0)


def solve_contextuality(
    n_rays: int,
    adj: List[Set[int]],
    contexts: List[List[int]],
) -> Tuple[bool, Optional[List[int]], Optional[Dict[str, Any]]]:
    """
    Decides whether a valid KS non-contextual colouring exists.
    Returns:
        (colourable, colouring_if_true, certificate_if_false)
    """
    solver = KSBacktracker(n_rays, adj, contexts)
    init_assignment: List[Optional[int]] = [None] * n_rays
    sol = solver.search(init_assignment)

    if sol is not None:
        return True, sol, None

    # Uncolourable: search for parity certificate
    parity_ctxs = solve_f2_parity_certificate(n_rays, contexts)
    if parity_ctxs is not None:
        # Collect rays involved in parity contexts
        involved_rays = sorted(list(set(r for ctx in parity_ctxs for r in ctx)))
        cert = {
            "kind": "parity",
            "contexts": parity_ctxs,
            "subset": involved_rays,
        }
        return False, None, cert

    # Fallback uncolourable certificate
    cert = {
        "kind": "refutation",
        "method": "complete_backtracking_exhaustion",
        "contexts_count": len(contexts),
        "subset": list(range(n_rays)),
    }
    return False, None, cert
