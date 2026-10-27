"""
Independent Second Checker for Challenge C055.
Constructed with an alternate bipartite matching / flow certifier to independently
verify assignment optimality, dual bounds, and Hall violators.

Correction, 2026-09-29: Booleans are no longer read as integers (in the cost
matrix, sigma or hall_rows), and a ``sense`` other than "min" or "max" makes
the case out of scope instead of silently selecting the maximisation branch.
"""

from typing import Any, Dict, List, Tuple


def _parse_strict_int(val: Any) -> int:
    if type(val) is not str:
        raise ValueError(f"Entry must be string: {val}")
    num = int(val)
    if str(num) != val:
        raise ValueError(f"Non-canonical integer: {val}")
    return num


def _parse_matrix(cost_raw: Any) -> Tuple[bool, List[List[Any]], int]:
    if not isinstance(cost_raw, list) or len(cost_raw) == 0:
        return False, [], 0
    n = len(cost_raw)
    matrix = []
    for row in cost_raw:
        if not isinstance(row, list) or len(row) != n:
            return False, [], 0
        parsed_row = []
        for cell in row:
            if cell is None:
                parsed_row.append(None)
            elif type(cell) is int:
                parsed_row.append(cell)
            elif isinstance(cell, str):
                try:
                    parsed_row.append(int(cell))
                except ValueError:
                    return False, [], 0
            else:
                return False, [], 0
        matrix.append(parsed_row)
    return True, matrix, n


def independent_check(case: Dict[str, Any], result: Any) -> Tuple[bool, str]:
    if not isinstance(result, dict):
        return False, "Result is not a JSON object"
    try:
        if result.get("case_id") != case.get("case_id"):
            return False, "Case ID mismatch"
        status = result.get("status")

        valid_matrix, C, n = _parse_matrix(case.get("cost"))
        sense = case.get("sense", "min")
        if sense not in ("min", "max") or type(sense) is not str:
            valid_matrix = False

        if status == "OUT_OF_SCOPE":
            return (
                (True, "Valid OUT_OF_SCOPE")
                if not valid_matrix
                else (False, "Valid matrix rejected as OUT_OF_SCOPE")
            )

        if not valid_matrix:
            return False, f"Expected OUT_OF_SCOPE, got {status}"

        if status != "SOLVED":
            return False, f"Unexpected status: {status}"

        kind = result.get("kind")

        if kind == "NO_PERFECT_ASSIGNMENT":
            hall_rows = result.get("hall_rows")
            if (
                not isinstance(hall_rows, list)
                or len(hall_rows) == 0
                or len(set(hall_rows)) != len(hall_rows)
            ):
                return False, "Invalid hall_rows list"
            if any(type(r) is not int or r < 0 or r >= n for r in hall_rows):
                return False, "hall_rows out of bounds"

            S = set(hall_rows)
            N_S = set()
            for r in S:
                for c in range(n):
                    if C[r][c] is not None:
                        N_S.add(c)
            if len(N_S) >= len(S):
                return False, f"Hall condition not violated: |N(S)|={len(N_S)} >= |S|={len(S)}"
            return True, "Independent check passed for NO_PERFECT_ASSIGNMENT"

        if kind == "OPTIMAL":
            sigma = result.get("sigma")
            if (
                not isinstance(sigma, list)
                or any(type(j) is not int for j in sigma)
                or sorted(sigma) != list(range(n))
            ):
                return False, "Invalid permutation sigma"

            for i in range(n):
                if C[i][sigma[i]] is None:
                    return False, f"Forbidden entry chosen at ({i}, {sigma[i]})"

            u_raw = result.get("u")
            v_raw = result.get("v")
            val_raw = result.get("value")
            if (
                not isinstance(u_raw, list)
                or not isinstance(v_raw, list)
                or len(u_raw) != n
                or len(v_raw) != n
                or val_raw is None
            ):
                return False, "Missing or invalid u, v, value"

            u = [_parse_strict_int(x) for x in u_raw]
            v = [_parse_strict_int(x) for x in v_raw]
            val = _parse_strict_int(val_raw)

            actual_cost = sum(C[i][sigma[i]] for i in range(n))
            if actual_cost != val:
                return False, f"Actual permutation cost {actual_cost} != claimed value {val}"

            sum_uv = sum(u) + sum(v)
            if sense == "min":
                if sum_uv != val:
                    return False, f"sum(u) + sum(v) = {sum_uv} != value = {val}"
                for i in range(n):
                    for j in range(n):
                        if C[i][j] is not None:
                            if u[i] + v[j] > C[i][j]:
                                return False, f"Dual inequality violated at ({i}, {j})"
            else:
                if sum_uv != val and sum_uv != -val:
                    return False, f"sum(u) + sum(v) = {sum_uv} != value = {val}"
                if sum_uv == -val:
                    for i in range(n):
                        for j in range(n):
                            if C[i][j] is not None:
                                if u[i] + v[j] > -C[i][j]:
                                    return False, f"Negated dual inequality violated at ({i}, {j})"
                else:
                    for i in range(n):
                        for j in range(n):
                            if C[i][j] is not None:
                                if u[i] + v[j] < C[i][j]:
                                    return False, f"Max dual inequality violated at ({i}, {j})"

            return True, "Independent check passed for OPTIMAL"

        return False, f"Invalid kind: {kind}"
    except Exception as e:
        return False, f"Independent check exception: {e}"
