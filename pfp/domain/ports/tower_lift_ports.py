"""Domain protocols for Discrete Manifold Tower Lift Necessity (Prompt 28).

AuthorityEffect: None.
Clean Architecture: Domain port protocols (@runtime_checkable).
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from ..tower_lift.models import BinaryRelation, CarrierSet, LiftExhaustionReceipt


@runtime_checkable
class IFiniteExhaustionSearch(Protocol):
    """Protocol for enumerating relations and computing cryptographic exhaustion digests."""

    def enumerate_relations(self, carrier: CarrierSet) -> Sequence[BinaryRelation]:
        """Enumerates all 2^(|X|^2) candidate binary relations on carrier."""
        ...

    def compute_exhaustion_digest(
        self, from_stage: int, goal: str, results: Sequence[bool]
    ) -> str:
        """Computes deterministic SHA-256 digest over sorted enumeration test outcomes."""
        ...


@runtime_checkable
class ILiftNecessityVerifier(Protocol):
    """Protocol for verifying necessity of tower lifts across stages."""

    def verify_stage_0_to_1(self) -> LiftExhaustionReceipt:
        """Verifies irreflexive witnessed relation is unachievable on Stage 0 (|X|=1)."""
        ...

    def verify_stage_1_to_2_path(self) -> LiftExhaustionReceipt:
        """Verifies length-2 path composition is unachievable on Stage 1 (|X|=2)."""
        ...

    def verify_stage_1_to_2_cycle(self) -> LiftExhaustionReceipt:
        """Verifies directed 3-cycle is unachievable on Stage 1 (|X|=2)."""
        ...
