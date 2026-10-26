"""The nonlinear Woland engineering scene graph and exact seat composition."""

from __future__ import annotations

from dataclasses import dataclass

from omega_engine_woland.stage.domain import (
    LicensedWorkflowPlanV1,
    MetaSkillPolicyV1,
    NodeAssignmentV1,
    SceneGraphV1,
    SceneSpecV1,
    SceneTransitionV1,
    SeatRequirementV1,
    SwarmDefinitionV1,
    SwarmProfileV1,
)

from .models import WolandSeatBindingV1


@dataclass(frozen=True, slots=True)
class _Seat:
    trust_domain: str
    operation_id: str
    colours: tuple[str, ...]
    independent_from: tuple[str, ...] = ()


_SEATS: dict[str, _Seat] = {
    "anti-skill-gate": _Seat(
        "EVALUATOR",
        "adversarial-receipt-audit",
        ("Audit", "Receipt", "State"),
        ("begemot", "massolit-proposer", "techne-developer", "woland-selector"),
    ),
    "ball-evaluator": _Seat(
        "EVALUATOR",
        "adversarial-receipt-audit",
        ("Audit", "Receipt", "State"),
        ("begemot", "koroviev", "red-panel", "green-panel", "blue-panel"),
    ),
    "begemot": _Seat(
        "PRODUCER",
        "goo-bulgakov-dramatic-cochain-synthesizer",
        ("Audit", "Receipt", "State"),
        ("koroviev", "red-panel", "blue-panel", "soviet-inspector"),
    ),
    "blue-panel": _Seat(
        "TESTER",
        "techne-code-clean-arch",
        ("Code", "State"),
        ("begemot", "koroviev", "red-panel", "green-panel"),
    ),
    "clinic-diagnostician": _Seat(
        "CRITIC",
        "techne-code-antipattern-scanner",
        ("Code",),
        ("techne-developer", "soviet-builder"),
    ),
    "green-panel": _Seat(
        "PRODUCER",
        "meta-code-audit--code--contractive",
        ("Audit", "Code"),
        ("begemot", "koroviev", "red-panel", "blue-panel"),
    ),
    "koroviev": _Seat(
        "CRITIC",
        "omega-old-man-chatgpt-red-team",
        ("Audit", "Receipt"),
        ("begemot", "red-panel", "green-panel", "blue-panel"),
    ),
    "massolit-proposer": _Seat(
        "PRODUCER",
        "meta-code-audit--code--contractive",
        ("Audit", "Code"),
        ("anti-skill-gate", "soviet-inspector"),
    ),
    "red-panel": _Seat(
        "CRITIC",
        "omega-old-man-chatgpt-red-team",
        ("Audit", "Receipt"),
        ("begemot", "koroviev", "green-panel", "blue-panel"),
    ),
    "sealer-miner": _Seat(
        "PRODUCER",
        "goo-bulgakov-dramatic-cochain-synthesizer",
        ("Audit", "Receipt", "State"),
        ("anti-skill-gate", "woland-selector"),
    ),
    "soviet-builder": _Seat(
        "PRODUCER",
        "techne-code-soviet-builder",
        ("Code",),
        ("clinic-diagnostician", "soviet-inspector"),
    ),
    "soviet-inspector": _Seat(
        "TESTER",
        "techne-code-soviet-inspector",
        ("Audit", "Code"),
        (
            "begemot",
            "massolit-proposer",
            "soviet-builder",
            "techne-developer",
        ),
    ),
    "task-freezer": _Seat(
        "EVALUATOR",
        "adversarial-receipt-audit",
        ("Audit", "Receipt", "State"),
    ),
    "techne-developer": _Seat(
        "PRODUCER",
        "techne-code-python-principal-developer",
        ("Code",),
        ("clinic-diagnostician", "soviet-inspector"),
    ),
    "woland-selector": _Seat(
        "SELECTOR",
        "meta-residual-harmonic-optimizer",
        ("Audit", "Ledger", "Receipt"),
        (
            "anti-skill-gate",
            "ball-evaluator",
            "begemot",
            "blue-panel",
            "green-panel",
            "koroviev",
            "red-panel",
            "sealer-miner",
        ),
    ),
}


_SCENE_SEATS: dict[str, tuple[str, ...]] = {
    "massolit": ("massolit-proposer",),
    "patriarchs-ponds": ("task-freezer",),
    "satans-ball": ("ball-evaluator", "soviet-inspector"),
    "seal-and-mine": ("anti-skill-gate", "sealer-miner"),
    "stravinsky-clinic": ("clinic-diagnostician",),
    "techne-workshop": (
        "soviet-builder",
        "soviet-inspector",
        "techne-developer",
    ),
    "variety-theatre": (
        "anti-skill-gate",
        "begemot",
        "blue-panel",
        "green-panel",
        "koroviev",
        "red-panel",
        "soviet-inspector",
    ),
    "woland-gate": ("anti-skill-gate", "woland-selector"),
}


