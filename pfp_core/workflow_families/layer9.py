"""Layer 9 families: recursive re-entry and the restart boundary, both built on the WF20 loop.

Both are checked by the Rust host (``pfp_operad family``): each class here is its registry
entry and its offline fixtures. The digests below only build fixture replies, in the form the
host's own receipts take.
"""
from __future__ import annotations

from typing import Any

from .base import HostedFamily, digest, spec_from
from .registry import register


def root_receipt(task: dict[str, Any], plan: list[list[int]]) -> str:
    return digest({'root': digest(task), 'plan': plan})


def reentry_receipt(parent: str, child: int, root_flips: list[int], fuel: int) -> str:
    return digest({'parent': parent, 'child': child, 'flips': root_flips, 'fuel': fuel})


@register
class RecursiveReentryWithSharedFuel(HostedFamily):
    """WF33. Split a repair into child derivations that share one fuel counter and one budget.

    Domain: XOR edge labels on a graph. A plan maps root edges onto children
    (forward coverage must be a partition); each child re-enters the WF20 loop
    on its subgraph, and its flips map back to root edges, where the union must
    pass the root WF9 check. Every ask draws from a strictly decreasing fuel
    counter. A stale parent receipt, a changed task or a fuel reset is refused.
    """
    spec = spec_from('WF33', 'Recursive re-entry with shared fuel', 9, ['WF9', 'WF20'], None,
                     'shared_fuel_parent_bound_reentry', 'wf33_recursive_re_entry_with_shared_fuel')

    def fixtures(self):
        task = {'statement': 'Repair the labels by delegating disjoint parts to child derivations.',
                'edges': [[0, 1], [1, 2], [2, 0], [2, 3], [3, 0], [4, 5], [5, 6], [6, 4]],
                'labels': [1, 0, 0, 0, 0, 0, 0, 1], 'fuel': 12}
        plan = [[0, 1, 2, 3, 4], [5, 6, 7]]
        root = root_receipt(task, plan)
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


def immutable_spec(task: dict[str, Any]) -> dict[str, Any]:
    return {'edges': task['edges'], 'faces': task['faces'], 'c': task['c']}


def refusal_receipts(task: dict[str, Any], residuals: list[dict[str, Any]]) -> list[str]:
    """The receipts the host shows for failed attempts with these residuals, in attempt order."""
    spec_digest = digest(immutable_spec(task))
    return [digest({'spec': spec_digest, 'attempt': t, 'residual': residual})
            for t, residual in enumerate(residuals)]


@register
class RestartBoundaryAfterExhaustedRepair(HostedFamily):
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

    def fixtures(self):
        edges = [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2]]
        base = {'statement': 'Find potentials matching the edge values, or take the admissible boundary action.',
                'edges': edges, 'faces': [[[0, 1], [1, 1], [4, -1]]], 'max_attempts': 2}
        exact = {**base, 'c': [2, 3, -2, -3, 5]}
        unclosed = {**base, 'c': [2, 3, -2, -3, 6]}
        winding = {**base, 'c': [2, 3, -2, -2, 5]}
        miss = [{'phi': [0, 0, 0, 0]}, {'phi': [0, 0, 0, 0]}]
        solved = {'phi': [0, 2, 5, 3]}
        # Zero potentials leave every edge of `exact` off, with a misfit of 2 + 3 + 2 + 3 + 5.
        missed = [{'defect_l1': '15', 'off_edges': [0, 1, 2, 3, 4]}] * 2

        def restart(seed_change=None, extra=None):
            seed = {'spec': immutable_spec(exact), 'receipts': refusal_receipts(exact, missed)}
            seed.update(seed_change or {})
            seed.update(extra or {})
            return {'task': exact, 'replies': [*miss, {'restart': {'seed': seed}}, solved]}
        return {
            'exact_restart_repairs': (restart(), 'HOST_CERTIFIED'),
            'unclosed_typed_refusal': ({'task': unclosed, 'replies': [*miss, {'refusal': {'face': 0}}]},
                                       'TYPED_REFUSAL'),
            'closed_non_exact_lift': ({'task': winding, 'replies': [
                *miss, {'lift': {'h': [0, 0, 0, 1, 0], 'k': 1, 'phi': [0, 2, 5, 3]}}]}, 'HOST_CERTIFIED'),
            'restart_with_changed_claims': (restart({'spec': immutable_spec(unclosed)}), 'REFUSED'),
            'restart_seed_carries_history': (restart(extra={'history': miss}), 'REFUSED'),
            'lift_without_closed_witness': ({'task': unclosed, 'replies': [
                *miss, {'lift': {'h': [0, 0, 0, 0, 1], 'k': 1, 'phi': [0, 2, 5, 3]}}]}, 'REFUSED'),
            'false_refusal_on_exact': ({'task': exact, 'replies': [*miss, {'refusal': {'face': 0}}]}, 'REFUSED'),
        }
