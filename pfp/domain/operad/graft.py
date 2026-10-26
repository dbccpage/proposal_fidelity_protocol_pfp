"""Planar Graft Sites and Invariant Evaluation for the Polarized Operad.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
import enum
from typing import Any, Mapping, Sequence

from omega_engine_pfp.domain.operad.errors import (
    IllTypedCompositionError,
    OperadError,
)


@enum.unique
class GraftSite(str, enum.Enum):
    """The 3 canonical planar tree grafting sites for anti-skill binding.

    - VERTEX: V-graft evaluating a single generator f in O^+ (local defect, pre-generation).
    - EDGE: E-graft evaluating partial composition seam f circle_i g (boundary type escalation, seam).
    - TREE: T-graft evaluating entire planar tree T in Trees(O) (circular dependencies, post-AST).
    """

    VERTEX = "VERTEX"
    EDGE = "EDGE"
    TREE = "TREE"

    @property
    def is_vertex(self) -> bool:
        return self is GraftSite.VERTEX

    @property
    def is_edge(self) -> bool:
        return self is GraftSite.EDGE

    @property
    def is_tree(self) -> bool:
        return self is GraftSite.TREE


@dataclass(frozen=True)
class PlanarGraft:
    """A planar graft binding an interrogation or verification check to a specific tree site."""

    site: GraftSite
    target_id: str
    morphism_name: str
    seam_index: int | None = None
    expected_type: str | None = None
    actual_type: str | None = None

    def __post_init__(self) -> None:
        if self.site is GraftSite.EDGE and self.seam_index is None:
            raise OperadError("EDGE graft site requires non-null seam_index")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.site == other.site
            and self.target_id == other.target_id
            and self.morphism_name == other.morphism_name
            and self.seam_index == other.seam_index
            and self.expected_type == other.expected_type
            and self.actual_type == other.actual_type
        )

    def evaluate_invariants(self, context: Mapping[str, Any]) -> tuple[bool, str]:
        """Evaluate generator, seam, and whole-tree invariants based on graft site."""
        if self.site is GraftSite.VERTEX:
            # V-graft: evaluate single generator validity
            is_valid = context.get("generator_valid", True)
            if not is_valid:
                return False, f"VERTEX generator invariant violated on {self.target_id}"
            return True, "VERTEX generator invariant satisfied"

        elif self.site is GraftSite.EDGE:
            # E-graft: evaluate composition seam boundary type compatibility
            expected = self.expected_type or context.get("expected_type")
            actual = self.actual_type or context.get("actual_type")
            if expected is not None and actual is not None and expected != actual:
                return (
                    False,
                    f"EDGE seam invariant violated at index {self.seam_index}: "
                    f"type mismatch expected '{expected}' but got '{actual}'",
                )
            return True, "EDGE seam invariant satisfied"

        elif self.site is GraftSite.TREE:
            # T-graft: evaluate whole-tree circularity and boundary nilpotency (d1 circ d0 == 0)
            has_cycle = context.get("has_circular_dependency", False)
            if has_cycle:
                return False, f"TREE composite invariant violated: circular dependency detected in {self.target_id}"
            boundary_leakage = context.get("boundary_leakage", 0)
            if boundary_leakage != 0:
                return False, f"TREE composite invariant violated: non-zero boundary leakage {boundary_leakage}"
            return True, "TREE composite invariant satisfied"

        return False, f"Unknown graft site: {self.site}"


__all__ = ["GraftSite", "PlanarGraft"]
