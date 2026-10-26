"""Shared pydantic base for WDP product frames and contracts. AuthorityEffect: None."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Immutable, strict record that refuses unknown fields."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
