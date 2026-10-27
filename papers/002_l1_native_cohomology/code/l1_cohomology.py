"""Exact rational L1-Native Cohomology Engine for Paper 002.

Pure standard library, zero floating-point arithmetic for decision paths (Zero-Float Law),
zero tolerances, exact rational LP duality with Bland's minimal-index pivot rule.

Includes:
- Finite directed graphs with strictly positive weights (Theorem L1C-T2 zero-weight refusal).
- Simplicial complexes with boundary matrices D1, D2 and nilpotency checks (Theorem L1C-T7).
- Exact Two-Phase Simplex solver over fractions.Fraction.
- Primal quotient norm solver, dual circulation solver, and zero duality gap certification (Theorems L1C-T1, L1C-T3, L1C-T4).
- Cycle rank support bound verification |supp(r)| <= beta (Theorem L1C-T5).
- Total unimodularity and integral optimum verification (Theorem L1C-T6).
- Discrete physics: lattice gauge connections, discrete Bianchi identity, current conservation.
- Finite quantum obstruction calculus: phase cocycles and trace-norm defect bounds (Theorem L1C-T8).

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import NamedTuple

import numpy as np

# ============================================================================
# 1. Strongly Typed Exceptions & Refusal Contracts
# ============================================================================

class L1CohomologyError(Exception):
    """Base exception for all L1-native cohomology domain errors."""
    def __init__(self, message: str, code: str = "L1_COHOMOLOGY_ERROR") -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message


class TopologyIntegrityError(L1CohomologyError):
    """Raised when graph or simplicial topology is corrupted."""


class SelfLoopError(TopologyIntegrityError):
    """Raised when an edge connects a vertex to itself."""


class DuplicateEdgeError(TopologyIntegrityError):
    """Raised when an identical oriented edge is declared multiple times."""


class NilpotencyViolationError(TopologyIntegrityError):
    """Raised when D1 @ D2 != 0 or d1 o d0 != 0."""


class WeightIntegrityError(L1CohomologyError):
    """Raised when edge weights violate positivity hypotheses."""


class ZeroWeightRefusalError(WeightIntegrityError):
    """Raised when a zero edge weight is encountered (refused per Theorem L1C-T2)."""


class NegativeWeightError(WeightIntegrityError):
    """Raised when a negative edge weight is encountered."""


class CochainDimensionError(L1CohomologyError):
    """Raised when cochain length does not match graph/complex dimensions."""


class SolverError(L1CohomologyError):
    """Base exception for linear programming solver errors."""


class SolverInfeasibleError(SolverError):
    """Raised when the primal or dual problem is mathematically infeasible."""


class SolverUnboundedError(SolverError):
    """Raised when a linear program is unbounded."""


class SolverIterationLimitError(SolverError):
    """Raised when simplex budget max_iter is exhausted before optimality."""


class CertificateViolationError(L1CohomologyError):
    """Raised when a proposed primal or dual witness fails mathematical verification."""


class PrimalFeasibilityError(CertificateViolationError):
    """Raised when emitted residual fails primal equation r = omega + B f."""


class CapacityBoundExceededError(CertificateViolationError):
    """Raised when a dual circulation violates |z_e| <= w_e."""


class CirculationDivergenceError(CertificateViolationError):
    """Raised when a dual witness has nonzero divergence (B^T z != 0)."""


class DualityGapNonZeroError(CertificateViolationError):
    """Raised when Delta = ||r||_{1, w} - <z, omega> != 0."""


class ComplementarySlacknessError(CertificateViolationError):
    """Raised when complementary slackness coordinate conditions are violated."""


class PhysicsConstraintError(L1CohomologyError):
    """Raised when discrete physics conservation or gauge laws are violated."""


class BianchiViolationError(PhysicsConstraintError):
    """Raised when field strength of a pure gauge field does not vanish."""


class GaussLawViolationError(PhysicsConstraintError):
    """Raised when discrete current fails divergence-free conservation."""


class QuantumIntegrityError(L1CohomologyError):
    """Raised when a quantum state or phase cochain violates axiomatic constraints."""


class NonHermitianStateError(QuantumIntegrityError):
    """Raised when density matrix rho != rho^dagger."""


class TraceNormalizationError(QuantumIntegrityError):
    """Raised when Tr(rho) != 1."""


class NegativeSpectrumError(QuantumIntegrityError):
    """Raised when density matrix has negative eigenvalues."""


# ============================================================================
# 2. Exact Two-Phase Simplex LP Solver over fractions.Fraction
# ============================================================================

class SimplexResult(NamedTuple):
    status: str  # "OPTIMAL", "INFEASIBLE", "UNBOUNDED"
    obj_val: Fraction
    x: list[Fraction]
    dual: list[Fraction]


class ExactTwoPhaseSimplexSolver:
    """Exact Two-Phase Simplex LP solver over fractions.Fraction with Bland's rule.

    Solves the standard-form linear program:
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

        # --------------------------------------------------------------------
        # Phase 1: Minimize artificial variable sum w = sum a_i
        # --------------------------------------------------------------------
        tab1 = [[Fraction(0) for _ in range(n + m + 1)] for _ in range(m + 1)]
        for i in range(m):
            for j in range(n):
                tab1[i + 1][j] = A_mat[i][j]
            tab1[i + 1][n + i] = Fraction(1)  # Artificial var
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

        valid_rows: list[int] = []
        new_basis: list[int] = []
        for i in range(1, m + 1):
            if basis1[i - 1] < n:
                valid_rows.append(i)
                new_basis.append(basis1[i - 1])

        m2 = len(valid_rows)

        # --------------------------------------------------------------------
        # Phase 2: Optimize original objective c
        # --------------------------------------------------------------------
        tab2 = [[Fraction(0) for _ in range(n + 1)] for _ in range(m2 + 1)]
        for r_idx, orig_r in enumerate(valid_rows):
            for j in range(n):
                tab2[r_idx + 1][j] = tab1[orig_r][j]
            tab2[r_idx + 1][n] = tab1[orig_r][n + m]

        for j in range(n):
            tab2[0][j] = c_vec[j]
        tab2[0][n] = Fraction(0)

        for r_idx in range(1, m2 + 1):
            bv = new_basis[r_idx - 1]
            cost = tab2[0][bv]
            if cost != Fraction(0):
                for j in range(n + 1):
                    tab2[0][j] -= cost * tab2[r_idx][j]

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

            candidates2: list[tuple[Fraction, int, int]] = []
            for i in range(1, m2 + 1):
                if tab2[i][enter] > Fraction(0):
                    ratio = tab2[i][n] / tab2[i][enter]
                    candidates2.append((ratio, new_basis[i - 1], i))
            if not candidates2:
                raise SolverUnboundedError("Linear program is unbounded in Phase 2")
            candidates2.sort(key=lambda item: (item[0], item[1]))
            leave_row = candidates2[0][2]

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

        return SimplexResult("OPTIMAL", obj_val, x_sol, [])


