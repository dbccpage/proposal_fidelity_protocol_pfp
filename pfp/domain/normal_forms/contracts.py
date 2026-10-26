"""Pydantic v2 models for S(n) and PFP Normal Forms.

Defines NormalFormContract, Identity, Purpose, ValidationCriteria, and TerminalRoutes.
AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr


class NFIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: StrictStr = Field(min_length=1)
    name: StrictStr = Field(min_length=1)
    short_name: StrictStr = Field(min_length=1)
    version: StrictStr = Field(default="v0")
    status: StrictStr = Field(default="draft")
    family: StrictStr = Field(default="coda")
    theory_status: StrictStr = Field(default="established")
    contract_status: StrictStr = Field(default="draft")
    verification_status: StrictStr = Field(default="executable")
    alias_of: Optional[StrictStr] = None
    deprecation_note: Optional[StrictStr] = None


class NFPurpose(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    excludes_anomaly: StrictStr = Field(min_length=1)
    preserves_invariant: StrictStr = Field(min_length=1)
    protected_skeleton: List[StrictStr] = Field(default_factory=list)
    erased_structure: List[StrictStr] = Field(default_factory=list)
    non_claims: List[StrictStr] = Field(default_factory=list)


class NFClassification(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    hierarchy_level: StrictStr = Field(default="normal_form")
    subject_kind: List[StrictStr] = Field(default_factory=list)
    data_posture: StrictStr = Field(default="in_transformation")
    mathematical_posture: StrictStr = Field(default="operational")


class ProofObligation(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: StrictStr = Field(min_length=1)
    status: StrictStr = Field(default="upstream_theorem")
    ref: StrictStr = Field(default="")
    section: StrictStr = Field(default="")


class NormalFormContract(BaseModel):
    """Canonical normal form contract schema (normal_forms/nf.*.yaml)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    schema_version: StrictStr = Field(default="smplx.nf.contract.v0")
    schema_ref: Optional[StrictStr] = None
    contract_kind: StrictStr = Field(default="normal_form_contract")
    identity: NFIdentity
    classification: NFClassification
    purpose: NFPurpose
    quadrilateral: Optional[Dict[str, Any]] = None
    declarations_required: List[Union[StrictStr, Dict[str, Any]]] = Field(default_factory=list)
    evidence_required: List[Union[StrictStr, Dict[str, Any]]] = Field(default_factory=list)
    validation_criteria: List[Union[StrictStr, Dict[str, Any]]] = Field(default_factory=list)
    proof_obligations: List[Union[ProofObligation, Dict[str, Any], StrictStr]] = Field(default_factory=list)
    terminal_routes: List[Union[StrictStr, Dict[str, Any]]] = Field(default_factory=list)
    terminal_route_map: Optional[Dict[str, Any]] = None
    certification: Optional[Dict[str, Any]] = None
    authorization: Optional[Dict[str, Any]] = None
    failure_modes: Optional[List[Dict[str, Any]]] = None
    examples: Optional[List[Dict[str, Any]]] = None
    references: Optional[List[StrictStr]] = None


class NormalFormVerificationReceipt(BaseModel):
    """Receipt emitted when an artifact is verified against a NormalFormContract."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    normal_form_id: StrictStr = Field(min_length=1)
    is_confluent: StrictBool
    is_in_normal_form: StrictBool
    chase_steps_count: int = Field(ge=0)
    terminal_route: StrictStr = Field(min_length=1)
    defects_remaining: int = Field(ge=0)
    authority_effect: StrictStr = Field(default="None")
