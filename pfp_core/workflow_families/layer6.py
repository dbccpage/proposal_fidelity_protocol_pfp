"""Layer 6 families: immune classification, dossier replay and channel comparison.

WF14 owns the shared immune domain used by WF15, WF19, WF26 and WF41: replies
that give the coefficients of the monic polynomial with stated rational roots,
an exact host classifier that names the epitope of a defective reply, and
``admit_rules``, which runs thymic negative selection and the two-signal table
from ``pfp_core.immunity`` over candidate detector rules.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from eis.domain.value_objects import DetectorRule

from ..fidelity import HostOracleContext
from ..immunity import HOLD, HOST_OBSERVERS, AntibodyRegistry, decide, host_danger, screen_rules, signal1
from .base import (
    CERTIFIED,
    REFUSED,
    TYPED_REFUSAL,
    Session,
    Verdict,
    WorkflowFamily,
    as_fraction,
    as_int,
    digest,
    judge,
    refused,
    require,
    spec_from,
)
from .exact import sha256_bytes
from .registry import register

# ---------------------------------------------------------------- shared immune domain

EPITOPES = ('MALFORMED_JSON', 'RATIONAL_NONCANONICAL', 'NONMONIC_LEADING_COEFFICIENT', 'SIGN_MISMATCH',
            'WRONG_VALUE')
CLEAN = 'CLEAN'
HOST_OBSERVER = 'host.contract_check'
DANGER_KIND = 'MALFORMED_PAYLOAD'


def poly_from_roots(roots: Sequence[Any]) -> list[Fraction]:
    """Coefficients of prod (x - r), highest degree first."""
    coeffs = [Fraction(1)]
    for r in (as_fraction(x, 'root') for x in roots):
        coeffs = [a - r * b for a, b in zip([*coeffs, Fraction(0)], [Fraction(0), *coeffs], strict=True)]
    return coeffs


def canonical_rational(x: Fraction) -> int | str:
    return x.numerator if x.denominator == 1 else f'{x.numerator}/{x.denominator}'


def classify_reply(text: Any, roots: Sequence[Any]) -> str:
    """Host epitope of a reply text, or CLEAN when it is the canonical expected polynomial."""
    values = _parse_coefficients(text)
    if values is None:
        return 'MALFORMED_JSON'
    coeffs = json.loads(text)['coefficients']
    expected = poly_from_roots(roots)
    if any(c != canonical_rational(v) for c, v in zip(coeffs, values, strict=True)):
        out = 'RATIONAL_NONCANONICAL'
    elif values[0] != 1:
        out = 'NONMONIC_LEADING_COEFFICIENT'
    elif values == expected:
        out = CLEAN
    elif len(values) == len(expected) and all(abs(a) == abs(b) for a, b in zip(values, expected, strict=True)):
        out = 'SIGN_MISMATCH'
    else:
        out = 'WRONG_VALUE'
    return out


def _parse_coefficients(text: Any) -> list[Fraction] | None:
    try:
        obj = json.loads(text) if isinstance(text, str) else None
    except ValueError:
        return None
    coeffs = obj.get('coefficients') if isinstance(obj, dict) else None
    if not isinstance(coeffs, list) or not coeffs or any(type(c) not in (int, str) for c in coeffs):
        return None
    try:
        return [Fraction(c) for c in coeffs]
    except (ValueError, ZeroDivisionError):
        return None


def build_rules(specs: Any) -> list[DetectorRule]:
    require(isinstance(specs, list) and specs, 'rules must be a non-empty list')
    rules = []
    for s in specs:
        require(isinstance(s, Mapping) and s.get('target_epitope') in EPITOPES, 'rule needs a known target_epitope')
        try:
            rules.append(DetectorRule(str(s.get('rule_id', '')), s['target_epitope'], s.get('pattern', '')))
        except (TypeError, ValueError) as exc:
            require(False, f'bad rule: {exc}')
    require(len({r.rule_id for r in rules}) == len(rules), 'rule ids must be unique')
    return rules


def admit_rules(specs: Any, self_panel: Sequence[str], failures: Sequence[Mapping[str, Any]],
                observer: str = HOST_OBSERVER, observers: frozenset[str] = HOST_OBSERVERS) -> dict[str, Any]:
    """Thymus screen, then the two-signal table on every failure each survivor matches.

    A rule is ADMITTED only when it matches at least one failure and every match
    is held by an independent host danger signal of the rule's own epitope.
    """
    rules = build_rules(specs)
    survivors, killed = screen_rules(rules, list(self_panel))
    status = {k['rule_id']: 'KILLED_BY_THYMUS' for k in killed}
    admitted = []
    for rule in survivors:
        hits = 0
        for f in failures:
            matches = signal1(f['text'], [rule])
            if not matches:
                continue
            hits += 1
            epitope = classify_reply(f['text'], f['roots'])
            danger = None if epitope == CLEAN else host_danger(DANGER_KIND, observer, f['text'])
            d = decide(matches, danger, observers)
            if danger is None:
                code = 'DIAGNOSTIC_ONLY'
            elif d.disposition != HOLD or d.refusal_code:
                code = d.refusal_code or 'NOT_HELD'
            else:
                code = 'EPITOPE_MISMATCH' if epitope != rule.target_epitope else None
            if code:
                status[rule.rule_id] = code
                break
        else:
            status[rule.rule_id] = 'ADMITTED' if hits else 'UNMATCHED'
        if status[rule.rule_id] == 'ADMITTED':
            admitted.append(rule)
    return {'status': dict(sorted(status.items())), 'admitted': admitted, 'killed': len(killed)}


def classify_failures(failures: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in failures:
        e = classify_reply(f['text'], f['roots'])
        out[e] = out.get(e, 0) + 1
    return dict(sorted(out.items()))


def antibody_support(failures: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Provisional custody per epitope needs >= 3 observations sharing no provenance key."""
    reg = AntibodyRegistry()
    for i, f in enumerate(failures):
        e = classify_reply(f['text'], f['roots'])
        if e == CLEAN:
            continue
        p = f.get('provenance', {})
        reg.observe(e, f.get('id', str(i)), model_id=p.get('model', ''), scaffold_digest=p.get('scaffold', ''),
                    precedent_digest=p.get('precedent', ''), lineage_root=p.get('lineage', ''))
    return {e: reg.status(e)['custody'] for e in sorted(reg.observations)}


