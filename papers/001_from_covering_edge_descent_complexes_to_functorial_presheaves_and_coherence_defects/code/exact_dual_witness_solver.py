"""Exact primal-dual L1 gauge solver for PO-001.

AuthorityEffect: None.

This module implements the finite obstruction calculus
primal-dual L1 gauge distance solver:
    Phi_1([H]) := min_{T in C^1(P, Hom)} ||H - delta_1 T||_{1, w}
and certifies exact zero duality gap via rational dual witness certificates:
    max_{Y in C^2(P, Hom)^*} <Y, H>  s.t.  (delta_1)^*(Y) = 0, ||Y||_{infty, w^*} <= 1.

Key structural properties:
1. Exact rational arithmetic: all linear program pivots and inner products use
   fractions.Fraction, ensuring zero floating-point approximation error.
2. Primal-dual certificate totality: by strong linear programming duality,
   duality_gap = primal_value - dual_value == 0 identically.
3. Dual cocycle certification: the dual witness Y* satisfies (delta_1)^*(Y*) == 0,
   meaning <Y*, delta_1 T> == 0 for all 1-cochains T.
4. Dual subgradient bound: |Y^*_i| <= w_i for all components, certifying that Y*
   lies strictly inside the dual L_infty unit ball.
5. Inward clean architecture: depends only on covering_edge_poset, exact, exactsym,
   cohomology_quotient, and restriction_system.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple, Union

from covering_edge_poset import FinitePoset, NodeId
from exact import exact_equal
from exactsym import Matrix
from restriction_system import RestrictionSystem
from cohomology_quotient import (
    Operator1Cochain,
    Operator2Cochain,
    OperatorCochainImageDiagnostic,
    operator_coboundary_delta1,
    build_curvature_operator_cochain,
)


@dataclass(frozen=True)
class DualWitnessCertificate:
    """Exact rational primal-dual witness certificate for L1 gauge distance.

    Holds the primal optimal gauge T*, optimal residual R* = H - delta_1 T*,
    and dual witness cochain Y* pricing the obstruction distance Phi_1([H]).
    """

    poset: FinitePoset
    primal_value: Fraction
    dual_value: Fraction
    duality_gap: Fraction
    is_zero_gap: bool
    optimal_gauge_t: Operator1Cochain
    optimal_residual: Operator2Cochain
    dual_witness_y: Operator2Cochain
    weights: List[Fraction]
    iterations: int
    is_cocycle_certified: bool
    is_subgradient_certified: bool

    def summary(self) -> Dict[str, Any]:
        """Return a structured summary of the certificate."""
        return {
            "primal_value": str(self.primal_value),
            "dual_value": str(self.dual_value),
            "duality_gap": str(self.duality_gap),
            "is_zero_gap": self.is_zero_gap,
            "iterations": self.iterations,
            "is_cocycle_certified": self.is_cocycle_certified,
            "is_subgradient_certified": self.is_subgradient_certified,
            "residual_is_zero": self.optimal_residual.is_zero(),
        }


def cochain1_from_vector(
    diagnostic: OperatorCochainImageDiagnostic,
    vec: List[Fraction],
) -> Operator1Cochain:
    """Reconstruct an Operator1Cochain from a 1D rational vector.

    The vector ordering matches the column definition in compute_coboundary_matrix_delta1:
    iterating over pairs (a, b) in diagnostic.pairs, then row r in [0, dim_a),
    then col c in [0, dim_b).
    """
    idx = 0
    ops: Dict[Tuple[NodeId, NodeId], Matrix] = {}
    for a, b in diagnostic.pairs:
        rows = diagnostic.system.fiber_dimensions[a]
        cols = diagnostic.system.fiber_dimensions[b]
        data: List[List[Fraction]] = []
        for _ in range(rows):
            row: List[Fraction] = []
            for _ in range(cols):
                row.append(vec[idx])
                idx += 1
            data.append(row)
        ops[(a, b)] = Matrix(data)
    return Operator1Cochain(poset=diagnostic.poset, operators=ops)


def cochain1_to_vector(
    diagnostic: OperatorCochainImageDiagnostic,
    t: Operator1Cochain,
) -> List[Fraction]:
    """Flatten an Operator1Cochain into a 1D rational vector matching column order."""
    vec: List[Fraction] = []
    for a, b in diagnostic.pairs:
        mat = t(a, b)
        for r in range(mat.rows):
            for c in range(mat.cols):
                vec.append(Fraction(mat[r, c]))
    return vec


def solve_l1_primal_dual_exact(
    m_rows: List[List[Fraction]],
    b: List[Fraction],
    w: Optional[List[Fraction]] = None,
    max_iter: int = 5000,
) -> Tuple[Fraction, Fraction, List[Fraction], List[Fraction], int]:
    """Solve min_gamma ||b - M gamma||_{1, w} over Q via exact rational simplex LP.

    Standard form formulation:
        min sum_{i=1}^m w_i (p_i + n_i)
        s.t. M gamma^+ - M gamma^- + p - n = b
             gamma^+, gamma^-, p, n >= 0

    Returns:
        (primal_value, dual_value, gamma_optimal, y_optimal, iterations)
    """
    m = len(b)
    k = len(m_rows[0]) if m > 0 and len(m_rows) > 0 else 0

    if w is None:
        w = [Fraction(1) for _ in range(m)]
    else:
        if len(w) != m:
            raise ValueError(f"Weights length {len(w)} does not match row dimension {m}")
        for wi in w:
            if wi <= 0:
                raise ValueError("All weights must be strictly positive rational numbers")

    if m == 0:
        return Fraction(0), Fraction(0), [Fraction(0)] * k, [], 0

    if k == 0:
        # Zero degrees of freedom: gamma is empty, residual is b itself.
        primal_val = sum(w[i] * abs(b[i]) for i in range(m))
        y = [w[i] if b[i] > 0 else (-w[i] if b[i] < 0 else Fraction(0)) for i in range(m)]
        dual_val = sum(b[i] * y[i] for i in range(m))
        return primal_val, dual_val, [], y, 0

    n_vars = 2 * k + 2 * m
    sigma: List[Fraction] = []
    basis: List[int] = []

    # Tableau shape: (m + 1) rows, (n_vars + 1) cols
    tableau: List[List[Fraction]] = [[Fraction(0) for _ in range(n_vars + 1)] for _ in range(m + 1)]

    for i in range(m):
        if b[i] >= 0:
            sigma.append(Fraction(1))
            basis.append(2 * k + i)  # p_i
            rhs = b[i]
        else:
            sigma.append(Fraction(-1))
            basis.append(2 * k + m + i)  # n_i
            rhs = -b[i]

        row = i + 1
        tableau[row][n_vars] = rhs

        # gamma^+ and gamma^- columns
        for j in range(k):
            val = sigma[i] * m_rows[i][j]
            tableau[row][j] = val
            tableau[row][k + j] = -val

        # p columns
        for p_idx in range(m):
            tableau[row][2 * k + p_idx] = sigma[i] if p_idx == i else Fraction(0)

        # n columns
        for n_idx in range(m):
            tableau[row][2 * k + m + n_idx] = -sigma[i] if n_idx == i else Fraction(0)

    # Cost vector
    c = [Fraction(0)] * (2 * k) + list(w) + list(w)

    # Initial reduced costs (row 0): r_j = c_j - sum_i c_{B[i]} * A_{norm}[i][j]
    for j in range(n_vars):
        cb_dot_a = sum(w[i] * tableau[i + 1][j] for i in range(m))
        tableau[0][j] = c[j] - cb_dot_a

    # Simplex pivots using Bland's rule (smallest subscript)
    it = 0
    while it < max_iter:
        it += 1

        # 1. Entering variable: smallest index j with reduced cost < 0
        entering = -1
        for j in range(n_vars):
            if tableau[0][j] < 0:
                entering = j
                break

        if entering == -1:
            # Optimal basis reached
            break

        # 2. Leaving variable: min-ratio test with Bland's tie breaking
        best_ratio: Optional[Fraction] = None
        pivot_row = -1
        for i in range(m):
            coeff = tableau[i + 1][entering]
            if coeff > 0:
                ratio = tableau[i + 1][n_vars] / coeff
                if best_ratio is None or ratio < best_ratio:
                    best_ratio = ratio
                    pivot_row = i + 1
                elif ratio == best_ratio:
                    if basis[i] < basis[pivot_row - 1]:
                        pivot_row = i + 1

        if pivot_row == -1:
            raise RuntimeError("Unbounded linear program encountered (incompatible with L1 geometry)")

        # 3. Pivot Gauss-Jordan step
        pivot_val = tableau[pivot_row][entering]
        for col in range(n_vars + 1):
            tableau[pivot_row][col] /= pivot_val

        for r in range(m + 1):
            if r != pivot_row:
                factor = tableau[r][entering]
                if factor != 0:
                    for col in range(n_vars + 1):
                        tableau[r][col] -= factor * tableau[pivot_row][col]

        basis[pivot_row - 1] = entering
    else:
        raise RuntimeError(f"Exact simplex did not converge within {max_iter} iterations")

    # Extract primal solution
    x = [Fraction(0)] * n_vars
    for i in range(m):
        x[basis[i]] = tableau[i + 1][n_vars]

    gamma = [x[j] - x[k + j] for j in range(k)]
    p = [x[2 * k + i] for i in range(m)]
    n = [x[2 * k + m + i] for i in range(m)]

    primal_val = sum(w[i] * (p[i] + n[i]) for i in range(m))

    # Dual variables: y_i = w_i - r_{p_i} where r_{p_i} is tableau[0][2k + i]
    y = [w[i] - tableau[0][2 * k + i] for i in range(m)]
    dual_val = sum(b[i] * y[i] for i in range(m))

    return primal_val, dual_val, gamma, y, it


class ExactDualWitnessSolver:
    """Exact rational primal-dual solver for finite obstruction calculus gauge distance.

    Computes:
        Phi_1([H]) := min_T ||H - delta_1 T||_{1, w}
    and constructs a DualWitnessCertificate verifying zero duality gap over Q.
    """

    def __init__(
        self,
        system: RestrictionSystem,
        weights: Optional[Union[List[Fraction], Dict[Tuple[NodeId, NodeId, NodeId], Fraction]]] = None,
    ) -> None:
        self.system = system
        self.poset = system.poset
        self.diagnostic = OperatorCochainImageDiagnostic(system)

        # Parse weights
        m = self.diagnostic.c2_dim
        if weights is None:
            self.weights = [Fraction(1) for _ in range(m)]
        elif isinstance(weights, list):
            if len(weights) != m:
                raise ValueError(f"Weight vector length {len(weights)} != C^2 dimension {m}")
            self.weights = [Fraction(wi) for wi in weights]
        elif isinstance(weights, dict):
            # Map dictionary over triples to flat vector
            w_list: List[Fraction] = []
            for a, b, c in self.diagnostic.triples:
                w_triple = Fraction(weights.get((a, b, c), Fraction(1)))
                dim_a = self.system.fiber_dimensions[a]
                dim_c = self.system.fiber_dimensions[c]
                for _ in range(dim_a * dim_c):
                    w_list.append(w_triple)
            self.weights = w_list
        else:
            raise TypeError("weights must be None, List[Fraction], or Dict[triple, Fraction]")

        # Coboundary matrix of delta_1: C^1 -> C^2
        self.m_matrix = self.diagnostic.compute_coboundary_matrix_delta1()
        self.m_rows: List[List[Fraction]] = [
            [Fraction(self.m_matrix[r, c]) for c in range(self.m_matrix.cols)]
            for r in range(self.m_matrix.rows)
        ]

    def solve(self, h: Optional[Operator2Cochain] = None) -> DualWitnessCertificate:
        """Solve the primal-dual L1 gauge problem for 2-cochain h (default: curvature K)."""
        if h is None:
            h = build_curvature_operator_cochain(self.system)

        b_vec = self.diagnostic.cochain2_to_vector(h)

        primal_val, dual_val, gamma, y, it = solve_l1_primal_dual_exact(
            self.m_rows,
            b_vec,
            self.weights,
        )

        duality_gap = primal_val - dual_val
        is_zero_gap = (duality_gap == Fraction(0))

        # Reconstruct optimal gauge T*
        t_optimal = cochain1_from_vector(self.diagnostic, gamma)

        # Compute delta_1(T*) and residual R* = H - delta_1(T*)
        delta1_t = operator_coboundary_delta1(self.system, t_optimal)
        residual = h - delta1_t

        # Reconstruct dual witness 2-cochain Y*
        y_optimal = self.diagnostic.vector_to_cochain2(y)

        # Verify dual cocycle condition: (delta_1)^*(Y*) == 0 <=> M^T y == 0
        is_cocycle_certified = True
        k = len(gamma)
        m = len(b_vec)
        for j in range(k):
            m_t_y_j = sum(self.m_rows[i][j] * y[i] for i in range(m))
            if m_t_y_j != Fraction(0):
                is_cocycle_certified = False
                break

        # Verify dual subgradient condition: |y_i| <= w_i
        is_subgradient_certified = True
        for i in range(m):
            if abs(y[i]) > self.weights[i]:
                is_subgradient_certified = False
                break

        return DualWitnessCertificate(
            poset=self.poset,
            primal_value=primal_val,
            dual_value=dual_val,
            duality_gap=duality_gap,
            is_zero_gap=is_zero_gap,
            optimal_gauge_t=t_optimal,
            optimal_residual=residual,
            dual_witness_y=y_optimal,
            weights=self.weights,
            iterations=it,
            is_cocycle_certified=is_cocycle_certified,
            is_subgradient_certified=is_subgradient_certified,
        )

    def compute_l1_gauge_distance(self, h: Optional[Operator2Cochain] = None) -> Fraction:
        """Return the exact rational L1 gauge distance Phi_1([H])."""
        cert = self.solve(h)
        return cert.primal_value


# Backward compatibility alias
ExactCodaL1Solver = ExactDualWitnessSolver


def compute_exact_gauge_distance(
    system: RestrictionSystem,
    weights: Optional[Union[List[Fraction], Dict[Tuple[NodeId, NodeId, NodeId], Fraction]]] = None,
) -> DualWitnessCertificate:
    """Convenience helper computing exact L1 gauge certificate for system curvature K."""
    solver = ExactDualWitnessSolver(system, weights=weights)
    return solver.solve()


# Backward compatibility alias
compute_exact_coda_gauge_distance = compute_exact_gauge_distance
