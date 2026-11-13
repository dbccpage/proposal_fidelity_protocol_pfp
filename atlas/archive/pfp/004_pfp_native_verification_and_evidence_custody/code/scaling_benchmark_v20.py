"""
Historical scaling benchmark entrypoint: now delegates to the governor's compute_phi1.

Solves the L1 primary obstruction problem:
    min_{f in Q^V} sum_{e=(u,v) in E} w_e |claim_e - (f(v) - f(u))|
through l1_symbol_game_governor.compute_phi1, which asks the pinned native graph
calculator first and falls back to exact Python enumeration of spanning-tree
potentials when that call raises. The former Python LP-versus-enumeration
comparison is retired because both names now reach one implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

try:
    from .l1_symbol_game_governor import (
        Cochain1,
        ConstraintGraph,
        compute_phi1,
    )
except (ImportError, ValueError):
    from l1_symbol_game_governor import (
        Cochain1,
        ConstraintGraph,
        compute_phi1,
    )


def solve_phi1_lp_exact_basis(
    graph: ConstraintGraph,
    claims: Cochain1,
) -> Tuple[Fraction, Dict[str, Fraction]]:
    """Alias of compute_phi1; exact rational arithmetic, no floating-point Phi1.

    This no longer benchmarks the former Python LP implementation. A native
    refusal (for example an exceeded exhaustive-search bound) is caught by
    compute_phi1, which then enumerates spanning-tree potentials in Python.
    """
    return compute_phi1(graph, claims)


@dataclass(frozen=True)
class ScalingTrialResult:
    """Benchmark result for a single graph size trial."""
    num_vertices: int
    num_edges: int
    phi1_val: Fraction
    lp_runtime_sec: float
    enum_runtime_sec: Optional[float]
    speedup_factor: Optional[float]
    exact_match: bool


def run_scaling_benchmark(
    vertex_counts: Sequence[int] = (4, 6, 8, 12, 20, 50),
    seed: int = 42,
) -> List[ScalingTrialResult]:
    """The historical comparison is invalid after both APIs share one owner."""
    raise RuntimeError("BENCHMARK_RETIRED: both paths now use canonical Rust graph enumeration; "
                       "no independent LP-versus-enumeration speedup can be reported")


__all__ = ['ScalingTrialResult', 'run_scaling_benchmark', 'solve_phi1_lp_exact_basis']
