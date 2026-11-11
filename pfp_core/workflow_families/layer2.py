"""Layer 2 families: built on WF1, WF2 and WF7."""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Any

from ..fidelity import HostOracleContext
from .base import (
    POSITIVE,
    MalformedCandidateError,
    Session,
    Verdict,
    WorkflowFamily,
    as_fraction,
    as_int,
    canonical,
    certified,
    digest,
    judge,
    refused,
    require,
    spec_from,
    typed_refusal,
)
from .exact import Graph, matmul
from .layer1 import REFUSAL_CODES, TypedRefusal
from .registry import register


@dataclass(frozen=True)
class Assessment:
    """One host assessment inside a repair loop. ``residual`` must never contain the answer."""
    accepted: bool
    residual: Mapping[str, Any]
    measure: Any = 0  # host defect size, e.g. Phi1; lower is better


@register
class BoundedCheckAndRepair(WorkflowFamily):
    """WF9. Check, return only the typed residual, allow at most L repairs.

    Domain: XOR labels ``c`` on the edges of a graph. A consistent 0/1 vertex
    labelling exists iff every cycle sum of ``c`` is 0 mod 2. The candidate
    returns a set of edges to flip; the host accepts iff ``c + Delta`` is a
    coboundary mod 2 and ``|Delta|`` is minimal. On rejection the next prompt
    carries only the indices of the fundamental cycles that are still odd.

    Subclasses reuse the loop by overriding ``assess`` and ``repair_prompt``.
    """
    spec = spec_from('WF9', 'Bounded check-and-repair', 2, ['WF2'], None, 'xor_cycle_minimal_repair',
                     'wf09_bounded_check_and_repair')

    def max_attempts(self, task: Mapping[str, Any]) -> int:
        limit = as_int(task.get('max_attempts', 3), 'max_attempts')
        require(1 <= limit <= 8, 'max_attempts must be in 1..8')
        return limit

    def validate(self, task):
        require(isinstance(task.get('edges'), list) and isinstance(task.get('labels'), list), 'edges, labels')
        require(len(task['edges']) == len(task['labels']), 'one label per edge')
        self.max_attempts(task)
        return task

    def assess(self, task, sealed, content) -> Assessment:
        g = Graph.of(task['edges'])
        require(isinstance(content, Mapping) and isinstance(content.get('flip'), list), 'flip list required')
        flips = {as_int(i, 'flip') for i in content['flip']}
        require(all(0 <= i < len(g.edges) for i in flips), 'flip index out of range')
        c = [(int(x) + (1 if i in flips else 0)) % 2 for i, x in enumerate(task['labels'])]
        odd = [k for k, cyc in enumerate(g.fundamental_cycles()) if g.cycle_sum(c, cyc, 2)]
        minimal = minimal_xor_repair(g, [int(x) % 2 for x in task['labels']])
        accepted = not odd and len(flips) == minimal
        residual = {'odd_cycles': odd, 'flip_count': len(flips), 'minimal_known': not odd}
        return Assessment(accepted, residual, len(odd))

    def repair_prompt(self, task, residual: Mapping[str, Any]) -> str:
        return self.prompt(task) + '\nHost residual: ' + canonical(dict(residual)).decode('utf-8')

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        prompt = self.prompt(task)
        trail = []
        for attempt in range(self.max_attempts(task)):
            reply = session.ask(f'attempt:{attempt}', prompt)
            if reply is None:
                break
            try:
                result = self.assess(task, session.sealed, reply.content)
            except MalformedCandidateError as exc:
                result = Assessment(False, {'malformed': str(exc)}, None)
            trail.append({'attempt': attempt, 'measure': result.measure, 'residual': dict(result.residual)})
            if result.accepted:
                host.record('accepted_within_limit', True, canonical(trail).decode('utf-8'))
                return certified('REPAIRED' if attempt else 'ACCEPTED_FIRST_TRY', attempts=attempt + 1, trail=trail)
            prompt = self.repair_prompt(task, result.residual)
        host.record('accepted_within_limit', False, canonical(trail).decode('utf-8'))
        return refused('REPAIR_LIMIT_EXHAUSTED', attempts=len(trail), trail=trail)

    def fixtures(self):
        task = {'statement': 'Flip the fewest edge labels so every cycle has an even label sum.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'labels': [1, 0, 0, 0, 0], 'max_attempts': 3}
        return {
            'repaired_on_second_try': ({'task': task, 'replies': [{'flip': [2]}, {'flip': [0]}]}, 'HOST_CERTIFIED'),
            'non_minimal_never_accepted': ({'task': task, 'replies': [{'flip': [0, 3, 4]}] * 3}, 'REFUSED'),
            'limit_exhausted': ({'task': task, 'replies': [{'flip': [3]}, {'flip': [4]}, {'flip': [3, 4]}]},
                                'REFUSED'),
        }


def minimal_xor_repair(g: Graph, labels: list[int]) -> int:
    """Smallest number of flips making ``labels`` a coboundary mod 2 (brute force; small graphs only)."""
    m = len(g.edges)
    require(m <= 20, 'brute-force repair is limited to 20 edges')
    cycles = g.fundamental_cycles()
    for k in range(m + 1):
        for flips in combinations(range(m), k):
            c = [(x + (1 if i in flips else 0)) % 2 for i, x in enumerate(labels)]
            if not any(g.cycle_sum(c, cyc, 2) for cyc in cycles):
                return k
    return m


# Exact-domain helpers shared by WF13, WF24 and WF32.

def as_perm(value: Any, n: int, name: str) -> tuple[int, ...]:
    """A permutation of ``range(n)`` in one-line notation."""
    require(isinstance(value, list), f'{name} must be a list')
    p = tuple(as_int(x, name) for x in value)
    require(sorted(p) == list(range(n)), f'{name} must permute 0..{n - 1}')
    return p


def pmul(p: tuple[int, ...], q: tuple[int, ...]) -> tuple[int, ...]:
    """Apply ``p``, then ``q``."""
    return tuple(q[i] for i in p)


def pinv(p: tuple[int, ...]) -> tuple[int, ...]:
    out = [0] * len(p)
    for i, x in enumerate(p):
        out[x] = i
    return tuple(out)


def perm_matrix(p: tuple[int, ...]) -> list[list[int]]:
    """Row ``i`` has its 1 in column ``p[i]``, so ``P_p P_q = P_{pmul(p, q)}``."""
    return [[1 if j == p[i] else 0 for j in range(len(p))] for i in range(len(p))]


_PAULI = {'I': (0, 0), 'X': (1, 0), 'Z': (0, 1), 'Y': (1, 1)}


def symplectic(a: str, b: str) -> int:
    """Symplectic product of two Pauli strings mod 2; 0 iff they commute."""
    return sum(_PAULI[x][0] * _PAULI[y][1] + _PAULI[x][1] * _PAULI[y][0] for x, y in zip(a, b, strict=True)) % 2


def _check_stabilizer(data, answer):
    gens = data.get('generators')
    require(isinstance(gens, list) and gens and all(
        isinstance(g, str) and len(g) == len(gens[0]) and set(g) <= set(_PAULI) for g in gens),
        'generators must be Pauli strings of one length')
    truth = [[i, j] for i, j in combinations(range(len(gens)), 2) if symplectic(gens[i], gens[j])]
    require(isinstance(answer, Mapping) and isinstance(answer.get('anticommuting'), list),
            'anticommuting list required')
    require(all(isinstance(p, list) and len(p) == 2 for p in answer['anticommuting']), 'pairs are [i, j]')
    claimed = sorted(sorted(as_int(x, 'pair') for x in p) for p in answer['anticommuting'])
    return claimed == truth, {'anticommuting': truth}


def _check_anomaly(data, answer):
    require(isinstance(data.get('charges'), list) and data['charges'], 'charges required')
    q = [as_fraction(x, 'charge') for x in data['charges']]
    linear, cubic = sum(q, Fraction(0)), sum((x ** 3 for x in q), Fraction(0))
    require(isinstance(answer, Mapping) and type(answer.get('anomaly_free')) is bool, 'anomaly_free bool required')
    ok = (as_fraction(answer.get('linear'), 'linear') == linear and as_fraction(answer.get('cubic'), 'cubic') == cubic
          and answer['anomaly_free'] == (linear == 0 and cubic == 0))
    return ok, {'linear': str(linear), 'cubic': str(cubic)}


def _check_commutator(data, answer):
    n = as_int(data.get('n'), 'n')
    require(1 <= n <= 8, 'n must be in 1..8')
    g, h = as_perm(data.get('g'), n, 'g'), as_perm(data.get('h'), n, 'h')
    truth = pmul(pmul(pmul(pinv(g), pinv(h)), g), h)
    require(isinstance(answer, Mapping), 'reply must be an object')
    return as_perm(answer.get('commutator'), n, 'commutator') == truth, {'commutator': list(truth)}


def _check_linear_refusal(data, answer):
    """The refusal capsule: WF7's rank test decides between an answer and a typed refusal."""
    family = TypedRefusal()
    family.validate(data)
    verdict = family.check(data, {}, answer, HostOracleContext())
    return verdict.verdict in POSITIVE, {'code': verdict.code, **dict(verdict.detail).get('witness', {})}


Checker = Callable[[Mapping[str, Any], Any], tuple[bool, dict[str, Any]]]
DOMAIN_CHECKERS: dict[str, Checker] = {
    'stabilizer_commutation': _check_stabilizer,
    'u1_anomaly': _check_anomaly,
    'group_commutator': _check_commutator,
    'linear_refusal': _check_linear_refusal,
}


@register
class ExactDomainCapsuleBattery(WorkflowFamily):
    """WF13. Run a battery of exact-domain capsules, each judged by its own registered checker.

    Domains: stabilizer commutation (symplectic product mod 2), U(1) anomaly sums
    (sum q and sum q^3), commutators in S_n, and a WF7 linear capsule that must be
    answered or refused by the rank test. Every domain needs a checker before any
    capsule is dispatched. Results are per domain over the full declared denominator:
    a missing or malformed reply counts as a failure, and no cross-domain average is formed.
    """
    spec = spec_from('WF13', 'Exact-domain capsule battery', 2, ['WF1', 'WF7'], 'WF1',
                     'per_domain_registered_checker', 'wf13_exact_domain_capsule_battery')

    def validate(self, task):
        caps = task.get('capsules')
        require(isinstance(caps, list) and caps, 'capsules required')
        require(all(isinstance(c, Mapping) and isinstance(c.get('data'), Mapping) for c in caps), 'capsules need data')
        ids = [str(c.get('id')) for c in caps]
        require(len(set(ids)) == len(ids), 'capsule ids must be unique')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        caps = session.task['capsules']
        unregistered = sorted({str(c.get('domain')) for c in caps} - set(DOMAIN_CHECKERS))
        if not host.record('checkers_registered_before_dispatch', not unregistered, str(unregistered)):
            return refused('UNREGISTERED_DOMAIN', unregistered=unregistered)
        per_domain: dict[str, dict[str, int]] = {}
        for cap in caps:
            tally = per_domain.setdefault(cap['domain'], {'passed': 0, 'total': 0})
            tally['total'] += 1
            reply = session.ask(f"capsule:{cap['id']}", self.prompt({**cap, 'statement': session.task['statement']}))
            ok, witness = False, {'reply': None}
            if reply is not None:
                try:
                    ok, witness = DOMAIN_CHECKERS[cap['domain']](cap['data'], reply.content)
                except MalformedCandidateError as exc:
                    witness = {'malformed': str(exc)}
            tally['passed'] += int(ok)
            host.record(f"capsule:{cap['id']}", ok, canonical(witness).decode('utf-8'))
        counted = sum(t['total'] for t in per_domain.values())
        host.record('denominator_preserved', counted == len(caps), f'{counted}/{len(caps)}')
        return judge(host, 'BATTERY_PASSED', per_domain=per_domain, denominator=len(caps))

    def fixtures(self):
        caps = [
            {'id': 'stab5', 'domain': 'stabilizer_commutation', 'data': {'generators': ['XZZXI', 'IXZZX', 'XIXZZ',
                                                                                        'ZXIXZ']}},
            {'id': 'stab3', 'domain': 'stabilizer_commutation', 'data': {'generators': ['XXI', 'ZZI', 'IXZ']}},
            {'id': 'anom', 'domain': 'u1_anomaly', 'data': {'charges': [1, 5, -7, -8, 9]}},
            {'id': 'comm', 'domain': 'group_commutator', 'data': {'n': 4, 'g': [1, 0, 2, 3], 'h': [0, 2, 1, 3]}},
            {'id': 'refuse', 'domain': 'linear_refusal', 'data': {'A': [[1, 1], [2, 2]], 'b': [3, 7]}},
        ]
        task = {'statement': 'Answer this capsule exactly, or refuse with a typed code.', 'capsules': caps}
        good = [{'anticommuting': []}, {'anticommuting': [[1, 2]]}, {'linear': 0, 'cubic': 0, 'anomaly_free': True},
                {'commutator': [1, 2, 0, 3]}, {'refusal': 'UNRESOLVED_INCONSISTENT'}]
        regge = {**task, 'capsules': [*caps, {'id': 'regge', 'domain': 'regge_deficit', 'data': {}}]}
        return {
            'every_capsule_passes': ({'task': task, 'replies': good}, 'HOST_CERTIFIED'),
            'dropped_capsule_keeps_denominator': ({'task': task, 'replies': good[:-1]}, 'REFUSED'),
            'bluff_on_refusal_capsule': ({'task': task, 'replies': [*good[:-1], {'answer': [1, 2]}]}, 'REFUSED'),
            'missed_anticommuting_pair': ({'task': task, 'replies': [good[0], {'anticommuting': []}, *good[2:]]},
                                          'REFUSED'),
            'unregistered_domain_not_dispatched': ({'task': regge, 'replies': good}, 'REFUSED'),
        }


_TOKEN = re.compile(r'e\d+[+-]')


@register
class PinnedTokenScratchpad(WorkflowFamily):
    """WF24. Loop holonomy with pinned edge tokens, an exact scratchpad and two agreeing checkers.

    Domain: an S_n gauge field on edges; token ``eK+`` is U(eK) and ``eK-`` its inverse.
    The reply echoes the pinned loop tokens, lists every partial product
    g_k = g_(k-1) * U(token_k), and gives the holonomy and whether it is the identity.
    The host folds the loop twice, by permutation composition and by permutation-matrix
    products, and the two must agree. A reoriented token, a copied or skipped step, or a
    wrong flatness claim is refused.
    """
    spec = spec_from('WF24', 'Pinned-token operational scratchpad', 2, ['WF2'], None,
                     'dual_holonomy_checkers', 'wf24_pinned_token_operational_scratchpad')

    def validate(self, task):
        n = as_int(task.get('n'), 'n')
        require(isinstance(task.get('links'), Mapping) and isinstance(task.get('loop'), list) and task['loop'],
                'links and loop required')
        for name, p in task['links'].items():
            as_perm(p, n, name)
        require(all(isinstance(t, str) and _TOKEN.fullmatch(t) and t[:-1] in task['links'] for t in task['loop']),
                'loop tokens must be pinned eK+ / eK- on declared links')
        return task

    @staticmethod
    def link(task, token: str) -> tuple[int, ...]:
        p = tuple(task['links'][token[:-1]])
        return p if token[-1] == '+' else pinv(p)

    def check(self, task, sealed, content, host):
        n, loop = task['n'], task['loop']
        require(isinstance(content, Mapping) and isinstance(content.get('tokens'), list)
                and isinstance(content.get('scratchpad'), list), 'tokens and scratchpad required')
        require(type(content.get('flat')) is bool, 'flat must be a bool')
        steps = [as_perm(s, n, 'scratchpad') for s in content['scratchpad']]
        claimed = as_perm(content.get('holonomy'), n, 'holonomy')
        host.record('tokens_pinned', content['tokens'] == loop, canonical(content['tokens']).decode('utf-8'))
        identity = tuple(range(n))
        chain, acc, matrix = [], identity, perm_matrix(identity)
        for t in loop:
            acc = pmul(acc, self.link(task, t))
            chain.append(acc)
        for t in loop:
            matrix = matmul(matrix, perm_matrix(self.link(task, t)))
        second = tuple(row.index(1) for row in matrix)
        bad = next((k for k, (s, c) in enumerate(zip(steps, chain, strict=False)) if s != c),
                   None if len(steps) == len(chain) else min(len(steps), len(chain)))
        host.record('scratchpad_steps_exact', bad is None, f'first_bad_step={bad}')
        host.record('dual_checkers_agree', acc == second, f'{acc}|{second}')
        host.record('holonomy_matches', claimed == acc, str(acc))
        host.record('flatness_matches', content['flat'] == (acc == identity), str(acc == identity))
        return judge(host, holonomy=list(acc), flat=acc == identity, first_bad_step=bad)

    def fixtures(self):
        task = {'statement': 'Echo the pinned tokens, list every partial product, then give the holonomy and '
                             'whether the loop is flat.', 'n': 3,
                'links': {'e0': [1, 0, 2], 'e1': [0, 2, 1], 'e2': [1, 2, 0]}, 'loop': ['e0+', 'e1+', 'e2-']}
        flat_task = {**task, 'loop': ['e0+', 'e1+', 'e2+']}
        good = {'tokens': task['loop'], 'scratchpad': [[1, 0, 2], [2, 0, 1], [1, 2, 0]], 'holonomy': [1, 2, 0],
                'flat': False}
        flat = {'tokens': flat_task['loop'], 'scratchpad': [[1, 0, 2], [2, 0, 1], [0, 1, 2]], 'holonomy': [0, 1, 2],
                'flat': True}
        copied = {**good, 'scratchpad': [[1, 0, 2], [1, 2, 0], [1, 2, 0]]}
        return {
            'nontrivial_holonomy': ({'task': task, 'replies': [good]}, 'HOST_CERTIFIED'),
            'flat_loop': ({'task': flat_task, 'replies': [flat]}, 'HOST_CERTIFIED'),
            'reoriented_token_claims_flat': ({'task': task, 'replies': [flat]}, 'REFUSED'),
            'copied_final_skips_a_step': ({'task': task, 'replies': [copied]}, 'REFUSED'),
            'flat_claim_on_nontrivial_loop': ({'task': task, 'replies': [{**good, 'flat': True}]}, 'REFUSED'),
        }


@register
class ClaimScopedReceipt(WorkflowFamily):
    """WF32. Admit each atomic claim only through its own checker, bound to its own evidence digest.

    Exact claims cite an input the task declares (with its WF13 domain checker) and give
    a witness; free text on an exact claim is never admitted with it. Quote claims need a
    declared source and a non-empty byte span whose bytes equal the quoted text. Prose,
    universal and unsupported claims stay ``uncertified_obligations``. The receipt lists
    admitted(J) with one digest per claim. A reply that lists a claim as admitted outside
    J, forges a digest, cites an undeclared input, or carries a failing witness is refused.
    """
    spec = spec_from('WF32', 'Claim-scoped receipt', 2, ['WF1', 'WF2'], None, 'per_claim_independent_checkers',
                     'wf32_claim_scoped_receipt')

    def validate(self, task):
        require(isinstance(task.get('sources', {}), Mapping), 'sources must be an object')
        inputs = task.get('inputs', {})
        require(isinstance(inputs, Mapping) and all(
            isinstance(v, Mapping) and v.get('checker') in DOMAIN_CHECKERS and isinstance(v.get('input'), Mapping)
            for v in inputs.values()), 'declared inputs need a registered checker and an input object')
        return task

    def check_claim(self, task, claim) -> tuple[bool, dict[str, Any]] | None:
        """(accepted, host witness) for a claim a checker covers; None leaves it unadmitted."""
        kind, sources = claim.get('kind'), task.get('sources', {})
        if kind == 'exact':
            declared = task.get('inputs', {}).get(claim.get('input_ref'))
            if declared is None or 'input' in claim or 'checker' in claim:
                return False, {'undeclared_input': canonical(claim.get('input_ref')).decode('utf-8')}
            return DOMAIN_CHECKERS[declared['checker']](declared['input'], claim.get('witness'))
        if kind == 'quote' and claim.get('source') in sources and isinstance(claim.get('span'), list):
            require(len(claim['span']) == 2 and isinstance(claim.get('text'), str), 'quote needs [start, end] and text')
            start, end = (as_int(x, 'span') for x in claim['span'])
            data = sources[claim['source']].encode('utf-8')
            ok = 0 <= start < end <= len(data) and data[start:end] == claim['text'].encode('utf-8')
            return ok, {'source_sha256': digest(sources[claim['source']]), 'span': [start, end]}
        return None

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and isinstance(content.get('claims'), list) and content['claims'],
                'claims required')
        require(all(isinstance(c, Mapping) for c in content['claims']), 'claims are objects')
        ids = [c.get('id') for c in content['claims']]
        require(all(isinstance(i, str) for i in ids) and len(set(ids)) == len(ids), 'claims need unique string ids')
        admitted: dict[str, str] = {}
        unadmitted: list[str] = []
        for claim in content['claims']:
            kind, checked = claim.get('kind'), self.check_claim(task, claim)
            if checked is None:
                unadmitted.append(claim['id'])
                continue
            ok, witness = checked
            scope = {k: v for k, v in claim.items() if k != 'evidence_sha256' and (k != 'text' or kind == 'quote')}
            if kind != 'quote' and 'text' in claim:
                unadmitted.append(f"{claim['id']}:text")
            bound = digest({'claim': scope, 'host': witness})
            host.record(f"claim:{claim['id']}", ok, canonical(witness).decode('utf-8'))
            if 'evidence_sha256' in claim:
                host.record(f"claim:{claim['id']}:digest_bound", claim['evidence_sha256'] == bound, bound)
            if ok:
                admitted[claim['id']] = bound
        listed = content.get('admitted', [])
        require(isinstance(listed, list), 'admitted must be a list')
        overreach = sorted({str(x) for x in listed} - set(admitted))
        host.record('no_admission_overreach', not overreach, str(overreach))
        host.record('some_claim_admitted', bool(admitted), str(sorted(admitted)))
        if host.failed:
            return judge(host, overreach=overreach, admitted=sorted(admitted), unadmitted=unadmitted)
        host.uncertified_obligations = tuple(unadmitted)
        return certified('CLAIM_SCOPED' if unadmitted else 'ALL_CLAIMS_ADMITTED', admitted=admitted,
                         unadmitted=unadmitted)

    def fixtures(self):
        text = 'Charges 1, 5, -7, -8 and 9 cancel both U(1) anomalies.'
        task = {'statement': 'Make atomic claims; cite a declared input and a witness, or a source span, for each.',
                'sources': {'note': text},
                'inputs': {'charges': {'checker': 'u1_anomaly', 'input': {'charges': [1, 5, -7, -8, 9]}}}}
        free = {'linear': 0, 'cubic': 0, 'anomaly_free': True}
        exact = {'id': 'c1', 'kind': 'exact', 'input_ref': 'charges', 'witness': free}
        trivial = {'id': 'c5', 'kind': 'exact', 'checker': 'u1_anomaly', 'input': {'charges': [0]}, 'witness': free,
                   'text': 'Every chiral theory is anomaly free.'}
        quote = {'id': 'c2', 'kind': 'quote', 'source': 'note', 'span': [0, 26], 'text': text[:26]}
        universal = {'id': 'c3', 'kind': 'universal', 'text': 'Any five charges summing to zero are anomaly free.'}
        prose = {'id': 'c4', 'kind': 'prose', 'text': 'This is the standard example.'}
        claims = [exact, quote, universal, prose]

        def bundle(cs, listed):
            return {'task': task, 'replies': [{'claims': cs, 'admitted': listed}]}
        return {
            'checked_claims_admitted_rest_open': (bundle(claims, ['c1', 'c2']), 'HOST_CERTIFIED'),
            'every_claim_checked': (bundle([exact, quote], ['c1', 'c2']), 'HOST_CERTIFIED'),
            'correct_witness_admits_universal': (bundle(claims, ['c1', 'c2', 'c3']), 'REFUSED'),
            'quote_span_off_by_one_byte': (bundle([exact, {**quote, 'span': [1, 27]}], ['c1', 'c2']), 'REFUSED'),
            'exact_claim_text_stays_open': (bundle([{**exact, 'text': 'So all charge sets cancel.'}], ['c1']),
                                            'HOST_CERTIFIED'),
            'empty_quote_admits_nothing': (bundle([{**quote, 'span': [0, 0], 'text': ''}], ['c2']), 'REFUSED'),
            'self_chosen_trivial_input_carries_prose': (bundle([trivial], ['c5']), 'REFUSED'),
            'forged_evidence_digest': (bundle([{**exact, 'evidence_sha256': '0' * 64}], ['c1']), 'REFUSED'),
            'prose_only_admits_nothing': (bundle([universal, prose], []), 'REFUSED'),
        }


