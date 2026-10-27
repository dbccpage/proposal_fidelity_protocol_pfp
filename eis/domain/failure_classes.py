"""Innate barrier failure classes and pattern detection.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List


@dataclass(frozen=True)
class InnateFinding:
    """Finding emitted by innate pattern detector."""
    failure_class: str
    span: str = ""
    rationale: str = ""


from eis.domain.definitions_loader import (
    load_screening_vocabulary,
)

_vocab = load_screening_vocabulary()
_innate = _vocab.get("innate_patterns", {})


class InnatePatternDetectorV1:
    """Scans text for unbacked authority mimicry, self-certification, or fake receipts."""

    def scan_text(self, text: str, host_receipt: Any = None) -> List[InnateFinding]:
        findings: List[InnateFinding] = []
        lowered = text.lower()
        if host_receipt is None:
            pal = _innate.get("PersonaAuthorityLeak", {})
            if any(p in lowered for p in pal.get("patterns", ())):
                findings.append(
                    InnateFinding(
                        failure_class="PersonaAuthorityLeak",
                        rationale=pal.get("rationale", "Unbacked system administration / persona authority claim without host receipt"),
                    )
                )
            sc = _innate.get("SelfCertification", {})
            if any(p in lowered for p in sc.get("patterns", ())):
                findings.append(
                    InnateFinding(
                        failure_class="SelfCertification",
                        rationale=sc.get("rationale", "Self-certified verification or authorization bypass"),
                    )
                )
            fr = _innate.get("FakeReceipt", {})
            if any(p in lowered for p in fr.get("patterns", ())):
                findings.append(
                    InnateFinding(
                        failure_class="FakeReceipt",
                        rationale=fr.get("rationale", "Host-only receipt assertion without host cryptographic signature"),
                    )
                )
        return findings
