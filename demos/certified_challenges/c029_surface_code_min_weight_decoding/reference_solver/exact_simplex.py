# AuthorityEffect: None.
"""
Exact Two-Phase Rational Simplex Solver over Q for C029.

Solves linear programs:
    min c^T x
    subject to A x = b, x >= 0
in exact rational arithmetic (fractions.Fraction) with Bland's pivot rule.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Optional, Tuple


def format_fraction(f: Fraction) -> str:
    """Formats Fraction as string: '3' or '1/2'."""
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def parse_fraction(val: str | int | Fraction) -> Fraction:
    """Parses integer, string, or Fraction into Fraction."""
    if isinstance(val, Fraction):
        return val
    if isinstance(val, int):
        return Fraction(val, 1)
    return Fraction(val)


class ExactSimplex:
    """Two-phase exact rational simplex solver."""

    def __init__(self, c: List[Fraction], A: List[List[Fraction]], b: List[Fraction]) -> None:
        self.m = len(A)
        self.n = len(c)
        self.c = [parse_fraction(v) for v in c]
        self.A = [[parse_fraction(v) for v in row] for row in A]
        self.b = [parse_fraction(v) for v in b]

        # Ensure b >= 0
        for i in range(self.m):
            if self.b[i] < 0:
                self.b[i] = -self.b[i]
                self.A[i] = [-x for x in self.A[i]]

    def solve(self) -> Tuple[bool, Optional[Fraction], Optional[List[Fraction]]]:
        """
        Solves LP in exact rational arithmetic.
        Returns:
            (is_feasible, optimal_value, primal_solution)
        """
        m, n = self.m, self.n
        if m == 0 or n == 0:
            return True, Fraction(0), [Fraction(0)] * n

        # Tableau size: (m + 1) rows x (n + m + 1) columns
        tab = [[Fraction(0)] * (n + m + 1) for _ in range(m + 1)]
        basis = [n + i for i in range(m)]

        for i in range(m):
            for j in range(n):
                tab[i][j] = self.A[i][j]
            tab[i][n + i] = Fraction(1)
            tab[i][-1] = self.b[i]

        # Phase 1 cost row: - sum of rows for original variables, 0 for artificials
        for j in range(n):
            s = sum(tab[i][j] for i in range(m))
            tab[m][j] = -s
        for j in range(n, n + m):
            tab[m][j] = Fraction(0)
        tab[m][-1] = -sum(tab[i][-1] for i in range(m))

        def pivot(r: int, col: int) -> None:
            piv = tab[r][col]
            for j in range(len(tab[0])):
                tab[r][j] /= piv
            for i in range(len(tab)):
                if i != r and tab[i][col] != 0:
                    factor = tab[i][col]
                    for j in range(len(tab[0])):
                        tab[i][j] -= factor * tab[r][j]
            basis[r] = col

        # Phase 1 loop: only search among original variables (artificials must not re-enter)
        while True:
            # Bland's rule: first negative reduced cost
            c_enter = -1
            for j in range(n):
                if tab[m][j] < 0:
                    c_enter = j
                    break
            if c_enter == -1:
                break

            r_leave = -1
            min_ratio = None
            for i in range(m):
                if tab[i][c_enter] > 0:
                    ratio = tab[i][-1] / tab[i][c_enter]
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        r_leave = i
            if r_leave == -1:
                return False, None, None

            pivot(r_leave, c_enter)

        # Check phase 1 feasibility
        if tab[m][-1] != 0:
            return False, None, None

        # Drive any artificial variables out of basis if possible
        for i in range(m):
            if basis[i] >= n:
                for j in range(n):
                    if tab[i][j] != 0:
                        pivot(i, j)
                        break

        # Phase 2: drop artificial columns
        for i in range(m + 1):
            tab[i] = tab[i][:n] + [tab[i][-1]]

        # Compute cost row for phase 2
        for j in range(n):
            tab[m][j] = self.c[j]
        tab[m][-1] = Fraction(0)
        for i in range(m):
            b_var = basis[i]
            if b_var < n:
                cost_b = self.c[b_var]
                for j in range(n + 1):
                    tab[m][j] -= cost_b * tab[i][j]

        # Phase 2 loop
        while True:
            c_enter = -1
            for j in range(n):
                if tab[m][j] < 0:
                    c_enter = j
                    break
            if c_enter == -1:
                break

            r_leave = -1
            min_ratio = None
            for i in range(m):
                if tab[i][c_enter] > 0:
                    ratio = tab[i][-1] / tab[i][c_enter]
                    if min_ratio is None or ratio < min_ratio:
                        min_ratio = ratio
                        r_leave = i
            if r_leave == -1:
                return False, None, None  # Unbounded

            pivot(r_leave, c_enter)

        x = [Fraction(0)] * n
        for i in range(m):
            if basis[i] < n:
                x[basis[i]] = tab[i][-1]

        opt_val = -tab[m][-1]
        return True, opt_val, x
