"""Layer 7 families: tribunal, rule transfer, cost ladder, antibody dialogue, detector adequacy and exclusion retests.

WF19, WF26 and WF41 reuse the immune domain of WF14 (``layer6``). WF22 is the
cost ladder that WF34 and WF49 build on: subclass ``CertifiedCostLadder`` and
override ``validate_item`` and ``grade``.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from ..exclusions import REFUTED, ExclusionError, ExclusionHypothesisV1, ExclusionVoteV1, plan_retests, run_plan
from ..fidelity import HostOracleContext
from ..immunity import HOLD, HOST_OBSERVERS, decide, host_danger, screen_rules, signal1
from .base import (
    CERTIFIED,
    POSITIVE,
    REFUSED,
    MalformedCandidateError,
    Session,
    Verdict,
    WorkflowFamily,
    as_fraction,
    as_int,
    canonical,
    digest,
    judge,
    refused,
    require,
    spec_from,
    typed_refusal,
)
from .exact import commitment
from .layer1 import TypedRefusal
from .layer2 import Assessment, BoundedCheckAndRepair
from .layer6 import (
    CLEAN,
    DANGER_KIND,
    EPITOPES,
    HOST_OBSERVER,
    SELF_PANEL,
    ImmuneFailureClassification,
    _parse_coefficients,
    admit_rules,
    build_rules,
    canonical_rational,
    classify_reply,
    poly_from_roots,
    require_items,
    text,
)
from .registry import register


def sealed_panel(task: Mapping[str, Any], sealed: Mapping[str, Any], host: HostOracleContext) -> list[str] | None:
    """Self panel texts when the public seal opens, else None (recorded either way)."""
    panel = require_items(sealed.get('self_panel'), 'self_panel')
    ok = host.record('self_panel_sealed', digest(panel) == task.get('self_panel_sha256'), digest(panel))
    return [s['text'] for s in panel] if ok else None


# ---------------------------------------------------------------- WF15

def kripke_sat(model: Mapping[str, Any], formula: Any, world: str) -> bool:
    """``M, w |= formula`` for atoms, not, and, or, box and dia on a finite Kripke model."""
    succ = [v for u, v in model['relation'] if u == world]
    if isinstance(formula, str):
        return formula in model['valuation'].get(world, [])
    require(isinstance(formula, list) and formula and formula[0] in ('not', 'and', 'or', 'box', 'dia'),
            'formula must be an atom or [op, ...]')
    op, args = formula[0], formula[1:]
    require(len(args) == (2 if op in ('and', 'or') else 1), f'{op} has the wrong arity')
    if op == 'not':
        return not kripke_sat(model, args[0], world)
    if op in ('and', 'or'):
        vals = [kripke_sat(model, a, world) for a in args]
        return all(vals) if op == 'and' else any(vals)
    vals = [kripke_sat(model, args[0], v) for v in succ]
    return all(vals) if op == 'box' else any(vals)


@register
class AdversaryTribunal(WorkflowFamily):
    """WF15. Prosecutor and defender commit before either reveals; only the model check rules.

    Domain: a finite Kripke model and a claim ``M, w |= box psi``. Both sides
    commit salted digests, then open them. The host checks each opening, checks
    the defence by evaluating psi at every successor, and counts the prosecution
    only when its witness is a successor at which psi fails. It refuses an opening
    that does not match its commitment and a true but unwitnessed prosecution.
    """
    spec = spec_from('WF15', 'Adversary tribunal', 7, ['WF4', 'WF14'], None, 'kripke_box_witness_check',
                     'wf15_adversary_tribunal')

    def validate(self, task):
        require(isinstance(task.get('relation'), list) and isinstance(task.get('valuation'), Mapping), 'model required')
        require(isinstance(task.get('formula'), list) and task['formula'][:1] == ['box'] and len(task['formula']) == 2,
                'the claim must be [box, psi]')
        require(task.get('world') in task.get('worlds', []), 'world must be a model world')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        commits, reveals = {}, {}
        for role in ('prosecutor', 'defender'):
            reply = session.ask(f'{role}:commit', self.prompt(task) + f'\nRole: {role}. Send only a commitment.')
            require(reply is not None and isinstance(reply.content, Mapping), f'{role} commitment missing')
            commits[role] = reply.content.get('commitment')
        for role in ('prosecutor', 'defender'):
            reply = session.ask(f'{role}:reveal', self.prompt(task) + f'\nRole: {role}. Open {commits[role]}.')
            require(reply is not None and isinstance(reply.content, Mapping), f'{role} opening missing')
            r = reply.content
            require(isinstance(r.get('salt'), str) and isinstance(r.get('claim'), Mapping), 'opening needs salt, claim')
            reveals[role] = r['claim']
            if not host.record(f'{role}_opening_matches_commitment', commitment(r['salt'], r['claim']) == commits[role],
                               str(commits[role])):
                return refused('COMMITMENT_MISMATCH', role=role)
        require(reveals['prosecutor'].get('holds') is False and reveals['defender'].get('holds') is True,
                'prosecutor claims failure, defender claims truth')
        w, psi = task['world'], task['formula'][1]
        witness = reveals['prosecutor'].get('witness')
        confirmed = [w, witness] in task['relation'] and not kripke_sat(task, psi, witness)
        truth = kripke_sat(task, task['formula'], w)
        if confirmed:
            host.record('prosecution_confirmed_by_failing_case', True, str(witness))
            return judge(host, 'PROSECUTION_UPHELD', witness=witness)
        if not host.record('defence_holds_at_every_successor', truth, str(w)):
            return refused('UNCONFIRMED_PROSECUTION', prosecution_witness=witness)
        return judge(host, 'DEFENCE_UPHELD', prosecution_witness=witness)

    def fixtures(self):
        model = {'worlds': ['w0', 'w1', 'w2', 'w3'], 'relation': [['w0', 'w1'], ['w0', 'w2'], ['w1', 'w3']],
                 'valuation': {'w1': ['p'], 'w2': ['q'], 'w3': ['p']}, 'world': 'w0'}

        def case(formula, p_claim, p_opened=None):
            p_open = p_opened or p_claim
            d_claim = {'holds': True}
            task = {'statement': 'Decide the modal claim at the world.', **model, 'formula': formula}
            return {'task': task, 'replies': [{'commitment': commitment('salt-p', p_claim)},
                                              {'commitment': commitment('salt-d', d_claim)},
                                              {'salt': 'salt-p', 'claim': p_open},
                                              {'salt': 'salt-d', 'claim': d_claim}]}
        return {
            'prosecution_witnessed': (case(['box', 'p'], {'holds': False, 'witness': 'w2'}), CERTIFIED),
            'defence_upheld_over_bogus_witness': (case(['box', ['or', 'p', 'q']], {'holds': False, 'witness': 'w2'}),
                                                  CERTIFIED),
            'opening_changed_after_commit': (case(['box', 'p'], {'holds': False, 'witness': 'w1'},
                                                  {'holds': False, 'witness': 'w2'}), REFUSED),
            'true_prosecution_without_failing_case': (case(['box', 'p'], {'holds': False, 'witness': 'w3'}), REFUSED),
        }


# ---------------------------------------------------------------- WF19

def vieta_checker(t: str, roots: Sequence[Any]) -> bool:
    """Independent clean test: canonical, monic, degree = #roots and p(r) = 0 at every root."""
    values = _parse_coefficients(t)
    if values is None:
        return False
    raw = json.loads(t)['coefficients']
    rs = [as_fraction(r, 'root') for r in roots]
    canonical_form = all(c == canonical_rational(v) for c, v in zip(raw, values, strict=True))
    vanish = all(sum((c * r ** (len(values) - 1 - i) for i, c in enumerate(values)), Fraction(0)) == 0 for r in rs)
    return canonical_form and values[0] == 1 and len(values) == len(rs) + 1 and vanish


