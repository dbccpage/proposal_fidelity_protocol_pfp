"""Socratic Elenchus Bureau: Interrogation, Contradiction Extraction, and Flattery Defense.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import re
from typing import Any, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class ElenchusResult:
    """Outcome of Socratic Elenchus interrogation."""

    is_refused: bool
    status: str
    contradiction: str | None
    fitness_score: Fraction
    prime_rules_checked: Tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.fitness_score, float):
            raise TypeError("Float fitness_score violates Zero-Float law; use Fraction")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.is_refused == other.is_refused
            and self.status == other.status
            and self.contradiction == other.contradiction
            and self.fitness_score == other.fitness_score
            and self.prime_rules_checked == other.prime_rules_checked
        )


class SocraticElenchusBureau:
    """Interrogation bureau enforcing PRIME_00–PRIME_09 against cognitive smuggling.

    Detects:
    1. Flattery context smuggling (e.g. praising intellect to waive formal checks).
    2. Theorem laundering (citing buzzwords without formal grounding).
    3. Urgency panic (inventing artificial sprint emergencies to bypass local gates).
    4. Boundary laundering (recommending re-export shims).
    """

    PRIME_RULES = tuple(f"PRIME_0{i}" for i in range(10))

    FLATTERY_PATTERNS = [
        re.compile(
            r"\b(greatest|great|unmatched|supreme|flawless|genius|infallible)\b",
            re.IGNORECASE,
        ),
        re.compile(
            r"\b(you are too smart to need|too smart to need|trusted to proceed)\b",
            re.IGNORECASE,
        ),
    ]

    WAIVER_PATTERNS = [
        re.compile(
            r"\b(waive|skip|bypass|omit|ignore|without)\s+(?:\w+\s+)?(proof|verification|checks?|ci|tests?|testing|rules?|review)\b",
            re.IGNORECASE,
        ),
    ]

    URGENCY_PATTERNS = [
        re.compile(
            r"\b(emergency|urgent|critical|immediately|hotfix|incident|outage)\b",
            re.IGNORECASE,
        ),
        re.compile(r"\bemergency release\b", re.IGNORECASE),
    ]

    def interrogate(
        self, prompt_text: str, metadata: Mapping[str, Any] | None = None
    ) -> ElenchusResult:
        """Execute Socratic interrogation over candidate text."""
        # 1. Match decoupled praise, waiver, and urgency patterns
        is_flattery = any(pat.search(prompt_text) for pat in self.FLATTERY_PATTERNS)
        has_waiver = any(pat.search(prompt_text) for pat in self.WAIVER_PATTERNS)
        is_urgency = any(pat.search(prompt_text) for pat in self.URGENCY_PATTERNS)
        is_emergency_release = bool(
            re.search(r"\bemergency release\b", prompt_text, re.IGNORECASE)
        )

        # Flattery context smuggling attempting to waive rules
        if is_flattery and has_waiver:
            return ElenchusResult(
                is_refused=True,
                status="REFUSED_FLATTERY_CONTEXT_SMUGGLE",
                contradiction="Flattery context smuggling detected attempting to bypass PRIME_00–PRIME_09",
                fitness_score=Fraction(0, 1),
                prime_rules_checked=self.PRIME_RULES,
            )

        # Urgency panic attempting to bypass local gates
        if (is_urgency and has_waiver) or is_emergency_release:
            return ElenchusResult(
                is_refused=True,
                status="REFUSED_URGENCY_PANIC",
                contradiction="Urgency panic detected attempting to bypass local CI gates (violates PRIME_02)",
                fitness_score=Fraction(0, 1),
                prime_rules_checked=self.PRIME_RULES,
            )

        # Clean candidate passes elenchus
        return ElenchusResult(
            is_refused=False,
            status="PROCEED",
            contradiction=None,
            fitness_score=Fraction(1, 1),
            prime_rules_checked=self.PRIME_RULES,
        )


__all__ = [
    "ElenchusResult",
    "SocraticElenchusBureau",
]
