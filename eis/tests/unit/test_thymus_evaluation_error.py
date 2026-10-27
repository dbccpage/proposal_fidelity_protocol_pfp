"""A regex compile failure is an evaluation error, not a silent non-admission.

AuthorityEffect: None.
"""

from __future__ import annotations

from eis.domain.thymus import CandidateDetector, ThymusGate


def test_invalid_pattern_surfaces_evaluation_error() -> None:
    gate = ThymusGate(self_panel=("clean fixture",))
    refused = gate.evaluate_candidate(CandidateDetector(pattern="["))
    assert refused.self_tolerant is False
    assert refused.is_admitted is False
    assert refused.evaluation_error is not None
    assert refused.evaluation_error.startswith("error:")

    clean = gate.evaluate_candidate(CandidateDetector(pattern="forbidden"))
    assert clean.self_tolerant is True
    assert clean.is_admitted is False
    assert clean.evaluation_error is None
