"""`ImmuneScreenPort` implemented by the Epistemic Immune System (OEEIS).

The only OEWAS module that imports OEEIS. Each method converts the port's
records to OEEIS value objects, delegates to the OEEIS gate that owns the
decision, and translates the result (or refusal) into the port's terms.
"""

from __future__ import annotations

import re
from typing import Sequence

from eis.domain import (
    AllostericConsensusGate,
    AllosteryRefusal,
    DangerSeverity,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
    SignalIndependenceRefusal,
    ThymusGate,
    TwoSignalDangerGate,
)
from eis.infrastructure.native_domain import (
    NativeAllostericConsensusGate,
)

from ...application.ports.immune_screen_port import (
    DetectorIdentity,
    DetectorMatch,
    HostDangerObservation,
    ImmuneEvidenceRefusal,
    ImmuneVerdict,
    SensorReading,
)


def _signal1(match: DetectorMatch) -> Signal1Match:
    if type(match) is not DetectorMatch:
        raise ImmuneEvidenceRefusal("BAD_EVIDENCE", "matches must be exact DetectorMatch records")
    return Signal1Match(match.epitope, match.matched_text, 1.0, match.offset)


def _signal2(danger: HostDangerObservation) -> Signal2Danger:
    if type(danger) is not HostDangerObservation:
        raise ImmuneEvidenceRefusal("BAD_EVIDENCE", "danger must be an exact HostDangerObservation")
    try:
        return Signal2Danger(
            danger.kind,
            DangerSeverity(danger.severity),
            danger.defect_count,
            danger.evidence_digest,
            danger.observer_id,
            danger.evidence_spans,
        )
    except (TypeError, ValueError) as exc:
        raise ImmuneEvidenceRefusal("BAD_EVIDENCE", str(exc)) from exc


class OeeisImmuneAdapter:
    """Danger gate, allosteric gate and thymus from OEEIS."""

    def __init__(
        self,
        *,
        self_panel: Sequence[str] = (),
        quorum_gate: AllostericConsensusGate | None = None,
    ) -> None:
        self._self_panel = tuple(self_panel)
        self._quorum_gate = (
            quorum_gate if quorum_gate is not None else NativeAllostericConsensusGate()
        )

    def danger_verdict(
        self,
        matches: Sequence[DetectorMatch],
        danger: HostDangerObservation | None,
        *,
        detector: DetectorIdentity,
    ) -> ImmuneVerdict:
        if type(detector) is not DetectorIdentity:
            raise ImmuneEvidenceRefusal(
                "BAD_EVIDENCE", "detector must be an exact DetectorIdentity"
            )
        signal1 = tuple(_signal1(match) for match in matches)
        signal2 = None if danger is None else _signal2(danger)
        try:
            result = TwoSignalDangerGate.evaluate_independent(
                signal1,
                signal2,
                detector_id=detector.detector_id,
                detector_predicates=detector.predicates,
                offsets_are_content=detector.offsets_are_content,
            )
        except SignalIndependenceRefusal as exc:
            raise ImmuneEvidenceRefusal(exc.code, exc.detail) from exc
        return ImmuneVerdict(
            blocks=result.is_suppressed,
            decision=result.decision.value,
            rationale=result.rationale,
        )

    def quorum_verdict(self, readings: Sequence[SensorReading]) -> ImmuneVerdict:
        signals: dict[str, object] = {}
        for reading in readings:
            if type(reading) is not SensorReading:
                raise ImmuneEvidenceRefusal(
                    "BAD_EVIDENCE", "readings must be exact SensorReading records"
                )
            if reading.sensor_id.strip().casefold() in {key.strip().casefold() for key in signals}:
                raise ImmuneEvidenceRefusal(
                    "DUPLICATE_SENSOR", f"sensor {reading.sensor_id!r} reported more than once"
                )
            signals[reading.sensor_id] = reading.value
        try:
            decision = self._quorum_gate.evaluate_quorum(signals)
        except AllosteryRefusal as exc:
            raise ImmuneEvidenceRefusal(exc.code, exc.detail) from exc
        return ImmuneVerdict(
            blocks=not decision.is_activated,
            decision="ACTIVATED" if decision.is_activated else "NOT_ACTIVATED",
            rationale=decision.rationale,
        )

    def trigger_tolerance_verdict(self, rule_id: str, phrases: Sequence[str]) -> ImmuneVerdict:
        if not self._self_panel:
            raise ValueError("a thymus screen needs a non-empty self panel")
        thymus = ThymusGate(self._self_panel)
        for phrase in phrases:
            if type(phrase) is not str:
                raise TypeError("trigger phrases must be exact str")
            rule = DetectorRule(
                rule_id=rule_id, target_epitope=rule_id, match_pattern=re.escape(phrase)
            )
            selection = thymus.evaluate_rule(rule)
            if not selection.is_admitted:
                # A match on the panel is autoimmunity; any other refusal means the
                # phrase could not be screened (for example it is too long).
                decision = "REFUSED" if selection.autoimmune_violations > 0 else "UNSCREENABLE"
                return ImmuneVerdict(blocks=True, decision=decision, rationale=selection.rationale)
        return ImmuneVerdict(
            blocks=False,
            decision="ADMITTED",
            rationale=f"{len(phrases)} trigger phrase(s) matched none of {len(self._self_panel)} self fixture(s)",
        )


__all__ = ["OeeisImmuneAdapter"]
