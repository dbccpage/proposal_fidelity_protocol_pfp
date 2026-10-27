"""SwarmSpecializationV1: the typed contract every swarm declares to specialise Adversary.

A specialisation names its ancestry (Adversary first), the skills it requires (``/adversary``
always), the estate ports it is licensed to use, the seven-act stage plan that uses
them, the routing terminals it may end on, and its budget. ``specialize`` derives a
child from a parent and refuses any widening: a child may narrow ports, terminals and
budget, never add to them. The routing terminal set mirrors the closed Rust enum
``core_types::routing::RoutingTerminal``.

AuthorityEffect: None.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from adversary.stage.domain.topology import SwarmCompositionV1

ADVERSARY_ANCESTOR = "core.adversary.swarm.v1"
BASE_ID = "adversary.base"
ADVERSARY_SKILL = "/adversary"
ADVERSARY_RUNTIME = "core.adversary.runtime.v1"
OEOS_HOST = "core.oeos.host.v1"
SYMBOL_GAME_PROTOCOL = "core.symbol_game.protocol.v2"
ACTS = ("I", "II", "III", "IV", "V", "VI", "VII")

#: Mirrors ``core_types::routing::RoutingTerminal`` (closed set of seven).
ROUTING_TERMINALS = frozenset(
    {"CheckPassed", "RequiresLift", "Repair", "Refusal", "NoRule", "BudgetUnknown", "Refused"}
)

_IDENTIFIER = re.compile(r"[a-z][a-z0-9_.-]*\Z")
_SKILL = re.compile(r"/[a-z0-9]+(-[a-z0-9]+)*\Z")


class SwarmTypeV1(str, Enum):
    """The canonical domain specializations of the Adversary base swarm."""

    OPEN_TOPIC = "open-topic"
    RESEARCH_PAPER = "research-paper"
    SOFTWARE_DEV = "software-dev"
    PRODUCT_MGMT = "product-mgmt"
    GOVERNING_COUNCILS = "governing-councils"
    THANATOS = "thanatos"

    @classmethod
    def from_str(cls, value: str | SwarmTypeV1) -> SwarmTypeV1:
        if isinstance(value, cls):
            return value
        normalized = str(value).strip().lower().replace("_", "-")
        for member in cls:
            if member.value == normalized:
                return member
        valid = ", ".join(f"'{m.value}'" for m in cls)
        raise ValueError(f"Unknown swarm_type '{value}'. Valid types are: {valid}")


class PortName(str, Enum):
    """The closed set of estate ports a swarm may be licensed to use."""

    ADVERSARY_RUNTIME = "adversary_runtime"
    NATIVE_BOUT = "native_bout"
    SEAT_TRANSPORT = "seat_transport"
    SGT_EMISSION = "sgt_emission"
    IMMUNE_ANTIBODIES = "immune_antibodies"
    OEWAS_LEARNING = "oewas_learning"
    OEWAS_ANTI_SKILL = "oewas_anti_skill"
    PROMPT_GENEALOGY = "prompt_genealogy"
    CODA_EVALUATION = "coda_evaluation"
    LGGR_GLUING = "lggr_gluing"
    ENVELOPE_STORE = "envelope_store"


class SpecializationError(ValueError):
    """A specialisation violates the Adversary contract; the code names the violated clause."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


def _require(condition: bool, code: str, message: str) -> None:
    if not condition:
        raise SpecializationError(code, message)


def _exact_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


@dataclass(frozen=True, slots=True)
class BudgetDefaultsV1:
    """Per-bout ceilings. ``max_cost_microusd == 0`` disables paid dispatch."""

    max_rounds: int
    compute_budget: int
    max_cost_microusd: int

    def __post_init__(self) -> None:
        _require(
            _exact_int(self.max_rounds) and 1 <= self.max_rounds <= 10,
            "BUDGET_INVALID",
            "max_rounds must be an exact integer from 1 through 10",
        )
        _require(
            _exact_int(self.compute_budget) and self.compute_budget >= 1,
            "BUDGET_INVALID",
            "compute_budget must be an exact positive integer",
        )
        _require(
            _exact_int(self.max_cost_microusd) and self.max_cost_microusd >= 0,
            "BUDGET_INVALID",
            "max_cost_microusd must be an exact non-negative integer",
        )

    def within(self, ceiling: BudgetDefaultsV1) -> bool:
        return (
            self.max_rounds <= ceiling.max_rounds
            and self.compute_budget <= ceiling.compute_budget
            and self.max_cost_microusd <= ceiling.max_cost_microusd
        )


