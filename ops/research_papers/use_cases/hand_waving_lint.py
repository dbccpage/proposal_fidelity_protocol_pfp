"""Hand-waving lint: a regex scan for unhedged phrases in monograph prose.

The scan is a deterministic text check. Its findings are evidence for the Adversary bout's
critic seat (Act II, `seat_defect_hunter`); the criticism itself happens in the bout.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

VAGUE_HANDWAVY_PATTERNS = [
    r"\bvastly\s+superior\b",
    r"\bclearly\s+seen\b",
    r"\brapid\s+convergence\b",
    r"\bholds\s+generally\b",
    r"\bnaturally\s+follows\b",
    r"\bintuitive\s+proof\b",
    r"\btrivial\s+exercise\b",
    r"\bunprecedented\b",
    r"\bstate[- ]of[- ]the[- ]art\b",
]


@dataclass(frozen=True)
class HandWavingFinding:
    """One unhedged phrase, with the line it was found on."""

    line_number: int
    matched_phrase: str
    objection: str
    severity: str  # "BLOCKING", "MAJOR", "MINOR"


@dataclass(frozen=True)
class HandWavingReport:
    """The findings of one scan."""

    passed: bool
    findings: tuple[HandWavingFinding, ...]
    blocking_count: int
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


class HandWavingLint:
    """Scans prose for the phrases in `VAGUE_HANDWAVY_PATTERNS`."""

    @classmethod
    def scan(cls, content: str) -> HandWavingReport:
        findings: list[HandWavingFinding] = []
        for idx, line in enumerate(content.splitlines()):
            line_lower = line.lower()
            for pattern in VAGUE_HANDWAVY_PATTERNS:
                m = re.search(pattern, line_lower)
                if m:
                    phrase = m.group(0)
                    findings.append(
                        HandWavingFinding(
                            line_number=idx + 1,
                            matched_phrase=phrase,
                            objection=f"Hand-waving / unhedged assertion '{phrase}' detected. Provide exact mathematical bound or dual certificate.",
                            severity="BLOCKING",
                        )
                    )

        blocking = sum(1 for f in findings if f.severity == "BLOCKING")
        return HandWavingReport(
            passed=blocking == 0,
            findings=tuple(findings),
            blocking_count=blocking,
            authority_effect="None",
        )
