"""Typed register of the PFP schema files.

Models the two groups stated in ``schemas/README.md``: nine Draft 2020-12
envelope schemas (each with an ``$id`` except ``code_rewrite_packet_v1``) and
four grammar schemas identified by a ``schema_id``.  The schema bodies stay in
the YAML files; this module types the register and its invariants.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    model_validator,
)

DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


class _Frozen(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class EnvelopeSchemaEntry(_Frozen):
    """A Draft 2020-12 envelope schema file."""

    file: StrictStr = Field(pattern=r"^[a-z0-9_]+\.schema\.yaml$")
    dialect: Literal["https://json-schema.org/draft/2020-12/schema"]
    schema_dollar_id: StrictStr | None = None
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _id_shape(self) -> EnvelopeSchemaEntry:
        if self.schema_dollar_id is not None and not self.schema_dollar_id.startswith("omega."):
            raise ValueError("$id must live in the omega. namespace")
        return self


class GrammarSchemaEntry(_Frozen):
    """A grammar schema file identified by ``schema_id`` (no ``$schema``)."""

    file: StrictStr = Field(pattern=r"^[a-z0-9_]+_schema\.yaml$")
    schema_id: StrictStr = Field(pattern=r"^[A-Z0-9]+(-[A-Z0-9]+)*-v\d+\.\d+$")
    authority_effect: Literal["None"] = "None"


class SchemaRegister(_Frozen):
    """Nine envelope schemas and four grammar schemas."""

    envelope_schemas: tuple[EnvelopeSchemaEntry, ...]
    grammar_schemas: tuple[GrammarSchemaEntry, ...]
    authority_effect: Literal["None"] = "None"

    @model_validator(mode="after")
    def _shape(self) -> SchemaRegister:
        if len(self.envelope_schemas) != 9 or len(self.grammar_schemas) != 4:
            raise ValueError("expected 9 envelope schemas and 4 grammar schemas")
        missing = [e.file for e in self.envelope_schemas if e.schema_dollar_id is None]
        if missing != ["code_rewrite_packet_v1.schema.yaml"]:
            raise ValueError("only code_rewrite_packet_v1 may omit $id")
        ids = [e.schema_dollar_id for e in self.envelope_schemas if e.schema_dollar_id]
        ids += [g.schema_id for g in self.grammar_schemas]
        if len(set(ids)) != len(ids):
            raise ValueError("schema identifiers must be unique")
        return self