@dataclass(frozen=True, slots=True)
class WolandProfileAssemblyV1:
    definition: SwarmDefinitionV1
    graph: SceneGraphV1
    profile: SwarmProfileV1
    plan: LicensedWorkflowPlanV1
    meta_policy: MetaSkillPolicyV1
    seat_bindings: tuple[WolandSeatBindingV1, ...]


def woland_scene_graph_v1() -> SceneGraphV1:
    scenes = (
        SceneSpecV1(
            "massolit",
            "Divergent proposals with explicit scope, imports, evidence prices, and predictions.",
            _SCENE_SEATS["massolit"],
            ("FINDING", "HOLD", "PASS", "PROPOSED"),
            3,
        ),
        SceneSpecV1(
            "patriarchs-ponds",
            "Freeze the task, evidence, budget, and evaluator epoch.",
            _SCENE_SEATS["patriarchs-ponds"],
            ("HOLD", "PASS", "PROPOSED", "REFUSE"),
            1,
        ),
        SceneSpecV1(
            "satans-ball",
            "Compare surviving candidates under identical frozen probes and budgets.",
            _SCENE_SEATS["satans-ball"],
            ("FINDING", "HOLD", "PASS", "PROPOSED", "REFUSE"),
            3,
        ),
        SceneSpecV1(
            "seal-and-mine",
            "Render UNS and canonical JSONL packets; emit inert mined proposals.",
            _SCENE_SEATS["seal-and-mine"],
            ("HOLD", "PASS", "REFUSE"),
            1,
            terminal=True,
        ),
        SceneSpecV1(
            "stravinsky-clinic",
            "Quarantine hallucination, circular repair, missing evidence, and unstable epochs.",
            _SCENE_SEATS["stravinsky-clinic"],
            ("HOLD", "PROPOSED", "REFUSE"),
            3,
        ),
        SceneSpecV1(
            "techne-workshop",
            "Develop and test with an independent Soviet Builder and Inspector.",
            _SCENE_SEATS["techne-workshop"],
            ("FINDING", "HOLD", "PASS", "PROPOSED", "REFUSE"),
            3,
        ),
        SceneSpecV1(
            "variety-theatre",
            "Begemot and Koroviev duel while independent red, green, blue, and inspector seats adjudicate.",
            _SCENE_SEATS["variety-theatre"],
            ("FINDING", "HOLD", "PASS", "PROPOSED", "REFUSE"),
            4,
        ),
        SceneSpecV1(
            "woland-gate",
            "Select one candidate from explicit admissible receipts or return HOLD.",
            _SCENE_SEATS["woland-gate"],
            ("FINDING", "HOLD", "PASS", "PROPOSED", "REFUSE"),
            2,
        ),
    )
    transitions = (
        SceneTransitionV1(
            "ponds-to-massolit",
            "patriarchs-ponds",
            "massolit",
            ("PASS", "PROPOSED"),
            (),
            10,
        ),
        SceneTransitionV1(
            "massolit-to-workshop",
            "massolit",
            "techne-workshop",
            ("PASS", "PROPOSED"),
            (),
            20,
        ),
        SceneTransitionV1(
            "workshop-to-variety",
            "techne-workshop",
            "variety-theatre",
            ("PASS", "PROPOSED"),
            (),
            30,
        ),
        SceneTransitionV1(
            "variety-to-clinic",
            "variety-theatre",
            "stravinsky-clinic",
            ("FINDING", "HOLD"),
            ("QUARANTINE",),
            40,
        ),
        SceneTransitionV1(
            "variety-to-ball",
            "variety-theatre",
            "satans-ball",
            ("PASS", "PROPOSED"),
            (),
            41,
        ),
        SceneTransitionV1(
            "clinic-to-massolit",
            "stravinsky-clinic",
            "massolit",
            ("PROPOSED",),
            ("REFRAME",),
            50,
        ),
        SceneTransitionV1(
            "clinic-to-workshop",
            "stravinsky-clinic",
            "techne-workshop",
            ("PROPOSED",),
            ("REPAIR",),
            51,
        ),
        SceneTransitionV1(
            "ball-to-variety",
            "satans-ball",
            "variety-theatre",
            ("FINDING",),
            ("REBUTTAL",),
            60,
        ),
        SceneTransitionV1(
            "ball-to-workshop",
            "satans-ball",
            "techne-workshop",
            ("PROPOSED",),
            ("REPAIR",),
            61,
        ),
        SceneTransitionV1(
            "ball-to-gate",
            "satans-ball",
            "woland-gate",
            ("PASS",),
            (),
            62,
        ),
        SceneTransitionV1(
            "gate-to-clinic",
            "woland-gate",
            "stravinsky-clinic",
            ("FINDING", "HOLD"),
            ("QUARANTINE",),
            70,
        ),
        SceneTransitionV1(
            "gate-to-seal",
            "woland-gate",
            "seal-and-mine",
            ("PASS", "PROPOSED"),
            (),
            71,
        ),
    )
    return SceneGraphV1(
        entry_scene_id="patriarchs-ponds",
        scenes=scenes,
        transitions=transitions,
    )