def require_items(items: Any, name: str) -> list[Mapping[str, Any]]:
    require(isinstance(items, list) and items, f'{name} must be a non-empty list')
    require(all(isinstance(x, Mapping) and isinstance(x.get('text'), str) and isinstance(x.get('roots'), list)
                for x in items), f'{name} entries need text and roots')
    return items


def text(coeffs: Sequence[Any]) -> str:
    return json.dumps({'coefficients': list(coeffs)})


SELF_PANEL = [{'roots': [1, 2], 'text': text([1, -3, 2])}, {'roots': [2, -2], 'text': text([1, 0, -4])},
              {'roots': ['1/2'], 'text': text([1, '-1/2'])}, {'roots': [3, 1, 0], 'text': text([1, -4, 3, 0])}]


def _prov(k: int) -> dict[str, str]:
    return {'model': f'm{k}', 'scaffold': f's{k}', 'precedent': f'p{k}', 'lineage': f'l{k}'}


@register
class ImmuneFailureClassification(WorkflowFamily):
    """WF14. Classify refused runs into epitopes and admit detector rules only on two signals.

    Domain: replies giving the monic polynomial with stated rational roots. The
    host verifies the seal on its self panel of clean replies, kills any rule
    that fires on that panel, and admits a surviving rule only when each failure
    it matches carries an allowlisted host danger signal of the rule's epitope.
    It refuses autoimmune rules, pattern-only matches and mislabelled epitopes.
    """
    spec = spec_from('WF14', 'Immune failure classification', 6, ['WF7', 'WF12'], None,
                     'thymus_two_signal_admission', 'wf14_immune_failure_classification')

    def validate(self, task):
        require_items(task.get('failures'), 'failures')
        require(isinstance(task.get('self_panel_sha256'), str), 'self panel seal required')
        return task

    def check(self, task, sealed, content, host):
        panel = require_items(sealed.get('self_panel'), 'self_panel')
        require(isinstance(content, Mapping), 'reply must be an object')
        if not host.record('self_panel_sealed', digest(panel) == task['self_panel_sha256'], digest(panel)):
            return refused('SELF_PANEL_SEAL_BROKEN')
        host.record('self_panel_clean', all(classify_reply(s['text'], s['roots']) == CLEAN for s in panel),
                    str(len(panel)))
        report = admit_rules(content.get('rules'), [s['text'] for s in panel], task['failures'])
        status = report['status']
        host.record('no_autoimmune_rule', report['killed'] == 0, str(status))
        host.record('every_rule_two_signal_admitted', all(v == 'ADMITTED' for v in status.values()), str(status))
        return judge(host, 'RULES_ADMITTED', rules=status, epitopes=classify_failures(task['failures']),
                     antibodies=antibody_support(task['failures']))

    @staticmethod
    def failures() -> list[dict[str, Any]]:
        return [
            {'id': 'f1', 'roots': [2, 3], 'text': text([1, '-5/1', 6]), 'provenance': _prov(1)},
            {'id': 'f2', 'roots': [1, 4], 'text': text([1, '-5/1', 4]), 'provenance': _prov(2)},
            {'id': 'f3', 'roots': [0, 5], 'text': text([1, '-5/1', 0]), 'provenance': _prov(3)},
            {'id': 'f4', 'roots': [1, 3], 'text': text([2, -8, 6]), 'provenance': _prov(4)},
            {'id': 'f5', 'roots': [1, 2], 'text': "{'coefficients': [1, -3, 2]}", 'provenance': _prov(5)},
            {'id': 'f6', 'roots': [1, 5], 'text': text([1, 6, 5]), 'provenance': _prov(6)},
            {'id': 'f7', 'roots': [2, 4], 'text': text([1, -6, 8]), 'provenance': {'model': 'self-report'}},
        ]

    def fixtures(self):
        task = {'statement': 'Propose detector rules for the observed failures.', 'failures': self.failures(),
                'self_panel_sha256': digest(SELF_PANEL)}
        sealed = {'self_panel': SELF_PANEL}
        good = [{'rule_id': 'denominator_one', 'target_epitope': 'RATIONAL_NONCANONICAL', 'pattern': '/1"'},
                {'rule_id': 'leading_two', 'target_epitope': 'NONMONIC_LEADING_COEFFICIENT', 'pattern': r'\[2,'},
                {'rule_id': 'single_quotes', 'target_epitope': 'MALFORMED_JSON', 'pattern': r"\{'"}]

        def case(rules, panel_seal=None):
            t = dict(task, self_panel_sha256=panel_seal or task['self_panel_sha256'])
            return {'task': t, 'sealed': sealed, 'replies': [{'rules': rules}]}
        return {
            'two_signal_rules_admitted': (case(good), CERTIFIED),
            'autoimmune_rule_killed': (case([*good, {'rule_id': 'any_reply', 'target_epitope': 'MALFORMED_JSON',
                                                     'pattern': 'coefficients'}]), REFUSED),
            'pattern_only_on_clean_failure': (case([{'rule_id': 'minus_six', 'target_epitope': 'WRONG_VALUE',
                                                     'pattern': '-6, 8'}]), REFUSED),
            'mislabelled_epitope': (case([{'rule_id': 'denominator_one', 'target_epitope': 'SIGN_MISMATCH',
                                           'pattern': '/1"'}]), REFUSED),
            'forged_self_panel_seal': (case(good, digest(SELF_PANEL[:2])), REFUSED),
        }


