"""Layer 3 families: cochain gluing, LP duality and the repair-loop extensions of WF9.

Every family here is checked by the Rust host (``pfp_operad family``): each class is its
registry entry and its offline fixtures. The seals below only build fixture replies, in the
form the host's own seals take.
"""
from __future__ import annotations

from typing import Any

from .base import HostedFamily, digest, spec_from
from .exact import seal_chain
from .registry import register

# ---------------------------------------------------------------- WF10


@register
class ObstructionCertificate(HostedFamily):
    """WF10. Glue local sections of an edge cochain into a global potential, or certify the obstruction.

    Domain: a rational 1-cochain ``c`` on a graph covered by patches that each
    carry a local section. A gluing is a vertex potential with ``c - delta phi = 0``
    on every edge; an obstruction is a closed signed cycle on which ``c`` sums to
    a nonzero value, a nonzero class in ``H^1``. Prose claims, open paths and
    zero-sum cycles are refused.
    """
    spec = spec_from('WF10', 'Local-to-global obstruction certificate', 3, ['WF4', 'WF9'], 'WF4',
                     'cochain_gluing_or_cycle_obstruction', 'wf10_local_to_global_obstruction_certificate')

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
class DualCertificateSynthesis(HostedFamily):
    """WF11. Certify an LP optimum with an exact dual, or infeasibility with a Farkas vector.

    Domain: ``max c.x`` subject to ``A x <= b, x >= 0`` over Q. An optimum needs
    primal and dual feasibility and ``c.x = b.y``; complementary slackness is
    recorded as a second check of the same fact. Infeasibility needs ``y >= 0``,
    ``A^T y >= 0`` and ``b.y < 0``. A feasible pair with a positive gap is a
    weak-duality bound, not a certificate, and is refused.
    """
    spec = spec_from('WF11', 'Dual-certificate synthesis', 3, ['WF3', 'WF9'], 'WF1',
                     'lp_dual_and_farkas_certificate', 'wf11_dual_certificate_synthesis')

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
class HierarchicalDecimation(HostedFamily):
    """WF25. Decimate tree and degree-2 parts of a cochain graph without changing any cycle residual.

    The candidate returns a reduced multigraph whose edges are signed walks in
    the original graph, each labelled with its exact path sum. The host checks
    every walk, every label, equal first Betti number, and that the lifted
    fundamental cycles have full rank ``b1`` (so ``H_1`` maps isomorphically and
    every cycle residual survives). A changed label or a dropped loop is refused.
    """
    spec = spec_from('WF25', 'Hierarchical decimation', 3, ['WF24'], None, 'cycle_residual_preserving_decimation',
                     'wf25_hierarchical_decimation')

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


@register
class DiagnosticTraceSelection(HostedFamily):
    """WF38. Rank candidate repairs by the host's own defect recomputation, never the model's score.

    Domain: a rational edge cochain with defect ``Phi = sum |cycle sums|``. Each
    candidate is a sparse edge correction. The host recomputes ``Phi`` after
    each one, keeps only strict decreases, and ranks by ``(Phi, |delta|_1, name)``.
    A self-reported score is never read. If no candidate strictly lowers ``Phi``
    the selection is refused.
    """
    spec = spec_from('WF38', 'Diagnostic-trace proposal selection', 3, ['WF9'], 'WF9',
                     'host_recomputed_defect_ranking', 'wf38_diagnostic_trace_proposal_selection')

    def fixtures(self):
        task = {'statement': 'Propose edge corrections that lower the cycle defect.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0]], 'labels': [1, 2, '-5/2', '3/2', -4]}
        worse = {'name': 'alpha', 'delta': [[3, 1]], 'self_score': 'certain'}
        gauge = {'name': 'regauge', 'delta': [[3, 1], [4, -1]], 'self_score': 'certain'}
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
class BoundarySufficiency(HostedFamily):
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


def presentation_key(task: dict[str, Any]) -> str:
    return digest({k: task[k] for k in ('edges', 'signs', 'basis', 'representation')})


def checkpoints(key: str, gauge: int | None = None, forged: tuple[dict[str, Any], ...] = ()) -> list[dict[str, Any]]:
    """Four sealed batches of two candidates under ``key``; the last one finds ``gauge`` if given.

    ``forged`` overwrites fields of the third and fourth records before they are sealed.
    """
    bodies: list[dict[str, Any]] = [{'index': i, 'key': key, 'spent': 2 * i + 2, 'start': 2 * i, 'end': 2 * i + 2,
                                     'status': 'unknown', 'gauge': None} for i in range(4)]
    if gauge is not None:
        bodies[3].update(status='verified', gauge=gauge)
    for body, change in zip(bodies[2:], forged, strict=False):
        body.update(change)
    return [{**body, 'seal': seal} for body, seal in zip(bodies, seal_chain(key, bodies)[1:], strict=True)]


@register
class ResumableFrontierSearch(HostedFamily):
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

    def fixtures(self):
        task = {'statement': 'Find a sign gauge s with sigma_uv = s_u s_v by bounded lexicographic batches.',
                'edges': [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]], 'signs': [-1, 1, -1, 1, -1],
                'basis': [0, 1, 2, 3], 'representation': 'pm1', 'batch': 2, 'max_sessions': 2, 'session_evals': 4}
        frustrated = {**task, 'signs': [-1, 1, -1, 1, 1]}
        key, moved = presentation_key(task), presentation_key({**task, 'basis': [0, 2, 1, 3]})
        # Candidate 6 (vertices 1 and 2 at -1) is the first gauge of `task`; `frustrated` has none.
        honest, barren = checkpoints(key, 6), checkpoints(presentation_key(frustrated))

        def two(t, resumed, first=honest[:2]):
            return {'task': t, 'replies': [{'checkpoints': first}, {'checkpoints': resumed}]}
        return {
            'resumed_search_verifies_gauge': (two(task, honest), 'HOST_CERTIFIED'),
            'frustrated_graph_exhausted': (two(frustrated, barren, barren[:2]), 'TYPED_REFUSAL'),
            'budget_reset_on_resume': (two(task, checkpoints(key, 6, ({'spent': 2}, {'spent': 4}))), 'REFUSED'),
            'changed_problem_on_resume': (two(task, checkpoints(key, 6, ({'key': moved}, {'key': moved}))),
                                          'REFUSED'),
            'resume_skips_replay': (two(task, honest[2:]), 'REFUSED'),
        }
