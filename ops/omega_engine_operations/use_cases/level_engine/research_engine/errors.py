# Research-grade adapter; AuthorityEffect: None; not a production verifier.
# Rust port pending; source custody is recorded in the Level Engine migration ledger.
"""Typed refusals.  Every refusal the harness raises carries one exact code.

Classification: metatheory apparatus.

AuthorityEffect: None
"""

from __future__ import annotations


class Refusal(Exception):
    """A refusal by name.  ``code`` is exact and stable; ``detail`` is prose."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}" if detail else code)
        self.code = code
        self.detail = detail


class ExactError(Refusal):
    """Exact arithmetic or serialization refused a value (``RR-FLOAT`` etc.)."""


class EmbargoRefusal(Refusal):
    """The embargo guard refused a request before any computation."""


class ClaimFrozen(Refusal):
    """A response tried to touch a claim form."""


class NonDescent(Refusal):
    """A term outside the old image has no old meaning."""


class NonAdmissible(Refusal):
    """Sealed admission refused a hosting event."""


class IntakeRefusal(Refusal):
    """Intake refused a fixture, spec or checker pin."""


class StageRefusal(Refusal):
    """The stage-change contract refused a proposal or an execution."""
