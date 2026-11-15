"""Layer 1 families: built directly on WF1 (typed answer).

All three are checked by the Rust host (``code/rust/pfp_operads/src/families``).
This module holds their registry entries and offline fixtures, and decides nothing.
"""
from __future__ import annotations

from .base import HostedFamily, spec_from
from .registry import register

# The two refusal codes the host's rank test gives. Read by the families that reuse WF7.
REFUSAL_CODES = {'inconsistent': 'UNRESOLVED_INCONSISTENT', 'underdetermined': 'UNRESOLVED_UNDERDETERMINED'}


@register
class TypedRefusal(HostedFamily):
    """WF7. Answer ``A x = b`` exactly, or refuse with the code the rank test predicts.

    The host decides answerability by Rouche-Capelli: a unique solution needs
    ``rank(A) = rank([A|b]) = n``. A confident answer to an unanswerable task is
    a bluff; a refusal of a solvable task is a false refusal. Both are refused.
    """
    spec = spec_from('WF7', 'Typed refusal', 1, ['WF1'], None, 'typed_refusal_rank_test', 'wf07_typed_refusal')

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


@register
class ConstraintForcingAntiRecitation(HostedFamily):
    """WF30. A sorting network under constraints that a memorised network breaks.

    The task forces a comparator prefix and forbids some comparators. The host
    checks the constraints, the size bound, and sorting by the 0-1 principle:
    a comparator network sorts every input iff it sorts all ``2^n`` binary ones.
    """
    spec = spec_from('WF30', 'Constraint-forcing anti-recitation', 1, ['WF1'], None,
                     'comparator_network_zero_one_principle', 'wf30_constraint_forcing_anti_recitation')

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
class HeldOutTournament(HostedFamily):
    """WF31. Several proposers fit a public training share; the host scores a sealed held-out share.

    Each proposer returns exact polynomial coefficients. The referee counts
    held-out points the polynomial hits exactly, against a declared baseline
    control. Selection is refused when the training and held-out ids overlap,
    and no winner is certified unless it strictly beats the baseline.
    """
    spec = spec_from('WF31', 'Multi-agent tournament with held-out cross-validation', 1, ['WF1'], None,
                     'exact_held_out_referee', 'wf31_multi_agent_tournament_with_held_out_cross_validation')

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
