"""Layer 4 families: dialects, staged packets, crosswalks, witnesses, rewriting, custody, checkers, presets."""
from __future__ import annotations

import base64
import re
from collections.abc import Callable, Mapping
from fractions import Fraction
from typing import Any, ClassVar

from ..fidelity import HostOracleContext, ProtectedContract
from .base import (
    POSITIVE,
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
    sealed_literals,
    spec_from,
)
from .exact import (
    Graph,
    classify_linear,
    commitment,
    det,
    dot,
    matvec,
    mutation_score,
    rank,
    rref,
    seal_chain,
    sha256_bytes,
)
from .layer1 import TypedRefusal
from .registry import register

# ---------------------------------------------------------------- shared helpers (candidates for exact.py)

def jsonable(x: Any) -> Any:
    """Fractions as ints or 'p/q' strings, tuples as lists; the inverse of ``rationals``."""
    if isinstance(x, Fraction):
        return x.numerator if x.denominator == 1 else f'{x.numerator}/{x.denominator}'
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, Mapping):
        return {k: jsonable(v) for k, v in x.items()}
    return x


def rationals(x: Any) -> Any:
    """Parse a JSON payload of ints and 'p/q' strings into Fractions; floats are refused."""
    if isinstance(x, list):
        return [rationals(v) for v in x]
    if isinstance(x, Mapping):
        return {k: rationals(v) for k, v in x.items()}
    return as_fraction(x, 'value')


def linear_task(task: Mapping[str, Any]) -> tuple[list[list[Fraction]], list[Fraction]]:
    require(isinstance(task.get('A'), list) and task['A'] and isinstance(task.get('b'), list), 'A and b required')
    require(all(isinstance(r, list) and len(r) == len(task['A'][0]) for r in task['A'])
            and len(task['b']) == len(task['A']), 'A must be rectangular and match b')
    return [[as_fraction(x, 'A') for x in row] for row in task['A']], [as_fraction(x, 'b') for x in task['b']]


def fenced_contract(text: str, fences: list[tuple[str, str, str]]) -> ProtectedContract:
    """A ProtectedContract with one span per ``(begin, end, name)`` marker pair."""
    try:
        spans = tuple(ProtectedContract.fence_markers(text, b, e, n).fences[0] for b, e, n in fences)
    except ValueError as exc:
        raise MalformedCandidateError(str(exc)) from exc
    return ProtectedContract(text.encode('utf-8'), spans)


# ---------------------------------------------------------------- WF6

def apply_dialect(dialect: Mapping[str, Any], a: list[list[Fraction]], b: list[Fraction]):
    """rho(s): rows permuted and scaled, variables renamed by ``col_perm``, optional shift of b."""
    m, n = len(a), len(a[0])
    rp = dialect.get('row_perm', list(range(m)))
    cp = dialect.get('col_perm', list(range(n)))
    scale = [as_fraction(s, 'row_scale') for s in dialect.get('row_scale', [1] * m)]
    shift = [as_fraction(s, 'b_shift') for s in dialect.get('b_shift', [0] * m)]
    require(sorted(rp) == list(range(m)) and sorted(cp) == list(range(n)), 'permutations required')
    require(len(scale) == m and len(shift) == m, 'one scale and shift per row')
    a2 = [[scale[i] * a[rp[i]][cp[j]] for j in range(n)] for i in range(m)]
    b2 = [scale[i] * b[rp[i]] + shift[i] for i in range(m)]
    return a2, b2, cp


def query(a, b, cp=None):
    """q(s): answerability status and the solution in seed coordinates (decoded through ``cp``)."""
    st = classify_linear(a, b)
    if st.solution is None or cp is None:
        return st.status, st.solution
    x = [Fraction(0)] * len(cp)
    for j, old in enumerate(cp):
        x[old] = st.solution[j]
    return st.status, tuple(x)


