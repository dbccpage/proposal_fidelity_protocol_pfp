"""Re-export of exact Verlinde and combinatorial engine for C037.

AuthorityEffect: None.
"""

from .verlinde import (
    combinatorial_su2,
    compute_fusion_minimal,
    compute_fusion_su2,
    format_rational,
    get_canonical_kac_label,
    get_minimal_model_primaries,
    is_exact_int,
    solve_c037_case,
    verlinde_su2_exact,
)

__all__ = [
    "is_exact_int",
    "format_rational",
    "verlinde_su2_exact",
    "combinatorial_su2",
    "get_canonical_kac_label",
    "get_minimal_model_primaries",
    "compute_fusion_su2",
    "compute_fusion_minimal",
    "solve_c037_case",
]
