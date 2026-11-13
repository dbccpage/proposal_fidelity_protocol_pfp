"""Reference implementation for path-additive coboundary defect validation in reasoning traces.

Decides exact l^1 coboundary repairability over the rationals, proposes a repair
potential and a dual circulation with a floating-point linear programme, and
certifies those proposals only in exact rational arithmetic: an upper bound on
phi_1 from an exact potential, a lower bound from an exactly feasible dual
circulation, and the exact gap between the two. No floating-point number is
ever reported as an exact value.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import linprog

Edge = Tuple[str, str]
Cochain = Dict[Edge, Fraction]
Potential = Dict[str, Fraction]

STATUS_EXACT = "Exact"
STATUS_OBSTRUCTION = "CohomologicalObstruction"
STATUS_CARRIER_FAILURE = "CarrierFailure"
STATUS_BUDGET_EXCEEDED = "BudgetExceeded"

_SNAP_TOLERANCE = 1e-7
_MAX_DENOMINATOR = 10**9


def _is_exact_rational(value: object) -> bool:
    return isinstance(value, (int, Fraction)) and not isinstance(value, bool)


def _rationalise(value: float) -> Fraction:
    """Turn a floating-point LP coordinate into a rational proposal (never a certificate)."""
    for target in (Fraction(-1), Fraction(0), Fraction(1)):
        if abs(value - float(target)) < _SNAP_TOLERANCE:
            return target
    return Fraction(value).limit_denominator(_MAX_DENOMINATOR)


@dataclass(frozen=True)
class CarrierGraph:
    """Finite directed carrier graph representing reasoning steps, citations, or claims."""
    vertices: Tuple[str, ...]
    edges: Tuple[Edge, ...]

    @classmethod
    def create(cls, vertices: List[str], edges: List[Edge]) -> "CarrierGraph":
        return cls(vertices=tuple(vertices), edges=tuple(edges))


@dataclass
class ValidationVerdict:
    """Audit-grade diagnostic verdict for a declared carrier and defect cochain.

    ``phi_1`` is exact when ``diagnostics["certified"]`` is True. Otherwise it is
    the exact upper bound realised by ``repair_potential`` and the exact lower
    bound certified by ``dual_witness`` is in ``diagnostics["phi_1_lower_bound"]``.
    """
    status: str  # STATUS_EXACT, STATUS_OBSTRUCTION, STATUS_CARRIER_FAILURE, STATUS_BUDGET_EXCEEDED
    phi_1: Fraction
    repair_potential: Optional[Potential]
    dual_witness: Optional[Cochain]
    diagnostics: Dict[str, Any]


def _failure(status: str, **diagnostics: Any) -> ValidationVerdict:
    return ValidationVerdict(
        status=status,
        phi_1=Fraction(0),
        repair_potential=None,
        dual_witness=None,
        diagnostics=diagnostics,
    )


class TraceValidator:
    """Exact rational decision of l^1 coboundary repair with certified dual witnesses."""

    @staticmethod
    def coboundary_d0(graph: CarrierGraph, alpha: Potential) -> Cochain:
        """Compute (d_0 alpha)(u, v) = alpha(v) - alpha(u)."""
        return {(u, v): alpha[v] - alpha[u] for u, v in graph.edges}

    @staticmethod
    def divergence(graph: CarrierGraph, phi: Cochain) -> Potential:
        """Compute divergence (d_0^* phi)(v) = sum_{w} phi(v,w) - sum_{u} phi(u,v)."""
        div = {v: Fraction(0) for v in graph.vertices}
        for (u, v), val in phi.items():
            div[u] += val
            div[v] -= val
        return div

    @staticmethod
    def l1_norm(graph: CarrierGraph, cochain: Cochain) -> Fraction:
        return sum((abs(cochain.get(e, Fraction(0))) for e in graph.edges), Fraction(0))

    @classmethod
    def exact_repair(cls, graph: CarrierGraph, omega: Cochain) -> Optional[Potential]:
        """Solve d_0 alpha = omega exactly over the rationals, or return None.

        The first vertex of every connected component is gauged to zero; the
        system is solvable exactly when omega sums to zero around every cycle,
        which the breadth-first walk checks on each non-tree edge.
        """
        adjacency: Dict[str, List[Tuple[str, Fraction]]] = {v: [] for v in graph.vertices}
        for u, v in graph.edges:
            w = omega.get((u, v), Fraction(0))
            adjacency[u].append((v, w))
            adjacency[v].append((u, -w))
        alpha: Potential = {}
        for root in graph.vertices:
            if root in alpha:
                continue
            alpha[root] = Fraction(0)
            queue = deque([root])
            while queue:
                x = queue.popleft()
                for y, delta in adjacency[x]:
                    candidate = alpha[x] + delta
                    if y not in alpha:
                        alpha[y] = candidate
                        queue.append(y)
                    elif alpha[y] != candidate:
                        return None
        return alpha

    @classmethod
    def certify_dual(cls, graph: CarrierGraph, omega: Cochain, phi: Cochain) -> Optional[Fraction]:
        """Return <omega, phi> if phi is exactly a circulation with |phi_e| <= 1, else None."""
        if any(abs(phi.get(e, Fraction(0))) > 1 for e in graph.edges):
            return None
        if any(val != 0 for val in cls.divergence(graph, phi).values()):
            return None
        return sum((omega.get(e, Fraction(0)) * phi.get(e, Fraction(0)) for e in graph.edges), Fraction(0))

    @classmethod
    def validate_trace(
        cls,
        graph: CarrierGraph,
        omega: Cochain,
        step_budget: int = 1000,
    ) -> ValidationVerdict:
        """Validate trace cochain omega against the declared carrier graph.

        ``step_budget`` bounds the carrier size (vertices plus edges) the
        validator will decide; larger carriers are refused with
        ``BudgetExceeded`` instead of being partially evaluated.
        """
        if not graph.vertices or not graph.edges:
            return _failure(STATUS_CARRIER_FAILURE, error="Carrier graph contains empty vertex or edge set.")
        if len(set(graph.vertices)) != len(graph.vertices):
            return _failure(STATUS_CARRIER_FAILURE, error="Carrier graph declares a vertex twice.")
        if len(set(graph.edges)) != len(graph.edges):
            return _failure(STATUS_CARRIER_FAILURE, error="Carrier graph declares an edge twice.")
        declared = set(graph.vertices)
        for u, v in graph.edges:
            if u not in declared or v not in declared:
                return _failure(STATUS_CARRIER_FAILURE, error=f"Edge ({u}, {v}) references undeclared vertices.")
        edge_set = set(graph.edges)
        for e, val in omega.items():
            if e not in edge_set:
                return _failure(STATUS_CARRIER_FAILURE, error=f"Cochain references undeclared edge {e}.")
            if not _is_exact_rational(val):
                return _failure(
                    STATUS_CARRIER_FAILURE,
                    error=f"Cochain value on edge {e} is not an exact rational: {type(val).__name__}.",
                )
        size = len(graph.vertices) + len(graph.edges)
        if size > step_budget:
            return _failure(
                STATUS_BUDGET_EXCEEDED,
                error=f"Carrier size {size} exceeds the declared step budget {step_budget}.",
                carrier_size=size,
                step_budget=step_budget,
            )

        omega = {e: Fraction(val) for e, val in omega.items()}

        # 1. Exact decision: is omega a coboundary?
        alpha_exact = cls.exact_repair(graph, omega)
        if alpha_exact is not None:
            zero_witness = {e: Fraction(0) for e in graph.edges}
            return ValidationVerdict(
                status=STATUS_EXACT,
                phi_1=Fraction(0),
                repair_potential=alpha_exact,
                dual_witness=zero_witness,
                diagnostics={
                    "certified": True,
                    "phi_1_upper_bound": Fraction(0),
                    "phi_1_lower_bound": Fraction(0),
                    "dual_value": Fraction(0),
                    "divergence_defect": Fraction(0),
                    "duality_gap": Fraction(0),
                    "is_circulation": True,
                    "certificate": "exact coboundary solve",
                },
            )

        # 2. Floating-point proposals (never reported as exact values).
        n_v, n_e = len(graph.vertices), len(graph.edges)
        v_idx = {v: i for i, v in enumerate(graph.vertices)}
        edge_list = list(graph.edges)
        omega_float = [float(omega.get(e, Fraction(0))) for e in edge_list]

        # Dual: maximise <omega, phi> over circulations with -1 <= phi_e <= 1.
        incidence = np.zeros((n_v, n_e))
        for j, (u, v) in enumerate(edge_list):
            incidence[v_idx[u], j] += 1.0
            incidence[v_idx[v], j] -= 1.0
        res_dual = linprog(
            [-w for w in omega_float],
            A_eq=incidence,
            b_eq=np.zeros(n_v),
            bounds=[(-1.0, 1.0)] * n_e,
            method="highs",
        )

        # Primal: minimise sum_e t_e subject to |omega_e - (alpha_v - alpha_u)| <= t_e, alpha_0 = 0.
        c_primal = [1.0] * n_e + [0.0] * n_v
        a_ub = np.zeros((2 * n_e, n_e + n_v))
        b_ub = np.zeros(2 * n_e)
        for j, (u, v) in enumerate(edge_list):
            a_ub[2 * j, j] = -1.0
            a_ub[2 * j, n_e + v_idx[v]] = 1.0
            a_ub[2 * j, n_e + v_idx[u]] = -1.0
            b_ub[2 * j] = omega_float[j]
            a_ub[2 * j + 1, j] = -1.0
            a_ub[2 * j + 1, n_e + v_idx[v]] = -1.0
            a_ub[2 * j + 1, n_e + v_idx[u]] = 1.0
            b_ub[2 * j + 1] = -omega_float[j]
        a_eq = np.zeros((1, n_e + n_v))
        a_eq[0, n_e] = 1.0
        res_primal = linprog(
            c_primal,
            A_ub=a_ub,
            b_ub=b_ub,
            A_eq=a_eq,
            b_eq=np.zeros(1),
            bounds=[(0.0, None)] * n_e + [(None, None)] * n_v,
            method="highs",
        )

        # 3. Exact lower bound from the rationalised dual, certified or discarded.
        dual_phi: Cochain = {e: Fraction(0) for e in edge_list}
        lower: Optional[Fraction] = None
        if res_dual.success:
            dual_phi = {e: _rationalise(float(res_dual.x[j])) for j, e in enumerate(edge_list)}
            lower = cls.certify_dual(graph, omega, dual_phi)
            if lower is None:
                rounded = {
                    e: Fraction(max(-1, min(1, int(round(float(res_dual.x[j])))))) for j, e in enumerate(edge_list)
                }
                lower = cls.certify_dual(graph, omega, rounded)
                if lower is not None:
                    dual_phi = rounded
        if lower is None:
            dual_phi = {e: Fraction(0) for e in edge_list}
            lower = Fraction(0)  # the zero circulation is always feasible
            dual_certified = False
        else:
            dual_certified = True

        # 4. Exact upper bound from an exact potential built on the LP's tight edges.
        alpha_exact = cls._exact_potential_from_proposal(graph, omega, res_primal, n_e, edge_list, omega_float)
        upper = cls.l1_norm(graph, {e: omega.get(e, Fraction(0)) - d for e, d in cls.coboundary_d0(graph, alpha_exact).items()})

        certified = dual_certified and upper == lower
        div_norm = sum((abs(val) for val in cls.divergence(graph, dual_phi).values()), Fraction(0))
        return ValidationVerdict(
            status=STATUS_OBSTRUCTION,
            phi_1=upper,
            repair_potential=alpha_exact,
            dual_witness=dual_phi,
            diagnostics={
                "certified": certified,
                "phi_1_upper_bound": upper,
                "phi_1_lower_bound": lower,
                "dual_value": lower,
                "divergence_defect": div_norm,
                "duality_gap": upper - lower,
                "is_circulation": div_norm == 0,
                "dual_lp_status": str(res_dual.message),
                "primal_lp_status": str(res_primal.message),
                "certificate": "exact primal/dual pair" if certified else "bounds only; gap is exact",
            },
        )

    @classmethod
    def _exact_potential_from_proposal(
        cls,
        graph: CarrierGraph,
        omega: Cochain,
        res_primal: Any,
        n_e: int,
        edge_list: List[Edge],
        omega_float: List[float],
    ) -> Potential:
        """Build an exact potential that reproduces the LP's tight edges exactly.

        Along edges the LP reports as tight (residual numerically zero) the
        potential is propagated with the exact omega values, so the exact
        residual on those edges is zero. Vertices the tight edges do not reach
        take the rationalised LP value. Any potential gives a valid upper
        bound; this construction makes it meet the dual bound whenever the LP
        found an optimal vertex.
        """
        v_idx = {v: i for i, v in enumerate(graph.vertices)}
        if not res_primal.success:
            return {v: Fraction(0) for v in graph.vertices}
        lp_alpha = [float(res_primal.x[n_e + i]) for i in range(len(graph.vertices))]
        tight: Dict[str, List[Tuple[str, Fraction]]] = {v: [] for v in graph.vertices}
        for j, (u, v) in enumerate(edge_list):
            residual = omega_float[j] - (lp_alpha[v_idx[v]] - lp_alpha[v_idx[u]])
            if abs(residual) < _SNAP_TOLERANCE:
                w = omega.get((u, v), Fraction(0))
                tight[u].append((v, w))
                tight[v].append((u, -w))
        alpha: Potential = {}
        for root in graph.vertices:
            if root in alpha:
                continue
            alpha[root] = _rationalise(lp_alpha[v_idx[root]])
            queue = deque([root])
            while queue:
                x = queue.popleft()
                for y, delta in tight[x]:
                    if y not in alpha:
                        alpha[y] = alpha[x] + delta
                        queue.append(y)
        return alpha


class PathDefectAuditor:
    """Evaluates observer-relative commutativity defect bounds along reasoning paths."""

    @staticmethod
    def audit_paths(
        omega: Cochain,
        path_a: List[Edge],
        path_b: List[Edge],
    ) -> Dict[str, Any]:
        """Compute commutativity defect between two paths with matching endpoints."""
        sum_a = sum((omega.get(e, Fraction(0)) for e in path_a), Fraction(0))
        sum_b = sum((omega.get(e, Fraction(0)) for e in path_b), Fraction(0))
        delta = sum_a - sum_b

        # Combined closed walk support
        walk_edges = list(path_a) + list(path_b)
        walk_l1_bound = sum((abs(omega.get(e, Fraction(0))) for e in walk_edges), Fraction(0))

        return {
            "path_a_defect": sum_a,
            "path_b_defect": sum_b,
            "noncommutativity_delta": delta,
            "abs_delta": abs(delta),
            "walk_l1_bound": walk_l1_bound,
            "bound_satisfied": (abs(delta) <= walk_l1_bound),
        }
