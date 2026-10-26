"""Pydantic v2 and domain models for Prompts and Prompt Templates.

AuthorityEffect: None.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator


class PromptAssemblyError(ValueError):
    """A source, dependency, privacy contract, or budget prevented prompt assembly."""


class PromptSlot(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: StrictStr = Field(min_length=1)
    description: StrictStr = Field(default="")
    required: StrictBool = True
    slot_type: StrictStr = Field(default="text")
    max_tokens: Optional[StrictInt] = None


class PromptTemplate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    template_id: StrictStr = Field(min_length=1)
    version: StrictStr = Field(min_length=1)
    authority_effect: StrictStr = Field(default="None")
    system_format: StrictStr = Field(min_length=1)
    user_format: StrictStr = Field(min_length=1)
    slots: List[PromptSlot] = Field(default_factory=list)
    default_response_schema: Dict[str, Any] = Field(default_factory=dict)


class PromptPacket(BaseModel):
    """An assembled prompt packet ready for dispatch or offline replay."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    demo_id: StrictStr = Field(min_length=1)
    stage: StrictInt = Field(ge=0)
    system: StrictStr
    user: StrictStr
    response_schema: Dict[str, Any]
    system_sha256: StrictStr = ""
    user_sha256: StrictStr = ""
    schema_sha256: StrictStr = ""
    derived_under_policy: StrictStr = "SPK-001"
    authority_effect: StrictStr = "None"
    template_sha256: StrictStr = ""
    controller_sha256: StrictStr = ""
    seed_sha256: StrictStr = ""

    @model_validator(mode="after")
    def validate_authority(self) -> PromptPacket:
        if self.authority_effect != "None":
            raise ValueError("PromptPacket authority_effect must be 'None'")
        return self
