"""Legacy mathematical evaluator interfaces with a fail-closed Rust boundary.

Generic constraint checks and bipartiteness remain available. Named Phi1 and
Gamma2 output requires an adapter backed by core_functional; former Python
functional formulas have been retired.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from pfp.functional_boundary import require_rust_functional

from ..models import ObstructionScore

# ── 1. Linear Programming Duality & Feasibility Calculator ─────────────────

@dataclass(frozen=True)
class LPConstraint:
    name: str
    coefficients: Dict[str, float]
    op: str  # "<=", ">=", "=="
    rhs: float

    def evaluate(self, point: Mapping[str, float]) -> Tuple[float, float, bool]:
        """Returns (lhs, slack/violation, is_satisfied)."""
        lhs = sum(coeff * point.get(var, 0.0) for var, coeff in self.coefficients.items())
        if self.op == "<=":
            violation = max(0.0, lhs - self.rhs)
            return lhs, violation, lhs <= self.rhs + 1e-8
        elif self.op == ">=":
            violation = max(0.0, self.rhs - lhs)
            return lhs, violation, lhs >= self.rhs - 1e-8
        else:  # "=="
            violation = abs(lhs - self.rhs)
            return lhs, violation, abs(lhs - self.rhs) < 1e-8


class LPDualityCalculator:
    """Legacy primal and dual scoring interface awaiting a Rust-backed adapter."""

    @staticmethod
    def evaluate_lp(
        *,
        objective_coeffs: Dict[str, float],
        is_max: bool,
        constraints: Sequence[LPConstraint],
        primal_point: Mapping[str, float],
        dual_multipliers: Mapping[str, float],
    ) -> Dict[str, Any]:
        require_rust_functional("LPDualityCalculator.evaluate_lp")


# ── 2. Discrete Cochain Cohomology Calculator ──────────────────────────────

class CochainTriadCalculator:
    """Legacy cochain scoring interface awaiting a Rust-backed adapter."""

    @staticmethod
    def evaluate_cochain(
        carrier_edges: Sequence[Tuple[int, int]],
        carrier_faces: Sequence[Tuple[int, int, int]],
        edge_weights: Mapping[Tuple[int, int], float],
    ) -> Dict[str, Any]:
        require_rust_functional("CochainTriadCalculator.evaluate_cochain")


# ── 3. Meron-Cluster Lattice Evaluator ─────────────────────────────────────

class MeronClusterCalculator:
    """Legacy cluster scoring interface; the structural bipartiteness check remains available."""

    @staticmethod
    def evaluate_clusters(
        sites: Sequence[int],
        all_bonds: Sequence[Tuple[int, int]],
        activated_bonds: Sequence[Tuple[int, int]],
        occupations: Mapping[int, int],  # site -> 0 or 1
    ) -> Dict[str, Any]:
        require_rust_functional("MeronClusterCalculator.evaluate_clusters")

    @staticmethod
    def check_bipartiteness(sites: Sequence[int], all_bonds: Sequence[Tuple[int, int]]) -> Tuple[bool, List[int]]:
        """
        Tests if the lattice graph is 2-colorable (bipartite).
        Returns (is_bipartite, odd_cycle_witness).
        """
        adj: Dict[int, List[int]] = {s: [] for s in sites}
        for u, v in all_bonds:
            adj[u].append(v)
            adj[v].append(u)

        color: Dict[int, int] = {}
        for start_node in sites:
            if start_node in color:
                continue
            queue = [start_node]
            color[start_node] = 0
            while queue:
                u = queue.pop(0)
                for v in adj[u]:
                    if v not in color:
                        color[v] = 1 - color[u]
                        queue.append(v)
                    elif color[v] == color[u]:
                        # Odd cycle found
                        return False, [u, v]

        return True, []

    @staticmethod
    def evaluate_frustrated_lattice(
        sites: Sequence[int],
        all_bonds: Sequence[Tuple[int, int]],
        activated_bonds: Sequence[Tuple[int, int]],
        occupations: Mapping[int, int],
    ) -> Dict[str, Any]:
        require_rust_functional("MeronClusterCalculator.evaluate_frustrated_lattice")


# ── 4. Complexified Lefschetz Thimble & Majorana Kramers Lift Calculator ────

class MajoranaThimbleLiftCalculator:
    """Legacy proposed-lift scoring interface awaiting a Rust-backed adapter."""

    @staticmethod
    def evaluate_thimble_lift(
        *,
        sites: Sequence[int],
        odd_cycle: Sequence[int],
        flow_time: float,  # tau in Morse downward gradient flow dz/dtau = -conj(dS/dz)
        majorana_pairing_basis: str = "time_reversal_kramers_invariant",
    ) -> Dict[str, Any]:
        """Refuse named functional output until a Rust-backed adapter exists."""
        require_rust_functional("MajoranaThimbleLiftCalculator.evaluate_thimble_lift")


# ── 5. Kagome Multi-Thimble & Stokes Phenomena Calculator ──────────────────

@dataclass(frozen=True)
class KagomeSaddlePoint:
    saddle_id: str
    action_real: float
    action_imag: float  # theta_sigma
    intersection_number: int  # n_sigma = <K_sigma, M_R>
    stability: str  # "STABLE_THIMBLE", "UNSTABLE", "DEGENERATE"


class KagomeMultiThimbleCalculator:
    """Legacy multi-thimble scoring interface awaiting a Rust-backed adapter."""

    @staticmethod
    def evaluate_kagome_thimbles(
        *,
        sites: Sequence[int],
        triangles: Sequence[Tuple[int, int, int]],
        flow_time: float,
        include_stokes_resummation: bool,
    ) -> Dict[str, Any]:
        """Refuse named functional output until a Rust-backed adapter exists."""
        require_rust_functional("KagomeMultiThimbleCalculator.evaluate_kagome_thimbles")


# ── 6. Category Adjunction & Sheaf Defect Calculator ───────────────────────

@dataclass(frozen=True)
class AdjunctionEvaluationState:
    adjunction_name: str
    left_functor: str
    right_functor: str
    unit_isomorphism_error: float   # || DefectToVariance(VarianceToDefect(c)) - c ||
    counit_isomorphism_error: float # || VarianceToDefect(DefectToVariance(s)) - s ||
    variance_growth_rate: float
    l1_sheaf_defect_norm: float
    is_exact_adjunction: bool
    score: ObstructionScore


class AdjunctionSheafDefectCalculator:
    """Legacy adjunction scoring interface awaiting a Rust-backed adapter."""

    @staticmethod
    def evaluate_adjunction(
        *,
        adjunction_name: str,
        stage_round: int,
        lattice_extent: int = 4,
    ) -> Dict[str, Any]:
        require_rust_functional("AdjunctionSheafDefectCalculator.evaluate_adjunction")