def _requirements() -> tuple[SeatRequirementV1, ...]:
    return tuple(
        SeatRequirementV1(
            seat_id=seat_id,
            trust_domain=seat.trust_domain,
            required_operations=(seat.operation_id,),
            required_colours=seat.colours,
            independent_from=seat.independent_from,
        )
        for seat_id, seat in sorted(_SEATS.items())
    )


def build_woland_engineering_profile_v1(
    *,
    catalog_id: str,
    seat_bindings: tuple[WolandSeatBindingV1, ...],
    anti_skill_profile_digest: str = "",
) -> WolandProfileAssemblyV1:
    """Compose Woland from exact capabilities without minting agent licences."""

    if type(seat_bindings) is not tuple or any(
        type(binding) is not WolandSeatBindingV1 for binding in seat_bindings
    ):
        raise TypeError("seat_bindings must be an exact typed tuple")
    bindings = {binding.seat_id: binding for binding in seat_bindings}
    if len(bindings) != len(seat_bindings):
        raise ValueError("Woland seat bindings must be unique")
    if set(bindings) != set(_SEATS):
        missing = sorted(set(_SEATS) - set(bindings))
        unknown = sorted(set(bindings) - set(_SEATS))
        raise ValueError(
            f"Woland seat binding mismatch: missing={missing}, unknown={unknown}"
        )
    for seat_id, required in _SEATS.items():
        binding = bindings[seat_id]
        if required.operation_id not in binding.licensed_operation_ids:
            raise ValueError(f"seat {seat_id} lacks operation {required.operation_id}")
        if not set(required.colours).issubset(binding.licensed_colours):
            raise ValueError(f"seat {seat_id} lacks its complete colour boundary")
        for independent_id in required.independent_from:
            if binding.agent_id == bindings[independent_id].agent_id:
                raise ValueError(
                    f"independent Woland seats {seat_id}/{independent_id} share an agent"
                )

    graph = woland_scene_graph_v1()
    definition = SwarmDefinitionV1(
        definition_name="omega-engineering-swarm-v1",
        seat_requirements=_requirements(),
        skill_catalog_id=catalog_id,
        max_parallelism=1,
    )
    profile = SwarmProfileV1(
        profile_name="woland-engineering-v1",
        base_definition_id=definition.definition_id,
        scene_graph_id=graph.graph_id,
        skill_ids=tuple(sorted({seat.operation_id for seat in _SEATS.values()})),
        anti_skill_profile_digest=anti_skill_profile_digest,
    )
    assignments = tuple(
        NodeAssignmentV1(
            scene_id=scene_id,
            seat_id=seat_id,
            agent_id=bindings[seat_id].agent_id,
            operation_ids=bindings[seat_id].licensed_operation_ids,
            agent_license_id=bindings[seat_id].agent_license_id,
        )
        for scene_id, seats in sorted(_SCENE_SEATS.items())
        for seat_id in seats
    )
    plan = LicensedWorkflowPlanV1(
        plan_name="woland-engineering-scene-plan-v1",
        catalog_id=catalog_id,
        assignments=assignments,
        normalized_operation_ids=profile.skill_ids,
        path2_evidence_ids=(),
    )
    meta_policy = MetaSkillPolicyV1(
        policy_name="woland-meta-selection-v1",
        meta_skill_ids=(
            "meta-code-audit--code--contractive",
            "meta-residual-harmonic-optimizer",
        ),
        selectable_operation_ids=profile.skill_ids,
    )
    return WolandProfileAssemblyV1(
        definition,
        graph,
        profile,
        plan,
        meta_policy,
        tuple(sorted(seat_bindings, key=lambda item: item.seat_id)),
    )


def woland_seat_requirements_v1() -> tuple[SeatRequirementV1, ...]:
    """Expose the exact required boundary for callers preparing seat bindings."""

    return _requirements()


__all__ = [
    "WolandProfileAssemblyV1",
    "build_woland_engineering_profile_v1",
    "woland_scene_graph_v1",
    "woland_seat_requirements_v1",
]