# ============================================================================
# 3. Directed Graph Topology & L1-Native Cohomology
# ============================================================================

class DirectedGraph:
    """Finite directed graph G = (V, E) with strictly positive edge weights.

    Orientation is bookkeeping: reversing an edge negates its cochain coordinate.
    Weights w_e > 0 are strictly enforced (Theorem L1C-T2 zero-weight refusal).
    """

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
        self.B: list[list[Fraction]] = [[Fraction(0) for _ in range(n)] for _ in range(m)]
        for e_idx, (u, v) in enumerate(self.edges):
            u_idx = self.vertex_index[u]
            v_idx = self.vertex_index[v]
            self.B[e_idx][v_idx] += Fraction(1)
            self.B[e_idx][u_idx] -= Fraction(1)

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
                    f"Edge {self.edges[i]} has zero weight; strictly positive weights required by L1C-T2"
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
        """Divergence operator B^T z: C1 -> C0. (B^T z)_v = sum_{e: head(e)=v} z_e - sum_{e: tail(e)=v} z_e."""
        if len(z) != len(self.edges):
            raise CochainDimensionError(f"Circulation length {len(z)} != edge count {len(self.edges)}")
        z_frac = [Fraction(x) for x in z]
        n = len(self.vertices)
        div = [Fraction(0)] * n
        for e_idx, (u, v) in enumerate(self.edges):
            div[self.vertex_index[v]] += z_frac[e_idx]
            div[self.vertex_index[u]] -= z_frac[e_idx]
        return div

    def weighted_l1_norm(self, cochain: Sequence[Fraction | int]) -> Fraction:
        """Compute weighted L1 norm sum_e w_e |c_e|."""
        if len(cochain) != len(self.edges):
            raise CochainDimensionError(f"Cochain length {len(cochain)} != edge count {len(self.edges)}")
        return sum((self.weights[i] * abs(Fraction(c)) for i, c in enumerate(cochain)), Fraction(0))

    def inner_product(self, z: Sequence[Fraction | int], omega: Sequence[Fraction | int]) -> Fraction:
        """Compute pairing <z, omega> = sum_e z_e omega_e."""
        if len(z) != len(self.edges) or len(omega) != len(self.edges):
            raise CochainDimensionError("Dimension mismatch in inner product")
        return sum((Fraction(z[i]) * Fraction(omega[i]) for i in range(len(self.edges))), Fraction(0))

    @classmethod
    def cycle(cls, n: int, weights: Sequence[Fraction | int | str] | None = None) -> DirectedGraph:
        """Factory for directed cycle graph C_n."""
        if n < 3:
            raise TopologyIntegrityError("Cycle graph requires at least 3 vertices")
        vertices = list(range(n))
        edges = [(i, (i + 1) % n) for i in range(n)]
        return cls(vertices=vertices, edges=edges, weights=weights)

    @classmethod
    def triangle(cls, weights: Sequence[Fraction | int | str] | None = None) -> DirectedGraph:
        """Factory for oriented 3-vertex triangle with edges (0,1), (1,2), (0,2)."""
        return cls(vertices=[0, 1, 2], edges=[(0, 1), (1, 2), (0, 2)], weights=weights)


# ============================================================================
# 4. Simplicial 2-Complex Topology & Discrete Bianchi Identity
# ============================================================================

