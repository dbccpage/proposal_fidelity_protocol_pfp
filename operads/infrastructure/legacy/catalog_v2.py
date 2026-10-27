"""Versioned typed bindings for the derived WAS estate catalog.

The V2 catalog does not replace ``.agents``.  It binds selected legacy-current
bytes to small immutable records that can be consumed by OEAS without granting
execution, admission, or transition authority.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from .models import (
    DECLARATION_STRICT_EXPLICIT,
    CatalogAntiSkillRefV1,
    EstateCatalogSnapshotV1,
    SkillOperationV1,
)

SCHEMA_ESTATE_CATALOG_V2 = "core.was.estate_catalog.v2"
LIFECYCLE_STATES = frozenset(
    {"DRAFT", "TYPED", "BOUND", "TESTED", "COMPOSABLE", "ADMITTED"}
)
SOURCE_ROLES = frozenset({"LEGACY_CURRENT", "SHADOW", "COMPATIBILITY"})


def _text(value: Any, label: str, *, nonempty: bool = True) -> str:
    if type(value) is not str:
        raise TypeError(f"{label} must be an exact str")
    if nonempty and not value:
        raise ValueError(f"{label} must not be empty")
    if len(value.encode("utf-8")) > 16_384:
        raise ValueError(f"{label} exceeds the 16384-byte bound")
    return value


def _integer(value: Any, label: str, *, minimum: int = 0) -> int:
    if type(value) is not int:
        raise TypeError(f"{label} must be an exact int")
    if value < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    return value


def _tuple_text(value: Sequence[str], label: str) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise TypeError(f"{label} must be an exact tuple or list")
    if len(value) > 256:
        raise ValueError(f"{label} exceeds the 256-item bound")
    result = tuple(_text(item, f"{label}[]") for item in value)
    if len(set(result)) != len(result):
        raise ValueError(f"{label} must not contain duplicates")
    return result


def _sha256(value: Any, label: str) -> str:
    text = _text(value, label)
    if len(text) != 71 or not text.startswith("sha256:"):
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>")
    try:
        int(text[7:], 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be sha256:<64 lowercase hex>") from exc
    if text.lower() != text:
        raise ValueError(f"{label} must use lowercase hex")
    return text


def _authority_none(value: Any) -> str:
    if value != "None":
        raise ValueError("authority_effect must be None")
    return "None"


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    """Return the single canonical JSON encoding used for V2 identities."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


@dataclass(frozen=True)
class SourceSpanV1:
    source_path: str
    start_byte: int
    end_byte: int
    source_digest: str
    content_digest: str

    def __post_init__(self) -> None:
        _text(self.source_path, "source_path")
        _integer(self.start_byte, "start_byte")
        _integer(self.end_byte, "end_byte", minimum=self.start_byte + 1)
        _sha256(self.source_digest, "source_digest")
        _sha256(self.content_digest, "content_digest")

    def verify(self, raw: bytes) -> None:
        if type(raw) is not bytes:
            raise TypeError("source bytes must be exact bytes")
        source_digest = f"sha256:{hashlib.sha256(raw).hexdigest()}"
        if source_digest != self.source_digest:
            raise ValueError("source span file digest mismatch")
        if self.end_byte > len(raw):
            raise ValueError("source span exceeds source bytes")
        content = raw[self.start_byte : self.end_byte]
        content_digest = f"sha256:{hashlib.sha256(content).hexdigest()}"
        if content_digest != self.content_digest:
            raise ValueError("source span content digest mismatch")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "start_byte": self.start_byte,
            "end_byte": self.end_byte,
            "source_digest": self.source_digest,
            "content_digest": self.content_digest,
        }


