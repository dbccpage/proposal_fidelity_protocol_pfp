"""Signal 2 must be independent of Signal 1, and one signal never suppresses.

Counterexamples from the study (design doc Appendix A, OEEIS rows):

- the demo screens set Signal 2 to `len(matches)`, so the two-signal gate was a
  one-signal gate and DIAGNOSTIC_ONLY was unreachable for a detector match;
- the gate's docstring required both signals, but a HIGH or CRITICAL Signal 2
  alone produced DEFENSIVE_LOCKDOWN.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eis.domain.danger_gate import TwoSignalDangerGate
from eis.domain.danger_signals import (
    HOST_DANGER_SIGNAL_KINDS,
    SignalIndependenceRefusal,
    assert_signals_independent,
    signal1_digest,
)
from eis.domain.ports import MatcherBindingRefusal
from eis.domain.value_objects import (
    DangerDecision,
    DangerSeverity,
    DetectorRule,
    Signal1Match,
    Signal2Danger,
)
from eis.infrastructure.mssn_pharmacy import (
    DetectionContext,
)
from eis.infrastructure.mssn_ports import (
    PHARMACY_MATCHER_ID,
    FixedSelfPanel,
    HostPayloadDangerSensor,
    PatternMatcher,
    PharmacyMatcher,
    RunQuarantineSink,
)
from eis.infrastructure.native_pharmacy import (
    NativePharmacyReport,
    PharmacyFinding,
)
from eis.use_cases.mssn_immune import screen

MATCH = Signal1Match("model-verdict", "verified", 1.0, 2)
RULE = DetectorRule("r1", "model-verdict", r"verified|phi1")
PANEL = FixedSelfPanel(("candidate contains data and needs a host check",))


def _danger(**overrides: object) -> Signal2Danger:
    fields: dict[str, object] = {
        "danger_type": "PROTECTED_FIELD_VIOLATION",
        "severity": DangerSeverity.HIGH,
        "defect_count": 1,
        "evidence_digest": "sha256:" + "a" * 64,
        "observer_id": "host-protected-field-check",
    }
    fields.update(overrides)
    return Signal2Danger(**fields)  # type: ignore[arg-type]


# -- the gate: one signal never suppresses --------------------------------------


@pytest.mark.parametrize("severity", list(DangerSeverity))
def test_signal2_alone_is_diagnostic_whatever_its_severity(severity: DangerSeverity) -> None:
    """Old code: HIGH or CRITICAL Signal 2 alone gave DEFENSIVE_LOCKDOWN."""
    result = TwoSignalDangerGate.evaluate([], _danger(severity=severity))
    assert result.decision == DangerDecision.DIAGNOSTIC_ONLY
    assert result.is_suppressed is False
    assert result.signal2_severity == severity


def test_both_signals_still_suppress() -> None:
    assert TwoSignalDangerGate.evaluate([MATCH], _danger()).decision == DangerDecision.QUARANTINED
    low = TwoSignalDangerGate.evaluate([MATCH], _danger(severity=DangerSeverity.LOW))
    assert low.decision == DangerDecision.DEFENSIVE_LOCKDOWN and low.is_suppressed is True


# -- independence ---------------------------------------------------------------


def test_an_independent_host_signal_is_accepted() -> None:
    basis = assert_signals_independent(
        [MATCH], _danger(), detector_id="regex", detector_predicates=frozenset(), offsets_are_content=False
    )
    assert "host-protected-field-check" in basis and "regex" in basis


def test_signal2_observed_by_the_matcher_is_a_collapse() -> None:
    """The danger bit derived from the match."""
    with pytest.raises(SignalIndependenceRefusal) as caught:
        assert_signals_independent(
            [MATCH], _danger(observer_id="regex"), detector_id="regex", detector_predicates=frozenset(), offsets_are_content=False
        )
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"


def test_signal2_whose_evidence_is_the_match_digest_is_a_collapse() -> None:
    """One signal counted twice."""
    derived = _danger(evidence_digest=signal1_digest([MATCH]))
    with pytest.raises(SignalIndependenceRefusal) as caught:
        assert_signals_independent([MATCH], derived, detector_id="regex", detector_predicates=frozenset(), offsets_are_content=False)
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"


@pytest.mark.parametrize("observer", ["MODEL", "llm", "Agent", "DETECTOR", "matcher"])
def test_model_or_detector_authored_signal2_is_a_collapse(observer: str) -> None:
    with pytest.raises(SignalIndependenceRefusal) as caught:
        assert_signals_independent(
            [MATCH], _danger(observer_id=observer), detector_id="regex", detector_predicates=frozenset(), offsets_are_content=False
        )
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"


def test_the_same_predicate_counted_twice_is_a_collapse() -> None:
    """The pharmacy already inspects host-only keys; a protected-field Signal 2 repeats it."""
    with pytest.raises(SignalIndependenceRefusal) as caught:
        assert_signals_independent(
            [MATCH],
            _danger(),
            detector_id=PHARMACY_MATCHER_ID,
            detector_predicates=frozenset({"PROTECTED_FIELD_VIOLATION"}),
            offsets_are_content=False,
        )
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"


def test_an_unwitnessed_or_unregistered_signal2_is_refused() -> None:
    with pytest.raises(SignalIndependenceRefusal) as caught:
        assert_signals_independent([MATCH], _danger(observer_id=""), detector_id="regex", detector_predicates=frozenset(), offsets_are_content=False)
    assert caught.value.code == "UNWITNESSED_DANGER_SIGNAL"
    # The kind the old match-count sensor emitted is not a registered host kind.
    with pytest.raises(SignalIndependenceRefusal) as caught:
        assert_signals_independent(
            [MATCH], _danger(danger_type="MSSN_HOST_OBJECTION"), detector_id="regex", detector_predicates=frozenset(), offsets_are_content=False
        )
    assert caught.value.code == "UNREGISTERED_DANGER_KIND"
    assert "MSSN_HOST_OBJECTION" not in HOST_DANGER_SIGNAL_KINDS


# -- the screen use case ----------------------------------------------------------


class MatchCountSensor:
    """The old collapse, as a sensor: Signal 2 = number of detector matches."""

    def __init__(self, matcher, rules) -> None:
        self.matcher, self.rules = matcher, rules
        self.observer_id = matcher.matcher_id

    def detect_danger(self, content):
        matches = self.matcher.match_antigen(content, self.rules)
        if not matches:
            return None
        return Signal2Danger(
            "PROTECTED_FIELD_VIOLATION",
            DangerSeverity.HIGH,
            len(matches),
            signal1_digest(matches),
            self.observer_id,
        )


def test_screen_refuses_a_match_count_signal2(tmp_path: Path) -> None:
    """Counterexample: the demo's `{"defect_count": len(matches)}` wiring."""
    matcher = PatternMatcher()
    with pytest.raises(SignalIndependenceRefusal) as caught:
        screen(
            '{"verified": true}',
            (RULE,),
            matcher=matcher,
            sensor=MatchCountSensor(matcher, (RULE,)),
            self_panel=PANEL,
            quarantine=RunQuarantineSink(tmp_path / "q"),
        )
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"
    assert not (tmp_path / "q").exists()