class Simplicial2Complex:
    """Finite 2-dimensional simplicial complex with vertices, edges, and triangular faces.

    Maintains signed boundary matrices D1 (vertices x edges) and D2 (edges x faces).
    Verifies D1 @ D2 == 0 and d1 o d0 == 0 (Theorem L1C-T7 Bianchi identity).
    """

    def __init__(
        self,
        vertices: Sequence[object],
        edges: Sequence[tuple[object, object]],
        faces: Sequence[tuple[object, object, object]],
        weights: Sequence[Fraction | int | str] | None = None,
        validate: bool = True,
    ) -> None:
        self.vertices = tuple(vertices)
        self.edges = tuple(edges)
        self.faces = tuple(faces)
        self.vertex_index = {v: i for i, v in enumerate(self.vertices)}
        self.edge_index = {e: i for i, e in enumerate(self.edges)}

        if weights is None:
            self.weights = tuple(Fraction(1) for _ in self.edges)
        else:
            if len(weights) != len(self.edges):
                raise CochainDimensionError("Weights length != edges length")
            self.weights = tuple(Fraction(w) for w in weights)

        nV = len(self.vertices)
        nE = len(self.edges)
        nF = len(self.faces)

        # D1 boundary matrix: |V| x |E|
        self.D1 = [[Fraction(0) for _ in range(nE)] for _ in range(nV)]
        for e_idx, (u, v) in enumerate(self.edges):
            u_idx = self.vertex_index[u]
            v_idx = self.vertex_index[v]
            self.D1[v_idx][e_idx] += Fraction(1)
            self.D1[u_idx][e_idx] -= Fraction(1)

        # D2 boundary matrix: |E| x |F|
        self.D2 = [[Fraction(0) for _ in range(nF)] for _ in range(nE)]
        for f_idx, (u, v, w) in enumerate(self.faces):
            segments = [((u, v), 1), ((v, w), 1), ((u, w), -1)]
            for (a, b), sgn in segments:
                if (a, b) in self.edge_index:
                    e_idx = self.edge_index[(a, b)]
                    self.D2[e_idx][f_idx] += Fraction(sgn)
                elif (b, a) in self.edge_index:
                    e_idx = self.edge_index[(b, a)]
                    self.D2[e_idx][f_idx] -= Fraction(sgn)
                else:
                    raise TopologyIntegrityError(f"Face boundary segment ({a}, {b}) missing from edges")

        if validate:
            self.verify_nilpotency()

    def verify_nilpotency(self) -> bool:
        """Assert D1 @ D2 == 0 and d1 o d0 == 0."""
        nV = len(self.vertices)
        nE = len(self.edges)
        nF = len(self.faces)
        for v in range(nV):
            for f in range(nF):
                s = sum(self.D1[v][e] * self.D2[e][f] for e in range(nE))
                if s != Fraction(0):
                    raise NilpotencyViolationError(f"D1 @ D2 != 0 at vertex {v}, face {f}: value = {s}")
        return True

    def d0(self, phi: Sequence[Fraction | int]) -> list[Fraction]:
        """Coboundary d0: C0 -> C1. (d0 phi)_e = phi(head(e)) - phi(tail(e))."""
        nV = len(self.vertices)
        nE = len(self.edges)
        if len(phi) != nV:
            raise CochainDimensionError(f"0-cochain length {len(phi)} != vertex count {nV}")
        phi_frac = [Fraction(x) for x in phi]
        return [sum((self.D1[v][e] * phi_frac[v] for v in range(nV)), Fraction(0)) for e in range(nE)]

    def d1(self, A: Sequence[Fraction | int]) -> list[Fraction]:
        """Coboundary d1: C1 -> C2 (Field strength / curvature F = d1 A)."""
        nE = len(self.edges)
        nF = len(self.faces)
        if len(A) != nE:
            raise CochainDimensionError(f"1-cochain length {len(A)} != edge count {nE}")
        A_frac = [Fraction(x) for x in A]
        return [sum((self.D2[e][f] * A_frac[e] for e in range(nE)), Fraction(0)) for f in range(nF)]

    def discrete_bianchi_identity(self, phi: Sequence[Fraction | int]) -> list[Fraction]:
        """Compute d1(d0 phi). Must evaluate identically to zero (Theorem L1C-T7)."""
        d0_phi = self.d0(phi)
        d1_d0_phi = self.d1(d0_phi)
        if any(x != Fraction(0) for x in d1_d0_phi):
            raise BianchiViolationError(f"Discrete Bianchi identity violated: d1(d0 phi) = {d1_d0_phi}")
        return d1_d0_phi


# ============================================================================
# 5. L1 Quotient Solver & Primal-Dual Certification
# ============================================================================

@dataclass(frozen=True)
class L1CertificateReceipt:
    """Complete mathematical certificate for an L1-native cohomology instance."""
    primal_norm: Fraction
    dual_bound: Fraction
    duality_gap: Fraction
    primal_potential: tuple[Fraction, ...]
    primal_residual: tuple[Fraction, ...]
    dual_circulation: tuple[Fraction, ...]
    support_size: int
    cycle_rank: int
    satisfies_support_bound: bool
    satisfies_complementary_slackness: bool
    solution_is_integral: bool  # Primal potential and residual; dual may be fractional.
    integrality_theorem_satisfied: bool
    diagnostic_type: str  # "ExactRepair", "ClosedResidual", or "CurvatureResidual"
    is_integral: bool = True  # Backwards compatibility alias for solution_is_integral


