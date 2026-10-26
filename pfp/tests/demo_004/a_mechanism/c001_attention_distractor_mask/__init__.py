"""
c001_attention_distractor_mask
==============================
Symbol Game Mechanism Challenge C001: Distractor-Key Attention Masking at Task Level.

This package provides:
- pipeline.json: Frozen reproducible configuration.
- case_generator.py: Graph generator, distractor embedder, offset mapper, and test sets.
- solver.py: Exact integer potential propagation solver, cycle extractor, single repair, and witness audit.
- solve.py: Standard executable interface exposing def solve(case: dict) -> dict.
- test_m1_solvers.py: Targeted unit tests.
"""

from .case_generator import (
    CaseGenerator,
    generate_case,
    generate_hidden_base_set,
    generate_mutation_cases,
    generate_poisoned_cases,
    generate_public_set,
    generate_relabel_controls,
    map_spans_to_token_positions,
)
from .solve import solve
from .solver import (
    ConstraintSystem,
    PotentialSolver,
    audit_witness,
    extract_contradiction_cycle,
    format_int,
    host_verdict,
    is_canonical_int_str,
    solve_single_repair,
    verify_certificate,
)

__all__ = [
    "solve",
    "PotentialSolver",
    "host_verdict",
    "extract_contradiction_cycle",
    "solve_single_repair",
    "audit_witness",
    "verify_certificate",
    "ConstraintSystem",
    "format_int",
    "is_canonical_int_str",
    "CaseGenerator",
    "generate_case",
    "generate_public_set",
    "generate_hidden_base_set",
    "generate_relabel_controls",
    "generate_poisoned_cases",
    "generate_mutation_cases",
    "map_spans_to_token_positions",
]
