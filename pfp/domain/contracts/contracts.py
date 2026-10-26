"""Pydantic v2 models for PFP Machine-Verifiable Contracts.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr


class Precondition(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: StrictStr = Field(min_length=1)
    description: StrictStr = Field(default="")
    predicate: StrictStr = Field(min_length=1)


class Postcondition(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: StrictStr = Field(min_length=1)
    description: StrictStr = Field(default="")
    predicate: StrictStr = Field(min_length=1)


class InvariantCheck(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: StrictStr = Field(min_length=1)
    description: StrictStr = Field(default="")
    is_satisfied: StrictBool = True
    evidence: Optional[StrictStr] = None


class ContractSpec(BaseModel):
    """Specification of an operational or mathematical contract."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    contract_id: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    version: StrictStr = Field(default="1.0.0")
    authority_effect: StrictStr = Field(default="None")
    entry_preconditions: List[Precondition] = Field(default_factory=list)
    exit_postconditions: List[Postcondition] = Field(default_factory=list)
    invariants: List[StrictStr] = Field(default_factory=list)
    winning_condition: StrictStr = Field(min_length=1)
    failure_modes: List[StrictStr] = Field(default_factory=list)


class ContractAuditReceipt(BaseModel):
    """Receipt emitted after validating candidate execution against a contract."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    contract_id: StrictStr = Field(min_length=1)
    is_compliant: StrictBool
    violations: List[StrictStr] = Field(default_factory=list)
    invariants_verified: List[InvariantCheck] = Field(default_factory=list)
    authority_effect: StrictStr = Field(default="None")
