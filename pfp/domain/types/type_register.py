"""PFP Type Register Metrics & Invariants (Census & World Definitions).

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import Field

from .base import AuthorityEffect, PfpBaseModel


class PfpModuleWorld(str, Enum):
    COLOCATED = "colocated"
    RUNTIME = "runtime"
    GENERATED = "generated"


class PfpModuleSource(str, Enum):
    PYDANTIC = "pydantic"
    YAML = "yaml"
    BOTH_PARITY_TESTED = "both_parity_tested"
    BOTH_UNCHECKED = "both_unchecked"


class PfpYamlRole(str, Enum):
    JSON_SCHEMA = "json_schema"
    GENERATED_JSON_SCHEMA = "generated_json_schema"
    CUSTOM_SCHEMA = "custom_schema"
    DATA = "data"


class PfpModuleStatus(str, Enum):
    CANONICAL = "canonical"
    REVIEW = "review"


class PfpYamlRef(PfpBaseModel):
    path: str = Field(min_length=1)
    role: PfpYamlRole


class PfpModuleRow(PfpBaseModel):
    path: str = Field(pattern=r"^[a-z0-9_/]+\.py$")
    world: PfpModuleWorld
    source: PfpModuleSource
    yaml: list[PfpYamlRef] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    status: PfpModuleStatus
    note: str | None = None


class PfpTypeRegister(PfpBaseModel):
    schema_: Literal["pfp.type-register.v1"] = Field(default="pfp.type-register.v1", alias="schema")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    modules: list[PfpModuleRow]
    name_collisions: list[dict[str, Any]] = Field(default_factory=list)
    overlaps: list[dict[str, Any]] = Field(default_factory=list)
    derived: list[dict[str, Any]] = Field(default_factory=list)


# Aliases
ModuleWorld = PfpModuleWorld
ModuleSource = PfpModuleSource
YamlRole = PfpYamlRole
ModuleStatus = PfpModuleStatus
YamlRef = PfpYamlRef
ModuleRow = PfpModuleRow
TypeRegister = PfpTypeRegister
