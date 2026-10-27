"""The nonlinear Adversary engineering scene graph and exact seat composition."""

from __future__ import annotations

from dataclasses import dataclass

from adversary.stage.domain import (
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

from .models import AdversarySeatBindingV1


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
        ("gauge_breaker", "massolit-proposer", "techne-developer", "adversary-selector"),
    ),
    "ball-evaluator": _Seat(
        "EVALUATOR",
        "adversarial-receipt-audit",
        ("Audit", "Receipt", "State"),
        ("gauge_breaker", "defect_hunter", "red-panel", "green-panel", "blue-panel"),
    ),
    "gauge_breaker": _Seat(
        "PRODUCER",
        "goo-novelist-dramatic-cochain-synthesizer",
        ("Audit", "Receipt", "State"),
        ("defect_hunter", "red-panel", "blue-panel", "inspector"),
    ),
    "blue-panel": _Seat(
        "TESTER",
        "techne-code-clean-arch",
        ("Code", "State"),
        ("gauge_breaker", "defect_hunter", "red-panel", "green-panel"),
    ),
    "clinic-diagnostician": _Seat(
        "CRITIC",
        "techne-code-antipattern-scanner",
        ("Code",),
        ("techne-developer", "builder"),
    ),
    "green-panel": _Seat(
        "PRODUCER",
        "meta-code-audit--code--contractive",
        ("Audit", "Code"),
        ("gauge_breaker", "defect_hunter", "red-panel", "blue-panel"),
    ),
    "defect_hunter": _Seat(
        "CRITIC",
        "core-chatgpt-red-team",
        ("Audit", "Receipt"),
        ("gauge_breaker", "red-panel", "green-panel", "blue-panel"),
    ),
    "massolit-proposer": _Seat(
        "PRODUCER",
        "meta-code-audit--code--contractive",
        ("Audit", "Code"),
        ("anti-skill-gate", "inspector"),
    ),
    "red-panel": _Seat(
        "CRITIC",
        "core-chatgpt-red-team",
        ("Audit", "Receipt"),
        ("gauge_breaker", "defect_hunter", "green-panel", "blue-panel"),
    ),
    "sealer-miner": _Seat(
        "PRODUCER",
        "goo-novelist-dramatic-cochain-synthesizer",
        ("Audit", "Receipt", "State"),
        ("anti-skill-gate", "adversary-selector"),
    ),
    "builder": _Seat(
        "PRODUCER",
        "techne-code-builder",
        ("Code",),
        ("clinic-diagnostician", "inspector"),
    ),
    "inspector": _Seat(
        "TESTER",
        "techne-code-inspector",
        ("Audit", "Code"),
        (
            "gauge_breaker",
            "massolit-proposer",
            "builder",
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
        ("clinic-diagnostician", "inspector"),
    ),
    "adversary-selector": _Seat(
        "SELECTOR",
        "meta-residual-harmonic-optimizer",
        ("Audit", "Ledger", "Receipt"),
        (
            "anti-skill-gate",
            "ball-evaluator",
            "gauge_breaker",
            "blue-panel",
            "green-panel",
            "defect_hunter",
            "red-panel",
            "sealer-miner",
        ),
    ),
}


_SCENE_SEATS: dict[str, tuple[str, ...]] = {
    "massolit": ("massolit-proposer",),
    "patriarchs-ponds": ("task-freezer",),
    "satans-ball": ("ball-evaluator", "inspector"),
    "seal-and-mine": ("anti-skill-gate", "sealer-miner"),
    "quarantine-clinic": ("clinic-diagnostician",),
    "techne-workshop": (
        "builder",
        "inspector",
        "techne-developer",
    ),
    "variety-theatre": (
        "anti-skill-gate",
        "gauge_breaker",
        "blue-panel",
        "green-panel",
        "defect_hunter",
        "red-panel",
        "inspector",
    ),
    "adversary-gate": ("anti-skill-gate", "adversary-selector"),
}


@dataclass(frozen=True, slots=True)
class AdversaryProfileAssemblyV1:
    definition: SwarmDefinitionV1
    graph: SceneGraphV1
    profile: SwarmProfileV1
    plan: LicensedWorkflowPlanV1
    meta_policy: MetaSkillPolicyV1
    seat_bindings: tuple[AdversarySeatBindingV1, ...]


