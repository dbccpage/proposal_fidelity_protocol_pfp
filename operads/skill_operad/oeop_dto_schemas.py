"""OEOP DTO schema models; existing WAS wire names and schemas are retained.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class WASDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class WASRoleProfile(WASDTO):
    id: str
    actor_kind: str
    maximum_mode: str


class WASRolePlanDTO(WASDTO):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    schema_uri: str = Field(
        alias="schema", default="anomalon.agent-system.a01.role-plan.v1"
    )
    proposal_only: Optional[bool] = None
    admitted: Optional[bool] = None
    active_profiles: List[WASRoleProfile] = Field(default_factory=list)
    planned_profiles: List[WASRoleProfile] = Field(default_factory=list)
    residual: Optional[str] = "Admitted: WAS V1 Role Plan DTO Schema"

    @model_validator(mode="after")
    def active_profile_ids_are_unique(self) -> "WASRolePlanDTO":
        ids = [profile.id for profile in self.active_profiles]
        if len(ids) != len(set(ids)):
            raise ValueError("active profile IDs must be unique")
        return self


class WASLifecyclePlanDTO(WASDTO):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    schema_uri: str = Field(
        alias="schema", default="anomalon.agent-system.a01.lifecycle-plan.v1"
    )
    proposal_only: Optional[bool] = None
    admitted: Optional[bool] = None
    planned_states: List[str] = Field(
        default_factory=lambda: ["Draft", "Canary", "Active", "Deprecated", "Quarantined", "Retired"]
    )
    automatic_discovery_rule: str = "Active plus explicitly allowlisted Canary only"
    current_automatic_discovery_allowlist: List[str] = Field(
        default_factory=lambda: ["Active"]
    )


class WASProviderSpec(WASDTO):
    id: str
    automatic_agent_root: Optional[str] = None
    automatic_skill_root: Optional[str] = None
    automatic_rule_root: Optional[str] = None
    automatic_workflow_root: Optional[str] = None
    configuration_is_enforcement: bool = False
    mutation_projection: str = "admitted-read-only"


class WASProviderObservationDTO(WASDTO):
    schema_uri: Literal["anomalon.agent-system.a01.provider-observation.v1"] = Field(
        alias="schema", default="anomalon.agent-system.a01.provider-observation.v1"
    )
    proposal_only: Literal[False] = False
    admitted: Literal[True] = True
    support_scale: List[str] = Field(
        default_factory=lambda: ["Enforced", "ExternallyEnforced", "AdvisoryOnly", "Unsupported"]
    )
    providers: List[WASProviderSpec] = Field(default_factory=list)