# ---------------------------------------------------------------- dossier replay

def grade_cycle_duality(item: Mapping[str, Any], raw: str) -> str:
    """Grade one weighted-digraph reply: a feasible potential or a negative cycle (Farkas duality).

    ``phi[v] - phi[u] <= w(u, v)`` for every edge certifies feasibility; a closed
    walk of negative total weight certifies that no potential exists. One of the
    two always exists, so a correct reply is always gradeable.
    """
    n = as_int(item['n'], 'n')
    w = {(as_int(u, 'u'), as_int(v, 'v')): as_fraction(c, 'w') for u, v, c in item['edges']}
    try:
        obj = json.loads(raw)
    except ValueError:
        return REFUSED
    if isinstance(obj, dict) and isinstance(obj.get('potential'), list) and len(obj['potential']) == n:
        try:
            phi = [as_fraction(x, 'phi') for x in obj['potential']]
        except ValueError:
            return REFUSED
        return CERTIFIED if all(phi[v] - phi[u] <= c for (u, v), c in w.items()) else REFUSED
    cyc = obj.get('negative_cycle') if isinstance(obj, dict) else None
    if isinstance(cyc, list) and len(cyc) >= 2 and all(type(x) is int for x in cyc):
        steps = list(zip(cyc, [*cyc[1:], cyc[0]], strict=True))
        if all(s in w for s in steps) and sum(w[s] for s in steps) < 0:
            return TYPED_REFUSAL
    return REFUSED


def _code_bytes(code: Any) -> bytes:
    parts = [code.co_code, repr(code.co_names).encode('utf-8')]
    for c in code.co_consts:
        parts.append(_code_bytes(c) if hasattr(c, 'co_code') else repr(c).encode('utf-8'))
    return b'|'.join(parts)