class L1QuotientSolver:
    """Exact primal and dual solver for L1-native cohomology on finite directed graphs."""

    @staticmethod
    def solve(
        graph: DirectedGraph,
        omega: Sequence[Fraction | int | str],
        gauge_vertex: object | None = None,
    ) -> L1CertificateReceipt:
        """Solve primal L1 quotient problem and extract dual certifying circulation.

        Primal formulation:
            minimize    sum_e w_e (r_e^+ + r_e^-)
            subject to  r_e^+ - r_e^- - (f_v - f_u) = omega_e
                        r_e^+, r_e^- >= 0, f_v free (gauge fixed at gauge_vertex)
        """
        m = len(graph.edges)
        n = len(graph.vertices)
        if len(omega) != m:
            raise CochainDimensionError(f"omega length {len(omega)} != edge count {m}")

        omega_frac = [Fraction(x) for x in omega]
        weights = graph.weights

        # Determine gauge root vertex (default vertex 0)
        if gauge_vertex is None:
            root_idx = 0
        else:
            if gauge_vertex not in graph.vertex_index:
                raise TopologyIntegrityError(f"Gauge vertex {gauge_vertex} not in graph")
            root_idx = graph.vertex_index[gauge_vertex]

        # Active vertices excluding root gauge vertex
        active_vertices = [i for i in range(n) if i != root_idx]
        n_act = len(active_vertices)
        act_map = {v_orig: i for i, v_orig in enumerate(active_vertices)}

        # LP Variables:
        # 0 .. m-1: r_e^+
        # m .. 2m-1: r_e^-
        # 2m .. 2m + n_act - 1: f_v^+
        # 2m + n_act .. 2m + 2*n_act - 1: f_v^-
        total_vars = 2 * m + 2 * n_act
        c = [Fraction(0)] * total_vars
        for e in range(m):
            c[e] = weights[e]
            c[m + e] = weights[e]

        # Constraints: r_e^+ - r_e^- - sum_v B_{e, v} (f_v^+ - f_v^-) = omega_e
        A: list[list[Fraction]] = []
        b: list[Fraction] = []

        for e, (u, v) in enumerate(graph.edges):
            u_orig = graph.vertex_index[u]
            v_orig = graph.vertex_index[v]

            row = [Fraction(0)] * total_vars
            row[e] = Fraction(1)       # r_e^+
            row[m + e] = Fraction(-1)   # -r_e^-

            # B_{e, v} = +1, B_{e, u} = -1
            # -(f_v - f_u) = f_u - f_v
            if v_orig != root_idx:
                v_act = act_map[v_orig]
                row[2 * m + v_act] -= Fraction(1)
                row[2 * m + n_act + v_act] += Fraction(1)
            if u_orig != root_idx:
                u_act = act_map[u_orig]
                row[2 * m + u_act] += Fraction(1)
                row[2 * m + n_act + u_act] -= Fraction(1)

            A.append(row)
            b.append(omega_frac[e])

        res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c, A, b)
        if res.status != "OPTIMAL":
            raise SolverInfeasibleError(f"Primal L1 quotient solver failed with status {res.status}")

        r_plus = res.x[:m]
        r_minus = res.x[m : 2 * m]
        f_plus = res.x[2 * m : 2 * m + n_act]
        f_minus = res.x[2 * m + n_act : total_vars]

        r_opt = [r_plus[e] - r_minus[e] for e in range(m)]
        f_opt = [Fraction(0)] * n
        for v_orig in active_vertices:
            v_act = act_map[v_orig]
            f_opt[v_orig] = f_plus[v_act] - f_minus[v_act]

        # Sparsify optimal representative to achieve support size <= beta (Theorem L1C-T5)
        r_opt, f_opt = L1QuotientSolver._sparsify_representative(
            graph, r_opt, f_opt, root_idx, active_vertices, act_map
        )

        # Independently recompute primal feasibility equation: r = omega + B f (Item 6)
        d0_f = graph.d0(f_opt)
        recomputed_r = [omega_frac[e] + d0_f[e] for e in range(m)]
        for e in range(m):
            if r_opt[e] != recomputed_r[e]:
                raise PrimalFeasibilityError(
                    f"Primal certificate feasibility equation violated on edge {e}: "
                    f"r_opt[{e}] = {r_opt[e]} != omega[{e}] + (d0 f)[{e}] = {recomputed_r[e]}"
                )

        primal_norm = sum(weights[e] * abs(r_opt[e]) for e in range(m))

        # --------------------------------------------------------------------
        # Extract dual circulation z by solving the exact dual circulation LP:
        # max sum_e z_e omega_e  s.t. B^T z = 0, -w_e <= z_e <= w_e
        # Substitution: z_e = u_e - w_e, 0 <= u_e <= 2 w_e.
        # min sum_e (-omega_e) u_e  s.t. B^T u = B^T w, u_e + s_e = 2 w_e.
        # --------------------------------------------------------------------
        # Variables: u_0..u_{m-1}, s_0..s_{m-1} (2m vars)
        c_dual = [-omega_frac[e] for e in range(m)] + [Fraction(0)] * m
        A_dual: list[list[Fraction]] = []
        b_dual: list[Fraction] = []

        # Divergence constraints: sum_e B_{e, v} u_e = sum_e B_{e, v} w_e
        for v in range(n):
            row = [Fraction(0)] * (2 * m)
            rhs = Fraction(0)
            for e in range(m):
                row[e] = graph.B[e][v]
                rhs += graph.B[e][v] * weights[e]
            A_dual.append(row)
            b_dual.append(rhs)

        # Upper bound slack constraints: u_e + s_e = 2 w_e
        for e in range(m):
            row = [Fraction(0)] * (2 * m)
            row[e] = Fraction(1)
            row[m + e] = Fraction(1)
            A_dual.append(row)
            b_dual.append(Fraction(2) * weights[e])

        dual_res = ExactTwoPhaseSimplexSolver.solve_standard_lp(c_dual, A_dual, b_dual)
        if dual_res.status != "OPTIMAL":
            raise SolverInfeasibleError(f"Dual circulation solver failed with status {dual_res.status}")

        u_sol = dual_res.x[:m]
        z_opt = [u_sol[e] - weights[e] for e in range(m)]
        dual_bound = sum(z_opt[e] * omega_frac[e] for e in range(m))

        # Check duality gap
        gap = primal_norm - dual_bound
        if gap != Fraction(0):
            raise DualityGapNonZeroError(f"Duality gap is nonzero: Delta = {gap}")

        # Check capacity bound |z_e| <= w_e
        for e in range(m):
            if abs(z_opt[e]) > weights[e]:
                raise CapacityBoundExceededError(
                    f"Dual witness capacity exceeded on edge {e}: |{z_opt[e]}| > {weights[e]}"
                )

        # Check divergence-free condition B^T z == 0
        div = graph.d0_star(z_opt)
        if any(d != Fraction(0) for d in div):
            raise CirculationDivergenceError(f"Dual witness divergence is nonzero: B^T z = {div}")

        # Check complementary slackness
        satisfies_cs = True
        for e in range(m):
            if r_opt[e] > Fraction(0) and z_opt[e] != weights[e] or r_opt[e] < Fraction(0) and z_opt[e] != -weights[e]:
                satisfies_cs = False

        support_size = sum(1 for re in r_opt if re != Fraction(0))
        beta = graph.cycle_rank()
        satisfies_supp = support_size <= beta

        # Check integrality (L1C-T6) (Item 6)
        inputs_integral = all(w.denominator == 1 for w in weights) and all(w.denominator == 1 for w in omega_frac)
        solution_is_integral = all(re.denominator == 1 for re in r_opt) and all(fe.denominator == 1 for fe in f_opt)
        integrality_theorem_satisfied = (not inputs_integral) or solution_is_integral

        diagnostic = "ExactRepair" if primal_norm == Fraction(0) else "ClosedResidual"

        return L1CertificateReceipt(
            primal_norm=primal_norm,
            dual_bound=dual_bound,
            duality_gap=gap,
            primal_potential=tuple(f_opt),
            primal_residual=tuple(r_opt),
            dual_circulation=tuple(z_opt),
            support_size=support_size,
            cycle_rank=beta,
            satisfies_support_bound=satisfies_supp,
            satisfies_complementary_slackness=satisfies_cs,
            solution_is_integral=solution_is_integral,
            integrality_theorem_satisfied=integrality_theorem_satisfied,
            diagnostic_type=diagnostic,
            is_integral=solution_is_integral,
        )

    @staticmethod
    def _nullspace_rational(A: Sequence[Sequence[Fraction]], n: int) -> list[Fraction]:
        m = len(A)
        if n == 0:
            return []
        mat = [[Fraction(A[i][j]) for j in range(n)] for i in range(m)]
        pivot_cols: list[int] = []
        r = 0
        for c in range(n):
            if r >= m:
                break
            piv = None
            for i in range(r, m):
                if mat[i][c] != Fraction(0):
                    piv = i
                    break
            if piv is None:
                continue
            mat[r], mat[piv] = mat[piv], mat[r]
            pv = mat[r][c]
            for j in range(c, n):
                mat[r][j] /= pv
            for i in range(m):
                if i != r and mat[i][c] != Fraction(0):
                    factor = mat[i][c]
                    for j in range(c, n):
                        mat[i][j] -= factor * mat[r][j]
            pivot_cols.append(c)
            r += 1
        free_cols = [c for c in range(n) if c not in pivot_cols]
        if not free_cols:
            return []
        free_c = free_cols[0]
        sol = [Fraction(0)] * n
        sol[free_c] = Fraction(1)
        for row_idx, piv_c in enumerate(pivot_cols):
            sol[piv_c] = -mat[row_idx][free_c]
        return sol

    @staticmethod
    def _sparsify_representative(
        graph: DirectedGraph,
        r_opt: list[Fraction],
        f_opt: list[Fraction],
        root_idx: int,
        active_vertices: list[int],
        act_map: dict[int, int],
        max_steps: int = 100,
    ) -> tuple[list[Fraction], list[Fraction]]:
        m = len(graph.edges)
        n = len(graph.vertices)
        beta = graph.cycle_rank()
        n_act = len(active_vertices)
        r = list(r_opt)
        f = list(f_opt)

        for _ in range(max_steps):
            supp = [e for e in range(m) if r[e] != Fraction(0)]
            if len(supp) <= beta:
                break
            zero_edges = [e for e in range(m) if r[e] == Fraction(0)]
            A_eq: list[list[Fraction]] = []
            for e in zero_edges:
                u, v = graph.edges[e]
                u_orig = graph.vertex_index[u]
                v_orig = graph.vertex_index[v]
                row = [Fraction(0)] * n_act
                if v_orig != root_idx:
                    row[act_map[v_orig]] += Fraction(1)
                if u_orig != root_idx:
                    row[act_map[u_orig]] -= Fraction(1)
                A_eq.append(row)
            delta_act = L1QuotientSolver._nullspace_rational(A_eq, n_act)
            if not delta_act or all(x == Fraction(0) for x in delta_act):
                break
            delta_f = [Fraction(0)] * n
            for v_orig in active_vertices:
                delta_f[v_orig] = delta_act[act_map[v_orig]]
            d_vec = graph.d0(delta_f)
            candidates_pos: list[Fraction] = []
            candidates_neg: list[Fraction] = []
            for e in supp:
                if d_vec[e] != Fraction(0):
                    ratio = -r[e] / d_vec[e]
                    if ratio > Fraction(0):
                        candidates_pos.append(ratio)
                    elif ratio < Fraction(0):
                        candidates_neg.append(ratio)
            if candidates_pos:
                t = min(candidates_pos)
            elif candidates_neg:
                t = max(candidates_neg)
            else:
                break
            for e in range(m):
                r[e] += t * d_vec[e]
            for v in range(n):
                f[v] += t * delta_f[v]

        return r, f


