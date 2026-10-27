"""Unstated-premise questions: keyword checks that ask about premises a monograph leaves out.

The checks only raise questions; they do not report a descent. The questions are evidence
for the Adversary bout, which owns the Act IV gauge break (`seat_primal_dual`).

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PremiseQuestion:
    """A question about one premise the text assumes without stating it."""

    question_id: str
    premise_under_attack: str
    inquiry: str


class UnstatedPremiseQuestions:
    """Asks about premises a monograph leaves unstated."""

    @staticmethod
    def ask(abstract: str, monograph_text: str) -> tuple[PremiseQuestion, ...]:
        questions: list[PremiseQuestion] = []
        if "obviously" in monograph_text.lower():
            questions.append(
                PremiseQuestion(
                    question_id="SQ_001",
                    premise_under_attack="Self-evident correctness",
                    inquiry="On what exact finite carrier is this step verified without circular dependency?",
                )
            )
        if "continuum" in abstract.lower() and "interval" not in monograph_text.lower():
            questions.append(
                PremiseQuestion(
                    question_id="SQ_002",
                    premise_under_attack="Continuum assumption without enclosure",
                    inquiry="How is the continuum shadow bounded? Exhibit the convex interval enclosure [lo, hi].",
                )
            )
        return tuple(questions)
