"""Typed domain models for Workflows, Agents, Skills, and Anti-Skill references.

All types are immutable, strongly typed, and enforce AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any

from operads.domain.value_objects.authority import AuthorityEffect

NAME_PATTERN = re.compile(r"^[a-z0-9_\-]+$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
ADMITTED_COLOURS = frozenset(
    {
        "State",
        "Proof",
        "Paper",
        "Code",
        "Contract",
        "Receipt",
        "Ledger",
        "Diagram",
        "Audit",
        "Post",
    }
)
ADMITTED_RESIDUAL = "unknown"
DECLARATION_STRICT_EXPLICIT = "STRICT_EXPLICIT"
DECLARATION_COMPATIBILITY_DEFAULTED = "COMPATIBILITY_DEFAULTED"
DECLARATION_STATUSES = frozenset(
    {DECLARATION_STRICT_EXPLICIT, DECLARATION_COMPATIBILITY_DEFAULTED}
)


def normalize_estate_path(raw_path: str) -> str:
    """Return the sole canonical estate-relative path or refuse it."""

    if type(raw_path) is not str or not raw_path:
        raise TypeError("estate path must be a non-empty exact str")
    normalized = raw_path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    normalized = normalized.removeprefix(".agents/")
    path = PurePosixPath(normalized)
    if (
        not normalized
        or normalized.startswith("/")
        or re.match(r"^[A-Za-z]:/", normalized)
        or path.is_absolute()
        or ".." in path.parts
    ):
        raise ValueError(f"snapshot path escapes estate root: {raw_path!r}")
    return path.as_posix()


def _validate_name(val: str, label: str) -> str:
    if type(val) is not str or not NAME_PATTERN.fullmatch(val):
        raise ValueError(f"{label} must match ^[a-z0-9_\\-]+$, got {val!r}")
    return val


def _validate_digest(val: str, label: str) -> str:
    if type(val) is not str or not DIGEST_PATTERN.fullmatch(val):
        raise ValueError(f"{label} must match sha256:[0-9a-f]{{64}}, got {val!r}")
    return val


def _validate_authority_none(val: str, label: str) -> str:
    if val != AuthorityEffect.NONE.value and val != "None":
        raise ValueError(f"{label} authority_effect must be 'None', got {val!r}")
    return "None"


@dataclass(frozen=True)
class InstructionAtomV1:
    """Atomic instruction line or block extracted from a markdown skill or agent spec."""

    atom_id: str
    section: str
    content: str
    ordinal: int
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.atom_id, "InstructionAtomV1.atom_id")
        if type(self.section) is not str:
            raise TypeError("section must be a str")
        if type(self.content) is not str:
            raise TypeError("content must be a str")
        if type(self.ordinal) is not int or self.ordinal < 0:
            raise ValueError("ordinal must be a non-negative int")
        _validate_authority_none(self.authority_effect, "InstructionAtomV1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "section": self.section,
            "content": self.content,
            "ordinal": self.ordinal,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class SkillOperationV1:
    """1-morphism atomic operation declaration."""

    operation_id: str
    source_colours: tuple[str, ...]
    target_colour: str
    arity: int
    residual_effect: str = "unknown"
    declaration_status: str = DECLARATION_STRICT_EXPLICIT
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.operation_id, "SkillOperationV1.operation_id")
        if type(self.arity) is not int or self.arity < 0:
            raise ValueError("arity must be a non-negative int")
        if not isinstance(self.source_colours, tuple):
            object.__setattr__(self, "source_colours", tuple(self.source_colours))
        if any(type(colour) is not str for colour in self.source_colours):
            raise TypeError("source_colours items must be exact str")
        if type(self.target_colour) is not str:
            raise TypeError("target_colour must be a str")
        unknown = [
            colour
            for colour in (*self.source_colours, self.target_colour)
            if colour not in ADMITTED_COLOURS
        ]
        if unknown:
            raise ValueError(f"unadmitted colour: {unknown[0]}")
        if self.arity != len(self.source_colours):
            raise ValueError("arity must equal len(source_colours)")
        if type(self.residual_effect) is not str or not self.residual_effect:
            raise TypeError("residual_effect must be a nonempty str")
        if self.declaration_status not in DECLARATION_STATUSES:
            raise ValueError("declaration_status is not a closed declaration status")
        if (
            self.declaration_status == DECLARATION_STRICT_EXPLICIT
            and self.residual_effect != ADMITTED_RESIDUAL
        ):
            raise ValueError(
                f"strict residual_effect must be {ADMITTED_RESIDUAL!r}, "
                f"got {self.residual_effect!r}"
            )
        _validate_authority_none(self.authority_effect, "SkillOperationV1")


@dataclass(frozen=True)
class SkillFamilyV1:
    """Categorical classification family for skills."""

    family_id: str
    description: str
    prefix: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.family_id, "SkillFamilyV1.family_id")
        if type(self.description) is not str:
            raise TypeError("description must be a str")
        if type(self.prefix) is not str:
            raise TypeError("prefix must be a str")
        _validate_authority_none(self.authority_effect, "SkillFamilyV1")


@dataclass(frozen=True)
class ResidualClaimRefV1:
    """Reference to a finite residual observation or claim."""

    claim_id: str
    subject_id: str
    residual_kind: str
    observation_digest: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.claim_id, "ResidualClaimRefV1.claim_id")
        _validate_name(self.subject_id, "ResidualClaimRefV1.subject_id")
        _validate_digest(
            self.observation_digest, "ResidualClaimRefV1.observation_digest"
        )
        _validate_authority_none(self.authority_effect, "ResidualClaimRefV1")


@dataclass(frozen=True)
class SkillSpecV1:
    """Full typed specification of a 1-morphism skill."""

    skill_id: str
    name: str
    description: str
    invocation: str
    operation: SkillOperationV1
    family: str
    atoms: tuple[InstructionAtomV1, ...] = ()
    file_path: str = ""
    source_digest: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.skill_id, "SkillSpecV1.skill_id")
        if type(self.name) is not str:
            raise TypeError("name must be a str")
        if type(self.description) is not str:
            raise TypeError("description must be a str")
        if not isinstance(self.operation, SkillOperationV1):
            raise TypeError("operation must be a SkillOperationV1")
        if not isinstance(self.atoms, tuple):
            object.__setattr__(self, "atoms", tuple(self.atoms))
        if self.source_digest:
            _validate_digest(self.source_digest, "SkillSpecV1.source_digest")
        _validate_authority_none(self.authority_effect, "SkillSpecV1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "invocation": self.invocation,
            "operation": {
                "operation_id": self.operation.operation_id,
                "source_colours": list(self.operation.source_colours),
                "target_colour": self.operation.target_colour,
                "arity": self.operation.arity,
                "residual_effect": self.operation.residual_effect,
                "declaration_status": self.operation.declaration_status,
                "authority_effect": self.operation.authority_effect,
            },
            "family": self.family,
            "atoms": [atom.to_dict() for atom in self.atoms],
            "file_path": self.file_path,
            "source_digest": self.source_digest,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class MetaSkillSpecV1:
    """Higher-arity quotient meta-skill specification."""

    meta_skill_id: str
    name: str
    source_colours: tuple[str, ...]
    target_colour: str
    arity: int
    quotient_signature: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.meta_skill_id, "MetaSkillSpecV1.meta_skill_id")
        if type(self.name) is not str:
            raise TypeError("name must be a str")
        if not isinstance(self.source_colours, tuple):
            object.__setattr__(self, "source_colours", tuple(self.source_colours))
        _validate_authority_none(self.authority_effect, "MetaSkillSpecV1")


@dataclass(frozen=True)
class AgentSkillBindingV1:
    """Binding of a licensed skill to an agent capability slice."""

    agent_id: str
    skill_id: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.agent_id, "AgentSkillBindingV1.agent_id")
        _validate_name(self.skill_id, "AgentSkillBindingV1.skill_id")
        _validate_authority_none(self.authority_effect, "AgentSkillBindingV1")


@dataclass(frozen=True)
class AgentSpecV1:
    """Agent functor and capability slice specification."""

    agent_id: str
    name: str
    description: str
    model: str
    licensed_skills: tuple[str, ...]
    licensed_colours: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    standalone: bool = True
    file_path: str = ""
    source_digest: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.agent_id, "AgentSpecV1.agent_id")
        if type(self.description) is not str:
            raise TypeError("description must be a str")
        if type(self.model) is not str:
            raise TypeError("model must be a str")
        if not isinstance(self.licensed_skills, tuple):
            object.__setattr__(self, "licensed_skills", tuple(self.licensed_skills))
        if not isinstance(self.licensed_colours, tuple):
            object.__setattr__(self, "licensed_colours", tuple(self.licensed_colours))
        if not isinstance(self.tools, tuple):
            object.__setattr__(self, "tools", tuple(self.tools))
        if self.source_digest:
            _validate_digest(self.source_digest, "AgentSpecV1.source_digest")
        _validate_authority_none(self.authority_effect, "AgentSpecV1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "licensed_skills": list(self.licensed_skills),
            "licensed_colours": list(self.licensed_colours),
            "tools": list(self.tools),
            "standalone": self.standalone,
            "file_path": self.file_path,
            "source_digest": self.source_digest,
            "authority_effect": self.authority_effect,
        }


# Aliases for backward compatibility
SkillDefV1 = SkillSpecV1
AgentDefV1 = AgentSpecV1


@dataclass(frozen=True)
class WorkflowNodeV1:
    """Typed domain node in a workflow pipeline."""

    node_id: str
    slot: int
    operation_id: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.node_id, "WorkflowNodeV1.node_id")
        if type(self.slot) is not int or self.slot < 0:
            raise ValueError("slot must be a non-negative int")
        _validate_name(self.operation_id, "WorkflowNodeV1.operation_id")
        _validate_authority_none(self.authority_effect, "WorkflowNodeV1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "slot": self.slot,
            "operation": self.operation_id,
            "authority_effect": self.authority_effect,
        }


WorkflowNodeDefV1 = WorkflowNodeV1


@dataclass(frozen=True)
class WorkflowEdgeV1:
    """Typed directed edge between workflow nodes."""

    from_node: str
    to_node: str
    colour: str

    def __post_init__(self) -> None:
        _validate_name(self.from_node, "WorkflowEdgeV1.from_node")
        _validate_name(self.to_node, "WorkflowEdgeV1.to_node")
        if type(self.colour) is not str or not self.colour:
            raise ValueError("WorkflowEdgeV1.colour must be a non-empty str")

    def to_dict(self) -> dict[str, str]:
        return {
            "from_node": self.from_node,
            "to_node": self.to_node,
            "colour": self.colour,
        }


@dataclass(frozen=True)
class WorkflowSpecV1:
    """Typed workflow pipeline specification."""

    workflow_id: str
    name: str
    source_colours: tuple[str, ...]
    target_colour: str
    nodes: tuple[WorkflowNodeV1, ...]
    edges: tuple[WorkflowEdgeV1, ...] = ()
    file_path: str = ""
    source_digest: str = ""
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.workflow_id, "WorkflowSpecV1.workflow_id")
        if type(self.name) is not str:
            raise TypeError("name must be a str")
        if type(self.target_colour) is not str:
            raise TypeError("target_colour must be a str")
        if not isinstance(self.source_colours, tuple):
            object.__setattr__(self, "source_colours", tuple(self.source_colours))
        if not isinstance(self.nodes, tuple):
            object.__setattr__(self, "nodes", tuple(self.nodes))
        if not isinstance(self.edges, tuple):
            object.__setattr__(self, "edges", tuple(self.edges))
        if self.source_digest:
            _validate_digest(self.source_digest, "WorkflowSpecV1.source_digest")
        _validate_authority_none(self.authority_effect, "WorkflowSpecV1")

    @property
    def pipeline(self) -> tuple[WorkflowNodeV1, ...]:
        return self.nodes

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "source_colours": list(self.source_colours),
            "target_colour": self.target_colour,
            "pipeline": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "file_path": self.file_path,
            "source_digest": self.source_digest,
            "authority_effect": self.authority_effect,
        }


WorkflowDefV1 = WorkflowSpecV1


@dataclass(frozen=True)
class CatalogAntiSkillRefV1:
    """Reference to an AntiSkill from Prompt Civilization domain."""

    anti_skill_id: str
    failure_code: str
    spec_digest: str
    status: str = "PROPOSED"
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _validate_name(self.anti_skill_id.lower().replace("_", "-"), "anti_skill_id")
        _validate_name(self.failure_code.lower().replace("_", "-"), "failure_code")
        if self.spec_digest:
            _validate_digest(self.spec_digest, "CatalogAntiSkillRefV1.spec_digest")
        _validate_authority_none(self.authority_effect, "CatalogAntiSkillRefV1")

    def to_dict(self) -> dict[str, Any]:
        return {
            "anti_skill_id": self.anti_skill_id,
            "failure_code": self.failure_code,
            "spec_digest": self.spec_digest,
            "status": self.status,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class SourceParityReceiptV1:
    """Witness checking byte agreement across the legacy-current source and 4-host mirrors."""

    receipt_id: str
    estate_root: str
    mirror_hashes: MappingProxyType[str, str]
    verified: bool
    authority_effect: str = "None"

    def __init__(
        self,
        receipt_id: str,
        estate_root: str,
        mirror_hashes: Mapping[str, str],
        verified: bool,
        authority_effect: str = "None",
    ) -> None:
        object.__setattr__(self, "receipt_id", receipt_id)
        object.__setattr__(self, "estate_root", estate_root)
        object.__setattr__(self, "mirror_hashes", MappingProxyType(dict(mirror_hashes)))
        object.__setattr__(self, "verified", verified)
        _validate_authority_none(authority_effect, "SourceParityReceiptV1")
        object.__setattr__(self, "authority_effect", "None")


@dataclass(frozen=True)
class LegacyEstateSnapshotV1:
    """Raw snapshot of the unparsed legacy-current estate files."""

    snapshot_id: str
    raw_files: MappingProxyType[str, bytes]
    file_hashes: MappingProxyType[str, str]
    authority_effect: str = "None"

    def __init__(
        self,
        snapshot_id: str,
        raw_files: Mapping[str, bytes],
        file_hashes: Mapping[str, str] | None = None,
        authority_effect: str = "None",
    ) -> None:
        _validate_name(snapshot_id, "LegacyEstateSnapshotV1.snapshot_id")
        frozen_raw: dict[str, bytes] = {}
        canonical_paths: dict[str, str] = {}
        for path, raw in raw_files.items():
            if type(path) is not str or not path:
                raise TypeError("raw_files keys must be non-empty str paths")
            if type(raw) is not bytes:
                raise TypeError(f"raw_files[{path!r}] must be exact bytes")
            canonical_path = normalize_estate_path(path)
            previous = canonical_paths.get(canonical_path)
            if previous is not None:
                raise ValueError(
                    "duplicate normalized estate path: "
                    f"{previous!r} and {path!r} -> {canonical_path!r}"
                )
            canonical_paths[canonical_path] = path
            frozen_raw[path] = raw
        object.__setattr__(self, "snapshot_id", snapshot_id)
        object.__setattr__(self, "raw_files", MappingProxyType(frozen_raw))
        computed = {
            k: f"sha256:{hashlib.sha256(v).hexdigest()}"
            for k, v in sorted(frozen_raw.items())
        }
        if file_hashes is not None:
            if set(file_hashes) != set(computed):
                raise ValueError("file_hashes keys must exactly match raw_files keys")
            for path, claimed in file_hashes.items():
                _validate_digest(claimed, f"file_hashes[{path!r}]")
                if claimed != computed[path]:
                    raise ValueError(f"file_hashes[{path!r}] does not match raw bytes")
        object.__setattr__(self, "file_hashes", MappingProxyType(computed))
        _validate_authority_none(authority_effect, "LegacyEstateSnapshotV1")
        object.__setattr__(self, "authority_effect", "None")


@dataclass(frozen=True)
class EstateDiagnosticFindingV1:
    finding_kind: str
    subject_id: str
    message: str


@dataclass(frozen=True)
class EstateDiagnosticsV1:
    """Diagnostics and refusal container for catalog compilation."""

    status: str  # "OK" | "HOLD" | "REFUSAL"
    findings: tuple[EstateDiagnosticFindingV1, ...]
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not isinstance(self.findings, tuple):
            object.__setattr__(self, "findings", tuple(self.findings))
        _validate_authority_none(self.authority_effect, "EstateDiagnosticsV1")

    @property
    def is_ok(self) -> bool:
        return self.status == "OK" and len(self.findings) == 0


@dataclass(frozen=True)
class EstateCatalogSnapshotV1:
    """Immutable snapshot of the entire WAS estate catalog."""

    snapshot_id: str
    skills: MappingProxyType[str, SkillSpecV1]
    agents: MappingProxyType[str, AgentSpecV1]
    workflows: MappingProxyType[str, WorkflowSpecV1]
    anti_skills: MappingProxyType[str, CatalogAntiSkillRefV1]
    snapshot_digest: str = ""
    authority_effect: str = "None"

    def __init__(
        self,
        snapshot_id: str,
        skills: Mapping[str, SkillSpecV1],
        agents: Mapping[str, AgentSpecV1],
        workflows: Mapping[str, WorkflowSpecV1],
        anti_skills: Mapping[str, CatalogAntiSkillRefV1],
        snapshot_digest: str = "",
        authority_effect: str = "None",
    ) -> None:
        _validate_name(snapshot_id, "EstateCatalogSnapshotV1.snapshot_id")
        object.__setattr__(self, "snapshot_id", snapshot_id)
        object.__setattr__(self, "skills", MappingProxyType(dict(skills)))
        object.__setattr__(self, "agents", MappingProxyType(dict(agents)))
        object.__setattr__(self, "workflows", MappingProxyType(dict(workflows)))
        object.__setattr__(self, "anti_skills", MappingProxyType(dict(anti_skills)))
        _validate_authority_none(authority_effect, "EstateCatalogSnapshotV1")
        object.__setattr__(self, "authority_effect", "None")

        payload = {
            "snapshot_id": snapshot_id,
            "skills": {k: v.to_dict() for k, v in sorted(self.skills.items())},
            "agents": {k: v.to_dict() for k, v in sorted(self.agents.items())},
            "workflows": {k: v.to_dict() for k, v in sorted(self.workflows.items())},
            "anti_skills": {
                k: v.to_dict() for k, v in sorted(self.anti_skills.items())
            },
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        computed_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
        if snapshot_digest and snapshot_digest != computed_digest:
            raise ValueError("snapshot_digest does not match canonical catalog bytes")
        object.__setattr__(self, "snapshot_digest", computed_digest)

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_digest": self.snapshot_digest,
            "skills": {k: v.to_dict() for k, v in sorted(self.skills.items())},
            "agents": {k: v.to_dict() for k, v in sorted(self.agents.items())},
            "workflows": {k: v.to_dict() for k, v in sorted(self.workflows.items())},
            "anti_skills": {
                k: v.to_dict() for k, v in sorted(self.anti_skills.items())
            },
            "authority_effect": self.authority_effect,
        }
