"""Two-Signal Danger Gate, after Matzinger's danger model.

The gate suppresses (quarantine or defensive lockdown) only when both signals
are present:

- neither signal: TOLERATED;
- Signal 1 alone (a detector match, no host-observed damage): DIAGNOSTIC_ONLY;
- Signal 2 alone (host-observed damage, no detector match): DIAGNOSTIC_ONLY,
  whatever its severity;
- both, with HIGH or CRITICAL damage: QUARANTINED; with LOW or MEDIUM damage:
  DEFENSIVE_LOCKDOWN.

A host refusal on its own is enforced by the host check that produced it; the
immune gate does not add a lockdown for it. (Before 2026-09-29 a HIGH or
CRITICAL Signal 2 alone produced DEFENSIVE_LOCKDOWN, contradicting this
docstring; the documented two-signal rule was kept.)

`evaluate` trusts its inputs. `evaluate_independent` first witnesses that
Signal 2 is independent of Signal 1 (`danger_signals.assert_signals_independent`)
and refuses a derived Signal 2 with `TWO_SIGNAL_COLLAPSE`; screening paths use it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from .danger_signals import assert_signals_independent
from .value_objects import (
    DangerDecision,
    DangerSeverity,
    Signal1Match,
    Signal2Danger,
)

__all__ = [
    "DangerDecision",
    "DangerSeverity",
    "Signal1Match",
    "Signal2Danger",
    "DangerEvaluationResult",
    "TwoSignalDangerGate",
    "GuardDisposition",
    "TwoSignalCollapseError",
    "ImmuneEvaluationEngineV1",
]


class GuardDisposition(str, Enum):
    NO_ACTIVATION = "NO_ACTIVATION"
    FINDING = "FINDING"
    HOLD = "HOLD"
    REFUSE = "REFUSE"
    DEFENSIVE_LOCKDOWN = "DEFENSIVE_LOCKDOWN"
    TWO_SIGNAL_COLLAPSE = "TWO_SIGNAL_COLLAPSE"


class TwoSignalCollapseError(ValueError):
    """Raised when Signal 2 danger is derived from Signal 1 match or model output."""
    pass


@dataclass(frozen=True, slots=True)
class DangerEvaluationResult:
    """Exact-type result emitted by TwoSignalDangerGate."""
    decision: DangerDecision
    signal1_count: int
    signal2_severity: DangerSeverity | None
    is_suppressed: bool
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.decision, DangerDecision):
            raise TypeError("decision must be a DangerDecision enum")
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
        return (
            self.decision == other.decision
            and self.signal1_count == other.signal1_count
            and self.signal2_severity == other.signal2_severity
            and self.is_suppressed is other.is_suppressed
            and self.rationale == other.rationale
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.decision,
            self.signal1_count,
            self.signal2_severity,
            self.is_suppressed,
            self.rationale,
        ))


class TwoSignalDangerGate:
    """Deterministic, stateless Two-Signal Danger Gate evaluator."""

    @staticmethod
    def evaluate(
        signal1_matches: Sequence[Signal1Match],
        signal2_danger: Signal2Danger | None,
    ) -> DangerEvaluationResult:
        """Evaluate co-occurrence of Signal 1 and Signal 2 according to Danger Theory."""
        has_signal1 = len(signal1_matches) > 0
        has_signal2 = signal2_danger is not None and signal2_danger.defect_count > 0

        # Case 0: Neither signal present
        if not has_signal1 and not has_signal2:
            return DangerEvaluationResult(
                decision=DangerDecision.TOLERATED,
                signal1_count=0,
                signal2_severity=None,
                is_suppressed=False,
                rationale="Clean execution: neither pathogen epitope nor structural damage detected.",
            )

        # Case 1: Signal 1 present, but NO Signal 2 (Benign foreignness / diagnostic pattern)
        if has_signal1 and not has_signal2:
            return DangerEvaluationResult(
                decision=DangerDecision.DIAGNOSTIC_ONLY,
                signal1_count=len(signal1_matches),
                signal2_severity=None,
                is_suppressed=False,
                rationale=(
                    f"Signal 1 detected ({len(signal1_matches)} epitope match(es)), but zero structural damage "
                    "(Signal 2 absent). Tolerated as benign probe or diagnostic context per Matzinger Danger Theory."
                ),
            )

        # Case 2: Signal 2 present, but NO Signal 1. One signal does not suppress,
        # whatever its severity; the host check that saw the damage enforces it.
        if not has_signal1 and has_signal2:
            assert signal2_danger is not None
            return DangerEvaluationResult(
                decision=DangerDecision.DIAGNOSTIC_ONLY,
                signal1_count=0,
                signal2_severity=signal2_danger.severity,
                is_suppressed=False,
                rationale=(
                    f"Signal 2 only (type={signal2_danger.danger_type}, severity={signal2_danger.severity.value}) "
                    "with no detector match. Diagnostic: the two-signal rule needs both signals to suppress; "
                    "the host check that observed the damage enforces its own refusal."
                ),
            )

        # Case 3: Both Signal 1 AND Signal 2 present (Corroborated pathogen)
        assert signal2_danger is not None
        if signal2_danger.severity in (DangerSeverity.HIGH, DangerSeverity.CRITICAL):
            return DangerEvaluationResult(
                decision=DangerDecision.QUARANTINED,
                signal1_count=len(signal1_matches),
                signal2_severity=signal2_danger.severity,
                is_suppressed=True,
                rationale=(
                    f"Corroborated pathogen: {len(signal1_matches)} epitope match(es) co-occur with severe structural damage "
                    f"(type={signal2_danger.danger_type}, severity={signal2_danger.severity.value}). Quarantined."
                ),
            )

        return DangerEvaluationResult(
            decision=DangerDecision.DEFENSIVE_LOCKDOWN,
            signal1_count=len(signal1_matches),
            signal2_severity=signal2_danger.severity,
            is_suppressed=True,
            rationale=(
                f"Corroborated low/medium breach: {len(signal1_matches)} match(es) with Signal 2 defect. "
                "Defensive lockdown engaged."
            ),
        )

    @staticmethod
    def evaluate_independent(
        signal1_matches: Sequence[Signal1Match],
        signal2_danger: Signal2Danger | None,
        *,
        detector_id: str,
        detector_predicates: frozenset[str],
        offsets_are_content: bool,
    ) -> DangerEvaluationResult:
        """`evaluate`, after refusing a Signal 2 that is not independent of Signal 1.

        Raises `SignalIndependenceRefusal` (`TWO_SIGNAL_COLLAPSE`,
        `UNWITNESSED_DANGER_SIGNAL` or `UNREGISTERED_DANGER_KIND`).
        """
        assert_signals_independent(
            tuple(signal1_matches),
            signal2_danger,
            detector_id=detector_id,
            detector_predicates=detector_predicates,
            offsets_are_content=offsets_are_content,
        )
        return TwoSignalDangerGate.evaluate(signal1_matches, signal2_danger)

    def evaluate_conjunction(
        self,
        signal1: Any,
        signal2: Any,
    ) -> GuardDisposition:
        """Evaluate conjunction of Signal 1 and Signal 2 according to danger gate rules."""
        if signal2 is not None:
            if getattr(signal2, "is_derived", False) or getattr(signal2, "derived_from", None) is not None:
                raise TwoSignalCollapseError("TWO_SIGNAL_COLLAPSE: Signal 2 cannot be derived from Signal 1")
            source = getattr(signal2, "source", None)
            if source == "MODEL":
                return GuardDisposition.TWO_SIGNAL_COLLAPSE
        if signal1 is None:
            return GuardDisposition.NO_ACTIVATION
        if signal2 is None:
            return GuardDisposition.FINDING
        return GuardDisposition.REFUSE


class ImmuneEvaluationEngineV1:
    """Evaluation engine partitioning diagnostic_eligible from enforcing_eligible."""

    def evaluate(
        self,
        *,
        custody: Any,
        target_scope: str,
        admitted_scope: Sequence[str] | None = None,
        detector_match: bool = False,
        independent_danger: bool = False,
    ) -> GuardDisposition:
        if not detector_match:
            return GuardDisposition.NO_ACTIVATION

        custody_str = custody.value if hasattr(custody, "value") else str(custody)
        c_lower = custody_str.lower()
        if c_lower in ("revoked", "suspended", "candidate", "wild"):
            return GuardDisposition.NO_ACTIVATION

        if c_lower in ("provisional", "antibodycustodytier.provisional"):
            if admitted_scope is not None and target_scope not in admitted_scope:
                return GuardDisposition.NO_ACTIVATION
            return GuardDisposition.FINDING

        if c_lower in ("humanadmitted", "human_admitted", "antibodycustodytier.human_admitted", "admitted"):
            if admitted_scope is not None and target_scope not in admitted_scope:
                return GuardDisposition.NO_ACTIVATION
            if detector_match and independent_danger:
                return GuardDisposition.REFUSE
            return GuardDisposition.FINDING

        return GuardDisposition.NO_ACTIVATION

