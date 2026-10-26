"""Typed register of every PFP data type, plus the census that keeps it complete.

AuthorityEffect: None.

A *type* here is a Pydantic model or an ``Enum`` subclass defined at module
level in a tracked ``.py`` file of the PFP (its root, plus
``omega_engine_education/code/``; see :func:`resolve`). Test files, ``demos/`` and
``papers/`` are outside the census: demo-local types live and die with their demo, and
each paper package is a hermetic deposit that must not import another paper's code, so
its types are not shared PFP types (three papers each define their own ``MoveType``).

The register (``type_register.yaml``) holds one row per module that defines
types, the public class names defined in more than one module, groups of types
that describe one fact under different names, and types derived from another
type. The census reads the source tree with ``ast`` only, so it imports nothing
it scans.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, model_validator


ModulePath = StrictStr
TypeRef = Annotated[StrictStr, Field(pattern=r"^[a-z0-9_/]+\.py::[A-Z][A-Za-z0-9]*$")]
"""``<module path>::<ClassName>``."""


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class World(str, Enum):
    """Which import world a module belongs to."""

    COLOCATED = "colocated"  # beside the files it types; loaded by file path
    RUNTIME = "runtime"  # the python/ import root (domain, use_cases, infrastructure)
    GENERATED = "generated"  # written by a generator from a YAML source


class Source(str, Enum):
    """Which side states the shape of the module's types."""

    PYDANTIC = "pydantic"  # only the .py states it; YAML, if any, is data or generated
    YAML = "yaml"  # a YAML file states it; the .py is generated from that file
    BOTH_PARITY_TESTED = "both_parity_tested"  # both hand-written; a test compares them
    BOTH_UNCHECKED = "both_unchecked"  # both hand-written; no test compares them


class YamlRole(str, Enum):
    JSON_SCHEMA = "json_schema"  # hand-written JSON Schema 2020-12
    GENERATED_JSON_SCHEMA = "generated_json_schema"  # written by a generator
    CUSTOM_SCHEMA = "custom_schema"  # a repo-specific field-spec dialect, not JSON Schema
    DATA = "data"  # instances the module validates (registers, catalogs, specs)


class Status(str, Enum):
    CANONICAL = "canonical"
    REVIEW = "review"  # placement, overlap or drift awaits the owner's decision


class YamlRef(_Frozen):
    path: StrictStr = Field(min_length=1)  # a file, or a glob for many data files
    role: YamlRole


class ModuleRow(_Frozen):
    path: ModulePath = Field(pattern=r"^[a-z0-9_/]+\.py$")
    world: World
    source: Source
    yaml: tuple[YamlRef, ...] = ()
    tests: tuple[StrictStr, ...] = ()
    status: Status
    note: StrictStr | None = None

    @model_validator(mode="after")
    def _source_is_named(self) -> ModuleRow:
        roles = {y.role for y in self.yaml}
        stated = roles & {YamlRole.JSON_SCHEMA, YamlRole.CUSTOM_SCHEMA}
        if (self.world is World.GENERATED) != (self.source is Source.YAML):
            raise ValueError(f"GENERATED_IFF_YAML_SOURCE: {self.path}")
        if self.source is not Source.PYDANTIC and not stated:
            raise ValueError(f"YAML_SOURCE_NOT_NAMED: {self.path}")
        if self.source is Source.PYDANTIC and stated:
            raise ValueError(f"PYDANTIC_SOURCE_LISTS_A_HAND_WRITTEN_SCHEMA: {self.path}")
        if self.source is Source.BOTH_PARITY_TESTED and not self.tests:
            raise ValueError(f"PARITY_CLAIM_WITHOUT_TEST: {self.path}")
        if self.status is Status.REVIEW and not self.note:
            raise ValueError(f"REVIEW_ROW_NEEDS_A_NOTE: {self.path}")
        return self


class NameCollision(_Frozen):
    """A public type name defined in two or more modules. The list may only shrink."""

    name: StrictStr = Field(pattern=r"^[A-Z][A-Za-z0-9]*$")
    modules: tuple[ModulePath, ...] = Field(min_length=2)
    disposition: StrictStr = Field(min_length=1)


class OverlapGroup(_Frozen):
    """Types that describe one fact under different names. Each group should end as one type."""

    fact: StrictStr = Field(pattern=r"^[a-z][a-z0-9_]*$")
    types: tuple[TypeRef, ...] = Field(min_length=2)
    disposition: StrictStr = Field(min_length=1)


class DerivedType(_Frozen):
    """A stored type that is a function of other data. It should become a view or computed field."""

    type: TypeRef
    of: tuple[StrictStr, ...] = Field(min_length=1)  # type refs, or file globs
    kind: Literal["projection", "join", "aggregate", "computed"]
    checked_by: StrictStr | None = None  # "<test file>::<test function>"


class TypeRegister(_Frozen):
    schema_: Literal["pfp.type-register.v1"] = Field(alias="schema")
    authority_effect: Literal["None"]
    modules: tuple[ModuleRow, ...]
    name_collisions: tuple[NameCollision, ...]
    overlaps: tuple[OverlapGroup, ...]
    derived: tuple[DerivedType, ...]

    @model_validator(mode="after")
    def _unique_and_sorted(self) -> TypeRegister:
        for label, keys in (
            ("MODULE", [m.path for m in self.modules]),
            ("COLLISION", [c.name for c in self.name_collisions]),
            ("OVERLAP", [o.fact for o in self.overlaps]),
            ("DERIVED", [d.type for d in self.derived]),
        ):
            if keys != sorted(set(keys)):
                raise ValueError(f"{label}_ROWS_MUST_BE_UNIQUE_AND_SORTED")
        return self
