"""Protocol for Sovereign Rust Math Solvers (engine/crates_rs).

Enforces that Python domain code delegates exact mathematical computations
to native Rust crates rather than duplicating algorithms in pure Python.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Protocol, Tuple


class SovereignRustSolversPort(Protocol):
    """Protocol for interacting with sovereign Rust solvers."""

    def compute_exact_rank(self, matrix: List[List[Fraction]]) -> int:
        """Computes exact matrix rank via Bareiss integer fraction-free elimination."""
        ...

    def solve_l1_dual_witness(
        self,
        boundary_matrix: List[List[Fraction]],
        target_cochain: List[Fraction],
    ) -> Tuple[Tuple[Fraction, ...], Tuple[Fraction, ...], Fraction, Fraction]:
        """Solves primal-dual L1 quotient and returns (primal_potential, dual_flow, primal_cost, dual_value)."""
        ...

    def compute_betti_numbers(self, simplicial_edges: List[Tuple[str, str]]) -> Tuple[int, int]:
        """Computes Betti numbers (b_0, b_1) via exact boundary complexes."""
        ...

    def validate_ddc_transition(
        self,
        rune: str,
        input_state_json: str,
    ) -> Dict[str, Any]:
        """Validates a DDC operational move using the core_wdp::ddc module."""
        ...
