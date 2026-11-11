"""Layer 8 families: derivation loops, audit dialogues, compression, harness evolution, query campaigns."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from fractions import Fraction
from math import comb
from typing import Any

from ..civilization import Candidate, Lineage, select
from ..fidelity import HostOracleContext
from .base import (
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
)
from .exact import Graph, seal_chain, transpose
from .layer2 import Assessment, BoundedCheckAndRepair
from .registry import register

STRUCTURAL_LIFTS = ('fundamental_cycles', 'chords')
STRUCTURE_KEYS = ('edges', 'faces')


class SharedFuel:
    """A shared integer fuel counter that only ever decreases."""

    def __init__(self, value: int):
        self.value = as_int(value, 'fuel')
        self.trace = [self.value]

    def draw(self, cost: int = 1) -> bool:
        if cost <= 0 or self.value < cost:
            return False
        self.value -= cost
        self.trace.append(self.value)
        return True

    @property
    def strictly_decreasing(self) -> bool:
        return all(a > b for a, b in zip(self.trace, self.trace[1:], strict=False))


@dataclass
class LoopResult:
    """End state of one derivation loop. ``status`` is certificate, budget, fuel, limit or scope."""
    status: str
    trail: list[dict[str, Any]] = field(default_factory=list)
    grants: list[dict[str, Any]] = field(default_factory=list)
    last: Assessment | None = None
    content: Any = None


def odd_cycle_count(g: Graph, labels: list[int], flips: list[int]) -> int:
    c = [(int(x) + (1 if i in set(flips) else 0)) % 2 for i, x in enumerate(labels)]
    return sum(1 for cyc in g.fundamental_cycles() if g.cycle_sum(c, cyc, 2))


def flip_list(value: Any, m: int) -> list[int]:
    require(isinstance(value, list), 'flip list required')
    out = sorted({as_int(i, 'flip') for i in value})
    require(all(0 <= i < m for i in out), 'flip index out of range')
    return out


@register
class DerivationLoopWithLiftGrants(BoundedCheckAndRepair):
    """WF20. The WF9 repair loop, with structural lift grants when the defect stalls.

    Domain: XOR edge labels, as in WF9. When the host defect (odd fundamental
    cycles) does not strictly fall, the host issues a LIFT_REQUEST grant of
    fundamental cycles or chords. The grant must be a function of the graph
    alone, never of the labels or the repair. The loop halts on a certificate,
    on budget or on the limit of 5; a request for non-structural data is refused.
    """
    spec = spec_from('WF20', 'Derivation loop with lift grants', 8, ['WF9', 'WF10', 'WF19'], 'WF9',
                     'structural_lift_grant_loop', 'wf20_derivation_loop_with_lift_grants')
    LOOP_LIMIT = 5

    def max_attempts(self, task):
        limit = as_int(task.get('max_attempts', self.LOOP_LIMIT), 'max_attempts')
        require(1 <= limit <= self.LOOP_LIMIT, f'max_attempts must be in 1..{self.LOOP_LIMIT}')
        return limit

    def lift_grant(self, task: Mapping[str, Any], kind: str) -> dict[str, Any]:
        g = Graph.of(task['edges'])
        if kind == 'chords':
            return {'chords': g.spanning_forest()[1]}
        return {'fundamental_cycles': [[[i, s] for i, s in cyc] for cyc in g.fundamental_cycles()]}

    def grant_is_structural(self, task: Mapping[str, Any], grant: Mapping[str, Any]) -> bool:
        """The grant recomputed from the structure keys alone must be identical."""
        blind = {k: v for k, v in task.items() if k in STRUCTURE_KEYS}
        return grant['kind'] in STRUCTURAL_LIFTS and self.lift_grant(blind, grant['kind']) == grant['data']

    def derive(self, session: Session, task: Mapping[str, Any], prefix: str = '',
               fuel: SharedFuel | None = None) -> LoopResult:
        out = LoopResult('limit')
        prompt, previous, granted = self.prompt(task), None, ''
        for t in range(self.max_attempts(task)):
            if fuel is not None and not fuel.draw():
                out.status = 'fuel'
                return out
            reply = session.ask(f'{prefix}attempt:{t}', prompt)
            if reply is None:
                out.status = 'budget'
                return out
            content = reply.content
            kind = content.get('lift_request') if isinstance(content, Mapping) else None
            if kind is not None and kind not in STRUCTURAL_LIFTS:
                out.status = 'scope'
                out.trail.append({'attempt': t, 'lift_request': str(kind)})
                return out
            try:
                result = self.assess(task, session.sealed, content)
            except MalformedCandidateError as exc:
                result = Assessment(False, {'malformed': str(exc)}, None)
            out.last, out.content = result, content
            out.trail.append({'attempt': t, 'measure': result.measure, 'residual': dict(result.residual)})
            if result.accepted:
                out.status = 'certificate'
                return out
            stalled = previous is not None and (result.measure is None or result.measure >= previous)
            if stalled:
                grant = {'attempt': t, 'kind': kind or STRUCTURAL_LIFTS[0]}
                grant['data'] = self.lift_grant(task, grant['kind'])
                out.grants.append(grant)
                granted += '\nLIFT_REQUEST grant: ' + canonical(grant['data']).decode('utf-8')
            previous = result.measure if result.measure is not None else previous
            prompt = self.repair_prompt(task, result.residual) + granted
        return out

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        res = self.derive(session, task)
        grants = [{'attempt': g['attempt'], 'kind': g['kind']} for g in res.grants]
        host.record('lift_grants_structural', all(self.grant_is_structural(task, g) for g in res.grants),
                    canonical(grants).decode('utf-8'))
        if res.status == 'scope':
            host.record('lift_request_structural', False, canonical(res.trail[-1]).decode('utf-8'))
            return refused('LIFT_SCOPE_VIOLATION', trail=res.trail)
        host.record('certificate_within_loop_limit', res.status == 'certificate', res.status)
        if res.status != 'certificate':
            return refused(f'HALTED_ON_{res.status.upper()}', attempts=len(res.trail), grants=grants)
        return judge(host, 'DERIVED', attempts=len(res.trail), grants=grants)

    def fixtures(self):
        task = {'statement': 'Flip the fewest edge labels so every cycle has an even label sum.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'labels': [1, 0, 0, 0, 0]}
        stall = [{'flip': [3]}, {'flip': [4], 'lift_request': 'chords'}]
        return {
            'stall_then_lift_then_derived': ({'task': task, 'replies': [*stall, {'flip': [0]}]}, 'HOST_CERTIFIED'),
            'first_try_without_lift': ({'task': task, 'replies': [{'flip': [1]}]}, 'HOST_CERTIFIED'),
            'lift_request_for_target_values': (
                {'task': task, 'replies': [{'flip': [3]}, {'flip': [4], 'lift_request': 'minimal_flip_set'}]},
                'REFUSED'),
            'loop_limit_of_five_exhausted': ({'task': task, 'replies': [*stall, {'flip': [3, 4]}, {'flip': [2]},
                                                                        {'flip': [0, 3]}, {'flip': [0]}]},
                                             'REFUSED'),
        }


# ---------------------------------------------------------------- WF28

ROLES = ('proposer', 'adversary', 'solver', 'overconfidence_probe', 'stabilizer', 'schema_auditor',
         'truth_repair', 'terminal_arbiter')
STATE_ROLES = frozenset({'proposer', 'solver', 'stabilizer', 'truth_repair'})


def l1_defect(g: Graph, c: list[Fraction], phi: list[Fraction]) -> Fraction:
    return sum((abs(r) for r in g.residual(c, phi)), Fraction(0))


@register
class EightRoleAuditDialogue(WorkflowFamily):
    """WF28. Eight roles in fixed order repair a potential; only the host defect decides.

    Domain: measured edge differences ``c`` on a graph; a state role proposes a
    vertex potential ``phi`` and the host defect is ``||c - delta phi||_1``.
    Each role sees only the frozen earlier outputs and must quote their seal
    head. State roles must strictly lower the defect; the run certifies only at
    defect 0. A stale view, a non-descending step or any acceptance claim is refused.
    """
    spec = spec_from('WF28', 'Eight-role audit dialogue', 8, ['WF15'], None, 'strict_l1_defect_descent',
                     'wf28_eight_role_audit_dialogue')

    def validate(self, task):
        require(isinstance(task.get('edges'), list) and isinstance(task.get('c'), list), 'edges and c required')
        require(len(task['edges']) == len(task['c']), 'one value per edge')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        g = Graph.of(task['edges'])
        n = len(g.vertices)
        c = [as_fraction(x, 'c') for x in task['c']]
        frozen: list[Any] = []
        defects: list[Fraction] = []
        for role in ROLES:
            head = seal_chain(task, frozen)[-1]
            reply = session.ask(role, self.prompt(task) + f'\nRole: {role}\nFrozen outputs: '
                                + canonical(frozen).decode('utf-8') + f'\nSeal head: {head}')
            if reply is None:
                return refused('NO_ADMISSIBLE_REPLY', role=role)
            content = reply.content
            require(isinstance(content, Mapping), f'{role}: reply must be an object')
            if not host.record(f'{role}:sees_frozen_outputs', content.get('seen') == head, head):
                return refused('STALE_VIEW', role=role)
            if not host.record(f'{role}:no_acceptance_claim', not ({'accept', 'certify'} & set(content)), role):
                return refused('ROLE_CANNOT_ACCEPT', role=role)
            if role in STATE_ROLES:
                require(isinstance(content.get('phi'), list) and len(content['phi']) == n, f'{role}: phi[n]')
                d = l1_defect(g, c, [as_fraction(x, 'phi') for x in content['phi']])
                if not host.record(f'{role}:strict_l1_descent', not defects or d < defects[-1], f'{defects}|{d}'):
                    return refused('DEFECT_NOT_DESCENDING', role=role, defects=[str(x) for x in [*defects, d]])
                defects.append(d)
            else:
                require(isinstance(content.get('finding'), str) and 'phi' not in content, f'{role}: finding only')
            frozen.append(content)
        trace = [str(x) for x in defects]
        host.record('final_defect_zero', defects[-1] == 0, ','.join(trace))
        return judge(host, 'AUDIT_CLOSED', defects=trace)

    def fixtures(self):
        task = {'statement': 'Find vertex potentials whose differences match the measured edge values.',
                'edges': [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]], 'c': [2, 3, -2, -3, 5]}
        good = [[0, 0, 0, 0], 'no sign check on edge 3', [0, 2, 5, 0], 'defect still 6', [0, 2, 5, 2],
                'phi is a 4-list', [0, 2, 5, 3], 'host decides']
        bump = [*good[:4], [0, 2, 5, -4], *good[5:]]
        return {
            'strict_descent_to_zero': ({'task': task, 'replies': self.dialogue(task, good)}, 'HOST_CERTIFIED'),
            'stabilizer_raises_defect': ({'task': task, 'replies': self.dialogue(task, bump)}, 'REFUSED'),
            'arbiter_accepts': ({'task': task, 'replies': self.dialogue(task, good, accept_at=7)}, 'REFUSED'),
            'auditor_reads_stale_view': ({'task': task, 'replies': self.dialogue(task, good, stale_at=5)},
                                         'REFUSED'),
        }

    @staticmethod
    def dialogue(task, outputs, accept_at=None, stale_at=None):
        """Build fixture replies that quote the correct seal head of the frozen prefix."""
        frozen: list[Any] = []
        for k, out in enumerate(outputs):
            head = seal_chain(task, frozen[:-1] if k == stale_at else frozen)[-1]
            reply = {'seen': head, 'phi' if isinstance(out, list) else 'finding': out}
            if k == accept_at:
                reply['accept'] = True
            frozen.append(reply)
        return frozen


# ---------------------------------------------------------------- WF34

COMPRESSED_KEYS = frozenset({'root', 'champion', 'recent', 'evidence'})


@register
class FutureFaithfulCompression(WorkflowFamily):
    """WF34. Compress a repair history to root, champion, two recent attempts and evidence references.

    Domain: a WF9-style XOR repair history. The host verdict on a continuation
    (REPEAT, UNKNOWN_REFERENCE, IMPROVES, NO_PROGRESS) is computed from the full
    history and from the proposed compressed state; the compression is accepted
    only if every declared continuation gets the identical verdict. A
    compression that drops needed state, or forges the root, is refused.
    """
    spec = spec_from('WF34', 'Future-faithful compression and bounded context', 8, ['WF8', 'WF22'], None,
                     'continuation_verdict_equality', 'wf34_future_faithful_compression_and_bounded_context')

    def validate(self, task):
        require(isinstance(task.get('history'), list) and task['history'], 'history required')
        require(isinstance(task.get('continuations'), list) and task['continuations'], 'continuations required')
        return task

    @staticmethod
    def root(task) -> str:
        return digest({'edges': task['edges'], 'labels': task['labels']})

    def full_state(self, task) -> dict[str, Any]:
        g = Graph.of(task['edges'])
        hist = task['history']
        best = min(range(len(hist)), key=lambda i: (odd_cycle_count(g, task['labels'], hist[i]['flip']), i))
        return {'root': self.root(task), 'champion': hist[best]['flip'], 'recent': [h['flip'] for h in hist[-2:]],
                'evidence': [h['ref'] for h in hist]}

    def verdict(self, task, state, cont) -> str:
        g, m = Graph.of(task['edges']), len(task['edges'])
        flips = flip_list(cont['flip'], m)
        if flips in [flip_list(r, m) for r in state['recent']]:
            return 'REPEAT'
        if 'cites' in cont and cont['cites'] not in state['evidence']:
            return 'UNKNOWN_REFERENCE'
        champion = odd_cycle_count(g, task['labels'], flip_list(state['champion'], m))
        return 'IMPROVES' if odd_cycle_count(g, task['labels'], flips) < champion else 'NO_PROGRESS'

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and set(content) == COMPRESSED_KEYS, 'compressed state keys')
        require(isinstance(content['recent'], list) and isinstance(content['evidence'], list), 'lists required')
        full = self.full_state(task)
        host.record('root_bound_to_spec', content['root'] == full['root'], str(content['root']))
        host.record('bounded_context', len(content['recent']) <= 2, str(len(content['recent'])))
        host.record('references_retained_not_invented', set(content['evidence']) <= set(full['evidence']),
                    canonical(content['evidence']).decode('utf-8'))
        rows = [[self.verdict(task, full, k), self.verdict(task, content, k)] for k in task['continuations']]
        diverged = [i for i, (a, b) in enumerate(rows) if a != b]
        host.record('identical_verdicts_on_every_continuation', not diverged, canonical(rows).decode('utf-8'))
        return judge(host, 'COMPRESSION_FAITHFUL', verdicts=[a for a, _ in rows], diverged=diverged)

    def fixtures(self):
        history = [{'flip': [3], 'ref': 'ev0'}, {'flip': [2], 'ref': 'ev1'}, {'flip': [4], 'ref': 'ev2'},
                   {'flip': [1, 2], 'ref': 'ev3'}]
        task = {'statement': 'Compress this repair history so every listed continuation is judged the same.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'labels': [1, 0, 0, 0, 0], 'history': history,
                'continuations': [{'flip': [4]}, {'flip': [3, 4]}, {'flip': [0], 'cites': 'ev0'},
                                  {'flip': [3], 'cites': 'ev1'}, {'flip': [3, 4]}]}
        good = {'root': self.root(task), 'champion': [2], 'recent': [[4], [1, 2]],
                'evidence': ['ev0', 'ev1', 'ev2', 'ev3']}

        def case(**change):
            return {'task': task, 'replies': [{**good, **change}]}
        return {
            'faithful_compression': (case(), 'HOST_CERTIFIED'),
            'dropped_old_evidence_reference': (case(evidence=['ev2', 'ev3']), 'REFUSED'),
            'kept_one_recent_attempt': (case(recent=[[1, 2]]), 'REFUSED'),
            'latest_attempt_as_champion': (case(champion=[1, 2]), 'REFUSED'),
            'forged_root': (case(root=digest({'edges': [], 'labels': []})), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF37

def sign_test_p(wins: int, losses: int) -> Fraction:
    """Exact one-sided sign test: P(X >= wins) for X ~ Bin(wins + losses, 1/2)."""
    n = wins + losses
    return Fraction(sum(comb(n, k) for k in range(wins, n + 1)), 2 ** n)


def paired(challenger: list[int], incumbent: list[int]) -> tuple[int, int]:
    require(len(challenger) == len(incumbent), 'paired panels must align')
    wins = sum(1 for a, b in zip(challenger, incumbent, strict=True) if a and not b)
    return wins, sum(1 for a, b in zip(challenger, incumbent, strict=True) if b and not a)


@register
class EvidenceBoundHarnessEvolution(WorkflowFamily):
    """WF37. Replace the incumbent harness only on untainted, Pareto-front, privately confirmed evidence.

    Genomes live in a ``civilization.Lineage``; contamination taints every
    descendant. ``civilization.select`` places public results in the 60/30/10
    reserves with four-axis Pareto dominance. The challenger must then win an
    exact sign test against the incumbent on the sealed private split and again
    on a fresh panel. A tainted, dominated or unconfirmed replacement is refused.
    """
    spec = spec_from('WF37', 'Evidence-bound harness evolution', 8, ['WF19', 'WF22'], None,
                     'taint_pareto_sign_test_confirmation', 'wf37_evidence_bound_harness_evolution')

    def validate(self, task):
        require(isinstance(task.get('candidates'), list) and isinstance(task.get('lineage'), list), 'population')
        as_fraction(task.get('alpha'), 'alpha')
        return task

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and isinstance(content.get('replace_with'), str), 'replace_with')
        gid, inc = content['replace_with'], task['incumbent']
        pop = {c['genome_id']: Candidate(**c) for c in task['candidates']}
        require(gid in pop and gid != inc, 'challenger must be a listed non-incumbent genome')
        lineage = Lineage()
        for g in pop:
            lineage.add(g)
        for parent, child in task['lineage']:
            lineage.derive(parent, child, f'{parent}->{child}')
        tainted = lineage.taint(set(task.get('contaminated', [])))
        reserves = select(list(pop.values()), cap=10, tainted=tainted)
        alpha = as_fraction(task['alpha'], 'alpha')
        host.record('challenger_untainted', gid not in tainted, canonical(sorted(tainted)).decode('utf-8'))
        host.record('challenger_on_front', gid in reserves['Front'], canonical(reserves).decode('utf-8'))
        ids = [set(task['public_ids']), set(sealed['private']['ids']), set(sealed['fresh']['ids'])]
        host.record('grading_splits_disjoint', not (ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2]), '')
        p = {}
        for panel in ('private', 'fresh'):
            w, lo = paired(sealed[panel]['results'].get(gid, []), sealed[panel]['results'][inc])
            p[panel] = sign_test_p(w, lo)
            host.record(f'{panel}_sign_test', w > lo and p[panel] <= alpha, f'{w}-{lo} p={p[panel]}')
        return judge(host, 'INCUMBENT_REPLACED', challenger=gid, front=reserves['Front'],
                     p_values={k: str(v) for k, v in p.items()}, tainted=sorted(tainted))

    def fixtures(self):
        def cand(g, passed, tokens, wall, **kw):
            return {'genome_id': g, 'passed': passed, 'attempted': 10, 'spent_microusd': 0,
                    'total_tokens': tokens, 'wall_ms': wall, **kw}
        task = {'statement': 'Propose a harness to replace the incumbent h0.', 'incumbent': 'h0', 'alpha': '1/20',
                'candidates': [cand('h0', 5, 1000, 100), cand('h1', 8, 1200, 120), cand('h2', 9, 900, 90),
                               cand('h3', 10, 800, 80), cand('h4', 7, 900, 90), cand('h5', 6, 1300, 130),
                               cand('base', 4, 500, 50, is_baseline=True)],
                'lineage': [['h0', 'h1'], ['h0', 'h2'], ['h2', 'h3'], ['h0', 'h4'], ['h1', 'h5']],
                'contaminated': ['h2'], 'public_ids': [f'q{i}' for i in range(10)]}
        inc_p, inc_f = [1, 1, 1, 1, 0, 0, 0, 0, 0, 0], [1, 0, 0, 0, 0, 0]
        sealed = {'private': {'ids': [f'p{i}' for i in range(10)],
                              'results': {'h0': inc_p, 'h1': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                                          'h3': [1] * 10, 'h4': [1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
                                          'h5': [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}},
                  'fresh': {'ids': [f'f{i}' for i in range(6)],
                            'results': {'h0': inc_f, 'h1': [1, 1, 1, 1, 1, 1], 'h3': [1] * 6,
                                        'h4': [0, 1, 1, 0, 0, 0], 'h5': [1] * 6}}}

        def case(gid, s=sealed):
            return {'task': task, 'sealed': s, 'replies': [{'replace_with': gid}]}
        leaky = {**sealed, 'fresh': {**sealed['fresh'], 'ids': ['p0', 'f1', 'f2', 'f3', 'f4', 'f5']}}
        return {
            'confirmed_front_challenger': (case('h1'), 'HOST_CERTIFIED'),
            'tainted_descendant_proposed': (case('h3'), 'REFUSED'),
            'fresh_confirmation_fails': (case('h4'), 'REFUSED'),
            'pareto_dominated_challenger': (case('h5'), 'REFUSED'),
            'fresh_panel_reuses_private_item': (case('h1', leaky), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF49

DIALECT_KEYS = {'json': {'A', 'b'}, 'augmented': {'rows'}, 'columns': {'cols', 'rhs'}}


def decode_query(mode: str, packet: Mapping[str, Any]) -> dict[str, Any]:
    """Independent decoder per dialect, back to exact ``{'A', 'b'}``."""
    def q(v):
        return [as_fraction(x, 'entry') for x in v]
    if mode == 'json':
        return {'A': [q(r) for r in packet['A']], 'b': q(packet['b'])}
    if mode == 'augmented':
        rows = []
        for line in packet['rows']:
            require(isinstance(line, str) and line.count('|') == 1, 'rows are "a b | c" strings')
            lhs, rhs = line.split('|')
            rows.append((q(lhs.split()), as_fraction(rhs.strip(), 'rhs')))
        return {'A': [r for r, _ in rows], 'b': [x for _, x in rows]}
    require(isinstance(packet['cols'], list) and packet['cols'], 'cols required')
    return {'A': transpose([q(col) for col in packet['cols']]), 'b': q(packet['rhs'])}


@register
class QueryPreservationCampaign(WorkflowFamily):
    """WF49. Run staged, sealed packets through mode lanes; a stage passes only if the query is unchanged.

    Domain: an exact linear query ``A x = b`` re-encoded per lane (json,
    augmented rows, columns). Each stage packet must quote the previous seal
    chain head; the host decodes it with the lane's own decoder and requires
    exact equality with the original query, not an equivalent one. A lane stops
    at its first safety regression (an unlisted field such as an answer).
    """
    spec = spec_from('WF49', 'Query-preservation stage and mode campaign', 8, ['WF8', 'WF22'], None,
                     'decoded_query_equality_seal_chain', 'wf49_query_preservation_stage_and_mode_campaign')

    def validate(self, task):
        require(set(task.get('lanes', [])) <= set(DIALECT_KEYS) and task.get('lanes'), 'known lanes required')
        require(isinstance(task.get('stages'), list) and task['stages'], 'stages required')
        return task

    @staticmethod
    def seed(task, lane: str) -> dict[str, Any]:
        return {'lane': lane, 'query': digest(task['query'])}

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        query = decode_query('json', task['query'])
        lanes: dict[str, str] = {}
        for lane in task['lanes']:
            packets: list[Any] = []
            lanes[lane] = 'PASSED'
            for stage in task['stages']:
                head = seal_chain(self.seed(task, lane), packets)[-1]
                reply = session.ask(f'{lane}:{stage}', self.prompt(task) + f'\nLane: {lane}\nStage: {stage}'
                                    f'\nPrevious seal head: {head}')
                content = reply.content if reply is not None else None
                if not isinstance(content, Mapping) or not isinstance(content.get('packet'), Mapping):
                    lanes[lane] = 'NO_ADMISSIBLE_REPLY'
                    break
                packet = content['packet']
                tag = f'{lane}:{stage}'
                if not host.record(f'{tag}:safe', set(packet) == DIALECT_KEYS[lane], canonical(sorted(packet))
                                   .decode('utf-8')):
                    lanes[lane] = 'SAFETY_REGRESSION'
                    break
                if not host.record(f'{tag}:seal_chain', content.get('prev') == head, head):
                    lanes[lane] = 'SEAL_CHAIN_BROKEN'
                    break
                try:
                    same = decode_query(lane, packet) == query
                except (MalformedCandidateError, KeyError, TypeError, ValueError):
                    same = False
                if not host.record(f'{tag}:query_unchanged', same, canonical(packet).decode('utf-8')):
                    lanes[lane] = 'QUERY_CHANGED'
                    break
                packets.append(packet)
        failed = sorted({v for v in lanes.values() if v != 'PASSED'})
        if failed:
            return refused(failed[0], lanes=lanes, asks=len(session.transcript))
        return certified('QUERY_PRESERVED', lanes=lanes, asks=len(session.transcript))

    def fixtures(self):
        task = {'statement': 'Re-encode the query in the lane dialect at each stage; do not change it.',
                'query': {'A': [[1, 1], [1, -1]], 'b': [3, 1]}, 'lanes': ['json', 'augmented', 'columns'],
                'stages': ['encode', 'relay']}
        enc = {'json': {'A': [[1, 1], [1, -1]], 'b': [3, 1]}, 'augmented': {'rows': ['1 1 | 3', '1 -1 | 1']},
               'columns': {'cols': [[1, 1], [1, -1]], 'rhs': [3, 1]}}
        plan = {lane: [enc[lane], enc[lane]] for lane in task['lanes']}
        scaled = {**plan, 'augmented': [{'rows': ['2 2 | 6', '1 -1 | 1']}]}
        injected = {**plan, 'json': [enc['json'], {**enc['json'], 'answer': [2, 1]}]}
        return {
            'all_lanes_preserve_query': ({'task': task, 'replies': self.lanes(task, plan)}, 'HOST_CERTIFIED'),
            'row_scaled_equivalent_not_equal': ({'task': task, 'replies': self.lanes(task, scaled)}, 'REFUSED'),
            'relay_injects_answer_lane_stopped': ({'task': task, 'replies': self.lanes(task, injected)},
                                                  'REFUSED'),
            'forged_previous_seal': ({'task': task, 'replies': self.lanes(task, plan, forge=('columns', 1))},
                                     'REFUSED'),
        }

    def lanes(self, task, plan, forge=None):
        """Fixture replies with correct seal heads; a lane's list ends where the host stops it."""
        replies = []
        for lane in task['lanes']:
            for k, packet in enumerate(plan[lane]):
                head = seal_chain(self.seed(task, lane), plan[lane][:k])[-1]
                replies.append({'packet': packet, 'prev': '0' * 64 if forge == (lane, k) else head})
        return replies
