"""Legacy Symbol Game copy of the two-signal danger gate.

Legacy (see the package docstring). Unlike the OEEIS gate
(`omega_engine_epistemic_immune_system.domain.danger_gate`), this copy puts a
HIGH or CRITICAL Signal 2 alone into DEFENSIVE_LOCKDOWN, so it is not a strict
two-signal rule, and it does not check that Signal 2 is independent of Signal 1.

Strict ZERO-FLOAT Law: All confidence scores, thresholds, and metrics must use
fractions.Fraction or exact rational types. Float values strictly raise TypeError.

Logic Tensor:
- Signal 1 alone (syntax/AST motif match) -> DIAGNOSTIC_ONLY (is_refusal=False).
- Signal 1 + Signal 2 (concrete defect/alarmin) -> REFUSE (is_refusal=True, QUARANTINED/DEFENSIVE_LOCKDOWN).
- Signal 2 alone (anomalous defect) -> DEFENSIVE_LOCKDOWN / DIAGNOSTIC_ONLY depending on severity.
- Neither -> TOLERATED.

Zero outward dependencies. Exact-type equality enforced on all Value Objects.
AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Any, Sequence


def _assert_zero_float(val: Any, field_name: str) -> None:
    if isinstance(val, float):
        raise TypeError(
            f"ZERO-FLOAT Invariant violated on {field_name}: float values are strictly forbidden; "
            "use fractions.Fraction or Q"
        )


class DangerDecision(str, Enum):
    """Four-way disposition of the Two-Signal Danger Gate."""

    TOLERATED = "TOLERATED"
    DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
    DEFENSIVE_LOCKDOWN = "DEFENSIVE_LOCKDOWN"
    QUARANTINED = "QUARANTINED"


class DangerSeverity(str, Enum):
    """Categorical severity scale for Signal 2 danger indications."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class Signal1AstMatch:
    """Epitope / AST syntactic pattern match (Signal 1)."""

    epitope_name: str
    pattern_matched: str
    confidence: Fraction
    offset: int = 0

    def __post_init__(self) -> None:
        _assert_zero_float(self.confidence, "confidence")
        if not isinstance(self.epitope_name, str) or isinstance(self.epitope_name, bool):
            raise TypeError(f"epitope_name must be a str, got {type(self.epitope_name).__name__}")
        if not isinstance(self.pattern_matched, str) or isinstance(self.pattern_matched, bool):
            raise TypeError(f"pattern_matched must be a str, got {type(self.pattern_matched).__name__}")
        if not isinstance(self.confidence, (int, Fraction)) or isinstance(self.confidence, bool):
            # Check for custom Q type with .num and .den
            if hasattr(self.confidence, "num") and hasattr(self.confidence, "den"):
                pass
            else:
                raise TypeError(f"confidence must be Fraction, int, or Q, got {type(self.confidence).__name__}")
        conf_frac = Fraction(self.confidence.num, self.confidence.den) if hasattr(self.confidence, "num") else Fraction(self.confidence)
        if not (Fraction(0, 1) <= conf_frac <= Fraction(1, 1)):
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence}")
        if not isinstance(self.offset, int) or isinstance(self.offset, bool) or self.offset < 0:
            raise ValueError(f"offset must be non-negative int, got {self.offset}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Signal1AstMatch)
        return (
            self.epitope_name == other.epitope_name
            and self.pattern_matched == other.pattern_matched
            and self.confidence == other.confidence
            and self.offset == other.offset
        )

    def __hash__(self) -> int:
        return hash((type(self), self.epitope_name, self.pattern_matched, self.confidence, self.offset))


# Compatibility alias
Signal1Match = Signal1AstMatch


@dataclass(frozen=True, slots=True)
class Signal2DangerState:
    """Structural / authority / integrity damage indicator (Signal 2 - Danger/Alarmin)."""

    danger_type: str
    severity: DangerSeverity
    defect_count: int
    evidence_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.danger_type, str) or isinstance(self.danger_type, bool):
            raise TypeError(f"danger_type must be a str, got {type(self.danger_type).__name__}")
        if not isinstance(self.severity, DangerSeverity):
            raise TypeError(f"severity must be a DangerSeverity enum, got {type(self.severity).__name__}")
        if not isinstance(self.defect_count, int) or isinstance(self.defect_count, bool) or self.defect_count < 0:
            raise ValueError(f"defect_count must be non-negative int, got {self.defect_count}")
        if not isinstance(self.evidence_digest, str) or isinstance(self.evidence_digest, bool):
            raise TypeError(f"evidence_digest must be a str, got {type(self.evidence_digest).__name__}")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, Signal2DangerState)
        return (
            self.danger_type == other.danger_type
            and self.severity == other.severity
            and self.defect_count == other.defect_count
            and self.evidence_digest == other.evidence_digest
        )

    def __hash__(self) -> int:
        return hash((type(self), self.danger_type, self.severity, self.defect_count, self.evidence_digest))


# Compatibility alias
Signal2Danger = Signal2DangerState


