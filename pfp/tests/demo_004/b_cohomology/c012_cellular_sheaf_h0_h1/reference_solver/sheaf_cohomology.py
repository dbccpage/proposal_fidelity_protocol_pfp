"""Exact Rational Linear Algebra and Sheaf Cohomology Solver for C012.

Standard library only (fractions.Fraction).
Computes exact cellular sheaf cohomology H^0 (global sections) and H^1
(obstruction space) on directed graphs over Q, with certified bases
and constructive gluing or Fredholm obstruction witnesses.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Any

CLOSED_REFUSAL_CODES = frozenset(
    {
        "VERTEX_COUNT_OUT_OF_BOUNDS",
        "EDGE_COUNT_OUT_OF_BOUNDS",
        "STALK_DIM_OUT_OF_BOUNDS",
        "COEFFICIENT_BOUND_EXCEEDED",
        "MALFORMED_RESTRICTION_MATRIX",
        "MALFORMED_TARGET_COCHAIN",
        "MALFORMED_CASE_STRUCTURE",
        "DISCONNECTED_GRAPH",
        "BUDGET_EXHAUSTED",
    }
)

CLOSED_OOS_REASONS = frozenset(
    {
        "RESTRICTION_SHAPE_MISMATCH",
        "SELF_LOOP",
        "UNKNOWN_ENDPOINT",
    }
)


def parse_canonical_rational(val: Any) -> Fraction:
    """Parses a canonical rational value strictly enforcing RFC 8785 conventions.

    Rejects:
    - floats, booleans, decimals, underscores
    - explicit positive sign (e.g. '+1', '+1/2')
    - negative zero ('-0', '-0/1')
    - leading zeros ('01', '01/2')
    - unreduced fractions ('2/4', '0/3')
    - redundant unit denominators ('1/1', '-5/1')
    - whitespace (' 1/2 ')
    - negative or zero denominators ('1/-2', '1/0')
    """
    if isinstance(val, bool):
        raise TypeError("Booleans are forbidden as numeric rational values")
    if isinstance(val, int):
        return Fraction(val, 1)
    if isinstance(val, str):
        if val != val.strip():
            raise ValueError(f"Whitespace forbidden in canonical rational string: {val!r}")
        if any(c.isspace() for c in val):
            raise ValueError(f"Whitespace forbidden in canonical rational string: {val!r}")
        if "." in val or "e" in val.lower() or "E" in val or "_" in val:
            raise ValueError(f"Floats, scientific notation, and underscores forbidden: {val!r}")
        if val == "-0" or val.startswith("-0/"):
            raise ValueError(f"Negative zero forbidden: {val!r}")
        if val.startswith("+"):
            raise ValueError(f"Explicit plus sign forbidden: {val!r}")

        if "/" in val:
            parts = val.split("/")
            if len(parts) != 2:
                raise ValueError(f"Malformed fraction string (multiple slashes): {val!r}")
            num_str, den_str = parts[0], parts[1]
            if num_str.startswith("+") or den_str.startswith("+"):
                raise ValueError(f"Explicit plus sign in fraction forbidden: {val!r}")
            if den_str.startswith("-"):
                raise ValueError(f"Negative denominator forbidden: {val!r}")

            try:
                num = int(num_str)
                den = int(den_str)
            except Exception as exc:
                raise ValueError(f"Non-integer fraction component in: {val!r}") from exc

            if str(num) != num_str or str(den) != den_str:
                raise ValueError(f"Leading zeros or invalid formatting in fraction: {val!r}")
            if den <= 0:
                raise ValueError(f"Denominator must be strictly positive: {val!r}")
            if den == 1:
                raise ValueError(f"Unit denominator '/1' must be formatted as integer: {val!r}")
            if num == 0:
                raise ValueError(f"Zero fraction must be formatted as '0': {val!r}")
            if math.gcd(abs(num), den) != 1:
                raise ValueError(f"Unreduced fraction forbidden: {val!r}")

            return Fraction(num, den)
        else:
            try:
                num = int(val)
            except Exception as exc:
                raise ValueError(f"Invalid integer string: {val!r}") from exc
            if str(num) != val:
                raise ValueError(f"Leading zeros forbidden in integer string: {val!r}")
            return Fraction(num, 1)

    raise TypeError(f"Unsupported rational type {type(val)}: {val!r}")


def format_canonical_rational(val: Fraction | int) -> str:
    """Formats a rational or integer into strict canonical string representation."""
    if isinstance(val, int):
        return str(val)
    f = Fraction(val)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def eliminate_augmented(
    delta: list[list[Fraction]],
    targets: list[list[Fraction]],
) -> tuple[int, list[int], list[list[Fraction]]]:
    """Performs Gauss-Jordan elimination on augmented block matrix [delta | I_{N1} | b_1 ... b_p].

    Returns:
    - rank: rank of delta
    - pivot_cols: list of pivot column indices in delta
    - augmented: reduced row echelon matrix of shape N1 x (N0 + N1 + p)
    """
    N1 = len(delta)
    N0 = len(delta[0]) if N1 > 0 else 0
    len(targets)

    if N1 == 0 or N0 == 0:
        return 0, [], []

    augmented: list[list[Fraction]] = []
    for i in range(N1):
        row = list(delta[i])
        row.extend([Fraction(1 if i == j else 0, 1) for j in range(N1)])
        for t in targets:
            row.append(t[i])
        augmented.append(row)

    pivot_cols: list[int] = []
    curr_row = 0
    for col in range(N0):
        pivot_idx = None
        for r in range(curr_row, N1):
            if augmented[r][col] != 0:
                pivot_idx = r
                break
        if pivot_idx is None:
            continue

        if pivot_idx != curr_row:
            augmented[curr_row], augmented[pivot_idx] = augmented[pivot_idx], augmented[curr_row]

        pivot_val = augmented[curr_row][col]
        for c in range(len(augmented[curr_row])):
            augmented[curr_row][c] /= pivot_val

        for r in range(N1):
            if r != curr_row and augmented[r][col] != 0:
                factor = augmented[r][col]
                for c in range(len(augmented[r])):
                    augmented[r][c] -= factor * augmented[curr_row][c]

        pivot_cols.append(col)
        curr_row += 1
        if curr_row == N1:
            break

    rank = len(pivot_cols)
    return rank, pivot_cols, augmented


def extract_h0_basis(
    rank: int,
    pivot_cols: list[int],
    augmented: list[list[Fraction]],
    N0: int,
) -> list[list[Fraction]]:
    """Extracts linearly independent canonical basis of H^0 = ker(delta)."""
    if N0 == 0:
        return []
    if rank == 0 and not augmented:
        return [[Fraction(1 if i == j else 0, 1) for j in range(N0)] for i in range(N0)]

    pivot_set = set(pivot_cols)
    free_cols = [c for c in range(N0) if c not in pivot_set]

    basis: list[list[Fraction]] = []
    for f in free_cols:
        vec = [Fraction(0, 1)] * N0
        vec[f] = Fraction(1, 1)
        for r_idx, p_col in enumerate(pivot_cols):
            vec[p_col] = -augmented[r_idx][f]
        basis.append(vec)

    return basis


def compute_matrix_rank(mat: list[list[Fraction]]) -> int:
    """Computes exact column/row rank of a matrix over Q."""
    if not mat or not mat[0]:
        return 0
    nrows = len(mat)
    ncols = len(mat[0])
    A = [[Fraction(entry) for entry in row] for row in mat]
    r = 0
    for col in range(ncols):
        pivot_row = -1
        for row in range(r, nrows):
            if A[row][col] != 0:
                pivot_row = row
                break
        if pivot_row == -1:
            continue
        A[r], A[pivot_row] = A[pivot_row], A[r]
        pivot_val = A[r][col]
        for c in range(col, ncols):
            A[r][c] /= pivot_val
        for row in range(nrows):
            if row != r and A[row][col] != 0:
                factor = A[row][col]
                for c in range(col, ncols):
                    A[row][c] -= factor * A[r][c]
        r += 1
        if r == nrows:
            break
    return r


def extract_h1_complement(
    delta: list[list[Fraction]],
    rank: int,
) -> list[list[Fraction]]:
    """Extracts H^1 complement basis such that [delta | complement] spans C^1."""
    N1 = len(delta)
    if N1 == 0:
        return []
    N0 = len(delta[0]) if N1 > 0 else 0
    expected_dim = N1 - rank
    if expected_dim <= 0:
        return []

    # Greedily test standard unit vectors e_0 ... e_{N1-1}
    # Form initial basis matrix from columns of delta
    cols: list[list[Fraction]] = []
    for c in range(N0):
        cols.append([delta[r][c] for r in range(N1)])

    current_rank = rank
    complement_vecs: list[list[Fraction]] = []

    for j in range(N1):
        candidate = [Fraction(1 if r == j else 0, 1) for r in range(N1)]
        test_mat = [
            row + [candidate[r]]
            for r, row in enumerate([[cols[c][r] for c in range(len(cols))] for r in range(N1)])
        ]
        new_rank = compute_matrix_rank(test_mat)
        if new_rank > current_rank:
            complement_vecs.append(candidate)
            cols.append(candidate)
            current_rank = new_rank
            if len(complement_vecs) == expected_dim:
                break

    return complement_vecs


def solve_sheaf_targets(
    rank: int,
    pivot_cols: list[int],
    augmented: list[list[Fraction]],
    delta: list[list[Fraction]],
    targets: list[list[Fraction]],
    N0: int,
    N1: int,
) -> list[dict[str, Any]]:
    """Determines feasibility of each target cochain under delta.

    Returns for each target either:
    - {"glues": True, "x": [...]}
    - {"glues": False, "eta": [...]} with delta^T eta == 0 and <eta, b> != 0
    """
    results: list[dict[str, Any]] = []

    if N1 == 0:
        for _ in targets:
            results.append({"glues": True, "x": ["0"] * N0 if N0 > 0 else []})
        return results

    if N0 == 0:
        for t in targets:
            is_zero = all(c == 0 for c in t)
            if is_zero:
                results.append({"glues": True, "x": []})
            else:
                results.append({"glues": False, "eta": [format_canonical_rational(c) for c in t]})
        return results

    for k, b_vec in enumerate(targets):
        col_offset = N0 + N1 + k
        is_glued = True
        obstructed_row = -1

        for r in range(rank, N1):
            if augmented[r][col_offset] != 0:
                is_glued = False
                obstructed_row = r
                break

        if is_glued:
            x_sol = [Fraction(0, 1)] * N0
            for r_idx, p_col in enumerate(pivot_cols):
                x_sol[p_col] = augmented[r_idx][col_offset]
            results.append(
                {
                    "glues": True,
                    "x": [format_canonical_rational(val) for val in x_sol],
                }
            )
        else:
            eta_raw = [augmented[obstructed_row][N0 + j] for j in range(N1)]
            results.append(
                {
                    "glues": False,
                    "eta": [format_canonical_rational(val) for val in eta_raw],
                }
            )

    return results
