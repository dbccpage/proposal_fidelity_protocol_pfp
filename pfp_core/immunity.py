"""EIS regulation for imported rules: thymus screening and two-signal dispositions.

* ``screen_rules`` runs every candidate ``DetectorRule`` over the task domain's
  self panel of known-clean outputs with ``eis.domain.thymus.ThymusGate``. A
  rule that fires on clean work is killed before it can refuse anything; a
  survivor has only been shown not to fire on these fixtures.
* ``decide`` implements the disposition table used here:

  ======================  =========================  ===========================
  Signal 1 (rule match)   Signal 2 (host danger)     disposition
  ======================  =========================  ===========================
  no                      no                         PASS
  yes                     no                         DIAGNOSTIC_OR_NORMALIZE
  no                      yes                        HOLD_OR_REPAIR (host refusal)
  yes                     yes, independent           HOLD_OR_REPAIR (activation)
  yes                     yes, collapsed             DIAGNOSTIC_OR_NORMALIZE +
                                                     TWO_SIGNAL_COLLAPSE recorded
  ======================  =========================  ===========================

  Signal 2 counts only when its observer is in ``HOST_OBSERVERS``; a danger
  signal from any other producer (a model name, ``MODEL``, a detector) is
  ignored and recorded as ``UNWITNESSED_DANGER_SIGNAL`` or
  ``TWO_SIGNAL_COLLAPSE``. A rule match alone never blocks. A failed host predicate alone is an exact
  checker refusal, labelled as such rather than as two observers. Independence
  is checked by ``eis.domain.danger_signals.assert_signals_independent``, so a
  model- or detector-authored danger signal is refused.
* ``AntibodyRegistry`` turns a recurring failure pattern into a ``Provisional``
  antibody only when ``ObservationSupportPolicyV1`` finds >= 3 observations
  that share no model, scaffold, precedent set or lineage root. Its authority
  effect stays ``None``: promotion queues review, it does not enforce.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import REPO_ROOT  # noqa: F401
from .fidelity import sha256_hex
from eis.domain.danger_signals import SignalIndependenceRefusal, assert_signals_independent
from eis.domain.provisional_promotion import ObservationSupportPolicyV1, RawObservationV1
from eis.domain.safe_pattern import compile_safe_pattern
from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import DangerSeverity, DetectorRule, Signal1Match, Signal2Danger

PASS = 'PASS'
DIAGNOSTIC = 'DIAGNOSTIC_OR_NORMALIZE'
HOLD = 'HOLD_OR_REPAIR'
MATCHER_ID = 'regex'


def screen_rules(rules: list[DetectorRule], self_panel: list[str]) -> tuple[list[DetectorRule], list[dict]]:
    """Return (admitted rules, kill records) after thymic negative selection."""
    gate = ThymusGate(self_panel=self_panel)
    admitted, killed = [], []
    for rule in rules:
        result = gate.evaluate_rule(rule)
        if result.is_admitted:
            admitted.append(rule)
        else:
            killed.append({'rule_id': rule.rule_id, 'violations': result.autoimmune_violations,
                           'rationale': result.rationale})
    return admitted, killed


def signal1(text: str, rules: list[DetectorRule]) -> list[Signal1Match]:
    matches = []
    for rule in rules:
        hit = compile_safe_pattern(rule.match_pattern).search(text)
        if hit:
            matches.append(Signal1Match(epitope_name=rule.target_epitope, pattern_matched=hit.group(0),
                                        offset=hit.start(), detector_id=rule.rule_id))
    return matches


def host_danger(kind: str, observer: str, evidence: str, defects: int = 1) -> Signal2Danger:
    """A danger signal observed by a named host check over ``evidence`` bytes."""
    return Signal2Danger(danger_type=kind, severity=DangerSeverity.HIGH, defect_count=defects,
                         evidence_digest='sha256:' + sha256_hex(evidence), observer_id=observer)


@dataclass
class Decision:
    disposition: str
    basis: str
    signal1: list = field(default_factory=list)
    refusal_code: str | None = None


HOST_OBSERVERS = frozenset({'host.ast_parse', 'host.contract_check', 'host.public_smoke', 'host.transition_table'})


def decide(matches: list[Signal1Match], danger: Signal2Danger | None,
           host_observers: frozenset[str] = HOST_OBSERVERS) -> Decision:
    """Disposition per the table above. Signal 2 counts only from an allowlisted host observer."""
    if danger is not None and danger.observer_id not in host_observers:
        code = 'TWO_SIGNAL_COLLAPSE' if matches else 'UNWITNESSED_DANGER_SIGNAL'
        disposition = DIAGNOSTIC if matches else PASS
        return Decision(disposition, f'danger from {danger.observer_id!r} is not an admitted host observer',
                        matches, code)
    if not matches and danger is None:
        return Decision(PASS, 'no rule match and no host danger')
    if danger is None:
        return Decision(DIAGNOSTIC, 'rule match without host danger: diagnostic only', matches)
    if not matches:
        return Decision(HOLD, f'host predicate refusal: {danger.danger_type} by {danger.observer_id}')
    try:
        basis = assert_signals_independent(matches, danger, detector_id=MATCHER_ID,
                                           detector_predicates=frozenset(), offsets_are_content=True)
    except SignalIndependenceRefusal as err:
        return Decision(DIAGNOSTIC, f'second signal refused: {err.detail}', matches, err.code)
    return Decision(HOLD, basis, matches)


class AntibodyRegistry:
    """Failure patterns with their raw observations; promotion needs independent support."""

    def __init__(self):
        self.observations: dict[str, list[RawObservationV1]] = {}
        self.policy = ObservationSupportPolicyV1()

    def observe(self, pattern: str, occurrence_id: str, *, model_id: str, scaffold_digest: str,
                precedent_digest: str, lineage_root: str) -> None:
        obs = RawObservationV1(occurrence_id, model_id, scaffold_digest, precedent_digest, lineage_root)
        self.policy.register_observation(obs)
        self.observations.setdefault(pattern, []).append(obs)

    def status(self, pattern: str) -> dict:
        result = self.policy.compute_support(self.observations.get(pattern, []))
        return {'pattern': pattern, 'support': result.support_count,
                'custody': 'Provisional' if result.eligible_for_provisional else 'Candidate',
                'authority_effect': result.authority_effect}
