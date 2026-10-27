"""Finite partially ordered sets, covering relations, and saturated chains for PO-001.

AuthorityEffect: None.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import TypeAlias

NodeId: TypeAlias = str


@dataclass(frozen=True)
class CoverEdge:
    """A covering relation a -< b (a is covered by b, meaning a < b and no x has a < x < b)."""

    lower: NodeId
    upper: NodeId

    def __post_init__(self) -> None:
        if self.lower == self.upper:
            raise ValueError(f"cover relation cannot be reflexive: {self.lower}")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CoverEdge):
            return False
        return self.lower == other.lower and self.upper == other.upper


@dataclass(frozen=True)
class ComparablePair:
    """A comparable pair a <= b in the poset."""

    lower: NodeId
    upper: NodeId

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ComparablePair):
            return False
        return self.lower == other.lower and self.upper == other.upper


class FinitePoset:
    """A finite partially ordered set defined by elements and relation pairs."""

    def __init__(
        self,
        elements: Collection[NodeId],
        relations: Collection[tuple[NodeId, NodeId]],
    ) -> None:
        self.elements: tuple[NodeId, ...] = tuple(sorted(set(elements)))
        elem_set = set(self.elements)
        if not elem_set:
            raise ValueError("poset must contain at least one element")

        # Build reflexive-transitive closure of pairs (a, b) meaning a <= b
        leq: set[tuple[NodeId, NodeId]] = {(x, x) for x in self.elements}
        for a, b in relations:
            if a not in elem_set or b not in elem_set:
                raise ValueError(f"relation ({a}, {b}) contains elements not in poset")
            leq.add((a, b))

        # Transitive closure
        changed = True
        while changed:
            changed = False
            new_pairs = set()
            for a, b in leq:
                for c, d in leq:
                    if b == c and (a, d) not in leq:
                        new_pairs.add((a, d))
                        changed = True
            leq.update(new_pairs)

        # Antisymmetry check: a <= b and b <= a implies a == b
        for a, b in leq:
            if a != b and (b, a) in leq:
                raise ValueError(f"poset relation is not antisymmetric: ({a}, {b}) and ({b}, {a}) both hold")

        self._leq: frozenset[tuple[NodeId, NodeId]] = frozenset(leq)

        # Extract covering relations: a < b and no c with a < c < b
        covering: set[CoverEdge] = set()
        for a, b in self._leq:
            if a == b:
                continue
            # Check if there is an intermediate element
            has_intermediate = False
            for c in self.elements:
                if c != a and c != b and (a, c) in self._leq and (c, b) in self._leq:
                    has_intermediate = True
                    break
            if not has_intermediate:
                covering.add(CoverEdge(lower=a, upper=b))

        self.covering_edges: tuple[CoverEdge, ...] = tuple(sorted(covering, key=lambda e: (e.lower, e.upper)))

    def is_le(self, a: NodeId, b: NodeId) -> bool:
        """Check if a <= b."""
        return (a, b) in self._leq

    def is_lt(self, a: NodeId, b: NodeId) -> bool:
        """Check if a < b."""
        return a != b and (a, b) in self._leq

    def is_covering(self, a: NodeId, b: NodeId) -> bool:
        """Check if a is covered by b (a -< b)."""
        if not self.is_lt(a, b):
            return False
        return CoverEdge(lower=a, upper=b) in self.covering_edges

    def comparable_pairs(self) -> tuple[ComparablePair, ...]:
        """Return all comparable pairs (a, b) with a <= b."""
        pairs = [ComparablePair(lower=a, upper=b) for a, b in self._leq]
        return tuple(sorted(pairs, key=lambda p: (p.lower, p.upper)))

    def strict_comparable_pairs(self) -> tuple[ComparablePair, ...]:
        """Return all strictly comparable pairs (a, b) with a < b."""
        pairs = [ComparablePair(lower=a, upper=b) for a, b in self._leq if a != b]
        return tuple(sorted(pairs, key=lambda p: (p.lower, p.upper)))

    def saturated_chains(self, a: NodeId, b: NodeId) -> list[tuple[NodeId, ...]]:
        """Return all saturated chains (paths of covering edges) from a up to b."""
        if a not in self.elements or b not in self.elements:
            return []
        if a == b:
            return [(a,)]
        if not self.is_lt(a, b):
            return []

        chains: list[tuple[NodeId, ...]] = []

        def _dfs(current: NodeId, path: list[NodeId]) -> None:
            if current == b:
                chains.append(tuple(path))
                return
            for edge in self.covering_edges:
                if edge.lower == current and self.is_le(edge.upper, b):
                    _dfs(edge.upper, path + [edge.upper])

        _dfs(a, [a])
        return chains

    def is_diamond(self, bottom: NodeId, left: NodeId, right: NodeId, top: NodeId) -> bool:
        """Verify if 4 nodes form an elementary diamond: bottom -< left -< top and bottom -< right -< top."""
        if len({bottom, left, right, top}) != 4:
            return False
        return (
            self.is_covering(bottom, left)
            and self.is_covering(left, top)
            and self.is_covering(bottom, right)
            and self.is_covering(right, top)
        )
