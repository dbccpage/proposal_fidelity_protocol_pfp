"""PFP Schema Registry and Envelope Envelopes (Draft 2020-12 & Grammar Schemas).

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from .base import AuthorityEffect, PfpBaseModel


class PfpEnvelopeSchemaEntry(PfpBaseModel):
    file: str = Field(pattern=r"^[a-z0-9_]+\.schema\.yaml$")
    dialect: Literal["https://json-schema.org/draft/2020-12/schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema_dollar_id: str | None = None
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpGrammarSchemaEntry(PfpBaseModel):
    file: str = Field(pattern=r"^[a-z0-9_]+_schema\.yaml$")
    schema_id: str = Field(pattern=r"^[A-Z0-9]+(-[A-Z0-9]+)*-v\d+\.\d+$")
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


class PfpSchemaRegister(PfpBaseModel):
    envelope_schemas: list[PfpEnvelopeSchemaEntry] = Field(min_length=9, max_length=9)
    grammar_schemas: list[PfpGrammarSchemaEntry] = Field(min_length=4, max_length=4)
    authority_effect: AuthorityEffect = AuthorityEffect.NONE


# Aliases
EnvelopeSchemaEntry = PfpEnvelopeSchemaEntry
GrammarSchemaEntry = PfpGrammarSchemaEntry
SchemaRegister = PfpSchemaRegister
