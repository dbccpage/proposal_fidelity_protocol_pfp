"""AST structural checks and a fail-closed functional evaluation boundary.

Dependency complexes can be built in Python. Their PHI and GAMMA2 values
require an adapter backed by ``omega_functional`` before a report is emitted.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

from omega_engine_pfp.functional_boundary import require_rust_functional

from .ast_dependency_complex import DependencyComplex
from .ast_models import ASTEvaluationReport


def verify_exactness(
    d1: np.ndarray, d0: np.ndarray, tolerance: float = 1e-9
) -> Tuple[bool, float]:
    """Check the structural chain-complex condition d1 . d0 = 0."""
    d1 = np.asarray(d1, dtype=float)
    d0 = np.asarray(d0, dtype=float)
    if d1.ndim != 2 or d0.ndim != 2 or d1.shape[1] != d0.shape[0]:
        return False, 1.0
    composite = d1 @ d0
    max_defect = float(np.max(np.abs(composite))) if composite.size else 0.0
    return max_defect <= tolerance, max_defect


def gamma2(d1: np.ndarray, h: np.ndarray, tolerance: float = 1e-9) -> None:
    """Legacy entry point retained to refuse off-boundary GAMMA2 computation."""
    require_rust_functional("ast_metrics_evaluator.gamma2")


def solve_phi(
    B: np.ndarray, omega: np.ndarray, weights: Optional[np.ndarray] = None
) -> None:
    """Legacy entry point retained to refuse off-boundary PHI computation."""
    require_rust_functional("ast_metrics_evaluator.solve_phi")


class ASTMetricsEvaluator:
    """Refuse named functional values until a Rust-backed adapter is wired."""

    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance

    def evaluate(self, complex_: DependencyComplex) -> ASTEvaluationReport:
        require_rust_functional("ASTMetricsEvaluator.evaluate")

    @staticmethod
    def empty_report() -> ASTEvaluationReport:
        require_rust_functional("ASTMetricsEvaluator.empty_report")