def _poly_eval(coeffs: list[Fraction], x: Fraction) -> Fraction:
    return sum((c * x ** k for k, c in enumerate(coeffs)), Fraction(0))


def _poly_mul(a: list[Fraction], b: list[Fraction]) -> list[Fraction]:
    out = [Fraction(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            out[i + j] += x * y
    return out


TERMINALS = ('Accepted', 'Underdetermined', 'Refuted', 'Refused')


@register
class FiniteTerminalSelector(WorkflowFamily):
    """WF45. Select within a declared finite candidate family, or name why no unique selection exists.

    Domain: candidate polynomials with exact coefficients and observations
    ``|p(x) - y| <= tol``. The survivor set fixes the terminal: one survivor is Accepted,
    several Underdetermined, none Refuted, and an empty family or empty evidence Refused.
    The host then adds a candidate that agrees with a survivor on every observation and
    checks that the survivor count rises, so acceptance stays relative to the family.
    Dropping competitors from the family, or claiming a terminal the survivors do not give,
    is refused.
    """
    spec = spec_from('WF45', 'Finite terminal selector and plenitude test', 2, ['WF7'], None,
                     'finite_survivor_set_verifier', 'wf45_finite_terminal_selector_and_plenitude_test')

    def validate(self, task):
        require(isinstance(task.get('family'), Mapping) and isinstance(task.get('evidence'), list),
                'family and evidence required')
        return task

    @staticmethod
    def survivors(family: Mapping[str, list[Fraction]], evidence) -> list[str]:
        return sorted(k for k, p in family.items() if all(abs(_poly_eval(p, x) - y) <= tol for x, y, tol in evidence))

    def check(self, task, sealed, content, host):
        family = {str(k): [as_fraction(c, 'coefficient') for c in v] for k, v in task['family'].items()}
        evidence = [(as_fraction(e['x'], 'x'), as_fraction(e['y'], 'y'), as_fraction(e.get('tol', 0), 'tol'))
                    for e in task['evidence']]
        require(all(tol >= 0 for *_, tol in evidence), 'tolerances must be non-negative')
        alive = self.survivors(family, evidence)
        by_count = {0: 'Refuted', 1: 'Accepted'}
        truth = by_count.get(len(alive), 'Underdetermined') if family and evidence else 'Refused'
        require(isinstance(content, Mapping) and content.get('terminal') in TERMINALS,
                f'terminal must be in {TERMINALS}')
        considered = content.get('family_considered')
        require(isinstance(considered, list) and all(isinstance(k, str) for k in considered),
                'family_considered must list candidate ids')
        host.record('declared_family_kept', sorted(considered) == sorted(family), canonical(considered).decode('utf-8'))
        host.record('terminal_matches_survivor_set', content['terminal'] == truth, f'{truth}:{alive}')
        if truth == 'Accepted':
            host.record('selection_is_the_survivor', content.get('selected') == alive[0], alive[0])
        if alive:
            vanishing = [Fraction(1)]
            for x in sorted({x for x, _y, _t in evidence}):
                vanishing = _poly_mul(vanishing, [-x, Fraction(1)])
            base = family[alive[0]]
            width = max(len(base), len(vanishing))
            twin = [(base[i] if i < len(base) else 0) + (vanishing[i] if i < len(vanishing) else 0)
                    for i in range(width)]
            grown = self.survivors({**family, '~twin': twin}, evidence)
            host.record('plenitude_raises_survivor_count', len(grown) == len(alive) + 1, f'{len(alive)}->{len(grown)}')
        if host.failed or truth == 'Accepted':
            return judge(host, 'ACCEPTED_WITHIN_FAMILY', survivors=alive, terminal=truth)
        code = {'Underdetermined': REFUSAL_CODES['underdetermined'], 'Refuted': REFUSAL_CODES['inconsistent'],
                'Refused': 'REFUSED_UNDECLARED_FAMILY'}[truth]
        return typed_refusal(code, survivors=alive, terminal=truth)

    def fixtures(self):
        family = {'a': [1, 2], 'b': [1, 0, 1], 'c': [1, 1, 1]}
        ids = sorted(family)
        under = {'statement': 'Pick the candidate the evidence selects, or return the terminal that applies.',
                 'family': family, 'evidence': [{'x': 0, 'y': 1}, {'x': 1, 'y': 3, 'tol': '1/10'}]}
        unique = {**under, 'evidence': [*under['evidence'], {'x': 2, 'y': '49/10', 'tol': '1/5'}]}
        refuted = {**under, 'evidence': [{'x': 0, 'y': 5}]}

        def reply(task, terminal, selected=None, considered=ids):
            return {'task': task, 'replies': [{'terminal': terminal, 'selected': selected,
                                               'family_considered': considered}]}
        return {
            'unique_survivor_accepted': (reply(unique, 'Accepted', 'a'), 'HOST_CERTIFIED'),
            'two_survivors_underdetermined': (reply(under, 'Underdetermined'), 'TYPED_REFUSAL'),
            'no_survivor_refuted': (reply(refuted, 'Refuted'), 'TYPED_REFUSAL'),
            'bluff_accept_when_underdetermined': (reply(under, 'Accepted', 'a'), 'REFUSED'),
            'competitor_deleted_to_force_accept': (reply(under, 'Accepted', 'a', ['a', 'b']), 'REFUSED'),
            'wrong_survivor_selected': (reply(unique, 'Accepted', 'c'), 'REFUSED'),
        }
