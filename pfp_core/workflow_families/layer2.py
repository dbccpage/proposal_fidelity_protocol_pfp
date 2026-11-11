"""Layer 2 families: built on WF1, WF2 and WF7."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from ..fidelity import HostOracleContext
from .base import (
    MalformedCandidateError,
    Session,
    Verdict,
    WorkflowFamily,
    as_int,
    canonical,
    certified,
    refused,
    require,
    spec_from,
)
from .exact import Graph
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
