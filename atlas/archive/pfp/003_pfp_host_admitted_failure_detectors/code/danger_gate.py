"""Two-signal decision table for PFP Paper 003 (package re-implementation).

The name "danger gate" is a component name only. The computation is a
four-way decision over two supplied inputs:

- Signal 1 (a pattern match) alone: DIAGNOSTIC_ONLY, no refusal.
- Signal 2 (a supplied structural defect) alone, low or medium severity:
  DIAGNOSTIC_ONLY, no refusal.
- Signal 2 alone, high or critical severity: DEFENSIVE_LOCKDOWN, refusal.
- Both signals: QUARANTINED, refusal.
- Neither: TOLERATED.

The table does not check that a supplied defect is real or authenticate its
evidence identifier. The repository gate at the paper's baseline differs in two
ways (paper Section 4.1): it counts a Signal 2 record only when its defect count
is positive, and it labels a two-signal refusal DEFENSIVE_LOCKDOWN when the
defect is low or medium.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence


class DangerDecision(str, Enum):
    TOLERATED = "TOLERATED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    DEFENSIVE_LOCKDOWN = "DEFENSIVE_LOCKDOWN"
    QUARANTINED = "QUARANTINED"


class DangerSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class Signal1Match:
    epitope_name: str
    pattern_matched: str
    confidence_num: int = 1
    confidence_den: int = 1
    offset: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "epitope_name": self.epitope_name,
            "pattern_matched": self.pattern_matched,
            "confidence_num": self.confidence_num,
            "confidence_den": self.confidence_den,
            "offset": self.offset,
        }


@dataclass(frozen=True)
class Signal2Danger:
    danger_type: str
    severity: str = "MEDIUM"
    defect_count: int = 1
    evidence_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "danger_type": self.danger_type,
            "severity": self.severity,
            "defect_count": self.defect_count,
            "evidence_digest": self.evidence_digest,
        }


@dataclass(frozen=True)
class TwoSignalDecision:
    decision: str
    is_refusal: bool
    disposition: str
    signal1_count: int
    signal2_severity: str | None
    is_suppressed: bool
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision,
            "is_refusal": self.is_refusal,
            "disposition": self.disposition,
            "signal1_count": self.signal1_count,
            "signal2_severity": self.signal2_severity,
            "is_suppressed": self.is_suppressed,
            "rationale": self.rationale,
        }


def evaluate_two_signal_gate(
    signal1_matches: Sequence[Signal1Match] | Sequence[dict[str, Any]],
    signal2: Signal2Danger | dict[str, Any] | None = None,
) -> TwoSignalDecision:
    s1_list: list[Signal1Match | dict[str, Any]] = list(signal1_matches)
    s1_count = len(s1_list)
    has_s1 = s1_count > 0

    s2_obj: Signal2Danger | None = None
    if isinstance(signal2, dict):
        s2_obj = Signal2Danger(
            danger_type=signal2.get("danger_type", "UNKNOWN_DEFECT"),
            severity=signal2.get("severity", "MEDIUM"),
            defect_count=signal2.get("defect_count", 1),
            evidence_digest=signal2.get("evidence_digest", ""),
        )
    elif isinstance(signal2, Signal2Danger):
        s2_obj = signal2

    if has_s1 and s2_obj is not None:
        first_name = (
            s1_list[0].epitope_name
            if isinstance(s1_list[0], Signal1Match)
            else s1_list[0].get("epitope_name", "UNKNOWN")
        )
        return TwoSignalDecision(
            decision=DangerDecision.QUARANTINED.value,
            is_refusal=True,
            disposition="REFUSED_DUAL_SIGNAL_CORROBORATION",
            signal1_count=s1_count,
            signal2_severity=s2_obj.severity,
            is_suppressed=True,
            rationale=(
                f"Both Signal 1 (syntax pattern: {first_name}) and Signal 2 "
                f"(structural damage: {s2_obj.severity}) detected."
            ),
        )

    if not has_s1 and s2_obj is not None:
        sev = s2_obj.severity.upper()
        if sev in ("HIGH", "CRITICAL"):
            return TwoSignalDecision(
                decision=DangerDecision.DEFENSIVE_LOCKDOWN.value,
                is_refusal=True,
                disposition="REFUSED_CRITICAL_STRUCTURAL_DEFECT",
                signal1_count=0,
                signal2_severity=s2_obj.severity,
                is_suppressed=True,
                rationale=(
                    f"High/Critical Signal 2 defect ({s2_obj.danger_type}) "
                    "without Signal 1 match triggers defensive lockdown."
                ),
            )
        return TwoSignalDecision(
            decision=DangerDecision.DIAGNOSTIC_ONLY.value,
            is_refusal=False,
            disposition="DIAGNOSTIC_LOW_SEVERITY_DEFECT",
            signal1_count=0,
            signal2_severity=s2_obj.severity,
            is_suppressed=False,
            rationale=(
                f"Low/Medium Signal 2 defect ({s2_obj.danger_type}) retained "
                "as diagnostic observation without refusal."
            ),
        )

    if has_s1 and s2_obj is None:
        first_name = (
            s1_list[0].epitope_name
            if isinstance(s1_list[0], Signal1Match)
            else s1_list[0].get("epitope_name", "UNKNOWN")
        )
        return TwoSignalDecision(
            decision=DangerDecision.DIAGNOSTIC_ONLY.value,
            is_refusal=False,
            disposition="DIAGNOSTIC_SYNTAX_MATCH_ONLY",
            signal1_count=s1_count,
            signal2_severity=None,
            is_suppressed=False,
            rationale=(
                f"Signal 1 pattern match ({first_name}) without Signal 2 "
                "structural damage is diagnostic only."
            ),
        )

    return TwoSignalDecision(
        decision=DangerDecision.TOLERATED.value,
        is_refusal=False,
        disposition="TOLERATED_CLEAN_PROPOSAL",
        signal1_count=0,
        signal2_severity=None,
        is_suppressed=False,
        rationale="Neither syntactic violation nor structural defect detected.",
    )