def predict(rules: Sequence[Any], t: str) -> str:
    return next((r.target_epitope for r in rules if signal1(t, [r])), CLEAN)


@register
class FailureDerivedRuleTransfer(WorkflowFamily):
    """WF19. Rules extracted from training failures are admitted only if they transfer to held-out tasks.

    Rules are proposed from public training failures, screened by the thymus on
    the sealed self panel and admitted on two signals (WF14). The host then
    scores them on disjoint sealed held-out replies: gain = accuracy(rules) -
    accuracy(no rules). It refuses zero gain, autoimmune rules after two stages,
    overlapping splits, and halts when two independent clean checkers disagree.
    """
    spec = spec_from('WF19', 'Failure-derived rule transfer', 7, ['WF12', 'WF14'], None, 'held_out_transfer_gain',
                     'wf19_failure_derived_rule_transfer')
    stages = ('extract', 'refine')

    def validate(self, task):
        require_items(task.get('train'), 'train')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task, sealed = session.task, session.sealed
        held = require_items(sealed.get('held_out'), 'held_out')
        panel = sealed_panel(task, sealed, host)
        if panel is None:
            return refused('SELF_PANEL_SEAL_BROKEN')
        overlap = sorted({x.get('id') for x in task['train']} & {x.get('id') for x in held})
        if not host.record('splits_disjoint', not overlap, str(overlap)):
            return refused('SPLIT_OVERLAP', overlap=overlap)
        split = [x for x in [*task['train'], *held]
                 if (classify_reply(x['text'], x['roots']) == CLEAN) != vieta_checker(x['text'], x['roots'])]
        if not host.record('checkers_agree', not split, str([x.get('id') for x in split])):
            return refused('CHECKER_DISAGREEMENT', items=[x.get('id') for x in split])
        prompt, report = self.prompt(task), None
        for stage in self.stages:
            reply = session.ask(stage, prompt)
            if reply is None:
                break
            report = admit_rules(reply.content.get('rules') if isinstance(reply.content, Mapping) else None,
                                 panel, task['train'])
            if report['killed'] == 0:
                break
            prompt = self.prompt(task) + '\nThymus status: ' + canonical(report['status']).decode('utf-8')
        if report is None:
            return refused('NO_ADMISSIBLE_REPLY')
        host.record('self_tolerance_holds', report['killed'] == 0, str(report['status']))
        host.record('rules_two_signal_admitted', all(v == 'ADMITTED' for v in report['status'].values()),
                    str(report['status']))
        rules = report['admitted']
        acc_rules = sum(predict(rules, x['text']) == classify_reply(x['text'], x['roots']) for x in held)
        acc_base = sum(classify_reply(x['text'], x['roots']) == CLEAN for x in held)
        host.record('transfer_gain_positive', acc_rules > acc_base, f'{acc_rules}-{acc_base}')
        return judge(host, 'RULES_TRANSFER', rules=report['status'], gain=acc_rules - acc_base, held_out=len(held))

    def fixtures(self):
        train = [{k: v for k, v in f.items() if k != 'provenance'} for f in ImmuneFailureClassification.failures()[:5]]
        held = [{'id': 'h1', 'roots': [3, 4], 'text': text([1, '-7/1', 12])},
                {'id': 'h2', 'roots': [2, 3], 'text': text([2, -10, 12])},
                {'id': 'h3', 'roots': [4, 5], 'text': text([1, -9, 20])},
                {'id': 'h4', 'roots': [2, 5], 'text': text([1, -7, 10])}]
        task = {'statement': 'Extract detector rules from the training failures.', 'train': train,
                'self_panel_sha256': digest(SELF_PANEL)}
        good = {'rules': [{'rule_id': 'denominator_one', 'target_epitope': 'RATIONAL_NONCANONICAL', 'pattern': '/1"'},
                          {'rule_id': 'leading_two', 'target_epitope': 'NONMONIC_LEADING_COEFFICIENT',
                           'pattern': r'\[2,'}]}
        broad = {'rules': [{'rule_id': 'any_reply', 'target_epitope': 'MALFORMED_JSON', 'pattern': 'coefficients'}]}
        overfit = {'rules': [{'rule_id': 'minus_five_over_one', 'target_epitope': 'RATIONAL_NONCANONICAL',
                              'pattern': '-5/1'}]}

        def case(replies, held_out=held):
            return {'task': task, 'sealed': {'self_panel': SELF_PANEL, 'held_out': held_out}, 'replies': replies}
        return {
            'rules_transfer_to_held_out': (case([good]), CERTIFIED),
            'refined_after_thymus_kill': (case([broad, good]), CERTIFIED),
            'overfit_rule_no_gain': (case([overfit]), REFUSED),
            'autoimmune_after_two_stages': (case([broad, broad]), REFUSED),
            'overlapping_split': (case([good], [*held, {'id': 'f1', 'roots': [6, 7], 'text': text([1, -13, 42])}]),
                                  REFUSED),
            'checkers_disagree_on_repeated_root': (case([good], [*held, {'id': 'h5', 'roots': [1, 1],
                                                                         'text': text([1, 0, -1])}]), REFUSED),
        }


