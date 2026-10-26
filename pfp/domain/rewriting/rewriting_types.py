"""PFP Prompt Rewriting Pydantic Data Model.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import re
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

_WIRE_RE = re.compile(r"^<<p><v1>((?:<<[a-z]><s[0-9]+>>)+)>$")
_WIRE_SYMBOL_RE = re.compile(r"<s([0-9]+)>")


class SpanRole(str, Enum):
    """Semantic roles for prompt byte spans."""

    TASK = "task"
    CONSTRAINT = "constraint"
    CONTEXT = "context"
    OUTPUT = "output"
    UNRESOLVED = "unresolved"


class RewritingBase(BaseModel):
    """Strict immutable base record with exact-type equality."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return NotImplemented
        if not isinstance(other, RewritingBase):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        return hash((type(self), repr(self.model_dump())))


class ByteSpan(RewritingBase):
    """Half-open byte interval [start_byte, end_byte) with a semantic role."""

    start_byte: StrictInt = Field(ge=0)
    end_byte: StrictInt = Field(ge=0)
    role: SpanRole

    @field_validator("start_byte", "end_byte", mode="before")
    @classmethod
    def _reject_bool(cls, v: object) -> object:
        if isinstance(v, bool):
            raise ValueError("bool is not a valid integer here.")
        return v

    @model_validator(mode="after")
    def _non_empty(self) -> ByteSpan:
        if self.end_byte <= self.start_byte:
            raise ValueError("end_byte must be strictly greater than start_byte.")
        return self


class SpanPartition(RewritingBase):
    """Contiguous disjoint byte-exact partition covering a whole UTF-8 prompt."""

    prompt_byte_length: StrictInt = Field(ge=1)
    spans: tuple[ByteSpan, ...] = Field(min_length=1)

    @field_validator("prompt_byte_length", mode="before")
    @classmethod
    def _reject_bool(cls, v: object) -> object:
        if isinstance(v, bool):
            raise ValueError("bool is not a valid integer here.")
        return v

    @model_validator(mode="after")
    def _contiguous_cover(self) -> SpanPartition:
        cursor = 0
        for span in self.spans:
            if span.start_byte != cursor:
                kind = "overlap or duplication" if span.start_byte < cursor else "gap"
                raise ValueError(
                    f"partition {kind} at byte {cursor}: next span starts at {span.start_byte}."
                )
            cursor = span.end_byte
        if cursor != self.prompt_byte_length:
            raise ValueError(
                f"partition ends at byte {cursor}, prompt has {self.prompt_byte_length} bytes."
            )
        return self


class BoundaryWire(RewritingBase):
    """mss-boundary-v1 wire term; natural language stays in the external codebook."""

    profile: Literal["mss-boundary-v1"]
    term: StrictStr

    @model_validator(mode="after")
    def _shape(self) -> BoundaryWire:
        match = _WIRE_RE.match(self.term)
        if match is None:
            raise ValueError("wire term must match <<p><v1>(<<role><sN>>)+>.")
        symbols = [int(n) for n in _WIRE_SYMBOL_RE.findall(match.group(1))]
        if symbols != list(range(len(symbols))):
            raise ValueError("wire symbols must be s0, s1, ... in order, each used once.")
        return self


class SymbolBinding(RewritingBase):
    """Resolution of one wire symbol to an exact source substring."""

    symbol_token: StrictStr = Field(pattern=r"^s[0-9]+$")
    start_byte: StrictInt = Field(ge=0)
    end_byte: StrictInt = Field(ge=1)
    text: StrictStr

    @field_validator("start_byte", "end_byte", mode="before")
    @classmethod
    def _reject_bool(cls, v: object) -> object:
        if isinstance(v, bool):
            raise ValueError("bool is not a valid integer here.")
        return v


class CompilationReceipt(RewritingBase):
    """Immutable receipt: no bytes dropped, duplicated, or mutated without trace."""

    prompt: StrictStr = Field(min_length=1)
    prompt_sha256: StrictStr = Field(pattern=r"^[0-9a-f]{64}$")
    partition: SpanPartition
    wire: BoundaryWire
    symbols: tuple[SymbolBinding, ...] = Field(min_length=1)
    authority_effect: Literal["None"]

    @model_validator(mode="after")
    def _byte_exact(self) -> CompilationReceipt:
        raw = self.prompt.encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != self.prompt_sha256:
            raise ValueError("prompt_sha256 does not match prompt UTF-8 bytes.")
        if len(raw) != self.partition.prompt_byte_length:
            raise ValueError("partition prompt_byte_length differs from prompt UTF-8 length.")
        spans = self.partition.spans
        if len(self.symbols) != len(spans):
            raise ValueError("one symbol binding is required per span.")
        wire_count = len(_WIRE_SYMBOL_RE.findall(self.wire.term))
        if wire_count != len(spans):
            raise ValueError("wire symbol count differs from span count.")
        for index, (span, sym) in enumerate(zip(spans, self.symbols, strict=True)):
            if sym.symbol_token != f"s{index}":
                raise ValueError(f"symbol {index} must be s{index}.")
            if (sym.start_byte, sym.end_byte) != (span.start_byte, span.end_byte):
                raise ValueError(f"symbol s{index} range differs from its span.")
            if raw[span.start_byte : span.end_byte] != sym.text.encode("utf-8"):
                raise ValueError(f"symbol s{index} text differs from source substring.")
        return self
