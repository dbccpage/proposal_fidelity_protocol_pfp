"""Domain base models with strict validation and authority-null semantics."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator


class _StrictFrozenModel(BaseModel):
    """Base model enforcing frozen immutability, strict typing, and no extra fields."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        strict=True,
        validate_default=True,
    )


class _AuthorityNullModel(_StrictFrozenModel):
    """Base model guaranteeing zero execution authority creation."""

    authority_effect: Literal[None] = None
    creates_execution_authority: Literal[False] = False

    @field_validator("creates_execution_authority", mode="before")
    @classmethod
    def _validate_execution_authority(cls, value: Any) -> bool:
        if type(value) is not bool or value is not False:
            raise ValueError("creates_execution_authority must be exact false")
        return value
