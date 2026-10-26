"""PFP Normal Forms Domain Index & Extended Form Contracts.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import AuthorityEffect, PfpBaseModel


class PfpNfFamily(str, Enum):
    CODA = "coda"
    EPISTEMIC = "epistemic"
    CHANGE = "change"
    COMPILATION = "compilation"
    REPRESENTATION = "representation"
    EVIDENCE = "evidence"
    EXPERIMENTAL = "experimental"


class PfpNfIndexEntry(PfpBaseModel):
    nf_id: str = Field(pattern=r"^nf\.[a-z]+\.[a-z_]+$")
    short_name: str = Field(min_length=1)
    name: str = Field(min_length=1)
    family: PfpNfFamily
    form_category: Literal["Extended Form Contract"] = "Extended Form Contract"
    qualifies_as_true_normal_form: Literal[False] = False
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpNfDomainIndex(PfpBaseModel):
    contracts: list[PfpNfIndexEntry] = Field(min_length=9, max_length=9)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpNormalFormContractIdentity(PfpBaseModel):
    id: str
    name: str
    short_name: str
    version: str
    theory_status: str
    contract_status: str
    verification_status: str
    family: str


class PfpNormalFormClassification(PfpBaseModel):
    hierarchy_level: str
    subject_kind: list[str] = Field(default_factory=list)
    data_posture: str
    mathematical_posture: str


class PfpNormalFormContract(PfpBaseModel):
    schema_version: str = "smplx.nf.contract_schema.v1"
    contract_kind: str
    identity: PfpNormalFormContractIdentity
    classification: PfpNormalFormClassification
    purpose: Any
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


# Aliases
NfFamily = PfpNfFamily
NfIndexEntry = PfpNfIndexEntry
NfDomainIndex = PfpNfDomainIndex
NormalFormContractIdentity = PfpNormalFormContractIdentity
NormalFormClassification = PfpNormalFormClassification
NormalFormContract = PfpNormalFormContract