# ---------------------------------------------------------------- WF22

def parse_answer_line(reply: Any) -> dict[str, Any]:
    """The reply's last line must be its only ``ANSWER: ...`` line."""
    require(isinstance(reply, str), 'arm reply must be text')
    lines = [x for x in reply.strip().splitlines() if x.strip()]
    answers = [x for x in lines if x.startswith('ANSWER:')]
    require(len(answers) == 1 and lines[-1] == answers[0] and answers[0].startswith('ANSWER: '),
            'exactly one final canonical ANSWER line required')
    payload = answers[0][len('ANSWER: '):]
    if payload.startswith('UNRESOLVED '):
        code = payload[len('UNRESOLVED '):]
        require(code.isupper() and ' ' not in code, 'UNRESOLVED needs one upper-case code')
        return {'refusal': 'UNRESOLVED_' + code}
    return {'answer': [x.strip() for x in payload.split(',')]}


@register
class CertifiedCostLadder(WorkflowFamily):
    """WF22. Escalate from cheap to expensive arms only after a host refusal, on one budget.

    Items are linear systems graded by the WF7 rank test; each arm reply ends with
    one canonical ``ANSWER:`` line. The host requires arms in strictly increasing
    cost, moves an item up a rung only when the host refused the rung below,
    charges every rung to one cap, and reports cost per certified item. It
    refuses unordered ladders, a spend past the single cap, and exhausted ladders.
    """
    spec = spec_from('WF22', 'Certified cost ladder', 7, ['WF6', 'WF8', 'WF18'], 'Sweep',
                     'cost_ladder_refusal_escalation', 'wf22_certified_cost_ladder')
    item_family = TypedRefusal

    def validate(self, task):
        require(isinstance(task.get('items'), list) and task['items'], 'items required')
        require(isinstance(task.get('arms'), list) and task['arms'], 'arms required')
        for item in task['items']:
            self.validate_item(item)
        as_int(task.get('budget_units'), 'budget_units')
        return task

    def validate_item(self, item: Mapping[str, Any]) -> None:
        self.item_family().validate(item)

    def grade(self, item: Mapping[str, Any], reply: Any) -> str:
        """Host verdict for one rung; any malformed reply is a host refusal."""
        try:
            return self.item_family().check(item, {}, parse_answer_line(reply), HostOracleContext()).verdict
        except MalformedCandidateError:
            return REFUSED

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        costs = [as_int(a.get('cost'), 'cost') for a in task['arms']]
        ordered = all(a < b for a, b in zip(costs, costs[1:], strict=False)) and costs[0] > 0
        if not host.record('arms_strictly_cost_ordered', ordered, str(costs)):
            return refused('LADDER_NOT_COST_ORDERED', costs=costs)
        cap, spent, rows = task['budget_units'], 0, []
        for k, item in enumerate(task['items']):
            row = {'item': k, 'rungs': [], 'verdict': REFUSED}
            for arm, cost in zip(task['arms'], costs, strict=True):
                if spent + cost > cap:
                    host.record('one_budget_covers_ladder', False, f'{spent}+{cost}>{cap}')
                    return refused('BUDGET_EXHAUSTED', spent=spent, cap=cap, rows=rows)
                spent += cost
                reply = session.ask(f"{k}:{arm['arm']}", self.prompt(item) + f"\nArm: {arm['arm']}")
                verdict = self.grade(item, reply.content) if reply is not None else REFUSED
                row['rungs'].append(arm['arm'])
                if verdict in POSITIVE:
                    row['verdict'] = verdict
                    break
            rows.append(row)
        certified_items = sum(r['verdict'] in POSITIVE for r in rows)
        host.record('one_budget_covers_ladder', spent <= cap, f'{spent}/{cap}')
        host.record('every_item_certified', certified_items == len(rows), str(rows))
        cost = Fraction(spent, certified_items) if certified_items else None
        return judge(host, 'LADDER_CERTIFIED', spent=spent, rows=rows,
                     cost_to_certified=None if cost is None else str(cost))

    def fixtures(self):
        solvable = {'statement': 'Solve A x = b exactly; end with one ANSWER line.', 'A': [[1, 1], [1, -1]],
                    'b': [3, 1]}
        singular = {**solvable, 'A': [[1, 1], [2, 2]], 'b': [3, 7]}
        arms = [{'arm': 'small', 'cost': 1}, {'arm': 'medium', 'cost': 4}, {'arm': 'large', 'cost': 16}]
        ok = ['Adding the rows gives x = 2.\nANSWER: 2, 1', 'Guessing.\nANSWER: 1, 2',
              'Row 2 is twice row 1 but 7 != 6.\nANSWER: UNRESOLVED INCONSISTENT']

        def case(replies, ladder=arms, cap=32):
            return {'task': {'statement': 'Run the cost ladder.', 'items': [solvable, singular], 'arms': ladder,
                             'budget_units': cap}, 'replies': replies}
        bluffs = [ok[0], ok[1], 'ANSWER: 1, 2\nANSWER: UNRESOLVED INCONSISTENT', 'ANSWER: 0, 3']
        return {
            'escalated_after_bluff': (case(ok), CERTIFIED),
            'ladder_not_cost_ordered': (case(ok, [arms[1], arms[0], arms[2]]), REFUSED),
            'spend_past_single_cap': (case(ok, cap=5), REFUSED),
            'ladder_exhausted_on_bluffs': (case(bluffs), REFUSED),
        }