@dataclass(frozen=True, slots=True)
class TwoSignalDecision:
    """Exact-type decision emitted by TwoSignalDangerGate."""

    decision: DangerDecision
    is_refusal: bool
    disposition: str
    signal1_count: int
    signal2_severity: DangerSeverity | None
    is_suppressed: bool
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision, DangerDecision):
            raise TypeError("decision must be a DangerDecision enum")
        if not isinstance(self.is_refusal, bool):
            raise TypeError("is_refusal must be a boolean")
        if not isinstance(self.disposition, str):
            raise TypeError("disposition must be a str")
        if not isinstance(self.signal1_count, int) or self.signal1_count < 0:
            raise ValueError("signal1_count must be non-negative int")
        if self.signal2_severity is not None and not isinstance(self.signal2_severity, DangerSeverity):
            raise TypeError("signal2_severity must be DangerSeverity or None")
        if not isinstance(self.is_suppressed, bool):
            raise TypeError("is_suppressed must be a boolean")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be non-empty string")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TwoSignalDecision)
        return (
            self.decision == other.decision
            and self.is_refusal is other.is_refusal
            and self.disposition == other.disposition
            and self.signal1_count == other.signal1_count
            and self.signal2_severity == other.signal2_severity
            and self.is_suppressed is other.is_suppressed
            and self.rationale == other.rationale
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.decision,
            self.is_refusal,
            self.disposition,
            self.signal1_count,
            self.signal2_severity,
            self.is_suppressed,
            self.rationale,
        ))


# Compatibility alias
DangerEvaluationResult = TwoSignalDecision


class TwoSignalDangerGate:
    """Polly Matzinger Danger Theory gate enforcing exact two-signal logic."""

    @staticmethod
    def evaluate(
        signal1_matches: Sequence[Signal1AstMatch],
        signal2_danger: Signal2DangerState | None,
    ) -> TwoSignalDecision:
        """Evaluate co-occurrence of Signal 1 and Signal 2 according to Danger Theory.

        Logic Tensor:
        - S1 alone -> is_refusal=False, disposition="DIAGNOSTIC_ONLY"
        - S1 + S2  -> is_refusal=True,  disposition="REFUSE"
        - S2 alone -> is_refusal=is_critical, disposition="REFUSE" if critical else "DIAGNOSTIC_ONLY"
        - Neither  -> is_refusal=False, disposition="TOLERATED"
        """
        has_signal1 = len(signal1_matches) > 0
        has_signal2 = signal2_danger is not None and signal2_danger.defect_count > 0

        # Case 0: Neither signal present
        if not has_signal1 and not has_signal2:
            return TwoSignalDecision(
                decision=DangerDecision.TOLERATED,
                is_refusal=False,
                disposition="TOLERATED",
                signal1_count=0,
                signal2_severity=None,
                is_suppressed=False,
                rationale="Clean execution: neither pathogen epitope nor structural damage detected.",
            )

        # Case 1: Signal 1 present, but NO Signal 2 (Benign foreignness / diagnostic pattern)
        if has_signal1 and not has_signal2:
            return TwoSignalDecision(
                decision=DangerDecision.DIAGNOSTIC_ONLY,
                is_refusal=False,
                disposition="DIAGNOSTIC_ONLY",
                signal1_count=len(signal1_matches),
                signal2_severity=None,
                is_suppressed=False,
                rationale=(
                    f"Signal 1 detected ({len(signal1_matches)} epitope match(es)), but zero structural damage "
                    "(Signal 2 absent). Tolerated as benign probe or diagnostic context per Matzinger Danger Theory."
                ),
            )

        # Case 2: Signal 2 present, but NO Signal 1 (Anomalous structural damage without recognized epitope)
        if not has_signal1 and has_signal2:
            assert signal2_danger is not None
            is_critical = signal2_danger.severity in (DangerSeverity.HIGH, DangerSeverity.CRITICAL)
            decision = DangerDecision.DEFENSIVE_LOCKDOWN if is_critical else DangerDecision.DIAGNOSTIC_ONLY
            disposition = "REFUSE" if is_critical else "DIAGNOSTIC_ONLY"
            return TwoSignalDecision(
                decision=decision,
                is_refusal=is_critical,
                disposition=disposition,
                signal1_count=0,
                signal2_severity=signal2_danger.severity,
                is_suppressed=is_critical,
                rationale=(
                    f"Signal 2 alarmin activated (type={signal2_danger.danger_type}, severity={signal2_danger.severity.value}) "
                    "without prior known epitope match. Structural defect requires inspection."
                ),
            )

        # Case 3: Both Signal 1 AND Signal 2 present (Corroborated pathogen)
        assert signal2_danger is not None
        if signal2_danger.severity in (DangerSeverity.HIGH, DangerSeverity.CRITICAL):
            return TwoSignalDecision(
                decision=DangerDecision.QUARANTINED,
                is_refusal=True,
                disposition="REFUSE",
                signal1_count=len(signal1_matches),
                signal2_severity=signal2_danger.severity,
                is_suppressed=True,
                rationale=(
                    f"Corroborated pathogen: {len(signal1_matches)} epitope match(es) co-occur with severe structural damage "
                    f"(type={signal2_danger.danger_type}, severity={signal2_danger.severity.value}). Quarantined."
                ),
            )

        return TwoSignalDecision(
            decision=DangerDecision.DEFENSIVE_LOCKDOWN,
            is_refusal=True,
            disposition="REFUSE",
            signal1_count=len(signal1_matches),
            signal2_severity=signal2_danger.severity,
            is_suppressed=True,
            rationale=(
                f"Corroborated low/medium breach: {len(signal1_matches)} match(es) with Signal 2 defect. "
                "Defensive lockdown engaged."
            ),
        )
