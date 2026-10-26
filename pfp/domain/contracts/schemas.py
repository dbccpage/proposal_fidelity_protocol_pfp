"""Pydantic v2 models for PFP Schemas and Schema Catalogs.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr


class SchemaSpec(BaseModel):
    """Specification of an admitted schema definition."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_id: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    version: StrictStr = Field(default="1.0.0")
    authority_effect: StrictStr = Field(default="None")
    definition: Dict[str, Any]
    closed_object_enforced: StrictBool = True


class SchemaCatalog(BaseModel):
    """Catalog of registered schemas in the PFP suite."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    version: StrictStr = Field(default="1.0.0")
    schemas: Dict[str, SchemaSpec] = Field(default_factory=dict)

    def get_schema(self, schema_id: str) -> Optional[SchemaSpec]:
        return self.schemas.get(schema_id)


class SchemaValidationResult(BaseModel):
    """Result of schema validation over a payload."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_id: StrictStr = Field(min_length=1)
    is_valid: StrictBool
    errors: List[StrictStr] = Field(default_factory=list)
    authority_effect: StrictStr = Field(default="None")
