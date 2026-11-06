"""Reference Solver for Challenge C040 (M-Theory on Tori: Cremmer-Julia Scalar Counting).

AuthorityEffect: None.
"""

from __future__ import annotations

from .coset_algebra import get_branching, get_coset_info
from .ddc_tracer import DDCTracer
from .field_reduction import compute_scalars_breakdown, compute_vectors_breakdown
from .solver import get_last_tracer, is_exact_int, solve

__all__ = [
    "DDCTracer",
    "compute_scalars_breakdown",
    "compute_vectors_breakdown",
    "get_branching",
    "get_coset_info",
    "get_last_tracer",
    "is_exact_int",
    "solve",
]
