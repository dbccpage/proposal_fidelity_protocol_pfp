"""Independent checkers and dual consensus evaluator for Challenge C037.

AuthorityEffect: None.
"""

from .combinatorial_fusion_checker import (
    verify_combinatorial_fusion_certificate,
    verify_combinatorial_fusion_checker,
)
from .dual_evaluator import (
    CheckerDisagreementError,
    EvaluationResult,
    assert_dual_agreement,
    evaluate_answer,
    evaluate_dual,
)
from .verlinde_cyclotomic_checker import (
    verify_verlinde_cyclotomic_certificate,
    verify_verlinde_cyclotomic_checker,
)

__all__ = [
    "verify_verlinde_cyclotomic_certificate",
    "verify_verlinde_cyclotomic_checker",
    "verify_combinatorial_fusion_certificate",
    "verify_combinatorial_fusion_checker",
    "CheckerDisagreementError",
    "EvaluationResult",
    "evaluate_answer",
    "evaluate_dual",
    "assert_dual_agreement",
]
