"""P1 abstention and impossibility governor: typed report skeleton.

The labels are WDP-CHS-D03's report table plus the two outcomes the reference
reporter (``code/certified_progress/reporting.py``) also emits. AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from fractions import Fraction
from typing import Literal, Protocol

from pydantic import Field, model_validator

from omega_engine_applications.wdp_products.base import FrozenModel
from omega_engine_applications.wdp_products.kernel.contracts import (
    CheckReceipt,
    TypedRefusal,
    is_rational_text,
)


class TerminationLabel(str, Enum):
    # WDP-CHS-D03 report table.
    REFUSED = "Refused"
    STALLED = "Stalled"
    EXHAUSTED = "Exhausted"
    IMPOSSIBLE = "Impossible"
    LOSING_IN_DECLARED_ARENA = "LosingInDeclaredArena"
    UNDETERMINED_BUDGET = "UndeterminedBudget"
    # Invalid certificate; not a controller refusal (WDP-CHS-D03, paragraph after the table).
    REFUSED_CERTIFICATE = "RefusedCertificate"
    # Successful terminal, as named by the reference reporter.
    RESOLVED_WITHIN_BUDGET = "ResolvedWithinBudget"


D03_TABLE_LABELS = frozenset(
    {
        TerminationLabel.REFUSED,
        TerminationLabel.STALLED,
        TerminationLabel.EXHAUSTED,
        TerminationLabel.IMPOSSIBLE,
        TerminationLabel.LOSING_IN_DECLARED_ARENA,
        TerminationLabel.UNDETERMINED_BUDGET,
    }
)


def derive_label(
    check: CheckReceipt, budget: str, *, task_admits_impossibility: bool
) -> TerminationLabel:
    """The label WDP-CHS-D03 assigns to a checked certificate.

    Same precedence as the reference ``report_termination``: invalid certificate,
    then loss (stalled before trapped), then value against budget, then claim kind.
    """
    if not check.accepted:
        return TerminationLabel.REFUSED_CERTIFICATE
    if check.claim == "LOSS":
        if check.initial_stalled:
            return TerminationLabel.STALLED
        if task_admits_impossibility:
            return TerminationLabel.IMPOSSIBLE
        return TerminationLabel.LOSING_IN_DECLARED_ARENA
    assert check.initial_value is not None  # CheckReceipt enforces this for accepted wins.
    if Fraction(check.initial_value) <= Fraction(budget):
        return TerminationLabel.RESOLVED_WITHIN_BUDGET
    if check.claim == "WIN_OPTIMAL":
        return TerminationLabel.EXHAUSTED
    return TerminationLabel.UNDETERMINED_BUDGET


class GovernorReport(FrozenModel):
    """Exactly one label, and only the label the receipt and budget support under D03."""

    label: TerminationLabel
    task_admits_impossibility: bool
    budget: str
    check: CheckReceipt | None = None
    evidence_refs: tuple[str, ...] = Field(default=())
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _evidence_matches_label(self) -> GovernorReport:
        if not is_rational_text(self.budget):
            raise ValueError("budget must be an exact rational string")
        if self.label is TerminationLabel.REFUSED:
            if self.check is not None:
                raise ValueError(
                    "Refused is a controller action and carries no certificate receipt; "
                    "an invalid certificate is RefusedCertificate (WDP-CHS-D03)"
                )
            if not self.evidence_refs:
                raise ValueError(
                    "Refused needs the declared refusal action the controller performed"
                )
            return self
        if self.check is None:
            raise ValueError(f"{self.label.value} requires a checked certificate receipt")
        expected = derive_label(
            self.check, self.budget, task_admits_impossibility=self.task_admits_impossibility
        )
        if self.label is not expected:
            raise ValueError(
                f"{self.label.value} is not supported by the receipt and budget; "
                f"WDP-CHS-D03 gives {expected.value}"
            )
        return self


class AbstentionGovernor(Protocol):
    """Wraps an agent loop declared as a finite belief arena (WDP-CHS-D01)."""

    def report(
        self, model: object, certificate: object, budget: str, *, task_admits_impossibility: bool
    ) -> GovernorReport | TypedRefusal: ...


GovernorReport.model_rebuild()
