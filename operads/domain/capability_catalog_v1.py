"""Closed, deterministic capability-catalog contracts.

The catalog is a compiled projection of Git-tracked agent and skill
frontmatter. It records declarations and integrity evidence only; it does not
make an executor reachable, healthy, or authorized and has AuthorityEffect
``none``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from typing import Any, NoReturn

from .operad.colours import ADMITTED_FINITE_COLOURS

CATALOG_SCHEMA_V1 = "core.oewas.capability_catalog.v1"
CATALOG_DIGEST_DOMAIN_V1 = b"core.oewas.capability_catalog.v1\0"
AGENT_LICENSE_DIGEST_DOMAIN_V1 = b"core.oewas.agent_license.v1\0"
AUTHORITY_EFFECT_NONE = "none"
TRACKED_INVENTORY_V1 = "GIT_TRACKED_CANONICAL_ENTRYPOINTS"
TRACKED_ENTRYPOINT_V1 = "TRACKED_CANONICAL"
UNBOUND_EXECUTOR_V1 = "UNBOUND"
BOUND_EXECUTOR_V1 = "BOUND"
EXECUTOR_STATES_V1 = frozenset({UNBOUND_EXECUTOR_V1, BOUND_EXECUTOR_V1})
OPERAD_COLOURS_V1 = frozenset(ADMITTED_FINITE_COLOURS)

_ID_RE = re.compile(r"[a-z0-9][a-z0-9_-]{0,127}")
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class CapabilityCatalogRefusal(ValueError):
    """A catalog or catalog member violates the closed v1 contract."""

    def __init__(self, code: str, locus: str, detail: str) -> None:
        super().__init__(f"{code}:{locus}:{detail}")
        self.code = code
        self.locus = locus
        self.detail = detail


def _refuse(code: str, locus: str, detail: str) -> NoReturn:
    raise CapabilityCatalogRefusal(code, locus, detail)


def _text(value: object, locus: str, *, identifier: bool = False) -> str:
    if type(value) is not str or not value or len(value) > 16_384:
        _refuse("TEXT_REFUSED", locus, "expected a bounded non-empty exact string")
    if identifier and _ID_RE.fullmatch(value) is None:
        _refuse("IDENTIFIER_REFUSED", locus, f"invalid identifier {value!r}")
    return value


def _digest(value: object, locus: str) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        _refuse("DIGEST_REFUSED", locus, "expected a lowercase SHA-256 digest")
    return value


def _path(value: object, locus: str) -> str:
    path = _text(value, locus)
    parts = path.split("/")
    if (
        "\\" in path
        or ":" in path
        or path.startswith("/")
        or any(ord(character) < 32 or ord(character) == 127 for character in path)
        or any(part in {"", ".", ".."} for part in parts)
    ):
        _refuse("PATH_REFUSED", locus, f"non-canonical relative path {path!r}")
    return path


def _strings(
    value: object,
    locus: str,
    *,
    identifiers: bool = False,
    allow_empty: bool = True,
    sorted_unique: bool = True,
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        _refuse("LIST_REFUSED", locus, "expected an exact list or tuple")
    result = tuple(
        _text(item, f"{locus}[{index}]", identifier=identifiers)
        for index, item in enumerate(value)
    )
    if not allow_empty and not result:
        _refuse("EMPTY_LIST_REFUSED", locus, "at least one item is required")
    if sorted_unique and result != tuple(sorted(set(result))):
        _refuse("ORDER_REFUSED", locus, "items must be sorted and unique")
    return result


def _exact_keys(value: object, expected: set[str], locus: str) -> dict[str, Any]:
    if type(value) is not dict:
        _refuse("OBJECT_REFUSED", locus, "expected an exact object")
    actual = set(value)
    if actual != expected:
        _refuse(
            "FIELD_SET_REFUSED",
            locus,
            f"missing={sorted(expected - actual)} unknown={sorted(actual - expected)}",
        )
    return value


@dataclass(frozen=True, slots=True)
class ResourceRefV1:
    path: str
    sha256: str
    byte_length: int

    def __post_init__(self) -> None:
        _path(self.path, "resource.path")
        _digest(self.sha256, "resource.sha256")
        if type(self.byte_length) is not int or self.byte_length < 0:
            _refuse("LENGTH_REFUSED", self.path, "byte_length must be a non-negative int")

    def to_wire(self) -> dict[str, object]:
        return {
            "byte_length": self.byte_length,
            "path": self.path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True, slots=True)
class ExecutorBindingV1:
    """UNBOUND, or BOUND to host code the compiler found and digested.

    Source frontmatter can never declare a binding; only the compiler sets BOUND, from
    the op inventory, after checking every op of the skill has a registered host executor.
    BOUND says the code exists at these bytes, not that it is correct or authorized.
    """

    state: str = UNBOUND_EXECUTOR_V1
    host_executor_id: str | None = None
    implementation_digest: str | None = None

    def __post_init__(self) -> None:
        if self.state not in EXECUTOR_STATES_V1:
            _refuse("EXECUTOR_STATE_REFUSED", "executor.state", f"{self.state!r}")
        if self.state == UNBOUND_EXECUTOR_V1:
            if self.host_executor_id is not None or self.implementation_digest is not None:
                _refuse(
                    "EXECUTOR_BINDING_REFUSED",
                    "executor",
                    "unbound declarations cannot claim an executor",
                )
            return
        _text(self.host_executor_id, "executor.host_executor_id")
        _digest(self.implementation_digest, "executor.implementation_digest")

    def to_wire(self) -> dict[str, object]:
        return {
            "host_executor_id": self.host_executor_id,
            "implementation_digest": self.implementation_digest,
            "state": self.state,
        }


@dataclass(frozen=True, slots=True)
class SkillCapabilityV1:
    skill_id: str
    name: str
    description: str
    source_path: str
    source_digest: str
    source_colours: tuple[str, ...]
    target_colour: str
    arity: int
    residual_effect: str
    invocation: str
    invocation_explicit: bool
    families: tuple[str, ...]
    declared_dependencies: tuple[str, ...]
    declared_triggers: tuple[str, ...]
    package_resources: tuple[ResourceRefV1, ...]
    executor: ExecutorBindingV1 = ExecutorBindingV1()
    equivariant: bool | None = None
    agent_scope: tuple[str, ...] = ()
    entrypoint_state: str = TRACKED_ENTRYPOINT_V1
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _text(self.skill_id, "skill.skill_id", identifier=True)
        _text(self.name, f"{self.skill_id}.name", identifier=True)
        if self.name != self.skill_id:
            _refuse("NAME_ID_REFUSED", self.skill_id, "skill name must equal skill_id")
        _text(self.description, f"{self.skill_id}.description")
        _path(self.source_path, f"{self.skill_id}.source_path")
        _digest(self.source_digest, f"{self.skill_id}.source_digest")
        colours = _strings(
            self.source_colours,
            f"{self.skill_id}.source_colours",
            sorted_unique=False,
        )
        if any(colour not in OPERAD_COLOURS_V1 for colour in colours):
            _refuse("COLOUR_REFUSED", self.skill_id, "unknown source colour")
        if self.target_colour not in OPERAD_COLOURS_V1:
            _refuse("COLOUR_REFUSED", self.skill_id, "unknown target colour")
        if type(self.arity) is not int or self.arity != len(colours):
            _refuse("ARITY_REFUSED", self.skill_id, "arity must equal source-colour count")
        _text(self.residual_effect, f"{self.skill_id}.residual_effect")
        _text(self.invocation, f"{self.skill_id}.invocation")
        if type(self.invocation_explicit) is not bool:
            _refuse("BOOLEAN_REFUSED", self.skill_id, "invocation_explicit must be bool")
        _strings(
            self.families,
            f"{self.skill_id}.families",
            identifiers=True,
            allow_empty=False,
        )
        _strings(
            self.declared_dependencies,
            f"{self.skill_id}.declared_dependencies",
            identifiers=True,
        )
        _strings(self.declared_triggers, f"{self.skill_id}.declared_triggers")
        if type(self.package_resources) is not tuple:
            _refuse("RESOURCE_LIST_REFUSED", self.skill_id, "package_resources must be a tuple")
        if any(type(item) is not ResourceRefV1 for item in self.package_resources):
            _refuse(
                "RESOURCE_TYPE_REFUSED",
                self.skill_id,
                "package_resources must contain exact ResourceRefV1 values",
            )
        if tuple(item.path for item in self.package_resources) != tuple(
            sorted({item.path for item in self.package_resources})
        ):
            _refuse("RESOURCE_ORDER_REFUSED", self.skill_id, "resources must be sorted and unique")
        if type(self.executor) is not ExecutorBindingV1:
            _refuse(
                "EXECUTOR_TYPE_REFUSED",
                self.skill_id,
                "executor binding has the wrong type",
            )
        if self.equivariant is not None and type(self.equivariant) is not bool:
            _refuse("BOOLEAN_REFUSED", self.skill_id, "equivariant must be bool or null")
        _strings(self.agent_scope, f"{self.skill_id}.agent_scope")
        if self.entrypoint_state != TRACKED_ENTRYPOINT_V1:
            _refuse(
                "ENTRYPOINT_STATE_REFUSED",
                self.skill_id,
                "skill must be Git-tracked canonical",
            )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            _refuse("AUTHORITY_REFUSED", self.skill_id, "authority_effect must be none")

    def to_wire(self) -> dict[str, object]:
        return {
            "agent_scope": list(self.agent_scope),
            "arity": self.arity,
            "authority_effect": self.authority_effect,
            "declared_dependencies": list(self.declared_dependencies),
            "declared_triggers": list(self.declared_triggers),
            "description": self.description,
            "entrypoint_state": self.entrypoint_state,
            "equivariant": self.equivariant,
            "executor": self.executor.to_wire(),
            "families": list(self.families),
            "invocation": self.invocation,
            "invocation_explicit": self.invocation_explicit,
            "name": self.name,
            "package_resources": [item.to_wire() for item in self.package_resources],
            "residual_effect": self.residual_effect,
            "skill_id": self.skill_id,
            "source_colours": list(self.source_colours),
            "source_digest": self.source_digest,
            "source_path": self.source_path,
            "target_colour": self.target_colour,
        }


@dataclass(frozen=True, slots=True)
class AgentCapabilityV1:
    agent_id: str
    name: str
    description: str
    model: str
    source_path: str
    source_digest: str
    license_digest: str
    licensed_skill_ids: tuple[str, ...]
    licensed_colour_ids: tuple[str, ...]
    tools: tuple[str, ...]
    standalone: bool
    entrypoint_state: str = TRACKED_ENTRYPOINT_V1
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        _text(self.agent_id, "agent.agent_id", identifier=True)
        _text(self.name, f"{self.agent_id}.name", identifier=True)
        if self.name != self.agent_id:
            _refuse("NAME_ID_REFUSED", self.agent_id, "agent name must equal agent_id")
        _text(self.description, f"{self.agent_id}.description")
        _text(self.model, f"{self.agent_id}.model")
        _path(self.source_path, f"{self.agent_id}.source_path")
        _digest(self.source_digest, f"{self.agent_id}.source_digest")
        _digest(self.license_digest, f"{self.agent_id}.license_digest")
        _strings(
            self.licensed_skill_ids,
            f"{self.agent_id}.licensed_skill_ids",
            identifiers=True,
            allow_empty=False,
        )
        colours = _strings(
            self.licensed_colour_ids,
            f"{self.agent_id}.licensed_colour_ids",
            allow_empty=False,
        )
        if any(colour not in OPERAD_COLOURS_V1 for colour in colours):
            _refuse("COLOUR_REFUSED", self.agent_id, "unknown licensed colour")
        _strings(self.tools, f"{self.agent_id}.tools")
        if type(self.standalone) is not bool:
            _refuse("BOOLEAN_REFUSED", self.agent_id, "standalone must be bool")
        if self.entrypoint_state != TRACKED_ENTRYPOINT_V1:
            _refuse(
                "ENTRYPOINT_STATE_REFUSED",
                self.agent_id,
                "agent must be Git-tracked canonical",
            )
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            _refuse("AUTHORITY_REFUSED", self.agent_id, "authority_effect must be none")
        expected_license_digest = compute_agent_license_digest(
            agent_id=self.agent_id,
            licensed_skill_ids=self.licensed_skill_ids,
            licensed_colour_ids=self.licensed_colour_ids,
            tools=self.tools,
            standalone=self.standalone,
        )
        if self.license_digest != expected_license_digest:
            _refuse(
                "LICENSE_DIGEST_MISMATCH_REFUSED",
                self.agent_id,
                "license digest does not verify",
            )

    def to_wire(self) -> dict[str, object]:
        return {
            "agent_id": self.agent_id,
            "authority_effect": self.authority_effect,
            "description": self.description,
            "entrypoint_state": self.entrypoint_state,
            "license_digest": self.license_digest,
            "licensed_colour_ids": list(self.licensed_colour_ids),
            "licensed_skill_ids": list(self.licensed_skill_ids),
            "model": self.model,
            "name": self.name,
            "source_digest": self.source_digest,
            "source_path": self.source_path,
            "standalone": self.standalone,
            "tools": list(self.tools),
        }


def compute_agent_license_digest(
    *,
    agent_id: str,
    licensed_skill_ids: tuple[str, ...],
    licensed_colour_ids: tuple[str, ...],
    tools: tuple[str, ...],
    standalone: bool,
) -> str:
    payload = {
        "agent_id": agent_id,
        "authority_effect": AUTHORITY_EFFECT_NONE,
        "licensed_colour_ids": list(licensed_colour_ids),
        "licensed_skill_ids": list(licensed_skill_ids),
        "standalone": standalone,
        "tools": list(tools),
    }
    return hashlib.sha256(
        AGENT_LICENSE_DIGEST_DOMAIN_V1 + _canonical_json(payload)
    ).hexdigest()


def _validate_dependency_dag(skills: dict[str, SkillCapabilityV1]) -> None:
    states: dict[str, int] = {}

    def visit(skill_id: str, trail: tuple[str, ...]) -> None:
        state = states.get(skill_id, 0)
        if state == 2:
            return
        if state == 1:
            cycle = (*trail, skill_id)
            _refuse(
                "DEPENDENCY_CYCLE_REFUSED",
                skill_id,
                " -> ".join(cycle),
            )
        states[skill_id] = 1
        for dependency in skills[skill_id].declared_dependencies:
            visit(dependency, (*trail, skill_id))
        states[skill_id] = 2

    for skill_id in sorted(skills):
        visit(skill_id, ())


@dataclass(frozen=True, slots=True)
class CapabilityCatalogV1:
    skills: tuple[SkillCapabilityV1, ...]
    agents: tuple[AgentCapabilityV1, ...]
    catalog_digest: str
    schema_version: str = CATALOG_SCHEMA_V1
    inventory_kind: str = TRACKED_INVENTORY_V1
    authority_effect: str = AUTHORITY_EFFECT_NONE

    def __post_init__(self) -> None:
        if self.schema_version != CATALOG_SCHEMA_V1:
            _refuse("SCHEMA_REFUSED", "catalog", "unsupported schema")
        if self.inventory_kind != TRACKED_INVENTORY_V1:
            _refuse("INVENTORY_KIND_REFUSED", "catalog", "inventory is not Git-tracked")
        if self.authority_effect != AUTHORITY_EFFECT_NONE:
            _refuse("AUTHORITY_REFUSED", "catalog", "authority_effect must be none")
        _digest(self.catalog_digest, "catalog.catalog_digest")
        if type(self.skills) is not tuple or type(self.agents) is not tuple:
            _refuse("CATALOG_LIST_REFUSED", "catalog", "skills and agents must be tuples")
        if any(type(item) is not SkillCapabilityV1 for item in self.skills):
            _refuse(
                "SKILL_TYPE_REFUSED",
                "catalog.skills",
                "skills must contain exact SkillCapabilityV1 values",
            )
        if any(type(item) is not AgentCapabilityV1 for item in self.agents):
            _refuse(
                "AGENT_TYPE_REFUSED",
                "catalog.agents",
                "agents must contain exact AgentCapabilityV1 values",
            )
        skill_ids = tuple(item.skill_id for item in self.skills)
        agent_ids = tuple(item.agent_id for item in self.agents)
        if skill_ids != tuple(sorted(set(skill_ids))) or not skill_ids:
            _refuse(
                "SKILL_ORDER_REFUSED",
                "catalog.skills",
                "skills must be non-empty, sorted, and unique",
            )
        if agent_ids != tuple(sorted(set(agent_ids))):
            _refuse(
                "AGENT_ORDER_REFUSED",
                "catalog.agents",
                "agents must be sorted and unique",
            )
        skills = {item.skill_id: item for item in self.skills}
        for skill in self.skills:
            missing = set(skill.declared_dependencies) - set(skills)
            if missing:
                _refuse(
                    "DEPENDENCY_REFUSED",
                    skill.skill_id,
                    f"unknown dependencies {sorted(missing)}",
                )
        _validate_dependency_dag(skills)
        for agent in self.agents:
            missing = set(agent.licensed_skill_ids) - set(skills)
            if missing:
                _refuse("LICENSE_REFUSED", agent.agent_id, f"unknown skills {sorted(missing)}")
            allowed = set(agent.licensed_colour_ids)
            for skill_id in agent.licensed_skill_ids:
                operation = skills[skill_id]
                used = set(operation.source_colours) | {operation.target_colour}
                if not used <= allowed:
                    _refuse(
                        "LICENSE_COLOUR_ESCAPE_REFUSED",
                        agent.agent_id,
                        f"{skill_id} uses {sorted(used - allowed)}",
                    )

    def to_wire(self, *, include_digest: bool = True) -> dict[str, object]:
        result: dict[str, object] = {
            "agents": [item.to_wire() for item in self.agents],
            "authority_effect": self.authority_effect,
            "inventory_kind": self.inventory_kind,
            "schema_version": self.schema_version,
            "skills": [item.to_wire() for item in self.skills],
        }
        if include_digest:
            result["catalog_digest"] = self.catalog_digest
        return result


def _canonical_json(value: object) -> bytes:
    try:
        return (
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n"
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as error:
        raise CapabilityCatalogRefusal("JSON_REFUSED", "catalog", str(error)) from error


def compute_catalog_digest(catalog: CapabilityCatalogV1) -> str:
    return hashlib.sha256(
        CATALOG_DIGEST_DOMAIN_V1 + _canonical_json(catalog.to_wire(include_digest=False))
    ).hexdigest()


def seal_capability_catalog(
    *, skills: tuple[SkillCapabilityV1, ...], agents: tuple[AgentCapabilityV1, ...]
) -> CapabilityCatalogV1:
    provisional = CapabilityCatalogV1(
        skills=skills,
        agents=agents,
        catalog_digest="0" * 64,
    )
    return replace(provisional, catalog_digest=compute_catalog_digest(provisional))


def encode_capability_catalog(catalog: CapabilityCatalogV1) -> bytes:
    if type(catalog) is not CapabilityCatalogV1:
        _refuse("TYPE_REFUSED", "catalog", "expected CapabilityCatalogV1")
    if compute_catalog_digest(catalog) != catalog.catalog_digest:
        _refuse("DIGEST_MISMATCH_REFUSED", "catalog", "catalog digest does not verify")
    return _canonical_json(catalog.to_wire())


def _duplicate_refusing_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _refuse("DUPLICATE_KEY_REFUSED", key, "duplicate JSON key")
        result[key] = value
    return result


def _resource_from_wire(value: object, locus: str) -> ResourceRefV1:
    row = _exact_keys(value, {"byte_length", "path", "sha256"}, locus)
    return ResourceRefV1(path=row["path"], sha256=row["sha256"], byte_length=row["byte_length"])


def _executor_from_wire(value: object, locus: str) -> ExecutorBindingV1:
    row = _exact_keys(value, {"host_executor_id", "implementation_digest", "state"}, locus)
    return ExecutorBindingV1(
        state=row["state"],
        host_executor_id=row["host_executor_id"],
        implementation_digest=row["implementation_digest"],
    )


def _skill_from_wire(value: object, locus: str) -> SkillCapabilityV1:
    keys = {
        "agent_scope", "arity", "authority_effect", "declared_dependencies",
        "declared_triggers", "description", "entrypoint_state", "equivariant",
        "executor", "families", "invocation", "invocation_explicit", "name",
        "package_resources", "residual_effect", "skill_id", "source_colours",
        "source_digest", "source_path", "target_colour",
    }
    row = _exact_keys(value, keys, locus)
    resources = row["package_resources"]
    if type(resources) is not list:
        _refuse("RESOURCE_LIST_REFUSED", locus, "package_resources must be a list")
    return SkillCapabilityV1(
        skill_id=row["skill_id"],
        name=row["name"],
        description=row["description"],
        source_path=row["source_path"],
        source_digest=row["source_digest"],
        source_colours=_strings(
            row["source_colours"],
            f"{locus}.source_colours",
            sorted_unique=False,
        ),
        target_colour=row["target_colour"],
        arity=row["arity"],
        residual_effect=row["residual_effect"],
        invocation=row["invocation"],
        invocation_explicit=row["invocation_explicit"],
        families=_strings(
            row["families"],
            f"{locus}.families",
            identifiers=True,
            allow_empty=False,
        ),
        declared_dependencies=_strings(
            row["declared_dependencies"],
            f"{locus}.declared_dependencies",
            identifiers=True,
        ),
        declared_triggers=_strings(row["declared_triggers"], f"{locus}.declared_triggers"),
        package_resources=tuple(
            _resource_from_wire(item, f"{locus}.package_resources[{index}]")
            for index, item in enumerate(resources)
        ),
        executor=_executor_from_wire(row["executor"], f"{locus}.executor"),
        equivariant=row["equivariant"],
        agent_scope=_strings(row["agent_scope"], f"{locus}.agent_scope"),
        entrypoint_state=row["entrypoint_state"],
        authority_effect=row["authority_effect"],
    )


def _agent_from_wire(value: object, locus: str) -> AgentCapabilityV1:
    keys = {
        "agent_id", "authority_effect", "description", "entrypoint_state",
        "license_digest", "licensed_colour_ids", "licensed_skill_ids", "model",
        "name", "source_digest", "source_path", "standalone", "tools",
    }
    row = _exact_keys(value, keys, locus)
    return AgentCapabilityV1(
        agent_id=row["agent_id"],
        name=row["name"],
        description=row["description"],
        model=row["model"],
        source_path=row["source_path"],
        source_digest=row["source_digest"],
        license_digest=row["license_digest"],
        licensed_skill_ids=_strings(
            row["licensed_skill_ids"],
            f"{locus}.licensed_skill_ids",
            identifiers=True,
            allow_empty=False,
        ),
        licensed_colour_ids=_strings(
            row["licensed_colour_ids"],
            f"{locus}.licensed_colour_ids",
            allow_empty=False,
        ),
        tools=_strings(row["tools"], f"{locus}.tools"),
        standalone=row["standalone"],
        entrypoint_state=row["entrypoint_state"],
        authority_effect=row["authority_effect"],
    )


def decode_capability_catalog(data: bytes) -> CapabilityCatalogV1:
    if (
        type(data) is not bytes
        or not data
        or b"\r" in data
        or data.startswith(b"\xef\xbb\xbf")
    ):
        _refuse("BYTES_REFUSED", "catalog", "catalog must be non-empty LF UTF-8 without BOM")
    try:
        wire = json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=_duplicate_refusing_object,
            parse_float=lambda _value: _refuse(
                "FLOAT_REFUSED", "catalog", "floats are forbidden"
            ),
            parse_constant=lambda _value: _refuse(
                "CONSTANT_REFUSED", "catalog", "non-finite values are forbidden"
            ),
        )
    except CapabilityCatalogRefusal:
        raise
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CapabilityCatalogRefusal("JSON_REFUSED", "catalog", str(error)) from error
    row = _exact_keys(
        wire,
        {
            "agents",
            "authority_effect",
            "catalog_digest",
            "inventory_kind",
            "schema_version",
            "skills",
        },
        "catalog",
    )
    if type(row["skills"]) is not list or type(row["agents"]) is not list:
        _refuse("CATALOG_LIST_REFUSED", "catalog", "skills and agents must be lists")
    catalog = CapabilityCatalogV1(
        skills=tuple(
            _skill_from_wire(item, f"catalog.skills[{index}]")
            for index, item in enumerate(row["skills"])
        ),
        agents=tuple(
            _agent_from_wire(item, f"catalog.agents[{index}]")
            for index, item in enumerate(row["agents"])
        ),
        catalog_digest=row["catalog_digest"],
        schema_version=row["schema_version"],
        inventory_kind=row["inventory_kind"],
        authority_effect=row["authority_effect"],
    )
    if data != encode_capability_catalog(catalog):
        _refuse("NONCANONICAL_JSON_REFUSED", "catalog", "catalog bytes are not canonical")
    return catalog


__all__ = [
    "BOUND_EXECUTOR_V1",
    "OPERAD_COLOURS_V1",
    "AgentCapabilityV1",
    "CapabilityCatalogRefusal",
    "CapabilityCatalogV1",
    "ExecutorBindingV1",
    "ResourceRefV1",
    "SkillCapabilityV1",
    "compute_agent_license_digest",
    "compute_catalog_digest",
    "decode_capability_catalog",
    "encode_capability_catalog",
    "seal_capability_catalog",
]