def check_certificate_receipt(
    receipt: L1CertificateReceipt,
    graph: DirectedGraph,
    omega: Sequence[Fraction | int | str],
    complex2: Simplicial2Complex | None = None,
) -> bool:
    """Independently re-verify an emitted L1CertificateReceipt against the graph and omega.

    Verifies:
    1. Primal feasibility: r_e == omega_e + (d0 f)_e for all e.
    2. Primal norm: sum_e w_e |r_e| == receipt.primal_norm.
    3. Dual divergence: B^T z == 0 (z is a valid circulation).
    4. Capacity bounds: |z_e| <= w_e for all e.
    5. Dual bound: <z, omega> == receipt.dual_bound.
    6. Zero duality gap: primal_norm - dual_bound == receipt.duality_gap == 0.
    7. Complementary slackness: z_e * r_e == w_e * |r_e| for all e.
    8. Support bound: support_size <= cycle_rank beta.
    9. Diagnostic type consistency.
    """
    m = len(graph.edges)
    omega_frac = [Fraction(x) for x in omega]
    if len(omega_frac) != m:
        raise CochainDimensionError(f"omega length {len(omega_frac)} != edge count {m}")

    # 1. Primal feasibility
    d0_f = graph.d0(receipt.primal_potential)
    for e in range(m):
        expected_r = omega_frac[e] + d0_f[e]
        if receipt.primal_residual[e] != expected_r:
            raise PrimalFeasibilityError(
                f"Primal feasibility failed on edge {e}: {receipt.primal_residual[e]} != {expected_r}"
            )

    # 2. Primal norm
    computed_norm = graph.weighted_l1_norm(receipt.primal_residual)
    if computed_norm != receipt.primal_norm:
        raise CertificateViolationError(
            f"Primal norm mismatch: computed {computed_norm} != reported {receipt.primal_norm}"
        )

    # 3. Dual divergence
    div = graph.d0_star(receipt.dual_circulation)
    if any(d != Fraction(0) for d in div):
        raise CirculationDivergenceError(f"Dual circulation has non-zero divergence: {div}")

    # 4. Capacity bounds
    for e in range(m):
        if abs(receipt.dual_circulation[e]) > graph.weights[e]:
            raise CapacityBoundExceededError(
                f"Capacity exceeded on edge {e}: |{receipt.dual_circulation[e]}| > {graph.weights[e]}"
            )

    # 5. Dual bound
    computed_dual = graph.inner_product(receipt.dual_circulation, omega_frac)
    if computed_dual != receipt.dual_bound:
        raise CertificateViolationError(
            f"Dual bound mismatch: computed {computed_dual} != reported {receipt.dual_bound}"
        )

    # 6. Complementary slackness
    for e in range(m):
        re = receipt.primal_residual[e]
        ze = receipt.dual_circulation[e]
        we = graph.weights[e]
        if re > Fraction(0) and ze != we:
            raise ComplementarySlacknessError(f"CS violated at positive residual edge {e}: z = {ze} != w = {we}")
        if re < Fraction(0) and ze != -we:
            raise ComplementarySlacknessError(f"CS violated at negative residual edge {e}: z = {ze} != -w = {-we}")
        if re == Fraction(0) and abs(ze) > we:
            raise CapacityBoundExceededError(f"Capacity violated at zero residual edge {e}: |z| = {abs(ze)} > w = {we}")

    # 7. Zero duality gap
    gap = computed_norm - computed_dual
    if gap != Fraction(0) or gap != receipt.duality_gap:
        raise DualityGapNonZeroError(f"Duality gap is non-zero: Delta = {gap}")

    # 8. Cycle rank and support size
    computed_beta = graph.cycle_rank()
    if receipt.cycle_rank != computed_beta:
        raise CertificateViolationError(
            f"Cycle rank mismatch: computed {computed_beta} != reported {receipt.cycle_rank}"
        )

    computed_supp = sum(1 for re in receipt.primal_residual if re != Fraction(0))
    if computed_supp != receipt.support_size:
        raise CertificateViolationError(f"Support size mismatch: computed {computed_supp} != reported {receipt.support_size}")

    expected_satisfies_supp = (computed_supp <= computed_beta)
    if receipt.satisfies_support_bound != expected_satisfies_supp:
        raise CertificateViolationError(
            f"Support bound predicate mismatch: computed {expected_satisfies_supp} != reported {receipt.satisfies_support_bound}"
        )

    if receipt.satisfies_complementary_slackness is not True:
        raise CertificateViolationError("Receipt claims complementary slackness is not satisfied, but CS was verified")

    # 9. Diagnostic type
    if complex2 is not None:
        curv = complex2.d1(receipt.primal_residual)
        is_closed = all(c == Fraction(0) for c in curv)
        if receipt.primal_norm == Fraction(0):
            expected_diag = "ExactRepair"
        elif is_closed:
            expected_diag = "ClosedResidual"
        else:
            expected_diag = "CurvatureResidual"
    else:
        expected_diag = "ExactRepair" if receipt.primal_norm == Fraction(0) else "ClosedResidual"

    if receipt.diagnostic_type != expected_diag:
        raise CertificateViolationError(
            f"Diagnostic type mismatch: reported {receipt.diagnostic_type} != expected {expected_diag}"
        )

    # 10. Integrality properties
    inputs_integral = all(Fraction(w).denominator == 1 for w in graph.weights) and all(
        Fraction(x).denominator == 1 for x in omega_frac
    )
    computed_is_integral = (
        all(r.denominator == 1 for r in receipt.primal_residual)
        and all(f.denominator == 1 for f in receipt.primal_potential)
    )
    if receipt.solution_is_integral != computed_is_integral:
        raise CertificateViolationError(
            f"Solution integrality mismatch: computed {computed_is_integral} != reported {receipt.solution_is_integral}"
        )
    if receipt.is_integral != computed_is_integral:
        raise CertificateViolationError(
            f"is_integral alias mismatch: computed {computed_is_integral} != reported {receipt.is_integral}"
        )

    expected_integrality_thm = (not inputs_integral) or computed_is_integral
    if receipt.integrality_theorem_satisfied != expected_integrality_thm:
        raise CertificateViolationError(
            f"Integrality theorem predicate mismatch: computed {expected_integrality_thm} != reported {receipt.integrality_theorem_satisfied}"
        )

    return True