@register
class DialectSweep(WorkflowFamily):
    """WF6. Pose each seed item in k query-preserving dialects and grade every reply with one checker.

    Items are linear systems ``A x = b``. A dialect permutes and scales rows and renames variables;
    the host checks ``decode(rho_k(s)) = q(s)`` (same rank-test status, same decoded solution) before
    anything is dispatched, then grades each capsule with the WF7 checker and reports acceptance per
    dialect, item by item. A dialect that changes the query or an incomplete sweep is refused.
    """
    spec = spec_from('WF6', 'Dialect sweep', 4, ['WF5'], 'Sweep', 'dialect_query_preservation_sweep',
                     'wf06_dialect_sweep')

    def validate(self, task):
        require(isinstance(task.get('items'), list) and task['items'], 'items required')
        require(isinstance(task.get('dialects'), list) and task['dialects'], 'dialects required')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        capsules, broken = [], []
        for item in task['items']:
            a, b = linear_task(item)
            seed = query(a, b)
            for d in task['dialects']:
                a2, b2, cp = apply_dialect(d, a, b)
                if query(a2, b2, cp) != seed:
                    broken.append([item['id'], d['name']])
                capsules.append((item['id'], d['name'], {'A': jsonable(a2), 'b': jsonable(b2)}))
        if not host.record('dialects_preserve_query', not broken, str(broken)):
            return refused('DIALECT_CHANGES_QUERY', broken=broken)
        grader, table = TypedRefusal(), {}
        for item_id, name, enc in capsules:
            reply = session.ask(f'{item_id}:{name}', f'{task["statement"]}\n' + canonical(enc).decode('utf-8'))
            if reply is None:
                table.setdefault(item_id, {})[name] = None
                continue
            try:
                ok = grader.check(enc, {}, reply.content, HostOracleContext()).verdict in POSITIVE
            except MalformedCandidateError:
                ok = False
            table.setdefault(item_id, {})[name] = ok
        missing = [[i, n] for i, row in table.items() for n, v in row.items() if v is None]
        if not host.record('every_capsule_graded_once', not missing, str(missing)):
            return refused('INCOMPLETE_SWEEP', missing=missing)
        names = [d['name'] for d in task['dialects']]
        acceptance = {n: jsonable(Fraction(sum(row[n] for row in table.values()), len(table))) for n in names}
        flips = [[i, n] for i, row in table.items() for n in names[1:] if row[n] != row[names[0]]]
        return judge(host, 'SWEEP_GRADED', acceptance=acceptance, items=table, flips_vs_first=flips)

    def fixtures(self):
        items = [{'id': 'i1', 'A': [[1, 2], [3, 4]], 'b': [5, 6]}, {'id': 'i2', 'A': [[1, 1], [2, 2]], 'b': [1, 3]}]
        plain = {'name': 'plain'}
        swapped = {'name': 'swapped', 'row_perm': [1, 0], 'col_perm': [1, 0], 'row_scale': [3, '-1/2']}
        st = 'Solve A x = b exactly or refuse with a code.'
        task = {'statement': st, 'items': items, 'dialects': [plain, swapped]}
        refuse = {'refusal': 'UNRESOLVED_INCONSISTENT'}
        good = [{'answer': [-4, '9/2']}, {'answer': ['9/2', -4]}, refuse, refuse]
        undecoded = [good[0], {'answer': [-4, '9/2']}, refuse, refuse]
        zero = {'name': 'zero_row', 'row_scale': [0, 1]}
        shifted = {'name': 'shifted', 'b_shift': [1, 0]}
        return {
            'all_dialects_accepted': ({'task': task, 'replies': good}, 'HOST_CERTIFIED'),
            'one_dialect_fails_item_by_item': ({'task': task, 'replies': undecoded}, 'HOST_CERTIFIED'),
            'dialect_zeroes_a_row': ({'task': {**task, 'dialects': [plain, zero]}, 'replies': good}, 'REFUSED'),
            'dialect_shifts_rhs': ({'task': {**task, 'dialects': [plain, shifted]}, 'replies': good}, 'REFUSED'),
            'incomplete_sweep': ({'task': task, 'replies': good[:3]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF8

def build_packets(seed: Any, stages: list[str], payloads: list[Any], carry: str) -> list[dict[str, Any]]:
    """Honest packets for ``payloads``: each carries the fenced text and links into the seal chain."""
    chain = seal_chain(seed, payloads)
    return [{'stage': s, 'carry': carry, 'payload': p, 'prev': chain[i], 'seal': chain[i + 1]}
            for i, (s, p) in enumerate(zip(stages, payloads, strict=True))]


def _eliminate(task, _prev):
    a, b = linear_task(task)
    return rref([[*row, bi] for row, bi in zip(a, b, strict=True)])[0]


def _solve(task, prev):
    return [row[-1] for row in prev[:len(task['A'][0])]]


def _residual(task, prev):
    a, b = linear_task(task)
    return [ax - bi for ax, bi in zip(matvec(a, prev), b, strict=True)]


@register
class StagedSealedPackets(WorkflowFamily):
    """WF8. Run a task as declared stages; seal each stage packet before the next stage reads it.

    Stage i returns ``{stage, carry, payload, prev, seal}``. The host checks that ``carry`` holds the
    fenced question byte for byte (ProtectedContract), that ``prev = h_{i-1}``, that
    ``seal = H(h_{i-1} || payload)`` (exact.seal_chain over the task seed), and recomputes the stage
    from the previous verified payload. Instance: eliminate, solve, residual for ``A x = b``.
    Subclasses override ``stages``, ``same_payload`` and ``final_check``.
    """
    spec = spec_from('WF8', 'Staged sealed packets', 4, ['WF2', 'WF5'], None, 'stage_seal_chain_recompute',
                     'wf08_staged_sealed_packets')
    fence: ClassVar[tuple[str, str, str]] = ('<<Q>>', '<</Q>>', 'question')
    FIELDS: ClassVar[frozenset[str]] = frozenset({'stage', 'carry', 'payload', 'prev', 'seal'})

    def stages(self, task) -> list[tuple[str, Callable[[Mapping[str, Any], Any], Any]]]:
        return [('eliminate', _eliminate), ('solve', _solve), ('residual', _residual)]

    def contract(self, task) -> ProtectedContract:
        return fenced_contract(task['statement'], [self.fence])

    def validate(self, task):
        a, b = linear_task(task)
        require(classify_linear(a, b).status == 'unique', 'the staged instance needs a unique solution')
        self.contract(task)
        return task

    def same_payload(self, expected, got) -> bool:
        return rationals(jsonable(expected)) == rationals(got)

    def final_check(self, task, payloads, host) -> None:
        a, b = linear_task(task)
        host.record('answer_is_unique_solution', tuple(rationals(payloads[1])) == classify_linear(a, b).solution,
                    canonical(payloads[1]).decode('utf-8'))
        host.record('final_residual_zero', not any(rationals(payloads[-1])), canonical(payloads[-1]).decode('utf-8'))

    def check_packet(self, task, contract, name, fn, accepted, packet, host) -> str | None:
        """Record this stage's predicates; return the first failure code or None."""
        require(isinstance(packet, Mapping) and set(packet) >= self.FIELDS, 'packet fields missing')
        prev = seal_chain(task, accepted)[-1]
        expected = fn(task, rationals(accepted[-1]) if accepted else None)
        checks = [
            ('stage_named', packet['stage'] == name, 'STAGE_MISNAMED'),
            ('fence_intact', isinstance(packet['carry'], str) and not contract.violations(packet['carry']),
             'FENCE_VIOLATED'),
            ('chain_linked', packet['prev'] == prev, 'CHAIN_BROKEN'),
            ('seal_matches', packet['seal'] == seal_chain(task, [*accepted, packet['payload']])[-1], 'SEAL_MISMATCH'),
            ('recomputed', self.same_payload(expected, packet['payload']), 'STAGE_RECOMPUTE_MISMATCH'),
        ]
        failed = [code for key, ok, code in checks if not host.record(f'{name}:{key}', ok, canonical(packet).decode())]
        return failed[0] if failed else None

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task, accepted, last = session.task, [], None
        contract = self.contract(task)
        for name, fn in self.stages(task):
            note = '' if last is None else '\nPrevious sealed packet: ' + canonical(last).decode('utf-8')
            reply = session.ask(f'stage:{name}', self.prompt(task) + f'\nStage {name}.' + note)
            if reply is None:
                host.record(f'{name}:packet_received', False)
                return refused('STAGE_MISSING', stage=name)
            code = self.check_packet(task, contract, name, fn, accepted, reply.content, host)
            if code:
                return refused(code, stage=name, sealed_stages=len(accepted))
            accepted.append(reply.content['payload'])
            last = reply.content
        self.final_check(task, accepted, host)
        return judge(host, 'SEALED_PIPELINE', stages=len(accepted), head=seal_chain(task, accepted)[-1])

    def fixtures(self):
        q = '<<Q>>Solve A x = b for x with A = [[2, 1], [1, 3]], b = [3, 5].<</Q>>'
        task = {'statement': q + ' Work in three sealed stages.', 'A': [[2, 1], [1, 3]], 'b': [3, 5]}
        names = ['eliminate', 'solve', 'residual']
        payloads = [[[1, 0, '4/5'], [0, 1, '7/5']], ['4/5', '7/5'], [0, 0]]
        honest = build_packets(task, names, payloads, q)
        edited = [honest[0], {**honest[1], 'payload': ['1', '1/3']}, honest[2]]
        broken = [honest[0], {**honest[1], 'prev': honest[0]['prev']}, honest[2]]
        no_fence = [honest[0], {**honest[1], 'carry': 'Solve A x = b.'}, honest[2]]
        wrong = build_packets(task, names, [payloads[0], ['1', '1/3'], [0, 0]], q)
        return {
            'three_sealed_stages': ({'task': task, 'replies': honest}, 'HOST_CERTIFIED'),
            'packet_edited_after_seal': ({'task': task, 'replies': edited}, 'REFUSED'),
            'chain_link_broken': ({'task': task, 'replies': broken}, 'REFUSED'),
            'fence_dropped_from_packet': ({'task': task, 'replies': no_fence}, 'REFUSED'),
            'sealed_but_wrong_stage': ({'task': task, 'replies': wrong}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF16

@register
class SubstrateCrosswalk(WorkflowFamily):
    """WF16. Map one finite task between two substrates and require the same host verdict in both.

    Source: an edge cochain ``c`` on an oriented graph (exact iff every fundamental cycle sum is 0).
    Target: a signed incidence matrix ``D`` and vector ``y`` (exact iff ``rank D = rank [D|y]``).
    A crosswalk maps vertices to columns and edges to signed rows; the host checks it is bijective,
    preserves every incidence relation and transports ``c`` to ``y``, and records where valid
    crosswalks differ (non-unique choices). A broken relation or a verdict mismatch is refused.
    """
    spec = spec_from('WF16', 'Substrate crosswalk', 4, ['WF5', 'WF10'], 'WF5', 'incidence_rank_crosswalk',
                     'wf16_substrate_crosswalk')

    def validate(self, task):
        require(all(isinstance(task.get(k), list) for k in ('edges', 'c', 'D', 'y')), 'edges, c, D, y required')
        return task

    def check(self, task, sealed, content, host):
        g = Graph.of(task['edges'])
        verts, c = g.vertices, [as_fraction(x, 'c') for x in task['c']]
        d = [[as_fraction(x, 'D') for x in row] for row in task['D']]
        y = [as_fraction(x, 'y') for x in task['y']]
        source = g.is_exact(c)
        target = rank(d) == rank([[*row, yi] for row, yi in zip(d, y, strict=True)])
        host.record('verdicts_identical', source == target, f'{source}|{target}')
        require(isinstance(content, Mapping) and isinstance(content.get('crosswalks'), list)
                and content['crosswalks'], 'crosswalks required')
        maps = []
        for k, f in enumerate(content['crosswalks']):
            require(isinstance(f, Mapping) and isinstance(f.get('vertex_col'), Mapping)
                    and isinstance(f.get('edge_row'), Mapping), 'vertex_col and edge_row maps required')
            cols = {v: as_int(f['vertex_col'].get(v), 'column') for v in verts}
            rows = {i: f['edge_row'].get(str(i)) for i in range(len(g.edges))}
            require(all(isinstance(r, list) and len(r) == 2 for r in rows.values()), 'edge_row entries are [row, sign]')
            rows = {i: (as_int(r, 'row'), as_int(s, 'sign')) for i, (r, s) in rows.items()}
            bij = (sorted(cols.values()) == list(range(len(verts))) and len(d) == len(rows)
                   and sorted(r for r, _ in rows.values()) == list(range(len(d)))
                   and all(s in (1, -1) for _, s in rows.values()))
            if not host.record(f'crosswalk{k}:bijective', bij, canonical(f).decode('utf-8')):
                continue
            image = {}
            for i, (u, v) in enumerate(g.edges):
                r, s = rows[i]
                image[i] = [s * ((j == cols[v]) - (j == cols[u])) for j in range(len(verts))]
            host.record(f'crosswalk{k}:relations_preserved', all(image[i] == d[rows[i][0]] for i in image),
                        canonical(f).decode('utf-8'))
            host.record(f'crosswalk{k}:data_transported', all(y[r] == s * c[i] for i, (r, s) in rows.items()),
                        canonical(f).decode('utf-8'))
            maps.append((cols, rows))
        choices = [{'flipped_edges': [i for i, (_, s) in rows.items() if s == -1]} for _, rows in maps]
        differ = [[v for v in verts if maps[0][0][v] != m[0][v]] for m in maps[1:]]
        return judge(host, 'CROSSWALK_PRESERVED', verdict='exact' if source else 'not_exact', choices=choices,
                     differ_on_vertices=differ)

    def fixtures(self):
        task = {'statement': 'Map the graph cochain onto the incidence matrix: vertex -> column, edge -> [row, sign].',
                'edges': [['a', 'b'], ['b', 'c'], ['c', 'd'], ['d', 'a']], 'c': [1, -1, 1, -1],
                'D': [[0, -1, 0, 1], [1, 0, -1, 0], [0, -1, 1, 0], [1, 0, 0, -1]], 'y': [-1, 1, -1, 1]}
        f1 = {'vertex_col': {'a': 2, 'b': 0, 'c': 3, 'd': 1}, 'edge_row': {'0': [1, 1], '1': [3, -1], '2': [0, -1],
                                                                          '3': [2, 1]}}
        f2 = {'vertex_col': {'a': 3, 'b': 1, 'c': 2, 'd': 0}, 'edge_row': {'0': [0, -1], '1': [2, 1], '2': [1, 1],
                                                                          '3': [3, -1]}}
        bad_sign = {**f1, 'edge_row': {**f1['edge_row'], '2': [0, 1]}}
        clash = {**f1, 'vertex_col': {**f1['vertex_col'], 'd': 2}}
        return {
            'one_crosswalk_preserves': ({'task': task, 'replies': [{'crosswalks': [f1]}]}, 'HOST_CERTIFIED'),
            'two_crosswalks_non_unique': ({'task': task, 'replies': [{'crosswalks': [f1, f2]}]}, 'HOST_CERTIFIED'),
            'orientation_sign_dropped': ({'task': task, 'replies': [{'crosswalks': [bad_sign]}]}, 'REFUSED'),
            'two_vertices_one_column': ({'task': task, 'replies': [{'crosswalks': [clash]}]}, 'REFUSED'),
            'target_data_not_transported': ({'task': {**task, 'y': [-1, 1, -1, 3]},
                                             'replies': [{'crosswalks': [f1]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF17

def hml(lts: Mapping[str, list[tuple[str, str]]], state: str, formula: Any, depth: int = 0) -> bool:
    """Hennessy-Milner logic: 'tt', 'ff', ['not', f], ['and'|'or', f, g], ['dia'|'box', label, f]."""
    require(depth <= 12, 'formula too deep')
    if formula in ('tt', 'ff'):
        return formula == 'tt'
    require(isinstance(formula, list) and formula and formula[0] in ('not', 'and', 'or', 'dia', 'box'),
            f'unknown formula {formula!r}')
    op, args = formula[0], formula[1:]
    if op == 'not':
        require(len(args) == 1, 'not takes one formula')
        return not hml(lts, state, args[0], depth + 1)
    require(len(args) == 2, f'{op} takes two arguments')
    if op in ('and', 'or'):
        vals = [hml(lts, state, f, depth + 1) for f in args]
        return all(vals) if op == 'and' else any(vals)
    succ = [hml(lts, t, args[1], depth + 1) for lab, t in lts.get(state, []) if lab == args[0]]
    return any(succ) if op == 'dia' else all(succ)


def is_bisimulation(lts: Mapping[str, list[tuple[str, str]]], rel: set[tuple[str, str]]) -> bool:
    """Every move of either side is matched by a move with the same label into a related pair."""
    def matched(p, q, flip):
        return all(any(lab == lab2 and ((q2, p2) if flip else (p2, q2)) in rel for lab2, q2 in lts.get(q, []))
                   for lab, p2 in lts.get(p, []))
    return all(matched(p, q, False) and matched(q, p, True) for p, q in rel)


@register
class WitnessedDifferenceProgramme(WorkflowFamily):
    """WF17. Every claimed difference needs a separating formula; every equivalence needs a bisimulation.

    Instance: a finite labelled transition system (a.(b+c) versus a.b+a.c, and a.b versus a.b+a.b).
    A difference claim is accepted only if a Hennessy-Milner formula holds on one state and fails on
    the other; an equivalence only if the given relation contains the pair and is a bisimulation.
    Unwitnessed claims, non-separating formulas and false bisimulations are refused.
    """
    spec = spec_from('WF17', 'Witnessed-difference programme', 4, ['WF10', 'WF11'], 'WF10',
                     'hml_separator_bisimulation_check', 'wf17_witnessed_difference_programme')

    def validate(self, task):
        require(isinstance(task.get('transitions'), list), 'transitions required')
        return task

    def check(self, task, sealed, content, host):
        lts: dict[str, list[tuple[str, str]]] = {}
        for t in task['transitions']:
            lts.setdefault(t[0], []).append((t[1], t[2]))
        require(isinstance(content, Mapping) and isinstance(content.get('claims'), list) and content['claims'],
                'claims required')
        for k, claim in enumerate(content['claims']):
            require(isinstance(claim, Mapping) and claim.get('kind') in ('difference', 'equivalence'), 'claim kind')
            p, q, ev = claim.get('left'), claim.get('right'), canonical(claim).decode('utf-8')
            if claim['kind'] == 'difference':
                if not host.record(f'claim{k}:witnessed', 'witness' in claim, ev):
                    continue
                host.record(f'claim{k}:separates', hml(lts, p, claim['witness']) != hml(lts, q, claim['witness']), ev)
            else:
                if not host.record(f'claim{k}:witnessed', isinstance(claim.get('certificate'), list), ev):
                    continue
                rel = {(x[0], x[1]) for x in claim['certificate'] if isinstance(x, list) and len(x) == 2}
                host.record(f'claim{k}:bisimulation', (p, q) in rel and is_bisimulation(lts, rel), ev)
        return judge(host, 'CLAIMS_WITNESSED', claims=len(content['claims']))

    def fixtures(self):
        tr = [['p0', 'a', 'p1'], ['p1', 'b', 'p2'], ['p1', 'c', 'p3'],
              ['q0', 'a', 'q1'], ['q0', 'a', 'q2'], ['q1', 'b', 'q3'], ['q2', 'c', 'q4'],
              ['r0', 'a', 'r1'], ['r1', 'b', 'r2'],
              ['s0', 'a', 's1'], ['s0', 'a', 's2'], ['s1', 'b', 's3'], ['s2', 'b', 's4']]
        task = {'statement': 'Claim differences with a separating formula and equivalences with a bisimulation.',
                'transitions': tr}
        diff = {'kind': 'difference', 'left': 'p0', 'right': 'q0',
                'witness': ['dia', 'a', ['and', ['dia', 'b', 'tt'], ['dia', 'c', 'tt']]]}
        equiv = {'kind': 'equivalence', 'left': 'r0', 'right': 's0',
                 'certificate': [['r0', 's0'], ['r1', 's1'], ['r1', 's2'], ['r2', 's3'], ['r2', 's4']]}
        weak = {**diff, 'witness': ['dia', 'a', ['dia', 'b', 'tt']]}
        fake = {'kind': 'equivalence', 'left': 'p0', 'right': 'q0',
                'certificate': [['p0', 'q0'], ['p1', 'q1'], ['p1', 'q2'], ['p2', 'q3'], ['p3', 'q4']]}
        bare = {'kind': 'difference', 'left': 'p0', 'right': 'q0'}
        return {
            'difference_and_equivalence_witnessed': ({'task': task, 'replies': [{'claims': [diff, equiv]}]},
                                                     'HOST_CERTIFIED'),
            'unwitnessed_difference': ({'task': task, 'replies': [{'claims': [bare, equiv]}]}, 'REFUSED'),
            'formula_does_not_separate': ({'task': task, 'replies': [{'claims': [weak]}]}, 'REFUSED'),
            'trace_equivalent_is_not_bisimilar': ({'task': task, 'replies': [{'claims': [fake]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF21

@register
class StructuralPromptRewriting(WorkflowFamily):
    """WF21. Rewrite a prompt only outside its protected fences, then solve the rewritten prompt.

    A rewrite is a list of rule applications ``{lhs, rhs, at}``: the match must be exact and the
    matches pairwise disjoint (an injective match), and each edit goes through
    ProtectedContract.apply_edit, which refuses any edit inside the question or output fence. The
    result must carry each fence exactly once and no answer-key literal; only then is it dispatched
    and the answer judged exactly (a 2x2 determinant).
    """
    spec = spec_from('WF21', 'Structural prompt rewriting', 4, ['WF5'], 'WF5', 'fenced_rewrite_exact_judge',
                     'wf21_structural_prompt_rewriting')
    FENCES: ClassVar[list[tuple[str, str, str]]] = [('<<Q>>', '<</Q>>', 'question'),
                                                    ('<<OUT>>', '<</OUT>>', 'output')]

    def validate(self, task):
        fenced_contract(task['statement'], self.FENCES)
        require(isinstance(task.get('matrix'), list), 'matrix required')
        return task

    def rewrite(self, task, sealed, content, host) -> bytes | Verdict:
        contract = fenced_contract(task['statement'], self.FENCES)
        data = contract.task_bytes
        require(isinstance(content, Mapping) and isinstance(content.get('edits'), list), 'edits list required')
        edits = []
        for e in content['edits']:
            require(isinstance(e, Mapping) and isinstance(e.get('lhs'), str) and e['lhs']
                    and isinstance(e.get('rhs'), str), 'edits are {lhs, rhs, at}')
            at = as_int(e.get('at'), 'at')
            edits.append((at, at + len(e['lhs'].encode('utf-8')), e['lhs'].encode('utf-8'), e['rhs'].encode('utf-8')))
        edits.sort()
        if not host.record('matches_exact', all(data[s:t] == lhs for s, t, lhs, _ in edits), str(edits)):
            return refused('NO_MATCH')
        disjoint = all(a[1] <= b[0] for a, b in zip(edits, edits[1:], strict=False))
        if not host.record('match_injective', disjoint, str(edits)):
            return refused('OVERLAPPING_MATCHES')
        try:
            for s, t, _, rhs in edits:
                contract.apply_edit(s, t, rhs)
        except PermissionError as exc:
            host.record('edits_outside_fences', False, str(exc))
            return refused('EDIT_INSIDE_FENCE')
        host.record('edits_outside_fences', True, str(edits))
        out = data
        for s, t, _, rhs in reversed(edits):
            out = out[:s] + rhs + out[t:]
        if not host.record('protected_bytes_unchanged', not contract.violations(out), out.decode('utf-8')):
            return refused('QUESTION_NOT_PRESERVED', violations=contract.violations(out))
        keys = sealed_literals(sealed) | {str(sealed.get('answer_key'))}
        leaks = sorted(k for k in keys if k.encode('utf-8') in out)
        if not host.record('no_answer_key_leak', not leaks, str(len(leaks))):
            return refused('ANSWER_KEY_LEAK')
        return out

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task, sealed = session.task, session.sealed
        reply = session.ask('rewrite', self.prompt(task))
        if reply is None:
            return refused('NO_ADMISSIBLE_REPLY')
        out = self.rewrite(task, sealed, reply.content, host)
        if isinstance(out, Verdict):
            return out
        answer = session.ask('solve', out.decode('utf-8'))
        if answer is None:
            return refused('NO_ADMISSIBLE_REPLY')
        require(isinstance(answer.content, Mapping), 'answer must be an object')
        value = as_fraction(answer.content.get('answer'), 'answer')
        truth = det([[as_fraction(x, 'matrix') for x in r] for r in task['matrix']])
        host.record('answer_key_consistent', truth == as_fraction(sealed['answer_key'], 'answer_key'), '')
        host.record('answer_exact', value == truth, str(value))
        return judge(host, 'REWRITE_CERTIFIED', rewritten_sha256=sha256_bytes(out))

    def fixtures(self):
        st = ('Please read the task.\n<<Q>>Compute det(M) for M = [[12, 5], [7, 263]].<</Q>>\n'
              '<<OUT>>Reply as {"answer": <int>}.<</OUT>>\nPlease be concise.')
        task = {'statement': st, 'matrix': [[12, 5], [7, 263]]}
        sealed = {'answer_key': 3121}
        tail = st.index('Please be concise.')
        clean = {'edits': [{'lhs': 'Please read the task.', 'rhs': 'Read the task below.', 'at': 0},
                           {'lhs': 'Please be concise.', 'rhs': 'Keep the reply short.', 'at': tail}]}
        inside = {'edits': [{'lhs': '263', 'rhs': '264', 'at': st.index('263')}]}
        leak = {'edits': [{'lhs': 'Please be concise.', 'rhs': 'Hint: it is 3121.', 'at': tail}]}
        overlap = {'edits': [{'lhs': 'Please', 'rhs': 'Kindly', 'at': 0},
                             {'lhs': 'Please read', 'rhs': 'Read', 'at': 0}]}
        dup = {'edits': [{'lhs': 'Please be concise.', 'rhs': st[st.index('<<Q>>'):st.index('<</Q>>') + 6],
                          'at': tail}]}
        ok = {'answer': 3121}

        def case(rewrite):
            return {'task': task, 'sealed': sealed, 'replies': [rewrite, ok]}
        return {
            'rewrite_outside_fences_solved': (case(clean), 'HOST_CERTIFIED'),
            'edit_inside_question_fence': (case(inside), 'REFUSED'),
            'rewrite_leaks_answer_key': (case(leak), 'REFUSED'),
            'overlapping_matches': (case(overlap), 'REFUSED'),
            'question_duplicated_outside_fence': (case(dup), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF23

def canonical_file(text: str) -> bytes:
    """File bytes as hashed by custody: UTF-8, LF line endings."""
    return text.replace('\r\n', '\n').encode('utf-8')


def derivable_views(text: str):
    """Participant text plus the views a reader derives trivially: reversed, unspaced, base64, hex."""
    yield text
    yield text[::-1]
    yield ''.join(text.split())
    for tok in re.findall(r'[A-Za-z0-9+/=]{4,}', text):
        for decode in (lambda t: base64.b64decode(t, validate=True), bytes.fromhex):
            try:
                yield decode(tok).decode('utf-8')
            except ValueError:
                continue


@register
class JudgePacketCustodyAudit(WorkflowFamily):
    """WF23. Audit a judge run: file hashes, answer-free participant bytes, sealed checker, stdout tags.

    The submission carries the participant files, their manifest and the judge run record. The host
    hashes every canonicalised file against the manifest, scans participant bytes and their trivial
    decodings for the sealed expected answer, checks the executed checker hash equals the recorded
    hash of the sealed checker source, and checks every stdout line's keyed tag. Leaks, stale
    checkers, edited files and forged stdout lines are refused. ``audit`` is reusable by later gates.
    """
    spec = spec_from('WF23', 'Judge-packet custody audit', 4, ['WF11'], None, 'judge_packet_custody_audit',
                     'wf23_judge_packet_custody_audit')
    stage = 'packet'

    def audit(self, sealed, content, host) -> Verdict:
        require(isinstance(content, Mapping) and all(isinstance(content.get(k), Mapping)
                                                     for k in ('participant', 'manifest', 'run')), 'packet fields')
        files, manifest, run = content['participant'], content['manifest'], content['run']
        require(all(isinstance(v, str) for v in files.values()), 'participant files are text')
        hashes = {name: sha256_bytes(canonical_file(text)) for name, text in files.items()}
        host.record('manifest_complete', set(manifest) == set(files), canonical(sorted(manifest)).decode())
        host.record('file_hashes_match', all(manifest.get(n) == h for n, h in hashes.items()),
                    canonical(hashes).decode())
        answer = as_fraction(sealed['expected_answer'], 'expected_answer')
        form = str(answer)
        leaked = sorted(n for n, text in files.items() if any(form in v for v in derivable_views(text)))
        host.record('answer_not_derivable', not leaked, str(leaked))
        recorded = sealed['recorded_checker_sha256']
        host.record('recorded_hash_is_checker', recorded == sha256_bytes(canonical_file(sealed['checker_source'])), '')
        host.record('executed_checker_is_recorded', run.get('executed_checker_sha256') == recorded, '')
        lines = run.get('stdout', [])
        require(isinstance(lines, list) and all(isinstance(x, Mapping) for x in lines), 'stdout is a list of lines')
        forged = [x.get('line') for x in lines if x.get('tag') != commitment(sealed['stdout_key'], x.get('line'))]
        host.record('stdout_lines_authentic', bool(lines) and not forged, str(len(forged)))
        return judge(host, 'CUSTODY_INTACT', participant_sha256=digest(hashes), leaked_files=leaked,
                     forged_lines=len(forged))

    def check(self, task, sealed, content, host):
        return self.audit(sealed, content, host)

    def fixtures(self):
        task = {'statement': 'Submit the participant packet, its manifest and the judge run record.'}
        src = 'def check(answer):\r\n    return answer == det([[12, 5], [7, 263]])\r\n'
        key = 'stdout-key-wf23'
        sealed = {'expected_answer': 3121, 'checker_source': src,
                  'recorded_checker_sha256': sha256_bytes(canonical_file(src)), 'stdout_key': key}
        files = {'task.txt': 'Compute det(M) for M = [[12, 5], [7, 263]].', 'format.txt': 'Reply with one integer.'}
        manifest = {n: sha256_bytes(canonical_file(t)) for n, t in files.items()}
        line = 'ITEM det2 PASS'
        run = {'executed_checker_sha256': sealed['recorded_checker_sha256'],
               'stdout': [{'line': line, 'tag': commitment(key, line)}]}
        good = {'participant': files, 'manifest': manifest, 'run': run}

        def with_file(text):
            f = {**files, 'notes.txt': text}
            return {**good, 'participant': f, 'manifest': {n: sha256_bytes(canonical_file(t)) for n, t in f.items()}}
        forged = {**good, 'run': {**run, 'stdout': [*run['stdout'], {'line': 'ITEM det3 PASS', 'tag': '0' * 64}]}}
        stale = {**good, 'run': {**run, 'executed_checker_sha256': sha256_bytes(b'def check(answer): return True')}}
        edited = {**good, 'participant': {**files, 'format.txt': 'Reply with one integer or a guess.'}}

        def case(sub):
            return {'task': task, 'sealed': sealed, 'replies': [sub]}
        return {
            'clean_custody': (case(good), 'HOST_CERTIFIED'),
            'answer_in_participant_bytes': (case(with_file('Hint: the answer is 3121.')), 'REFUSED'),
            'answer_base64_encoded': (case(with_file('cache: MzEyMQ==')), 'REFUSED'),
            'forged_stdout_line': (case(forged), 'REFUSED'),
            'stale_checker_executed': (case(stale), 'REFUSED'),
            'file_edited_after_manifest': (case(edited), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF29

def potential_atoms(g: Graph) -> dict[str, Callable[[Mapping[str, Any]], bool]]:
    """Declared predicates over a case ``{'c': edge values, 'phi': vertex potential}``."""
    verts = g.vertices

    def edge_values(case):
        return [as_fraction(x, 'c') for x in case['c']]
    return {
        'c_length_matches': lambda case: len(case['c']) == len(g.edges),
        'phi_covers_vertices': lambda case: set(case['phi']) == set(verts),
        'coboundary_matches': lambda case: g.coboundary(
            {v: as_fraction(case['phi'][v], 'phi') for v in verts}) == edge_values(case),
        'cycle_sums_zero': lambda case: g.is_exact(edge_values(case)),
        'phi_root_zero': lambda case: as_fraction(case['phi'][verts[0]], 'phi') == 0,
    }


def compile_checker(tree: Any, atoms: Mapping[str, Callable[[Any], bool]], depth: int = 0) -> Callable[[Any], bool]:
    """Interpret the checker DSL (atom names, ['and'|'or', ...], ['not', x]); nothing is executed."""
    require(depth <= 6, 'checker too deep')
    if isinstance(tree, str):
        require(tree in atoms, f'unknown predicate {tree!r}')
        return atoms[tree]
    require(isinstance(tree, list) and len(tree) >= 2 and tree[0] in ('and', 'or', 'not'), f'bad checker {tree!r}')
    parts = [compile_checker(t, atoms, depth + 1) for t in tree[1:]]
    if tree[0] == 'not':
        require(len(parts) == 1, 'not takes one checker')
        return lambda x: not parts[0](x)
    combine = all if tree[0] == 'and' else any
    return lambda x: combine(p(x) for p in parts)


@register
class CheckerSynthesisMutationKill(WorkflowFamily):
    """WF29. Score a proposed checker by its mutation kill rate, after it passes every valid case.

    The declared certificate is a vertex potential ``phi`` with ``delta phi = c`` on a fixed graph. The
    checker is a tree over declared predicates (never model code). The host runs it on the public
    valid panel and the sealed hostile mutants with exact.mutation_score, and certifies only a sound
    checker (zero false rejections) whose kill rate meets the declared bar.
    """
    spec = spec_from('WF29', 'Checker synthesis scored by mutation kill rate', 4, ['WF11'], 'WF11',
                     'mutation_kill_rate_with_valid_panel', 'wf29_checker_synthesis_scored_by_mutation_kill_rate')

    def validate(self, task):
        require(isinstance(task.get('edges'), list) and isinstance(task.get('valid'), list), 'edges, valid required')
        as_fraction(task.get('min_kill_rate'), 'min_kill_rate')
        return task

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and 'checker' in content, 'checker required')
        checker = compile_checker(content['checker'], potential_atoms(Graph.of(task['edges'])))
        score = mutation_score(checker, task['valid'], sealed.get('mutants', []))
        host.record('no_false_rejection', score.sound, str(score.false_rejections))
        host.record('kill_rate_meets_bar', score.kill_rate >= as_fraction(task['min_kill_rate'], 'bar'),
                    str(score.kill_rate))
        return judge(host, 'CHECKER_ACCEPTED', kill_rate=jsonable(score.kill_rate),
                     false_rejections=score.false_rejections, mutants=score.mutants_total)

    def fixtures(self):
        phi = {'a': 0, 'b': 1, 'c': 3, 'd': 7}
        task = {'statement': 'Write a checker for "phi is a potential of c" from the declared predicates.',
                'edges': [['a', 'b'], ['b', 'c'], ['c', 'a'], ['c', 'd']], 'min_kill_rate': '4/5',
                'predicates': sorted(potential_atoms(Graph.of([['a', 'b']]))),
                'valid': [{'c': [1, 2, -3, 4], 'phi': phi},
                          {'c': [1, 2, -3, 4], 'phi': {k: v + 5 for k, v in phi.items()}},
                          {'c': [0, -2, 2, -1], 'phi': {'a': 2, 'b': 2, 'c': 0, 'd': -1}}]}
        mutants = [{'c': [1, 2, -3, 4], 'phi': {**phi, 'b': 2}}, {'c': [1, 2, -2, 4], 'phi': phi},
                   {'c': [1, 2, -3, 4], 'phi': {'a': 0, 'b': 1, 'c': 3}}, {'c': [1, 2, -3, 4, 0], 'phi': phi},
                   {'c': [1, 2, -3, 4], 'phi': {'a': 0, 'b': 0, 'c': 0, 'd': 0}}]

        def case(checker):
            return {'task': task, 'sealed': {'mutants': mutants}, 'replies': [{'checker': checker}]}
        return {
            'sound_checker_kills_all': (case(['and', 'c_length_matches', 'phi_covers_vertices',
                                              'coboundary_matches']), 'HOST_CERTIFIED'),
            'root_gauge_falsely_rejects': (case(['and', 'phi_root_zero', 'coboundary_matches']), 'REFUSED'),
            'cycle_only_checker_too_weak': (case('cycle_sums_zero'), 'REFUSED'),
            'model_code_not_executed': (case('lambda case: True'), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF44

RATIONAL = re.compile(r'-?\d+(/[1-9]\d*)?')
FLOATISH = re.compile(r'[-+]?(\d*\.\d*|\d+(\.\d*)?[eE][-+]?\d+)')


def _has_float(x: Any) -> bool:
    if isinstance(x, float):
        return True
    if isinstance(x, str):
        return bool(FLOATISH.fullmatch(x))
    if isinstance(x, Mapping):
        return any(_has_float(v) for v in x.values())
    return isinstance(x, list) and any(_has_float(v) for v in x)


def _rational_typed(x: Any) -> bool:
    return type(x) is int or (isinstance(x, str) and bool(RATIONAL.fullmatch(x)))


def _well_typed(kind: str, value: Any, task: Mapping[str, Any]) -> bool:
    """Shape and scalar type only; no equation of the certificate is evaluated here."""
    if kind == 'vertex_map':
        verts = Graph.of(task['edges']).vertices
        return isinstance(value, Mapping) and set(value) == set(verts) and all(map(_rational_typed, value.values()))
    size = len(task['edges']) if kind == 'edge_vector' else len(task['A'][0])
    return isinstance(value, list) and len(value) == size and all(map(_rational_typed, value))


def _check_coboundary(task, cert, host):
    g = Graph.of(task['edges'])
    c = [as_fraction(x, 'c') for x in task['c']]
    host.record('coboundary_matches', g.residual(c, rationals(cert['phi'])) == [0] * len(c), canonical(cert).decode())


def _check_l1_dual(task, cert, host):
    """r = w + B f, B^T z = 0, |z_e| <= cap_e, w . z = sum cap_e |r_e|  (weak duality makes r optimal)."""
    g = Graph.of(task['edges'])
    w = [as_fraction(x, 'w') for x in task['w']]
    cap = [as_fraction(x, 'cap') for x in task.get('cap', [1] * len(w))]
    f, r, z = rationals(cert['f']), rationals(cert['r']), rationals(cert['z'])
    ev = canonical(cert).decode()
    host.record('residual_is_w_plus_Bf', r == [wi + bi for wi, bi in zip(w, g.coboundary(f), strict=True)], ev)
    flow = {v: Fraction(0) for v in g.vertices}
    for (u, v), ze in zip(g.edges, z, strict=True):
        flow[u] -= ze
        flow[v] += ze
    host.record('dual_is_circulation', not any(flow.values()), ev)
    host.record('dual_within_caps', all(abs(ze) <= ce for ze, ce in zip(z, cap, strict=True)), ev)
    host.record('duality_gap_zero', dot(w, z) == sum(ce * abs(re) for ce, re in zip(cap, r, strict=True)), ev)


def _check_canonical(task, cert, host):
    a, b = linear_task(task)
    st = classify_linear(a, b)
    host.record('unique_solution', st.status == 'unique', st.status)
    host.record('values_equal_solution', tuple(rationals(cert['x'])) == st.solution, canonical(cert).decode())
    host.record('canonical_form', all(type(x) is int or x == str(Fraction(x)) for x in cert['x']), str(cert['x']))


CERTIFICATE_PRESETS: dict[str, tuple[dict[str, str], Callable[[Any, Any, HostOracleContext], None]]] = {
    'coboundary_potential': ({'phi': 'vertex_map'}, _check_coboundary),
    'l1_dual_circulation': ({'f': 'vertex_map', 'r': 'edge_vector', 'z': 'edge_vector'}, _check_l1_dual),
    'canonical_rational': ({'x': 'unknown_vector'}, _check_canonical),
}


@register
class ExactCertificatePresets(WorkflowFamily):
    """WF44. Check a certificate against a registered exact schema; type-check before evaluating.

    Presets: a coboundary potential (``delta phi = c``), an l1 primal-dual pair (residual
    ``r = w + B f``, circulation ``z`` with ``B^T z = 0`` and ``|z_e| <= cap_e``, and
    ``w . z = sum cap_e |r_e|``), and a solution in canonical rational form. A certificate with a
    float, a wrong shape or the wrong schema is refused before any equation is evaluated.
    """
    spec = spec_from('WF44', 'Exact certificate presets', 4, ['WF11', 'WF10'], 'WF11', 'exact_certificate_presets',
                     'wf44_exact_certificate_presets')

    def validate(self, task):
        require(task.get('schema') in CERTIFICATE_PRESETS, 'unknown certificate schema')
        return task

    def check(self, task, sealed, content, host):
        require(isinstance(content, Mapping) and isinstance(content.get('certificate'), Mapping), 'certificate')
        fields, evaluate = CERTIFICATE_PRESETS[task['schema']]
        cert = content['certificate']
        if not host.record('no_float', not _has_float(cert), ''):
            return refused('FLOAT_IN_CERTIFICATE')
        typed = (content.get('schema') == task['schema'] and set(cert) == set(fields)
                 and all(_well_typed(kind, cert[name], task) for name, kind in fields.items()))
        if not host.record('well_typed', typed, canonical(content).decode()):
            return refused('ILL_TYPED')
        evaluate(task, cert, host)
        return judge(host, 'CERTIFICATE_VALID', schema=task['schema'])

    def fixtures(self):
        square = [['a', 'b'], ['b', 'c'], ['c', 'd'], ['d', 'a'], ['a', 'c']]
        cob = {'schema': 'coboundary_potential', 'statement': 'Certify that c is exact with a potential.',
               'edges': [['a', 'b'], ['b', 'c'], ['c', 'a']], 'c': [1, 2, -3]}
        l1 = {'schema': 'l1_dual_circulation', 'statement': 'Certify the l1 distance of w to the coboundaries.',
              'edges': square, 'w': [2, 0, 0, 0, 1]}
        rat = {'schema': 'canonical_rational', 'statement': 'Solve A x = b in canonical rational form.',
               'A': [[2, 1], [1, 3]], 'b': [3, 5]}
        dual = {'f': {'a': 0, 'b': -1, 'c': -1, 'd': 0}, 'r': [1, 0, 1, 0, 0], 'z': [1, 1, 1, 1, 0]}

        def case(task, cert, schema=None):
            return {'task': task, 'replies': [{'schema': schema or task['schema'], 'certificate': cert}]}
        return {
            'coboundary_potential_valid': (case(cob, {'phi': {'a': 0, 'b': 1, 'c': 3}}), 'HOST_CERTIFIED'),
            'l1_dual_pair_optimal': (case(l1, dual), 'HOST_CERTIFIED'),
            'canonical_rational_solution': (case(rat, {'x': ['4/5', '7/5']}), 'HOST_CERTIFIED'),
            'non_canonical_rational': (case(rat, {'x': ['8/10', '7/5']}), 'REFUSED'),
            'dual_not_a_circulation': (case(l1, {**dual, 'z': [1, 0, 1, 0, 0]}), 'REFUSED'),
            'ill_typed_short_dual': (case(l1, {**dual, 'z': [1, 1, 1, 1]}), 'REFUSED'),
            'float_in_certificate': (case(l1, {**dual, 'f': {**dual['f'], 'b': -1.0}}), 'REFUSED'),
            'wrong_schema_named': (case(cob, {'phi': {'a': 0, 'b': 1, 'c': 3}}, 'canonical_rational'), 'REFUSED'),
        }
