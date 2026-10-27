"""Antimorphism transition models, involution algebra, and protected distinction preservation.

Zero outward dependencies.
AuthorityEffect: None.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence

from pfp.domain.mssn_research.shared_kernel.result import Failure, Result, Success, err, ok
from .errors import (
    DecodingError,
    InvolutionIdentityError,
    ProtectedDistinctionCollapseError,
)


@dataclass(frozen=True)
class EdgeInvolution:
    """Involution mapping for an individual transition edge: e |-> e^dagger."""

    source_edge: str
    reversed_edge: str

    def __post_init__(self) -> None:
        if not self.source_edge or not self.reversed_edge:
            raise ValueError("Edge labels must be non-empty strings")

    def is_dissipative(self) -> bool:
        """True if the edge has no reversible preimage, representing irreversible entropy dissipation."""
        return self.reversed_edge in ("bot", "<bot>", "", "None")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EdgeInvolution)
        return self.source_edge == other.source_edge and self.reversed_edge == other.reversed_edge

    def __hash__(self) -> int:
        return hash((type(self), self.source_edge, self.reversed_edge))


@dataclass(frozen=True)
class ReversalMap:
    """Lookup table of edge involutions across a transition graph."""

    involutions: tuple[EdgeInvolution, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.involutions, tuple):
            object.__setattr__(self, "involutions", tuple(self.involutions))

    def reverse(self, edge: str) -> Optional[str]:
        """Returns the reversed edge or None if dissipative / unmapped."""
        for inv in self.involutions:
            if inv.source_edge == edge:
                return None if inv.is_dissipative() else inv.reversed_edge
        return None

    def satisfies_involution_law(self) -> bool:
        """Verifies the Involution Law: ((e)^dagger)^dagger = e for all reversible edges."""
        for inv in self.involutions:
            if inv.is_dissipative():
                continue
            rev = self.reverse(inv.reversed_edge)
            if rev != inv.source_edge:
                return False
        return True

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ReversalMap)
        return self.involutions == other.involutions

    def __hash__(self) -> int:
        return hash((type(self), self.involutions))


@dataclass(frozen=True)
class ProtectedDistinction:
    """An essential boundary distinction (state_a != state_b) that must not collapse under projection."""

    state_a: str
    state_b: str
    label: str = ""

    def __post_init__(self) -> None:
        if self.state_a == self.state_b:
            raise ValueError(f"Protected distinction requires distinct states, got ({self.state_a}, {self.state_b})")

    def is_collapsed_by(self, projection: Mapping[str, str]) -> bool:
        """Returns True if the projection maps state_a and state_b to the same target state."""
        proj_a = projection.get(self.state_a, self.state_a)
        proj_b = projection.get(self.state_b, self.state_b)
        return proj_a == proj_b

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ProtectedDistinction)
        return (
            frozenset((self.state_a, self.state_b)) == frozenset((other.state_a, other.state_b))
            and self.label == other.label
        )

    def __hash__(self) -> int:
        return hash((type(self), frozenset((self.state_a, self.state_b)), self.label))


@dataclass(frozen=True)
class AntimorphismTransitionModel:
    """Transition model with contravariant path inversion and boundary conservation."""

    model_id: str
    states: frozenset[str]
    edges: frozenset[str]
    reversal_map: ReversalMap
    protected_distinctions: frozenset[ProtectedDistinction]

    def reverse_edge(self, edge: str) -> str:
        """Reverse a single edge. Raises InvolutionIdentityError if edge is irreversible."""
        rev = self.reversal_map.reverse(edge)
        if rev is None:
            raise InvolutionIdentityError(
                f"Edge '{edge}' is irreversible (dissipative or missing involution in reversal map)"
            )
        return rev

    def reverse_path(self, path: Sequence[str]) -> tuple[str, ...]:
        """Contravariant path composition: (e1 . e2 ... . ek)^dagger = ek^dagger ... . e2^dagger . e1^dagger."""
        reversed_edges: list[str] = []
        for edge in reversed(path):
            rev_e = self.reverse_edge(edge)
            reversed_edges.append(rev_e)
        return tuple(reversed_edges)

    def satisfies_involution(self) -> bool:
        """Verifies the Involution Law on the underlying reversal map."""
        return self.reversal_map.satisfies_involution_law()

    def down_map(self, projection: Mapping[str, str]) -> AntimorphismTransitionModel:
        """Execute a state space reduction projection, refusing if any protected distinction collapses."""
        for dist in self.protected_distinctions:
            if dist.is_collapsed_by(projection):
                raise ProtectedDistinctionCollapseError(
                    f"Projection collapses protected distinction ({dist.state_a}, {dist.state_b}) [{dist.label}]"
                )

        projected_states = frozenset(projection.get(s, s) for s in self.states)
        return AntimorphismTransitionModel(
            model_id=f"{self.model_id}/projected",
            states=projected_states,
            edges=self.edges,
            reversal_map=self.reversal_map,
            protected_distinctions=self.protected_distinctions,
        )

    def reverse_edge_result(self, edge: str) -> Result[str, DecodingError]:
        try:
            return ok(self.reverse_edge(edge))
        except DecodingError as exc:
            return err(exc)

    def reverse_path_result(self, path: Sequence[str]) -> Result[tuple[str, ...], DecodingError]:
        try:
            return ok(self.reverse_path(path))
        except DecodingError as exc:
            return err(exc)

    def down_map_result(self, projection: Mapping[str, str]) -> Result[AntimorphismTransitionModel, DecodingError]:
        try:
            return ok(self.down_map(projection))
        except DecodingError as exc:
            return err(exc)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AntimorphismTransitionModel)
        return (
            self.model_id == other.model_id
            and self.states == other.states
            and self.edges == other.edges
            and self.reversal_map == other.reversal_map
            and self.protected_distinctions == other.protected_distinctions
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.model_id,
            self.states,
            self.edges,
            self.reversal_map,
            self.protected_distinctions,
        ))


__all__ = [
    "AntimorphismTransitionModel",
    "EdgeInvolution",
    "ProtectedDistinction",
    "ReversalMap",
]