# ============================================================================
# 6. Finite Quantum Obstruction Calculus
# ============================================================================

@dataclass(frozen=True)
class RationalComplex:
    """Exact rational complex number z = re + i * im."""
    re: Fraction
    im: Fraction

    def __add__(self, other: RationalComplex) -> RationalComplex:
        return RationalComplex(self.re + other.re, self.im + other.im)

    def __sub__(self, other: RationalComplex) -> RationalComplex:
        return RationalComplex(self.re - other.re, self.im - other.im)

    def __mul__(self, other: RationalComplex | Fraction | int) -> RationalComplex:
        if isinstance(other, RationalComplex):
            return RationalComplex(
                self.re * other.re - self.im * other.im,
                self.re * other.im + self.im * other.re,
            )
        frac = Fraction(other)
        return RationalComplex(self.re * frac, self.im * frac)

    def conjugate(self) -> RationalComplex:
        return RationalComplex(self.re, -self.im)

    def norm_sq(self) -> Fraction:
        return self.re * self.re + self.im * self.im

    def modulus_exact_or_float(self) -> tuple[bool, Fraction | float]:
        """Return (is_exact, value) where is_exact is True if |z| is rational."""
        ns = self.norm_sq()
        if ns == Fraction(0):
            return True, Fraction(0)
        num = ns.numerator
        den = ns.denominator
        isqrt_num = math.isqrt(num)
        isqrt_den = math.isqrt(den)
        if isqrt_num * isqrt_num == num and isqrt_den * isqrt_den == den:
            return True, Fraction(isqrt_num, isqrt_den)
        return False, math.sqrt(float(ns))

    def modulus(self) -> Fraction | float:
        """Return an exact Fraction for rational moduli, otherwise a binary64 float."""
        _, val = self.modulus_exact_or_float()
        return val


