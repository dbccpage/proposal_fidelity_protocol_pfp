"""Checkers package for Challenge C036: Genus-Zero Invariants of the Quintic via Mirror Symmetry.

AuthorityEffect: None.
"""

from .dual_evaluator import (
    CheckerDisagreementError,
    EvaluationResult,
    assert_dual_agreement,
    evaluate_answer,
    evaluate_dual,
)
from .hypergeometric_mirror_checker import (
    verify_hypergeometric_mirror_certificate,
)
from .picard_fuchs_recurrence_checker import (
    verify_picard_fuchs_recurrence_certificate,
)

__all__ = [
    "verify_hypergeometric_mirror_certificate",
    "verify_picard_fuchs_recurrence_certificate",
    "evaluate_answer",
    "evaluate_dual",
    "assert_dual_agreement",
    "CheckerDisagreementError",
    "EvaluationResult",
]
