"""Paper 002 finite sign-graph adapter for the inward checker port.

The canonical ``sign_graph`` and ``frontier_search`` sources stay byte-pinned;
this module owns all translation and host-file hashing. AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Callable

from omega_engine_pfp.domain.finite_gauge import (
    CandidateCheck,
    CheckerIdentity,
    GaugeFrontier,
    GaugeRefusal,
    GaugeRefusalCode,
    GraphSpec,
    SearchReceipt,
    Witness,
)
from omega_engine_pfp.domain.kernel.result import Result

from . import frontier_search, sign_graph


def _refusal(code: GaugeRefusalCode, error: Exception | str) -> GaugeRefusal:
    return GaugeRefusal(code=code, message=str(error))


def _source_hash(module_file: str | None) -> str:
    if module_file is None:
        raise FileNotFoundError("checker module has no source path")
    return sha256(Path(module_file).read_bytes()).hexdigest()


def _presentation_key() -> frontier_search.PresentationKey:
    return frontier_search.PresentationKey(
        hamiltonian_digest="0" * 64,
        basis="finite signed graph vertices",
        ensemble="unspecified graph control",
        filling="not supplied",
        boundary="declared graph",
        representation="signed rewrite graph",
        estimator="not supplied",
        observables=("graph parity",),
        beta="not supplied",
        parameters=(),
        transformation_grammar=frontier_search.DIAGONAL_Z2_GRAMMAR,
        adapter_digest="0" * 64,
        checker_version=frontier_search.CHECKER_VERSION,
    )


def _edges(graph: GraphSpec) -> tuple[sign_graph.SignedRewrite, ...]:
    return tuple(
        sign_graph.SignedRewrite(edge.source, edge.target, edge.odd)
        for edge in graph.edges
    )


def _witness(value: object) -> Witness | None:
    if isinstance(value, sign_graph.GaugeWitness):
        return Witness(kind="gauge", vertices=value.vertices, bits=value.bits)
    if isinstance(value, sign_graph.OddCycleWitness):
        return Witness(kind="odd_cycle", steps=value.steps)
    return None


def _to_domain(receipt: frontier_search.SearchReceipt) -> SearchReceipt:
    return SearchReceipt(
        status=receipt.status,
        receipt_sha256=receipt.receipt_sha256,
        presentation_digest=receipt.presentation_digest,
        graph_digest=receipt.graph_digest,
        node_budget=receipt.node_budget,
        checks=tuple(CandidateCheck(item.index, item.bits, item.valid) for item in receipt.checks),
        frontier=GaugeFrontier(receipt.frontier.next_index, receipt.frontier.stop_index),
        witness=_witness(receipt.witness),
        complete_oracle_used=receipt.complete_oracle_used,
    )


@dataclass(frozen=True, slots=True)
class Paper002FiniteGaugeChecker:
    """Concrete, fail-closed adapter around the byte-pinned Paper 002 checker."""

    receipt_verifier: Callable[..., bool] = frontier_search.verify_search_receipt

    def identity(self) -> Result[CheckerIdentity, GaugeRefusal]:
        try:
            identity = CheckerIdentity(
                checker_version=frontier_search.CHECKER_VERSION,
                checker_sha256=_source_hash(frontier_search.__file__),
                sign_graph_sha256=_source_hash(sign_graph.__file__),
            )
        except (OSError, TypeError) as exc:
            return Result.err(_refusal(GaugeRefusalCode.CHECKER_UNAVAILABLE, exc))
        return Result.ok(identity)

    def graph_digest(self, graph: GraphSpec) -> Result[str, GaugeRefusal]:
        try:
            digest = frontier_search.graph_digest(graph.vertices, _edges(graph))
        except Exception as exc:
            return Result.err(_refusal(GaugeRefusalCode.CHECK_FAILED, exc))
        return Result.ok(digest)

    def verify_candidate(
        self, graph: GraphSpec, bits: tuple[int, ...]
    ) -> Result[bool, GaugeRefusal]:
        try:
            witness = sign_graph.GaugeWitness(graph.vertices, bits)
            verified = sign_graph.verify_gauge(graph.vertices, _edges(graph), witness)
        except Exception as exc:
            return Result.err(_refusal(GaugeRefusalCode.CHECK_FAILED, exc))
        return Result.ok(verified)

    def search_and_replay(
        self, graph: GraphSpec, node_budget: int
    ) -> Result[SearchReceipt, GaugeRefusal]:
        try:
            edges = _edges(graph)
            key = _presentation_key()
            receipt = frontier_search.search_sign_graph(
                graph.vertices,
                edges,
                key,
                node_budget=node_budget,
                workers=1,
            )
            if not self.receipt_verifier(graph.vertices, edges, key, receipt):
                return Result.err(
                    _refusal(
                        GaugeRefusalCode.REPLAY_FAILED,
                        "Paper 002 search receipt failed independent replay",
                    )
                )
        except Exception as exc:
            return Result.err(_refusal(GaugeRefusalCode.CHECK_FAILED, exc))
        return Result.ok(_to_domain(receipt))


__all__ = ["Paper002FiniteGaugeChecker"]
