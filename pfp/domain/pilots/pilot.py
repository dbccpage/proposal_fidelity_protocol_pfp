"""Pydantic V2 Models for PFP Pilot Instances and Families.

AuthorityEffect: None.
Governing schema: pilots/pilot_models.yaml
"""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class ParameterAxis(_Frozen):
    name: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    values: Annotated[List[Any], Field(min_length=1)]


class PilotBudget(_Frozen):
    max_calls: Annotated[int, Field(ge=1)]
    max_cost_usd: Annotated[StrictStr, Field(pattern=r"^(0|[1-9][0-9]*)(\.[0-9]+)?(E[+-][0-9]+)?$")]
    per_call_reserve_usd: Annotated[StrictStr, Field(pattern=r"^(0|[1-9][0-9]*)(\.[0-9]+)?(E[+-][0-9]+)?$")]


class NoLlmPilotFamily(_Frozen):
    family_id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    subject: Literal[
        "prompt", "packet", "stage", "mode", "gate", "grammar",
        "receipt", "ledger", "level", "normal_form", "derivation", "swarm",
    ]
    description: Annotated[StrictStr, Field(min_length=1)]
    targets: Any
    axes: List[ParameterAxis] = Field(default_factory=list)
    expected_outcome: Literal["PASS", "FAIL"] = "PASS"
    max_instances: Annotated[int, Field(ge=1)]
    kind: Literal["NO_LLM"] = "NO_LLM"
    check_id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    authority_effect: Literal["None"] = "None"


class LlmPilotFamily(_Frozen):
    family_id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    subject: Literal[
        "prompt", "packet", "stage", "mode", "gate", "grammar",
        "receipt", "ledger", "level", "normal_form", "derivation", "swarm",
    ]
    description: Annotated[StrictStr, Field(min_length=1)]
    targets: Any
    axes: List[ParameterAxis] = Field(default_factory=list)
    expected_outcome: Literal["PASS", "FAIL"] = "PASS"
    max_instances: Annotated[int, Field(ge=1)]
    kind: Literal["LLM"] = "LLM"
    provider: Literal["openrouter"] = "openrouter"
    models: Annotated[List[Annotated[StrictStr, Field(min_length=1)]], Field(min_length=1)]
    response_check_id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    budget: PilotBudget
    authority_effect: Literal["None"] = "None"


class PilotInstance(_Frozen):
    pilot_id: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    family_id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    kind: Literal["LLM", "NO_LLM"]
    check_id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    target: Annotated[StrictStr, Field(min_length=1)]
    target_sha256: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    params: Dict[StrictStr, Any]
    model: Optional[Annotated[StrictStr, Field(min_length=1)]] = None
    expected_outcome: Literal["PASS", "FAIL"]


class PilotRun(_Frozen):
    pilot_id: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    family_id: Annotated[StrictStr, Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")]
    kind: Literal["LLM", "NO_LLM"]
    outcome: Literal["NOT_RUN", "COMPLETED", "REFUSED", "FAILED", "BUDGET_CENSORED"] = "NOT_RUN"
    cost_microusd: Annotated[StrictInt, Field(ge=0)] | None = None
    cost_basis: Literal["NOT_RUN", "METERED_ESTIMATE", "PROVIDER_REPORTED", "UNKNOWN"] = "NOT_RUN"
    evidence_refs: List[StrictStr] = Field(default_factory=list)


class PilotCatalog(_Frozen):
    schema_: Literal["pfp.pilot-catalog.v1"] = Field(alias="schema", default="pfp.pilot-catalog.v1")
    kind: Literal["LLM", "NO_LLM"]
    authority_effect: Literal["None"] = "None"
    families: Annotated[List[Any], Field(min_length=1)]


__all__ = [
    "LlmPilotFamily",
    "NoLlmPilotFamily",
    "ParameterAxis",
    "PilotBudget",
    "PilotCatalog",
    "PilotInstance",
    "PilotRun",
]
