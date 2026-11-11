"""Layer 1 families: built directly on WF1 (typed answer)."""
from __future__ import annotations

from collections.abc import Mapping
from fractions import Fraction
from itertools import product

from ..fidelity import HostOracleContext
from .base import (
    MalformedCandidateError,
    Session,
    Verdict,
    WorkflowFamily,
    as_fraction,
    as_int,
    judge,
    refused,
    require,
    spec_from,
    typed_refusal,
)
from .exact import classify_linear
from .registry import register

REFUSAL_CODES = {'inconsistent': 'UNRESOLVED_INCONSISTENT', 'underdetermined': 'UNRESOLVED_UNDERDETERMINED'}


@register
class TypedRefusal(WorkflowFamily):
    """WF7. Answer ``A x = b`` exactly, or refuse with the code the rank test predicts.

    The host decides answerability by Rouche-Capelli: a unique solution needs
    ``rank(A) = rank([A|b]) = n``. A confident answer to an unanswerable task is
    a bluff; a refusal of a solvable task is a false refusal. Both are refused.
    """
    spec = spec_from('WF7', 'Typed refusal', 1, ['WF1'], None, 'typed_refusal_rank_test', 'wf07_typed_refusal')

    def validate(self, task):
        require(isinstance(task.get('A'), list) and task['A'] and isinstance(task.get('b'), list), 'A and b required')
        require(all(len(r) == len(task['A'][0]) for r in task['A']) and len(task['b']) == len(task['A']),
                'A must be rectangular and match b')
        return task

    def check(self, task, sealed, content, host):
        a = [[as_fraction(x, 'A') for x in row] for row in task['A']]
        b = [as_fraction(x, 'b') for x in task['b']]
        status = classify_linear(a, b)
        witness = {'rank_A': status.rank_a, 'rank_Ab': status.rank_ab, 'n': len(a[0]), 'status': status.status}
        require(isinstance(content, Mapping), 'reply must be an object')
        if 'refusal' in content:
            if status.status == 'unique':
                host.record('no_false_refusal', False, str(witness))
                return refused('FALSE_REFUSAL', witness=witness)
            ok = host.record('refusal_code_matches_rank_test', content['refusal'] == REFUSAL_CODES[status.status],
                             str(witness))
            return typed_refusal(REFUSAL_CODES[status.status], witness=witness) if ok else refused(
                'WRONG_REFUSAL_CODE', witness=witness)
        x = [as_fraction(v, 'answer') for v in content.get('answer', [])]
        if status.status != 'unique':
            host.record('no_bluff', False, str(witness))
            return refused('BLUFF', witness=witness)
        host.record('answer_equals_unique_solution', tuple(x) == status.solution, str(witness))
        return judge(host, witness=witness)

    def fixtures(self):
        solvable = {'statement': 'Solve A x = b exactly or refuse with a code.', 'A': [[1, 1], [1, -1]], 'b': [3, 1]}
        singular = {'statement': solvable['statement'], 'A': [[1, 1], [2, 2]], 'b': [3, 7]}
        under = {'statement': solvable['statement'], 'A': [[1, 1], [2, 2]], 'b': [3, 6]}
        return {
            'solvable_answered': ({'task': solvable, 'replies': [{'answer': [2, 1]}]}, 'HOST_CERTIFIED'),
            'inconsistent_refused': ({'task': singular, 'replies': [{'refusal': 'UNRESOLVED_INCONSISTENT'}]},
                                     'TYPED_REFUSAL'),
            'underdetermined_refused': ({'task': under, 'replies': [{'refusal': 'UNRESOLVED_UNDERDETERMINED'}]},
                                        'TYPED_REFUSAL'),
            'bluff_on_inconsistent': ({'task': singular, 'replies': [{'answer': [1, 2]}]}, 'REFUSED'),
            'false_refusal_on_solvable': ({'task': solvable, 'replies': [{'refusal': 'UNRESOLVED_INCONSISTENT'}]},
                                          'REFUSED'),
            'wrong_code': ({'task': under, 'replies': [{'refusal': 'UNRESOLVED_INCONSISTENT'}]}, 'REFUSED'),
        }


def apply_network(network: list[tuple[int, int]], values: tuple[int, ...]) -> tuple[int, ...]:
    v = list(values)
    for i, j in network:
        if v[i] > v[j]:
            v[i], v[j] = v[j], v[i]
    return tuple(v)


