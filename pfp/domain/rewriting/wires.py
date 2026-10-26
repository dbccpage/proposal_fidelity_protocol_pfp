"""Pydantic v2 and domain models for Wire Representations.

Defines recursive wire terms (Void | Atom | App), TokenLegend, and Syntax Profiles.
AuthorityEffect: None.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, model_validator


class WireTermKind(str, Enum):
    VOID = "Void"
    ATOM = "Atom"
    APP = "App"


class VoidTerm(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    kind: Literal[WireTermKind.VOID] = WireTermKind.VOID

    def render(self) -> str:
        return "()"


class AtomTerm(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    kind: Literal[WireTermKind.ATOM] = WireTermKind.ATOM
    value: StrictStr = Field(min_length=1)

    def render(self) -> str:
        return self.value


class AppTerm(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    kind: Literal[WireTermKind.APP] = WireTermKind.APP
    operator: StrictStr = Field(min_length=1)
    arguments: List[Union[VoidTerm, AtomTerm, AppTerm]] = Field(default_factory=list)

    def render(self) -> str:
        args_str = " ".join(arg.render() for arg in self.arguments)
        return f"({self.operator} {args_str})" if args_str else f"({self.operator})"


WireTerm = Union[VoidTerm, AtomTerm, AppTerm]


class TokenLegend(BaseModel):
    """Token legend mapping wire tokens to semantic primitives."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    profile_name: StrictStr = Field(min_length=1)
    tokens: Dict[str, str] = Field(default_factory=dict)
    delimiters: Dict[str, str] = Field(default_factory=dict)


class SyntaxProfile(BaseModel):
    """Operational syntax restriction profile (e.g. Tier H, Tier D, mss-boundary-v1)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    profile_id: StrictStr = Field(min_length=1)
    title: StrictStr = Field(min_length=1)
    version: StrictStr = Field(default="1.0.0")
    tier: StrictStr = Field(default="Tier-H")
    allowed_tokens: List[StrictStr] = Field(default_factory=list)
    max_expression_depth: StrictInt = Field(default=32, ge=1)
    max_tokens_count: StrictInt = Field(default=4096, ge=1)
    token_legend: Optional[TokenLegend] = None


class WirePacket(BaseModel):
    """Encapsulation of a wire term payload with its syntax profile."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    packet_id: StrictStr = Field(min_length=1)
    profile_id: StrictStr = Field(min_length=1)
    term: WireTerm
    authority_effect: StrictStr = Field(default="None")

    def render(self) -> str:
        return self.term.render()


class WireCodec:
    """Deterministic parser and serializer for wire representation strings."""

    @staticmethod
    def parse_s_expression(text: str) -> WireTerm:
        """Parses simple S-expression wire strings into WireTerm AST."""
        stripped = text.strip()
        if not stripped or stripped == "()":
            return VoidTerm()
        if not (stripped.startswith("(") and stripped.endswith(")")):
            return AtomTerm(value=stripped)
        inner = stripped[1:-1].strip()
        parts = inner.split(None, 1)
        if not parts:
            return VoidTerm()
        op = parts[0]
        if len(parts) == 1:
            return AppTerm(operator=op, arguments=[])
        arg_tokens = parts[1].split()
        args: List[WireTerm] = [AtomTerm(value=t) for t in arg_tokens]
        return AppTerm(operator=op, arguments=args)

    @staticmethod
    def serialize(term: WireTerm) -> str:
        return term.render()
