"""Pydantic v2 Schema for Normal Form Contracts and Contract Meta-Schema.

Models both:
1. NormalFormContract: An individual contract instance (smplx.nf.contract.v0 / v1).
2. NormalFormContractMetaSchema: The contract meta-schema (smplx.nf.contract_schema.v1).

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

CANONICAL_TERMINALS: frozenset[str] = frozenset(
    {
        "Preserve",
        "Repair",
        "Invalidate",
        "Recompute",
        "Serialize",
        "Lift",
        "Escalate",
        "Unsupported",
        "ClosureFailure",
        "BudgetUnknown",
        "ConservativeInvalidate",
        "Quarantine",
        "Decompose",
        "Refuse",
        "Reject",
        "Abstain",
    }
)

ContractKind = Literal[
    "normal_form_contract",
    "genesis_contract",
    "bridge_contract",
    "form_contract",
    "transformation_contract",
    "authority_contract",
    "evidence_contract",
]

ContractFamily = Literal[
    "genesis",
    "bridge",
    "shape",
    "change",
    "evidence",
    "epistemic",
    "motion",
    "relativistic",
    "representation",
    "transport",
    "compilation",
    "authority",
    "experimental",
    "derivation",
    "topology",
    "physics",
    "recursion",
    "query",
    "runtime",
    "security",
    "classical",
    "coda",
    "fsp",
    "cochain",
    "cohomology",
    "logic",
]

HierarchyLevel = Literal[
    "genesis_form",
    "bridge_form",
    "form",
    "normal_form",
    "certified_normal_form",
    "authorized_normal_form",
    "transformation_contract",
    "authority_contract",
]


# =============================================================================
# 1. Normal Form Contract Instance Models (smplx.nf.contract.v0 / v1)
# =============================================================================


class ContractIdentity(BaseModel):
    """Identity block identifying the contract."""

    model_config = ConfigDict(frozen=True, extra="allow")

    id: str
    name: str
    short_name: str
    version: str
    theory_status: Literal["established", "proposed", "experimental"] | None = None
    contract_status: Literal["draft", "active", "deprecated"] | None = None
    status: Literal["draft", "active", "deprecated"] | None = None
    verification_status: Literal["absent", "executable", "machine_checked"] | None = None
    family: ContractFamily


class ContractClassification(BaseModel):
    """Classification block defining hierarchy, subject, and postures."""

    model_config = ConfigDict(frozen=True, extra="allow")

    hierarchy_level: HierarchyLevel
    subject_kind: list[str]
    data_posture: Literal["at_rest", "in_motion", "in_transformation"]
    mathematical_posture: Literal["operational", "formal_algebraic", "verified_mechanized"]


class ContractPurpose(BaseModel):
    """Purpose block defining anomaly exclusion, invariants, and non-claims."""

    model_config = ConfigDict(frozen=True, extra="allow")

    excludes_anomaly: str
    preserves_invariant: str
    protected_skeleton: list[str] = Field(default_factory=list)
    erased_structure: list[str] = Field(default_factory=list)
    non_claims: list[str] = Field(default_factory=list)


class ObstructionSubstrate(BaseModel):
    """Finite obstruction substrate specification."""

    model_config = ConfigDict(frozen=True, extra="allow")

    policy_ref: str | None = None
    finite_carrier: dict[str, Any] | None = None
    cochain_complex: dict[str, Any] | None = None
    obstruction_class: dict[str, Any] | None = None
    carrier_realization: dict[str, Any] | None = None
    geometry_module: str | None = None
    gauge_metric_selector: str | None = None


class CertificationSection(BaseModel):
    """Certification requirements and verifier expectations."""

    model_config = ConfigDict(frozen=True, extra="allow")

    certificate_required: bool = False
    certificate_kind: str | None = None
    obstruction_class_required: bool = False
    loss_ledger_required: Literal["true", "false", "conditional"] | bool = False
    loss_ledger_trigger_id: str | None = None
    verifier_required: bool = False


class AuthorizationSection(BaseModel):
    """Authorization boundaries and load-bearing invariant."""

    model_config = ConfigDict(frozen=True, extra="allow")

    authorized_by: str | None = None
    certified_implies_authorized: bool = Field(default=False)

    @field_validator("certified_implies_authorized")
    @classmethod
    def must_be_false(cls, v: bool) -> bool:
        if v is not False:
            raise ValueError("certified_implies_authorized must strictly be False")
        return v


class NormalFormContract(BaseModel):
    """Root model for an individual Simplex Normal Form contract document."""

    model_config = ConfigDict(frozen=True, extra="allow")

    schema_version: str = Field(default="smplx.nf.contract.v0")
    schema_ref: str | None = None
    contract_kind: ContractKind = Field(default="normal_form_contract")
    identity: ContractIdentity
    classification: ContractClassification
    purpose: ContractPurpose
    obstruction_substrate: ObstructionSubstrate | None = None
    declarations_required: list[Any] = Field(default_factory=list)
    evidence_required: list[Any] = Field(default_factory=list)
    validation_criteria: list[Any] = Field(default_factory=list)
    proof_obligations: list[Any] = Field(default_factory=list)
    terminal_routes: list[str] = Field(default_factory=list)
    terminal_route_map: dict[str, str] = Field(default_factory=dict)
    certification: CertificationSection = Field(default_factory=CertificationSection)
    authorization: AuthorizationSection = Field(default_factory=AuthorizationSection)
    failure_modes: list[Any] = Field(default_factory=list)
    examples: list[Any] = Field(default_factory=list)
    references: list[Any] = Field(default_factory=list)
    definition: dict[str, Any] | None = None

    @field_validator("terminal_route_map")
    @classmethod
    def validate_terminal_route_map(cls, v: dict[str, str]) -> dict[str, str]:
        for local_route, target in v.items():
            if target not in CANONICAL_TERMINALS:
                raise ValueError(
                    f"Terminal route '{local_route}' maps to '{target}', "
                    f"which is not a canonical terminal in {sorted(CANONICAL_TERMINALS)}"
                )
        return v

    @model_validator(mode="after")
    def validate_protected_nf_checklist(self) -> NormalFormContract:
        """Enforces the Protected NF Checklist (anti-slop rule)."""
        is_nf = self.classification.hierarchy_level in {
            "normal_form",
            "certified_normal_form",
            "authorized_normal_form",
        }
        if is_nf:
            # 1. Must exclude an anomaly
            anomaly = self.purpose.excludes_anomaly.strip()
            if not anomaly or anomaly.lower() in ("none", "n/a", "not applicable"):
                raise ValueError(
                    f"Contract '{self.identity.id}' has hierarchy_level '{self.classification.hierarchy_level}' "
                    "but excludes no non-trivial anomaly. Non-reducing carriers must use form or genesis_form."
                )

            # 2. Must declare non-empty non_claims
            if not self.purpose.non_claims:
                raise ValueError(
                    f"Contract '{self.identity.id}' must declare non-empty purpose.non_claims."
                )

            # 3. Must have terminal routes mapped
            if not self.terminal_routes or not self.terminal_route_map:
                raise ValueError(
                    f"Contract '{self.identity.id}' must declare terminal_routes and a terminal_route_map."
                )
        return self

    @classmethod
    def from_yaml_file(cls, path: Path | str) -> NormalFormContract:
        """Loads and validates a NormalFormContract from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)


