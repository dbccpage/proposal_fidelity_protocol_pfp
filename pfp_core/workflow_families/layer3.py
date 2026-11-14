"""Layer 3 families: cochain gluing, LP duality and the repair-loop extensions of WF9."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from fractions import Fraction
from typing import Any

from ..fidelity import HostOracleContext
from .base import (
    HostedFamily,
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
from .exact import Graph, dot, matvec, rank, seal_chain, transpose
from .registry import register

# ---------------------------------------------------------------- shared parsing helpers


def parse_graph(edges: Any) -> Graph:
    """Graph on vertices ``0..n-1`` from ``[[u, v], ...]``; vertices must be contiguous ints."""
    require(isinstance(edges, list) and edges, 'edges required')
    pairs = []
    for e in edges:
        require(isinstance(e, list) and len(e) == 2, 'edges are [u, v] pairs')
        pairs.append((as_int(e[0], 'u'), as_int(e[1], 'v')))
    g = Graph.of(pairs)
    require(sorted(g.vertices) == list(range(len(g.vertices))), 'vertices must be 0..n-1')
    return g


def cochain_task(task: Mapping[str, Any]) -> tuple[Graph, list[Fraction]]:
    """``(graph, c)`` for a task carrying ``edges`` and one rational ``labels`` entry per edge."""
    g = parse_graph(task.get('edges'))
    labels = task.get('labels')
    require(isinstance(labels, list) and len(labels) == len(g.edges), 'one label per edge')
    return g, [as_fraction(x, 'label') for x in labels]


def parse_cycle(g: Graph, raw: Any) -> list[tuple[int, int]]:
    """Signed edge list ``[[edge, +1/-1], ...]`` with indices in range."""
    require(isinstance(raw, list) and raw, 'cycle must be a non-empty list')
    out = []
    for item in raw:
        require(isinstance(item, list) and len(item) == 2, 'cycle entries are [edge, sign]')
        i, s = as_int(item[0], 'edge'), as_int(item[1], 'sign')
        require(0 <= i < len(g.edges) and s in (1, -1), 'edge index in range and sign +1/-1')
        out.append((i, s))
    return out


def chain_boundary(g: Graph, chain: Sequence[tuple[int, int]]) -> dict[Any, int]:
    """Nonzero vertex coefficients of the boundary of a signed edge chain."""
    out: dict[Any, int] = {}
    for i, s in chain:
        u, v = g.edges[i]
        out[u] = out.get(u, 0) - s
        out[v] = out.get(v, 0) + s
    return {k: x for k, x in out.items() if x}


def walk_end(g: Graph, start: Any, path: Sequence[tuple[int, int]]) -> Any:
    """End vertex of a signed walk from ``start``; raises if a step does not leave the current vertex."""
    at = start
    for i, s in path:
        u, v = g.edges[i]
        require(at == (u if s == 1 else v), f'edge {i} does not continue the walk')
        at = v if s == 1 else u
    return at


def parse_potential(raw: Any, n: int) -> list[Fraction]:
    require(isinstance(raw, list) and len(raw) == n, 'potential is one rational per vertex')
    return [as_fraction(x, 'potential') for x in raw]


def fmt(x: Fraction) -> str:
    return f'{x.numerator}/{x.denominator}'


# ---------------------------------------------------------------- WF10


@register
class ObstructionCertificate(WorkflowFamily):
    """WF10. Glue local sections of an edge cochain into a global potential, or certify the obstruction.

    Domain: a rational 1-cochain ``c`` on a graph covered by patches that each
    carry a local section. A gluing is a vertex potential with ``c - delta phi = 0``
    on every edge; an obstruction is a closed signed cycle on which ``c`` sums to
    a nonzero value, a nonzero class in ``H^1``. Prose claims, open paths and
    zero-sum cycles are refused. Later families call ``certify_gluing`` and
    ``certify_obstruction`` directly.
    """
    spec = spec_from('WF10', 'Local-to-global obstruction certificate', 3, ['WF4', 'WF9'], 'WF4',
                     'cochain_gluing_or_cycle_obstruction', 'wf10_local_to_global_obstruction_certificate')

    def validate(self, task):
        g, _ = cochain_task(task)
        for patch in task.get('patches', []):
            require(isinstance(patch, list) and all(type(i) is int and 0 <= i < len(g.edges) for i in patch),
                    'patches are lists of edge indices')
        return task

    @staticmethod
    def local_sections(task: Mapping[str, Any], g: Graph, c: Sequence[Fraction]) -> list[bool]:
        """Per patch: is the restriction of ``c`` a coboundary on that patch alone."""
        return [Graph.of([g.edges[i] for i in p]).is_exact([c[i] for i in p]) for p in task.get('patches', [])]

    @staticmethod
    def certify_gluing(g: Graph, c: Sequence[Fraction], phi_raw: Any, host: HostOracleContext,
                       **detail: Any) -> Verdict:
        phi = parse_potential(phi_raw, len(g.vertices))
        support = [i for i, x in enumerate(g.residual(c, dict(enumerate(phi)))) if x]
        host.record('zero_residual_on_every_edge', not support, str(support))
        return judge(host, 'GLUED', residual_support=support, **detail)

    @staticmethod
    def certify_obstruction(g: Graph, c: Sequence[Fraction], cycle_raw: Any, host: HostOracleContext,
                            **detail: Any) -> Verdict:
        cycle = parse_cycle(g, cycle_raw)
        boundary = chain_boundary(g, cycle)
        if not host.record('witness_is_closed_cycle', not boundary, str(boundary)):
            return refused('OPEN_CYCLE_WITNESS', boundary={str(k): v for k, v in boundary.items()}, **detail)
        holonomy = g.cycle_sum(c, cycle)
        if not host.record('nonzero_holonomy', holonomy != 0, fmt(holonomy)):
            return refused('ZERO_HOLONOMY_WITNESS', **detail)
        return typed_refusal('GLOBAL_OBSTRUCTION', holonomy=fmt(holonomy), cycle=[list(x) for x in cycle], **detail)

    def check(self, task, sealed, content, host):
        g, c = cochain_task(task)
        require(isinstance(content, Mapping), 'reply must be an object')
        local = self.local_sections(task, g, c)
        if 'potential' in content:
            return self.certify_gluing(g, c, content['potential'], host, local_sections=local)
        if 'obstruction' in content:
            return self.certify_obstruction(g, c, content['obstruction'], host, local_sections=local)
        raise MalformedCandidateError('reply must carry a potential or an obstruction cycle, not a claim')

    def fixtures(self):
        edges = [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]]
        base = {'statement': 'Glue the local sections into one vertex potential, or give an obstruction cycle.',
                'edges': edges, 'patches': [[0, 1, 3], [2, 4]]}
        exact = {**base, 'labels': [1, '3/2', '-5/2', '3/2', -4]}
        twisted = {**base, 'labels': [1, 2, '-5/2', '3/2', -4]}
        return {
            'consistent_cover_glued': ({'task': exact, 'replies': [{'potential': [0, 1, '5/2', 4]}]},
                                       'HOST_CERTIFIED'),
            'twisted_cover_obstructed': ({'task': twisted, 'replies': [{'obstruction': [[0, 1], [1, 1], [2, 1]]}]},
                                         'TYPED_REFUSAL'),
            'prose_gluing_claim': ({'task': twisted, 'replies': [{'claim': 'the local sections agree'}]}, 'REFUSED'),
            'bluffed_potential_on_twisted_cover': ({'task': twisted, 'replies': [{'potential': [0, 1, '5/2', 4]}]},
                                                   'REFUSED'),
            'open_path_witness': ({'task': twisted, 'replies': [{'obstruction': [[0, 1], [1, 1]]}]}, 'REFUSED'),
            'zero_holonomy_witness': ({'task': twisted, 'replies': [{'obstruction': [[2, -1], [3, 1], [4, 1]]}]},
                                      'REFUSED'),
        }


# ---------------------------------------------------------------- WF11


@register
class DualCertificateSynthesis(WorkflowFamily):
    """WF11. Certify an LP optimum with an exact dual, or infeasibility with a Farkas vector.

    Domain: ``max c.x`` subject to ``A x <= b, x >= 0`` over Q. An optimum needs
    primal and dual feasibility and ``c.x = b.y``; complementary slackness is
    checked as an independent second checker. Infeasibility needs ``y >= 0``,
    ``A^T y >= 0`` and ``b.y < 0``. A feasible pair with a positive gap is a
    weak-duality bound, not a certificate, and is refused.
    """
    spec = spec_from('WF11', 'Dual-certificate synthesis', 3, ['WF3', 'WF9'], 'WF1',
                     'lp_dual_and_farkas_certificate', 'wf11_dual_certificate_synthesis')

    @staticmethod
    def lp(task: Mapping[str, Any]) -> tuple[list[list[Fraction]], list[Fraction], list[Fraction]]:
        a, b, c = task.get('A'), task.get('b'), task.get('c')
        require(isinstance(a, list) and a and isinstance(b, list) and isinstance(c, list), 'A, b, c required')
        require(len(b) == len(a) and all(isinstance(r, list) and len(r) == len(c) for r in a), 'shapes')
        return ([[as_fraction(x, 'A') for x in r] for r in a], [as_fraction(x, 'b') for x in b],
                [as_fraction(x, 'c') for x in c])

    def validate(self, task):
        self.lp(task)
        return task

    @staticmethod
    def vector(raw: Any, n: int, name: str) -> list[Fraction]:
        require(isinstance(raw, list) and len(raw) == n, f'{name} must have {n} entries')
        return [as_fraction(v, name) for v in raw]

    @classmethod
    def certify_optimum(cls, a, b, c, x_raw, y_raw, host: HostOracleContext, **detail: Any) -> Verdict:
        x, y = cls.vector(x_raw, len(c), 'x'), cls.vector(y_raw, len(b), 'y')
        slack = [bi - ai for bi, ai in zip(b, matvec(a, x), strict=True)]
        reduced = [ai - ci for ai, ci in zip(matvec(transpose(a), y), c, strict=True)]
        primal = host.record('primal_feasible', min(x) >= 0 and min(slack) >= 0, canonical([x, slack]).decode())
        dual = host.record('dual_feasible', min(y) >= 0 and min(reduced) >= 0, canonical([y, reduced]).decode())
        gap = dot(b, y) - dot(c, x)
        host.record('zero_duality_gap', gap == 0, fmt(gap))
        cs = all(p * q == 0 for p, q in zip(y, slack, strict=True)) and all(
            p * q == 0 for p, q in zip(x, reduced, strict=True))
        host.record('complementary_slackness', cs, canonical([slack, reduced]).decode())
        if primal and dual and gap != 0:
            return refused('WEAK_DUALITY_ONLY_BOUND', gap=fmt(gap), **detail)
        return judge(host, 'OPTIMAL', value=fmt(dot(c, x)), gap=fmt(gap), **detail)

    @classmethod
    def certify_infeasible(cls, a, b, y_raw, host: HostOracleContext, **detail: Any) -> Verdict:
        y = cls.vector(y_raw, len(b), 'farkas')
        aty = matvec(transpose(a), y)
        host.record('farkas_y_nonnegative', min(y) >= 0, canonical(y).decode())
        host.record('farkas_aty_nonnegative', min(aty) >= 0, canonical(aty).decode())
        host.record('farkas_by_negative', dot(b, y) < 0, fmt(dot(b, y)))
        if host.final_output_certified:
            return typed_refusal('PRIMAL_INFEASIBLE', farkas=[fmt(v) for v in y], by=fmt(dot(b, y)), **detail)
        return judge(host, **detail)

    def check(self, task, sealed, content, host):
        a, b, c = self.lp(task)
        require(isinstance(content, Mapping), 'reply must be an object')
        if 'farkas' in content:
            return self.certify_infeasible(a, b, content['farkas'], host)
        require('x' in content and 'y' in content, 'reply must carry x and y, or a farkas vector')
        return self.certify_optimum(a, b, c, content['x'], content['y'], host)

    def fixtures(self):
        lp = {'statement': 'Maximise c.x subject to A x <= b, x >= 0; certify with an exact dual or Farkas y.',
              'A': [[1, 1], [1, 3], [1, 0]], 'b': [4, 6, 3], 'c': [3, 2]}
        empty = {**lp, 'A': [[1, 1], [1, -1]], 'b': [-2, 1]}
        return {
            'optimum_with_exact_dual': ({'task': lp, 'replies': [{'x': [3, 1], 'y': [2, 0, 1]}]}, 'HOST_CERTIFIED'),
            'farkas_infeasibility': ({'task': empty, 'replies': [{'farkas': [1, 0]}]}, 'TYPED_REFUSAL'),
            'weak_duality_bound_only': ({'task': lp, 'replies': [{'x': [3, 1], 'y': [3, 0, 0]}]}, 'REFUSED'),
            'dual_infeasible_y': ({'task': lp, 'replies': [{'x': [3, 1], 'y': ['11/4', 0, 0]}]}, 'REFUSED'),
            'wrong_farkas_vector': ({'task': empty, 'replies': [{'farkas': [0, 1]}]}, 'REFUSED'),
            'prose_infeasibility_claim': ({'task': empty, 'replies': [{'claim': 'no feasible point'}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF25


@register
class HierarchicalDecimation(WorkflowFamily):
    """WF25. Decimate tree and degree-2 parts of a cochain graph without changing any cycle residual.

    The candidate returns a reduced multigraph whose edges are signed walks in
    the original graph, each labelled with its exact path sum. The host checks
    every walk, every label, equal first Betti number, and that the lifted
    fundamental cycles have full rank ``b1`` (so ``H_1`` maps isomorphically and
    every cycle residual survives). A changed label or a dropped loop is refused.
    """
    spec = spec_from('WF25', 'Hierarchical decimation', 3, ['WF24'], None, 'cycle_residual_preserving_decimation',
                     'wf25_hierarchical_decimation')

    def validate(self, task):
        cochain_task(task)
        return task

    def check(self, task, sealed, content, host):
        g, c = cochain_task(task)
        require(isinstance(content, Mapping), 'reply must be an object')
        edges, labels, paths = content.get('edges'), content.get('labels'), content.get('paths')
        require(all(isinstance(x, list) for x in (edges, labels, paths)), 'edges, labels, paths')
        require(len(edges) == len(labels) == len(paths) and edges, 'one label and one path per reduced edge')
        reduced = Graph.of([(as_int(u, 'u'), as_int(v, 'v')) for u, v in edges])
        require(set(reduced.vertices) <= set(g.vertices), 'reduced vertices must be original vertices')
        walks = [parse_cycle(g, p) for p in paths]
        ends_ok = all(walk_end(g, u, w) == v for (u, v), w in zip(reduced.edges, walks, strict=True))
        host.record('paths_are_walks', ends_ok, canonical(paths).decode())
        sums = [sum((s * c[i] for i, s in w), Fraction(0)) for w in walks]
        new = [as_fraction(x, 'label') for x in labels]
        host.record('labels_are_path_sums', new == sums, canonical([new, sums]).decode())
        host.record('cycle_rank_preserved', reduced.cycle_rank == g.cycle_rank, f'{reduced.cycle_rank}|{g.cycle_rank}')
        lifts = []
        for cyc in reduced.fundamental_cycles():
            vec = [0] * len(g.edges)
            for j, sj in cyc:
                for i, s in walks[j]:
                    vec[i] += sj * s
            lifts.append(vec)
        host.record('lifted_cycles_span_h1', (rank(lifts) if lifts else 0) == g.cycle_rank, canonical(lifts).decode())
        degree: dict[Any, int] = {}
        for u, v in reduced.edges:
            degree[u], degree[v] = degree.get(u, 0) + 1, degree.get(v, 0) + 1
        host.record('strictly_smaller_without_leaves', len(reduced.edges) < len(g.edges) and min(degree.values()) > 1,
                    canonical(sorted(degree.items())).decode())
        residuals = [fmt(reduced.cycle_sum(new, cyc)) for cyc in reduced.fundamental_cycles()]
        return judge(host, 'DECIMATED', edges=len(reduced.edges), b1=g.cycle_rank, cycle_residuals=residuals)

    def fixtures(self):
        task = {'statement': 'Eliminate tree and degree-2 parts exactly; keep every cycle residual.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [3, 4], [4, 5]],
                'labels': [1, 2, -2, '1/2', '-1/2', 5, 7]}
        reduced = {'edges': [[0, 2], [2, 0], [2, 0]], 'labels': [3, -2, 0],
                   'paths': [[[0, 1], [1, 1]], [[2, 1]], [[3, 1], [4, 1]]]}
        return {
            'tail_and_chains_decimated': ({'task': task, 'replies': [reduced]}, 'HOST_CERTIFIED'),
            'changed_cycle_residual': ({'task': task, 'replies': [{**reduced, 'labels': [3, -2, 1]}]}, 'REFUSED'),
            'loop_dropped_as_tree': ({'task': task, 'replies': [{'edges': [[0, 2], [2, 0]], 'labels': [3, -2],
                                                                 'paths': [[[0, 1], [1, 1]], [[2, 1]]]}]}, 'REFUSED'),
            'path_is_not_a_walk': ({'task': task, 'replies': [{**reduced, 'paths': [[[0, 1], [3, 1]], [[2, 1]],
                                                                                    [[3, 1], [4, 1]]]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF27


@register
class HintedRetraction(HostedFamily):
    """WF27. The WF9 repair loop with answer-free structural hints and a stationary-loop stop.

    Domain: XOR edge labels, as in WF9. Each rejected turn adds a hint built
    only from the host residual and the public graph: the vertex sets of the odd
    fundamental cycles, never an edge to flip. If the residual at turn ``t``
    equals the residual at ``t - 3`` the proposer is stuck: the run stops and is
    refused with code ``STATIONARY_LOOP`` and the last hint. Malformed replies
    never count as a stationary signal; exhausting the turn cap is refused.
    """
    spec = spec_from('WF27', 'Hinted retraction with a stationary-loop detector', 3, ['WF9'], 'WF9',
                     'xor_residual_gate_stationary_loop', 'wf27_hinted_retraction_with_a_stationary_loop_detector')

    def fixtures(self):
        task = {'statement': 'Flip the fewest edge labels so every cycle has an even label sum.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'labels': [1, 0, 0, 0, 0], 'max_attempts': 6}
        capped = {**task, 'max_attempts': 3}
        loop = [{'flip': [3]}, {'flip': [0, 3]}, {'flip': [1, 4]}, {'flip': [4]}]
        return {
            'repaired_after_hint': ({'task': task, 'replies': [{'flip': [3]}, {'flip': [1]}]}, 'HOST_CERTIFIED'),
            'repaired_after_three_hints': ({'task': task, 'replies': [*loop[:3], {'flip': [1]}]}, 'HOST_CERTIFIED'),
            'stationary_loop_stopped': ({'task': task, 'replies': loop + [{'flip': [0]}]}, 'REFUSED'),
            'empty_replies_are_not_a_stationary_signal': ({'task': task, 'replies': [{}] * 4}, 'REFUSED'),
            'turn_cap_exhausted': ({'task': capped, 'replies': loop}, 'REFUSED'),
            'malformed_repairs_until_cap': ({'task': capped, 'replies': [{'flip': ['1']}, {'flip': [9]}, {}]},
                                            'REFUSED'),
        }


# ---------------------------------------------------------------- WF38


def cycle_defect(g: Graph, c: Sequence[Fraction]) -> Fraction:
    """Phi = sum of |fundamental cycle sums|; zero iff ``c`` is a coboundary."""
    return sum((abs(g.cycle_sum(c, cyc)) for cyc in g.fundamental_cycles()), Fraction(0))


@register
class DiagnosticTraceSelection(WorkflowFamily):
    """WF38. Rank candidate repairs by the host's own defect recomputation, never the model's score.

    Domain: a rational edge cochain with defect ``Phi = sum |cycle sums|``. Each
    candidate is a sparse edge correction. The host recomputes ``Phi`` after
    each one, keeps only strict decreases, and ranks by ``(Phi, |delta|_1, name)``.
    A self-reported score is never read. If no candidate strictly lowers ``Phi``
    the selection is refused.
    """
    spec = spec_from('WF38', 'Diagnostic-trace proposal selection', 3, ['WF9'], 'WF9',
                     'host_recomputed_defect_ranking', 'wf38_diagnostic_trace_proposal_selection')

    def validate(self, task):
        cochain_task(task)
        return task

    def check(self, task, sealed, content, host):
        g, c = cochain_task(task)
        require(isinstance(content, Mapping) and isinstance(content.get('candidates'), list), 'candidates required')
        phi0 = cycle_defect(g, c)
        table = {}
        for cand in content['candidates']:
            require(isinstance(cand, Mapping) and isinstance(cand.get('name'), str), 'candidate needs a name')
            require(cand['name'] not in table and isinstance(cand.get('delta'), list), 'unique name and delta list')
            new = list(c)
            size = Fraction(0)
            for item in cand['delta']:
                require(isinstance(item, list) and len(item) == 2, 'delta entries are [edge, value]')
                i, d = as_int(item[0], 'edge'), as_fraction(item[1], 'delta')
                require(0 <= i < len(c), 'edge index in range')
                new[i] += d
                size += abs(d)
            table[cand['name']] = (cycle_defect(g, new), size)
        admissible = sorted((phi, size, name) for name, (phi, size) in table.items() if phi < phi0)
        scores = {k: [fmt(p), fmt(s)] for k, (p, s) in sorted(table.items())}
        host.record('strict_defect_decrease_exists', bool(admissible), canonical([fmt(phi0), scores]).decode())
        if not admissible:
            return refused('NO_STRICT_DECREASE', phi0=fmt(phi0), scores=scores)
        phi, _size, winner = admissible[0]
        return judge(host, 'SELECTED', winner=winner, phi0=fmt(phi0), phi=fmt(phi), scores=scores,
                     ranking=[x[2] for x in admissible])

    def fixtures(self):
        task = {'statement': 'Propose edge corrections that lower the cycle defect.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'labels': [1, 2, '-5/2', '3/2', -4]}
        worse = {'name': 'alpha', 'delta': [[3, 1]], 'self_score': 'certain'}
        gauge = {'name': 'regauge','delta': [[3, 1], [4, -1]], 'self_score': 'certain'}
        good = [{'name': 'beta', 'delta': [[1, '-1/4']], 'self_score': 'low'},
                {'name': 'gamma', 'delta': [[0, '-1/2']], 'self_score': 'low'},
                {'name': 'delta', 'delta': [[1, '-1/2']], 'self_score': 'low'}]
        return {
            'host_ranks_by_defect': ({'task': task, 'replies': [{'candidates': [worse, *good]}]}, 'HOST_CERTIFIED'),
            'confident_but_worse': ({'task': task, 'replies': [{'candidates': [worse]}]}, 'REFUSED'),
            'gauge_move_is_not_a_decrease': ({'task': task, 'replies': [{'candidates': [gauge]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF46


@register
class BoundarySufficiency(WorkflowFamily):
    """WF46. Test whether boundary packets between patch agents decide global consistency.

    Domain: a rational cochain on a graph split into two edge patches. Each run
    returns a local potential per patch. The host keeps the locally accepted
    runs, glues them by the packet (the declared interface vertices), and runs
    the global evaluator on the glued trace. It reports
    ``NGD = Pr(global fail | all locals pass)``, undefined with no accepted run,
    and refuses when a packet passes but the glued trace fails.
    """
    spec = spec_from('WF46', 'Boundary sufficiency and gluing diagnostic', 3, ['WF4'], None,
                     'glued_trace_global_evaluator', 'wf46_boundary_sufficiency_and_gluing_diagnostic')

    def validate(self, task):
        g, _ = cochain_task(task)
        patches, packet = task.get('patches'), task.get('packet')
        require(isinstance(patches, list) and len(patches) == 2, 'two patches required')
        require(sorted(i for p in patches for i in p) == list(range(len(g.edges))), 'patches partition the edges')
        require(isinstance(packet, list) and packet and all(type(v) is int for v in packet), 'packet vertices')
        as_int(task.get('runs'), 'runs')
        return task

    @staticmethod
    def local(g: Graph, c, patch: list[int], raw: Any) -> dict[int, Fraction] | None:
        """The patch potential if it explains ``c`` on every patch edge, else None."""
        require(isinstance(raw, list) and all(isinstance(p, list) and len(p) == 2 for p in raw),
                'patch potential is a list of [vertex, value]')
        phi = {as_int(v, 'vertex'): as_fraction(x, 'potential') for v, x in raw}
        verts = {x for i in patch for x in g.edges[i]}
        if set(phi) != verts:
            return None
        ok = all(phi[g.edges[i][1]] - phi[g.edges[i][0]] == c[i] for i in patch)
        return phi if ok else None

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        g, c = cochain_task(task)
        packet, runs = task['packet'], task['runs']
        accepted, rows, replied = [], [], 0
        for k in range(runs):
            reply = session.ask(f'run:{k}', self.prompt(task))
            if reply is None:
                continue
            replied += 1
            require(isinstance(reply.content, list) and len(reply.content) == 2, 'one potential per patch')
            p1, p2 = (self.local(g, c, p, raw) for p, raw in zip(task['patches'], reply.content, strict=True))
            if p1 is None or p2 is None:
                rows.append({'run': k, 'local': False})
                continue
            shift = p1[packet[0]] - p2[packet[0]]
            packet_ok = all(p1[v] - p2[v] == shift for v in packet)
            glued = {**{v: x + shift for v, x in p2.items()}, **p1}
            global_ok = not any(g.residual(c, glued))
            accepted.append((packet_ok, global_ok))
            rows.append({'run': k, 'local': True, 'packet': packet_ok, 'global': global_ok})
        share = {'completed': f'{replied}/{runs}', 'backlog': runs - replied, 'runs': rows}
        if not host.record('ngd_defined', bool(accepted), canonical(rows).decode()):
            return refused('NGD_UNDEFINED', ngd=None, **share)
        ngd = Fraction(sum(1 for _p, ok in accepted if not ok), len(accepted))
        hidden = sum(1 for p, ok in accepted if p and not ok)
        if not host.record('packet_decides_global', all(p == ok for p, ok in accepted), str(hidden)):
            return refused('BOUNDARY_INSUFFICIENT', ngd=fmt(ngd), hidden_failures=hidden, **share)
        return judge(host, 'BOUNDARY_SUFFICIENT', ngd=fmt(ngd), **share)

    def fixtures(self):
        base = {'statement': 'Each agent returns a potential on its patch; the packet is shared.',
                'edges': [[0, 1], [1, 2], [2, 3], [3, 0]], 'patches': [[0, 1], [2, 3]], 'packet': [0, 2], 'runs': 3}
        exact = {**base, 'labels': [1, 2, -1, -2]}
        twisted = {**base, 'labels': [1, 2, -1, -1]}
        lossy = {**twisted, 'packet': [0]}
        good = [[[0, 0], [1, 1], [2, 3]], [[2, 5], [3, 4], [0, 2]]]
        shifted = [[[0, 7], [1, 8], [2, 10]], [[2, 3], [3, 2], [0, 0]]]
        twist = [[[0, 0], [1, 1], [2, 3]], [[2, 0], [3, -1], [0, -2]]]
        broken = [[[0, 0], [1, 1], [2, 2]], [[2, 5], [3, 4], [0, 2]]]
        return {
            'consistent_cover_packet_sufficient': ({'task': exact, 'replies': [good, shifted, broken]},
                                                   'HOST_CERTIFIED'),
            'obstruction_seen_by_full_packet': ({'task': twisted, 'replies': [twist, broken]}, 'HOST_CERTIFIED'),
            'lossy_packet_hides_obstruction': ({'task': lossy, 'replies': [twist, broken]}, 'REFUSED'),
            'no_locally_accepted_run': ({'task': exact, 'replies': [broken, broken]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF47


def gauge_signs(task: Mapping[str, Any], k: int) -> dict[int, int]:
    """Candidate ``k`` in lexicographic order: basis[0] is +1, then one bit per basis vertex, MSB first."""
    basis = task['basis']
    bits = len(basis) - 1
    signs = {basis[0]: 1}
    for j, v in enumerate(basis[1:]):
        signs[v] = -1 if (k >> (bits - 1 - j)) & 1 else 1
    return signs


def gauge_ok(task: Mapping[str, Any], k: int) -> bool:
    s = gauge_signs(task, k)
    return all(sigma == s[u] * s[v] for (u, v), sigma in zip(task['edges'], task['signs'], strict=True))


def presentation_key(task: Mapping[str, Any]) -> str:
    return digest({k: task[k] for k in ('edges', 'signs', 'basis', 'representation')})


@register
class ResumableFrontierSearch(WorkflowFamily):
    """WF47. A bounded sign-gauge search in deterministic batches, resumable under one ledger.

    Domain: a signed graph; a gauge is ``s_v in {+1, -1}`` with ``sigma_uv = s_u s_v``.
    Candidates are enumerated lexicographically in fixed batches; each batch is
    a sealed checkpoint carrying the presentation key and the cumulative spend.
    A resume must replay the contiguous chain from index 0 under the same key,
    and the ledger must continue. Budget resets, changed problems and partial
    replays are refused; exhausting a frustrated graph is a typed obstruction.
    """
    spec = spec_from('WF47', 'Resumable bounded frontier search', 3, ['WF9'], None, 'sign_gauge_checkpoint_chain',
                     'wf47_resumable_bounded_frontier_search')

    def validate(self, task):
        g = parse_graph(task.get('edges'))
        require(isinstance(task.get('signs'), list) and len(task['signs']) == len(g.edges), 'one sign per edge')
        require(all(s in (1, -1) and type(s) is int for s in task['signs']), 'signs are +1/-1')
        require(sorted(task.get('basis', [])) == sorted(g.vertices), 'basis orders every vertex')
        for k in ('batch', 'max_sessions', 'session_evals'):
            require(as_int(task.get(k), k) > 0, f'{k} must be positive')
        return task

    @staticmethod
    def total(task: Mapping[str, Any]) -> int:
        return 2 ** (len(task['basis']) - 1)

    @classmethod
    def expected(cls, task: Mapping[str, Any], start: int) -> dict[str, Any]:
        end = min(start + task['batch'], cls.total(task))
        hit = next((k for k in range(start, end) if gauge_ok(task, k)), None)
        return {'start': start, 'end': end, 'status': 'unknown' if hit is None else 'verified', 'gauge': hit}

    def chain_error(self, task, chain: Any, prior: list | None) -> str | None:
        """First failed custody rule of a checkpoint chain, or None."""
        require(isinstance(chain, list) and chain and all(isinstance(r, Mapping) for r in chain), 'chain of records')
        key = presentation_key(task)
        bodies = [{k: v for k, v in r.items() if k != 'seal'} for r in chain]
        wants, start = [], 0
        for _ in chain:
            wants.append(self.expected(task, start))
            start = wants[-1]['end']
        pairs = list(zip(chain, wants, strict=True))
        new = wants[-1]['end'] - (prior[-1]['end'] if prior else 0)
        rules = (
            ('RESUME_NOT_REPLAYED_FROM_ZERO', lambda: chain[0].get('index') == 0),
            ('CHAIN_NOT_CONTIGUOUS', lambda: [r.get('index') for r in chain] == list(range(len(chain)))),
            ('RESUME_DIVERGES_FROM_CHECKPOINT',
             lambda: prior is None or (len(chain) > len(prior) and chain[:len(prior)] == prior)),
            ('PRESENTATION_KEY_CHANGED', lambda: all(r.get('key') == key for r in chain)),
            ('SEAL_MISMATCH', lambda: [r.get('seal') for r in chain] == seal_chain(key, bodies)[1:]),
            ('BATCH_NOT_LEXICOGRAPHIC', lambda: all(r.get('start') == w['start'] and r.get('end') == w['end']
                                                    for r, w in pairs)),
            ('BUDGET_RESET', lambda: all(r.get('spent') == w['end'] for r, w in pairs)),
            ('STATUS_NOT_RECOMPUTED', lambda: all(r.get('status') == w['status'] and r.get('gauge') == w['gauge']
                                                  for r, w in pairs)),
            ('SEARCH_CONTINUED_AFTER_VERIFIED', lambda: all(w['status'] == 'unknown' for w in wants[:-1])),
            ('SESSION_BUDGET_EXCEEDED', lambda: new <= task['session_evals']),
        )
        return next((code for code, ok in rules if not ok()), None)

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task = session.task
        prior: list | None = None
        for s in range(task['max_sessions']):
            note = '' if prior is None else f"\nResume after seal {prior[-1]['seal']} at index {len(prior)}."
            reply = session.ask('search' if s == 0 else f'resume:{s}', self.prompt(task) + note)
            if reply is None:
                break
            chain = reply.content.get('checkpoints') if isinstance(reply.content, Mapping) else None
            error = self.chain_error(task, chain, prior)
            if error:
                host.record(error.lower(), False, canonical(chain).decode())
                return refused(error, session=s)
            prior = list(chain)
            if prior[-1]['status'] == 'verified' or prior[-1]['end'] == self.total(task):
                break
        if prior is None:
            return refused('NO_ADMISSIBLE_REPLY')
        host.record('checkpoint_chain_valid', True, prior[-1]['seal'])
        last = prior[-1]
        if last['status'] == 'verified':
            host.record('gauge_balances_every_edge', gauge_ok(task, last['gauge']), str(last['gauge']))
            return judge(host, 'GAUGE_VERIFIED', gauge=last['gauge'], checkpoints=len(prior))
        if last['end'] < self.total(task):
            return refused('SEARCH_INCOMPLETE', suffix=last['end'], checkpoints=len(prior))
        g = Graph.of(task['edges'])
        odd = [k for k, cyc in enumerate(g.fundamental_cycles())
               if g.cycle_sum([(1 - s) // 2 for s in task['signs']], cyc, 2)]
        if not host.record('frustrated_cycle_witness', bool(odd), str(odd)):
            return refused('EXHAUSTED_WITHOUT_OBSTRUCTION')
        return typed_refusal('RESTRICTED_OBSTRUCTION', frustrated_cycles=odd, checkpoints=len(prior))

    @classmethod
    def build_chain(cls, task, batches: int, *, key: str | None = None, from_index: int = 0,
                    spent_offset: int = 0, offset_from: int = 0) -> list[dict[str, Any]]:
        """Honest checkpoint records (fixture helper); keyword arguments forge specific faults."""
        bodies, start = [], 0
        for i in range(batches):
            want = cls.expected(task, start)
            spent = want['end'] - (spent_offset if i >= offset_from else 0)
            bodies.append({'index': i, 'key': key if key and i >= offset_from else presentation_key(task),
                           'spent': spent, **want})
            start = want['end']
        seals = seal_chain(presentation_key(task), bodies)[1:]
        return [{**b, 'seal': h} for b, h in zip(bodies, seals, strict=True)][from_index:]

    def fixtures(self):
        task = {'statement': 'Find a sign gauge s with sigma_uv = s_u s_v by bounded lexicographic batches.',
                'edges': [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]], 'signs': [-1, 1, -1, 1, -1],
                'basis': [0, 1, 2, 3], 'representation': 'pm1', 'batch': 2, 'max_sessions': 2, 'session_evals': 4}
        frustrated = {**task, 'signs': [-1, 1, -1, 1, 1]}
        moved = presentation_key({**task, 'basis': [0, 2, 1, 3]})

        def two(t, **forge):
            return [{'checkpoints': self.build_chain(t, 2)}, {'checkpoints': self.build_chain(t, 4, **forge)}]
        return {
            'resumed_search_verifies_gauge': ({'task': task, 'replies': two(task)}, 'HOST_CERTIFIED'),
            'frustrated_graph_exhausted': ({'task': frustrated, 'replies': two(frustrated)}, 'TYPED_REFUSAL'),
            'budget_reset_on_resume': ({'task': task, 'replies': two(task, spent_offset=4, offset_from=2)},
                                       'REFUSED'),
            'changed_problem_on_resume': ({'task': task, 'replies': two(task, key=moved, offset_from=2)}, 'REFUSED'),
            'resume_skips_replay': ({'task': task, 'replies': two(task, from_index=2)}, 'REFUSED'),
        }