def test_screen_reaches_all_three_dispositions_with_a_host_sensor(tmp_path: Path) -> None:
    kwargs = dict(
        matcher=PatternMatcher(),
        sensor=HostPayloadDangerSensor(),
        self_panel=PANEL,
        quarantine=RunQuarantineSink(tmp_path / "q"),
    )
    assert screen('{"candidate": "x"}', (RULE,), **kwargs)["decision"] == "TOLERATED"
    # A matched word in prose is Signal 1 only.
    assert screen('{"note": "verified"}', (RULE,), **kwargs)["decision"] == "DIAGNOSTIC_ONLY"
    # A protected key the host observes, and a match elsewhere: two signals.
    rule = DetectorRule("r2", "universal-solver", r"universal\s{1,4}solver")
    content = '{"note": "a universal solver", "phi1": "0"}'
    both = screen(content, (rule,), **kwargs)
    assert both["decision"] == "QUARANTINED"
    assert both["signal2"]["kind"] == "PROTECTED_FIELD_VIOLATION"
    key = content.index('"phi1"')
    assert both["signal2"]["evidence_spans"] == [[key, key + len('"phi1"')]]
    assert both["quarantine_refs"]


def test_one_token_cannot_be_both_signals(tmp_path: Path) -> None:
    """Counterexample (review, 2026-09-29): the reply rule `verified|phi1|...` matched the
    key "verified", which the protected-field sensor also flagged, and the screen
    returned QUARANTINED on that one token."""
    kwargs = dict(
        matcher=PatternMatcher(),
        sensor=HostPayloadDangerSensor(),
        self_panel=PANEL,
        quarantine=RunQuarantineSink(tmp_path / "q"),
    )
    with pytest.raises(SignalIndependenceRefusal) as caught:
        screen('{"verified": true}', (RULE,), **kwargs)
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"
    assert "one token cannot be both signals" in str(caught.value)
    assert not (tmp_path / "q").exists()


def test_span_overlap_is_checked_only_for_content_offsets() -> None:
    danger = _danger(evidence_spans=((1, 11),))
    inside = Signal1Match("model-verdict", "verified", 1.0, 2)
    outside = Signal1Match("model-verdict", "verified", 1.0, 20)
    with pytest.raises(SignalIndependenceRefusal):
        assert_signals_independent(
            [inside], danger, detector_id="regex", detector_predicates=frozenset(), offsets_are_content=True
        )
    assert assert_signals_independent(
        [outside], danger, detector_id="regex", detector_predicates=frozenset(), offsets_are_content=True
    )
    # A matcher whose matches name finding codes has no content offsets to compare.
    assert assert_signals_independent(
        [inside], danger, detector_id="pharmacy", detector_predicates=frozenset(), offsets_are_content=False
    )


