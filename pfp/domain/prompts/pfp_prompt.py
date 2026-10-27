"""PFP Raw Prompt Pydantic Data Model.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictStr,
    field_validator,
    model_validator,
)


class PfpPrompt(BaseModel):
    """Raw prompt source text container."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: Literal["core.pfp.prompt.v1"]
    prompt_id: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    system_prompt: StrictStr | None = None
    user_prompt: StrictStr = Field(min_length=1)
    content_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    authority_effect: Literal["None"]

    @field_validator("user_prompt")
    @classmethod
    def validate_user_prompt_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("user_prompt text cannot be empty or whitespace.")
        return v

    @model_validator(mode="after")
    def validate_content_digest(self) -> PfpPrompt:
        actual = hashlib.sha256(self.user_prompt.encode("utf-8")).hexdigest()
        if actual != self.content_sha256:
            raise ValueError("content_sha256 does not match SHA-256 of user_prompt UTF-8 bytes.")
        return self

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        if not isinstance(other, PfpPrompt):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        return hash((type(self), self.prompt_id))
