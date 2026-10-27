"""Factory methods for building Airy RuntimeProblem instances for the Symbol Game."""

from __future__ import annotations

from typing import Any

from pfp.domain.entities import PacketEnvelopeV2
from pfp.domain.entities.airy import (
    AiryCriticalCarrierV1,
    AiryCriticalStateV1,
    AirySeedSlotV1,
    ComplexScalarV1,
)
from pfp.domain.entities.airy_projector import (
    AIRY_CARRIER_ID,
    AIRY_OBSTRUCTION_ID,
    AIRY_PACKET_FAMILY,
    AiryCriticalProjector,
    _payload,
)
from pfp.domain.entities.problem import (
    DetectorCase,
    IdentityAdapter,
    RuntimeProblem,
)
from pfp.domain.shared_kernel.canonical import domain_digest, freeze

DEFAULT_AIRY_LAMBDA = 1.0 + 0.4j
DEFAULT_AIRY_SEEDS = (
    0.5 + 0.5j,
    -0.5 - 0.5j,
    2.0 + 0.1j,
    -2.0 + 0.3j,
    0.1 - 1.2j,
)
DEFAULT_AIRY_SLOT_IDS = tuple(f"seed-{index:02d}" for index in range(5))


def _is_sha256(value: Any) -> bool:
    return bool(
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _require_sha256(value: Any, label: str) -> str:
    if not _is_sha256(value):
        raise ValueError(f"{label} must be a lowercase SHA-256 digest")
    return value


def build_airy_problem(
    *,
    task_id: str = "witten-airy-critical-five-seed",
    lam: complex = DEFAULT_AIRY_LAMBDA,
    seeds: tuple[complex, ...] = DEFAULT_AIRY_SEEDS,
    research_parent_event_id: str,
    source_digest: str,
) -> RuntimeProblem:
    """Build the strictly source-bound finite Airy OESOS problem."""
    _require_sha256(research_parent_event_id, "research_parent_event_id")
    _require_sha256(source_digest, "source_digest")

    if len(seeds) != 5:
        raise ValueError("Airy critical problem requires exactly five seeds")

    carrier = AiryCriticalCarrierV1(
        lambda_scalar=ComplexScalarV1.from_complex(lam),
        slot_ids=DEFAULT_AIRY_SLOT_IDS,
        research_parent_event_id=research_parent_event_id,
        source_digest=source_digest,
    )
    initial_slots = tuple(
        AirySeedSlotV1(slot_id=slot_id, value=ComplexScalarV1.from_complex(seed))
        for slot_id, seed in zip(DEFAULT_AIRY_SLOT_IDS, seeds)
    )
    initial_state = AiryCriticalStateV1(slots=initial_slots)

    exact_slots = tuple(
        AirySeedSlotV1(
            slot_id=slot_id,
            value=ComplexScalarV1.from_complex(1.0 + 0.0j if i % 2 == 0 else -1.0 + 0.0j),
        )
        for i, slot_id in enumerate(DEFAULT_AIRY_SLOT_IDS)
    )
    exact_state = AiryCriticalStateV1(slots=exact_slots)

    obstructed_slots = tuple(
        AirySeedSlotV1(slot_id=slot_id, value=ComplexScalarV1.from_complex(0.0j))
        for slot_id in DEFAULT_AIRY_SLOT_IDS
    )
    obstructed_state = AiryCriticalStateV1(slots=obstructed_slots)

    projector = AiryCriticalProjector(carrier=carrier)
    exact_projection = projector.project(exact_state)
    obstructed_projection = projector.project(obstructed_state)

    detector_cases = (
        DetectorCase(
            case_id="exact-five-seed-roots",
            native_state=exact_state,
            expected_active_ids=(),
            expected_projection_digest=exact_projection.control_digest,
        ),
        DetectorCase(
            case_id="obstructed-all-zero-seeds",
            native_state=obstructed_state,
            expected_active_ids=(AIRY_OBSTRUCTION_ID,),
            expected_projection_digest=obstructed_projection.control_digest,
        ),
    )

    initial_state_hash = domain_digest("core.oesos.native-state.v1", initial_state)
    payload = _payload(carrier, initial_state)

    envelope = PacketEnvelopeV2(
        task_id=task_id,
        packet_family=AIRY_PACKET_FAMILY,
        carrier_id=AIRY_CARRIER_ID,
        initial_state_hash=initial_state_hash,
        payload=freeze(payload),
        constraints=(AIRY_OBSTRUCTION_ID,),
        protected_boundaries=(AIRY_OBSTRUCTION_ID,),
        step_budget=16,
        authority_effect="None",
        parent_event_id=research_parent_event_id,
        source_digest=source_digest,
        allowed_transforms=("same_carrier_retraction",),
    )

    adapter = IdentityAdapter(
        source_carrier_id=AIRY_CARRIER_ID,
        target_carrier_id=AIRY_CARRIER_ID,
    )

    return RuntimeProblem(
        envelope=envelope,
        native_initial_state=initial_state,
        projector=projector,
        adapter=adapter,
        detector_cases=detector_cases,
        primitive_difference="discrete complex root deviation",
        zero_relation="all critical values vanish under lambda*(z^2-1)=0",
        observer_id=projector.projector_id,
        witness_certificate=f"research-parent:{research_parent_event_id}",
        protected_obstruction_ids=(AIRY_OBSTRUCTION_ID,),
    )