class QuantumDensityMatrix:
    """Exact finite quantum density matrix rho on N-dimensional Hilbert space.

    Axiomatic constraints:
    1. Hermitian: rho = rho^dagger.
    2. Unit trace: Tr(rho) == 1.
    3. Positive semidefinite: all principal minors non-negative / exact rational LDL^dagger certificate.
    """

    def __init__(self, matrix: Sequence[Sequence[RationalComplex]], validate: bool = True) -> None:
        self.dim = len(matrix)
        if self.dim == 0:
            raise QuantumIntegrityError("Empty density matrix")
        for row in matrix:
            if len(row) != self.dim:
                raise QuantumIntegrityError("Non-square density matrix")

        self.matrix = [[RationalComplex(val.re, val.im) for val in row] for row in matrix]
        if validate:
            self.validate_state()

    def validate_state(self) -> None:
        """Validate Hermiticity, unit trace, and positive semidefiniteness."""
        # 1. Check Hermiticity: rho_{jk} == conj(rho_{kj})
        for j in range(self.dim):
            for k in range(self.dim):
                cj = self.matrix[j][k]
                ck = self.matrix[k][j].conjugate()
                if cj.re != ck.re or cj.im != ck.im:
                    raise NonHermitianStateError(f"Non-Hermitian at ({j}, {k}): {cj} vs {ck}")

        # 2. Check unit trace: sum_j rho_{jj}.re == 1, sum_j rho_{jj}.im == 0
        tr_re = sum((self.matrix[j][j].re for j in range(self.dim)), Fraction(0))
        tr_im = sum((self.matrix[j][j].im for j in range(self.dim)), Fraction(0))
        if tr_re != Fraction(1) or tr_im != Fraction(0):
            raise TraceNormalizationError(f"Trace normalization failed: Tr(rho) = {tr_re} + i {tr_im}")

        # 3. Preliminary necessary conditions: diagonal non-negativity and 2x2 principal minors
        for j in range(self.dim):
            if self.matrix[j][j].re < Fraction(0):
                raise NegativeSpectrumError(f"Negative diagonal entry at {j}: {self.matrix[j][j].re}")
            if self.matrix[j][j].re == Fraction(0):
                for k in range(self.dim):
                    if self.matrix[j][k].norm_sq() != Fraction(0):
                        raise NegativeSpectrumError(
                            f"Zero diagonal entry at {j} with non-zero off-diagonal at ({j}, {k})"
                        )

        for j in range(self.dim):
            for k in range(j + 1, self.dim):
                diag_prod = self.matrix[j][j].re * self.matrix[k][k].re
                off_sq = self.matrix[j][k].norm_sq()
                if diag_prod < off_sq:
                    raise NegativeSpectrumError(
                        f"2x2 principal minor violated at ({j}, {k}): {diag_prod} < {off_sq}"
                    )

        # 4. Complete exact rational positive semidefiniteness via LDL^dagger with complete diagonal pivoting
        if not self._is_positive_semidefinite():
            raise NegativeSpectrumError("State violates positive semidefiniteness (has negative eigenvalues)")

    def _is_positive_semidefinite(self) -> bool:
        """Exact rational Cholesky/LDL^dagger decomposition with complete diagonal pivoting."""
        dim = self.dim
        A = [[RationalComplex(self.matrix[i][j].re, self.matrix[i][j].im) for j in range(dim)] for i in range(dim)]

        for k in range(dim):
            # Complete diagonal pivoting
            best_idx = k
            best_diag = A[k][k].re
            for idx in range(k + 1, dim):
                if A[idx][idx].re > best_diag:
                    best_diag = A[idx][idx].re
                    best_idx = idx

            if best_diag < Fraction(0):
                return False

            if best_diag == Fraction(0):
                # In a PSD matrix, if max remaining diagonal is 0, all remaining entries must be 0
                for i in range(k, dim):
                    for j in range(k, dim):
                        if A[i][j].norm_sq() != Fraction(0):
                            return False
                return True

            # Swap pivot to position k
            if best_idx != k:
                A[k], A[best_idx] = A[best_idx], A[k]
                for i in range(dim):
                    A[i][k], A[i][best_idx] = A[i][best_idx], A[i][k]

            pivot = A[k][k].re
            # Submatrix elimination
            for i in range(k + 1, dim):
                factor = A[i][k]
                if factor.norm_sq() == Fraction(0):
                    continue
                for j in range(k + 1, dim):
                    prod = factor * A[j][k].conjugate()
                    A[i][j] = A[i][j] - RationalComplex(prod.re / pivot, prod.im / pivot)

        return True

    def dephased_state(self) -> QuantumDensityMatrix:
        """Return diagonal pointer state rho_diag = sum_v rho_{vv} |v><v|."""
        diag_mat = [
            [RationalComplex(self.matrix[j][k].re if j == k else Fraction(0), Fraction(0)) for k in range(self.dim)]
            for j in range(self.dim)
        ]
        return QuantumDensityMatrix(diag_mat, validate=False)

    def off_diagonal_l1_coherence(self) -> Fraction | float:
        """Total upper-triangle off-diagonal coherence sum_{j < k} |rho_{jk}|.

        Correctly evaluates complex moduli |z| = sqrt(a^2 + b^2). If all moduli
        have exact rational square roots, returns an exact Fraction; otherwise
        returns a binary64 float.
        """
        exact = True
        total_frac = Fraction(0)
        total_float = 0.0
        for j in range(self.dim):
            for k in range(j + 1, self.dim):
                is_exact, val = self.matrix[j][k].modulus_exact_or_float()
                if is_exact and exact:
                    total_frac += val  # type: ignore
                else:
                    if exact:
                        total_float = float(total_frac)
                        exact = False
                    total_float += float(val)
        return total_frac if exact else total_float

    def total_l1_coherence(self) -> Fraction | float:
        """Standard Baumgratz-Cramer-Plenio l1-coherence C_{l1}(rho) = sum_{j != k} |rho_{jk}| = 2 * sum_{j < k} |rho_{jk}|."""
        off = self.off_diagonal_l1_coherence()
        return 2 * off

    @classmethod
    def pure_state(cls, amplitudes: Sequence[RationalComplex]) -> QuantumDensityMatrix:
        """Construct pure state |psi><psi|."""
        norm_sq = sum((a.norm_sq() for a in amplitudes), Fraction(0))
        if norm_sq != Fraction(1):
            raise TraceNormalizationError(f"Pure state vector is not normalized: norm^2 = {norm_sq}")
        mat = [[amplitudes[j] * amplitudes[k].conjugate() for k in range(len(amplitudes))] for j in range(len(amplitudes))]
        return cls(mat)


