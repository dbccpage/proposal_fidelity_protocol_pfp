"""Dual Independent Checkers and Evaluator for Challenge C038.

AuthorityEffect: None.
"""

from .combinatorial_primal_checker import verify_combinatorial_primal_certificate
from .dual_evaluator import (
    CheckerDisagreementError,
    EvaluationResult,
    assert_dual_agreement,
    evaluate_answer,
    evaluate_dual,
)
from .homology_dual_potential_checker import (
    verify_homology_dual_potential_certificate,
)

__all__ = [
    "verify_combinatorial_primal_certificate",
    "verify_homology_dual_potential_certificate",
    "evaluate_answer",
    "evaluate_dual",
    "assert_dual_agreement",
    "EvaluationResult",
    "CheckerDisagreementError",
]