def source_pin(fn: Any) -> str:
    """SHA-256 of a grader's bytecode, names and constants (nested code included): moves when the grader does."""
    return sha256_bytes(_code_bytes(fn.__code__))


GRADERS = {'cycle_duality': grade_cycle_duality}


def dossier_cell(cell_id: str, item: Mapping[str, Any], raw: str, grade: str) -> dict[str, Any]:
    return {'cell_id': cell_id, 'input': dict(item), 'input_sha256': digest(item), 'raw_reply': raw,
            'raw_reply_sha256': sha256_bytes(raw.encode('utf-8')), 'grade': grade}


@register
class DossierReplayCampaign(WorkflowFamily):
    """WF18. Replay a frozen campaign dossier with zero model calls; every grade must reproduce.

    Each cell stores its input, the raw reply bytes and their SHA-256 values; the
    dossier pins the grader source. The host checks each digest and the pin,
    regrades every stored reply with the weighted-cycle duality grader, and
    refuses any drifted byte, drifted pin or grade that does not reproduce.
    """
    spec = spec_from('WF18', 'Dossier replay campaign', 6, ['WF6', 'WF12'], None,
                     'dossier_replay_reproduces_grades', 'wf18_dossier_replay_campaign')

    def validate(self, task):
        d = task.get('dossier')
        require(isinstance(d, Mapping) and isinstance(d.get('cells'), list) and d['cells'], 'dossier cells required')
        require(isinstance(d.get('source_pins'), Mapping) and d.get('grader') in GRADERS, 'grader and pins required')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        d = session.task['dossier']
        grader = GRADERS[d['grader']]
        pin_ok = host.record('source_pin_matches', d['source_pins'].get(d['grader']) == source_pin(grader),
                             d['grader'])
        drift, regrades = [], {}
        for cell in d['cells']:
            raw = cell.get('raw_reply')
            require(isinstance(raw, str), 'raw_reply must be stored text')
            if sha256_bytes(raw.encode('utf-8')) != cell.get('raw_reply_sha256'):
                drift.append(f"{cell['cell_id']}:raw_reply")
            if digest(cell.get('input')) != cell.get('input_sha256'):
                drift.append(f"{cell['cell_id']}:input")
            regrades[cell['cell_id']] = grader(cell['input'], raw)
        host.record('stored_bytes_match_digests', not drift, str(drift))
        mismatched = sorted(k for k, c in zip(regrades, d['cells'], strict=True) if c['grade'] != regrades[k])
        host.record('every_grade_reproduces', not mismatched, str(mismatched))
        host.record('zero_model_calls', not session.transcript, str(len(session.transcript)))
        if not pin_ok:
            return refused('SOURCE_PIN_DRIFT')
        if drift:
            return refused('STORED_BYTES_DRIFTED', drift=drift)
        return judge(host, 'REPLAY_REPRODUCED', cells=len(regrades), mismatched=mismatched)

    def fixtures(self):
        feasible = {'n': 3, 'edges': [[0, 1, 2], [1, 2, -1], [0, 2, 3], [2, 0, 1]]}
        negative = {'n': 3, 'edges': [[0, 1, 1], [1, 2, -3], [2, 0, 1]]}
        cells = [dossier_cell('c1', feasible, '{"potential": [0, 2, 1]}', CERTIFIED),
                 dossier_cell('c2', negative, '{"negative_cycle": [0, 1, 2]}', TYPED_REFUSAL),
                 dossier_cell('c3', feasible, '{"potential": [0, 0, 0]}', REFUSED)]
        pins = {'cycle_duality': source_pin(grade_cycle_duality)}

        def case(cs, p=pins):
            return {'task': {'statement': 'Replay the frozen dossier.',
                             'dossier': {'grader': 'cycle_duality', 'source_pins': p, 'cells': cs}}, 'replies': []}
        edited = dict(cells[0], raw_reply='{"potential": [0, 2, 2]}')
        regraded = [cells[0], dict(cells[1], grade=CERTIFIED), cells[2]]
        return {
            'replay_reproduces_every_grade': (case(cells), CERTIFIED),
            'reply_byte_drifted': (case([edited, *cells[1:]]), REFUSED),
            'grade_not_reproduced': (case(regraded), REFUSED),
            'grader_pin_drifted': (case(cells, {'cycle_duality': '0' * 64}), REFUSED),
        }


# ---------------------------------------------------------------- channel comparison