def adversary_scene_graph_v1() -> SceneGraphV1:
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
            "quarantine-clinic",
            "Quarantine hallucination, circular repair, missing evidence, and unstable epochs.",
            _SCENE_SEATS["quarantine-clinic"],
            ("HOLD", "PROPOSED", "REFUSE"),
            3,
        ),
        SceneSpecV1(
            "techne-workshop",
            "Develop and test with an independent Builder and Inspector.",
            _SCENE_SEATS["techne-workshop"],
            ("FINDING", "HOLD", "PASS", "PROPOSED", "REFUSE"),
            3,
        ),
        SceneSpecV1(
            "variety-theatre",
            "Gauge Breaker and Defect Hunter duel while independent red, green, blue, and inspector seats adjudicate.",
            _SCENE_SEATS["variety-theatre"],
            ("FINDING", "HOLD", "PASS", "PROPOSED", "REFUSE"),
            4,
        ),
        SceneSpecV1(
            "adversary-gate",
            "Select one candidate from explicit admissible receipts or return HOLD.",
            _SCENE_SEATS["adversary-gate"],
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
            "quarantine-clinic",
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
            "quarantine-clinic",
            "massolit",
            ("PROPOSED",),
            ("REFRAME",),
            50,
        ),
        SceneTransitionV1(
            "clinic-to-workshop",
            "quarantine-clinic",
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
            "adversary-gate",
            ("PASS",),
            (),
            62,
        ),
        SceneTransitionV1(
            "gate-to-clinic",
            "adversary-gate",
            "quarantine-clinic",
            ("FINDING", "HOLD"),
            ("QUARANTINE",),
            70,
        ),
        SceneTransitionV1(
            "gate-to-seal",
            "adversary-gate",
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


def build_adversary_engineering_profile_v1(
    *,
    catalog_id: str,
    seat_bindings: tuple[AdversarySeatBindingV1, ...],
    anti_skill_profile_digest: str = "",
) -> AdversaryProfileAssemblyV1:
    """Compose Adversary from exact capabilities without minting agent licences."""

    if type(seat_bindings) is not tuple or any(
        type(binding) is not AdversarySeatBindingV1 for binding in seat_bindings
    ):
        raise TypeError("seat_bindings must be an exact typed tuple")
    bindings = {binding.seat_id: binding for binding in seat_bindings}
    if len(bindings) != len(seat_bindings):
        raise ValueError("Adversary seat bindings must be unique")
    if set(bindings) != set(_SEATS):
        missing = sorted(set(_SEATS) - set(bindings))
        unknown = sorted(set(bindings) - set(_SEATS))
        raise ValueError(
            f"Adversary seat binding mismatch: missing={missing}, unknown={unknown}"
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
                    f"independent Adversary seats {seat_id}/{independent_id} share an agent"
                )

    graph = adversary_scene_graph_v1()
    definition = SwarmDefinitionV1(
        definition_name="engineering-swarm-v1",
        seat_requirements=_requirements(),
        skill_catalog_id=catalog_id,
        max_parallelism=1,
    )
    profile = SwarmProfileV1(
        profile_name="adversary-engineering-v1",
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
        plan_name="adversary-engineering-scene-plan-v1",
        catalog_id=catalog_id,
        assignments=assignments,
        normalized_operation_ids=profile.skill_ids,
        path2_evidence_ids=(),
    )
    meta_policy = MetaSkillPolicyV1(
        policy_name="adversary-meta-selection-v1",
        meta_skill_ids=(
            "meta-code-audit--code--contractive",
            "meta-residual-harmonic-optimizer",
        ),
        selectable_operation_ids=profile.skill_ids,
    )
    return AdversaryProfileAssemblyV1(
        definition,
        graph,
        profile,
        plan,
        meta_policy,
        tuple(sorted(seat_bindings, key=lambda item: item.seat_id)),
    )


def adversary_seat_requirements_v1() -> tuple[SeatRequirementV1, ...]:
    """Expose the exact required boundary for callers preparing seat bindings."""

    return _requirements()


__all__ = [
    "AdversaryProfileAssemblyV1",
    "build_adversary_engineering_profile_v1",
    "adversary_scene_graph_v1",
    "adversary_seat_requirements_v1",
]
