"""Self-contained Airy critical projector implementation for symbol game domain.

AuthorityEffect: None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from omega_engine_pfp.domain.shared_kernel.canonical import domain_digest, freeze
from omega_engine_pfp.domain.entities.projection_receipt import Obstruction, ProjectionReceipt
from omega_engine_pfp.domain.entities.packet_envelope import PacketEnvelopeV2
from omega_engine_pfp.domain.entities.airy import (
    AiryCriticalCarrierV1,
    AiryCriticalStateV1,
    evaluate_airy_critical_residuals,
)

AIRY_PACKET_FAMILY = "witten_airy_critical"
AIRY_CARRIER_ID = "witten-airy-critical-five-slot-v1"
AIRY_OBSTRUCTION_ID = "WITTEN_AIRY_CRITICAL_EQUATION"
AIRY_SOLVER_ID = "witten-airy-bounded-newton-proposal-v1"
AIRY_PAYLOAD_SCHEMA = "omega.symbol-game.witten-airy-critical-payload.v1"


def _payload(
    carrier: AiryCriticalCarrierV1,
    initial_state: AiryCriticalStateV1,
) -> dict[str, Any]:
    return {
        "schema_version": AIRY_PAYLOAD_SCHEMA,
        "carrier": carrier,
        "initial_state": initial_state,
        "critical_equation": "lambda*(z^2-1)=0",
        "scope": "finite five-seed Airy critical-point search",
        "complex_encoding": "normalized-float-hex-pair-v1",
    }


@dataclass(frozen=True, slots=True)
class AiryCriticalProjector:
    carrier: AiryCriticalCarrierV1
    projector_id: str = "witten-airy-critical-projector-v1"

    @property
    def config_digest(self) -> str:
        return domain_digest(
            "omega.oesos.projector-config.v1",
            {
                "projector_id": self.projector_id,
                "carrier": self.carrier,
                "equation": "lambda*(z^2-1)=0",
            },
        )

    def meaning(self, state: Any) -> AiryCriticalStateV1:
        if type(state) is not AiryCriticalStateV1:
            raise TypeError("Airy projector requires AiryCriticalStateV1")
        if state.slot_ids != self.carrier.slot_ids:
            raise ValueError("Airy state slots must equal the carrier slot skeleton")
        return state

    def skeleton(self, state: Any) -> AiryCriticalCarrierV1:
        self.meaning(state)
        return self.carrier

    def validate_packet(
        self,
        envelope: PacketEnvelopeV2,
        native_initial_state: Any,
    ) -> bool:
        try:
            initial_state = self.meaning(native_initial_state)
        except (TypeError, ValueError):
            return False
        expected_payload = _payload(self.carrier, initial_state)
        return (
            envelope.packet_family == AIRY_PACKET_FAMILY
            and envelope.carrier_id == AIRY_CARRIER_ID
            and envelope.parent_event_id == self.carrier.research_parent_event_id
            and envelope.source_digest == self.carrier.source_digest
            and envelope.constraints == (AIRY_OBSTRUCTION_ID,)
            and envelope.protected_boundaries == (AIRY_OBSTRUCTION_ID,)
            and envelope.payload == freeze(expected_payload)
        )

    def project(self, state: Any) -> ProjectionReceipt:
        normalized = self.meaning(state)
        residuals, maximum = evaluate_airy_critical_residuals(self.carrier, normalized)
        obstructions = ()
        if maximum > 0.0:
            obstructions = (
                Obstruction(
                    obstruction_id=AIRY_OBSTRUCTION_ID,
                    magnitude=maximum,
                    witness=(
                        "independent-max-abs-lambda-times-z-squared-minus-one:"
                        f"{maximum.hex()}"
                    ),
                ),
            )
        return ProjectionReceipt(
            projector_id=self.projector_id,
            state_hash=domain_digest("omega.oesos.state.v1", normalized),
            obstructions=obstructions,
            witness="witten-airy-critical-independent-replay-v1",
            representative_l1_mass=maximum,
            authority_effect="None",
        )

    def verify_retraction(
        self,
        solver_id: str,
        before_state: Any,
        after_state: Any,
    ) -> bool:
        if solver_id != AIRY_SOLVER_ID:
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


__all__ = [
    "AIRY_CARRIER_ID",
    "AIRY_OBSTRUCTION_ID",
    "AIRY_PACKET_FAMILY",
    "AIRY_PAYLOAD_SCHEMA",
    "AIRY_SOLVER_ID",
    "AiryCriticalProjector",
]
