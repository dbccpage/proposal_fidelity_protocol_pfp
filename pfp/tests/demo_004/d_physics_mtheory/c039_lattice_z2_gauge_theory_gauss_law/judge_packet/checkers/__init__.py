"""Dual checkers package for Challenge C039."""

from .dual_evaluator import (
    CheckerDisagreementError,
    EvaluationResult,
    assert_dual_agreement,
    evaluate_answer,
    evaluate_dual,
)
from .homology_cohomology_checker import verify_homology_cohomology_certificate
from .stabilizer_tableau_checker import verify_stabilizer_tableau_certificate

__all__ = [
    "CheckerDisagreementError",
    "EvaluationResult",
    "assert_dual_agreement",
    "evaluate_answer",
    "evaluate_dual",
    "verify_homology_cohomology_certificate",
    "verify_stabilizer_tableau_certificate",
]