@dataclass(frozen=True, slots=True)
class StageBindingV1:
    """One stage of the plan: which act it runs in and which ports it uses."""

    stage_id: str
    act: str
    ports: tuple[PortName, ...]

    def __post_init__(self) -> None:
        _require(
            isinstance(self.stage_id, str) and _IDENTIFIER.fullmatch(self.stage_id) is not None,
            "STAGE_INVALID",
            "stage_id must be a lowercase identifier",
        )
        _require(self.act in ACTS, "STAGE_INVALID", f"act must be one of {ACTS}")
        _require(
            isinstance(self.ports, tuple)
            and len(self.ports) > 0
            and all(type(port) is PortName for port in self.ports)
            and len(set(self.ports)) == len(self.ports),
            "STAGE_INVALID",
            "ports must be a non-empty tuple of distinct PortName values",
        )


@dataclass(frozen=True, slots=True)
class SwarmSpecializationV1:
    specialization_id: str
    ancestry: tuple[str, ...]
    required_skills: tuple[str, ...]
    licensed_ports: frozenset[PortName]
    stage_plan: tuple[StageBindingV1, ...]
    routing_terminals: frozenset[str]
    budget: BudgetDefaultsV1
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _require(self.authority_effect == "None", "AUTHORITY_EFFECT_FORBIDDEN", "must be 'None'")
        _require(
            isinstance(self.specialization_id, str)
            and _IDENTIFIER.fullmatch(self.specialization_id) is not None,
            "SPECIALIZATION_ID_INVALID",
            "specialization_id must be a lowercase identifier",
        )
        _require(
            isinstance(self.ancestry, tuple)
            and len(self.ancestry) >= 1
            and self.ancestry[0] == ADVERSARY_ANCESTOR
            and all(isinstance(item, str) for item in self.ancestry)
            and len(set(self.ancestry)) == len(self.ancestry),
            "ADVERSARY_INHERITANCE_REQUIRED",
            f"ancestry must start with {ADVERSARY_ANCESTOR} and contain no repeats",
        )
        is_base = self.ancestry == (ADVERSARY_ANCESTOR,) and self.specialization_id == BASE_ID
        _require(
            is_base or (len(self.ancestry) >= 2 and self.ancestry[-1] == self.specialization_id),
            "ADVERSARY_INHERITANCE_REQUIRED",
            "ancestry must end with this specialization_id",
        )
        _require(
            isinstance(self.required_skills, tuple)
            and ADVERSARY_SKILL in self.required_skills
            and all(isinstance(s, str) and _SKILL.fullmatch(s) for s in self.required_skills)
            and len(set(self.required_skills)) == len(self.required_skills),
            "ADVERSARY_SKILL_REQUIRED",
            "required_skills must be distinct /skill-names and include /adversary",
        )
        _require(
            isinstance(self.licensed_ports, frozenset)
            and len(self.licensed_ports) > 0
            and all(type(port) is PortName for port in self.licensed_ports),
            "PORTS_INVALID",
            "licensed_ports must be a non-empty frozenset of PortName",
        )
        _require(
            isinstance(self.stage_plan, tuple)
            and len(self.stage_plan) > 0
            and all(type(stage) is StageBindingV1 for stage in self.stage_plan),
            "STAGE_PLAN_INVALID",
            "stage_plan must be a non-empty tuple of StageBindingV1",
        )
        stage_ids = [stage.stage_id for stage in self.stage_plan]
        _require(len(set(stage_ids)) == len(stage_ids), "STAGE_PLAN_INVALID", "duplicate stage_id")
        acts = [ACTS.index(stage.act) for stage in self.stage_plan]
        _require(acts == sorted(acts), "STAGE_PLAN_INVALID", "stages must follow act order I..VII")
        used = {port for stage in self.stage_plan for port in stage.ports}
        _require(
            used <= self.licensed_ports,
            "PORT_NOT_LICENSED",
            f"stage plan uses unlicensed ports {sorted(p.value for p in used - self.licensed_ports)}",
        )
        _require(
            isinstance(self.routing_terminals, frozenset)
            and len(self.routing_terminals) > 0
            and self.routing_terminals <= ROUTING_TERMINALS,
            "ROUTING_TERMINALS_INVALID",
            "routing_terminals must be a non-empty subset of the core_types routing axis",
        )
        _require(type(self.budget) is BudgetDefaultsV1, "BUDGET_INVALID", "budget type")

    def to_wire(self) -> dict[str, Any]:
        """The JSON form the native ``specialization_validate`` host operation reads."""
        return {
            "specialization_id": self.specialization_id,
            "ancestry": list(self.ancestry),
            "required_skills": list(self.required_skills),
            "licensed_ports": sorted(port.value for port in self.licensed_ports),
            "stage_plan": [
                {
                    "stage_id": stage.stage_id,
                    "act": stage.act,
                    "ports": [p.value for p in stage.ports],
                }
                for stage in self.stage_plan
            ],
            "routing_terminals": sorted(self.routing_terminals),
            "budget": {
                "max_rounds": self.budget.max_rounds,
                "compute_budget": self.budget.compute_budget,
                "max_cost_microusd": self.budget.max_cost_microusd,
            },
            "authority_effect": self.authority_effect,
        }

    @property
    def composition(self) -> SwarmCompositionV1:
        """The stage composition this specialisation declares."""
        return SwarmCompositionV1(
            swarm_ancestry=self.ancestry,
            required_skills=self.required_skills,
            runtime=ADVERSARY_RUNTIME,
            operating_system=OEOS_HOST,
            llm_protocol=SYMBOL_GAME_PROTOCOL,
        )


