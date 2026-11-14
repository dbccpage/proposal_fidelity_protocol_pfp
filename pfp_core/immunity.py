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
  yes                     yes, collapsed             HOLD_OR_REPAIR (host refusal) +
                                                     the refusal code recorded
  ======================  =========================  ===========================

  The disposition is monotone in Signal 2: an allowlisted host failure holds
  the candidate whatever Signal 1 says. A Signal 1 match that cannot be
  separated from the host evidence only loses its own activation credit; it
  never downgrades the host's refusal. (Before 2026-11-11 the collapsed row
  returned DIAGNOSTIC_OR_NORMALIZE, so adding a rule could release a candidate
  that the host check alone would hold.)

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

from eis.domain.danger_signals import SignalIndependenceRefusal, assert_signals_independent
from eis.domain.provisional_promotion import ObservationSupportPolicyV1, RawObservationV1
from eis.domain.safe_pattern import compile_safe_pattern
from eis.domain.thymus import ThymusGate
from eis.domain.value_objects import DangerSeverity, DetectorRule, Signal1Match, Signal2Danger

from . import (
    REPO_ROOT,  # noqa: F401
    immune_host,
)
from .fidelity import sha256_hex

PASS = 'PASS'  # noqa: S105
DIAGNOSTIC = 'DIAGNOSTIC_OR_NORMALIZE'
HOLD = 'HOLD_OR_REPAIR'
MATCHER_ID = 'regex'


def screen_rules(rules: list[DetectorRule], self_panel: list[str]) -> tuple[list[DetectorRule], list[dict]]:
    """Return (admitted rules, kill records) after thymic negative selection.

    Invokes Rust host binary pfp_immune screen when available, retaining
    deterministic Python fallback for offline execution.
    """
    if immune_host.is_available():
        try:
            candidates = [
                {
                    "rule_id": r.rule_id,
                    "pattern": r.match_pattern,
                    "capability_kind": getattr(r, "target_epitope", "rule"),
                }
                for r in rules
            ]
            res = immune_host.screen(self_panel, candidates)
            admitted_ids = set(res.get("admitted", []))
            admitted = [r for r in rules if r.rule_id in admitted_ids]
            killed = [
                {
                    "rule_id": p["rule_id"],
                    "violations": [p["reason"]],
                    "rationale": p["reason"],
                }
                for p in res.get("purged", [])
            ]
            return admitted, killed
        except (immune_host.ImmuneHostError, OSError, KeyError):
            pass

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
    """Disposition per the table above. Signal 2 counts only from an allowlisted host observer.

    Invokes Rust host binary pfp_immune decide when available, retaining
    deterministic Python fallback for offline execution.
    """
    if danger is not None and danger.observer_id not in host_observers:
        code = 'TWO_SIGNAL_COLLAPSE' if matches else 'UNWITNESSED_DANGER_SIGNAL'
        disposition = DIAGNOSTIC if matches else PASS
        return Decision(disposition, f'danger from {danger.observer_id!r} is not an admitted host observer',
                        matches, code)

    status: str | None = None
    disposition_text: str | None = None
    if immune_host.is_available():
        try:
            defects = getattr(danger, 'defect_count', 1) or 1 if danger is not None else 0
            danger_score = (defects, 1)
            threshold = (1, 2)
            rule_ids = [m.detector_id for m in matches]
            res = immune_host.decide(rule_ids, danger_score, threshold)
            status = res['status']
            disposition_text = res['disposition']
        except (immune_host.ImmuneHostError, OSError, KeyError):
            pass

    if not matches and danger is None:
        return Decision(status or PASS, disposition_text or 'no rule match and no host danger')
    if danger is None:
        return Decision(status or DIAGNOSTIC, disposition_text or 'rule match without host danger: diagnostic only',
                        matches)
    if not matches:
        return Decision(status or HOLD, f'host predicate refusal: {danger.danger_type} by {danger.observer_id}')

    try:
        basis = assert_signals_independent(matches, danger, detector_id=MATCHER_ID,
                                           detector_predicates=frozenset(), offsets_are_content=True)
    except SignalIndependenceRefusal as err:
        return Decision(HOLD, f'host predicate refusal: {danger.danger_type} by {danger.observer_id}; '
                              f'Signal 1 adds no independent activation: {err.detail}', matches, err.code)
    return Decision(status or HOLD, basis, matches)


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
