"""Domain models and boundary parser for prompt rewriting.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Annotated, Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator

ALPHABET = frozenset("0123456789abcdefghijklmnopqrstuvwxyz<>")
MAX_BYTES = 65536
MAX_DEPTH = 32
MAX_NODES = 4096

Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
Role = Literal["task", "constraint", "context", "output", "unresolved"]
ROLES: Dict[str, str] = {"task": "q", "constraint": "c", "context": "d", "output": "o", "unresolved": "u"}


@dataclass(frozen=True)
class Boundary:
    """Grammatical bracket nesting `<...>` for prompt isolation."""

    atom: Optional[str] = None
    children: Tuple[Boundary, ...] = ()

    def render(self) -> str:
        return (
            "<"
            + (self.atom if self.atom is not None else "".join(c.render() for c in self.children))
            + ">"
        )


def parse_boundary(text: str) -> Boundary:
    """Parses nested angle-bracket boundary trees."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("WIRE_BYTE_BUDGET")
    if not text or any(c not in ALPHABET for c in text):
        raise ValueError("WIRE_ALPHABET")
    pos = 0
    nodes = 0

    def packet(depth: int) -> Boundary:
        nonlocal pos, nodes
        nodes += 1
        if depth > MAX_DEPTH or nodes > MAX_NODES:
            raise ValueError("WIRE_STRUCTURE_BUDGET")
        if pos >= len(text) or text[pos] != "<":
            raise ValueError("EXPECTED_OPEN")
        pos += 1
        start = pos
        while pos < len(text) and text[pos] not in "<>":
            pos += 1
        atom_content = text[start:pos]
        if pos < len(text) and text[pos] == ">":
            pos += 1
            if not atom_content:
                raise ValueError("EMPTY_ATOM")
            return Boundary(atom=atom_content)
        if atom_content:
            raise ValueError("MIXED_ATOM_AND_CHILDREN")
        kids: List[Boundary] = []
        while pos < len(text) and text[pos] != ">":
            kids.append(packet(depth + 1))
        if pos >= len(text) or text[pos] != ">":
            raise ValueError("UNCLOSED_BOUNDARY")
        pos += 1
        if not kids:
            raise ValueError("EMPTY_BOUNDARY")
        return Boundary(children=tuple(kids))

    root = packet(0)
    if pos != len(text):
        raise ValueError("TRAILING_GARBAGE")
    return root


class Segment(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    role: Role
    boundary: StrictStr
    text: StrictStr = Field(min_length=1)

    @model_validator(mode="after")
    def validate_boundary_syntax(self) -> Segment:
        parse_boundary(self.boundary)
        return self


class Binding(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    symbol: StrictStr = Field(min_length=1)
    target_role: Role
    description: StrictStr = Field(default="")


class RewriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    request_id: StrictStr = Field(min_length=1)
    raw_prompt: StrictStr = Field(min_length=1)
    segments: List[Segment] = Field(default_factory=list)
    bindings: List[Binding] = Field(default_factory=list)
    boundary_format: StrictStr = Field(default="boundary_tree_v1")
    authority_effect: StrictStr = Field(default="None")


class TrialObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    trial_id: StrictStr = Field(min_length=1)
    passed: bool
    score: float
    fidelity_delta: float
    details: str = ""


class ComparisonTrial(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    candidate_a: StrictStr = Field(min_length=1)
    candidate_b: StrictStr = Field(min_length=1)
    observations: List[TrialObservation] = Field(default_factory=list)
    preferred_candidate: Optional[StrictStr] = None


class RewriteReceipt(BaseModel):
    """Machine receipt summarizing prompt rewrite and boundary parsing."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    request_id: StrictStr = Field(min_length=1)
    rewritten_prompt: StrictStr = Field(min_length=1)
    root_boundary: StrictStr = Field(min_length=1)
    segments_count: StrictInt = Field(ge=0)
    receipt_sha256: StrictStr = Field(default="")
    authority_effect: StrictStr = Field(default="None")

    @property
    def boundary_format(self) -> str:
        if self.root_boundary.startswith("<root>") and self.root_boundary.endswith("</root>"):
            return self.root_boundary[6:-7]
        return self.root_boundary
