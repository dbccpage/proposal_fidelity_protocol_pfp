"""Layer 2 families: built on WF1, WF2 and WF7.

WF13, WF24, WF32 and WF45 are checked by the Rust host (``pfp_operad family``): each class
here is its registry entry and its offline fixtures. WF9 is still checked in this file.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from ..fidelity import HostOracleContext
from .base import (
    HostedFamily,
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
        require(all(isinstance(e, list) and len(e) == 2 for e in task['edges']), 'each edge is a pair')
        # Exact 0/1 labels only: a float, string, bool or non-finite value is refused, never coerced.
        require(all(type(x) is int and x in (0, 1) for x in task['labels']), 'labels must be exact int 0 or 1')
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


@register
class ExactDomainCapsuleBattery(HostedFamily):
    """WF13. Run a battery of exact-domain capsules, each judged by its own registered checker.

    Domains: stabilizer commutation (symplectic product mod 2), U(1) anomaly sums
    (sum q and sum q^3), commutators in S_n, and a WF7 linear capsule that must be
    answered or refused by the rank test. Every domain needs a checker before any
    capsule is dispatched. Results are per domain over the full declared denominator:
    a missing or malformed reply counts as a failure, and no cross-domain average is formed.
    """
    spec = spec_from('WF13', 'Exact-domain capsule battery', 2, ['WF1', 'WF7'], 'WF1',
                     'per_domain_registered_checker', 'wf13_exact_domain_capsule_battery')

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


@register
class PinnedTokenScratchpad(HostedFamily):
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
class ClaimScopedReceipt(HostedFamily):
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


@register
class FiniteTerminalSelector(HostedFamily):
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
