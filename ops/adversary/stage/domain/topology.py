"""Pure topology and composition records for the Adversary stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .canonical import (
    AUTHORITY_EFFECT_NONE,
    digest,
    exact_bool,
    exact_object,
    identifier,
    integer,
    semantic_id,
    string_tuple,
    text,
    wire_tuple,
)

TRUST_DOMAINS = frozenset({"PRODUCER", "CRITIC", "TESTER", "EVALUATOR", "SELECTOR"})
RESULT_STATUSES = frozenset({"PROPOSED", "FINDING", "PASS", "HOLD", "REFUSE"})


@dataclass(frozen=True, slots=True)
class SeatRequirementV1:
    seat_id: str
    trust_domain: str
    required_operations: tuple[str, ...]
    required_colours: tuple[str, ...]
    independent_from: tuple[str, ...] = ()
    cognitive_operator: str = ""

    def __post_init__(self) -> None:
        identifier(self.seat_id, "seat_id")
        if self.trust_domain not in TRUST_DOMAINS:
            raise ValueError("seat trust_domain is not closed")
        object.__setattr__(
            self,
            "required_operations",
            string_tuple(
                self.required_operations, "required_operations", identifiers=True
            ),
        )
        object.__setattr__(
            self,
            "required_colours",
            string_tuple(self.required_colours, "required_colours", identifiers=True),
        )
        object.__setattr__(
            self,
            "independent_from",
            string_tuple(self.independent_from, "independent_from", identifiers=True),
        )
        if self.cognitive_operator:
            text(self.cognitive_operator, "cognitive_operator")
        if not self.required_operations or not self.required_colours:
            raise ValueError("seat requires operations and colours")
        if self.seat_id in self.independent_from:
            raise ValueError("seat cannot be independent from itself")

    def to_dict(self) -> dict[str, Any]:
        result = {
            "seat_id": self.seat_id,
            "trust_domain": self.trust_domain,
            "required_operations": list(self.required_operations),
            "required_colours": list(self.required_colours),
            "independent_from": list(self.independent_from),
        }
        if self.cognitive_operator:
            result["cognitive_operator"] = self.cognitive_operator
        return result

    @classmethod
    def from_dict(cls, value: Any) -> "SeatRequirementV1":
        allowed_keys = {
            "seat_id",
            "trust_domain",
            "required_operations",
            "required_colours",
            "independent_from",
            "cognitive_operator",
        }
        wire = exact_object(
            value,
            frozenset(allowed_keys),
            "seat requirement",
            allow_missing=True,
        )
        return cls(
            seat_id=identifier(wire["seat_id"], "seat_id"),
            trust_domain=text(wire["trust_domain"], "trust_domain"),
            required_operations=wire_tuple(
                wire["required_operations"], "required_operations", identifiers=True
            ),
            required_colours=wire_tuple(
                wire["required_colours"], "required_colours", identifiers=True
            ),
            independent_from=wire_tuple(
                wire.get("independent_from", ()), "independent_from", identifiers=True
            ),
            cognitive_operator=text(wire.get("cognitive_operator", ""), "cognitive_operator") if wire.get("cognitive_operator") else "",
        )


@dataclass(frozen=True, slots=True)
class NodeAssignmentV1:
    scene_id: str
    seat_id: str
    agent_id: str
    operation_ids: tuple[str, ...]
    agent_license_id: str

    def __post_init__(self) -> None:
        identifier(self.scene_id, "scene_id")
        identifier(self.seat_id, "seat_id")
        identifier(self.agent_id, "agent_id")
        object.__setattr__(
            self,
            "operation_ids",
            string_tuple(self.operation_ids, "operation_ids", identifiers=True),
        )
        if not self.operation_ids:
            raise ValueError("node assignment requires operations")
        digest(self.agent_license_id, "agent_license_id")

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "seat_id": self.seat_id,
            "agent_id": self.agent_id,
            "operation_ids": list(self.operation_ids),
            "agent_license_id": self.agent_license_id,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "NodeAssignmentV1":
        wire = exact_object(
            value,
            frozenset(
                {"scene_id", "seat_id", "agent_id", "operation_ids", "agent_license_id"}
            ),
            "node assignment",
        )
        return cls(
            scene_id=identifier(wire["scene_id"], "scene_id"),
            seat_id=identifier(wire["seat_id"], "seat_id"),
            agent_id=identifier(wire["agent_id"], "agent_id"),
            operation_ids=wire_tuple(
                wire["operation_ids"], "operation_ids", identifiers=True
            ),
            agent_license_id=digest(wire["agent_license_id"], "agent_license_id"),
        )


@dataclass(frozen=True, slots=True)
class SceneSpecV1:
    scene_id: str
    purpose: str
    required_seat_ids: tuple[str, ...]
    allowed_result_statuses: tuple[str, ...]
    max_visits: int
    terminal: bool = False

    def __post_init__(self) -> None:
        identifier(self.scene_id, "scene_id")
        text(self.purpose, "purpose")
        object.__setattr__(
            self,
            "required_seat_ids",
            string_tuple(self.required_seat_ids, "required_seat_ids", identifiers=True),
        )
        object.__setattr__(
            self,
            "allowed_result_statuses",
            string_tuple(
                self.allowed_result_statuses,
                "allowed_result_statuses",
                identifiers=True,
            ),
        )
        if not self.required_seat_ids:
            raise ValueError("scene requires at least one seat")
        if not self.allowed_result_statuses or any(
            status not in RESULT_STATUSES for status in self.allowed_result_statuses
        ):
            raise ValueError("scene result status is not closed")
        integer(self.max_visits, "max_visits", minimum=1, maximum=64)
        exact_bool(self.terminal, "terminal")

    def to_dict(self) -> dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "purpose": self.purpose,
            "required_seat_ids": list(self.required_seat_ids),
            "allowed_result_statuses": list(self.allowed_result_statuses),
            "max_visits": self.max_visits,
            "terminal": self.terminal,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "SceneSpecV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "scene_id",
                    "purpose",
                    "required_seat_ids",
                    "allowed_result_statuses",
                    "max_visits",
                    "terminal",
                }
            ),
            "scene spec",
        )
        return cls(
            scene_id=identifier(wire["scene_id"], "scene_id"),
            purpose=text(wire["purpose"], "purpose"),
            required_seat_ids=wire_tuple(
                wire["required_seat_ids"], "required_seat_ids", identifiers=True
            ),
            allowed_result_statuses=wire_tuple(
                wire["allowed_result_statuses"],
                "allowed_result_statuses",
                identifiers=True,
            ),
            max_visits=integer(wire["max_visits"], "max_visits", minimum=1, maximum=64),
            terminal=exact_bool(wire["terminal"], "terminal"),
        )


@dataclass(frozen=True, slots=True)
class SceneTransitionV1:
    transition_id: str
    source_scene_id: str
    target_scene_id: str
    trigger_statuses: tuple[str, ...]
    residual_codes: tuple[str, ...]
    priority: int

    def __post_init__(self) -> None:
        identifier(self.transition_id, "transition_id")
        identifier(self.source_scene_id, "source_scene_id")
        identifier(self.target_scene_id, "target_scene_id")
        object.__setattr__(
            self,
            "trigger_statuses",
            string_tuple(self.trigger_statuses, "trigger_statuses", identifiers=True),
        )
        if not self.trigger_statuses or any(
            status not in RESULT_STATUSES for status in self.trigger_statuses
        ):
            raise ValueError("transition trigger status is not closed")
        object.__setattr__(
            self,
            "residual_codes",
            string_tuple(self.residual_codes, "residual_codes", identifiers=True),
        )
        integer(self.priority, "priority", minimum=0, maximum=10_000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transition_id": self.transition_id,
            "source_scene_id": self.source_scene_id,
            "target_scene_id": self.target_scene_id,
            "trigger_statuses": list(self.trigger_statuses),
            "residual_codes": list(self.residual_codes),
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "SceneTransitionV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "transition_id",
                    "source_scene_id",
                    "target_scene_id",
                    "trigger_statuses",
                    "residual_codes",
                    "priority",
                }
            ),
            "scene transition",
        )
        return cls(
            transition_id=identifier(wire["transition_id"], "transition_id"),
            source_scene_id=identifier(wire["source_scene_id"], "source_scene_id"),
            target_scene_id=identifier(wire["target_scene_id"], "target_scene_id"),
            trigger_statuses=wire_tuple(
                wire["trigger_statuses"], "trigger_statuses", identifiers=True
            ),
            residual_codes=wire_tuple(
                wire["residual_codes"], "residual_codes", identifiers=True
            ),
            priority=integer(wire["priority"], "priority", maximum=10_000),
        )


@dataclass(frozen=True, slots=True)
class SceneGraphV1:
    entry_scene_id: str
    scenes: tuple[SceneSpecV1, ...]
    transitions: tuple[SceneTransitionV1, ...]
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.scene-graph.v1"
    graph_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.entry_scene_id, "entry_scene_id")
        if type(self.scenes) is not tuple or not self.scenes:
            raise TypeError("scenes must be a nonempty exact tuple")
        if any(type(scene) is not SceneSpecV1 for scene in self.scenes):
            raise TypeError("scene graph contains a non-exact scene")
        if type(self.transitions) is not tuple or any(
            type(edge) is not SceneTransitionV1 for edge in self.transitions
        ):
            raise TypeError("transitions must be an exact typed tuple")
        if tuple(sorted(self.scenes, key=lambda item: item.scene_id)) != self.scenes:
            raise ValueError("scenes must be sorted by scene_id")
        if (
            tuple(
                sorted(
                    self.transitions,
                    key=lambda item: (item.priority, item.transition_id),
                )
            )
            != self.transitions
        ):
            raise ValueError("transitions must be sorted by priority and id")
        scene_ids = {scene.scene_id for scene in self.scenes}
        if len(scene_ids) != len(self.scenes) or self.entry_scene_id not in scene_ids:
            raise ValueError("scene graph has duplicate scenes or missing entry")
        if not any(scene.terminal for scene in self.scenes):
            raise ValueError("scene graph requires a terminal scene")
        transition_ids = {edge.transition_id for edge in self.transitions}
        if len(transition_ids) != len(self.transitions):
            raise ValueError("scene transition ids must be unique")
        if any(
            edge.source_scene_id not in scene_ids
            or edge.target_scene_id not in scene_ids
            for edge in self.transitions
        ):
            raise ValueError("scene transition references an unknown scene")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("scene graph authority_effect must be None")
        if self.schema_version != "core.oeas.scene-graph.v1":
            raise ValueError("unsupported scene graph schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.graph_id and self.graph_id != expected:
            raise ValueError("graph_id does not match canonical content")
        object.__setattr__(self, "graph_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "entry_scene_id": self.entry_scene_id,
            "scenes": [scene.to_dict() for scene in self.scenes],
            "transitions": [edge.to_dict() for edge in self.transitions],
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "graph_id": self.graph_id}

    @classmethod
    def from_dict(cls, value: Any) -> "SceneGraphV1":
        wire = exact_object(
            value,
            frozenset(
                {
                    "entry_scene_id",
                    "scenes",
                    "transitions",
                    "authority_effect",
                    "schema_version",
                    "graph_id",
                }
            ),
            "scene graph",
        )
        if type(wire["scenes"]) is not list or type(wire["transitions"]) is not list:
            raise ValueError("scene graph collections must be exact JSON arrays")
        return cls(
            entry_scene_id=identifier(wire["entry_scene_id"], "entry_scene_id"),
            scenes=tuple(SceneSpecV1.from_dict(item) for item in wire["scenes"]),
            transitions=tuple(
                SceneTransitionV1.from_dict(item) for item in wire["transitions"]
            ),
            authority_effect=text(wire["authority_effect"], "authority_effect"),
            schema_version=text(wire["schema_version"], "schema_version"),
            graph_id=digest(wire["graph_id"], "graph_id"),
        )


@dataclass(frozen=True, slots=True)
class SwarmDefinitionV1:
    definition_name: str
    seat_requirements: tuple[SeatRequirementV1, ...]
    skill_catalog_id: str
    max_parallelism: int = 1
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.swarm-definition.v1"
    definition_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.definition_name, "definition_name")
        if type(self.seat_requirements) is not tuple or not self.seat_requirements:
            raise TypeError("seat_requirements must be a nonempty exact tuple")
        if any(type(item) is not SeatRequirementV1 for item in self.seat_requirements):
            raise TypeError("swarm definition contains a non-exact seat")
        if (
            tuple(sorted(self.seat_requirements, key=lambda item: item.seat_id))
            != self.seat_requirements
        ):
            raise ValueError("seat requirements must be sorted")
        seat_ids = {seat.seat_id for seat in self.seat_requirements}
        if len(seat_ids) != len(self.seat_requirements):
            raise ValueError("seat requirements must be unique")
        if any(
            not set(seat.independent_from).issubset(seat_ids)
            for seat in self.seat_requirements
        ):
            raise ValueError("seat independence references an unknown seat")
        digest(self.skill_catalog_id, "skill_catalog_id")
        integer(self.max_parallelism, "max_parallelism", minimum=1, maximum=64)
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("swarm definition authority_effect must be None")
        if self.schema_version != "core.oeas.swarm-definition.v1":
            raise ValueError("unsupported swarm definition schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.definition_id and self.definition_id != expected:
            raise ValueError("definition_id does not match canonical content")
        object.__setattr__(self, "definition_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "definition_name": self.definition_name,
            "seat_requirements": [seat.to_dict() for seat in self.seat_requirements],
            "skill_catalog_id": self.skill_catalog_id,
            "max_parallelism": self.max_parallelism,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "definition_id": self.definition_id}


@dataclass(frozen=True, slots=True)
class SwarmProfileV1:
    profile_name: str
    base_definition_id: str
    scene_graph_id: str
    skill_ids: tuple[str, ...]
    anti_skill_profile_digest: str = ""
    authority_effect: str = AUTHORITY_EFFECT_NONE
    schema_version: str = "core.oeas.swarm-profile.v1"
    profile_id: str = ""

    def __post_init__(self) -> None:
        identifier(self.profile_name, "profile_name")
        digest(self.base_definition_id, "base_definition_id")
        digest(self.scene_graph_id, "scene_graph_id")
        object.__setattr__(
            self,
            "skill_ids",
            string_tuple(self.skill_ids, "skill_ids", identifiers=True),
        )
        if not self.skill_ids:
            raise ValueError("swarm profile requires skills")
        digest(
            self.anti_skill_profile_digest,
            "anti_skill_profile_digest",
            allow_empty=True,
        )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            raise ValueError("swarm profile authority_effect must be None")
        if self.schema_version != "core.oeas.swarm-profile.v1":
            raise ValueError("unsupported swarm profile schema")
        expected = semantic_id(self.schema_version, self._payload())
        if self.profile_id and self.profile_id != expected:
            raise ValueError("profile_id does not match canonical content")
        object.__setattr__(self, "profile_id", expected)

    def _payload(self) -> dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "base_definition_id": self.base_definition_id,
            "scene_graph_id": self.scene_graph_id,
            "skill_ids": list(self.skill_ids),
            "anti_skill_profile_digest": self.anti_skill_profile_digest,
            "authority_effect": self.authority_effect,
            "schema_version": self.schema_version,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "profile_id": self.profile_id}


@dataclass(frozen=True, slots=True)
class SwarmCompositionV1:
    swarm_ancestry: list[str] | tuple[str, ...]
    required_skills: list[str] | tuple[str, ...]
    runtime: str
    operating_system: str
    llm_protocol: str
    authority_effect: str = AUTHORITY_EFFECT_NONE


def validate_swarm_composition(composition: SwarmCompositionV1) -> bool:
    """Validate that swarm composition strictly adheres to the stage runtime and OEOS host invariants."""
    if not isinstance(composition, SwarmCompositionV1):
        raise TypeError("composition must be exact SwarmCompositionV1")
    if not composition.swarm_ancestry:
        raise ValueError("SWARM_ANCESTRY_REQUIRED: Swarm must declare ancestry")
    if not isinstance(composition.required_skills, (list, tuple)):
        raise TypeError("REQUIRED_SKILLS_INVALID: required_skills must be a sequence")
    if composition.runtime != "core.adversary.runtime.v1":
        raise ValueError("ADVERSARY_RUNTIME_REQUIRED: Runtime must be core.adversary.runtime.v1")
    if composition.operating_system != "core.oeos.host.v1":
        raise ValueError("OEOS_HOST_REQUIRED: Host operating system must be core.oeos.host.v1")
    if not composition.llm_protocol:
        raise ValueError("LLM_PROTOCOL_REQUIRED: LLM protocol must be specified")
    return True


__all__ = [
    "NodeAssignmentV1",
    "RESULT_STATUSES",
    "SceneGraphV1",
    "SceneSpecV1",
    "SceneTransitionV1",
    "SeatRequirementV1",
    "SwarmCompositionV1",
    "SwarmDefinitionV1",
    "SwarmProfileV1",
    "validate_swarm_composition",
]
