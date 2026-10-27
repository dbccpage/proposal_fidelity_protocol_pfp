"""Two-signal screening of one payload through the OEEIS ports.

Order matters and is fixed:

1. Signal 2 is computed first, by the host sensor, from the payload alone. The
   sensor never sees the detector's matches, so it cannot count them.
2. The thymus screens every rule with the matcher that will run it (or with
   `thymus_matcher`, which must be an instance of the same matcher class with
   the same `matcher_id`, bound to a neutral host context).
3. The admitted, active rules run on the payload (Signal 1).
4. `assert_signals_independent` witnesses that Signal 2 is independent of
   Signal 1 and refuses otherwise (`TWO_SIGNAL_COLLAPSE`,
   `UNWITNESSED_DANGER_SIGNAL`, `UNREGISTERED_DANGER_KIND`), including a match
   that overlaps Signal 2's evidence spans when the matcher reports content
   offsets.
5. Quarantine records are written only for a QUARANTINED decision.
6. Every input rule is returned, in input order, with its status: MATCHED and
   UNMATCHED rules ran and have updated idle counters; DORMANT rules (admitted
   but inactive) and THYMUS_REFUSED rules did not run and are returned
   unchanged. Nothing is discarded.
"""

from __future__ import annotations

from dataclasses import dataclass

from eis.domain.clonal_selection import (
    ClonalSelectionEngine,
)
from eis.domain.danger_gate import TwoSignalDangerGate
from eis.domain.danger_signals import (
    assert_signals_independent,
)
from eis.domain.ports import (
    AntigenMatcher,
    DangerSensor,
    ImmuneQuarantineSink,
    MatcherBindingRefusal,
    SelfPanelStore,
)
from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import (
    DangerDecision,
    DetectorRule,
)


@dataclass(frozen=True, slots=True)
class ScreenOutcome:
    """The full result of one screen, including the updated rule states."""

    record: dict
    repertoire_after: tuple[DetectorRule, ...]


RULE_STATUSES = ("MATCHED", "UNMATCHED", "DORMANT", "THYMUS_REFUSED")


def _rule_state(rule: DetectorRule, status: str) -> dict:
    return {
        "rule_id": rule.rule_id,
        "matcher_id": rule.matcher_id,
        "status": status,
        "matched": status == "MATCHED",
        "runs_idle": rule.runs_idle,
        "idle_limit": rule.half_life_runs,
        "is_active": rule.is_active,
    }


def _require_same_matcher(matcher: AntigenMatcher, thymus_matcher: AntigenMatcher) -> None:
    if type(thymus_matcher) is not type(matcher) or getattr(
        thymus_matcher, "matcher_id", None
    ) != getattr(matcher, "matcher_id", None):
        raise MatcherBindingRefusal(
            "THYMUS_MATCHER_MISMATCH",
            f"the thymus matcher ({type(thymus_matcher).__name__}, "
            f"{getattr(thymus_matcher, 'matcher_id', None)!r}) is not the matcher that runs the "
            f"rules ({type(matcher).__name__}, {getattr(matcher, 'matcher_id', None)!r})",
        )


def screen_payload(
    content: str,
    rules: tuple[DetectorRule, ...],
    *,
    matcher: AntigenMatcher,
    sensor: DangerSensor,
    self_panel: SelfPanelStore,
    quarantine: ImmuneQuarantineSink,
    thymus_matcher: AntigenMatcher | None = None,
) -> ScreenOutcome:
    """Screen `content`; see the module docstring for the order of steps."""
    if type(content) is not str:
        raise TypeError("content must be the exact payload text")
    if type(rules) is not tuple or any(type(rule) is not DetectorRule for rule in rules):
        raise TypeError("rules must be a tuple of exact DetectorRule")
    if type(getattr(matcher, "reports_content_offsets", None)) is not bool:
        raise TypeError("the matcher must declare reports_content_offsets as a bool")
    if thymus_matcher is not None:
        _require_same_matcher(matcher, thymus_matcher)
    danger = sensor.detect_danger(content)

    thymus = ThymusGate(self_panel.get_self_fixtures())
    screening_matcher = thymus_matcher if thymus_matcher is not None else matcher
    selections = [thymus.evaluate_rule(rule, screening_matcher) for rule in rules]
    admitted = {index for index, result in enumerate(selections) if result.is_admitted}
    active = tuple(
        rule for index, rule in enumerate(rules) if index in admitted and rule.is_active
    )

    matches = tuple(matcher.match_antigen(content, active))
    basis = assert_signals_independent(
        matches,
        danger,
        detector_id=matcher.matcher_id,
        detector_predicates=matcher.detector_predicates,
        offsets_are_content=matcher.reports_content_offsets,
    )
    decision = TwoSignalDangerGate.evaluate(matches, danger)

    stored = []
    if danger is not None and decision.decision == DangerDecision.QUARANTINED:
        for match in matches:
            rule = next(r for r in active if r.target_epitope == match.epitope_name)
            stored.append(quarantine.record_quarantine(rule, match, danger, decision.decision))

    matched_epitopes = {match.epitope_name for match in matches}
    after: list[DetectorRule] = []
    states: list[dict] = []
    for index, rule in enumerate(rules):
        if index not in admitted:
            status, updated = "THYMUS_REFUSED", rule
        elif not rule.is_active:
            status, updated = "DORMANT", rule
        elif rule.target_epitope in matched_epitopes:
            status, updated = "MATCHED", ClonalSelectionEngine.stimulate(rule)
        else:
            status, updated = "UNMATCHED", ClonalSelectionEngine.apply_decay(rule)
        after.append(updated)
        states.append(_rule_state(updated, status))
    record = {
        "decision": decision.decision.value,
        "matches": [match.epitope_name for match in matches],
        "signal2": None
        if danger is None
        else {
            "kind": danger.danger_type,
            "observer": danger.observer_id,
            "severity": danger.severity.value,
            "defect_count": danger.defect_count,
            "evidence_digest": danger.evidence_digest,
            "evidence_spans": [list(span) for span in danger.evidence_spans],
        },
        "independence_basis": basis,
        "thymus_admitted": [rules[index].rule_id for index in sorted(admitted)],
        "thymus_refused": [
            {"rule_id": rule.rule_id, "rationale": result.rationale}
            for rule, result in zip(rules, selections)
            if not result.is_admitted
        ],
        "quarantine_refs": stored,
        "repertoire_after": states,
        "AuthorityEffect": "None",
    }
    return ScreenOutcome(record=record, repertoire_after=tuple(after))


def screen(
    content: str,
    rules: tuple[DetectorRule, ...],
    *,
    matcher: AntigenMatcher,
    sensor: DangerSensor,
    self_panel: SelfPanelStore,
    quarantine: ImmuneQuarantineSink,
    thymus_matcher: AntigenMatcher | None = None,
) -> dict:
    """The JSON record of `screen_payload` (the updated rules are in `repertoire_after`)."""
    return screen_payload(
        content,
        rules,
        matcher=matcher,
        sensor=sensor,
        self_panel=self_panel,
        quarantine=quarantine,
        thymus_matcher=thymus_matcher,
    ).record
