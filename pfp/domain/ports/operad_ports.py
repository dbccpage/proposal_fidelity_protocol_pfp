"""Domain ports (protocols) for operadic routing and graft evaluation.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Mapping, Protocol, runtime_checkable

from pfp.domain.operad.graft import PlanarGraft


@runtime_checkable
class IOperadRouter(Protocol):
    """Port interface for dispatching operad morphisms and verifying slices."""

    def route_morphism(self, name: str, args: Any) -> Any:
        """Route and execute an operad morphism."""
        ...

    def check_slice(self, agent_role: str, morphism_name: str) -> None:
        """Verify that agent role has capability slice license for morphism."""
        ...


@runtime_checkable
class IPlanarGraftEvaluator(Protocol):
    """Port interface for evaluating planar graft site invariants."""

    def evaluate_graft(
        self, graft: PlanarGraft, context: Mapping[str, Any]
    ) -> tuple[bool, str]:
        """Evaluate planar graft invariants at V, E, or T site."""
        ...


__all__ = [
    "IOperadRouter",
    "IPlanarGraftEvaluator",
]
