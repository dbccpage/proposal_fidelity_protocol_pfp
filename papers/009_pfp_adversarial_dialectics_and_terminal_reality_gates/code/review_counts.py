"""Descriptive counts against historical checker labels, not physical ground truth."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any


@dataclass(frozen=True)
class Counts:
    true_positive: int = 0
    false_negative: int = 0
    false_positive: int = 0
    true_negative: int = 0

    @property
    def total(self) -> int:
        return (self.true_positive + self.false_negative
                + self.false_positive + self.true_negative)

    def rates(self) -> dict[str, Fraction | None]:
        """Undefined denominators stay undefined. All defined fractions are exact."""
        def ratio(numerator: int, denominator: int) -> Fraction | None:
            return Fraction(numerator, denominator) if denominator else None

        return {
            "challenge_among_refused": ratio(
                self.true_positive, self.true_positive + self.false_negative),
            "challenge_among_not_refused": ratio(
                self.false_positive, self.false_positive + self.true_negative),
            "refused_among_challenges": ratio(
                self.true_positive, self.true_positive + self.false_positive),
            "agreement_with_historical_labels": ratio(
                self.true_positive + self.true_negative, self.total),
        }


def recount(rows: Sequence[Mapping[str, Any]]) -> Counts:
    """Check label consistency and tally CHALLENGE/CONCUR against recorded status.

    The constant adversary_caught_am flag is deliberately unused. This accepts
    the two status strings of the deposited trace, not arbitrary checker APIs.
    Dataset completeness and byte identity require separate custody checks.
    """
    cells = {(True, "CHALLENGE"): 0, (True, "CONCUR"): 0,
             (False, "CHALLENGE"): 0, (False, "CONCUR"): 0}
    statuses = {"Refused_AM_FSP_2_FrustratedObstruction": True,
                "OpenSignObstruction": False}
    for row in rows:
        label = row["proposer_hallucination"]
        if type(label) is not bool:
            raise TypeError("historical label must be a Boolean, not a truthy value")
        status = row["proposer_status"]
        if status not in statuses or statuses[status] is not label:
            raise ValueError("unknown status or label/status disagreement")
        verdict = row["adversary_critique"]["adversary_verdict"]
        if verdict not in {"CHALLENGE", "CONCUR"}:
            raise ValueError("unknown adversary verdict")
        cells[label, verdict] += 1
    return Counts(cells[True, "CHALLENGE"], cells[True, "CONCUR"],
                  cells[False, "CHALLENGE"], cells[False, "CONCUR"])
