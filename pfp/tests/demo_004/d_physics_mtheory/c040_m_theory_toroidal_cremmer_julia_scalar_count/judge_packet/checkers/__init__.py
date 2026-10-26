"""Checkers for Challenge C040: Field Reduction, Coset Group Theory, and Dual Evaluator.

AuthorityEffect: None.
"""

from __future__ import annotations

from .coset_group_theory_checker import verify_coset_group_theory_certificate
from .dual_evaluator import (
    CheckerDisagreementError,
    EvaluationResult,
    assert_dual_agreement,
    evaluate_answer,
    evaluate_dual,
)
from .field_reduction_checker import verify_field_reduction_certificate

__all__ = [
    "CheckerDisagreementError",
    "EvaluationResult",
    "assert_dual_agreement",
    "evaluate_answer",
    "evaluate_dual",
    "verify_coset_group_theory_certificate",
    "verify_field_reduction_certificate",
]
