"""Layer 5 families: arm controls, staged guards, authority and gate audits, commit-reveal."""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from fractions import Fraction
from itertools import product
from typing import Any

from ..fidelity import HostOracleContext
from .base import (
    AUTHORITY_NONE,
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
from .exact import Graph, classify_linear, commitment, matvec, mutation_score, rank
from .registry import register


def _ints(values: Any, name: str) -> list[int]:
    require(isinstance(values, list), f'{name} must be a list')
    return [as_int(v, name) for v in values]


def _reply(session: Session, stage: str, prompt: str) -> Mapping[str, Any] | None:
    """One model turn; the content must be an object."""
    reply = session.ask(stage, prompt)
    if reply is None:
        return None
    require(isinstance(reply.content, Mapping), f'{stage} reply must be an object')
    return reply.content


def cycle_matrix(g: Graph) -> list[list[int]]:
    """Signed fundamental-cycle matrix S (one row per chord); ``S c = 0`` iff ``c`` is exact."""
    rows = []
    for cyc in g.fundamental_cycles():
        row = [0] * len(g.edges)
        for i, sign in cyc:
            row[i] += sign
        rows.append(row)
    return rows


def _potential(g: Graph, values: Any, name: str = 'potential') -> dict[Any, int]:
    """Vertex potential given as a list indexed by the integer vertex labels 0..n-1."""
    phi = _ints(values, name)
    require(sorted(g.vertices) == list(range(len(phi))), f'{name} needs one integer per vertex 0..n-1')
    return dict(enumerate(phi))


# ---------------------------------------------------------------- WF12

ARMS = ('baseline', 'mechanism', 'null_control', 'random_control')
ARM_PAIRS = (('baseline', 'mechanism'), ('null_control', 'mechanism'), ('random_control', 'mechanism'),
             ('baseline', 'null_control'))


@register
class MechanismControlArms(WorkflowFamily):
    """WF12. Run a mechanism arm against matched null and random controls on the same items.

    Items are integer sums graded by one host checker. The paired effect is
    ``d_i = 1[check(B, i)] - 1[check(A, i)]``; the proposer's arm ranks are a
    potential on the arm-comparison graph, accepted iff its coboundary equals
    every paired total, which is invariant under ``r -> r + c``. Controls must be
    matched first: a zero null vector and a random vector with the mechanism's
    exact squared norm.
    """
    spec = spec_from('WF12', 'Mechanism-control arms', 5, ['WF6', 'WF3'], 'Sweep',
                     'integer_rank_difference_certificate', 'wf12_mechanism_control_arms')

    def validate(self, task):
        require(isinstance(task.get('items'), list) and task['items'], 'items required')
        for key in ('mechanism_vector', 'null_control_vector', 'random_control_vector'):
            _ints(task.get(key), key)
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        mech, null, rnd = (task[k] for k in ('mechanism_vector', 'null_control_vector', 'random_control_vector'))
        norms = {'mechanism': sum(x * x for x in mech), 'random_control': sum(x * x for x in rnd)}
        host.record('null_control_is_zero', len(null) == len(mech) and not any(null), str(null))
        host.record('random_norm_matches_mechanism', len(rnd) == len(mech) and norms['random_control']
                    == norms['mechanism'], str(norms))
        host.record('random_differs_from_mechanism', rnd != mech, str(rnd))
        if host.failed:
            return refused('CONTROLS_UNMATCHED', failed=host.failed, squared_norms=norms)
        truth = [sum(_ints(item['values'], 'values')) for item in task['items']]
        passes: dict[str, list[int]] = {}
        for arm in ARMS:
            content = _reply(session, f'arm:{arm}', self.prompt(task) + f'\nArm: {arm}')
            if content is None:
                return refused('NO_ADMISSIBLE_REPLY', arm=arm)
            answers = _ints(content.get('answers'), 'answers')
            require(len(answers) == len(truth), 'every arm must answer the same items')
            passes[arm] = [int(a == t) for a, t in zip(answers, truth, strict=True)]
        paired = {f'{a}->{b}': [pb - pa for pa, pb in zip(passes[a], passes[b], strict=True)] for a, b in ARM_PAIRS}
        totals = [sum(d) for d in paired.values()]
        cert = _reply(session, 'certificate', self.prompt(task) + '\nReport integer arm ranks.')
        if cert is None:
            return refused('NO_ADMISSIBLE_REPLY', arm='certificate')
        require(isinstance(cert.get('ranks'), Mapping) and set(cert['ranks']) == set(ARMS), 'one rank per arm')
        ranks = {a: as_int(cert['ranks'][a], 'rank') for a in ARMS}
        residual = Graph.of(ARM_PAIRS).residual(totals, ranks)
        host.record('rank_differences_match_paired_totals', not any(residual), canonical(residual).decode())
        gauge_fixed = {a: ranks[a] - ranks['baseline'] for a in ARMS}
        return judge(host, 'ARMS_COMPARED', paired_totals=dict(zip(paired, totals, strict=True)),
                     gauge_fixed_ranks=gauge_fixed, residual=residual)

    def fixtures(self):
        task = {'statement': 'Sum each item. The arm note is the only thing that changes.',
                'items': [{'id': k, 'values': v} for k, v in enumerate([[1, 2], [3, 4], [5, 5], [2, 7]])],
                'mechanism_vector': [3, 4, 0], 'null_control_vector': [0, 0, 0], 'random_control_vector': [0, 0, 5]}
        arms = [{'answers': [3, 7, 0, 0]}, {'answers': [3, 7, 10, 9]}, {'answers': [3, 0, 0, 0]},
                {'answers': [3, 7, 10, 0]}]
        shifted = {'ranks': {'baseline': 12, 'mechanism': 14, 'null_control': 11, 'random_control': 13}}
        inflated = {'ranks': {'baseline': 2, 'mechanism': 6, 'null_control': 1, 'random_control': 3}}
        unmatched = {**task, 'random_control_vector': [1, 1, 1]}
        return {
            'gauge_shifted_ranks_certified': ({'task': task, 'replies': [*arms, shifted]}, 'HOST_CERTIFIED'),
            'inflated_mechanism_effect': ({'task': task, 'replies': [*arms, inflated]}, 'REFUSED'),
            'random_control_norm_differs': ({'task': unmatched, 'replies': [*arms, shifted]}, 'REFUSED'),
            'arm_on_different_items': ({'task': task, 'replies': [arms[0], {'answers': [3, 7, 10]}, *arms[2:],
                                                                  shifted]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF36

@register
class GuardedStagedSlotMaterialisation(WorkflowFamily):
    """WF36. Stage 1 fills typed cochain slots; a complete guard with one retry gates stage 2.

    Edge values on a graph are partly fixed, partly slots. The syndrome
    ``r = S c`` over the full cycle matrix is the single object used for the
    verdict, the retry prompt and the audit. Stage 2 must give a potential with
    ``delta phi = c``. Abstention is accepted only when the rank test shows no
    filling exists; a guard over a strict subset of cycles is refused with a
    false-green kernel witness.
    """
    spec = spec_from('WF36', 'Guarded staged slot materialisation', 5, ['WF8'], 'WF8', 'exact_cochain_check',
                     'wf36_guarded_staged_slot_materialisation')

    def validate(self, task):
        require(isinstance(task.get('edges'), list) and isinstance(task.get('values'), list), 'edges, values')
        require(len(task['edges']) == len(task['values']), 'one value or null slot per edge')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        g = Graph.of(task['edges'])
        s = cycle_matrix(g)
        guard = _ints(task.get('guard_rows', list(range(len(s)))), 'guard_rows')
        require(all(0 <= k < len(s) for k in guard), 'guard row out of range')
        if not host.record('guard_complete', rank([s[k] for k in guard]) == rank(s), str(sorted(set(guard)))):
            k = min(set(range(len(s))) - set(guard))
            w = [0] * len(g.edges)
            w[g.spanning_forest()[1][k]] = 1
            return refused('PARTIAL_GUARD', kernel_witness=w, guard_syndrome=matvec([s[j] for j in guard], w),
                           full_syndrome=matvec(s, w))
        slots = [i for i, v in enumerate(task['values']) if v is None]
        fixed = [0 if v is None else as_int(v, 'value') for v in task['values']]
        a = [[row[i] for i in slots] for row in s]
        aug = [[*ra, -sum(x * y for x, y in zip(row, fixed, strict=True))] for ra, row in zip(a, s, strict=True)]
        ranks = {'rank_S_slots': rank(a), 'rank_augmented': rank(aug)}
        fillable = ranks['rank_S_slots'] == ranks['rank_augmented']
        prompt, syndromes = self.prompt(task), []
        for attempt in range(2):
            content = _reply(session, f'stage1:{attempt}', prompt)
            if content is None:
                break
            if content.get('abstain') is True:
                if not host.record('abstention_matches_rank_test', not fillable, str(ranks)):
                    return refused('FALSE_ABSTENTION', **ranks)
                return typed_refusal('ABSTAIN_NOT_MATERIALISABLE', **ranks)
            filled = content.get('slots')
            require(isinstance(filled, Mapping) and set(filled) == {str(i) for i in slots}, 'one slot per null edge')
            c = [as_int(filled[str(i)], 'slot') if i in slots else fixed[i] for i in range(len(fixed))]
            syndromes.append(matvec(s, c))
            if not any(syndromes[-1]):
                break
            prompt = self.prompt(task) + '\nGuard syndrome: ' + canonical(syndromes[-1]).decode()
        if not host.record('guard_green_within_one_retry', bool(syndromes) and not any(syndromes[-1]),
                           canonical(syndromes).decode()):
            return refused('GUARD_RED_AFTER_RETRY', syndromes=syndromes)
        stage2 = _reply(session, 'stage2', self.prompt(task) + '\nSlots: ' + canonical(c).decode())
        if stage2 is None:
            return refused('NO_ADMISSIBLE_REPLY', stage='stage2')
        residual = g.residual(c, _potential(g, stage2.get('potential')))
        host.record('stage2_potential_explains_slots', not any(residual), canonical(residual).decode())
        return judge(host, 'MATERIALISED' if len(syndromes) == 1 else 'MATERIALISED_AFTER_RETRY',
                     syndromes=syndromes, residual=residual)

    def fixtures(self):
        base = {'statement': 'Fill the null edge slots so every cycle sums to zero, then give a potential.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'values': [1, 2, None, 1, None]}
        blocked = {**base, 'values': [1, 2, 0, None, None]}
        partial = {**base, 'guard_rows': [0]}
        good, near = {'slots': {'2': -3, '4': -4}}, {'slots': {'2': -3, '4': -3}}
        phi = {'potential': [0, 1, 3, 4]}
        return {
            'materialised_first_try': ({'task': base, 'replies': [good, phi]}, 'HOST_CERTIFIED'),
            'repaired_from_shared_syndrome': ({'task': base, 'replies': [near, good, phi]}, 'HOST_CERTIFIED'),
            'abstain_on_closed_nonexact_cycle': ({'task': blocked, 'replies': [{'abstain': True}]}, 'TYPED_REFUSAL'),
            'partial_guard_false_green': ({'task': partial, 'replies': [near, phi]}, 'REFUSED'),
            'lazy_false_abstention': ({'task': base, 'replies': [{'abstain': True}]}, 'REFUSED'),
            'guard_red_after_retry': ({'task': base, 'replies': [near, near, phi]}, 'REFUSED'),
            'stage2_drifts_from_slots': ({'task': base, 'replies': [good, {'potential': [0, 1, 3, 5]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF39

def _replay_cochain_residual(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Registered verifier: residual of the payload's cochain against its potential."""
    g = Graph.of(payload['edges'])
    r = g.residual(_ints(payload['c'], 'c'), _potential(g, payload['phi'], 'phi'))
    return {'residual': r, 'defect': sum(abs(x) for x in r)}


VERIFIERS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    'exact.cochain_residual.v1': _replay_cochain_residual}
RECEIPT_FIELDS = frozenset({'authority_effect', 'verifier_id', 'payload_sha256', 'replay_sha256', 'claimed', 'nonce'})


@register
class AuthorityFirewallGate(WorkflowFamily):
    """WF39. Accept a reply only when every guard in the vector passes.

    The reply is a payload (cochain plus potential) and a receipt. The host
    replays the registered verifier and checks: authority effect 'None' with no
    extra fields, verifier registered, witness bound to the exact payload hash,
    replay hash, replay match, zero defect and a fresh nonce. A failed guard
    becomes residual evidence; self-certifying or escalating receipts are refused.
    """
    spec = spec_from('WF39', 'Authority firewall gate', 5, ['WF1', 'WF23'], None, 'authority_guard_vector',
                     'wf39_authority_firewall_gate')

    def validate(self, task):
        require(isinstance(task.get('nonce'), str) and isinstance(task.get('registered_verifiers'), list), 'nonce')
        return task

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and isinstance(content.get('payload'), Mapping)
                and isinstance(content.get('receipt'), Mapping), 'payload and receipt objects required')
        payload, receipt = content['payload'], content['receipt']
        extra = sorted(set(receipt) - RECEIPT_FIELDS)
        if not host.record('authority_effect_none', receipt.get('authority_effect') == AUTHORITY_NONE and not extra,
                           canonical({'effect': receipt.get('authority_effect'), 'extra': extra}).decode()):
            return refused('AUTHORITY_ESCALATION', escalating_fields=extra, residual_evidence=['authority'])
        vid = receipt.get('verifier_id')
        registered = vid in task['registered_verifiers'] and vid in VERIFIERS
        host.record('witness_verifier_registered', registered, str(vid))
        host.record('witness_bound_to_payload', receipt.get('payload_sha256') == digest(payload), str(vid))
        replay = VERIFIERS[vid](payload) if registered else None
        host.record('replay_hash', replay is not None and receipt.get('replay_sha256') == digest(replay), str(vid))
        host.record('replay_match', replay is not None and receipt.get('claimed') == replay, str(replay))
        host.record('zero_defect', replay is not None and replay['defect'] == 0, str(replay))
        host.record('fresh_nonce', receipt.get('nonce') == task['nonce'], str(receipt.get('nonce')))
        return judge(host, 'ALL_GUARDS_PASS', residual_evidence=host.failed)

    def fixtures(self):
        task = {'statement': 'Return the payload and a receipt from the registered verifier.', 'nonce': 'run-0042',
                'registered_verifiers': ['exact.cochain_residual.v1']}
        good = {'edges': [[0, 1], [1, 2], [2, 0]], 'c': [1, 1, -2], 'phi': [0, 1, 2]}
        bad = {**good, 'c': [1, 1, -1]}

        def packet(payload, bound=None, **over):
            replay = _replay_cochain_residual(payload)
            receipt = {'authority_effect': 'None', 'verifier_id': 'exact.cochain_residual.v1',
                       'payload_sha256': digest(bound or payload), 'replay_sha256': digest(replay),
                       'claimed': replay, 'nonce': 'run-0042', **over}
            return {'task': task, 'replies': [{'payload': payload, 'receipt': receipt}]}
        return {
            'all_guards_pass': (packet(good), 'HOST_CERTIFIED'),
            'self_certifying_receipt': (packet(good, verifier_id='self', verdict='HOST_CERTIFIED'), 'REFUSED'),
            'authority_escalation': (packet(good, authority_effect='Host'), 'REFUSED'),
            'stale_nonce': (packet(good, nonce='run-0041'), 'REFUSED'),
            'truthful_nonzero_defect': (packet(bad), 'REFUSED'),
            'witness_bound_to_other_payload': (packet(bad, bound=good, claimed={'residual': [0, 0, 0], 'defect': 0}),
                                               'REFUSED'),
        }


# ---------------------------------------------------------------- WF42

STEP = re.compile(r'^\s*(?:\w+:\s*)?([a-z]\w*)\s*-\s*([a-z]\w*)\s*=\s*(-?\d+)\s*$')


def extract_claim(line: Any) -> tuple[str, str, int]:
    """Fixed extractor: 'u - v = k' becomes the oriented edge (v, u) with value k."""
    require(isinstance(line, str), 'trace steps must be strings')
    m = STEP.match(line)
    require(m is not None, f'extractor cannot parse step {line!r}')
    return m.group(2), m.group(1), int(m.group(3))


def max_dual_circulation(g: Graph, c: Sequence[int]) -> tuple[int, list[int]]:
    """``Phi = max z . c`` over circulations ``B^T z = 0`` with ``|z_e| <= 1``.

    The incidence matrix is totally unimodular, so the LP optimum is attained at
    a {-1, 0, 1} vertex and this enumeration is exact; it equals the minimum l1
    correction making ``c`` a coboundary.
    """
    require(len(g.edges) <= 8, 'trace graphs are limited to 8 claims')
    best, arg = 0, [0] * len(g.edges)
    for z in product((-1, 0, 1), repeat=len(g.edges)):
        flow = dict.fromkeys(g.vertices, 0)
        for (u, v), ze in zip(g.edges, z, strict=True):
            flow[u] -= ze
            flow[v] += ze
        value = sum(ze * ce for ze, ce in zip(z, c, strict=True))
        if not any(flow.values()) and value > best:
            best, arg = value, list(z)
    return best, arg


@register
class ReasoningTraceValidation(WorkflowFamily):
    """WF42. Extract a claim graph from a trace and certify it, or certify its obstruction.

    Each step 'u - v = k' is an edge cochain value. The host computes the
    obstruction ``Phi`` and a dual circulation. A consistent trace needs a
    potential explaining every step and a conclusion the steps force; an
    obstructed trace needs a correction with ``||r||_1 = Phi`` (primal = dual).
    Hidden obstructions and conclusions that contradict the steps are refused.
    """
    spec = spec_from('WF42', 'Reasoning-trace validation', 5, ['WF10', 'WF21'], None,
                     'rational_lp_primal_dual_check', 'wf42_reasoning_trace_validation')

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and isinstance(content.get('trace'), list), 'trace list required')
        require(content.get('status') in ('CONSISTENT', 'OBSTRUCTED'), 'status must be CONSISTENT or OBSTRUCTED')
        claims = [extract_claim(s) for s in content['trace']]
        g = Graph.of([(v, u) for v, u, _k in claims])
        c = [k for _v, _u, k in claims]
        phi_value, dual = max_dual_circulation(g, c)
        witness = {'Phi': phi_value, 'dual': dual}
        if not host.record('status_matches_obstruction', (content['status'] == 'OBSTRUCTED') == (phi_value > 0),
                           str(witness)):
            return refused('HIDDEN_OBSTRUCTION' if phi_value else 'FALSE_OBSTRUCTION', **witness)
        if phi_value:
            r = _ints(content.get('correction'), 'correction')
            require(len(r) == len(c), 'one correction per step')
            host.record('correction_closes_cycles', g.is_exact([x - y for x, y in zip(c, r, strict=True)]), str(r))
            host.record('primal_equals_dual', sum(abs(x) for x in r) == phi_value, str(witness))
            return typed_refusal('TRACE_OBSTRUCTED', **witness) if not host.failed else judge(host, **witness)
        require(isinstance(content.get('potential'), Mapping), 'potential object required')
        phi = {v: as_int(content['potential'].get(v), 'potential') for v in g.vertices}
        host.record('potential_explains_steps', not any(g.residual(c, phi)), str(phi))
        v, u, k = extract_claim(content.get('conclusion'))
        joined = Graph.of([*g.edges, (v, u)])
        forced = u in phi and v in phi and joined.cycle_rank == g.cycle_rank + 1
        host.record('conclusion_forced_by_steps', forced, str((u, v)))
        host.record('conclusion_matches_steps', forced and phi[u] - phi[v] == k, str((u, v, k)))
        return judge(host, 'TRACE_VALID', **witness)

    def fixtures(self):
        task = {'statement': "Reason in steps of the form 'u - v = k', then state the conclusion."}
        chain = ['s1: b - a = 1', 's2: c - b = 1']
        cycle = ['s1: b - a = 1', 's2: c - b = 0', 's3: a - c = 0']
        pot = {'a': 0, 'b': 1, 'c': 2}

        def case(reply):
            return {'task': task, 'replies': [reply]}
        return {
            'consistent_trace': (case({'trace': chain, 'status': 'CONSISTENT', 'potential': pot,
                                       'conclusion': 'c - a = 2'}), 'HOST_CERTIFIED'),
            'three_claim_cycle_obstructed': (case({'trace': cycle, 'status': 'OBSTRUCTED', 'correction': [1, 0, 0]}),
                                             'TYPED_REFUSAL'),
            'conclusion_contradicts_steps': (case({'trace': chain, 'status': 'CONSISTENT', 'potential': pot,
                                                   'conclusion': 'c - a = 3'}), 'REFUSED'),
            'hidden_obstruction': (case({'trace': cycle, 'status': 'CONSISTENT', 'potential': pot,
                                         'conclusion': 'c - a = 1'}), 'REFUSED'),
            'non_minimal_correction': (case({'trace': cycle, 'status': 'OBSTRUCTED', 'correction': [2, -1, 0]}),
                                       'REFUSED'),
            'unextractable_step': (case({'trace': ['b exceeds a by one'], 'status': 'CONSISTENT'}), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF43

def _solves(a: Any, b: Any, x: Any) -> bool:
    rows = [[as_fraction(v, 'A') for v in row] for row in a]
    xs = [as_fraction(v, 'answer') for v in x]
    return matvec(rows, xs) == [as_fraction(v, 'b') for v in b]


GATE_OPS: dict[str, Callable[..., bool]] = {
    'solves_task': lambda task, reply: _solves(task['A'], task['b'], reply['answer']),
    'solves_own': lambda task, reply: _solves(reply['A'], reply['b'], reply['answer']),
    'has_field': lambda task, reply, f: f in reply,
    'field_equals': lambda task, reply, f, value: reply.get(f) == value,
    'keyword': lambda task, reply, f, word: word in str(reply.get(f, '')),
}


def gate_accepts(gate: Mapping[str, Any], task: Mapping[str, Any], reply: Mapping[str, Any]) -> tuple[bool, list]:
    """Interpret the gate DSL; returns (verdict, the checks that passed). A crashing check fails."""
    passed = []
    for op, *args in gate['checks']:
        try:
            ok = GATE_OPS[op](task, reply, *args) is True
        except Exception:  # noqa: BLE001  (a check that cannot evaluate rejects)
            ok = False
        if ok:
            passed.append(op)
    return (len(passed) == len(gate['checks']) if gate['mode'] == 'all' else bool(passed)), passed


@register
class GateHonestyAudit(WorkflowFamily):
    """WF43. Replay answer-free probes against a proposed gate and refuse a gate that lets one pass.

    The proposer writes a gate in a small check language for the task
    ``A x = b``. The host replays an empty object, constant verdicts and
    refusals, a templated receipt, keyword bait, a wrong answer and an input
    replacement. Honest means no probe passes and the true solution does; every
    probe verdict is traced to the checks that produced it.
    """
    spec = spec_from('WF43', 'Gate-honesty and answer-free leak audit', 5, ['WF23'], None,
                     'answer_free_probe_replay', 'wf43_gate_honesty_and_answer_free_leak_audit')

    def validate(self, task):
        require(isinstance(task.get('A'), list) and isinstance(task.get('b'), list), 'A and b required')
        return task

    @staticmethod
    def solution(task: Mapping[str, Any]) -> list[Fraction]:
        a = [[as_fraction(v, 'A') for v in row] for row in task['A']]
        status = classify_linear(a, [as_fraction(v, 'b') for v in task['b']])
        require(status.status == 'unique', 'the audited task must have a unique solution')
        return list(status.solution)

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and isinstance(content.get('gate'), Mapping), 'gate object required')
        gate = content['gate']
        require(gate.get('mode') in ('all', 'any') and isinstance(gate.get('checks'), list) and gate['checks'],
                'gate needs mode all|any and a non-empty check list')
        require(all(isinstance(ch, list) and ch and ch[0] in GATE_OPS for ch in gate['checks']), 'unknown check')
        x = self.solution(task)
        valid = {'answer': [f'{v.numerator}/{v.denominator}' for v in x]}
        probes = {
            'empty_object': {},
            'constant_verdict': {'verdict': 'HOST_CERTIFIED', 'status': 'solved'},
            'constant_refusal': {'refusal': 'UNRESOLVED_INCONSISTENT'},
            'templated_receipt': {'receipt': {'checker': 'exact', 'sha256': '0' * 64}, 'status': 'solved'},
            'keyword_bait': {'status': 'solved', 'note': 'verified correct answer'},
            'wrong_answer': {'answer': [f'{v + 1}' for v in x]},
            'input_replacement': {'A': [[1]], 'b': [1], 'answer': [1]},
        }
        trace = {name: gate_accepts(gate, task, p) for name, p in probes.items()}
        leaked = {name: ops for name, (ok, ops) in trace.items() if ok}
        host.record('no_answer_free_reply_passes', not leaked, canonical(leaked).decode())
        host.record('accepts_true_solution', gate_accepts(gate, task, valid)[0], str(gate['checks']))
        return judge(host, 'GATE_HONEST', leaked=leaked, probes=len(probes))

    def fixtures(self):
        task = {'statement': 'Write a gate that accepts a reply only if it solves A x = b.',
                'A': [[1, 1], [1, -1]], 'b': [3, 1]}

        def gate(mode, *checks):
            return {'task': task, 'replies': [{'gate': {'mode': mode, 'checks': [list(ch) for ch in checks]}}]}
        return {
            'honest_gate': (gate('all', ['has_field', 'answer'], ['solves_task']), 'HOST_CERTIFIED'),
            'keyword_adjudication': (gate('all', ['keyword', 'status', 'solved']), 'REFUSED'),
            'receipt_or_answer': (gate('any', ['solves_task'], ['has_field', 'receipt']), 'REFUSED'),
            'input_replacement_gate': (gate('all', ['solves_own']), 'REFUSED'),
            'constant_reject_gate': (gate('all', ['field_equals', 'status', 'never']), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF48

def _check_residual(g: Graph, c: list[int], phi: Any) -> bool:
    return not any(g.residual(c, _potential(g, phi)))


def _check_tree_integration(g: Graph, c: list[int], phi: Any) -> bool:
    """Independent checker: every cycle sums to zero and phi agrees with the tree integral up to gauge."""
    p = _potential(g, phi)
    pot = g.potential(c)
    if any(g.cycle_sum(c, cyc) for cyc in g.fundamental_cycles()):
        return False
    return all(p[v] - p[0] == pot[v] - pot[0] for v in g.vertices)


def _check_length_only(g: Graph, c: list[int], phi: Any) -> bool:  # noqa: ARG001  (deliberately weak)
    return isinstance(phi, list) and len(phi) == len(g.vertices)


CHECKERS = {'residual.v1': _check_residual, 'tree_integration.v1': _check_tree_integration,
            'length_only.v1': _check_length_only}


def potential_mutants(phi: list[int]) -> list[list[int]]:
    """Hostile edits: bump each entry by +-1, swap unequal neighbours, truncate."""
    out = [[*phi[:i], phi[i] + d, *phi[i + 1:]] for i in range(len(phi)) for d in (1, -1)]
    out += [[*phi[:i], phi[i + 1], phi[i], *phi[i + 2:]] for i in range(len(phi) - 1) if phi[i] != phi[i + 1]]
    return [*out, phi[:-1]]


@register
class CommitRevealMutationGate(WorkflowFamily):
    """WF48. Commit an artifact before reveal, then require two checkers to kill every mutant.

    The judge manifest names two registered checkers and is committed with a
    sealed salt. The proposer commits ``H(salt || potential)`` for a public
    cochain, then reveals. The host checks the commitment, both checkers accept
    the artifact and its gauge shift, and both reject every hostile mutant. A
    changed artifact after commit, or a surviving mutant, is refused.
    """
    spec = spec_from('WF48', 'Commit-reveal with a hostile mutation gate', 5, ['WF11', 'WF23'], 'WF23',
                     'dual_checker_mutation_suite', 'wf48_commit_reveal_with_a_hostile_mutation_gate')

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task, sealed = session.task, session.sealed
        ids = task['judge_manifest']['checkers']
        host.record('manifest_commitment_matches', commitment(sealed.get('manifest_salt', ''), task['judge_manifest'])
                    == task['manifest_commitment'], str(ids))
        host.record('two_independent_registered_checkers', len(set(ids)) == 2 == len(ids)
                    and all(i in CHECKERS for i in ids), str(ids))
        if host.failed:
            return judge(host)
        committed = _reply(session, 'commit', self.prompt(task) + '\nCommit H(salt || potential) only.')
        if committed is None:
            return refused('NO_ADMISSIBLE_REPLY', stage='commit')
        h = committed.get('commitment')
        require(isinstance(h, str), 'commitment must be a hex string')
        revealed = _reply(session, 'reveal', self.prompt(task) + '\nCommitment recorded: ' + h + '\nReveal now.')
        if revealed is None:
            return refused('NO_ADMISSIBLE_REPLY', stage='reveal')
        salt, phi = revealed.get('salt'), _ints(revealed.get('artifact'), 'artifact')
        require(isinstance(salt, str), 'salt must be a string')
        if not host.record('reveal_matches_commitment', commitment(salt, phi) == h, h):
            return refused('ARTIFACT_CHANGED_AFTER_COMMIT')
        g, c = Graph.of(task['edges']), _ints(task['c'], 'c')
        mutants = potential_mutants(phi)
        kills = {}
        for cid in ids:
            score = mutation_score(lambda x, f=CHECKERS[cid]: f(g, c, x), [phi, [v + 3 for v in phi]], mutants)
            kills[cid] = f'{score.killed}/{score.mutants_total}'
            host.record(f'{cid}:accepts_artifact_and_gauge', score.sound, kills[cid])
            host.record(f'{cid}:kills_every_mutant', score.killed == score.mutants_total, kills[cid])
        return judge(host, 'COMMIT_REVEAL_CERTIFIED', kills=kills)

    def fixtures(self):
        manifest = {'checkers': ['residual.v1', 'tree_integration.v1']}
        weak = {'checkers': ['residual.v1', 'length_only.v1']}
        task = {'statement': 'Commit to a potential phi with delta phi = c, then reveal it.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3]], 'c': [1, 2, -3, 1], 'judge_manifest': manifest,
                'manifest_commitment': commitment('judge-salt-17', manifest)}
        weak_task = {**task, 'judge_manifest': weak, 'manifest_commitment': commitment('judge-salt-17', weak)}
        sealed = {'manifest_salt': 'judge-salt-17'}
        phi, other = [0, 1, 3, 4], [0, 1, 3, 5]

        def case(t, committed, revealed):
            return {'task': t, 'sealed': sealed, 'replies': [{'commitment': commitment('s4lt', committed)},
                                                            {'salt': 's4lt', 'artifact': revealed}]}
        return {
            'committed_and_both_checkers_kill': (case(task, phi, phi), 'HOST_CERTIFIED'),
            'artifact_changed_after_commit': (case(task, other, phi), 'REFUSED'),
            'weak_checker_lets_mutant_survive': (case(weak_task, phi, phi), 'REFUSED'),
            'committed_wrong_artifact': (case(task, other, other), 'REFUSED'),
            'manifest_swapped_after_commit': ({**case(task, phi, phi), 'task': {**task, 'judge_manifest': weak}},
                                              'REFUSED'),
        }
