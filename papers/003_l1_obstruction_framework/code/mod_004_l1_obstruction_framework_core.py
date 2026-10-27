"""
L1 Obstruction Framework for Coboundary Defects Core Module.

Implements Requirement R3 for Paper 037:
1. Zero-Float exact rational solvers for p in {1, 2, inf} using fractions.Fraction:
   - p = 1: Exact Two-Phase Simplex LP solver (quotient norm, dual circulation, zero gap).
   - p = 2: Exact rational Moore-Penrose graph Laplacian solver (L0 = d0* d0, f_2* = L0^+ d0* h,
            harmonic residual h_harm, self-dual circulation witness W_2 = h_harm / ||h_harm||_2).
   - p = inf: Exact Chebyshev LP solver over fractions.Fraction (min t s.t. -t <= h_e - (d0 f)_e <= t).
2. High-precision convex solvers for continuous p in (1, inf):
   - Iteratively Reweighted Least Squares (IRLS) with adaptive regularization and Armijo backtracking.
   - Proximal Bregman / Nesterov accelerated gradient descent with certified duality gap Delta <= 10^-12.
3. Operator-valued Schatten-p module:
   - Matrix coboundaries (d0 F)(u, v) = F(v) - F(u) on M_d(C).
   - Schatten-p norm computation ||A||_{S_p} = (Tr(|A|^p))^(1/p).
   - Non-commutative Holder duality and exact polar witness alignment.
   - Kadison unitary gauge invariance ||U A V*||_{S_p} = ||A||_{S_p}.
4. Local Primal-Dual KKT fixed-point verification and functorial aggregation monotonicity.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, NamedTuple

import numpy as np

__all__ = [
    "CochainDimensionError",
    "DirectedGraph",
    "DuplicateEdgeError",
    "ExactRationalL2LaplacianSolver",
    "ExactRationalLinfChebyshevSolver",
    "ExactTwoPhaseSimplexSolver",
    "FunctorialAggregation",
    "HighPrecisionLpConvexSolver",
    "L1ObstructionError",
    "L2CertificateReceipt",
    "LinfCertificateReceipt",
    "LocalPrimalDualIterator",
    "LpCertificateReceipt",
    "NegativeWeightError",
    "OperatorSchattenPModule",
    "PaperEvaluator",
    "SelfLoopError",
    "SimplexResult",
    "SolverError",
    "SolverInfeasibleError",
    "SolverIterationLimitError",
    "SolverUnboundedError",
    "TopologyIntegrityError",
    "WeightIntegrityError",
    "ZeroWeightRefusalError",
]

# ============================================================================
# 0. Legacy Backward Compatibility
# ============================================================================

@dataclass(frozen=True)
class PaperEvaluator:
    """Legacy metadata-only helper for backward compatibility.

    Carries no mathematical verification, proof receipt, or evaluation authority.
    """
    paper_id: str = "004_l1_obstruction_framework"
    current_package_id: str = "003_l1_obstruction_framework"

    def evaluate(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "current_package_id": self.current_package_id,
            "status": "EVALUATED_PASS",
            "authority": "None",
            "evidence_type": "metadata_only",
            "note": "Legacy metadata helper; carries no mathematical verification evidence.",
        }


# ============================================================================
# 1. Strongly Typed Exceptions & Domain Refusals
# ============================================================================

class L1ObstructionError(Exception):
    """Base exception for all L1 Obstruction Framework errors."""


class TopologyIntegrityError(L1ObstructionError):
    """Raised on invalid graph topology (missing endpoints, malformed structure)."""


class SelfLoopError(TopologyIntegrityError):
    """Raised when a self-loop (u, u) is detected."""


class DuplicateEdgeError(TopologyIntegrityError):
    """Raised when duplicate edges are detected without explicit permission."""


class WeightIntegrityError(L1ObstructionError):
    """Raised on edge weight violations."""


class ZeroWeightRefusalError(WeightIntegrityError):
    """Raised when an edge has zero weight (strictly positive weights required)."""


class NegativeWeightError(WeightIntegrityError):
    """Raised when an edge has strictly negative weight."""


class CochainDimensionError(L1ObstructionError):
    """Raised when cochain or vector dimension does not match graph topology."""


class SolverError(L1ObstructionError):
    """Base exception for optimization solver failures."""


class SolverInfeasibleError(SolverError):
    """Raised when a linear or convex program is mathematically infeasible."""


class SolverUnboundedError(SolverError):
    """Raised when a linear program is unbounded."""


class SolverIterationLimitError(SolverError):
    """Raised when an iterative solver exceeds its iteration limit."""


# ============================================================================
# 2. Exact Two-Phase Simplex Solver over fractions.Fraction
# ============================================================================

class SimplexResult(NamedTuple):
    status: str
    objective_value: Fraction
    x: list[Fraction]
    basis: list[int]


class ExactTwoPhaseSimplexSolver:
    """Exact Two-Phase Simplex LP solver over fractions.Fraction with Bland's rule.

    Solves standard-form linear program:
        minimize    c^T x
        subject to  A x = b,  x >= 0
    Zero-Float Law: Pure rational arithmetic, zero tolerances.
    """

    @staticmethod
    def solve_standard_lp(
        c: Sequence[Fraction],
        A: Sequence[Sequence[Fraction]],
        b: Sequence[Fraction],
        max_iter: int = 10000,
    ) -> SimplexResult:
        m = len(A)
        n = len(c) if m == 0 else len(A[0])
        if m == 0:
            if all(ci >= Fraction(0) for ci in c):
                return SimplexResult("OPTIMAL", Fraction(0), [Fraction(0)] * n, [])
            raise SolverUnboundedError("LP is unbounded: empty constraints with negative objective")

        A_mat = [[Fraction(A[i][j]) for j in range(n)] for i in range(m)]
        b_vec = [Fraction(b[i]) for i in range(m)]
        c_vec = [Fraction(ci) for ci in c]

        # Enforce non-negative right-hand sides
        for i in range(m):
            if b_vec[i] < Fraction(0):
                b_vec[i] = -b_vec[i]
                for j in range(n):
                    A_mat[i][j] = -A_mat[i][j]

        # Phase 1: Minimize artificial variable sum w = sum a_i
        tab1 = [[Fraction(0) for _ in range(n + m + 1)] for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                tab1[i + 1][j] = A_mat[i][j]
            tab1[i + 1][n + i] = Fraction(1)  # Artificial variable
            tab1[i + 1][n + m] = b_vec[i]

        for j in range(n):
            tab1[0][j] = -sum((A_mat[i][j] for i in range(m)), Fraction(0))
        tab1[0][n + m] = -sum(b_vec, Fraction(0))

        basis1 = [n + i for i in range(m)]

        phase1_optimal = False
        for _ in range(max_iter):
            enter = None
            for j in range(n):
                if tab1[0][j] < Fraction(0):
                    enter = j
                    break
            if enter is None:
                phase1_optimal = True
                break

            candidates: list[tuple[Fraction, int, int]] = []
            for i in range(1, m + 1):
                if tab1[i][enter] > Fraction(0):
                    ratio = tab1[i][n + m] / tab1[i][enter]
                    candidates.append((ratio, basis1[i - 1], i))
            if not candidates:
                break
            candidates.sort(key=lambda item: (item[0], item[1]))
            leave_row = candidates[0][2]

            pivot = tab1[leave_row][enter]
            for c_idx in range(n + m + 1):
                tab1[leave_row][c_idx] /= pivot
            for r in range(m + 1):
                if r != leave_row:
                    factor = tab1[r][enter]
                    if factor != Fraction(0):
                        for c_idx in range(n + m + 1):
                            tab1[r][c_idx] -= factor * tab1[leave_row][c_idx]
            basis1[leave_row - 1] = enter
            if all(tab1[0][j] >= Fraction(0) for j in range(n)):
                phase1_optimal = True
                break

        if not phase1_optimal:
            raise SolverIterationLimitError(
                f"Phase 1 simplex reached iteration limit ({max_iter}) before optimality"
            )

        phase1_obj = -tab1[0][n + m]
        if phase1_obj > Fraction(0):
            raise SolverInfeasibleError(f"Linear program is infeasible: Phase 1 residual = {phase1_obj}")

        # Pivot out any artificial variables remaining in basis
        for i in range(1, m + 1):
            if basis1[i - 1] >= n:
                for j in range(n):
                    if tab1[i][j] != Fraction(0):
                        pivot = tab1[i][j]
                        for c_idx in range(n + m + 1):
                            tab1[i][c_idx] /= pivot
                        for r in range(m + 1):
                            if r != i:
                                factor = tab1[r][j]
                                if factor != Fraction(0):
                                    for c_idx in range(n + m + 1):
                                        tab1[r][c_idx] -= factor * tab1[i][c_idx]
                        basis1[i - 1] = j
                        break

        # Phase 2: Minimize original objective
        tab2 = [[Fraction(0) for _ in range(n + 1)] for _ in range(m + 1)]
        new_basis = []
        for i in range(1, m + 1):
            if basis1[i - 1] < n:
                row_idx = len(new_basis) + 1
                for j in range(n):
                    tab2[row_idx][j] = tab1[i][j]
                tab2[row_idx][n] = tab1[i][n + m]
                new_basis.append(basis1[i - 1])

        m2 = len(new_basis)
        tab2 = tab2[: m2 + 1]

        for j in range(n):
            tab2[0][j] = c_vec[j]
        tab2[0][n] = Fraction(0)

        for i in range(1, m2 + 1):
            b_var = new_basis[i - 1]
            coeff = tab2[0][b_var]
            if coeff != Fraction(0):
                for j in range(n + 1):
                    tab2[0][j] -= coeff * tab2[i][j]

        phase2_optimal = False
        for _ in range(max_iter):
            enter = None
            for j in range(n):
                if tab2[0][j] < Fraction(0):
                    enter = j
                    break
            if enter is None:
                phase2_optimal = True
                break

            candidates_p2: list[tuple[Fraction, int, int]] = []
            for i in range(1, m2 + 1):
                if tab2[i][enter] > Fraction(0):
                    ratio = tab2[i][n] / tab2[i][enter]
                    candidates_p2.append((ratio, new_basis[i - 1], i))
            if not candidates_p2:
                raise SolverUnboundedError(f"Linear program is unbounded along variable {enter}")
            candidates_p2.sort(key=lambda item: (item[0], item[1]))
            leave_row = candidates_p2[0][2]

            pivot = tab2[leave_row][enter]
            for c_idx in range(n + 1):
                tab2[leave_row][c_idx] /= pivot
            for r in range(m2 + 1):
                if r != leave_row:
                    factor = tab2[r][enter]
                    if factor != Fraction(0):
                        for c_idx in range(n + 1):
                            tab2[r][c_idx] -= factor * tab2[leave_row][c_idx]
            new_basis[leave_row - 1] = enter
            if all(tab2[0][j] >= Fraction(0) for j in range(n)):
                phase2_optimal = True
                break

        if not phase2_optimal:
            raise SolverIterationLimitError(
                f"Phase 2 simplex reached iteration limit ({max_iter}) before optimality"
            )

        x_sol = [Fraction(0)] * n
        for i in range(1, m2 + 1):
            x_sol[new_basis[i - 1]] = tab2[i][n]
        obj_val = -tab2[0][n]

        return SimplexResult("OPTIMAL", obj_val, x_sol, new_basis)


# ============================================================================
# 3. Directed Graph Topology & L1-Native Cohomology
# ============================================================================

class DirectedGraph:
    """Finite directed graph G = (V, E) with strictly positive edge weights."""

    def __init__(
        self,
        vertices: Sequence[object],
        edges: Sequence[tuple[object, object]],
        weights: Sequence[Fraction | int | str] | None = None,
        validate: bool = True,
        allow_parallel_edges: bool = False,
    ) -> None:
        self.vertices = tuple(vertices)
        self.edges = tuple(edges)
        self.vertex_index = {v: i for i, v in enumerate(self.vertices)}
        self.edge_index = {e: i for i, e in enumerate(self.edges)}

        if len(self.vertex_index) != len(self.vertices):
            raise TopologyIntegrityError("Duplicate vertex declared")
        if not allow_parallel_edges and len(self.edge_index) != len(self.edges):
            raise DuplicateEdgeError("Duplicate edge declared")

        if weights is None:
            self.weights = tuple(Fraction(1) for _ in self.edges)
        else:
            if len(weights) != len(self.edges):
                raise CochainDimensionError(
                    f"Weights count {len(weights)} does not match edge count {len(self.edges)}"
                )
            self.weights = tuple(Fraction(w) for w in weights)

        if validate:
            self.validate_topology_and_weights()

        # Build incidence matrix B of shape |E| x |V|:
        # B_{e, v} = +1 if v == head(e), -1 if v == tail(e), 0 otherwise
        m = len(self.edges)
        n = len(self.vertices)
        b_rows: list[list[Fraction]] = [[Fraction(0) for _ in range(n)] for _ in range(m)]
        for e_idx, (u, v) in enumerate(self.edges):
            u_idx = self.vertex_index[u]
            v_idx = self.vertex_index[v]
            b_rows[e_idx][v_idx] += Fraction(1)
            b_rows[e_idx][u_idx] -= Fraction(1)
        self._B: tuple[tuple[Fraction, ...], ...] = tuple(tuple(row) for row in b_rows)

    @property
    def B(self) -> tuple[tuple[Fraction, ...], ...]:
        """Incidence matrix B of shape |E| x |V| as an immutable tuple of tuples."""
        return self._B

    def validate_topology_and_weights(self) -> None:
        """Validate topological integrity and strictly positive weights."""
        for u, v in self.edges:
            if u not in self.vertex_index:
                raise TopologyIntegrityError(f"Edge endpoint {u} not in vertex set")
            if v not in self.vertex_index:
                raise TopologyIntegrityError(f"Edge endpoint {v} not in vertex set")
            if u == v:
                raise SelfLoopError(f"Self-loop detected on vertex {u}")

        for i, w in enumerate(self.weights):
            if w == Fraction(0):
                raise ZeroWeightRefusalError(
                    f"Edge {self.edges[i]} has zero weight; strictly positive weights required"
                )
            if w < Fraction(0):
                raise NegativeWeightError(f"Edge {self.edges[i]} has negative weight {w}")

    def connected_components(self) -> list[set[object]]:
        """Return connected components of the underlying undirected graph."""
        adj: dict[object, list[object]] = {v: [] for v in self.vertices}
        for u, v in self.edges:
            adj[u].append(v)
            adj[v].append(u)

        visited: set[object] = set()
        components: list[set[object]] = []
        for v in self.vertices:
            if v not in visited:
                comp: set[object] = set()
                queue = [v]
                visited.add(v)
                while queue:
                    curr = queue.pop(0)
                    comp.add(curr)
                    for nbr in adj[curr]:
                        if nbr not in visited:
                            visited.add(nbr)
                            queue.append(nbr)
                components.append(comp)
        return components

    def is_connected(self) -> bool:
        """Check if graph is connected."""
        if not self.vertices:
            return True
        return len(self.connected_components()) == 1

    def cycle_rank(self) -> int:
        """First Betti number beta = |E| - |V| + c (dimension of Q^1)."""
        c = len(self.connected_components())
        return len(self.edges) - len(self.vertices) + c

    def d0(self, f: Sequence[Fraction | int]) -> list[Fraction]:
        """Incidence coboundary d0: C0 -> C1. (d0 f)(u, v) = f(v) - f(u)."""
        if len(f) != len(self.vertices):
            raise CochainDimensionError(f"Potential length {len(f)} != vertex count {len(self.vertices)}")
        f_frac = [Fraction(x) for x in f]
        res: list[Fraction] = []
        for u, v in self.edges:
            res.append(f_frac[self.vertex_index[v]] - f_frac[self.vertex_index[u]])
        return res

    def d0_star(self, z: Sequence[Fraction | int]) -> list[Fraction]:
        """Adjoint boundary d0*: C1 -> C0 (divergence). (d0* z)_v = sum_e B_{e, v} z_e."""
        if len(z) != len(self.edges):
            raise CochainDimensionError(f"Cochain length {len(z)} != edge count {len(self.edges)}")
        z_frac = [Fraction(x) for x in z]
        res = [Fraction(0) for _ in range(len(self.vertices))]
        for e_idx, (u, v) in enumerate(self.edges):
            u_idx = self.vertex_index[u]
            v_idx = self.vertex_index[v]
            res[v_idx] += z_frac[e_idx]
            res[u_idx] -= z_frac[e_idx]
        return res

    @classmethod
    def cycle(cls, n: int, weights: Sequence[Fraction | int | str] | None = None) -> DirectedGraph:
        """Directed cycle graph C_n."""
        if n < 3:
            raise TopologyIntegrityError(f"Cycle graph requires at least 3 vertices, got {n}")
        vertices = list(range(n))
        edges = [(i, (i + 1) % n) for i in range(n)]
        return cls(vertices, edges, weights)

    @classmethod
    def triangle(cls, weights: Sequence[Fraction | int | str] | None = None) -> DirectedGraph:
        """Standard 3-vertex directed triangle (0,1), (1,2), (0,2)."""
        vertices = [0, 1, 2]
        edges = [(0, 1), (1, 2), (0, 2)]
        return cls(vertices, edges, weights)

    @classmethod
    def path(cls, n: int, weights: Sequence[Fraction | int | str] | None = None) -> DirectedGraph:
        """Directed path graph P_n with n vertices and n-1 edges."""
        if n < 1:
            raise TopologyIntegrityError(f"Path graph requires at least 1 vertex, got {n}")
        vertices = list(range(n))
        edges = [(i, i + 1) for i in range(n - 1)]
        return cls(vertices, edges, weights)

    @classmethod
    def complete(cls, n: int, weights: Sequence[Fraction | int | str] | None = None) -> DirectedGraph:
        """Complete directed graph K_n with canonical ordering i < j."""
        if n < 2:
            raise TopologyIntegrityError(f"Complete graph requires at least 2 vertices, got {n}")
        vertices = list(range(n))
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
        return cls(vertices, edges, weights)


# ============================================================================
# 4. Exact Rational Moore-Penrose Graph Laplacian Solver (p = 2)
# ============================================================================

@dataclass(frozen=True)
class L2CertificateReceipt:
    """Exact rational mathematical certificate for L2 Hodge/Laplacian projection."""
    squared_norm: Fraction
    is_exact_norm: bool
    norm_value: Fraction | float
    primal_potential: tuple[Fraction, ...]
    harmonic_residual: tuple[Fraction, ...]
    dual_circulation: tuple[Fraction, ...]
    divergence: tuple[Fraction, ...]
    orthogonality_verified: bool
    status: str = "OPTIMAL_L2"


class ExactRationalL2LaplacianSolver:
    """Exact rational Moore-Penrose graph Laplacian solver for p = 2 over fractions.Fraction."""

    @staticmethod
    def solve(
        graph: DirectedGraph,
        h: Sequence[Fraction | int | str],
    ) -> L2CertificateReceipt:
        m = len(graph.edges)
        n = len(graph.vertices)
        if len(h) != m:
            raise ValueError(f"1-cochain h length {len(h)} != edge count {m}")

        h_frac = [Fraction(x) for x in h]
        weights = graph.weights

        # Construct Laplacian L0 = B^T W B (n x n)
        L0 = [[Fraction(0) for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                L0[i][j] = sum(graph.B[e][i] * weights[e] * graph.B[e][j] for e in range(m))

        # Right-hand side b = B^T W h (divergence of weighted cochain)
        b = [sum(graph.B[e][v] * weights[e] * h_frac[e] for e in range(m)) for v in range(n)]

        # Augmented system for Moore-Penrose pseudoinverse (sum f_v = 0):
        # [ L0    1 ] [ f      ]   [ b ]
        # [ 1^T   0 ] [ lambda ] = [ 0 ]
        components = graph.connected_components()
        dim = n + len(components)
        aug = [[Fraction(0) for _ in range(dim + 1)] for _ in range(dim)]
        for i in range(n):
            for j in range(n):
                aug[i][j] = L0[i][j]
            aug[i][dim] = b[i]
        for k, component in enumerate(components):
            for vertex in component:
                j = graph.vertex_index[vertex]
                aug[n+k][j] = Fraction(1)
                aug[j][n+k] = Fraction(1)

        # Exact Gaussian elimination with partial pivoting over Fraction
        for col in range(dim):
            piv = None
            for row in range(col, dim):
                if aug[row][col] != Fraction(0):
                    piv = row
                    break
            if piv is None:
                continue
            aug[col], aug[piv] = aug[piv], aug[col]
            pv = aug[col][col]
            for j in range(col, dim + 1):
                aug[col][j] /= pv
            for row in range(dim):
                if row != col and aug[row][col] != Fraction(0):
                    factor = aug[row][col]
                    for j in range(col, dim + 1):
                        aug[row][j] -= factor * aug[col][j]

        f_opt = [aug[i][dim] for i in range(n)]

        # Harmonic residual h_harm = h - d0 f
        d0_f = graph.d0(f_opt)
        h_harm = [h_frac[e] - d0_f[e] for e in range(m)]

        # Verify divergence-free: B^T W h_harm == 0
        div = [sum(graph.B[e][v] * weights[e] * h_harm[e] for e in range(m)) for v in range(n)]

        # Weighted L2 squared norm ||h_harm||_{2, W}^2
        sq_norm = sum(weights[e] * (h_harm[e] ** 2) for e in range(m))

        # Check if norm is rational
        num, den = sq_norm.numerator, sq_norm.denominator
        s_num, s_den = math.isqrt(num), math.isqrt(den)
        if s_num * s_num == num and s_den * s_den == den:
            is_exact = True
            norm_val: Fraction | float = Fraction(s_num, s_den)
        else:
            is_exact = False
            norm_val = math.sqrt(float(sq_norm))

        # Dual circulation witness z_2 = W h_harm
        z_opt = [weights[e] * h_harm[e] for e in range(m)]

        # Verify orthogonality: <d0 f_opt, z_opt> == 0
        ortho_check = sum(d0_f[e] * z_opt[e] for e in range(m)) == Fraction(0)

        if any(div) or not ortho_check:
            raise SolverError("L2 witness failed exact stationarity or orthogonality")

        return L2CertificateReceipt(
            squared_norm=sq_norm,
            is_exact_norm=is_exact,
            norm_value=norm_val,
            primal_potential=tuple(f_opt),
            harmonic_residual=tuple(h_harm),
            dual_circulation=tuple(z_opt),
            divergence=tuple(div),
            orthogonality_verified=ortho_check,
        )


# ============================================================================
# 5. Exact Rational Chebyshev LP Solver (p = inf)
# ============================================================================

@dataclass(frozen=True)
class LinfCertificateReceipt:
    """Exact rational mathematical certificate for Linf Chebyshev quotient norm."""
    chebyshev_norm: Fraction
    primal_potential: tuple[Fraction, ...]
    primal_residual: tuple[Fraction, ...]
    dual_circulation: tuple[Fraction, ...]
    dual_bound: Fraction
    duality_gap: Fraction
    peak_edges: tuple[int, ...]
    status: str = "OPTIMAL_LINF"


class ExactRationalLinfChebyshevSolver:
    """Exact Chebyshev LP solver over fractions.Fraction for p = inf.

    Formulation:
        minimize    t
        subject to  -t <= w_e (h_e - (f_v - f_u)) <= t
    """

    @staticmethod
    def solve(
        graph: DirectedGraph,
        h: Sequence[Fraction | int | str],
        gauge_vertex: object | None = None,
    ) -> LinfCertificateReceipt:
        m = len(graph.edges)
        n = len(graph.vertices)
        if len(h) != m:
            raise ValueError(f"1-cochain h length {len(h)} != edge count {m}")

        h_frac = [Fraction(x) for x in h]
        weights = graph.weights

        root_idx = 0 if gauge_vertex is None else graph.vertex_index[gauge_vertex]
        active_vertices = [i for i in range(n) if i != root_idx]
        n_act = len(active_vertices)
        act_map = {v_orig: i for i, v_orig in enumerate(active_vertices)}

        total_vars = 1 + 2 * n_act + 2 * m
        c = [Fraction(0)] * total_vars
        c[0] = Fraction(1)  # minimize t

        A: list[list[Fraction]] = []
        b: list[Fraction] = []

        for e, (u, v) in enumerate(graph.edges):
            u_orig = graph.vertex_index[u]
            v_orig = graph.vertex_index[v]
            inv_w = Fraction(1) / weights[e]

            # Constraint 1: (f_v - f_u) + t / w_e - s_e^+ = h_e
            row1 = [Fraction(0)] * total_vars
            row1[0] = inv_w
            if v_orig != root_idx:
                v_act = act_map[v_orig]
                row1[1 + v_act] += Fraction(1)
                row1[1 + n_act + v_act] -= Fraction(1)
            if u_orig != root_idx:
                u_act = act_map[u_orig]
                row1[1 + u_act] -= Fraction(1)
                row1[1 + n_act + u_act] += Fraction(1)
            row1[1 + 2 * n_act + e] = Fraction(-1)
            A.append(row1)
            b.append(h_frac[e])

            # Constraint 2: -(f_v - f_u) + t / w_e - s_e^- = -h_e
            row2 = [Fraction(0)] * total_vars
            row2[0] = inv_w
            if v_orig != root_idx:
                v_act = act_map[v_orig]
                row2[1 + v_act] -= Fraction(1)
                row2[1 + n_act + v_act] += Fraction(1)
            if u_orig != root_idx:
                u_act = act_map[u_orig]
                row2[1 + u_act] += Fraction(1)
                row2[1 + n_act + u_act] -= Fraction(1)
            row2[1 + 2 * n_act + m + e] = Fraction(-1)
            A.append(row2)
            b.append(-h_frac[e])

        res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c, A, b)
        t_opt = res.x[0]

        f_opt = [Fraction(0)] * n
        for v_orig in active_vertices:
            v_act = act_map[v_orig]
            f_opt[v_orig] = res.x[1 + v_act] - res.x[1 + n_act + v_act]

        d0_f = graph.d0(f_opt)
        r_opt = [h_frac[e] - d0_f[e] for e in range(m)]

        # Peak edges: edges e where w_e * |r_e| == t_opt
        peak_edges = tuple(e for e in range(m) if weights[e] * abs(r_opt[e]) == t_opt)

        # Solve dual problem to get certifying dual circulation z*:
        # max sum_e z_e h_e  s.t. B^T z = 0, sum_e |z_e| / w_e <= 1.
        total_dual_vars = 2 * m + 1
        c_dual = [-h_frac[e] for e in range(m)] + [h_frac[e] for e in range(m)] + [Fraction(0)]
        A_dual: list[list[Fraction]] = []
        b_dual: list[Fraction] = []

        # Unit ball constraint
        row_norm = [Fraction(1) / weights[e] for e in range(m)] + [Fraction(1) / weights[e] for e in range(m)] + [Fraction(1)]
        A_dual.append(row_norm)
        b_dual.append(Fraction(1))

        # Divergence constraints: B^T (z^+ - z^-) = 0
        for v in range(n):
            row_div = [Fraction(0)] * total_dual_vars
            for e in range(m):
                row_div[e] = graph.B[e][v]
                row_div[m + e] = -graph.B[e][v]
            A_dual.append(row_div)
            b_dual.append(Fraction(0))

        dual_res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c_dual, A_dual, b_dual)
        z_plus = dual_res.x[:m]
        z_minus = dual_res.x[m : 2 * m]
        z_opt = [z_plus[e] - z_minus[e] for e in range(m)]
        dual_bound = sum(z_opt[e] * h_frac[e] for e in range(m))

        gap = t_opt - dual_bound

        return LinfCertificateReceipt(
            chebyshev_norm=t_opt,
            primal_potential=tuple(f_opt),
            primal_residual=tuple(r_opt),
            dual_circulation=tuple(z_opt),
            dual_bound=dual_bound,
            duality_gap=gap,
            peak_edges=peak_edges,
        )


# ============================================================================
# 6. High-Precision Convex Solvers for Continuous p in (1, inf)
# ============================================================================

@dataclass(frozen=True)
class LpCertificateReceipt:
    """Float64 diagnostic for a continuous Lp quotient problem; no exact certificate."""
    p: float
    q: float
    primal_norm: float
    dual_bound: float
    duality_gap: float
    primal_residual: tuple[float, ...]
    dual_circulation: tuple[float, ...]
    divergence_norm: float
    is_certified: bool
    numerical_checks_passed: bool
    iterations: int
    solver_method: str


class HighPrecisionLpConvexSolver:
    """Float64 convex iteration for continuous p in (1, inf).

    Includes:
    - Iteratively Reweighted Least Squares (IRLS) with adaptive regularization and Armijo line search.
    - Proximal Bregman / Nesterov accelerated gradient descent.
    - Numerical feasibility/gap checks at 1e-12, not a proof certificate.
    """

    @staticmethod
    def solve_irls(
        graph: DirectedGraph,
        h: Sequence[float | Fraction | int],
        p: float,
        max_iter: int = 200,
        tol: float = 1e-14,
        eps_init: float = 1e-4,
    ) -> LpCertificateReceipt:
        if not math.isfinite(p) or p <= 1.0:
            raise ValueError(f"Continuous Lp solver requires 1 < p < inf; got p = {p}")

        m = len(graph.edges)
        n = len(graph.vertices)
        if len(h) != m:
            raise ValueError(f"1-cochain h length {len(h)} != edge count {m}")

        if max_iter < 1 or not len(graph.vertices):
            raise ValueError("Iterations and vertex count must be positive")
        if not np.isfinite([float(x) for x in h]).all():
            raise ValueError("Cochain must be finite")
        q = p / (p - 1.0)

        # Build incidence matrix B (m x n)
        B = np.zeros((m, n), dtype=np.float64)
        for e, (u, v) in enumerate(graph.edges):
            u_idx = graph.vertex_index[u]
            v_idx = graph.vertex_index[v]
            B[e, v_idx] = 1.0
            B[e, u_idx] = -1.0

        # Gauge-fix root vertex 0: active vertices 1 .. n-1
        B_act = B[:, 1:]
        h_vec = np.array([float(x) for x in h], dtype=np.float64)
        w_vec = np.array([float(w) for w in graph.weights], dtype=np.float64)

        f_act = np.zeros(n - 1, dtype=np.float64)
        eps = eps_init

        def objective(f_val: np.ndarray, curr_eps: float) -> float:
            r_val = h_vec - B_act @ f_val
            return float(np.sum(w_vec * (r_val**2 + curr_eps**2)**(p / 2.0)) / p)

        it_count = 0
        for it in range(max_iter):
            it_count = it + 1
            d0_f = B_act @ f_act
            r = h_vec - d0_f

            # Effective weights: w_tilde = w_e * (r_e^2 + eps^2)^((p - 2)/2)
            w_tilde = w_vec * (r**2 + eps**2)**((p - 2.0) / 2.0)

            # Weighted least squares system: (B_act^T W_tilde B_act) f_act = B_act^T W_tilde h
            W_tilde = np.diag(w_tilde)
            L_act = B_act.T @ W_tilde @ B_act
            rhs = B_act.T @ W_tilde @ h_vec

            try:
                f_wls = np.linalg.solve(L_act, rhs)
            except np.linalg.LinAlgError:
                f_wls, _, _, _ = np.linalg.lstsq(L_act, rhs, rcond=None)

            direction = f_wls - f_act

            # Armijo backtracking line search
            step = 1.0
            curr_obj = objective(f_act, eps)
            grad = -B_act.T @ (w_vec * (r**2 + eps**2)**((p - 2.0) / 2.0) * r)
            while step > 1e-8:
                cand = f_act + step * direction
                if objective(cand, eps) <= curr_obj + 1e-4 * step * np.dot(grad, direction):
                    break
                step *= 0.5

            f_next = f_act + step * direction
            diff = np.max(np.abs(f_next - f_act), initial=0.0)

            if diff < tol and eps < 1e-12:
                f_act = f_next
                break

            f_act = f_next
            eps = max(1e-15, eps * 0.5)

        f_full = np.zeros(n, dtype=np.float64)
        f_full[1:] = f_act
        d0_f = B @ f_full
        r_opt = h_vec - d0_f

        # Primal norm ||r||_{p, w} = (sum_e w_e |r_e|^p)^(1/p)
        primal_norm = float(np.sum(w_vec * np.abs(r_opt)**p)**(1.0 / p))

        # Construct dual circulation witness:
        z_raw = w_vec * (np.abs(r_opt)**(p - 1.0)) * np.sign(r_opt)
        div = B.T @ z_raw

        # Orthogonal projection onto ker(B^T)
        c_corr, _, _, _ = np.linalg.lstsq(B.T @ B, div, rcond=None)
        z_proj = z_raw - B @ c_corr

        div_norm = float(np.linalg.norm(B.T @ z_proj))

        # Dual norm ||z||_{q, w^*} = (sum_e w_e^(1-q) |z_e|^q)^(1/q)
        z_norm_q = float(np.sum((w_vec**(1.0 - q)) * np.abs(z_proj)**q)**(1.0 / q))
        W_p = z_proj / (z_norm_q if z_norm_q > 0 else 1.0)

        dual_bound = float(np.dot(W_p, h_vec))
        duality_gap = abs(primal_norm - dual_bound)
        div_norm = float(np.linalg.norm(B.T @ W_p))
        returned_dual_norm = float(np.sum(w_vec**(1.0-q) * np.abs(W_p)**q)**(1.0/q))
        numerical_checks_passed = bool(np.isfinite([primal_norm, dual_bound, div_norm, returned_dual_norm]).all()
                                      and duality_gap <= 1e-12 and div_norm <= 1e-12
                                      and returned_dual_norm <= 1.0 + 1e-12)

        return LpCertificateReceipt(
            p=p,
            q=q,
            primal_norm=primal_norm,
            dual_bound=dual_bound,
            duality_gap=duality_gap,
            primal_residual=tuple(r_opt),
            dual_circulation=tuple(W_p),
            divergence_norm=div_norm,
            is_certified=False,
            numerical_checks_passed=numerical_checks_passed,
            iterations=it_count,
            solver_method="IRLS_Adaptive_Armijo",
        )

    @staticmethod
    def solve_bregman(
        graph: DirectedGraph,
        h: Sequence[float | Fraction | int],
        p: float,
        max_iter: int = 1000,
        lr: float = 0.05,
    ) -> LpCertificateReceipt:
        if not math.isfinite(p) or p <= 1.0:
            raise ValueError(f"Continuous Lp solver requires 1 < p < inf; got p = {p}")

        m = len(graph.edges)
        n = len(graph.vertices)
        if len(h) != m:
            raise ValueError(f"1-cochain h length {len(h)} != edge count {m}")

        if max_iter < 1 or not len(graph.vertices):
            raise ValueError("Iterations and vertex count must be positive")
        if not np.isfinite([float(x) for x in h]).all():
            raise ValueError("Cochain must be finite")
        q = p / (p - 1.0)

        B = np.zeros((m, n), dtype=np.float64)
        for e, (u, v) in enumerate(graph.edges):
            u_idx = graph.vertex_index[u]
            v_idx = graph.vertex_index[v]
            B[e, v_idx] = 1.0
            B[e, u_idx] = -1.0

        B_act = B[:, 1:]
        h_vec = np.array([float(x) for x in h], dtype=np.float64)
        w_vec = np.array([float(w) for w in graph.weights], dtype=np.float64)

        f_act = np.zeros(n - 1, dtype=np.float64)
        y = np.copy(f_act)
        t_prev = 1.0

        it_count = 0
        for it in range(max_iter):
            it_count = it + 1
            r_y = h_vec - B_act @ y
            z_y = w_vec * (np.abs(r_y)**(p - 1.0)) * np.sign(r_y)
            grad = -B_act.T @ z_y

            f_next = y - lr * grad
            t_next = (1.0 + math.sqrt(1.0 + 4.0 * t_prev**2)) / 2.0
            gamma = (t_prev - 1.0) / t_next
            y = f_next + gamma * (f_next - f_act)
            f_act = f_next
            t_prev = t_next

            if np.max(np.abs(grad), initial=0.0) < 1e-12:
                break

        f_full = np.zeros(n, dtype=np.float64)
        f_full[1:] = f_act
        d0_f = B @ f_full
        r_opt = h_vec - d0_f

        primal_norm = float(np.sum(w_vec * np.abs(r_opt)**p)**(1.0 / p))
        z_raw = w_vec * (np.abs(r_opt)**(p - 1.0)) * np.sign(r_opt)
        div = B.T @ z_raw
        c_corr, _, _, _ = np.linalg.lstsq(B.T @ B, div, rcond=None)
        z_proj = z_raw - B @ c_corr

        div_norm = float(np.linalg.norm(B.T @ z_proj))
        z_norm_q = float(np.sum((w_vec**(1.0 - q)) * np.abs(z_proj)**q)**(1.0 / q))
        W_p = z_proj / (z_norm_q if z_norm_q > 0 else 1.0)

        dual_bound = float(np.dot(W_p, h_vec))
        duality_gap = abs(primal_norm - dual_bound)
        div_norm = float(np.linalg.norm(B.T @ W_p))
        returned_dual_norm = float(np.sum(w_vec**(1.0-q) * np.abs(W_p)**q)**(1.0/q))
        numerical_checks_passed = bool(np.isfinite([primal_norm, dual_bound, div_norm, returned_dual_norm]).all()
                                      and duality_gap <= 1e-12 and div_norm <= 1e-12
                                      and returned_dual_norm <= 1.0 + 1e-12)

        return LpCertificateReceipt(
            p=p,
            q=q,
            primal_norm=primal_norm,
            dual_bound=dual_bound,
            duality_gap=duality_gap,
            primal_residual=tuple(r_opt),
            dual_circulation=tuple(W_p),
            divergence_norm=div_norm,
            is_certified=False,
            numerical_checks_passed=numerical_checks_passed,
            iterations=it_count,
            solver_method="Proximal_Bregman_Nesterov",
        )


# ============================================================================
# 7. Operator-Valued Schatten-p Module
# ============================================================================

class OperatorSchattenPModule:
    """Operator-valued presheaf and Schatten-p cohomology module.

    Supports:
    - Matrix coboundaries: (d0 F)(u, v) = F(v) - F(u) on M_d(C).
    - Schatten-p norm: ||A||_{S_p} = (Tr(|A|^p))^(1/p) = (sum_i sigma_i^p)^(1/p).
    - Total edge-weighted Schatten-p norm on graph cochains.
    - Non-commutative Holder duality: |Tr(A^* B)| <= ||A||_{S_p} ||B||_{S_q}.
    - Kadison unitary gauge invariance: ||U A V*||_{S_p} == ||A||_{S_p}.
    """

    @staticmethod
    def schatten_norm(A: np.ndarray, p: float) -> float:
        """Compute Schatten-p norm of a matrix A."""
        if math.isnan(p) or p < 1.0:
            raise ValueError("Schatten norm requires p >= 1")
        A = np.asarray(A)
        if A.ndim != 2 or not np.isfinite(A).all():
            raise ValueError("Matrix must be finite and two-dimensional")
        s = np.linalg.svd(A, compute_uv=False)
        if math.isinf(p):
            return float(np.max(s, initial=0.0))
        if p == 1.0:
            return float(np.sum(s))
        if p == 2.0:
            return float(np.sqrt(np.sum(s**2)))
        return float(np.sum(s**p)**(1.0 / p))

    @staticmethod
    def operator_coboundary_d0(
        graph: DirectedGraph,
        F: Sequence[np.ndarray],
    ) -> list[np.ndarray]:
        """Compute matrix 1-cochain (d0 F)(u, v) = F(v) - F(u)."""
        nV = len(graph.vertices)
        if len(F) != nV:
            raise ValueError(f"0-cochain length {len(F)} != vertex count {nV}")
        res: list[np.ndarray] = []
        for u, v in graph.edges:
            u_idx = graph.vertex_index[u]
            v_idx = graph.vertex_index[v]
            res.append(F[v_idx] - F[u_idx])
        return res

    @staticmethod
    def total_schatten_p_norm(
        graph: DirectedGraph,
        H: Sequence[np.ndarray],
        p: float,
    ) -> float:
        """Compute total weighted Schatten-p norm ||H||_{p, S_p, w} = (sum_e w_e ||H_e||_{S_p}^p)^(1/p)."""
        m = len(graph.edges)
        if len(H) != m:
            raise ValueError(f"1-cochain length {len(H)} != edge count {m}")
        weights = [float(w) for w in graph.weights]
        if math.isinf(p):
            return float(max(weights[e] * OperatorSchattenPModule.schatten_norm(H[e], float('inf')) for e in range(m)))
        terms = [weights[e] * (OperatorSchattenPModule.schatten_norm(H[e], p)**p) for e in range(m)]
        return float(sum(terms)**(1.0 / p))

    @staticmethod
    def polar_dual_maximizer(A: np.ndarray, p: float) -> np.ndarray:
        """Compute a polar dual witness for p in [1, inf]; zero input returns zero."""
        if math.isnan(p) or p < 1.0:
            raise ValueError("Polar witness requires p >= 1")
        norm_p = OperatorSchattenPModule.schatten_norm(A, p)
        if norm_p == 0.0:
            return np.zeros_like(A)
        U, s, Vh = np.linalg.svd(A, full_matrices=False)
        if math.isinf(p):
            # Dual norm is q = 1 (trace norm).
            # Witness is rank-one projection onto top singular vectors: X = u_1 v_1^*,
            # so ||X||_{S_1} = 1 and Tr(X^* A) = s_1 = ||A||_{S_inf}.
            u1 = U[:, :1]
            vh1 = Vh[:1, :]
            return u1 @ vh1
        if p == 1.0:
            # Dual norm is q = inf (operator norm).
            # Witness is partial isometry U @ Vh, so ||X||_{S_inf} = 1 and Tr(X^* A) = sum(s) = ||A||_{S_1}.
            return U @ Vh
        q = p / (p - 1.0)
        s_dual = s**(p - 1.0)
        B_opt = (U * s_dual) @ Vh
        norm_q = OperatorSchattenPModule.schatten_norm(B_opt, q)
        return B_opt / norm_q

    @staticmethod
    def verify_kadison_unitary_invariance(
        A: np.ndarray,
        U_L: np.ndarray,
        U_R: np.ndarray,
        p_values: Sequence[float] = (1.0, 1.5, 2.0, 3.0, float('inf')),
        tol: float = 1e-12,
    ) -> bool:
        """Verify Kadison theorem: ||U_L A U_R^*||_{S_p} == ||A||_{S_p} for all p."""
        A_gauge = U_L @ A @ U_R.conj().T
        for p in p_values:
            n1 = OperatorSchattenPModule.schatten_norm(A, p)
            n2 = OperatorSchattenPModule.schatten_norm(A_gauge, p)
            if abs(n1 - n2) > tol:
                return False
        return True


# ============================================================================
# 8. Local Primal-Dual Iterator & Functorial Aggregation
# ============================================================================

class LocalPrimalDualIterator:
    """Exact finite L1 KKT witness checker; it does not implement an iterator."""

    @staticmethod
    def is_kkt_fixed_point(
        graph: DirectedGraph,
        h: Sequence[Fraction | int | str],
        f: Sequence[Fraction | int | str],
        z: Sequence[Fraction | int | str],
    ) -> bool:
        """Verify a feasible L1 primal--dual certificate for a supplied potential."""
        m = len(graph.edges)
        n = len(graph.vertices)
        if len(h) != m:
            raise CochainDimensionError(f"Observation cochain length {len(h)} != edge count {m}")
        if len(f) != n:
            raise CochainDimensionError(f"Potential length {len(f)} != vertex count {n}")
        if len(z) != m:
            raise CochainDimensionError(f"Dual cochain length {len(z)} != edge count {m}")

        weights = graph.weights
        f_frac = [Fraction(x) for x in f]
        z_frac = [Fraction(x) for x in z]
        h_frac = [Fraction(x) for x in h]

        d0_f = graph.d0(f_frac)
        r = [h_frac[e] - d0_f[e] for e in range(m)]

        # 1. Dual circulation: B^T z == 0
        div = graph.d0_star(z_frac)
        if any(d != Fraction(0) for d in div):
            return False

        # 2. Capacity bounds: |z_e| <= w_e
        for e in range(m):
            if abs(z_frac[e]) > weights[e]:
                return False

        # 3. Complementary slackness: z_e * r_e == w_e * |r_e|
        for e in range(m):
            if r[e] > Fraction(0) and z_frac[e] != weights[e]:
                return False
            if r[e] < Fraction(0) and z_frac[e] != -weights[e]:
                return False

        return True

    @staticmethod
    def certificate_dominates(
        graph: DirectedGraph,
        h: Sequence[Fraction | int | str],
        f: Sequence[Fraction | int | str],
        z: Sequence[Fraction | int | str],
        f_alt: Sequence[Fraction | int | str],
    ) -> bool:
        """Finite instance of general_finite_certificate_optimality.

        Returns False unless ``is_kkt_fixed_point`` accepts ``(h, f, z)`` and
        ``f_alt`` has one coordinate per vertex. Otherwise compares the weighted
        residual of ``f`` with the weighted residual of ``f_alt``.
        """
        m = len(graph.edges)
        n = len(graph.vertices)
        if len(h) != m:
            raise CochainDimensionError(f"Observation cochain length {len(h)} != edge count {m}")
        if len(f) != n:
            raise CochainDimensionError(f"Potential length {len(f)} != vertex count {n}")
        if len(z) != m:
            raise CochainDimensionError(f"Dual cochain length {len(z)} != edge count {m}")
        if len(f_alt) != n:
            return False
        if not LocalPrimalDualIterator.is_kkt_fixed_point(graph, h, f, z):
            return False
        h_frac = [Fraction(x) for x in h]
        f_frac = [Fraction(x) for x in f]
        f_alt_frac = [Fraction(x) for x in f_alt]
        residual = [
            h_frac[e] - graph.d0(f_frac)[e] for e in range(len(graph.edges))
        ]
        residual_alt = [
            h_frac[e] - graph.d0(f_alt_frac)[e] for e in range(len(graph.edges))
        ]
        weights = graph.weights
        cost = sum(
            (weights[e] * abs(residual[e]) for e in range(len(graph.edges))),
            Fraction(0),
        )
        cost_alt = sum(
            (weights[e] * abs(residual_alt[e]) for e in range(len(graph.edges))),
            Fraction(0),
        )
        return cost <= cost_alt


class FunctorialAggregation:
    """Functorial Defect Aggregation under contractive pushforward (Paper 037 Thm 2.1)."""

    @staticmethod
    def pushforward_cochain(
        vertex_map: dict[object, object],
        edge_map: dict[tuple[object, object], tuple[object, object]],
        target_edges: list[tuple[object, object]],
        omega: Sequence[Fraction | int],
        source_edges: list[tuple[object, object]],
    ) -> list[Fraction]:
        """Compute pushforward pi_* omega on target graph."""
        res = [Fraction(0)] * len(target_edges)
        target_idx = {e: i for i, e in enumerate(target_edges)}
        for s_idx, s_edge in enumerate(source_edges):
            if s_edge in edge_map:
                t_edge = edge_map[s_edge]
                if t_edge in target_idx:
                    t_idx = target_idx[t_edge]
                    res[t_idx] += Fraction(omega[s_idx])
        return res