@dataclass(frozen=True)
class InstructionAtomBindingV1:
    atom_id: str
    skill_id: str
    section: str
    ordinal: int
    span: SourceSpanV1
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _text(self.atom_id, "atom_id")
        _text(self.skill_id, "skill_id")
        _text(self.section, "section")
        _integer(self.ordinal, "ordinal")
        if not isinstance(self.span, SourceSpanV1):
            raise TypeError("span must be SourceSpanV1")
        _authority_none(self.authority_effect)

    def to_dict(self) -> dict[str, Any]:
        return {
            "atom_id": self.atom_id,
            "skill_id": self.skill_id,
            "section": self.section,
            "ordinal": self.ordinal,
            "span": self.span.to_dict(),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class SkillLifecycleBindingV1:
    skill_id: str
    lifecycle_status: str
    source_role: str
    evaluation_receipt_refs: tuple[str, ...] = ()
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _text(self.skill_id, "skill_id")
        if self.lifecycle_status not in LIFECYCLE_STATES:
            raise ValueError("unsupported skill lifecycle status")
        if self.source_role not in SOURCE_ROLES:
            raise ValueError("unsupported skill source role")
        refs = _tuple_text(self.evaluation_receipt_refs, "evaluation_receipt_refs")
        for ref in refs:
            _sha256(ref, "evaluation_receipt_ref")
        object.__setattr__(self, "evaluation_receipt_refs", refs)
        _authority_none(self.authority_effect)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "lifecycle_status": self.lifecycle_status,
            "source_role": self.source_role,
            "evaluation_receipt_refs": list(self.evaluation_receipt_refs),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class SkillFamilyBindingV1:
    family_id: str
    skill_ids: tuple[str, ...]
    anti_skill_ids: tuple[str, ...] = ()
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _text(self.family_id, "family_id")
        object.__setattr__(self, "skill_ids", _tuple_text(self.skill_ids, "skill_ids"))
        object.__setattr__(
            self, "anti_skill_ids", _tuple_text(self.anti_skill_ids, "anti_skill_ids")
        )
        _authority_none(self.authority_effect)

    def to_dict(self) -> dict[str, Any]:
        return {
            "family_id": self.family_id,
            "skill_ids": list(self.skill_ids),
            "anti_skill_ids": list(self.anti_skill_ids),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class MetaSkillBindingV1:
    meta_skill_id: str
    selectable_operation_ids: tuple[str, ...]
    path2_evidence_refs: tuple[str, ...] = ()
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _text(self.meta_skill_id, "meta_skill_id")
        object.__setattr__(
            self,
            "selectable_operation_ids",
            _tuple_text(self.selectable_operation_ids, "selectable_operation_ids"),
        )
        refs = _tuple_text(self.path2_evidence_refs, "path2_evidence_refs")
        for ref in refs:
            _sha256(ref, "path2_evidence_ref")
        object.__setattr__(self, "path2_evidence_refs", refs)
        _authority_none(self.authority_effect)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta_skill_id": self.meta_skill_id,
            "selectable_operation_ids": list(self.selectable_operation_ids),
            "path2_evidence_refs": list(self.path2_evidence_refs),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class NodeAssignmentV1:
    workflow_id: str
    node_id: str
    operation_id: str
    agent_ids: tuple[str, ...]
    required_colours: tuple[str, ...]
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _text(self.workflow_id, "workflow_id")
        _text(self.node_id, "node_id")
        _text(self.operation_id, "operation_id")
        agents = _tuple_text(self.agent_ids, "agent_ids")
        if not agents:
            raise ValueError("node assignment requires at least one agent")
        object.__setattr__(self, "agent_ids", agents)
        object.__setattr__(
            self,
            "required_colours",
            _tuple_text(self.required_colours, "required_colours"),
        )
        _authority_none(self.authority_effect)

    @property
    def key(self) -> str:
        return f"{self.workflow_id}:{self.node_id}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "node_id": self.node_id,
            "operation_id": self.operation_id,
            "agent_ids": list(self.agent_ids),
            "required_colours": list(self.required_colours),
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class DeclaredSubstitutionBindingV1:
    """Digest-bearing witness for one validated operadic substitution."""

    outer_id: str
    slot: int
    inner_id: str
    normalized_term_id: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        _text(self.outer_id, "outer_id")
        _integer(self.slot, "slot")
        _text(self.inner_id, "inner_id")
        _sha256(self.normalized_term_id, "normalized_term_id")
        _authority_none(self.authority_effect)

    @property
    def key(self) -> tuple[str, int, str]:
        return (self.outer_id, self.slot, self.inner_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "outer_id": self.outer_id,
            "slot": self.slot,
            "inner_id": self.inner_id,
            "normalized_term_id": self.normalized_term_id,
            "authority_effect": self.authority_effect,
        }


@dataclass(frozen=True)
class EstateCatalogV2:
    """Derived V2 binding over an immutable V1 catalog."""

    catalog_id: str
    base_catalog: EstateCatalogSnapshotV1
    instruction_atoms: tuple[InstructionAtomBindingV1, ...]
    lifecycles: tuple[SkillLifecycleBindingV1, ...]
    families: tuple[SkillFamilyBindingV1, ...]
    meta_skills: tuple[MetaSkillBindingV1, ...]
    node_assignments: tuple[NodeAssignmentV1, ...]
    declared_substitutions: tuple[DeclaredSubstitutionBindingV1, ...]
    anti_skills: MappingProxyType[str, CatalogAntiSkillRefV1]
    source_manifest_digest: str = ""
    schema_version: str = SCHEMA_ESTATE_CATALOG_V2
    authority_effect: str = "None"
    catalog_digest: str = ""

    def __init__(
        self,
        *,
        catalog_id: str,
        base_catalog: EstateCatalogSnapshotV1,
        instruction_atoms: Sequence[InstructionAtomBindingV1],
        lifecycles: Sequence[SkillLifecycleBindingV1],
        families: Sequence[SkillFamilyBindingV1],
        meta_skills: Sequence[MetaSkillBindingV1],
        node_assignments: Sequence[NodeAssignmentV1],
        anti_skills: Mapping[str, CatalogAntiSkillRefV1],
        declared_substitutions: Sequence[DeclaredSubstitutionBindingV1] = (),
        source_manifest_digest: str = "",
        schema_version: str = SCHEMA_ESTATE_CATALOG_V2,
        authority_effect: str = "None",
        catalog_digest: str = "",
    ) -> None:
        _text(catalog_id, "catalog_id")
        if not isinstance(base_catalog, EstateCatalogSnapshotV1):
            raise TypeError("base_catalog must be EstateCatalogSnapshotV1")
        if schema_version != SCHEMA_ESTATE_CATALOG_V2:
            raise ValueError("unsupported estate catalog schema")
        _authority_none(authority_effect)
        object.__setattr__(self, "catalog_id", catalog_id)
        object.__setattr__(self, "base_catalog", base_catalog)
        object.__setattr__(self, "instruction_atoms", tuple(instruction_atoms))
        object.__setattr__(self, "lifecycles", tuple(lifecycles))
        object.__setattr__(self, "families", tuple(families))
        object.__setattr__(self, "meta_skills", tuple(meta_skills))
        object.__setattr__(self, "node_assignments", tuple(node_assignments))
        object.__setattr__(
            self, "declared_substitutions", tuple(declared_substitutions)
        )
        object.__setattr__(self, "anti_skills", MappingProxyType(dict(anti_skills)))
        if source_manifest_digest:
            _sha256(source_manifest_digest, "source_manifest_digest")
        object.__setattr__(self, "source_manifest_digest", source_manifest_digest)
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "authority_effect", "None")

        skill_ids = set(base_catalog.skills)
        for binding in self.lifecycles:
            if binding.skill_id not in skill_ids:
                raise ValueError(
                    f"lifecycle references unknown skill: {binding.skill_id}"
                )
            if (
                binding.lifecycle_status == "BOUND"
                and base_catalog.skills[binding.skill_id].operation.declaration_status
                != DECLARATION_STRICT_EXPLICIT
            ):
                raise ValueError(
                    "BOUND lifecycle requires a strict explicit operation declaration"
                )
        if len({item.skill_id for item in self.lifecycles}) != len(self.lifecycles):
            raise ValueError("duplicate lifecycle binding")
        if len({item.atom_id for item in self.instruction_atoms}) != len(
            self.instruction_atoms
        ):
            raise ValueError("duplicate instruction atom id")
        if len({item.key for item in self.node_assignments}) != len(
            self.node_assignments
        ):
            raise ValueError("duplicate node assignment")
        if len({item.key for item in self.declared_substitutions}) != len(
            self.declared_substitutions
        ):
            raise ValueError("duplicate declared substitution")
        bound_skill_ids = {
            item.skill_id
            for item in self.lifecycles
            if item.lifecycle_status == "BOUND"
        }
        for item in self.declared_substitutions:
            if (
                item.outer_id not in bound_skill_ids
                or item.inner_id not in bound_skill_ids
            ):
                raise ValueError(
                    "declared substitution must reference strictly BOUND operations"
                )
        for atom in self.instruction_atoms:
            if atom.skill_id not in skill_ids:
                raise ValueError(f"atom references unknown skill: {atom.skill_id}")
        for family in self.families:
            if not set(family.skill_ids).issubset(skill_ids):
                raise ValueError(f"family {family.family_id} references unknown skill")
        for key, ref in self.anti_skills.items():
            if key != ref.anti_skill_id:
                raise ValueError("anti-skill map key must equal anti_skill_id")

        payload = self._payload()
        computed = f"sha256:{hashlib.sha256(canonical_json_bytes(payload)).hexdigest()}"
        if catalog_digest and _sha256(catalog_digest, "catalog_digest") != computed:
            raise ValueError("catalog_digest does not match canonical catalog content")
        object.__setattr__(self, "catalog_digest", computed)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "catalog_id": self.catalog_id,
            "base_catalog": self.base_catalog.to_dict(),
            "instruction_atoms": [item.to_dict() for item in self.instruction_atoms],
            "lifecycles": [item.to_dict() for item in self.lifecycles],
            "families": [item.to_dict() for item in self.families],
            "meta_skills": [item.to_dict() for item in self.meta_skills],
            "node_assignments": [item.to_dict() for item in self.node_assignments],
            "declared_substitutions": [
                item.to_dict() for item in self.declared_substitutions
            ],
            "anti_skills": {
                key: value.to_dict() for key, value in sorted(self.anti_skills.items())
            },
            "source_manifest_digest": self.source_manifest_digest,
            "authority_effect": self.authority_effect,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self._payload(), "catalog_digest": self.catalog_digest}

    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_dict())

    def bound_operations(self) -> MappingProxyType[str, SkillOperationV1]:
        """Operations of BOUND lifecycles, keyed by skill id. Not a digest-bearing field."""

        bound: dict[str, SkillOperationV1] = {}
        for item in self.lifecycles:
            if item.lifecycle_status != "BOUND":
                continue
            bound[item.skill_id] = self.base_catalog.skills[item.skill_id].operation
        return MappingProxyType(bound)


__all__ = [
    "LIFECYCLE_STATES",
    "SCHEMA_ESTATE_CATALOG_V2",
    "SOURCE_ROLES",
    "DeclaredSubstitutionBindingV1",
    "EstateCatalogV2",
    "InstructionAtomBindingV1",
    "MetaSkillBindingV1",
    "NodeAssignmentV1",
    "SkillFamilyBindingV1",
    "SkillLifecycleBindingV1",
    "SourceSpanV1",
    "canonical_json_bytes",
]