# ---------------------------------------------------------------- WF26

ANTIBODIES = {
    'MALFORMED_JSON': 'Reply with one JSON object of the form {"coefficients": [...]} and nothing else.',
    'RATIONAL_NONCANONICAL': 'Write integers as integers and other rationals as p/q in lowest terms.',
    'NONMONIC_LEADING_COEFFICIENT': 'The leading coefficient must be 1.',
    'SIGN_MISMATCH': 'Some coefficient signs are wrong; the sign of each coefficient follows Vieta.',
    'WRONG_VALUE': 'The coefficients do not vanish at the stated roots.',
}


@register
class MultiRoundAntibodyDialogue(BoundedCheckAndRepair):
    """WF26. Each host-classified failure becomes a typed negative constraint carried into later rounds.

    Domain: the monic polynomial with stated roots (WF14). The exact oracle is
    equality with the expanded product. A rejected round adds the epitope's fixed
    constraint (never a coefficient value) to the antibody set, and every later
    prompt carries the whole set. Refused: recurring failures that exhaust the
    round limit and replies that never parse.
    """
    spec = spec_from('WF26', 'Multi-round antibody dialogue', 7, ['WF9', 'WF14'], None,
                     'epitope_antibody_exact_oracle', 'wf26_multi_round_antibody_dialogue')

    def validate(self, task):
        require(isinstance(task.get('roots'), list) and task['roots'], 'roots required')
        self.max_attempts(task)
        return task

    def assess(self, task, sealed, content) -> Assessment:
        require(isinstance(content, str), 'reply must be text')
        epitope = classify_reply(content, task['roots'])
        if epitope != CLEAN and epitope not in [a['epitope'] for a in self._antibodies]:
            self._antibodies.append({'epitope': epitope, 'constraint': ANTIBODIES[epitope]})
        return Assessment(epitope == CLEAN, {'antibodies': list(self._antibodies)}, epitope)

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        self._antibodies: list[dict[str, str]] = []
        verdict = super().run(session, host)
        answer = [canonical_rational(c) for c in poly_from_roots(session.task['roots'])]
        blob = canonical(self._antibodies).decode('utf-8') + json.dumps(self._antibodies)
        forms = (canonical(answer).decode('utf-8'), json.dumps(answer))
        free = host.record('antibodies_answer_free', not any(f in blob for f in forms), blob)
        if verdict.verdict == CERTIFIED and not free:
            return refused('ANSWER_LEAK')
        return Verdict(verdict.verdict, verdict.code, {**verdict.detail, 'antibodies': len(self._antibodies)})

    def fixtures(self):
        task = {'statement': 'Give the monic polynomial with roots 1, 2, 3 as JSON coefficients, highest first.',
                'roots': [1, 2, 3], 'max_attempts': 3}
        return {
            'repaired_with_two_antibodies': ({'task': task, 'replies': [text([2, -12, 22, -12]), text([1, 6, 11, 6]),
                                                                        text([1, -6, 11, -6])]}, CERTIFIED),
            'recurring_epitope_exhausts_rounds': ({'task': task, 'replies': [text([2, -12, 22, -12])] * 3}, REFUSED),
            'never_parses': ({'task': task, 'replies': ['coefficients: 1, -6, 11, -6'] * 3}, REFUSED),
        }


