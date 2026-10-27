"""CochainProjector domain entity for discrete cochain problem projections.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from pfp.domain.shared_kernel.canonical import domain_digest, freeze
from pfp.functional_boundary import require_rust_functional
from pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from pfp.domain.entities.projection_receipt import Obstruction, ProjectionReceipt
from pfp.domain.entities.cochain import CochainCarrier, CochainState
from pfp.domain.entities.problem import Projector


@dataclass(frozen=True, slots=True)
class CochainProjector(Projector):
    carrier: CochainCarrier
    tolerance: float = 1.0e-8
    projector_id: str = "coda-face-aware-phi1-gamma2-projector-v1"
    research_parent_event_id: str | None = None

    def __init__(
        self,
        carrier: CochainCarrier,
        tolerance: float = 1.0e-8,
        projector_id: str = "coda-face-aware-phi1-gamma2-projector-v1",
        research_parent_event_id: str | None = None,
    ) -> None:
        object.__setattr__(self, "carrier", carrier)
        object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "projector_id", projector_id)
        object.__setattr__(self, "research_parent_event_id", research_parent_event_id)

    @property
    def config_digest(self) -> str:
        config: dict[str, Any] = {
            "projector_id": self.projector_id,
            "carrier": self.carrier,
            "tolerance": self.tolerance,
        }
        if self.research_parent_event_id is not None:
            config["research_parent_event_id"] = self.research_parent_event_id
        return domain_digest(
            "core.oesos.projector-config.v1",
            config,
        )

    def meaning(self, state: Any) -> Any:
        if not isinstance(state, CochainState):
            raise TypeError("cochain projector requires CochainState")
        if set(state.as_mapping()) != set(self.carrier.edges):
            raise ValueError("cochain support must equal the declared carrier edges")
        return state

    def skeleton(self, state: Any) -> Any:
        self.meaning(state)
        return self.carrier

    def validate_packet(
        self,
        envelope: PacketEnvelopeV2,
        native_initial_state: Any,
    ) -> bool:
        if not isinstance(native_initial_state, CochainState):
            return False
        self.meaning(native_initial_state)
        expected_payload: dict[str, Any] = {
            "carrier": self.carrier,
            "omega": native_initial_state.values,
            "canonical_rust_owner": "core_solvers::solver_of_solvers",
        }
        if self.research_parent_event_id is not None:
            expected_payload["research_parent_event_id"] = self.research_parent_event_id
        expected_constraints = (
            "d1*d0=0",
            "finite exact carrier",
            "separate phi1 from gamma2",
        )
        return (
            envelope.carrier_id == "finite-cochain-2-v1"
            and envelope.parent_event_id == self.research_parent_event_id
            and envelope.constraints == expected_constraints
            and envelope.payload == freeze(expected_payload)
            and envelope.source_digest
            == domain_digest("core.oesos.coda-fixture.v1", expected_payload)
        )

    def project(self, state: Any) -> ProjectionReceipt:
        require_rust_functional("CochainProjector.project")

    def verify_retraction(
        self,
        solver_id: str,
        before_state: Any,
        after_state: Any,
    ) -> bool:
        if solver_id not in {
            "coda-face-aware-phi1-gamma2-cascade-solver-v1",
            "existing-coda-cascade-proposal",
        }:
            return False
        before = self.meaning(before_state)
        after = self.meaning(after_state)
        if before == after:
            return False
        before_skeleton = self.skeleton(before)
        after_skeleton = self.skeleton(after)
        after_projection = self.project(after)
        return (
            before_skeleton == after_skeleton
            and after_projection.is_exact
        )


__all__ = ["CochainProjector"]