@register
class ProposalChannelComparison(WorkflowFamily):
    """WF35. Compare proposal channels under one fixed host check; acceptance depends only on reply bytes.

    Each arm (prompt, grammar mask, logit mask, ...) answers the same weighted
    digraph items. The host grades every reply with the one pinned duality
    grader, ignores any acceptance a channel reports for itself, and reports
    per-arm accepts and discordant pairs. It refuses arms with different
    checkers or budgets and any channel whose self-reported accept set differs.
    """
    spec = spec_from('WF35', 'Proposal-channel comparison', 6, ['WF6', 'WF12'], None,
                     'channel_blind_fixed_oracle', 'wf35_proposal_channel_comparison')

    def validate(self, task):
        require(isinstance(task.get('items'), list) and task['items'], 'items required')
        require(isinstance(task.get('arms'), list) and len(task['arms']) >= 2, 'at least two arms')
        require(all(isinstance(a, Mapping) and isinstance(a.get('channel'), str) for a in task['arms']), 'arm channel')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        arms, items = task['arms'], task['items']
        pin = source_pin(grade_cycle_duality)
        same_checker = all(a.get('checker_pin') == pin for a in arms)
        same_budget = len({digest(a.get('budget')) for a in arms}) == 1
        host.record('arms_share_fixed_checker', same_checker, str([a.get('checker_pin') == pin for a in arms]))
        host.record('arms_share_budget', same_budget, digest([a.get('budget') for a in arms]))
        if not (same_checker and same_budget):
            return refused('ARMS_NOT_MATCHED')
        table: dict[str, list[bool]] = {}
        by_bytes: dict[tuple[int, str], set[str]] = {}
        label_dependent = []
        for arm in arms:
            row = []
            for k, item in enumerate(items):
                reply = session.ask(f"{arm['channel']}:{k}", self.prompt({**item, 'channel': arm['channel']}))
                content = reply.content if reply is not None else {}
                raw = content.get('text') if isinstance(content, Mapping) else None
                grade = grade_cycle_duality(item, raw) if isinstance(raw, str) else REFUSED
                ok = grade in (CERTIFIED, TYPED_REFUSAL)
                by_bytes.setdefault((k, raw if isinstance(raw, str) else ''), set()).add(grade)
                if isinstance(content, Mapping) and 'accepted' in content and content['accepted'] is not ok:
                    label_dependent.append(f"{arm['channel']}:{k}")
                row.append(ok)
            table[arm['channel']] = row
        host.record('same_bytes_same_verdict', all(len(g) == 1 for g in by_bytes.values()), str(len(by_bytes)))
        host.record('accept_set_depends_only_on_bytes', not label_dependent, str(label_dependent))
        a, b = (table[x['channel']] for x in arms[:2])
        return judge(host, 'CHANNELS_COMPARED', accepts={c: sum(r) for c, r in table.items()},
                     discordant={'first_only': sum(x and not y for x, y in zip(a, b, strict=True)),
                                 'second_only': sum(y and not x for x, y in zip(a, b, strict=True))})

    def fixtures(self):
        items = [{'n': 3, 'edges': [[0, 1, 2], [1, 2, -1], [0, 2, 3]]},
                 {'n': 3, 'edges': [[0, 1, 1], [1, 2, -3], [2, 0, 1]]}]
        pin = source_pin(grade_cycle_duality)
        budget = {'max_output_tokens': 256, 'cap_microusd': 1}

        def arm(channel, **over):
            return {'channel': channel, 'checker_pin': pin, 'budget': budget, **over}
        replies = [{'text': '{"potential": [0, 2, 1]}'}, {'text': '{"potential": [0, 0, 0]}'},
                   {'text': '{"potential": [0, 2, 1]}', 'accepted': True},
                   {'text': '{"negative_cycle": [0, 1, 2]}', 'accepted': True}]
        claimed = [*replies[:3], {'text': '{"negative_cycle": [0, 2]}', 'accepted': True}]

        def case(arms, reps=replies):
            return {'task': {'statement': 'Answer each weighted digraph item.', 'items': items, 'arms': arms},
                    'replies': reps}
        return {
            'channels_compared_on_one_checker': (case([arm('prompt'), arm('grammar_mask')]), CERTIFIED),
            'arms_used_different_checkers': (case([arm('prompt'), arm('logit_mask', checker_pin='f' * 64)]), REFUSED),
            'arms_used_different_budgets': (case([arm('prompt'), arm('typed_tree', budget={'max_output_tokens': 4096,
                                                                                          'cap_microusd': 1})]),
                                            REFUSED),
            'channel_label_claims_acceptance': (case([arm('prompt'), arm('grammar_mask')], claimed), REFUSED),
        }
