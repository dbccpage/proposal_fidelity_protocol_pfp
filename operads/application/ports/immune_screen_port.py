"""Port through which OEWAS consumes the Epistemic Immune System (OEEIS).

OEEIS owns the danger gate, the thymus and the allosteric gate. OEWAS's domain
does not import them; the application layer asks this port with the records
defined here, which OEWAS owns, and receives an `ImmuneVerdict`. The adapter
that implements the port lives in `infrastructure/immune/`.

Every danger verdict is checked for independence: the caller must name the
detector that produced the matches (`DetectorIdentity`), and a Signal 2 that is
not independent of it is refused with `ImmuneEvidenceRefusal`
(`TWO_SIGNAL_COLLAPSE` and related codes). There is no unchecked path.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Protocol, Sequence

DANGER_SEVERITIES = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})


def _text(value: object, label: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a non-empty str")
    return value


def _count(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be an exact int >= 0")
    return value


class ImmuneEvidenceRefusal(ValueError):
    """The immune system refused the evidence it was given (for example a derived Signal 2)."""

    def __init__(self, code: str, detail: str) -> None:
        self.code = _text(code, "code")
        self.detail = detail
        super().__init__(f"{code}: {detail}")


@dataclass(frozen=True, slots=True)
class DetectorMatch:
    """One Signal 1 match: the epitope label, the matched text and its offset."""

    epitope: str
    matched_text: str
    offset: int

    def __post_init__(self) -> None:
        _text(self.epitope, "epitope")
        _text(self.matched_text, "matched_text")
        _count(self.offset, "offset")


@dataclass(frozen=True, slots=True)
class HostDangerObservation:
    """One Signal 2 observation made by a named host check."""

    kind: str
    severity: str
    defect_count: int
    evidence_digest: str
    observer_id: str
    evidence_spans: tuple[tuple[int, int], ...] = ()

    def __post_init__(self) -> None:
        _text(self.kind, "kind")
        if self.severity not in DANGER_SEVERITIES:
            raise ValueError(f"severity must be one of {sorted(DANGER_SEVERITIES)}")
        _count(self.defect_count, "defect_count")
        _text(self.evidence_digest, "evidence_digest")
        _text(self.observer_id, "observer_id")
        if type(self.evidence_spans) is not tuple:
            raise ValueError("evidence_spans must be a tuple")


@dataclass(frozen=True, slots=True)
class DetectorIdentity:
    """The detector that produced the matches, and what it evaluates itself.

    `predicates` are the host danger kinds the detector already evaluates;
    `offsets_are_content` says whether match offsets locate text in the content.
    """

    detector_id: str
    predicates: frozenset[str]
    offsets_are_content: bool

    def __post_init__(self) -> None:
        _text(self.detector_id, "detector_id")
        if type(self.predicates) is not frozenset or any(type(p) is not str for p in self.predicates):
            raise ValueError("predicates must be a frozenset of str")
        if type(self.offsets_are_content) is not bool:
            raise ValueError("offsets_are_content must be an exact bool")


@dataclass(frozen=True, slots=True)
class SensorReading:
    """One sensor's exact signal for the allosteric gate."""

    sensor_id: str
    value: int | Fraction

    def __post_init__(self) -> None:
        _text(self.sensor_id, "sensor_id")
        if type(self.value) not in (int, Fraction):
            raise ValueError("value must be an exact int or Fraction")


@dataclass(frozen=True, slots=True)
class ImmuneVerdict:
    """What the immune system decided, in OEWAS's own terms.

    `blocks` is True when the guarded transition must not proceed (a
    suppressing danger decision, a quorum not reached, a rule refused by the
    thymus). `decision` is the immune system's own label; `rationale` its text.
    """

    blocks: bool
    decision: str
    rationale: str

    def __post_init__(self) -> None:
        if type(self.blocks) is not bool:
            raise TypeError("blocks must be an exact bool")
        _text(self.decision, "decision")
        _text(self.rationale, "rationale")


class ImmuneScreenPort(Protocol):
    """The three immune decisions OEWAS guards use."""

    def danger_verdict(
        self,
        matches: Sequence[DetectorMatch],
        danger: HostDangerObservation | None,
        *,
        detector: DetectorIdentity,
    ) -> ImmuneVerdict:
        """Two-signal gate after the independence check; raises `ImmuneEvidenceRefusal`."""
        ...

    def quorum_verdict(self, readings: Sequence[SensorReading]) -> ImmuneVerdict:
        """Allosteric gate over distinct sensors; raises `ImmuneEvidenceRefusal`."""
        ...

    def trigger_tolerance_verdict(self, rule_id: str, phrases: Sequence[str]) -> ImmuneVerdict:
        """Thymus screen of literal trigger phrases against the self panel."""
        ...


__all__ = [
    "DANGER_SEVERITIES",
    "DetectorIdentity",
    "DetectorMatch",
    "HostDangerObservation",
    "ImmuneEvidenceRefusal",
    "ImmuneScreenPort",
    "ImmuneVerdict",
    "SensorReading",
]
