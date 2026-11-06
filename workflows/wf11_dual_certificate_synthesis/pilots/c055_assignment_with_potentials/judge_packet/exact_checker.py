"""
Exact Checker for Challenge C055: Assignment Problems with Dual Potentials.
Validates:
- For OPTIMAL: permutation bijection, allowed entries only, exact dual inequalities u_i + v_j <= c_ij,
  and sum equality sum(u) + sum(v) == value == cost(sigma).
- For NO_PERFECT_ASSIGNMENT: Hall's condition violation |N(S)| < |S|.
- Strict canonical integer string formatting.
- The case is in scope only if the matrix is well formed (Booleans are not
  integers) and ``sense`` is absent, "min" or "max".

Correction, 2026-09-29: a Boolean permutation such as [true, false] passed,
a float permutation crashed the checker, and a ``sense`` outside {min, max}
skipped the dual checks.
"""

from typing import Any, Dict, List, Set, Tuple

VALID_SENSES = ("min", "max")


def parse_strict_int(val: Any) -> int:
    if type(val) is not str:
        raise ValueError(f"Entry must be string, got {type(val)}: {val}")
    # Canonical integer string: no sign '+', no leading zeros, no whitespace.
    num = int(val)
    if str(num) != val:
        raise ValueError(f"Non-canonical integer string: {val} vs {num}")
    return num


def parse_cost_matrix_lenient(cost_raw: Any) -> Tuple[bool, List[List[Any]], int, str]:
    if not isinstance(cost_raw, list):
        return False, [], 0, "Cost is not a list"
    n = len(cost_raw)
    if n == 0:
        return False, [], 0, "Empty matrix"
    matrix = []
    for r_idx, row in enumerate(cost_raw):
        if not isinstance(row, list) or len(row) != n:
            return False, [], 0, f"Row {r_idx} length mismatch"
        parsed_row = []
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


def check_exact(case: Dict[str, Any], result: Any) -> Tuple[bool, str]:
    if not isinstance(result, dict):
        return False, f"Result must be a JSON object, got {type(result).__name__}"
    if result.get("case_id") != case.get("case_id"):
        return (
            False,
            f"Case ID mismatch: expected {case.get('case_id')}, got {result.get('case_id')}",
        )

    status = result.get("status")
    if status not in ("SOLVED", "OUT_OF_SCOPE", "UNKNOWN"):
        return False, f"Invalid status: {status}"

    cost_raw = case.get("cost")
    is_valid_matrix, C, n, err_msg = parse_cost_matrix_lenient(cost_raw)
    sense = case.get("sense", "min")
    if is_valid_matrix and (type(sense) is not str or sense not in VALID_SENSES):
        is_valid_matrix = False

    if status == "OUT_OF_SCOPE":
        if is_valid_matrix:
            return False, "Solver claimed OUT_OF_SCOPE on a valid cost matrix"
        witness = result.get("witness")
        if not isinstance(witness, dict) or "reason" not in witness:
            return False, "Missing witness.reason for OUT_OF_SCOPE"
        return True, "Valid OUT_OF_SCOPE"

    if not is_valid_matrix:
        return False, f"Expected OUT_OF_SCOPE, but solver returned {status}"

    kind = result.get("kind")
    if kind not in ("OPTIMAL", "NO_PERFECT_ASSIGNMENT"):
        return False, f"Invalid kind: {kind}"

    if kind == "NO_PERFECT_ASSIGNMENT":
        hall_rows = result.get("hall_rows")
        if not isinstance(hall_rows, list) or len(hall_rows) == 0:
            return False, "hall_rows must be a non-empty list of row indices"
        if len(set(hall_rows)) != len(hall_rows):
            return False, "hall_rows contains duplicate row indices"
        if any(type(r) is not int or r < 0 or r >= n for r in hall_rows):
            return False, "hall_rows contains invalid row index"

        # Compute N(S)
        S = set(hall_rows)
        N_S: Set[int] = set()
        for r in S:
            for c in range(n):
                if C[r][c] is not None:
                    N_S.add(c)

        if len(N_S) >= len(S):
            return False, f"Hall condition not violated: |N(S)| = {len(N_S)} >= |S| = {len(S)}"

        return True, f"Valid Hall violator (|S|={len(S)}, |N(S)|={len(N_S)})"

    if kind == "OPTIMAL":
        sigma = result.get("sigma")
        if not isinstance(sigma, list) or len(sigma) != n:
            return False, f"sigma must be a list of length {n}"
        if any(type(j) is not int for j in sigma):
            return False, "sigma entries must be integers (not Booleans or floats)"
        if sorted(sigma) != list(range(n)):
            return False, "sigma is not a valid permutation of 0..n-1"

        # Check all chosen pairs are allowed
        for i in range(n):
            j = sigma[i]
            if C[i][j] is None:
                return False, f"sigma uses forbidden entry at ({i}, {j})"

        # Check potentials u and v
        u_raw = result.get("u")
        v_raw = result.get("v")
        val_raw = result.get("value")

        if not isinstance(u_raw, list) or len(u_raw) != n:
            return False, f"u must be a list of length {n}"
        if not isinstance(v_raw, list) or len(v_raw) != n:
            return False, f"v must be a list of length {n}"
        if val_raw is None:
            return False, "Missing value field"

        try:
            u = [parse_strict_int(x) for x in u_raw]
            v = [parse_strict_int(x) for x in v_raw]
            val = parse_strict_int(val_raw)
        except Exception as e:
            return False, f"Invalid integer string formatting: {e}"

        cost_sum = sum(C[i][sigma[i]] for i in range(n))
        if cost_sum != val:
            return False, f"Claimed value {val} does not match permutation cost {cost_sum}"

        sum_uv = sum(u) + sum(v)

        if sense == "min":
            for i in range(n):
                for j in range(n):
                    if C[i][j] is not None:
                        if u[i] + v[j] > C[i][j]:
                            return (
                                False,
                                f"Dual inequality violated at ({i}, {j}): u[{i}] + v[{j}] = {u[i] + v[j]} > c = {C[i][j]}",
                            )
            if sum_uv != val:
                return False, f"Dual sum mismatch: sum(u) + sum(v) = {sum_uv} != value = {val}"
        else:  # sense == "max", validated above
            # Supports negated formulation (u_i + v_j <= -C[i][j] with sum == -val)
            # OR standard maximization dual (u_i + v_j >= C[i][j] with sum == val)
            is_negated = sum_uv == -val
            is_standard = sum_uv == val
            if not is_negated and not is_standard:
                return (
                    False,
                    f"Dual sum mismatch for max sense: sum(u) + sum(v) = {sum_uv} not in ({val}, {-val})",
                )

            if is_negated:
                for i in range(n):
                    for j in range(n):
                        if C[i][j] is not None:
                            if u[i] + v[j] > -C[i][j]:
                                return (
                                    False,
                                    f"Negated dual inequality violated at ({i}, {j}): u[{i}] + v[{j}] = {u[i] + v[j]} > -c = {-C[i][j]}",
                                )
            else:
                for i in range(n):
                    for j in range(n):
                        if C[i][j] is not None:
                            if u[i] + v[j] < C[i][j]:
                                return (
                                    False,
                                    f"Max dual inequality violated at ({i}, {j}): u[{i}] + v[{j}] = {u[i] + v[j]} < c = {C[i][j]}",
                                )

        return True, "Valid OPTIMAL assignment with certified potentials"

    return False, f"Unhandled kind: {kind}"
