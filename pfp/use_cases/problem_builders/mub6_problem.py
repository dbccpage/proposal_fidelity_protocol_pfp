"""Factory methods for building MUB(6) Deltoid Cusp RuntimeProblem instances for the Symbol Game.

Encodes the MUB(6) deltoid cusp / 6-cycle boundary into Level 2 wire grammar.
The historical circulation reference is not a Phi_1 functional result.

AuthorityEffect: None.
Firewall Line: NOT MUB(6)=3, NOT MUB(6)<=3; stated region only; mints no authority
"""

from __future__ import annotations

from fractions import Fraction

from pfp.domain.entities import PacketEnvelopeV2
from pfp.domain.entities.cochain import CochainCarrier, CochainState
from pfp.domain.entities.cochain_projector import CochainProjector
from pfp.domain.entities.problem import (
    DetectorCase,
    IdentityAdapter,
    RuntimeProblem,
)
from pfp.domain.shared_kernel.canonical import domain_digest, freeze

MUB6_CARRIER_ID = "mub6-deltoid-cusp-6cycle-v1"
MUB6_PACKET_FAMILY = "mub6_cusp_obstruction"
MUB6_CONSTRAINTS = (
    "d1*d0=0",
    "exact rational arithmetic (zero float leakage)",
    "deltoid cusp net margin mu = 12133 / 30000",
    "cycle-circulation reference 12133 / 5000 requires Rust functional replay",
    "intercept AM-FSP-2 / AM-4 hallucinated zero-defect closures",
)

# Exact rational parameters from Target A2
EPSILON_CUSP: Fraction = Fraction(37249, 90000)
LIPSCHITZ_PROJ: Fraction = Fraction(85, 9)
DELTA: Fraction = Fraction(1, 1000)
MARGIN_CUSP: Fraction = Fraction(12133, 30000)  # 37249/90000 - (85/9)*(1/1000)
CYCLE_CIRCULATION_REFERENCE = "12133/5000"

# Level 2 binary vertex map: 0..5
VERTEX_BINARY_MAP: dict[int, str] = {
    0: "<0>",
    1: "<1>",
    2: "<10>",
    3: "<11>",
    4: "<100>",
    5: "<101>",
}


def encode_mub6_level2_wire() -> str:
    """Encodes the MUB(6) 6-cycle deltoid cusp boundary in Level 2 op<...> wire grammar.

    Structure:
      op<<11>
        op<<1><0>> ... op<<1><101>>              (6 vertices)
        op<<10><0><1>> ... op<<10><101><0>>      (6 directed edges)
        op<<100><>op<<10>...>...>                (obstruction witness attached to cycle)
      >
    """
    v_packets = "".join(f"op<<1>{VERTEX_BINARY_MAP[i]}>" for i in range(6))
    e_packets = "".join(
        f"op<<10>{VERTEX_BINARY_MAP[i]}{VERTEX_BINARY_MAP[(i+1)%6]}>"
        for i in range(6)
    )
    obs_carrier = "".join(
        f"op<<10>{VERTEX_BINARY_MAP[i]}{VERTEX_BINARY_MAP[(i+1)%6]}>"
        for i in range(6)
    )
    obs_packet = f"op<<100><>{obs_carrier}>"
    return f"op<<11>{v_packets}{e_packets}{obs_packet}>"


def build_mub6_deltoid_cusp_problem(
    *,
    task_id: str = "mub6-deltoid-cusp-demo",
    research_parent_event_id: str | None = None,
    carrier: CochainCarrier | None = None,
    initial: CochainState | None = None,
) -> RuntimeProblem:
    """Builds a RuntimeProblem representing the MUB(6) Deltoid Cusp 6-cycle obstruction."""
    if carrier is None:
        carrier = CochainCarrier(
            nodes=(0, 1, 2, 3, 4, 5),
            edges=((0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 0)),
            faces=(),
            weights=(1, 1, 1, 1, 1, 1),
        )
    elif type(carrier) is not CochainCarrier:
        raise TypeError("carrier must be a CochainCarrier")

    float_margin = float(MARGIN_CUSP)
    if initial is None:
        initial = CochainState.from_mapping(
            {
                (0, 1): float_margin,
                (1, 2): float_margin,
                (2, 3): float_margin,
                (3, 4): float_margin,
                (4, 5): float_margin,
                (5, 0): float_margin,
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

    wire_level2 = encode_mub6_level2_wire()

    payload = {
        "carrier": carrier,
        "omega": initial.values,
        "exact_margin_cusp": str(MARGIN_CUSP),
        "cycle_circulation_reference": CYCLE_CIRCULATION_REFERENCE,
        "functional_status": "RUST_FUNCTIONAL_REQUIRED",
        "level2_wire_grammar": wire_level2,
        "canonical_rust_owner": "core_mub::core_native::mub6_g1_variety",
        "authority_effect": "None",
        "firewall": "NOT MUB(6)=3, NOT MUB(6)<=3; stated region only; mints no authority",
    }
    if research_parent_event_id is not None:
        payload["research_parent_event_id"] = research_parent_event_id

    source_digest = domain_digest("core.mub6.deltoid-cusp-fixture.v1", payload)
    initial_state_hash = domain_digest("core.oesos.native-state.v1", initial)

    envelope = PacketEnvelopeV2(
        task_id=task_id,
        packet_family=MUB6_PACKET_FAMILY,
        carrier_id=MUB6_CARRIER_ID,
        initial_state_hash=initial_state_hash,
        payload=freeze(payload),
        constraints=MUB6_CONSTRAINTS,
        protected_boundaries=("cochain:phi1", "mub6:deltoid_cusp_boundary"),
        step_budget=16,
        authority_effect="None",
        parent_event_id=research_parent_event_id,
        source_digest=source_digest,
        allowed_transforms=("same_carrier_retraction", "open_sign_obstruction_declaration"),
    )

    adapter = IdentityAdapter(
        source_carrier_id=MUB6_CARRIER_ID,
        target_carrier_id=MUB6_CARRIER_ID,
    )

    detector_cases = (
        DetectorCase(
            case_id="exact-cochain-zero",
            native_state=exact,
            expected_active_ids=(),
            expected_projection_digest=exact_projection.control_digest,
        ),
        DetectorCase(
            case_id="obstructed-deltoid-cusp-cochain",
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
        primitive_difference="mub6 deltoid cusp 6-cycle holonomy obstruction",
        zero_relation="phi1=0 and gamma2=0",
        observer_id=projector.projector_id,
        witness_certificate=f"parent:{research_parent_event_id}",
        protected_obstruction_ids=("cochain:phi1", "mub6:deltoid_cusp_boundary"),
    )


__all__ = [
    "EPSILON_CUSP",
    "LIPSCHITZ_PROJ",
    "DELTA",
    "MARGIN_CUSP",
    "CYCLE_CIRCULATION_REFERENCE",
    "MUB6_CARRIER_ID",
    "MUB6_PACKET_FAMILY",
    "MUB6_CONSTRAINTS",
    "encode_mub6_level2_wire",
    "build_mub6_deltoid_cusp_problem",
]
