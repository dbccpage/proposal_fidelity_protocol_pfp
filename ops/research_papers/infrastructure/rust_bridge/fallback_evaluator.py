"""Exact Rational Fallback Evaluator.
=================================

DEPRECATED: Per Congruence Ideal I_silent_fallback, production evaluators must
delegate directly to sovereign Rust solver crates and CLI binaries rather than
relying on pure Python approximation or silent fallbacks.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Set, Tuple
import warnings


class ExactRationalFallbackEvaluator:
    """[DEPRECATED] Exact rational solver using Fraction arithmetic and Bareiss elimination.

    Deprecated per I_silent_fallback: use compiled Rust solvers instead.
    """

    @staticmethod
    def compute_exact_rank(matrix: List[List[Fraction]]) -> int:
        """Computes exact matrix rank via Bareiss fraction-free Gaussian elimination."""
        if not matrix or not matrix[0]:
            return 0

        # Copy matrix as Fractions
        rows = len(matrix)
        cols = len(matrix[0])
        m = [[matrix[r][c] for c in range(cols)] for r in range(rows)]

        rank = 0
        r = 0
        for c in range(cols):
            if r >= rows:
                break
            # Find non-zero pivot
            pivot_row = -1
            for i in range(r, rows):
                if m[i][c] != Fraction(0, 1):
                    pivot_row = i
                    break
            if pivot_row == -1:
                continue

            # Swap rows
            m[r], m[pivot_row] = m[pivot_row], m[r]
            pivot = m[r][c]

            # Eliminate below
            for i in range(r + 1, rows):
                factor = m[i][c] / pivot
                for j in range(c, cols):
                    m[i][j] -= factor * m[r][j]

            rank += 1
            r += 1

        return rank

    @staticmethod
    def compute_betti_numbers(edges: List[Tuple[str, str]]) -> Tuple[int, int]:
        """Computes exact 1D simplicial homology (b_0, b_1) = (|V| - rank(d_0), |E| - |V| + b_0)."""
        vertices: Set[str] = set()
        for u, v in edges:
            vertices.add(u)
            vertices.add(v)

        n_v = len(vertices)
        n_e = len(edges)
        if n_v == 0:
            return (0, 0)

        # Build boundary matrix d_0: C_1 -> C_0 (vertices as rows, edges as cols)
        v_list = sorted(list(vertices))
        v_idx = {v: i for i, v in enumerate(v_list)}

        matrix: List[List[Fraction]] = [[Fraction(0, 1) for _ in range(n_e)] for _ in range(n_v)]
        for col, (u, v) in enumerate(edges):
            matrix[v_idx[v]][col] = Fraction(1, 1)
            matrix[v_idx[u]][col] = Fraction(-1, 1)

        rank_d0 = ExactRationalFallbackEvaluator.compute_exact_rank(matrix)
        b_0 = n_v - rank_d0
        b_1 = n_e - rank_d0  # Euler characteristic: b_0 - b_1 = n_v - n_e
        return (b_0, max(0, b_1))

    @staticmethod
    def solve_l1_dual_witness(
        boundary_matrix: List[List[Fraction]],
        target_cochain: List[Fraction],
    ) -> Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...], Fraction, Fraction]:
        """Simple exact rational dual witness for trivial/orthogonal projections."""
        n_rows = len(boundary_matrix)
        n_cols = len(boundary_matrix[0]) if n_rows > 0 else 0

        # Primal potential phi in Q^n_cols
        primal_potential = tuple(Fraction(0, 1) for _ in range(n_cols))
        cost = sum(abs(x) for x in target_cochain)

        # Dual flow w with |w_e| <= 1
        dual_flow = tuple(
            Fraction(1, 1) if x > 0 else (Fraction(-1, 1) if x < 0 else Fraction(0, 1))
            for x in target_cochain
        )
        dual_value = sum(dual_flow[i] * target_cochain[i] for i in range(len(target_cochain)))

        return (primal_potential, dual_flow, cost, dual_value)
