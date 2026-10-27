r"""PolarizedOperadTriad aggregate root managing O = O^+ \sqcup O^- \sqcup O_repair.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from pfp.domain.operad.errors import (
    ArityMismatchError,
    IllTypedCompositionError,
    OperadError,
    OperadRoleViolationError,
    SliceViolationError,
)
from pfp.domain.operad.graft import GraftSite, PlanarGraft
from pfp.domain.operad.morphisms import (
    ConstructiveMorphism,
    InterrogativeMorphism,
    RepairMorphism,
)
from pfp.domain.operad.polarity import Polarity


@dataclass
class PolarizedOperadTriad:
    """Aggregate root managing the polarized operadic triad and partial composition.

    Maintains strictly disjoint sub-operads:
    - constructive: O^+ (generative / candidate proposing)
    - interrogative: O^- (anti-skills / findings & obligations)
    - corrective: O_repair (remediation / candidate patch proposing)
    """

    constructive: dict[str, ConstructiveMorphism] = field(default_factory=dict)
    interrogative: dict[str, InterrogativeMorphism] = field(default_factory=dict)
    corrective: dict[str, RepairMorphism] = field(default_factory=dict)
    licensed_slices: dict[str, set[str]] = field(default_factory=dict)

    def register_constructive(self, morphism: ConstructiveMorphism) -> None:
        """Register a morphism in O^+."""
        if not isinstance(morphism, ConstructiveMorphism) or morphism.polarity is not Polarity.CONSTRUCTIVE:
            raise OperadRoleViolationError(
                f"Cannot register {morphism} as constructive; must be ConstructiveMorphism with CONSTRUCTIVE polarity"
            )
        self.constructive[morphism.name] = morphism

    def register_interrogative(self, morphism: InterrogativeMorphism) -> None:
        """Register a morphism in O^-."""
        if not isinstance(morphism, InterrogativeMorphism) or morphism.polarity is not Polarity.INTERROGATIVE:
            raise OperadRoleViolationError(
                f"Cannot register {morphism} as interrogative; must be InterrogativeMorphism with INTERROGATIVE polarity"
            )
        self.interrogative[morphism.name] = morphism

    def register_corrective(self, morphism: RepairMorphism) -> None:
        """Register a morphism in O_repair."""
        if not isinstance(morphism, RepairMorphism) or morphism.polarity is not Polarity.CORRECTIVE:
            raise OperadRoleViolationError(
                f"Cannot register {morphism} as corrective; must be RepairMorphism with CORRECTIVE polarity"
            )
        self.corrective[morphism.name] = morphism

    def grant_slice(self, agent_role: str, morphism_names: set[str]) -> None:
        """Grant an agent role permission to invoke a specific set of operad morphisms."""
        if agent_role not in self.licensed_slices:
            self.licensed_slices[agent_role] = set()
        self.licensed_slices[agent_role].update(morphism_names)

    def check_slice_permission(self, agent_role: str, morphism_name: str) -> None:
        """Verify that an agent role has licensed authority to call morphism_name."""
        allowed = self.licensed_slices.get(agent_role, set())
        if morphism_name not in allowed:
            raise SliceViolationError(
                f"Agent role '{agent_role}' attempted to invoke unlicensed operad operation '{morphism_name}'; "
                f"licensed operations: {sorted(allowed)}"
            )

    def partial_compose(
        self,
        parent: ConstructiveMorphism,
        child: ConstructiveMorphism,
        i: int,
    ) -> ConstructiveMorphism:
        """Execute partial operadic composition f circle_i g at 0-indexed port i.

        Checks:
        1. Both parent and child must have constructive polarity (O^+).
        2. 0 <= i < arity(parent), else raises ArityMismatchError.
        3. parent.input_types[i] == child.output_type, else raises IllTypedCompositionError.
        Returns composite ConstructiveMorphism.
        """
        if not getattr(parent, "polarity", None) or not parent.polarity.is_constructive:
            raise OperadRoleViolationError(
                f"Parent morphism '{getattr(parent, 'name', parent)}' has non-constructive polarity "
                f"'{getattr(parent, 'polarity', None)}'; partial composition only permitted for constructive morphisms (O^+)"
            )
        if not getattr(child, "polarity", None) or not child.polarity.is_constructive:
            raise OperadRoleViolationError(
                f"Child morphism '{getattr(child, 'name', child)}' has non-constructive polarity "
                f"'{getattr(child, 'polarity', None)}'; partial composition only permitted for constructive morphisms (O^+)"
            )

        if i < 0 or i >= parent.arity:
            raise ArityMismatchError(
                f"Composition index {i} out of bounds for parent '{parent.name}' of arity {parent.arity}"
            )

        expected_type = parent.input_types[i]
        actual_type = child.output_type
        if expected_type != actual_type:
            raise IllTypedCompositionError(
                f"Partial composition {parent.name} circle_{i} {child.name} violates type matching: "
                f"parent expects '{expected_type}' at port {i}, but child produces '{actual_type}'"
            )

        # New input types: parent inputs before i + child inputs + parent inputs after i
        new_inputs = parent.input_types[:i] + child.input_types + parent.input_types[i + 1 :]
        new_name = f"({parent.name}_o_{i}_{child.name})"

        composite = ConstructiveMorphism(
            name=new_name,
            input_types=new_inputs,
            output_type=parent.output_type,
            polarity=Polarity.CONSTRUCTIVE,
        )
        return composite

    def create_graft(
        self,
        site: GraftSite,
        target_id: str,
        morphism_name: str,
        seam_index: int | None = None,
        expected_type: str | None = None,
        actual_type: str | None = None,
    ) -> PlanarGraft:
        """Create a typed PlanarGraft for verification at V, E, or T site."""
        return PlanarGraft(
            site=site,
            target_id=target_id,
            morphism_name=morphism_name,
            seam_index=seam_index,
            expected_type=expected_type,
            actual_type=actual_type,
        )


__all__ = ["PolarizedOperadTriad"]
