"""Exact Rational Simplex Solver with Dual and Farkas Certificates."""

from fractions import Fraction
from typing import Any, Dict, List


def parse_fraction(s: Any) -> Fraction:
    if isinstance(s, Fraction):
        return s
    if isinstance(s, int):
        return Fraction(s, 1)
    if isinstance(s, str):
        s = s.strip()
        if "/" in s:
            parts = s.split("/")
            if len(parts) == 2:
                num, den = int(parts[0]), int(parts[1])
                if den == 0:
                    raise ZeroDivisionError("Denominator cannot be zero")
                return Fraction(num, den)
            raise ValueError(f"Invalid fraction string: {s}")
        return Fraction(int(s), 1)
    raise TypeError(f"Invalid fraction type: {type(s)}")


def format_fraction(f: Fraction) -> str:
    return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"


def solve_lp_exact(A_raw: Any, b_raw: Any, c_raw: Any, max_pivots: int = 5000) -> Dict[str, Any]:
    if not isinstance(A_raw, list) or not isinstance(b_raw, list) or not isinstance(c_raw, list):
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "input", "reason": "A, b, c must be lists"},
        }
    m, n = len(b_raw), len(c_raw)
    if m == 0 or n == 0:
        return {
            "status": "OUT_OF_SCOPE",
            "witness": {"field": "dimensions", "reason": "m and n must be >= 1"},
        }
    if len(A_raw) != m:
        return {"status": "OUT_OF_SCOPE", "witness": {"field": "A", "reason": "ROW_COUNT_MISMATCH"}}
    try:
        A: List[List[Fraction]] = []
        for i, row in enumerate(A_raw):
            if not isinstance(row, list) or len(row) != n:
                return {
                    "status": "OUT_OF_SCOPE",
                    "witness": {"field": f"A[{i}]", "reason": "ROW_LENGTH_MISMATCH"},
                }
            A.append([parse_fraction(val) for val in row])
        b: List[Fraction] = [parse_fraction(val) for val in b_raw]
        c: List[Fraction] = [parse_fraction(val) for val in c_raw]
    except Exception as exc:
        return {"status": "OUT_OF_SCOPE", "witness": {"field": "data_parsing", "reason": str(exc)}}

    pivots_used = 0
    min_b = min(b)
    if min_b < 0:
        cols = 1 + n + m + 1
        tab = [[Fraction(0)] * cols for _ in range(m + 1)]
        k = b.index(min_b)
        for i in range(m):
            tab[i + 1][0] = Fraction(-1)
            for j in range(n):
                tab[i + 1][1 + j] = A[i][j]
            tab[i + 1][1 + n + i] = Fraction(1)
            tab[i + 1][-1] = b[i]
        basis = [1 + n + i for i in range(m)]
        piv_row = k + 1
        tab[piv_row] = [-v for v in tab[piv_row]]
        basis[k] = 0
        for i in range(1, m + 1):
            if i != piv_row:
                fac = tab[i][0]
                if fac != 0:
                    tab[i] = [tab[i][col] - fac * tab[piv_row][col] for col in range(cols)]
        tab[0] = [tab[piv_row][col] for col in range(cols)]
        tab[0][0] = Fraction(0)
        tab[0][-1] = -tab[piv_row][-1]

        while True:
            e = -1
            for j in range(1 + n + m):
                if tab[0][j] > 0:
                    e = j
                    break
            if e == -1:
                break
            if pivots_used >= max_pivots:
                return {"status": "UNKNOWN", "code": "PIVOT_LIMIT"}
            leaving = -1
            min_ratio = None
            for i in range(m):
                d = tab[i + 1][e]
                if d > 0:
                    ratio = tab[i + 1][-1] / d
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        leaving = i + 1
                    elif ratio == min_ratio:
                        if basis[i] < basis[leaving - 1]:
                            leaving = i + 1
            if leaving == -1:
                break
            piv = tab[leaving][e]
            tab[leaving] = [v / piv for v in tab[leaving]]
            for i in range(m + 1):
                if i != leaving:
                    fac = tab[i][e]
                    if fac != 0:
                        tab[i] = [tab[i][col] - fac * tab[leaving][col] for col in range(cols)]
            basis[leaving - 1] = e
            pivots_used += 1

        opt_val = tab[0][-1]
        if opt_val < 0:
            y = [tab[0][1 + n + i] for i in range(m)]
            dot_by = sum(b[i] * y[i] for i in range(m))
            if dot_by > 0:
                y = [-v for v in y]
            return {
                "status": "SOLVED",
                "kind": "INFEASIBLE",
                "farkas_y": [format_fraction(v) for v in y],
            }

        if 0 in basis:
            r = basis.index(0) + 1
            piv_col = None
            for col in range(1, 1 + n + m):
                if tab[r][col] != 0:
                    piv_col = col
                    break
            if piv_col is not None:
                piv = tab[r][piv_col]
                tab[r] = [v / piv for v in tab[r]]
                for i in range(m + 1):
                    if i != r:
                        fac = tab[i][piv_col]
                        if fac != 0:
                            tab[i] = [tab[i][col] - fac * tab[r][col] for col in range(cols)]
                basis[r - 1] = piv_col
                pivots_used += 1
        for row in tab:
            row.pop(0)
        basis = [b_idx - 1 for b_idx in basis]
        total_vars = n + m
    else:
        total_vars = n + m
        cols = total_vars + 1
        tab = [[Fraction(0)] * cols for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                tab[i + 1][j] = A[i][j]
            tab[i + 1][n + i] = Fraction(1)
            tab[i + 1][-1] = b[i]
        basis = [n + i for i in range(m)]

    tab[0] = [Fraction(0)] * (total_vars + 1)
    for j in range(n):
        tab[0][j] = c[j]
    for i in range(m):
        b_var = basis[i]
        coeff = c[b_var] if b_var < n else Fraction(0)
        if coeff != 0:
            tab[0] = [tab[0][col] - coeff * tab[i + 1][col] for col in range(total_vars + 1)]

    while True:
        e = -1
        for j in range(total_vars):
            if tab[0][j] > 0:
                e = j
                break
        if e == -1:
            x = [Fraction(0)] * n
            for i in range(m):
                b_var = basis[i]
                if b_var < n:
                    x[b_var] = tab[i + 1][-1]
            y = [-tab[0][n + k] for k in range(m)]
            val = sum(c[j] * x[j] for j in range(n))
            return {
                "status": "SOLVED",
                "kind": "OPTIMAL",
                "x": [format_fraction(v) for v in x],
                "y": [format_fraction(v) for v in y],
                "value": format_fraction(val),
            }
        if pivots_used >= max_pivots:
            return {"status": "UNKNOWN", "code": "PIVOT_LIMIT"}
        leaving = -1
        min_ratio = None
        for i in range(m):
            d = tab[i + 1][e]
            if d > 0:
                ratio = tab[i + 1][-1] / d
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    leaving = i + 1
                elif ratio == min_ratio:
                    if basis[i] < basis[leaving - 1]:
                        leaving = i + 1
        if leaving == -1:
            x = [Fraction(0)] * n
            for i in range(m):
                b_var = basis[i]
                if b_var < n:
                    x[b_var] = tab[i + 1][-1]
            d = [Fraction(0)] * n
            if e < n:
                d[e] = Fraction(1)
            for i in range(m):
                b_var = basis[i]
                if b_var < n:
                    d[b_var] += -tab[i + 1][e]
            return {
                "status": "SOLVED",
                "kind": "UNBOUNDED",
                "x": [format_fraction(v) for v in x],
                "ray": [format_fraction(v) for v in d],
            }
        piv = tab[leaving][e]
        tab[leaving] = [v / piv for v in tab[leaving]]
        for i in range(m + 1):
            if i != leaving:
                fac = tab[i][e]
                if fac != 0:
                    tab[i] = [
                        tab[i][col] - fac * tab[leaving][col] for col in range(total_vars + 1)
                    ]
        basis[leaving - 1] = e
        pivots_used += 1
