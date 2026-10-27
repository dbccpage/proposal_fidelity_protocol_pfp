"""Diagnostic classification contracts; neither record authenticates evidence."""

from __future__ import annotations

from typing import Literal

from .gate_contracts import Text, Wire


GateClassificationStatus = Literal[
    "PASSED_PREDICATE", "FINITE_PREDICATE_FAILURE", "ATTEMPT_POLICY_FAILURE",
    "MISSING_WITNESS", "INVALID_INPUT_OR_BINDING", "UNTRUSTED_OBSERVATION",
    "FORWARDED_REFUSAL", "UNSUPPORTED_OBSERVATION",
]


class GateOutcomeClassification(Wire):
    gate_id: Text
    status: GateClassificationStatus
    evidence_grade: Text
    reason: Text

    def to_json(self) -> dict:
        return self.model_dump(mode="json")


class GateOccurrenceCapability(Wire):
    gate_id: Text
    profiles: tuple[Text, ...]
    finite_failure_codes: tuple[Text, ...] = ()
    policy_failure_codes: tuple[Text, ...] = ()
    scope: Text

    def to_json(self) -> dict:
        return self.model_dump(mode="json")