# ---------------------------------------------------------------- WF41

@register
class DetectorAdequacyTwoSignal(WorkflowFamily):
    """WF41. Admit a detector only with a complete calibration record and two independent signals.

    Domain: the WF14 polynomial replies for fixed roots. The submission must carry
    positive, negative, collision and metamorphic cases and one representative per
    epitope class, so detector and host classifier agree on a class-representative
    set. The host also requires zero hits on the sealed self panel and Signal 2
    from its own classifier under a host-assigned observer; a reply that names a
    danger observer is refused, so a pattern alone stays diagnostic. It also
    refuses missing classes, self hits and inconsistent rewrites.
    """
    spec = spec_from('WF41', 'Detector adequacy and two-signal admission', 7, ['WF14'], 'WF14',
                     'detector_calibration_completeness', 'wf41_detector_adequacy_and_two_signal_admission')

    def validate(self, task):
        require(isinstance(task.get('roots'), list) and task['roots'], 'roots required')
        return task

    def check(self, task, sealed, content, host):
        panel = sealed_panel(task, sealed, host)
        if panel is None:
            return refused('SELF_PANEL_SEAL_BROKEN')
        require(isinstance(content, Mapping) and isinstance(content.get('calibration'), Mapping),
                'calibration required')
        rule = build_rules([content.get('rule')])[0]
        cal, roots, target = content['calibration'], task['roots'], rule.target_epitope

        def cls(t: str) -> str:
            return classify_reply(t, roots)

        def fires(t: str) -> bool:
            return bool(signal1(t, [rule]))

        def cases(name: str) -> list[Any]:
            got = cal.get(name)
            require(isinstance(got, list) and got, f'{name} cases required')
            return got
        pos, neg, col, meta = cases('positive'), cases('negative'), cases('collision'), cases('metamorphic')
        reps = cal.get('representatives')
        require(isinstance(reps, Mapping), 'representatives required')
        host.record('positives_fire', all(cls(t) == target and fires(t) for t in pos), str(len(pos)))
        host.record('negatives_silent', all(cls(t) == CLEAN and not fires(t) for t in neg), str(len(neg)))
        host.record('collisions_silent', all(cls(t) not in (target, CLEAN) and not fires(t) for t in col),
                    str(len(col)))
        host.record('metamorphic_consistent', all(isinstance(p, list) and len(p) == 2 and p[0] != p[1]
                                                  and cls(p[0]) == cls(p[1]) and fires(p[0]) == fires(p[1])
                                                  for p in meta), str(len(meta)))
        classes = {*EPITOPES, CLEAN}
        host.record('one_representative_per_class', set(reps) == classes, str(sorted(reps)))
        host.record('detector_equals_host_on_representatives',
                    all(cls(t) == k and fires(t) == (k == target) for k, t in reps.items()), str(len(reps)))
        host.record('zero_self_panel_hits', not screen_rules([rule], panel)[1], str(len(panel)))
        named = sorted(k for k in content if 'observer' in str(k) or 'danger' in str(k))
        host.record('observer_assigned_by_host', not named, str(named))
        fired = [t for t in [*pos, *reps.values(), *(x for p in meta for x in p)] if fires(t)]
        held = [decide(signal1(t, [rule]), None if cls(t) == CLEAN else host_danger(DANGER_KIND, HOST_OBSERVER, t),
                       HOST_OBSERVERS) for t in fired]
        host.record('two_independent_signals', all(d.disposition == HOLD and d.refusal_code is None for d in held),
                    str([d.disposition for d in held]))
        degrees = {len(_parse_coefficients(t) or []) - 1 for t in panel}
        return judge(host, 'DETECTOR_ADMITTED', rule=rule.rule_id,
                     self_panel={'size': len(panel), 'distinct_degrees': len(degrees)})

    def fixtures(self):
        task = {'statement': 'Submit one detector with its calibration record.', 'roots': [1, 2],
                'self_panel_sha256': digest(SELF_PANEL)}
        reps = {CLEAN: text([1, -3, 2]), 'MALFORMED_JSON': "{'coefficients': [1, -3, 2]}",
                'RATIONAL_NONCANONICAL': text([1, '-3/1', 2]), 'NONMONIC_LEADING_COEFFICIENT': text([2, -6, 4]),
                'SIGN_MISMATCH': text([1, 3, 2]), 'WRONG_VALUE': text([1, -4, 2])}
        cal = {'positive': [text([1, '-3/1', 2]), text([1, '-3/1', '2/1'])],
               'negative': [text([1, -3, 2]), '{"coefficients":[1,-3,2]}'],
               'collision': [text([2, -6, 4]), text([1, -3, 21])],
               'metamorphic': [[text([1, '-3/1', 2]), '{"coefficients":[1,"-3/1",2]}']], 'representatives': reps}

        def case(pattern='/1"', calibration=cal, **extra):
            reply = {'rule': {'rule_id': 'denominator_one', 'target_epitope': 'RATIONAL_NONCANONICAL',
                              'pattern': pattern}, 'calibration': calibration, **extra}
            return {'task': task, 'sealed': {'self_panel': SELF_PANEL}, 'replies': [reply]}
        partial = {**cal, 'representatives': {k: v for k, v in reps.items() if k != 'SIGN_MISMATCH'}}
        return {
            'calibrated_detector_admitted': (case(), CERTIFIED),
            'missing_class_representative': (case(calibration=partial), REFUSED),
            'fires_on_sealed_self_panel': (case(pattern='/'), REFUSED),
            'whitespace_rewrite_changes_firing': (case(pattern=', "-3/1"'), REFUSED),
            'pattern_alone_reported_as_danger': (case(signal2_observer='DETECTOR'), REFUSED),
            'reply_names_allowlisted_observer': (case(signal2_observer='host.contract_check'), REFUSED),
        }


