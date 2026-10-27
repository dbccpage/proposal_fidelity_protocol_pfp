"""
Reference Hungarian Solver for Challenge C055: Assignment Problems with Dual Potentials.
Computes minimum/maximum weight perfect bipartite matching with certified dual potentials
or extracts a certified Hall violator row set S with |N(S)| < |S|.
"""

from typing import Any, Dict, List, Optional, Set, Tuple


def parse_cost_matrix(cost_raw: Any) -> Tuple[bool, List[List[Optional[int]]], int, str]:
    if not isinstance(cost_raw, list):
        return False, [], 0, "Cost must be a list"
    n = len(cost_raw)
    if n == 0:
        return False, [], 0, "Matrix cannot be empty"

    matrix: List[List[Optional[int]]] = []
    for r_idx, row in enumerate(cost_raw):
        if not isinstance(row, list) or len(row) != n:
            return False, [], 0, f"Row {r_idx} length mismatch (not square n={n})"
        parsed_row: List[Optional[int]] = []
        for cell in row:
            if cell is None:
                parsed_row.append(None)
            elif isinstance(cell, bool):
                return False, [], 0, f"Boolean cell at row {r_idx}"
            elif type(cell) is int:
                parsed_row.append(cell)
            elif isinstance(cell, str):
                try:
                    parsed_row.append(int(cell))
                except ValueError:
                    return False, [], 0, f"Non-integer cell at row {r_idx}: {cell}"
            else:
                return False, [], 0, f"Invalid cell type at row {r_idx}: {type(cell)}"
        matrix.append(parsed_row)
    return True, matrix, n, ""


def find_max_bipartite_matching(
    n: int, allowed: List[List[bool]]
) -> Tuple[int, List[int], List[int]]:
    match_r_to_c = [-1] * n
    match_c_to_r = [-1] * n

    def dfs(u: int, visited: List[bool]) -> bool:
        for v in range(n):
            if allowed[u][v] and not visited[v]:
                visited[v] = True
                if match_c_to_r[v] < 0 or dfs(match_c_to_r[v], visited):
                    match_r_to_c[u] = v
                    match_c_to_r[v] = u
                    return True
        return False

    matching_size = 0
    for u in range(n):
        visited = [False] * n
        if dfs(u, visited):
            matching_size += 1

    return matching_size, match_r_to_c, match_c_to_r


def find_hall_violator(
    n: int, allowed: List[List[bool]], match_r_to_c: List[int], match_c_to_r: List[int]
) -> List[int]:
    unmatched_rows = [r for r in range(n) if match_r_to_c[r] == -1]
    visited_r: Set[int] = set(unmatched_rows)
    visited_c: Set[int] = set()
    queue = list(unmatched_rows)

    while queue:
        r = queue.pop(0)
        for c in range(n):
            if allowed[r][c] and c not in visited_c:
                visited_c.add(c)
                matched_row = match_c_to_r[c]
                if matched_row != -1 and matched_row not in visited_r:
                    visited_r.add(matched_row)
                    queue.append(matched_row)

    S = sorted(list(visited_r))
    return S


def solve_assignment(case: Dict[str, Any]) -> Dict[str, Any]:
    case_id = case.get("case_id", "unknown")
    sense = case.get("sense", "min")
    if type(sense) is not str or sense not in ("min", "max"):
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_SENSE"},
        }

    if "cost" not in case:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "MISSING_COST_MATRIX"},
        }

    valid, C_orig, n, err_msg = parse_cost_matrix(case["cost"])
    if not valid:
        return {
            "case_id": case_id,
            "status": "OUT_OF_SCOPE",
            "witness": {"reason": "INVALID_COST_MATRIX", "details": err_msg},
        }

    allowed = [[(C_orig[i][j] is not None) for j in range(n)] for i in range(n)]

    # 1. Check feasibility via maximum bipartite matching
    matching_size, match_r, match_c = find_max_bipartite_matching(n, allowed)
    if matching_size < n:
        hall_set = find_hall_violator(n, allowed, match_r, match_c)
        return {
            "case_id": case_id,
            "status": "SOLVED",
            "kind": "NO_PERFECT_ASSIGNMENT",
            "hall_rows": hall_set,
        }

    # 2. Perfect assignment exists -> Run exact integer Hungarian
    # Prepare working cost matrix C_work (minimized)
    # If max sense, negate costs
    C_work: List[List[int]] = []
    max_abs_cost = 0
    for i in range(n):
        for j in range(n):
            if C_orig[i][j] is not None:
                max_abs_cost = max(max_abs_cost, abs(C_orig[i][j]))

    BIG = 4 * n * max_abs_cost + 10**20

    for i in range(n):
        row = []
        for j in range(n):
            if C_orig[i][j] is None:
                row.append(BIG)
            else:
                val = C_orig[i][j]
                row.append(-val if sense == "max" else val)
        C_work.append(row)

    # Standard O(n^3) Kuhn-Munkres Hungarian in integers
    # 1-based indexing for columns
    u = [0] * (n + 1)
    v = [0] * (n + 1)
    p = [0] * (n + 1)
    way = [0] * (n + 1)

    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [float("inf")] * (n + 1)
        used = [False] * (n + 1)

        while True:
            used[j0] = True
            i0 = p[j0]
            delta = float("inf")
            j1 = 0

            for j in range(1, n + 1):
                if not used[j]:
                    cur = C_work[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j

            for j in range(0, n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta

            j0 = j1
            if p[j0] == 0:
                break

        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if j0 == 0:
                break

    sigma = [0] * n
    for j in range(1, n + 1):
        row_idx = p[j] - 1
        sigma[row_idx] = j - 1

    # Format potentials (1-indexed to 0-indexed)
    u_pot = [u[i] for i in range(1, n + 1)]
    v_pot = [v[j] for j in range(1, n + 1)]

    # Compute actual value under original sense
    total_cost = sum(C_orig[i][sigma[i]] for i in range(n))

    return {
        "case_id": case_id,
        "status": "SOLVED",
        "kind": "OPTIMAL",
        "sigma": sigma,
        "u": [str(val) for val in u_pot],
        "v": [str(val) for val in v_pot],
        "value": str(total_cost),
    }