@register
class ConstraintForcingAntiRecitation(WorkflowFamily):
    """WF30. A sorting network under constraints that a memorised network breaks.

    The task forces a comparator prefix and forbids some comparators. The host
    checks the constraints, the size bound, and sorting by the 0-1 principle:
    a comparator network sorts every input iff it sorts all ``2^n`` binary ones.
    """
    spec = spec_from('WF30', 'Constraint-forcing anti-recitation', 1, ['WF1'], None,
                     'comparator_network_zero_one_principle', 'wf30_constraint_forcing_anti_recitation')

    def validate(self, task):
        as_int(task.get('n'), 'n')
        require(2 <= task['n'] <= 10, 'n must be in 2..10')
        return task

    def check(self, task, sealed, content, host):
        n = task['n']
        require(isinstance(content, Mapping) and isinstance(content.get('network'), list), 'network required')
        net = []
        for pair in content['network']:
            require(isinstance(pair, list) and len(pair) == 2, 'comparators are [i, j] pairs')
            i, j = as_int(pair[0], 'i'), as_int(pair[1], 'j')
            require(0 <= i < j < n, 'comparator must satisfy 0 <= i < j < n')
            net.append((i, j))
        prefix = [tuple(p) for p in task.get('forced_prefix', [])]
        forbidden = {tuple(p) for p in task.get('forbidden', [])}
        host.record('forced_prefix_kept', net[:len(prefix)] == prefix, str(net))
        host.record('no_forbidden_comparator', not (set(net) & forbidden), str(net))
        host.record('within_size_bound', len(net) <= task.get('max_comparators', len(net)), str(len(net)))
        failures = [bits for bits in product((0, 1), repeat=n) if apply_network(net, bits) != tuple(sorted(bits))]
        host.record('sorts_all_binary_inputs', not failures, str(failures[:1]))
        return judge(host, comparators=len(net), binary_failures=len(failures))

    def fixtures(self):
        task = {'statement': 'Give a 4-wire sorting network whose first comparator is [0, 3], without [0, 2].',
                'n': 4, 'forced_prefix': [[0, 3]], 'forbidden': [[0, 2]], 'max_comparators': 6}
        textbook = [[0, 1], [2, 3], [0, 2], [1, 3], [1, 2]]
        good = [[0, 3], [1, 2], [0, 1], [2, 3], [1, 2]]
        return {
            'constrained_network_sorts': ({'task': task, 'replies': [{'network': good}]}, 'HOST_CERTIFIED'),
            'recited_textbook_network': ({'task': task, 'replies': [{'network': textbook}]}, 'REFUSED'),
            'prefix_kept_but_unsorted': ({'task': task, 'replies': [{'network': [[0, 3], [1, 2]]}]}, 'REFUSED'),
        }


@register
class HeldOutTournament(WorkflowFamily):
    """WF31. Several proposers fit a public training share; the host scores a sealed held-out share.

    Each proposer returns exact polynomial coefficients. The referee counts
    held-out points the polynomial hits exactly, against a declared baseline
    control. Selection is refused when the training and held-out ids overlap,
    and no winner is certified unless it strictly beats the baseline.
    """
    spec = spec_from('WF31', 'Multi-agent tournament with held-out cross-validation', 1, ['WF1'], None,
                     'exact_held_out_referee', 'wf31_multi_agent_tournament_with_held_out_cross_validation')

    def validate(self, task):
        require(isinstance(task.get('train'), list) and task['train'], 'train points required')
        as_int(task.get('proposers'), 'proposers')
        return task

    def run(self, session: Session, host: HostOracleContext) -> Verdict:
        task, sealed = session.task, session.sealed
        train_ids = {p['id'] for p in task['train']}
        held = sealed.get('held_out', [])
        overlap = sorted(train_ids & {p['id'] for p in held})
        if not host.record('splits_disjoint', not overlap, str(overlap)):
            return refused('SPLIT_OVERLAP', overlap=overlap)
        scores: dict[str, int] = {}
        for k in range(task['proposers']):
            reply = session.ask(f'proposer:{k}', self.prompt(task))
            if reply is None:
                continue
            try:
                coeffs = [as_fraction(c, 'coefficient') for c in reply.content['coefficients']]
            except (MalformedCandidateError, KeyError, TypeError):
                scores[f'proposer:{k}'] = -1
                continue
            scores[f'proposer:{k}'] = sum(1 for p in held if _poly(coeffs, as_fraction(p['x'], 'x'))
                                          == as_fraction(p['y'], 'y'))
        baseline = [as_fraction(c, 'baseline') for c in task.get('baseline_coefficients', [0])]
        base_score = sum(1 for p in held if _poly(baseline, as_fraction(p['x'], 'x')) == as_fraction(p['y'], 'y'))
        if not scores:
            return refused('NO_ADMISSIBLE_REPLY')
        winner = min(scores, key=lambda k: (-scores[k], k))
        host.record('winner_beats_baseline', scores[winner] > base_score, f'{scores}|{base_score}')
        return judge(host, 'WINNER_SELECTED', winner=winner, scores=scores, baseline=base_score,
                     held_out=len(held))

    def fixtures(self):
        train = [{'id': i, 'x': x, 'y': 2 * x * x + 1} for i, x in enumerate([0, 1, 2, 3])]
        task = {'statement': 'Fit an exact polynomial to the training points.', 'train': train, 'proposers': 3,
                'baseline_coefficients': [1]}
        held = [{'id': 10 + i, 'x': x, 'y': 2 * x * x + 1} for i, x in enumerate([5, 7, -4])]
        replies = [{'coefficients': [1, 0, 2]}, {'coefficients': [1, 2]}, {'coefficients': ['1/2', 1]}]
        overfit = [{'coefficients': [1, 2]}, {'coefficients': [3]}, {'coefficients': [1, 4]}]
        leaky = [*held[:1], {'id': 0, 'x': 0, 'y': 1}]
        return {
            'held_out_winner': ({'task': task, 'sealed': {'held_out': held}, 'replies': replies}, 'HOST_CERTIFIED'),
            'no_one_beats_baseline': ({'task': task, 'sealed': {'held_out': held}, 'replies': overfit}, 'REFUSED'),
            'split_overlap': ({'task': task, 'sealed': {'held_out': leaky}, 'replies': replies}, 'REFUSED'),
        }


def _poly(coeffs: list[Fraction], x: Fraction) -> Fraction:
    return sum((c * x ** k for k, c in enumerate(coeffs)), Fraction(0))

