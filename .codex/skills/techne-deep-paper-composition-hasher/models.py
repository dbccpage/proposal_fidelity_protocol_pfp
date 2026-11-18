"""Pydantic v2 data models for typing mathematical formulas and prose claims across paper formats."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FormulaType(str, Enum):
    """Classification of mathematical expressions."""
    INLINE = "inline"
    DISPLAY = "display"
    EQUATION_ENV = "equation_env"
    ALIGN_ENV = "align_env"
    SUBFORMULA = "subformula"


class ClaimType(str, Enum):
    """Classification of formal epistemic claims."""
    THEOREM = "theorem"
    LEMMA = "lemma"
    PROPOSITION = "proposition"
    COROLLARY = "corollary"
    DEFINITION = "definition"
    REMARK = "remark"
    CONJECTURE = "conjecture"
    AXIOM = "axiom"
    EMPIRICAL_ASSERTION = "empirical_assertion"
    NUMERICAL_BOUND = "numerical_bound"


class AlignmentStatus(str, Enum):
    """Cross-format alignment classification."""
    EXACT_MATCH = "exact_match"
    NORMALIZED_MATCH = "normalized_match"
    EQUIVALENT_NOTATION = "equivalent_notation"
    UNMATCHED = "unmatched"
    DRIFT_DETECTED = "drift_detected"


class LocationAnchor(BaseModel):
    """Precise source location coordinates."""
    model_config = ConfigDict(frozen=True)

    file_type: str = Field(description="Format indicator: md, tex, etc.")
    file_path: str = Field(description="Relative path to file")
    start_line: int = Field(ge=1, description="1-indexed start line")
    end_line: int = Field(ge=1, description="1-indexed end line")
    start_char: Optional[int] = Field(default=None, description="Character column offset")
    end_char: Optional[int] = Field(default=None, description="Character column offset")
    start_byte_offset: Optional[int] = Field(default=None, ge=0, description="0-indexed UTF-8 start byte offset")
    end_byte_offset: Optional[int] = Field(default=None, ge=0, description="0-indexed UTF-8 end byte offset")
    location_sha256: Optional[str] = Field(default=None, description="SHA-256 of file:lines:bytes:content_hash")
    environment: Optional[str] = Field(default=None, description="TeX or MD environment name")


class PdfLocationAnchor(BaseModel):
    """Location anchor within compiled PDF."""
    model_config = ConfigDict(frozen=True)

    page_number: int = Field(ge=1, description="1-indexed PDF page")
    char_offset: Optional[int] = Field(default=None, ge=0, description="0-indexed character offset on page")
    location_sha256: Optional[str] = Field(default=None, description="SHA-256 of page:offset:snippet")
    matched_snippet: str = Field(description="Extracted text snippet from PDF")
    surrounding_context: str = Field(default="", description="Contextual text on the page")


class MathFormulaEntry(BaseModel):
    """Exhaustive typing of a single mathematical formula."""
    model_config = ConfigDict(frozen=True)

    uuid: UUID = Field(description="Deterministic UUIDv5 of the formula")
    formula_type: FormulaType = Field(description="Inline, display, or environment")
    raw_latex: str = Field(description="Verbatim LaTeX source string")
    normalized_latex: str = Field(description="Whitespace and delimiter normalized LaTeX")
    sha256_raw: str = Field(description="SHA-256 hex digest of raw_latex")
    sha256_normalized: str = Field(description="SHA-256 hex digest of normalized_latex")
    md_location: Optional[LocationAnchor] = Field(default=None, description="Anchor in Markdown")
    tex_location: Optional[LocationAnchor] = Field(default=None, description="Anchor in TeX")
    pdf_location: Optional[PdfLocationAnchor] = Field(default=None, description="Anchor in PDF")
    ast_symbols: List[str] = Field(default_factory=list, description="Extracted mathematical operators/symbols")
    surrounding_prose_context: str = Field(default="", description="Surrounding sentence or paragraph")
    code_bindings: List[str] = Field(default_factory=list, description="Python implementation anchors in code/")
    lean_bindings: List[str] = Field(default_factory=list, description="Lean 4 proof anchors in lean4/")


class ProseClaimEntry(BaseModel):
    """Exhaustive typing of a formal prose claim (Theorem, Proposition, etc.)."""
    model_config = ConfigDict(frozen=True)

    uuid: UUID = Field(description="Deterministic UUIDv5 of the claim")
    claim_type: ClaimType = Field(description="Type of epistemic assertion")
    label: str = Field(description="Canonical label, e.g. 'Theorem 5.1' or 'Proposition E.6'")
    title: Optional[str] = Field(default=None, description="Descriptive title of claim")
    statement_text: str = Field(description="Complete text of claim statement")
    normalized_text: str = Field(description="Whitespace/punctuation normalized text")
    sha256_statement: str = Field(description="SHA-256 hex digest of statement_text")
    md_location: Optional[LocationAnchor] = Field(default=None, description="Anchor in Markdown")
    tex_location: Optional[LocationAnchor] = Field(default=None, description="Anchor in TeX")
    pdf_location: Optional[PdfLocationAnchor] = Field(default=None, description="Anchor in PDF")
    referenced_formula_uuids: List[UUID] = Field(default_factory=list, description="UUIDs of embedded formulas")
    claim_ledger_id: Optional[str] = Field(default=None, description="Registered ID in claim ledger (e.g. V1)")
    code_bindings: List[str] = Field(default_factory=list, description="Python implementation anchors in code/")
    lean_bindings: List[str] = Field(default_factory=list, description="Lean 4 proof anchors in lean4/")
    claim_hygiene_flags: List[str] = Field(default_factory=list, description="Detected hygiene warnings/violations")


class ProseLineEntry(BaseModel):
    """Hashed line of prose for complete line-by-line custody."""
    model_config = ConfigDict(frozen=True)

    uuid: UUID = Field(description="Deterministic UUIDv5 of the prose line")
    line_number_md: int = Field(ge=1, description="Markdown line number")
    section_header: str = Field(default="", description="Enclosing section header")
    raw_line: str = Field(description="Verbatim line text")
    sha256: str = Field(description="SHA-256 hex digest of line")
    is_claim_boundary: bool = Field(default=False, description="Whether this line opens/closes a formal claim")


class FormatCrossCheck(BaseModel):
    """Cross-format alignment receipt between Markdown, TeX, and PDF."""
    model_config = ConfigDict(frozen=True)

    item_uuid: UUID = Field(description="UUID of checked formula or claim")
    item_type: str = Field(description="'formula' | 'claim' | 'line'")
    md_sha256: Optional[str] = Field(default=None, description="MD representation hash")
    tex_sha256: Optional[str] = Field(default=None, description="TeX representation hash")
    pdf_matched: bool = Field(default=False, description="Whether located in PDF")
    status: AlignmentStatus = Field(description="Alignment verdict")
    drift_notes: Optional[str] = Field(default=None, description="Detailed explanation if drift detected")


class PaperCompositionManifest(BaseModel):
    """Top-level typed catalog of the paper's mathematical and prose composition."""
    manifest_version: str = Field(default="1.0.0", description="Schema version")
    paper_id: str = Field(description="Canonical paper ID, e.g. 'PO-000'")
    paper_title: str = Field(description="Title of monograph")
    manuscript_version: str = Field(description="Monograph version string")
    timestamp_utc: str = Field(description="Timestamp of manifest generation")
    total_formulas_extracted: int = Field(ge=0, description="Total inline and display formulas")
    total_claims_extracted: int = Field(ge=0, description="Total formal claims")
    total_lines_hashed: int = Field(ge=0, description="Total Markdown lines hashed")
    formulas: Dict[str, MathFormulaEntry] = Field(default_factory=dict, description="Math formulas keyed by UUID")
    claims: Dict[str, ProseClaimEntry] = Field(default_factory=dict, description="Prose claims keyed by UUID")
    cross_format_checks: List[FormatCrossCheck] = Field(default_factory=list, description="Alignment receipts")
    code_binding_coverage: float = Field(ge=0.0, le=1.0, description="Fraction of formulas bound to code")
    lean_binding_coverage: float = Field(ge=0.0, le=1.0, description="Fraction of claims bound to Lean 4")
    hygiene_clean_status: bool = Field(description="True if zero forbidden words detected")
    hygiene_warnings: List[str] = Field(default_factory=list, description="List of hygiene warnings")
    dialect_warnings: List[str] = Field(default_factory=list, description="Detected in-house jargon or over-guarded boilerplate")
    identity_checks: Dict[str, Any] = Field(default_factory=dict, description="Cross-file author, date, and version consistency checks")
