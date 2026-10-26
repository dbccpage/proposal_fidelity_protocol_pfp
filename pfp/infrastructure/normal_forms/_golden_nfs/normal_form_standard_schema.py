"""Pydantic v2 Schema for the Normal Form Standard (coda.normal_form_standard.v1).

Validates the Four-Pillar Relational Schema Profile, classical spectrum,
reconstruction targets, terminal route mappings, and anti-slop documentation lints.

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


class ProfileDefinition(BaseModel):
    """Profile definition within the standard."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    scope: str
    description: str


class DecisionStatusSemantics(BaseModel):
    """Semantics for evaluation decisions under resource limits."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    budget_unknown_policy: str


class Pillar(BaseModel):
    """One of the four foundational pillars of a True Normal Form."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: Literal[
        "anomaly_exclusion",
        "lossless_join",
        "dependency_preservation",
        "syntactic_decision",
    ]
    name: str
    requirement: str


class DocumentAuthorizationRules(BaseModel):
    """Authorization invariants for contract validation."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    certified_implies_authorized: bool = Field(default=False)

    @field_validator("certified_implies_authorized")
    @classmethod
    def must_be_false(cls, v: bool) -> bool:
        if v is not False:
            raise ValueError("certified_implies_authorized must strictly be False")
        return v


class DocumentShape(BaseModel):
    """Structural layout rules required for contract documents."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str
    contract_kinds: list[str]
    identity_required: list[str]
    purpose_required: list[str]
    quadrilateral_required: list[str]
    pillar_fields: list[str]
    authorization: DocumentAuthorizationRules
    terminal_route_mapping_rule: str


class UniquenessRules(BaseModel):
    """Uniqueness rules for contract identity and filenames."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id_matches_filename: bool = True
    one_file_per_id: bool = True


class KeyComponentScreen(BaseModel):
    """Notes or rules on candidate key component screening."""

    model_config = ConfigDict(frozen=True, extra="allow")

    note: str


class SpectrumItem(BaseModel):
    """An entry in the classical or extended normal form spectrum."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    short_name: str
    author: str
    year: int | None = None
    mathematical_normal_form: bool
    qualifies_as_true_normal_form: bool
    qualification_gap: str | None = None
    invariant: str
    anomaly: str
    reconstruction: str
    dependency_preservation: str | None = None
    key_component_screen: KeyComponentScreen | None = None
    binary_fact_shape_defines_membership: bool | None = None
    syntactic_decision: str | None = None
    decidable_subclass_fence: str | None = None
    unrestricted_first_order_status: str | None = None


class ExtendedFormItem(BaseModel):
    """Extended normal form or operational form defined by the source."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    short_name: str
    status: str | None = None
    alias_of: str | None = None


class DocumentationLint(BaseModel):
    """Lint expectation for documentation and specification conformance."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    qualifies_as_true_normal_form: bool | None = None
    formal_statement_contains: list[str] | None = None
    fields: dict[str, Any] | None = None


class NormalFormStandard(BaseModel):
    """Root model for coda.normal_form_standard.v1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    standard_id: Literal["coda.normal_form_standard.v1"]
    source: str
    authority_effect: Literal["None"]
    summary: str
    profile: ProfileDefinition
    reconstruction_targets: list[str]
    decision_subjects: list[str]
    decision_modes: list[str]
    decision_status_semantics: DecisionStatusSemantics
    pillars: list[Pillar]
    true_normal_form_reconstruction_statuses: list[str]
    document: DocumentShape
    canonical_terminals: list[str]
    uniqueness: UniquenessRules
    spectrum: list[SpectrumItem]
    extended_forms_defined_by_the_source: list[ExtendedFormItem]
    named_in_the_source_without_a_definition: list[str]
    documentation_lints: list[DocumentationLint]
    membership_checks: list[DocumentationLint] | None = None

    @field_validator("authority_effect")
    @classmethod
    def validate_authority_effect(cls, v: str) -> str:
        if v != "None":
            raise ValueError(f"AuthorityEffect must be 'None', got '{v}'")
        return v

    @field_validator("canonical_terminals")
    @classmethod
    def validate_canonical_terminals(cls, v: list[str]) -> list[str]:
        term_set = set(v)
        diff = term_set - CANONICAL_TERMINALS
        if diff:
            raise ValueError(f"Unknown canonical terminals: {diff}")
        return v

    @model_validator(mode="after")
    def validate_four_pillars(self) -> NormalFormStandard:
        pillar_ids = {p.id for p in self.pillars}
        expected = {
            "anomaly_exclusion",
            "lossless_join",
            "dependency_preservation",
            "syntactic_decision",
        }
        if pillar_ids != expected:
            raise ValueError(
                f"Standard must declare exactly the 4 pillars. Missing: {expected - pillar_ids}"
            )
        return self

    @classmethod
    def from_yaml_file(cls, path: Path | str) -> NormalFormStandard:
        """Loads and validates a NormalFormStandard from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)


NormalFormStandard.model_rebuild()