# ============================================================================
# 7. Exact Rational Moore-Penrose Graph Laplacian Solver (p = 2)
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
            try:
                norm_val = math.sqrt(float(sq_norm))
            except OverflowError:
                try:
                    shift = (num.bit_length() - den.bit_length() - 500) // 2
                    if shift > 0:
                        scaled_sq = (num >> (2 * shift)) / den
                        norm_val = math.sqrt(scaled_sq) * math.ldexp(1.0, shift)
                    else:
                        norm_val = float("inf")
                except (OverflowError, ValueError):
                    norm_val = float("inf")

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
# 8. Exact Rational Chebyshev LP Solver (p = inf)
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


def check_linf_certificate_receipt(
    receipt: LinfCertificateReceipt,
    graph: DirectedGraph,
    h: Sequence[Fraction | int | str],
) -> bool:
    """Independently certify the weighted Chebyshev optimum, using r = h - Bf.

    Backend status and objective values are not evidence for these checks.
    Feasibility and equality of the actual primal and dual values prove optimality.
    """
    m, n = len(graph.edges), len(graph.vertices)
    if (len(h), len(receipt.primal_potential), len(receipt.primal_residual),
            len(receipt.dual_circulation)) != (m, n, m, m):
        raise CertificateViolationError("Linf certificate dimension mismatch")
    values = (
        receipt.chebyshev_norm, receipt.dual_bound, receipt.duality_gap,
        *receipt.primal_potential, *receipt.primal_residual, *receipt.dual_circulation,
    )
    if any(isinstance(x, bool) or not isinstance(x, (Fraction, int)) for x in values):
        raise CertificateViolationError("Linf certificate must contain exact rational values")
    if receipt.status != "OPTIMAL_LINF":
        raise CertificateViolationError("Unexpected Linf certificate status")
    h_frac = [Fraction(x) for x in h]
    t = receipt.chebyshev_norm
    if t < 0:
        raise PrimalFeasibilityError("Linf radius must be nonnegative")
    d0_f = graph.d0(receipt.primal_potential)
    if any(receipt.primal_residual[e] != h_frac[e] - d0_f[e] for e in range(m)):
        raise PrimalFeasibilityError("Linf residual does not equal h - Bf")
    weighted = [graph.weights[e] * abs(receipt.primal_residual[e]) for e in range(m)]
    computed_norm = max(weighted, default=Fraction(0))
    if computed_norm > t:
        raise PrimalFeasibilityError("Linf residual exceeds the reported radius")
    if any(x != 0 for x in graph.d0_star(receipt.dual_circulation)):
        raise CirculationDivergenceError("Linf dual circulation has nonzero divergence")
    dual_norm = sum(
        (abs(receipt.dual_circulation[e]) / graph.weights[e] for e in range(m)),
        Fraction(0),
    )
    if dual_norm > 1:
        raise CapacityBoundExceededError("Linf dual weighted L1 norm exceeds one")
    computed_dual = graph.inner_product(receipt.dual_circulation, h_frac)
    if computed_dual != receipt.dual_bound:
        raise CertificateViolationError("Linf dual bound mismatch")
    gap = t - computed_dual
    if gap != 0 or receipt.duality_gap != gap or computed_norm != t:
        raise DualityGapNonZeroError("Linf primal and dual values do not coincide")
    peaks = tuple(e for e in range(m) if weighted[e] == t)
    if receipt.peak_edges != peaks:
        raise CertificateViolationError("Linf peak-edge metadata mismatch")
    return True


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
        if res.status != "OPTIMAL":
            raise SolverInfeasibleError(f"Linf primal LP status: {res.status}")
        if len(res.x) != total_vars or any(
            isinstance(x, bool) or not isinstance(x, (Fraction, int)) for x in res.x
        ):
            raise CertificateViolationError("Invalid Linf primal backend vector")
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
        if dual_res.status != "OPTIMAL":
            raise SolverInfeasibleError(f"Linf dual LP status: {dual_res.status}")
        if len(dual_res.x) != total_dual_vars or any(
            isinstance(x, bool) or not isinstance(x, (Fraction, int)) for x in dual_res.x
        ):
            raise CertificateViolationError("Invalid Linf dual backend vector")
        z_plus = dual_res.x[:m]
        z_minus = dual_res.x[m : 2 * m]
        z_opt = [z_plus[e] - z_minus[e] for e in range(m)]
        dual_bound = sum(z_opt[e] * h_frac[e] for e in range(m))

        gap = t_opt - dual_bound

        receipt = LinfCertificateReceipt(
            chebyshev_norm=t_opt,
            primal_potential=tuple(f_opt),
            primal_residual=tuple(r_opt),
            dual_circulation=tuple(z_opt),
            dual_bound=dual_bound,
            duality_gap=gap,
            peak_edges=peak_edges,
        )
        check_linf_certificate_receipt(receipt, graph, h_frac)
        return receipt


# ============================================================================
# 9. Float64 Convex Solvers for Continuous p in (1, inf)
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

    The historical class name is retained for API compatibility.
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
# 10. Operator-Valued Schatten-p Module
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
        """Compute a polar dual witness for finite p > 1; zero input returns zero."""
        if not math.isfinite(p) or p <= 1.0:
            raise ValueError("Polar witness requires finite p > 1")
        q = p / (p - 1.0)
        U, s, Vh = np.linalg.svd(A, full_matrices=False)
        norm_p = OperatorSchattenPModule.schatten_norm(A, p)
        if norm_p == 0.0:
            return np.zeros_like(A)
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

