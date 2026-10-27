"""Explicit registered recipe data, never executable DDC code or borrowed truth."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator

from .ddc_program import DdcProgramBinding


class _Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class BoundReuseFile(_Closed):
    path: StrictStr = Field(min_length=1, max_length=4096)
    sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")


class BoundReuseTask(_Closed):
    seed: StrictStr = Field(min_length=1, max_length=65536)
    premises: dict[StrictStr, Any]
    contract: BoundReuseFile


class BoundReuseChecker(_Closed):
    checker_id: StrictStr = Field(min_length=1, max_length=128)
    sources: tuple[BoundReuseFile, ...] = Field(min_length=1, max_length=32)


class RegisteredDdcRecipe(_Closed):
    """One exact source/target registration; only the literal seed may change."""

    recipe_id: StrictStr = Field(pattern=r"^[A-Za-z_][A-Za-z_0-9.-]{0,95}$")
    program_path: StrictStr = Field(min_length=1, max_length=4096)
    program_binding: DdcProgramBinding
    source_task: BoundReuseTask
    target_task: BoundReuseTask
    source_candidate: BoundReuseFile
    checker: BoundReuseChecker
    rule: dict[StrictStr, Any]
    rule_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    part_match: dict[StrictStr, StrictStr]
    link_match: dict[StrictStr, StrictStr]
    fuel: StrictInt = Field(ge=1, le=1024)


class CheckedReuseRegistry(_Closed):
    schema_version: Literal["core.adversary.checked-reuse-registry.v1"]
    recipes: tuple[RegisteredDdcRecipe, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def unique_recipe_ids(self):
        if len({recipe.recipe_id for recipe in self.recipes}) != len(self.recipes):
            raise ValueError("DUPLICATE_RECIPE_ID")
        return self


class FreshReuseCheck(_Closed):
    """Bound observation returned by the operator-selected host checker."""

    checker_id: StrictStr = Field(min_length=1, max_length=128)
    accepted: StrictBool
    outcome: Literal["ACCEPTED", "QUERY_USER_MORE_INFO"]
    missing_fields: tuple[StrictStr, ...] = ()
    candidate_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    seed_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    premises_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    contract_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    checker_source_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    output_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def explicit_residual(self):
        if not self.accepted:
            raise ValueError("FRESH_CHECK_NOT_ACCEPTED")
        if self.outcome == "QUERY_USER_MORE_INFO":
            if (not self.missing_fields or len(set(self.missing_fields)) != len(self.missing_fields)
                    or any(not item.strip() or item != item.strip() for item in self.missing_fields)):
                raise ValueError("MISSING_FIELDS_REQUIRED")
        elif self.missing_fields:
            raise ValueError("ACCEPTED_WITH_MISSING_FIELDS")
        return self


class CheckedReuseResult(_Closed):
    recipe_id: StrictStr
    registry_sha256: StrictStr
    source_candidate_sha256: StrictStr
    target_candidate_sha256: StrictStr
    output_path: StrictStr
    native_source_id: StrictStr
    semantic_ddc_root: StrictStr
    operation: dict[StrictStr, Any]
    source_check: FreshReuseCheck
    target_check: FreshReuseCheck
    outcome: Literal["ACCEPTED", "QUERY_USER_MORE_INFO"]
    mathematical_acceptance: Literal["HOST_CHECKED", "NOT_SOLVED"]
    provider_calls: Literal[0] = 0
    authority_effect: Literal["None"] = "None"
    automatic_default_lookup: Literal[False] = False
