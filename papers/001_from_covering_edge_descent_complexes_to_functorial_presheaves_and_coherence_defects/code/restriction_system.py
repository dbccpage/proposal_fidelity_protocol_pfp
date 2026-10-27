"""Restriction systems on finite posets, Path A strict completion, and functoriality checks for PO-001.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

from exact import (
    ExactInput,
    as_rational,
    exact_equal,
    exact_matrix_from_matrix,
    l1_norm,
)
from exactsym import Basic, Matrix, simplify

from covering_edge_poset import CoverEdge, ComparablePair, FinitePoset, NodeId


@dataclass(frozen=True)
class RestrictionMap:
    """A linear restriction map from source fiber to target fiber: r: F(source) -> F(target)."""

    source: NodeId
    target: NodeId
    matrix: Matrix

    def __post_init__(self) -> None:
        object.__setattr__(self, "matrix", exact_matrix_from_matrix(self.matrix))

    def __call__(self, vector: Matrix) -> Matrix:
        """Apply restriction operator r to vector v."""
        return self.matrix * vector

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RestrictionMap):
            return False
        return self.source == other.source and self.target == other.target and exact_equal(self.matrix, other.matrix)


class RestrictionSystem:
    """A collection of restriction maps over a finite poset."""

    def __init__(
        self,
        poset: FinitePoset,
        fiber_dimensions: Mapping[NodeId, int],
        restrictions: Sequence[RestrictionMap],
    ) -> None:
        self.poset = poset
        self.fiber_dimensions = dict(fiber_dimensions)

        # Validate dimensions
        for node in poset.elements:
            if node not in self.fiber_dimensions:
                raise ValueError(f"missing fiber dimension for node {node}")
            if self.fiber_dimensions[node] <= 0:
                raise ValueError(f"fiber dimension for node {node} must be positive")

        self._map: dict[tuple[NodeId, NodeId], RestrictionMap] = {}
        for r in restrictions:
            pair = (r.target, r.source)  # target <= source in poset order (restriction goes down!)
            if not poset.is_le(r.target, r.source):
                raise ValueError(f"restriction target {r.target} is not <= source {r.source}")
            expected_rows = self.fiber_dimensions[r.target]
            expected_cols = self.fiber_dimensions[r.source]
            if r.matrix.rows != expected_rows or r.matrix.cols != expected_cols:
                raise ValueError(
                    f"restriction {r.source}->{r.target} shape {r.matrix.shape} != ({expected_rows}, {expected_cols})"
                )
            if pair in self._map:
                raise ValueError(f"duplicate restriction declaration for {r.source}->{r.target}")
            if r.source == r.target and not exact_equal(r.matrix, Matrix.eye(expected_rows)):
                raise ValueError(f"self restriction for {r.source} must be the identity")
            self._map[pair] = r

    def get_restriction(self, target: NodeId, source: NodeId) -> RestrictionMap:
        """Get restriction map r: F(source) -> F(target) where target <= source."""
        if not self.poset.is_le(target, source):
            raise KeyError(f"({target}, {source}) is not a declared comparable pair")
        if target == source:
            # Identity map
            dim = self.fiber_dimensions[target]
            return RestrictionMap(source=source, target=target, matrix=Matrix.eye(dim))
        pair = (target, source)
        if pair not in self._map:
            raise KeyError(f"no restriction map registered for {source} -> {target}")
        return self._map[pair]

    def has_restriction(self, target: NodeId, source: NodeId) -> bool:
        if not self.poset.is_le(target, source):
            return False
        if target == source:
            return True
        return (target, source) in self._map

    def chain_composite(self, chain_nodes: Sequence[NodeId]) -> Matrix:
        """Compute restriction along an ascending chain (bottom, ..., top).
        
        chain_nodes is ordered (c_0, c_1, ..., c_k) where c_0 <= c_1 <= ... <= c_k.
        The composite maps F(c_k) -> ... -> F(c_0).
        """
        if not chain_nodes:
            raise ValueError("chain must contain at least one declared node")
        if any(node not in self.poset.elements for node in chain_nodes):
            raise ValueError("chain contains an undeclared node")
        if len(chain_nodes) == 1:
            dim = self.fiber_dimensions[chain_nodes[0]]
            return Matrix.eye(dim)

        # Start from top
        curr_mat = Matrix.eye(self.fiber_dimensions[chain_nodes[-1]])
        for i in range(len(chain_nodes) - 1, 0, -1):
            upper = chain_nodes[i]
            lower = chain_nodes[i - 1]
            r = self.get_restriction(target=lower, source=upper)
            curr_mat = r.matrix * curr_mat

        return curr_mat


def check_path_a_diamond_independence(
    poset: FinitePoset,
    system: RestrictionSystem,
    bottom: NodeId,
    left: NodeId,
    right: NodeId,
    top: NodeId,
) -> tuple[bool, Matrix]:
    """Check if left path and right path around diamond agree:
    
    r_{left, bottom} * r_{top, left} == r_{right, bottom} * r_{top, right}.
    Returns (is_independent, defect_matrix).
    """
    if not poset.is_diamond(bottom, left, right, top):
        raise ValueError(f"nodes ({bottom}, {left}, {right}, {top}) do not form a diamond")

    left_comp = system.chain_composite([bottom, left, top])
    right_comp = system.chain_composite([bottom, right, top])
    defect = left_comp - right_comp
    is_zero = exact_equal(defect, Matrix.zeros(*defect.shape))
    return is_zero, defect


def build_path_a_completion(
    poset: FinitePoset,
    fiber_dimensions: Mapping[NodeId, int],
    covering_restrictions: Sequence[RestrictionMap],
) -> RestrictionSystem:
    """Under Path A (assuming saturated chain composites are path-independent),
    construct the complete functorial presheaf extension for all comparable pairs.
    """
    # First build temporary system with covering edges
    cov_system = RestrictionSystem(poset, fiber_dimensions, covering_restrictions)

    completed_restrictions: list[RestrictionMap] = []

    for pair in poset.comparable_pairs():
        target, source = pair.lower, pair.upper
        if target == source:
            continue
        chains = poset.saturated_chains(target, source)
        if not chains:
            raise RuntimeError(f"no saturated chains found for {target} <= {source}")

        # Path A assumes all chains yield identical composites; evaluate first chain
        first_comp = cov_system.chain_composite(chains[0])

        # Verify path independence across all alternative saturated chains
        for alt_chain in chains[1:]:
            alt_comp = cov_system.chain_composite(alt_chain)
            if not exact_equal(first_comp, alt_comp):
                raise ValueError(
                    f"Path A hypothesis violated: chains {chains[0]} and {alt_chain} yield different composites"
                )

        completed_restrictions.append(
            RestrictionMap(source=source, target=target, matrix=first_comp)
        )

    return RestrictionSystem(poset, fiber_dimensions, completed_restrictions)
