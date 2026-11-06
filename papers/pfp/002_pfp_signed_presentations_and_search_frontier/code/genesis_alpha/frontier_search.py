"""Bounded finite sign-gauge search and presentation-keyed candidate retrieval.

AuthorityEffect: None.  These routines check a host-supplied signed rewrite
graph, or an exact matrix adapted by ``sign_graph``.  They do not prove that a
Hamiltonian admits the graph, that a path estimator is sign-free, or that a
different presentation preserves observables.  A retrieved candidate is never
a certificate: the host must run the exact checker again.

The scheduler is deterministic parallel *batch enumeration*, not MCTS.  A
ThreadPoolExecutor checks independent candidates concurrently, but CPython's
GIL means this prototype makes no multicore speedup claim for CPU-bound checks.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union

if __package__:
    from .sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
        classify_sign_graph,
        matrix_sign_graph,
        verify_gauge,
        verify_odd_cycle,
    )
else:
    from sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
        classify_sign_graph,
        matrix_sign_graph,
        verify_gauge,
        verify_odd_cycle,
    )


CHECKER_VERSION = "finite-sign-graph-v1"
DIAGONAL_Z2_GRAMMAR = "finite-vertex-diagonal-z2-v1"
BATCH_SIZE = 8  # Fixed independently of worker count, including receipt order.
MAX_NODE_BUDGET = 65536


def _canonical_sha256(value: object) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(data.encode("utf-8")).hexdigest()


def _is_digest(value: object) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


@dataclass(frozen=True)
class PresentationKey:
    """Exact retrieval boundary.  H-to-graph adapter validity is separate."""

    hamiltonian_digest: str
    basis: str
    ensemble: str
    filling: str
    boundary: str
    representation: str
    estimator: str
    observables: Tuple[str, ...]
    beta: str
    parameters: Tuple[Tuple[str, str], ...]
    transformation_grammar: str
    adapter_digest: str
    checker_version: str

    def __post_init__(self) -> None:
        if not _is_digest(self.hamiltonian_digest) or not _is_digest(self.adapter_digest):
            raise ValueError("Hamiltonian and adapter digests must be lowercase SHA-256")
        fields = (self.basis, self.ensemble, self.filling, self.boundary,
                  self.representation, self.estimator, self.beta,
                  self.transformation_grammar, self.checker_version)
        if any(not isinstance(value, str) or not value.strip() for value in fields):
            raise ValueError("every scalar presentation field must be a nonempty string")
        if (not isinstance(self.observables, tuple) or not self.observables
                or any(not isinstance(x, str) or not x.strip() for x in self.observables)
                or tuple(sorted(set(self.observables))) != self.observables):
            raise ValueError("observables must be a sorted, unique, nonempty tuple")
        if (not isinstance(self.parameters, tuple)
                or any(not isinstance(p, tuple) or len(p) != 2
                       or any(not isinstance(x, str) or not x.strip() for x in p)
                       for p in self.parameters)
                or tuple(sorted(set(self.parameters))) != self.parameters
                or len({p[0] for p in self.parameters}) != len(self.parameters)):
            raise ValueError("parameters must be sorted, unique (name, value) pairs")

    def fields(self) -> Tuple[Tuple[str, object], ...]:
        return tuple((name, getattr(self, name)) for name in self.__dataclass_fields__)

    def digest(self) -> str:
        return _canonical_sha256(dict(self.fields()))


@dataclass(frozen=True)
class RetrievedProposal:
    bits: Tuple[int, ...]
    source_note: str
    authority_effect: str = "None"


class PresentationIndex:
    """GIN-style field postings with *full-key* intersection for retrieval.

    A posting can suggest bits but contains no proof of their validity in the
    current graph.  Different representations are distinct keys even when the
    Hamiltonian digest matches.
    """

    def __init__(self) -> None:
        self._records: Dict[PresentationKey, List[RetrievedProposal]] = {}
        self._postings: Dict[Tuple[str, object], Set[PresentationKey]] = {}

    def add(self, key: PresentationKey, bits: Sequence[int], source_note: str) -> None:
        if not isinstance(key, PresentationKey):
            raise TypeError("key must be a PresentationKey")
        proposal = tuple(bits)
        if any(type(bit) is not int or bit not in (0, 1) for bit in proposal):
            raise ValueError("proposal bits must be exactly 0 or 1")
        if not isinstance(source_note, str) or not source_note.strip():
            raise ValueError("source note is required")
        self._records.setdefault(key, []).append(RetrievedProposal(proposal, source_note))
        for token in key.fields():
            self._postings.setdefault(token, set()).add(key)

    def lookup_exact(self, key: PresentationKey) -> Tuple[RetrievedProposal, ...]:
        if not isinstance(key, PresentationKey):
            raise TypeError("key must be a PresentationKey")
        sets = [self._postings.get(token, set()) for token in key.fields()]
        if not sets:
            return ()
        matches = set.intersection(*sets)
        # The equality guard also protects against any future tokenization loss.
        return tuple(self._records[key]) if key in matches and key in self._records else ()


def graph_digest(vertices: Sequence[str], edges: Sequence[SignedRewrite]) -> str:
    vs, es = tuple(vertices), tuple(edges)
    # Reuse the exact checker's input validation before serialization.
    verify_gauge(vs, es, GaugeWitness(vs, tuple(0 for _ in vs)))
    return _canonical_sha256({"vertices": vs, "edges": [(e.source, e.target, e.odd) for e in es]})


def exact_matrix_digest(matrix: Sequence[Sequence[Union[int, Fraction]]]) -> str:
    rows = tuple(tuple(row) for row in matrix)
    matrix_sign_graph(rows)  # validate the same snapshot that is serialized
    canonical = [["{}/{}".format(Fraction(value).numerator, Fraction(value).denominator)
                  for value in row] for row in rows]
    return _canonical_sha256({"exact_real_symmetric_matrix": canonical})


@dataclass(frozen=True)
class GaugeFrontier:
    graph_digest: str
    next_index: int
    stop_index: int


@dataclass(frozen=True)
class CandidateCheck:
    index: int
    bits: Tuple[int, ...]
    valid: bool


@dataclass(frozen=True)
class SearchReceipt:
    status: str  # GAUGE_VERIFIED, RESTRICTED_OBSTRUCTION, or UNKNOWN
    presentation_digest: str
    graph_digest: str
    start_index: int
    node_budget: int
    checks: Tuple[CandidateCheck, ...]
    frontier: GaugeFrontier
    witness: Optional[Union[GaugeWitness, OddCycleWitness]]
    complete_oracle_used: bool
    receipt_sha256: str


def _bits(index: int, width: int) -> Tuple[int, ...]:
    return tuple((index >> (width - offset - 1)) & 1 for offset in range(width))


def _receipt_body(receipt: SearchReceipt) -> dict:
    if isinstance(receipt.witness, GaugeWitness):
        witness = {"type": "gauge", "vertices": receipt.witness.vertices,
                   "bits": receipt.witness.bits}
    elif isinstance(receipt.witness, OddCycleWitness):
        witness = {"type": "odd_cycle", "steps": receipt.witness.steps}
    else:
        witness = None
    return {
        "status": receipt.status,
        "presentation_digest": receipt.presentation_digest,
        "graph_digest": receipt.graph_digest,
        "start_index": receipt.start_index,
        "node_budget": receipt.node_budget,
        "checks": [(c.index, c.bits, c.valid) for c in receipt.checks],
        "frontier": (receipt.frontier.graph_digest, receipt.frontier.next_index,
                     receipt.frontier.stop_index),
        "witness": witness,
        "complete_oracle_used": receipt.complete_oracle_used,
    }


def _seal_receipt(status: str, key: PresentationKey, digest: str, start: int,
                  budget: int, checks: Sequence[CandidateCheck], frontier: GaugeFrontier,
                  witness: Optional[Union[GaugeWitness, OddCycleWitness]],
                  oracle_used: bool) -> SearchReceipt:
    unsealed = SearchReceipt(status, key.digest(), digest, start, budget,
                             tuple(checks), frontier, witness, oracle_used, "")
    return SearchReceipt(status, key.digest(), digest, start, budget,
                         tuple(checks), frontier, witness, oracle_used,
                         _canonical_sha256(_receipt_body(unsealed)))


def search_sign_graph(
    vertices: Sequence[str], edges: Sequence[SignedRewrite], key: PresentationKey,
    node_budget: int, workers: int = 4, frontier: Optional[GaugeFrontier] = None,
    prior_receipts: Sequence[SearchReceipt] = (),
) -> SearchReceipt:
    """Check gauge proposals in fixed batches using independent worker tasks.

    The frontier is the exact untested lexicographic suffix after this call.
    A nonzero starting cursor requires a replayable chain of prior UNKNOWN
    receipts covering every earlier index.  ``UNKNOWN`` leaves every index in
    the remaining suffix available for continuation.
    Thread scheduling cannot change the selected smallest witness or receipt.
    """
    if (not isinstance(key, PresentationKey) or key.checker_version != CHECKER_VERSION
            or key.transformation_grammar != DIAGONAL_Z2_GRAMMAR):
        raise ValueError("presentation must pin this checker and diagonal Z2 grammar")
    if type(node_budget) is not int or not 0 <= node_budget <= MAX_NODE_BUDGET:
        raise ValueError("node_budget must be an integer within the host batch cap")
    if type(workers) is not int or workers < 1 or workers > 64:
        raise ValueError("workers must be an integer from 1 to 64")
    vs, es = tuple(vertices), tuple(edges)
    digest = graph_digest(vs, es)
    total = 1 << len(vs)
    if frontier is None:
        frontier = GaugeFrontier(digest, 0, total)
    if (not isinstance(frontier, GaugeFrontier) or frontier.graph_digest != digest
            or type(frontier.next_index) is not int or type(frontier.stop_index) is not int
            or not 0 <= frontier.next_index < frontier.stop_index == total):
        raise ValueError("frontier does not match this exact graph")
    cursor = _verified_prior_cursor(vs, es, key, prior_receipts)
    if cursor is None:
        raise ValueError("prior receipts do not form a verified UNKNOWN chain")
    if cursor != frontier.next_index:
        raise ValueError("prior receipts do not cover the starting frontier")

    start = frontier.next_index
    limit = min(total, start + node_budget)
    checked: List[CandidateCheck] = []
    first_valid: Optional[GaugeWitness] = None
    position = start

    if position < limit:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            while position < limit:
                end = min(limit, position + BATCH_SIZE)
                # submit all independent checks, then consume in canonical order
                proposals = [(index, _bits(index, len(vs))) for index in range(position, end)]
                futures = [pool.submit(verify_gauge, vs, es, GaugeWitness(vs, bits))
                           for _, bits in proposals]
                for (index, bits), future in zip(proposals, futures):
                    valid = future.result()
                    checked.append(CandidateCheck(index, bits, valid))
                    if valid and first_valid is None:
                        first_valid = GaugeWitness(vs, bits)
                position = end
                if first_valid is not None:
                    break

    remaining = GaugeFrontier(digest, position, total)
    if first_valid is not None:
        if not verify_gauge(vs, es, first_valid):
            raise AssertionError("worker returned an invalid gauge")
        return _seal_receipt("GAUGE_VERIFIED", key, digest, start, node_budget,
                             checked, remaining, first_valid, False)

    if position < total:
        return _seal_receipt("UNKNOWN", key, digest, start, node_budget,
                             checked, remaining, None, False)

    # Complete only for this finite vertex-gauge grammar.  The independent
    # graph oracle supplies a checkable odd cycle (or catches a bad cursor).
    oracle = classify_sign_graph(vs, es)
    if isinstance(oracle, OddCycleWitness):
        if not verify_odd_cycle(vs, es, oracle):
            raise AssertionError("oracle returned an invalid odd cycle")
        return _seal_receipt("RESTRICTED_OBSTRUCTION", key, digest, start,
                             node_budget, checked, remaining, oracle, True)
    # Verified UNKNOWN receipts cover every prior index; this call covered the
    # rest.  A gauge here would contradict the replayed exhaustive search.
    raise AssertionError("exhausted gauge search contradicts graph oracle")


def search_exact_matrix(
    matrix: Sequence[Sequence[Union[int, Fraction]]], key: PresentationKey,
    node_budget: int, workers: int = 4, frontier: Optional[GaugeFrontier] = None,
    prior_receipts: Sequence[SearchReceipt] = (),
) -> SearchReceipt:
    """Pin an exact matrix digest, then search its fixed-basis sign graph."""
    rows = tuple(tuple(row) for row in matrix)
    matrix_digest = exact_matrix_digest(rows)
    if key.hamiltonian_digest != matrix_digest:
        raise ValueError("presentation Hamiltonian digest does not match exact matrix")
    vs, es = matrix_sign_graph(rows)
    return search_sign_graph(vs, es, key, node_budget, workers, frontier,
                             prior_receipts)


def _verify_receipt_segment(
    vertices: Sequence[str], edges: Sequence[SignedRewrite], key: PresentationKey,
    receipt: SearchReceipt,
) -> bool:
    """Replay one segment; callers must separately check its prior coverage."""
    if (not isinstance(receipt, SearchReceipt) or not isinstance(key, PresentationKey)
            or key.checker_version != CHECKER_VERSION
            or key.transformation_grammar != DIAGONAL_Z2_GRAMMAR
            or not isinstance(receipt.frontier, GaugeFrontier)
            or not isinstance(receipt.checks, tuple)
            or type(receipt.complete_oracle_used) is not bool
            or not _is_digest(receipt.receipt_sha256)):
        return False
    vs, es = tuple(vertices), tuple(edges)
    try:
        digest = graph_digest(vs, es)
    except (TypeError, ValueError):
        return False
    total = 1 << len(vs)
    if (receipt.presentation_digest != key.digest() or receipt.graph_digest != digest
            or receipt.frontier.graph_digest != digest or receipt.frontier.stop_index != total
            or type(receipt.frontier.next_index) is not int
            or type(receipt.frontier.stop_index) is not int
            or type(receipt.start_index) is not int
            or not 0 <= receipt.start_index <= receipt.frontier.next_index <= total
            or type(receipt.node_budget) is not int
            or not 0 <= receipt.node_budget <= MAX_NODE_BUDGET
            or len(receipt.checks) > receipt.node_budget
            or receipt.frontier.next_index != receipt.start_index + len(receipt.checks)):
        return False
    saw_valid = False
    first_valid: Optional[Tuple[int, ...]] = None
    first_valid_offset: Optional[int] = None
    for expected, check in enumerate(receipt.checks, receipt.start_index):
        if (not isinstance(check, CandidateCheck) or type(check.index) is not int
                or check.index != expected or not isinstance(check.bits, tuple)
                or any(type(bit) is not int or bit not in (0, 1) for bit in check.bits)
                or check.bits != _bits(expected, len(vs)) or type(check.valid) is not bool):
            return False
        if verify_gauge(vs, es, GaugeWitness(vs, check.bits)) != check.valid:
            return False
        if check.valid and not saw_valid:
            saw_valid, first_valid = True, check.bits
            first_valid_offset = expected - receipt.start_index
    maximum = min(receipt.node_budget, total - receipt.start_index)
    expected_count = maximum
    if first_valid_offset is not None:
        expected_count = min(maximum,
                             (first_valid_offset // BATCH_SIZE + 1) * BATCH_SIZE)
    if len(receipt.checks) != expected_count:
        return False
    if receipt.status == "UNKNOWN":
        if receipt.witness is not None or saw_valid or receipt.complete_oracle_used or receipt.frontier.next_index == total:
            return False
    elif receipt.status == "GAUGE_VERIFIED":
        if not isinstance(receipt.witness, GaugeWitness) or not verify_gauge(vs, es, receipt.witness):
            return False
        if (not saw_valid or receipt.complete_oracle_used
                or receipt.witness.bits != first_valid):
            return False
    elif receipt.status == "RESTRICTED_OBSTRUCTION":
        if (receipt.frontier.next_index != total or saw_valid
                or not receipt.complete_oracle_used
                or not isinstance(receipt.witness, OddCycleWitness)
                or not verify_odd_cycle(vs, es, receipt.witness)):
            return False
    else:
        return False
    return receipt.receipt_sha256 == _canonical_sha256(_receipt_body(receipt))


def _verified_prior_cursor(
    vertices: Sequence[str], edges: Sequence[SignedRewrite], key: PresentationKey,
    prior_receipts: Sequence[SearchReceipt],
) -> Optional[int]:
    """Replay a contiguous UNKNOWN chain from zero, or reject it."""
    if not isinstance(prior_receipts, (tuple, list)):
        return None
    cursor = 0
    for prior in prior_receipts:
        if (not isinstance(prior, SearchReceipt) or prior.status != "UNKNOWN"
                or prior.start_index != cursor
                or not _verify_receipt_segment(vertices, edges, key, prior)
                or prior.frontier.next_index <= cursor):
            return None
        cursor = prior.frontier.next_index
    return cursor


def verify_search_receipt(
    vertices: Sequence[str], edges: Sequence[SignedRewrite], key: PresentationKey,
    receipt: SearchReceipt, prior_receipts: Sequence[SearchReceipt] = (),
) -> bool:
    """Replay a full finite receipt chain; do not certify a physical adapter."""
    cursor = _verified_prior_cursor(vertices, edges, key, prior_receipts)
    if cursor is None or not isinstance(receipt, SearchReceipt):
        return False
    if receipt.start_index != cursor:
        return False
    return _verify_receipt_segment(vertices, edges, key, receipt)
