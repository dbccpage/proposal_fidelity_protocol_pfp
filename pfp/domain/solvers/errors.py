"""Domain solver errors, refusals, and invariant failures.

AuthorityEffect: None.
"""

from __future__ import annotations

from ..exact.errors import ExactError, ExactRefusal


class SolverRefusal(ExactRefusal):
    """Base refusal for solver obligations and admissions."""


Refusal = SolverRefusal


class EmbargoRefusal(SolverRefusal):
    """The embargo guard refused a request before any computation."""


class ClaimFrozen(SolverRefusal):
    """A response attempted to touch a frozen claim form."""


class NonDescent(SolverRefusal):
    """A term outside the old image has no old meaning."""


class NonAdmissible(SolverRefusal):
    """Sealed admission refused a hosting event."""


class IntakeRefusal(SolverRefusal):
    """Intake refused a fixture, spec, or checker pin."""


class StageRefusal(SolverRefusal):
    """The stage-change contract refused a proposal or an execution."""


__all__ = [
    "ClaimFrozen",
    "EmbargoRefusal",
    "ExactError",
    "IntakeRefusal",
    "NonAdmissible",
    "NonDescent",
    "Refusal",
    "SolverRefusal",
    "StageRefusal",
]