def _poly(coefficients: Sequence[int], x: int) -> int:
    """Exact integer value of sum(c_i * x**i) by Horner's rule."""
    out = 0
    for c in reversed(coefficients):
        out = out * x + c
    return out


@register
class ExclusionHypothesisRetest(WorkflowFamily):
    """WF51. Treat every "don't search here" as a hypothesis and spend tests where models disagree.

    Domain: integer roots of an integer polynomial over named, disjoint integer
    branches. Stage ``exclude`` returns exclusions: a branch, the seats that
    voted on it with their model family, and a falsifier (witness points inside
    the branch, cost = number of points). The host classifies each exclusion
    with ``pfp_core.exclusions`` (seats of one family are one vote), plans
    falsifiers frontier first, then uncorroborated, then probably-dead ones no
    dearer than ``dead_floor``, under ``retest_budget``, and evaluates them
    exactly. A refuted exclusion reopens its branch. Stage ``solve`` sees only
    open branches and returns a root, or ``null`` to claim there is none; the
    host checks the root or scans every open branch. With ``retest`` false the
    same task is the control arm: no falsifier runs, and a wrong exclusion
    can hide the answer behind a lawful typed refusal.
    """
    spec = spec_from('WF51', 'Exclusion hypotheses with cheapest falsifiers', 7, ['WF14', 'WF31'], None,
                     'exact_falsifier_and_open_branch_check', 'wf51_exclusion_hypotheses_with_cheapest_falsifiers')
    MAX_WIDTH = 4096

    def validate(self, task):
        super().validate(task)
        coefficients = task.get('coefficients')
        require(isinstance(coefficients, list) and coefficients, 'coefficients must be a nonempty list')
        for i, c in enumerate(coefficients):
            as_int(c, f'coefficients[{i}]')
        branches = task.get('branches')
        require(isinstance(branches, Mapping) and branches, 'branches must be a nonempty object')
        spans = sorted((as_int(b[0], name), as_int(b[1], name), name) for name, b in branches.items()
                       if isinstance(b, list) and len(b) == 2)
        require(len(spans) == len(branches), 'each branch is [lo, hi]')
        require(all(lo <= hi for lo, hi, _ in spans), 'each branch needs lo <= hi')
        require(all(a[1] < b[0] for a, b in zip(spans, spans[1:], strict=False)), 'branches must be disjoint')
        require(sum(hi - lo + 1 for lo, hi, _ in spans) <= self.MAX_WIDTH, 'branches too wide to scan')
        for key in ('retest_budget', 'dead_floor', 'min_families'):
            require(as_int(task.get(key), key) >= (1 if key == 'min_families' else 0), f'{key} out of range')
        require(type(task.get('retest')) is bool, 'retest must be a bool')
        return task

    @staticmethod
    def hypotheses(task, content) -> tuple[list[Any], dict[str, list[int]]]:
        require(isinstance(content, Mapping) and isinstance(content.get('exclusions'), list), 'exclusions')
        out, points = [], {}
        for row in content['exclusions']:
            require(isinstance(row, Mapping) and row.get('branch') in task['branches'], 'unknown branch')
            pts = row.get('falsifier') or []
            require(isinstance(pts, list), 'falsifier must be a list of points')
            pts = [as_int(x, 'falsifier point') for x in pts]
            votes = tuple(ExclusionVoteV1(v.get('seat'), v.get('family'), v.get('excludes'))
                          for v in row.get('votes', ()) if isinstance(v, Mapping))
            out.append(ExclusionHypothesisV1(row.get('id'), row['branch'], f'no root in {row["branch"]}',
                                             canonical(pts).decode('utf-8') if pts else '', len(pts), votes))
            points[row.get('id')] = pts
        return out, points

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        reply = session.ask('exclude', self.prompt(task))
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        try:
            hyps, points = self.hypotheses(task, reply.content)
        except ExclusionError as exc:
            return refused(str(exc).split(':', 1)[0], reason=str(exc))
        for h in hyps:
            lo, hi = task['branches'][h.branch]
            inside = all(lo <= x <= hi for x in points[h.exclusion_id])
            if not host.record(f'falsifier_within_branch:{h.exclusion_id}', inside, h.falsifier):
                return refused('FALSIFIER_OUTSIDE_BRANCH', exclusion=h.exclusion_id)
        budget = task['retest_budget'] if task['retest'] else 0
        plan = plan_retests(hyps, budget=budget, dead_floor=task['dead_floor'], min_families=task['min_families'])
        coefficients = task['coefficients']
        status = run_plan(plan, hyps, lambda h: any(_poly(coefficients, x) == 0 for x in points[h.exclusion_id]))
        host.record('retest_within_budget', plan.cost <= budget, f'{plan.cost}|{budget}')
        closed = sorted({h.branch for h in hyps if status[h.exclusion_id] != REFUTED})
        open_ = sorted(b for b in task['branches'] if b not in closed)
        detail = {'plan': plan.to_dict(), 'status': status, 'open': open_, 'closed': closed}
        return self.solve(session, host, open_, detail)

    def solve(self, session: Session, host: HostOracleContext, open_: list[str], detail: dict[str, Any]) -> Verdict:
        """Ask for a root in the open branches; certify it, or check a no-root claim by full scan."""
        task, coefficients = session.task, session.task['coefficients']
        reply = session.ask('solve', self.prompt(task) + f'\nOpen branches: {", ".join(open_)}')
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY', **detail)
        require(isinstance(reply.content, Mapping) and 'root' in reply.content, 'solve reply needs root')
        root = reply.content['root']
        if root is None:
            scan = [x for b in open_ for x in range(task['branches'][b][0], task['branches'][b][1] + 1)]
            if not host.record('no_root_in_open_branches', all(_poly(coefficients, x) != 0 for x in scan),
                               canonical(open_).decode('utf-8')):
                return refused('MISSED_ROOT_IN_OPEN_BRANCH', **detail)
            return typed_refusal('NO_ROOT_IN_OPEN_BRANCHES', **detail)
        root = as_int(root, 'root')
        in_open = any(task['branches'][b][0] <= root <= task['branches'][b][1] for b in open_)
        if not host.record('root_in_open_branch', in_open, str(root)):
            return refused('ANSWER_IN_CLOSED_BRANCH', root=root, **detail)
        host.record('root_verified', _poly(coefficients, root) == 0, str(root))
        return judge(host, 'ROOT_CERTIFIED', root=root, **detail)

    def fixtures(self):
        task = {'statement': 'Find an integer root of the polynomial inside the branches.',
                'coefficients': [-35, -2, 1],
                'branches': {'b0': [-4, 0], 'b1': [1, 5], 'b2': [6, 10], 'b3': [11, 15]},
                'retest_budget': 10, 'dead_floor': 3, 'min_families': 2, 'retest': True}

        def ex(eid, branch, pts, *votes):
            return {'id': eid, 'branch': branch, 'falsifier': pts,
                    'votes': [{'seat': s, 'family': f, 'excludes': e} for s, f, e in votes]}
        both = (('s1', 'family_a', True), ('s2', 'family_b', True))
        frontier = ex('e_b0', 'b0', [-4, -3, -2, -1, 0], ('s1', 'family_a', True), ('s2', 'family_b', False))
        wrong = ex('e_b2', 'b2', [6, 7, 8], *both)
        right = ex('e_b3', 'b3', [11, 12, 13, 14, 15], *both)
        exclusions = [frontier, wrong, right]

        def bundle(root, exs=None, **over):
            return {'task': {**task, **over}, 'replies': [{'exclusions': exs or exclusions}, {'root': root}]}
        one_family = ex('e_b2', 'b2', [6, 7, 8], ('s1', 'family_a', True), ('s2', 'family_a', True),
                        ('s3', 'family_a', True))
        return {
            'planted_wrong_exclusion_refuted_by_cheap_retest': (bundle(7), 'HOST_CERTIFIED'),
            'same_family_agreement_is_one_vote': (bundle(7, [frontier, one_family, right], retest_budget=3),
                                                  'HOST_CERTIFIED'),
            'control_without_retest_hides_the_answer': (bundle(None, retest=False), 'TYPED_REFUSAL'),
            'exclusion_without_falsifier': (bundle(7, [ex('e_b2', 'b2', [], *both)]), 'REFUSED'),
            'falsifier_outside_its_branch': (bundle(7, [ex('e_b2', 'b2', [3], *both)]), 'REFUSED'),
            'answer_in_closed_branch': (bundle(12), 'REFUSED'),
            'false_no_root_claim': (bundle(None), 'REFUSED'),
            'wrong_root': (bundle(3), 'REFUSED'),
        }
