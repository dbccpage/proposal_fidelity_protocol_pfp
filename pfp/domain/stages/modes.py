"""Pydantic v2 models for PFP Modes (Modes 01 through 20).

Defines ModeFile, ModesManifest, ModeDefinition, ModeCluster, VerifierContract.
AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator


class AuthorityEffect(str, Enum):
    NONE = "None"


class ModeCluster(str, Enum):
    CLUSTER_I__CARRIER___REPRESENTATION = "Cluster I: Carrier & Representation"
    CLUSTER_II__INTERNAL_STEERING = "Cluster II: Internal Steering"
    CLUSTER_III__GROUP___COCHAIN_STRUCTURE = "Cluster III: Group & Cochain Structure"
    CLUSTER_IV__DIALECTICAL___ADVERSARIAL = "Cluster IV: Dialectical & Adversarial"
    CLUSTER_V__FOUNDATIONAL_MECHANIZATION = "Cluster V: Foundational Mechanization"


class VerifierContract(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    verifier_type: StrictStr = Field(min_length=1)
    fail_closed: StrictBool = True
    deterministic: StrictBool = True
    timeout_sec: StrictInt = Field(default=30, ge=1)


class ModeFile(BaseModel):
    """Canonical specification for one play mode (modes/mode_NN_*.yaml)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    mode_id: StrictInt = Field(ge=1, le=20)
    name: StrictStr = Field(min_length=1)
    cluster: ModeCluster
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    core_mechanism: StrictStr = Field(min_length=1)
    substrate: StrictStr = Field(min_length=1)
    paper_reference: StrictStr = Field(min_length=1)
    rules: List[StrictStr] = Field(default_factory=list)
    entry_preconditions: List[StrictStr] = Field(default_factory=list)
    winning_condition: StrictStr = Field(min_length=1)
    failure_modes: List[StrictStr] = Field(default_factory=list)
    verifier_contract: VerifierContract


class ModeClusterRef(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: StrictStr = Field(min_length=1)
    modes: List[StrictInt] = Field(min_length=1)


class ModeSummary(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    id: StrictInt = Field(ge=1, le=20)
    name: StrictStr = Field(min_length=1)
    cluster: StrictStr = Field(min_length=1)
    file: Optional[StrictStr] = None
    description: StrictStr = Field(default="")


class ModesManifest(BaseModel):
    """Manifest of all twenty canonical modes (modes/modes_manifest.yaml)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    manifest_version: StrictStr = Field(default="2.0.0")
    version: StrictStr = Field(default="2.0.0")
    title: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    mode_count: StrictInt = 20
    modes: List[ModeSummary]
    clusters: Dict[str, ModeClusterRef]

    @model_validator(mode="after")
    def validate_twenty_modes(self) -> ModesManifest:
        mode_ids = [m.id for m in self.modes]
        if mode_ids != list(range(1, 21)):
            raise ValueError(f"ModesManifest must contain modes 1..20, got {mode_ids}")
        all_cluster_mode_ids = sorted(
            [m_id for cluster in self.clusters.values() for m_id in cluster.modes]
        )
        if all_cluster_mode_ids != list(range(1, 21)):
            raise ValueError("Clusters do not partition modes 1..20 cleanly")
        return self