# =============================================================================
# 2. Meta-Schema Models (smplx.nf.contract_schema.v1)
# =============================================================================


class TriggerDefinition(BaseModel):
    """Loss ledger trigger entry in the schema registry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    description: str


class ProtectedNfChecklistDef(BaseModel):
    """Checklist rule defining normal form vs form qualification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    rule: str


class EnumFieldSpec(BaseModel):
    """Specification for an enumerated field in the metaschema."""

    model_config = ConfigDict(frozen=True, extra="allow")

    enum: list[str]


class NormalFormContractMetaSchema(BaseModel):
    """Root model validating the contract meta-schema document (normal_form_contract_schema.yaml)."""

    model_config = ConfigDict(frozen=True, extra="allow")

    schema_version: Literal["smplx.nf.contract_schema.v1"]
    description: str
    required_top_level_sections: list[str]
    contract_kinds: EnumFieldSpec
    section_definitions: dict[str, Any]
    canonical_terminals: EnumFieldSpec
    loss_ledger_trigger_registry: dict[str, TriggerDefinition]
    protected_nf_checklist: ProtectedNfChecklistDef

    @field_validator("canonical_terminals")
    @classmethod
    def validate_canonical_terminals(cls, v: EnumFieldSpec) -> EnumFieldSpec:
        terms = set(v.enum)
        diff = terms - CANONICAL_TERMINALS
        if diff:
            raise ValueError(f"Meta-schema has unknown canonical terminals: {diff}")
        return v

    @classmethod
    def from_yaml_file(cls, path: Path | str) -> NormalFormContractMetaSchema:
        """Loads and validates a NormalFormContractMetaSchema from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)


NormalFormContract.model_rebuild()
NormalFormContractMetaSchema.model_rebuild()
