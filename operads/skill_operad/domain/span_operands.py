"""span_operands.py
================
Clean Architecture Domain Models for Text Spans as Multicategory Operands.

Enforces:
1. Exact UTF-8 byte span boundaries without BOM (RULE_UTF8_MOJIBAKE_CLEANLINESS_001).
2. Content-addressable SHA-256 integrity digests for all parsed spans.
3. Sort mapping to ADMITTED_FINITE_COLOURS (State, Code, Contract, Proof, Receipt, Audit, Diagram, Ledger, Paper, Post).
4. Strict Value Object exact-type equality (type(self) is type(other)).
5. Operadic multi-ary evaluation over span operands.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Callable, Sequence

from .colours import ADMITTED_FINITE_COLOURS, Colour
from .errors import (
    ArityMismatchError,
    DomainError,
    Err,
    IllTypedCompositionError,
    InvalidColourError,
    Ok,
    Result,
)


@dataclass(frozen=True)
class SpanOperand:
    """An exact, content-addressed text span acting as an operand in a coloured multicategory."""

    file_path: str
    start_line: int  # 1-indexed
    end_line: int  # 1-indexed inclusive
    byte_offset: int  # 0-indexed byte offset in UTF-8
    byte_length: int
    colour: str
    content_sha256: str
    raw_text: str
    role: str = "general"

    def __post_init__(self) -> None:
        if self.colour not in ADMITTED_FINITE_COLOURS:
            raise InvalidColourError(f"Span colour '{self.colour}' not in admitted finite colours.")
        if self.start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {self.start_line}")
        if self.end_line < self.start_line:
            raise ValueError(f"end_line ({self.end_line}) cannot precede start_line ({self.start_line})")
        if self.byte_offset < 0 or self.byte_length < 0:
            raise ValueError("byte_offset and byte_length must be non-negative.")

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, SpanOperand)
        return (
            self.file_path == other.file_path
            and self.start_line == other.start_line
            and self.end_line == other.end_line
            and self.byte_offset == other.byte_offset
            and self.byte_length == other.byte_length
            and self.colour == other.colour
            and self.content_sha256 == other.content_sha256
            and self.role == other.role
            and self.raw_text == other.raw_text
        )

    def verify_integrity(self) -> Result[bool, DomainError]:
        """Verify that the raw_text matches byte_length, content_sha256, and contains no BOM."""
        raw_bytes = self.raw_text.encode("utf-8")
        if raw_bytes.startswith(b"\xef\xbb\xbf"):
            return Err(DomainError("UTF8_BOM_DETECTED", f"Span in {self.file_path} contains forbidden UTF-8 BOM."))
        if len(raw_bytes) != self.byte_length:
            return Err(
                DomainError(
                    "BYTE_LENGTH_MISMATCH",
                    f"Span byte length mismatch: declared {self.byte_length}, actual {len(raw_bytes)}",
                )
            )
        computed_sha = hashlib.sha256(raw_bytes).hexdigest()
        if computed_sha != self.content_sha256:
            return Err(
                DomainError(
                    "DIGEST_MISMATCH",
                    f"Span SHA-256 mismatch: declared {self.content_sha256}, computed {computed_sha}",
                )
            )
        return Ok(True)


@dataclass(frozen=True)
class DocumentSpanPartition:
    """The exhaustive partition of a skill or rule document into typed span operands."""

    file_path: str
    total_lines: int
    total_bytes: int
    spans: tuple[SpanOperand, ...]

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, DocumentSpanPartition)
        return (
            self.file_path == other.file_path
            and self.total_lines == other.total_lines
            and self.total_bytes == other.total_bytes
            and self.spans == other.spans
        )

    def get_spans_by_colour(self, colour: str) -> list[SpanOperand]:
        return [s for s in self.spans if s.colour == colour]

    def get_spans_by_role(self, role: str) -> list[SpanOperand]:
        return [s for s in self.spans if s.role == role]


def _infer_colour_from_heading(heading: str) -> tuple[str, str]:
    """Infers the multicategory colour and role from markdown section heading keywords."""
    h_strip = heading.strip("# \t\r\n")
    h_lower = h_strip.lower()
    if heading.startswith("# ") or h_lower.endswith("title"):
        return "Contract", "title_section"
    if any(k in h_lower for k in ("rule", "invariant", "principle", "contract", "boundary", "directive", "frontmatter")):
        return "Contract", "contract_section"
    if any(k in h_lower for k in ("code", "implementation", "script", "syntax", "python", "rust")):
        return "Code", "code_section"
    if any(k in h_lower for k in ("proof", "derivation", "lemma", "theorem", "axiom", "formal")):
        return "Proof", "proof_section"
    if any(k in h_lower for k in ("receipt", "evidence", "check", "hash", "acceptance criteria", "benchmark", "verification")):
        return "Receipt", "receipt_section"
    if any(k in h_lower for k in ("audit", "critique", "adversary", "red-team", "defect", "antibody")):
        return "Audit", "audit_section"
    if any(k in h_lower for k in ("diagram", "figure", "visual", "dime", "dag", "ast")):
        return "Diagram", "diagram_section"
    if any(k in h_lower for k in ("ledger", "register", "queue", "log", "headstone")):
        return "Ledger", "ledger_section"
    if any(k in h_lower for k in ("workflow", "step", "state", "protocol", "pipeline")):
        return "State", "workflow_section"
    return "State", "general_section"


def partition_markdown_document(
    content: str,
    file_path: str = "document.md",
) -> Result[DocumentSpanPartition, DomainError]:
    """Partition a markdown document into typed, content-addressed SpanOperand objects."""
    raw_bytes = content.encode("utf-8")
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        return Err(DomainError("UTF8_BOM_DETECTED", f"Document {file_path} contains forbidden UTF-8 BOM."))

    lines = content.splitlines(keepends=True)
    total_lines = len(lines)
    total_bytes = len(raw_bytes)

    if total_lines == 0:
        return Ok(
            DocumentSpanPartition(
                file_path=file_path,
                total_lines=0,
                total_bytes=0,
                spans=(),
            )
        )

    spans: list[SpanOperand] = []
    line_idx = 0
    curr_byte_offset = 0

    # 1. Check for YAML frontmatter
    if lines[0].strip() == "---":
        fm_end = -1
        for i in range(1, total_lines):
            if lines[i].strip() == "---":
                fm_end = i
                break
        if fm_end != -1:
            fm_lines = lines[: fm_end + 1]
            fm_text = "".join(fm_lines)
            fm_bytes = fm_text.encode("utf-8")
            spans.append(
                SpanOperand(
                    file_path=file_path,
                    start_line=1,
                    end_line=fm_end + 1,
                    byte_offset=0,
                    byte_length=len(fm_bytes),
                    colour="Contract",
                    content_sha256=hashlib.sha256(fm_bytes).hexdigest(),
                    raw_text=fm_text,
                    role="frontmatter",
                )
            )
            line_idx = fm_end + 1
            curr_byte_offset = len(fm_bytes)

    # 2. Partition remainder by markdown headers (## or #)
    sec_start_line = line_idx + 1
    sec_byte_offset = curr_byte_offset
    sec_lines: list[str] = []
    sec_heading = "Header" if spans else "Introduction"

    while line_idx < total_lines:
        line = lines[line_idx]
        is_header = line.startswith("#") and not line.startswith("```")

        if is_header and sec_lines:
            if "".join(sec_lines).strip():
                # Finalize previous section
                sec_text = "".join(sec_lines)
                sec_bytes = sec_text.encode("utf-8")
                colour, role = _infer_colour_from_heading(sec_heading)
                spans.append(
                    SpanOperand(
                        file_path=file_path,
                        start_line=sec_start_line,
                        end_line=line_idx,  # previous line
                        byte_offset=sec_byte_offset,
                        byte_length=len(sec_bytes),
                        colour=colour,
                        content_sha256=hashlib.sha256(sec_bytes).hexdigest(),
                        raw_text=sec_text,
                        role=role,
                    )
                )
            # Reset for new section
            sec_start_line = line_idx + 1
            sec_byte_offset = curr_byte_offset
            sec_lines = [line]
            sec_heading = line.strip("# \t\r\n")
        else:
            if not sec_lines and is_header:
                sec_heading = line.strip("# \t\r\n")
            sec_lines.append(line)

        curr_byte_offset += len(line.encode("utf-8"))
        line_idx += 1

    if sec_lines and "".join(sec_lines).strip():
        sec_text = "".join(sec_lines)
        sec_bytes = sec_text.encode("utf-8")
        colour, role = _infer_colour_from_heading(sec_heading)
        spans.append(
            SpanOperand(
                file_path=file_path,
                start_line=sec_start_line,
                end_line=total_lines,
                byte_offset=sec_byte_offset,
                byte_length=len(sec_bytes),
                colour=colour,
                content_sha256=hashlib.sha256(sec_bytes).hexdigest(),
                raw_text=sec_text,
                role=role,
            )
        )

    return Ok(
        DocumentSpanPartition(
            file_path=file_path,
            total_lines=total_lines,
            total_bytes=total_bytes,
            spans=tuple(spans),
        )
    )


@dataclass(frozen=True)
class SpanMulticategoryMorphism:
    """An executable planar morphism operating on typed span operands."""

    name: str
    source_colours: tuple[str, ...]
    target_colour: str
    transform: Callable[[tuple[SpanOperand, ...]], Result[SpanOperand, DomainError]] = field(
        repr=False, compare=False
    )

    @property
    def arity(self) -> int:
        return len(self.source_colours)

    def execute(self, inputs: Sequence[SpanOperand]) -> Result[SpanOperand, DomainError]:
        """Execute the morphism on a sequence of span operands with strict sort checks."""
        if len(inputs) != self.arity:
            return Err(
                ArityMismatchError(
                    f"Morphism '{self.name}' expects arity {self.arity}, got {len(inputs)}"
                )
            )
        for i, (span, expected_colour) in enumerate(zip(inputs, self.source_colours)):
            if span.colour != expected_colour:
                return Err(
                    IllTypedCompositionError(
                        f"Slot {i} of '{self.name}' expects colour '{expected_colour}', got '{span.colour}' from {span.file_path}:{span.start_line}"
                    )
                )
        return self.transform(tuple(inputs))
