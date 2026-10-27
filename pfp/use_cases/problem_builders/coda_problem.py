"""Factory methods for building Coda RuntimeProblem instances for the Symbol Game."""

from __future__ import annotations

from pfp.domain.entities import PacketEnvelopeV2
from pfp.domain.entities.cochain import CochainCarrier, CochainState
from pfp.domain.entities.cochain_projector import CochainProjector
from pfp.domain.entities.problem import (
    DetectorCase,
    IdentityAdapter,
    RuntimeProblem,
)
from pfp.domain.shared_kernel.canonical import domain_digest, freeze

CODA_CARRIER_ID = "finite-cochain-2-v1"
CODA_PACKET_FAMILY = "cochain_obstruction"
CODA_CONSTRAINTS = (
    "d1*d0=0",
    "finite exact carrier",
    "separate phi1 from gamma2",
)


def build_coda_problem(
    *,
    task_id: str = "coda-face-aware-demo",
    research_parent_event_id: str | None = None,
    carrier: CochainCarrier | None = None,
    initial: CochainState | None = None,
) -> RuntimeProblem:
    if carrier is None:
        carrier = CochainCarrier(
            nodes=(0, 1, 2, 3),
            edges=((0, 1), (1, 2), (2, 0), (1, 3), (3, 0)),
            faces=((0, 1, 2), (0, 1, 3)),
            weights=(1, 1, 1, 1, 1),
        )
    elif type(carrier) is not CochainCarrier:
        raise TypeError("carrier must be a CochainCarrier")

    if initial is None:
        initial = CochainState.from_mapping(
            {
                (0, 1): 3.0,
                (1, 2): 2.0,
                (2, 0): 2.0,
                (1, 3): 1.0,
                (3, 0): 1.0,
            }
        )
    elif type(initial) is not CochainState:
        raise TypeError("initial must be a CochainState")

    if set(initial.as_mapping()) != set(carrier.edges):
        raise ValueError("initial cochain support must equal the carrier edges")

    exact = CochainState.from_mapping({edge: 0.0 for edge in carrier.edges})
    projector = CochainProjector(
        carrier,
        research_parent_event_id=research_parent_event_id,
    )
    exact_projection = projector.project(exact)
    initial_projection = projector.project(initial)

    payload = {
        "carrier": carrier,
        "omega": initial.values,
        "canonical_rust_owner": "core_solvers::solver_of_solvers",
    }
    if research_parent_event_id is not None:
        payload["research_parent_event_id"] = research_parent_event_id

    source_digest = domain_digest("core.oesos.coda-fixture.v1", payload)
    initial_state_hash = domain_digest("core.oesos.native-state.v1", initial)

    envelope = PacketEnvelopeV2(
        task_id=task_id,
        packet_family=CODA_PACKET_FAMILY,
        carrier_id=CODA_CARRIER_ID,
        initial_state_hash=initial_state_hash,
        payload=freeze(payload),
        constraints=CODA_CONSTRAINTS,
        protected_boundaries=("cochain:phi1", "cochain:gamma2"),
        step_budget=16,
        authority_effect="None",
        parent_event_id=research_parent_event_id,
        source_digest=source_digest,
        allowed_transforms=("same_carrier_retraction",),
    )

    adapter = IdentityAdapter(
        source_carrier_id=CODA_CARRIER_ID,
        target_carrier_id=CODA_CARRIER_ID,
    )

    detector_cases = (
        DetectorCase(
            case_id="exact-cochain-zero",
            native_state=exact,
            expected_active_ids=(),
            expected_projection_digest=exact_projection.control_digest,
        ),
        DetectorCase(
            case_id="obstructed-initial-cochain",
            native_state=initial,
            expected_active_ids=initial_projection.active_ids,
            expected_projection_digest=initial_projection.control_digest,
        ),
    )

    return RuntimeProblem(
        envelope=envelope,
        native_initial_state=initial,
        projector=projector,
        adapter=adapter,
        detector_cases=detector_cases,
        primitive_difference="l1 cochain deviation from closed subspace",
        zero_relation="phi1=0 and gamma2=0",
        observer_id=projector.projector_id,
        witness_certificate=f"parent:{research_parent_event_id}",
        protected_obstruction_ids=("cochain:phi1", "cochain:gamma2"),
    )


__all__ = ["build_coda_problem", "CochainCarrier", "CochainState", "CochainProjector"]
