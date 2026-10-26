"""Thin Fraction/DTO adapter for native ancestral rank and certificates.

Rust owns reconstruction, exact elimination, solver budgets and verification.
AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Dict, List, Optional, Sequence, Tuple

from omega_engine_operations.domain.rop.result import Err
from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost


def _wire(value: Any) -> Any:
    if isinstance(value, Fraction):
        return str(value)
    if isinstance(value, dict):
        return {key: _wire(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_wire(item) for item in value]
    return value


def _edges(edges: Sequence[Any]) -> list[list[str]]:
    return [
        [edge.parent_id, edge.child_id]
        if hasattr(edge, "parent_id") and hasattr(edge, "child_id")
        else [edge[0], edge[1]]
        for edge in edges
    ]


def _invoke(operation: str, **payload: Any) -> Any:
    response = RustSymbolGameHost().invoke_runtime(
        "prompt_rank", _wire({"operation": operation, **payload})
    )
    if isinstance(response, Err):
        raise RuntimeError(f"{response.error.code}: {response.error.message}")
    envelope = response.value
    if not envelope["success"]:
        raise RuntimeError(str(envelope["error"]))
    result = envelope["result"]
    error = result["refusal"]
    if error is not None:
        if error["code"] == "BUDGET_EXHAUSTED":
            raise RuntimeError(error["message"])
        raise ValueError(error["message"])
    return result["outcome"]


class AncestralRankCalculatorV1:
    def compute_inverse_rank(
        self, *, parent_id: str, child_id: str, child_pass_fraction: Fraction
    ) -> Fraction:
        return Fraction(
            _invoke(
                "inverse",
                parent_id=parent_id,
                child_id=child_id,
                child_pass_fraction=child_pass_fraction,
            )
        )

    def compute_community_rank(
        self,
        graph_edges: Sequence[Tuple[str, str]],
        root: str,
        genome_action_digests: Optional[Dict[str, str]] = None,
    ) -> Fraction:
        return Fraction(
            _invoke(
                "community",
                graph_edges=_edges(graph_edges),
                root=root,
                genome_action_digests=genome_action_digests,
            )
        )


def reconstruct_transition_matrix(
    nodes: Sequence[str],
    edges: Sequence[Tuple[str, str]],
    evidence: Optional[Dict[str, Any]] = None,
) -> List[List[Fraction]]:
    return [
        [Fraction(value) for value in row]
        for row in _invoke("matrix", nodes=list(nodes), edges=_edges(edges), evidence=evidence)
    ]


class RankCertificateVerifierV1:
    def verify_certificate(
        self,
        *,
        graph: Dict[str, Any],
        evidence: Dict[str, Any],
        declared_transition_matrix: Sequence[Sequence[Fraction]],
        candidate_rank: Sequence[Fraction],
        alpha: Fraction = Fraction(17, 20),
    ) -> bool:
        return _invoke(
            "verify",
            nodes=list(graph.get("nodes", [])),
            edges=_edges(graph.get("edges", [])),
            evidence=evidence,
            declared_transition_matrix=declared_transition_matrix,
            candidate_rank=candidate_rank,
            alpha=alpha,
        )

    def verify_rank_certificate(
        self,
        *,
        nodes: Sequence[str],
        edges: Sequence[Any],
        candidate_rank: Sequence[Fraction],
        evidence: Optional[Dict[str, Any]] = None,
        alpha: Fraction = Fraction(17, 20),
    ) -> bool:
        return _invoke(
            "verify",
            nodes=list(nodes),
            edges=_edges(edges),
            evidence=evidence,
            candidate_rank=candidate_rank,
            alpha=alpha,
        )


class ExactRowReductionSolverV1:
    def __init__(
        self, max_nodes: int = 1000, max_edges: int = 5000, max_bit_length: int = 4096
    ) -> None:
        self.max_nodes = max_nodes
        self.max_edges = max_edges
        self.max_bit_length = max_bit_length

    def solve_fixed_point(
        self,
        num_nodes: int,
        edges: Sequence[Any],
        evidence: Optional[Dict[str, Any]] = None,
        alpha: Fraction = Fraction(17, 20),
        nodes: Optional[Sequence[str]] = None,
    ) -> List[Fraction]:
        values = _invoke(
            "solve",
            num_nodes=num_nodes,
            edges=_edges(edges),
            evidence=evidence,
            alpha=alpha,
            nodes=None if nodes is None else list(nodes),
            max_nodes=self.max_nodes,
            max_edges=self.max_edges,
            max_bit_length=self.max_bit_length,
        )
        return [Fraction(value) for value in values]


__all__ = [
    "AncestralRankCalculatorV1",
    "ExactRowReductionSolverV1",
    "RankCertificateVerifierV1",
    "reconstruct_transition_matrix",
]
