# AuthorityEffect: None.
"""Reference solver package for C026."""

from .ddc_tracer import DDCTracer
from .gaussian_rational import GaussianRat, format_fraction, parse_fraction
from .kronecker import extend_local_matrix
from .linear_algebra import (
    compute_left_inverse,
    compute_rref_and_kernel,
    invert_matrix,
    mat_add,
    mat_dagger,
    mat_mul,
    mat_scale,
    mat_trace,
)
from .projector_validator import validate_projector
from .solver import solve

__all__ = [
    "solve",
    "GaussianRat",
    "format_fraction",
    "parse_fraction",
    "extend_local_matrix",
    "mat_mul",
    "mat_dagger",
    "mat_add",
    "mat_scale",
    "mat_trace",
    "invert_matrix",
    "compute_rref_and_kernel",
    "compute_left_inverse",
    "validate_projector",
    "DDCTracer",
]
