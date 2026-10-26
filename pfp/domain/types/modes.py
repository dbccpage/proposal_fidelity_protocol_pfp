"""PFP Play Modes Catalog & Specifications (20 Modes across 5 Clusters).

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from .base import AuthorityEffect, PfpBaseModel


class PfpModeCluster(str, Enum):
    CARRIER_REPRESENTATION = "Cluster I: Carrier & Representation"
    INTERNAL_STEERING = "Cluster II: Internal Steering"
    GROUP_COCHAIN_STRUCTURE = "Cluster III: Group & Cochain Structure"
    DIALECTICAL_ADVERSARIAL = "Cluster IV: Dialectical & Adversarial"
    FOUNDATIONAL_MECHANIZATION = "Cluster V: Foundational Mechanization"


class PfpModeCatalogEntry(PfpBaseModel):
    mode_id: int = Field(ge=1, le=20)
    name: str = Field(min_length=1)
    cluster: PfpModeCluster
    contract_path: str = Field(pattern=r"^mode_\d{2}_[a-z0-9_]+/contract\.yaml$")
    extra_specs: list[str] = Field(default_factory=list)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpModeCatalog(PfpBaseModel):
    entries: list[PfpModeCatalogEntry] = Field(min_length=20, max_length=20)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpVerifierContract(PfpBaseModel):
    verifier_type: str = Field(min_length=1)
    fail_closed: bool


class PfpModeFile(PfpBaseModel):
    mode_id: int = Field(ge=1, le=20)
    name: str = Field(min_length=1)
    cluster: PfpModeCluster
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    core_mechanism: str = Field(min_length=1)
    substrate: str = Field(min_length=1)
    paper_reference: str = Field(min_length=1)
    rules: list[str] = Field(default_factory=list)
    entry_preconditions: list[str] = Field(default_factory=list)
    winning_condition: str = Field(min_length=1)
    failure_modes: list[str] = Field(default_factory=list)
    verifier_contract: PfpVerifierContract


class PfpClusterEntry(PfpBaseModel):
    name: str
    modes: list[int] = Field(default_factory=list)


class PfpClusterIndex(PfpBaseModel):
    cluster_1_carrier_representation: PfpClusterEntry
    cluster_2_internal_steering: PfpClusterEntry
    cluster_3_group_cochain_structure: PfpClusterEntry
    cluster_4_dialectical_adversarial: PfpClusterEntry
    cluster_5_foundational_mechanization: PfpClusterEntry


class PfpManifestMode(PfpBaseModel):
    id: int = Field(ge=1, le=20)
    file: str = Field(min_length=1)


# Aliases
ModeCluster = PfpModeCluster
ModeCatalogEntry = PfpModeCatalogEntry
ModeCatalog = PfpModeCatalog
VerifierContract = PfpVerifierContract
ModeFile = PfpModeFile
ClusterEntry = PfpClusterEntry
ClusterIndex = PfpClusterIndex
ManifestMode = PfpManifestMode
