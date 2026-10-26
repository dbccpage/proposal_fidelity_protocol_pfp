"""Pydantic v2 Models for Foundational Normal Form Definitions.

Formalizes the Quadrilateral Criterion of True Normal Forms, classical relational
dependency algebra, MSS-N grammar & math levels, Fermion Sign Problem (FSP)
normal forms, and Discrete Deformation Calculus (DDC) operational laws.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator


class PillarDefinition(BaseModel):
    """One of the four foundational pillars of a True Normal Form."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    pillar_index: Literal["I", "II", "III", "IV"]
    id: str
    name: str
    requirement: str
    formal_condition: str


class QuadrilateralCriterion(BaseModel):
    """The four inviolable criteria distinguishing True Normal Forms from procedural advice."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    summary: str
    pillars: list[PillarDefinition]

    @field_validator("pillars")
    @classmethod
    def validate_four_pillars(cls, v: list[PillarDefinition]) -> list[PillarDefinition]:
        indices = [p.pillar_index for p in v]
        if indices != ["I", "II", "III", "IV"]:
            raise ValueError(f"Pillars must be exactly [I, II, III, IV], got {indices}")
        return v


class RelationalConcept(BaseModel):
    """A formal definition in classical relational database theory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    formal_definition: str
    description: str


class DependencyAlgebraSection(BaseModel):
    """Mathematical concepts of dependencies, axioms, and keys."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    functional_dependency: RelationalConcept
    armstrongs_axioms: list[str]
    superkeys_and_candidate_keys: RelationalConcept
    prime_and_non_prime_attributes: RelationalConcept
    multivalued_dependency: RelationalConcept
    join_dependency: RelationalConcept
    reconstruction_theorems: dict[str, str]


class ClassicalSpectrumDefinition(BaseModel):
    """An entry in the classical relational normal form spectrum."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    short_name: str
    author: str
    year: int | None = None
    structural_invariant: str
    anomaly_excluded: str
    lossless_join_property: str
    dependency_preservation: str | None = None
    qualifies_as_true_normal_form: bool
    qualification_gap: str | None = None
    key_component_screen: str | None = None


class MssnLevelDefinition(BaseModel):
    """A discovered normal form across MSS-N grammar and math levels."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    short_name: str
    levels: str
    spec_files: list[str]
    anomaly_excluded: str
    preserved_invariant: str
    lossless_reconstruction: str
    claim_hygiene_note: str | None = None
    nomenclature_note: str | None = None


class FspNormalFormDefinition(BaseModel):
    """A Fermion Sign Problem (FSP) normal form specification."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    short_name: str
    domain: str
    transformation_group: str
    target_property: str
    anomaly_excluded: str
    necessary_and_sufficient_criterion: str
    reconstruction_theorem: str
    positive_witness: str
    negative_witness_obstruction: str


class DdcRuneDefinition(BaseModel):
    """An operational rune letter in the DDC alphabet."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    letter: str
    name: str
    description: str


class DdcOperationalNormalFormDefinition(BaseModel):
    """One of the 8 Discrete Deformation Calculus (DDC) operational normal forms."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_id: str
    short_name: str
    name: str
    family: str
    runes: list[str]
    target_runtime_law: str
    domain: str
    anomaly_excluded: str
    preserved_invariant: str
    reconstruction_theorem: str


class NormalFormFoundationalDefinitions(BaseModel):
    """Root model for foundational normal form definitions and theoretical specifications."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    definitions_id: Literal["coda.normal_form_foundational_definitions.v1"]
    status: Literal["CANONICAL_SPECIFICATION"]
    authority_effect: Literal["None"]
    treatise_title: str
    abstract: str
    governing_councils: list[str]
    quadrilateral_criterion: QuadrilateralCriterion
    relational_substrate: dict[str, RelationalConcept]
    dependency_algebra: DependencyAlgebraSection
    classical_spectrum: list[ClassicalSpectrumDefinition]
    mssn_levels_spectrum: list[MssnLevelDefinition]
    fsp_normal_forms: list[FspNormalFormDefinition]
    ddc_alphabet: list[DdcRuneDefinition]
    ddc_operational_normal_forms: list[DdcOperationalNormalFormDefinition]
    references: list[str]

    @field_validator("authority_effect")
    @classmethod
    def validate_authority(cls, v: str) -> str:
        if v != "None":
            raise ValueError("AuthorityEffect must strictly be 'None'")
        return v

    @classmethod
    def from_yaml_file(cls, path: Path | str) -> NormalFormFoundationalDefinitions:
        """Loads and validates NormalFormFoundationalDefinitions from a YAML file."""
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls.model_validate(data)


NormalFormFoundationalDefinitions.model_rebuild()