@pytest.mark.parametrize("observer", ["Regex", "REGEX", " regex "])
def test_observer_and_detector_ids_are_compared_casefolded(observer: str) -> None:
    """Counterexample (review): observer "Regex" passed as distinct from the matcher "regex"."""
    with pytest.raises(SignalIndependenceRefusal) as caught:
        assert_signals_independent(
            [MATCH],
            _danger(observer_id=observer),
            detector_id="regex",
            detector_predicates=frozenset(),
            offsets_are_content=False,
        )
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"


def test_the_screen_refuses_a_thymus_matcher_of_another_type(tmp_path: Path) -> None:
    """Counterexample (review): only the matcher_id string was compared."""

    class Impostor:
        matcher_id = "regex"
        detector_predicates: frozenset[str] = frozenset()
        reports_content_offsets = True

        def match_antigen(self, content, rules):
            return ()

    with pytest.raises(MatcherBindingRefusal) as caught:
        screen(
            '{"candidate": "x"}',
            (RULE,),
            matcher=PatternMatcher(),
            sensor=HostPayloadDangerSensor(),
            self_panel=PANEL,
            quarantine=RunQuarantineSink(tmp_path / "q"),
            thymus_matcher=Impostor(),
        )
    assert caught.value.code == "THYMUS_MATCHER_MISMATCH"


def test_every_input_rule_is_returned_with_its_status(tmp_path: Path) -> None:
    """Counterexample (review): dormant and thymus-refused rules vanished from the record."""
    matched = DetectorRule("m", "universal-solver", r"universal\s{1,4}solver")
    unmatched = DetectorRule("u", "other", r"nothing\s{1,4}here")
    dormant = DetectorRule("d", "dormant", r"dormant", is_active=False)
    refused = DetectorRule("r", "refused", r"data")  # matches the self panel
    unsafe = DetectorRule("x", "unsafe", r"\w*!")
    record = screen(
        '{"note": "a universal solver"}',
        (matched, unmatched, dormant, refused, unsafe),
        matcher=PatternMatcher(),
        sensor=HostPayloadDangerSensor(),
        self_panel=PANEL,
        quarantine=RunQuarantineSink(tmp_path / "q"),
    )
    states = {row["rule_id"]: row["status"] for row in record["repertoire_after"]}
    assert states == {
        "m": "MATCHED",
        "u": "UNMATCHED",
        "d": "DORMANT",
        "r": "THYMUS_REFUSED",
        "x": "THYMUS_REFUSED",
    }
    assert [row["rule_id"] for row in record["repertoire_after"]] == ["m", "u", "d", "r", "x"]


class RecordingNative:
    def __init__(self, classes: tuple[str, ...]) -> None:
        self.classes = classes

    def detect(self, candidate_json, context):
        return NativePharmacyReport(
            subject_digest="sha256:" + "0" * 64,
            semantic_payload_digest="sha256:" + "0" * 64,
            raw_bytes_digest=None,
            detectors_run=(),
            findings=tuple(
                PharmacyFinding(code, "REFUSE", "/verified", "d", "native")
                for code in self.classes
                if '"verified"' in candidate_json
            ),
        )


def test_pharmacy_with_a_protected_field_sensor_is_refused(tmp_path: Path) -> None:
    """Pharmacy self-certification reads host-only keys; so does the protected-field check."""
    native = RecordingNative(("SELF_CERTIFICATION",))
    rules = (
        DetectorRule("p1", "SELF_CERTIFICATION", "SELF_CERTIFICATION", matcher_id=PHARMACY_MATCHER_ID),
    )
    panel = FixedSelfPanel((json.dumps({"public_rationale": "clean"}),))
    with pytest.raises(SignalIndependenceRefusal) as caught:
        screen(
            json.dumps({"verified": True}),
            rules,
            matcher=PharmacyMatcher(DetectionContext(), native=native),
            sensor=HostPayloadDangerSensor(),
            self_panel=panel,
            quarantine=RunQuarantineSink(tmp_path / "q"),
        )
    assert caught.value.code == "TWO_SIGNAL_COLLAPSE"
    # With the strict-JSON check only, the same candidate is Signal 1 only.
    record = screen(
        json.dumps({"verified": True}),
        rules,
        matcher=PharmacyMatcher(DetectionContext(), native=native),
        sensor=HostPayloadDangerSensor(check_protected_fields=False),
        self_panel=panel,
        quarantine=RunQuarantineSink(tmp_path / "q"),
    )
    assert record["decision"] == "DIAGNOSTIC_ONLY"
