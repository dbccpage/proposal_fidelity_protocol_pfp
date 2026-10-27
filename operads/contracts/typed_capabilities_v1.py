"""Strict wire adapters; execution and admission remain separate host decisions."""

from __future__ import annotations

import hashlib
import json
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from ..domain.anti_skills.anti_skill_v2 import PredicateAtomV1, PredicateExpressionV1
from ..domain.anti_skills.json_wire import loads_strict_json
from ..domain.capability_catalog_v1 import ResourceRefV1

PROFILE = "oewas.sorted-ascii-json.v1"
SCHEMA = "oewas.typed-capability.v1"
ROOT = "operads/catalog/contracts/v1"
Identifier = Annotated[str, Field(pattern=r"^[a-z][a-z0-9-]{0,63}$")]
Colour = Literal[
    "Audit", "Code", "Contract", "Diagram", "Ledger", "Paper", "Post", "Proof", "Receipt", "State"
]
WireType = Literal["anti_skill_subject", "anti_skill_hits", "typed_audit_receipt", "code_text"]
Text = Annotated[str, Field(min_length=1, max_length=4096)]


def canonical_bytes(value: object) -> bytes:
    """A named repository profile, deliberately not an RFC 8785 claim."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def digest_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class StrictWire(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", frozen=True)


class RepositoryResourceWireV1(StrictWire):
    path: str
    sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    byte_length: Annotated[int, Field(ge=1, le=131072)]

    def to_domain(self) -> ResourceRefV1:
        return ResourceRefV1(self.path, self.sha256, self.byte_length)

    @model_validator(mode="after")
    def confined_resource(self):
        self.to_domain()
        return self


class ResourceWireV1(RepositoryResourceWireV1):
    @model_validator(mode="after")
    def canonical_resource(self):
        if not self.path.startswith(ROOT + "/"):
            raise ValueError("resource must remain inside canonical contracts/v1")
        return self


class PortWireV1(StrictWire):
    name: Identifier
    colour: Colour
    wire_type: WireType

    @model_validator(mode="after")
    def consistent_wire_colour(self):
        expected = {
            "anti_skill_subject": "Contract",
            "anti_skill_hits": "Audit",
            "typed_audit_receipt": "Receipt",
            "code_text": "Code",
        }
        if self.colour != expected[self.wire_type]:
            raise ValueError("wire type and colour differ")
        return self


class PredicateAtomWireV1(StrictWire):
    operator: Literal["NOT_SUBSET_FIELDS"]
    fields: tuple[Literal["claim_scope"], Literal["evidence_scope"]]
    values: tuple[()]

    def to_domain(self) -> PredicateAtomV1:
        return PredicateAtomV1(self.operator, self.fields, self.values)

    @model_validator(mode="after")
    def existing_predicate_contract(self):
        self.to_domain()
        return self


class PredicateWireV1(StrictWire):
    mode: Literal["ALL"]
    atoms: tuple[PredicateAtomWireV1]

    def to_domain(self) -> PredicateExpressionV1:
        return PredicateExpressionV1(self.mode, tuple(atom.to_domain() for atom in self.atoms))


class CapabilityWireV1(StrictWire):
    schema_version: Literal["oewas.typed-capability.v1"]
    skill_id: Identifier
    description: Annotated[str, Field(min_length=1, max_length=1024)]
    inputs: Annotated[tuple[PortWireV1, ...], Field(min_length=1, max_length=8)]
    output: PortWireV1
    instruction: ResourceWireV1
    dependencies: Annotated[tuple[Identifier, ...], Field(max_length=8)]
    effects: tuple[Literal["read_subject", "emit_finding"], ...]
    authority_effect: Literal["None"]
    admission: Literal["Unadmitted"]

    @model_validator(mode="after")
    def normalized_contract(self):
        if self.description != self.description.strip():
            raise ValueError("description must be normalized")
        if len({p.name for p in self.inputs}) != len(self.inputs):
            raise ValueError("input names must be unique")
        if self.dependencies != tuple(sorted(set(self.dependencies))):
            raise ValueError("dependencies must be sorted and unique")
        if self.effects != ("read_subject", "emit_finding"):
            raise ValueError("this version permits only read_subject then emit_finding")
        return self


class SkillWireV1(CapabilityWireV1):
    kind: Literal["skill"]
    binding: Literal["adversary.claim_audit.v1"]
    guard: Identifier


class AntiSkillWireV1(CapabilityWireV1):
    kind: Literal["anti_skill"]
    binding: Literal["anti_skill.scope_subset.v1"]
    trigger: Literal["PRE_SEAL"]
    enforcement: Literal["FINDING"]
    predicate: PredicateWireV1
    fixtures: ResourceWireV1


class DigestedLessonWireV1(StrictWire):
    """Existing lesson concepts, with an exact source resource instead of a loose path."""

    source: RepositoryResourceWireV1
    source_revision: Text
    evidence_excerpt: Text
    failed_claim: Text
    counterexample: Text
    cause: Text
    correction: Text
    verification: Text
    applicability: Text
    exceptions: Text


class DigestedGuidanceWireV1(CapabilityWireV1):
    binding: Literal["adversary.digested_guidance.v1"]
    lesson: DigestedLessonWireV1


class RuleWireV1(DigestedGuidanceWireV1):
    kind: Literal["rule"]
    trigger: Text
    predicate: Text
    response: Text


class HelpfulPatternWireV1(DigestedGuidanceWireV1):
    kind: Literal["helpful_pattern"]
    conditions: Text
    construction: Text
    example: Text


class AntiPatternWireV1(DigestedGuidanceWireV1):
    kind: Literal["anti_pattern"]
    failure: Text
    witness: Text
    repair: Text


class AntibodyWireV1(DigestedGuidanceWireV1):
    kind: Literal["antibody"]
    antibody_id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]{0,127}$")]
    pharmacy_status: Literal["candidate"]
    prompt: RepositoryResourceWireV1
    prompt_uri: Text
    signal1_epitope: Text
    signal2_required_danger: Text
    harmful_example: Text
    benign_example: Text

    @model_validator(mode="after")
    def existing_prompt_address(self):
        from ..domain.prompt_hierarchy.models import PromptUri

        PromptUri.parse(self.prompt_uri)
        return self


TypedCapabilityV1 = Annotated[
    Union[
        SkillWireV1,
        AntiSkillWireV1,
        RuleWireV1,
        HelpfulPatternWireV1,
        AntiPatternWireV1,
        AntibodyWireV1,
    ],
    Field(discriminator="kind"),
]
ADAPTER = TypeAdapter(TypedCapabilityV1)


def parse_typed_capability(
    raw: bytes,
) -> (
    SkillWireV1
    | AntiSkillWireV1
    | RuleWireV1
    | HelpfulPatternWireV1
    | AntiPatternWireV1
    | AntibodyWireV1
):
    if type(raw) is not bytes or not 0 < len(raw) <= 131072 or raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("bounded BOM-free UTF-8 contract bytes required")
    decoded = loads_strict_json(raw.decode("utf-8"))
    if canonical_bytes(decoded) != raw:
        raise ValueError("contract does not use " + PROFILE)
    return ADAPTER.validate_json(raw, strict=True)


def contract_json_schema() -> dict:
    return ADAPTER.json_schema()
