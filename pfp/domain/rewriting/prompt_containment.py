"""PFP Prompt Containment Pydantic Data Model.

AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    field_validator,
    model_validator,
)

MAX_DEPTH = 5


class MutationKind(str, Enum):
    """Mutation kinds named by the P-star family templates."""

    ROOT_SEED = "root_seed"
    DECOMPOSE = "decompose"


class PipelineStage(str, Enum):
    """Stated pipeline order: prompts, then rewriting, then packetization."""

    PROMPTS = "prompts"
    REWRITING = "rewriting"
    PACKETIZATION = "packetization"


class ExpansionNode(BaseModel):
    """Prompt expansion tree node with declared cardinality."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    mutation_kind: MutationKind
    prompt_ref: StrictStr = Field(min_length=1)
    cardinality: StrictInt = Field(ge=1)
    children: tuple[ExpansionNode, ...] = ()
    authority_effect: Literal["None"]

    @field_validator("cardinality", mode="before")
    @classmethod
    def _reject_bool(cls, v: object) -> object:
        if isinstance(v, bool):
            raise ValueError("bool is not a valid integer here.")
        return v

    @model_validator(mode="after")
    def _containment_law(self) -> ExpansionNode:
        expected = 1 + sum(child.cardinality for child in self.children)
        if self.cardinality != expected:
            raise ValueError(f"cardinality {self.cardinality} != containment sum {expected}.")
        if self.depth() > MAX_DEPTH:
            raise ValueError(f"tree depth exceeds max_depth = {MAX_DEPTH}.")
        return self

    def depth(self) -> int:
        """Number of edges on the longest root-to-leaf path."""
        return 0 if not self.children else 1 + max(c.depth() for c in self.children)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        if not isinstance(other, ExpansionNode):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        return hash((type(self), self.prompt_ref, self.cardinality))


ExpansionNode.model_rebuild()
