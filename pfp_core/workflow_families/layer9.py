"""Layer 9 families: recursive re-entry and the restart boundary, both built on the WF20 loop."""
from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from typing import Any

from ..fidelity import HostOracleContext
from .base import (
    Session,
    Verdict,
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
from .exact import Graph
from .layer2 import Assessment
from .layer8 import DerivationLoopWithLiftGrants, SharedFuel, flip_list
from .registry import register


def reentry_receipt(parent: str, child: int, root_flips: list[int], fuel: int) -> str:
    return digest({'parent': parent, 'child': child, 'flips': root_flips, 'fuel': fuel})


@register
class RecursiveReentryWithSharedFuel(DerivationLoopWithLiftGrants):
    """WF33. Split a repair into child derivations that share one fuel counter and one budget.

    Domain: XOR edge labels on a graph. A plan maps root edges onto children
    (forward coverage must be a partition); each child re-enters the WF20 loop
    on its subgraph, and its flips map back to root edges, where the union must
    pass the root WF9 check. Every ask draws from a strictly decreasing fuel
    counter. A stale parent receipt, a changed task or a fuel reset is refused.
    """
    spec = spec_from('WF33', 'Recursive re-entry with shared fuel', 9, ['WF9', 'WF20'], None,
                     'shared_fuel_parent_bound_reentry', 'wf33_recursive_re_entry_with_shared_fuel')

    def validate(self, task):
        super().validate(task)
        require(as_int(task.get('fuel'), 'fuel') > 0, 'fuel must be positive')
        return task

    @staticmethod
    def root_receipt(task, plan) -> str:
        return digest({'root': digest(task), 'plan': plan})

    @staticmethod
    def bind_header(host, k: int, head: Any, receipt: str, task, fuel: SharedFuel) -> str | None:
        """Parent binding of one re-entry: receipt, task digest and fuel must match the host's."""
        require(isinstance(head, Mapping), f'enter:{k} header must be an object')
        if not host.record(f'child{k}:parent_bound', head.get('parent_receipt') == receipt, receipt):
            return 'STALE_PARENT_RECEIPT'
        if not host.record(f'child{k}:task_unchanged', head.get('task_digest') == digest(task), digest(task)):
            return 'TASK_CHANGED'
        claimed = as_int(head.get('fuel'), 'fuel')
        if not host.record(f'child{k}:fuel_not_reset', claimed == fuel.value, f'{claimed}|{fuel.value}'):
            return 'FUEL_RESET' if claimed > fuel.value else 'FUEL_MISMATCH'
        return None

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task, m = session.task, len(session.task['edges'])
        fuel = SharedFuel(task['fuel'])
        reply = session.ask('plan', self.prompt(task) + f'\nFuel: {fuel.value}') if fuel.draw() else None
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        require(isinstance(reply.content, Mapping) and isinstance(reply.content.get('children'), list), 'plan')
        plan = [flip_list(ch, m) for ch in reply.content['children']]
        flat = sorted(i for ch in plan for i in ch)
        if not host.record('forward_coverage_partition', flat == list(range(m)), canonical(plan).decode('utf-8')):
            return refused('COVERAGE_NOT_A_PARTITION', plan=plan)
        receipt, combined = self.root_receipt(task, plan), []
        for k, child in enumerate(plan):
            if not fuel.draw():
                return refused('FUEL_EXHAUSTED', child=k, fuel_trace=fuel.trace)
            reply = session.ask(f'enter:{k}', self.prompt(task) + f'\nChild {k} edges: {child}'
                                f'\nParent receipt: {receipt}\nFuel: {fuel.value}')
            code = self.bind_header(host, k, reply.content if reply is not None else None, receipt, task, fuel)
            if code:
                return refused(code, child=k)
            sub ={'statement': task.get('statement', ''), 'edges': [task['edges'][i] for i in child],
                   'labels': [task['labels'][i] for i in child], 'max_attempts': self.max_attempts(task)}
            res = self.derive(session, sub, prefix=f'child:{k}:', fuel=fuel)
            if not host.record(f'child{k}:certified', res.status == 'certificate', res.status):
                return refused(f'CHILD_HALTED_ON_{res.status.upper()}', child=k, fuel_trace=fuel.trace)
            root_flips = sorted(child[i] for i in flip_list(res.content['flip'], len(child)))
            combined += root_flips
            receipt = reentry_receipt(receipt, k, root_flips, fuel.value)
        root = self.assess(task, session.sealed, {'flip': combined})
        host.record('backward_solution_map', root.accepted, canonical(combined).decode('utf-8'))
        host.record('fuel_strictly_decreasing', fuel.strictly_decreasing, canonical(fuel.trace).decode('utf-8'))
        asks = sum(1 for row in session.transcript if row.get('reply') is not None)
        host.record('ops_within_fuel', asks <= task['fuel'], f'{asks}|{task["fuel"]}')
        return judge(host, 'REENTRY_CERTIFIED', flips=sorted(combined), fuel_trace=fuel.trace, receipt=receipt)

    def fixtures(self):
        task = {'statement': 'Repair the labels by delegating disjoint parts to child derivations.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [4, 5], [5, 6], [6, 4]],
                'labels': [1, 0, 0, 0, 0, 0, 0, 1], 'fuel': 12}
        plan = [[0, 1, 2, 3, 4], [5, 6, 7]]
        root = self.root_receipt(task, plan)
        r0 = reentry_receipt(root, 0, [0], 9)
        changed = digest({**task, 'labels': [0] * 8})

        def bundle(enter0=None, enter1=None):
            e0 = {'parent_receipt': root, 'task_digest': digest(task), 'fuel': 10, **(enter0 or {})}
            e1 = {'parent_receipt': r0, 'task_digest': digest(task), 'fuel': 8, **(enter1 or {})}
            return {'task': task, 'replies': [{'children': plan}, e0, {'flip': [0]}, e1, {'flip': [2]}]}
        return {
            'two_children_share_fuel': (bundle(), 'HOST_CERTIFIED'),
            'stale_parent_receipt': (bundle(enter1={'parent_receipt': root}), 'REFUSED'),
            'changed_task_on_reentry': (bundle(enter0={'task_digest': changed}), 'REFUSED'),
            'fuel_reset_by_child': (bundle(enter1={'fuel': 12}), 'REFUSED'),
            'overlapping_coverage': ({'task': task, 'replies': [{'children': [[0, 1, 2, 3, 4], [4, 5, 6, 7]]}]},
                                     'REFUSED'),
        }


# ---------------------------------------------------------------- WF40

ACTIONS = ('refusal', 'lift', 'restart')
ADMISSIBLE = {'exact': 'restart', 'unclosed': 'refusal', 'closed_non_exact': 'lift'}


def face_sum(face: list[list[int]], c: list[Fraction]) -> Fraction:
    return sum((s * c[i] for i, s in face), Fraction(0))


@register
class RestartBoundaryAfterExhaustedRepair(DerivationLoopWithLiftGrants):
    """WF40. After repair ends with a positive residual, take exactly the boundary action the cochain admits.

    Domain: a 2-complex (graph plus faces) carrying measured edge values ``c``;
    repair proposes potentials ``phi`` in the WF20 loop. On exhaustion the host
    classifies ``c``: unclosed (a face sum is nonzero) admits a typed refusal
    with that face; closed non-exact admits a lift ``c = delta phi + k h`` with a
    closed ``h`` as preservation witness; exact admits a restart seeded only with
    the immutable spec and verified refusal receipts. A changed claim set is refused.
    """
    spec = spec_from('WF40', 'Restart boundary after exhausted repair', 9, ['WF9', 'WF20'], None,
                     'cochain_trichotomy_boundary', 'wf40_restart_boundary_after_exhausted_repair')

    def validate(self, task):
        require(isinstance(task.get('edges'), list) and isinstance(task.get('c'), list), 'edges and c required')
        require(len(task['edges']) == len(task['c']) and isinstance(task.get('faces'), list), 'faces required')
        g = Graph.of(task['edges'])
        for face in task['faces']:
            boundary: dict[Any, int] = {}
            for i, s in face:
                u, v = g.edges[i]
                boundary[v] = boundary.get(v, 0) + s
                boundary[u] = boundary.get(u, 0) - s
            require(not any(boundary.values()), 'every face must be a closed cycle')
        self.max_attempts(task)
        return task

    @staticmethod
    def immutable_spec(task) -> dict[str, Any]:
        return {'edges': task['edges'], 'faces': task['faces'], 'c': task['c']}

    def assess(self, task, sealed, content) -> Assessment:
        g = Graph.of(task['edges'])
        c = [as_fraction(x, 'c') for x in task['c']]
        require(isinstance(content, Mapping) and isinstance(content.get('phi'), list), 'phi list required')
        require(len(content['phi']) == len(g.vertices), 'one potential per vertex')
        r = g.residual(c, [as_fraction(x, 'phi') for x in content['phi']])
        defect = sum((abs(x) for x in r), Fraction(0))
        return Assessment(defect == 0, {'defect_l1': str(defect), 'off_edges': [i for i, x in enumerate(r) if x]},
                          defect)

    def receipts(self, task, trail) -> list[str]:
        spec_digest = digest(self.immutable_spec(task))
        return [digest({'spec': spec_digest, 'attempt': row['attempt'], 'residual': row['residual']})
                for row in trail]

    @staticmethod
    def classify(g: Graph, c: list[Fraction], faces) -> str:
        if any(face_sum(f, c) for f in faces):
            return 'unclosed'
        return 'exact' if g.is_exact(c) else 'closed_non_exact'

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        res = self.derive(session, task)
        if res.status in ('certificate', 'scope'):
            host.record('repaired_within_limit', res.status == 'certificate', res.status)
            return judge(host, 'REPAIRED', attempts=len(res.trail))
        receipts = self.receipts(task, res.trail)
        before = session.budget.summary()
        reply = session.ask('boundary', self.prompt(task) + '\nRefusal receipts: ' + canonical(receipts).decode())
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        content = reply.content
        require(isinstance(content, Mapping), 'boundary reply must be an object')
        actions = [a for a in ACTIONS if a in content]
        if not host.record('exactly_one_action', len(actions) == 1, canonical(actions).decode('utf-8')):
            return refused('NOT_EXACTLY_ONE_ACTION', actions=actions)
        g, faces = Graph.of(task['edges']), task['faces']
        c = [as_fraction(x, 'c') for x in task['c']]
        kind, delta = self.classify(g, c, faces), g.phi1(c)
        action, body = actions[0], content[actions[0]]
        require(isinstance(body, Mapping), f'{action} must be an object')
        host.record('action_matches_trichotomy', action == ADMISSIBLE[kind], f'{kind}|{action}|{delta}')
        detail = {'cochain_class': kind, 'delta': str(delta), 'action': action}
        if action == 'refusal':
            return self.check_refusal(host, body, c, faces, detail)
        if action == 'lift':
            return self.check_lift(host, body, g, c, faces, delta, detail)
        return self.check_restart(session, host, body, receipts, before, detail)

    @staticmethod
    def check_refusal(host, body, c, faces, detail) -> Verdict:
        i = as_int(body.get('face'), 'face')
        require(0 <= i < len(faces), 'face index out of range')
        host.record('face_witness_nonzero', face_sum(faces[i], c) != 0, str(face_sum(faces[i], c)))
        if host.final_output_certified:
            return typed_refusal('UNCLOSED_COCHAIN', face=i, **detail)
        return refused(host.failed[0].upper(), **detail)

    @staticmethod
    def check_lift(host, body, g: Graph, c, faces, delta, detail) -> Verdict:
        h = [as_fraction(x, 'h') for x in body.get('h', [])]
        require(len(h) == len(c), 'h is an edge cochain')
        phi = [as_fraction(x, 'phi') for x in body.get('phi', [])]
        require(len(phi) == len(g.vertices), 'one potential per vertex')
        k = as_fraction(body.get('k'), 'k')
        host.record('lift_authorised_by_positive_delta', delta > 0, str(delta))
        host.record('preservation_witness_closed', not any(face_sum(f, h) for f in faces), canonical(h).decode())
        fit = [d + k * hi for d, hi in zip(g.coboundary(phi), h, strict=True)]
        host.record('lift_reproduces_claims', fit == c, canonical(fit).decode('utf-8'))
        return judge(host, 'LIFT_AUTHORISED', **detail)

    def check_restart(self, session: Session, host, body, receipts, before, detail) -> Verdict:
        task, seed = session.task, body.get('seed')
        require(isinstance(seed, Mapping), 'restart needs a seed')
        spec = self.immutable_spec(task)
        host.record('seed_only_spec_and_receipts', set(seed) == {'spec', 'receipts'}, canonical(sorted(seed)).decode())
        same_frame = isinstance(seed.get('spec'), Mapping) and all(
            seed['spec'].get(key) == spec[key] for key in ('edges', 'faces'))
        if same_frame and seed['spec'].get('c') != spec['c']:
            host.record('claim_set_unchanged', False, canonical(seed['spec']).decode('utf-8'))
            return refused('NEW_PROBLEM_NOT_REPAIR', **detail)
        host.record('seed_spec_immutable', seed.get('spec') == spec, digest(spec))
        given = seed.get('receipts')
        host.record('receipts_verified', isinstance(given, list) and bool(given) and set(given) <= set(receipts),
                    canonical(receipts).decode('utf-8'))
        if host.failed:
            return refused(host.failed[0].upper(), **detail)
        fresh = {'statement': task.get('statement', ''), **spec, 'refusal_receipts': given}
        if 'max_attempts' in task:
            fresh['max_attempts'] = task['max_attempts']
        again = self.derive(session, fresh, prefix='restart:')
        after = session.budget.summary()
        host.record('prior_spend_locked', after['calls'] >= before['calls'] + 1 + len(again.trail)
                    and after['spent_microusd'] >= before['spent_microusd'], f"{before['calls']}|{after['calls']}")
        host.record('restart_certified', again.status == 'certificate', again.status)
        return judge(host, 'RESTART_REPAIRED', restart_attempts=len(again.trail), **detail)

    def fixtures(self):
        edges = [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]]
        base = {'statement': 'Find potentials matching the edge values, or take the admissible boundary action.',
                'edges': edges, 'faces': [[[0, 1], [1, 1], [4, -1]]], 'max_attempts': 2}
        exact = {**base, 'c': [2, 3, -2, -3, 5]}
        unclosed = {**base, 'c': [2, 3, -2, -3, 6]}
        winding = {**base, 'c': [2, 3, -2, -2, 5]}
        miss = [{'phi': [0, 0, 0, 0]}, {'phi': [0, 0, 0, 0]}]
        solved = {'phi': [0, 2, 5, 3]}

        def restart(seed_change=None, extra=None):
            seed = {'spec': self.immutable_spec(exact), 'receipts': self.fixture_receipts(exact, miss)}
            seed.update(seed_change or {})
            seed.update(extra or {})
            return {'task': exact, 'replies': [*miss, {'restart': {'seed': seed}}, solved]}
        return {
            'exact_restart_repairs': (restart(), 'HOST_CERTIFIED'),
            'unclosed_typed_refusal': ({'task': unclosed, 'replies': [*miss, {'refusal': {'face': 0}}]},
                                       'TYPED_REFUSAL'),
            'closed_non_exact_lift': ({'task': winding, 'replies': [
                *miss, {'lift': {'h': [0, 0, 0, 1, 0], 'k': 1, 'phi': [0, 2, 5, 3]}}]}, 'HOST_CERTIFIED'),
            'restart_with_changed_claims': (restart({'spec': self.immutable_spec(unclosed)}), 'REFUSED'),
            'restart_seed_carries_history': (restart(extra={'history': miss}), 'REFUSED'),
            'lift_without_closed_witness': ({'task': unclosed, 'replies': [
                *miss, {'lift': {'h': [0, 0, 0, 0, 1], 'k': 1, 'phi': [0, 2, 5, 3]}}]}, 'REFUSED'),
            'false_refusal_on_exact': ({'task': exact, 'replies': [*miss, {'refusal': {'face': 0}}]}, 'REFUSED'),
        }

    def fixture_receipts(self, task, attempts) -> list[str]:
        trail = [{'attempt': t, 'residual': dict(self.assess(task, {}, a).residual)} for t, a in enumerate(attempts)]
        return self.receipts(task, trail)