def specialize(
    parent: SwarmSpecializationV1,
    *,
    specialization_id: str,
    extra_skills: tuple[str, ...] = (),
    licensed_ports: frozenset[PortName] | None = None,
    stage_plan: tuple[StageBindingV1, ...] | None = None,
    routing_terminals: frozenset[str] | None = None,
    budget: BudgetDefaultsV1 | None = None,
) -> SwarmSpecializationV1:
    """Derive a child specialisation. Ports, terminals and budget may only narrow."""
    ports = parent.licensed_ports if licensed_ports is None else licensed_ports
    terminals = parent.routing_terminals if routing_terminals is None else routing_terminals
    child_budget = parent.budget if budget is None else budget
    _require(ports <= parent.licensed_ports, "PORT_WIDENING", "a child cannot license new ports")
    _require(
        terminals <= parent.routing_terminals,
        "TERMINAL_WIDENING",
        "a child cannot add routing terminals",
    )
    _require(
        type(child_budget) is BudgetDefaultsV1 and child_budget.within(parent.budget),
        "BUDGET_WIDENING",
        "a child budget cannot exceed its parent's",
    )
    if stage_plan is None:
        # Narrowing strips unlicensed ports from each stage; a stage left with no
        # port is dropped. The acts that remain keep their order.
        narrowed = (
            StageBindingV1(stage.stage_id, stage.act, tuple(p for p in stage.ports if p in ports))
            for stage in parent.stage_plan
            if any(p in ports for p in stage.ports)
        )
        plan = tuple(narrowed)
    else:
        plan = stage_plan
    return SwarmSpecializationV1(
        specialization_id=specialization_id,
        ancestry=(*parent.ancestry, specialization_id),
        required_skills=tuple(dict.fromkeys((*parent.required_skills, *extra_skills))),
        licensed_ports=ports,
        stage_plan=plan,
        routing_terminals=terminals,
        budget=child_budget,
    )


#: The base: every port, every terminal, the base budget, the seven-act plan.
ADVERSARY_BASE_SPECIALIZATION_V1 = SwarmSpecializationV1(
    specialization_id=BASE_ID,
    ancestry=(ADVERSARY_ANCESTOR,),
    required_skills=(ADVERSARY_SKILL,),
    licensed_ports=frozenset(PortName),
    stage_plan=(
        StageBindingV1("intake", "I", (PortName.ADVERSARY_RUNTIME, PortName.IMMUNE_ANTIBODIES)),
        StageBindingV1("panel_debate", "II", (PortName.ADVERSARY_RUNTIME, PortName.SEAT_TRANSPORT)),
        StageBindingV1(
            "carrier_measurement", "III", (PortName.CODA_EVALUATION, PortName.SGT_EMISSION)
        ),
        StageBindingV1("gauge_break", "IV", (PortName.SEAT_TRANSPORT,)),
        StageBindingV1("gluing_audit", "V", (PortName.LGGR_GLUING,)),
        StageBindingV1("compost", "VI", (PortName.IMMUNE_ANTIBODIES, PortName.PROMPT_GENEALOGY)),
        StageBindingV1(
            "terminal_gate",
            "VII",
            (
                PortName.NATIVE_BOUT,
                PortName.SGT_EMISSION,
                PortName.OEWAS_ANTI_SKILL,
                PortName.OEWAS_LEARNING,
                PortName.ENVELOPE_STORE,
            ),
        ),
    ),
    routing_terminals=ROUTING_TERMINALS,
    # A ceiling, never a default paid authorization: live dispatch also requires
    # an explicit positive operator-signed request cap. Fixtures spend nothing.
    budget=BudgetDefaultsV1(max_rounds=4, compute_budget=100, max_cost_microusd=2_000_000),
)


__all__ = [
    "ACTS",
    "ROUTING_TERMINALS",
    "ADVERSARY_ANCESTOR",
    "ADVERSARY_BASE_SPECIALIZATION_V1",
    "ADVERSARY_SKILL",
    "BudgetDefaultsV1",
    "PortName",
    "SpecializationError",
    "StageBindingV1",
    "SwarmSpecializationV1",
    "SwarmTypeV1",
    "specialize",
]
