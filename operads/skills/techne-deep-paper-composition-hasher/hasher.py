"""Deep Paper Composition Hasher.

Extracts Markdown formulas and prose claims, hashes their normalized text, and
records a TeX match only when that hash is equal. PDF text presence and zip
membership are separate checks. Line hashes are counted and not stored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from pydantic import ValidationError

try:
    import fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except ImportError:
    HAVE_PYMUPDF = False

try:
    import pypdf
    HAVE_PYPDF = True
except ImportError:
    HAVE_PYPDF = False

from models import (
    AlignmentStatus,
    ClaimType,
    FormatCrossCheck,
    FormulaType,
    LocationAnchor,
    MathFormulaEntry,
    PaperCompositionManifest,
    PdfLocationAnchor,
    ProseClaimEntry,
    ProseLineEntry,
)

# Canonical stable namespace for deterministic UUIDv5 generation
COMPOSITION_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "coda.anomalon.org.paper.composition")

# Forbidden words per Claim Hygiene rule
FORBIDDEN_WORDS = [
    "proves", "guarantees", "mathematically verifies", "fundamentally",
    "true intelligence", "impossible", "universal", "flawless",
    "perfectly", "clearly", "obviously", "simply", "merely", "weaponized"
]

RE_FORBIDDEN = re.compile(r"\b(" + "|".join(re.escape(w) for w in FORBIDDEN_WORDS) + r")\b", re.IGNORECASE)

# In-house jargon and excessive courtroom/bureaucratic scaffolding patterns
INHOUSE_AND_OVERGUARDED_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("AuthorityEffect", re.compile(r"\bAuthorityEffect\b")),
    ("GTLA", re.compile(r"\bGTLA\b")),
    ("Woland", re.compile(r"\bWoland\b")),
    ("Old Man / OMC", re.compile(r"\b(?:Old Man|OMC)\b")),
    ("Blackrod", re.compile(r"\bBlackrod\b")),
    ("anti-skill", re.compile(r"\banti-skill\b", re.IGNORECASE)),
    ("monorepo / worktree", re.compile(r"\b(?:monorepo|worktree)\b", re.IGNORECASE)),
    ("REVIEW_SCOPE", re.compile(r"\bREVIEW_SCOPE(?:\.md)?\b")),
    ("courtroom authority disclaimer", re.compile(r"\b(?:jurisdiction|institutional standing|operational authority|assigns no authorization)\b", re.IGNORECASE)),
    ("withdrawn theorem stamp", re.compile(r"\b(?:Withdrawn as a theorem of this deposit|not a (?:Lean )?theorem of this deposit)\b", re.IGNORECASE)),
    ("promotion disclaimer box", re.compile(r"\bNo automatic promotion from defect minimization\b", re.IGNORECASE)),
    ("repetitive status stamp", re.compile(r"\*\*Mathematical status\.\*\*.*\*\*Contribution status\.\*\*")),
    ("in-house estate header", re.compile(r"\b(?:Sovereign Mathematical Scope|Relative Path in Estate|Modular Delegation|Repository of Record)\b")),
    ("naked in-house paper number", re.compile(r"\bPapers?\s+0\d{2}\b")),
    ("unformatted ASCII math B-transpose", re.compile(r"\bB-transpose\b")),
]

# Mathematical symbol extraction pattern
RE_MATH_SYMBOLS = re.compile(
    r"(\\operatorname\{[a-zA-Z]+\}|\\mathcal\{[a-zA-Z]+\}|\\[a-zA-Z]+|\b[A-Za-z]\b|[=<>+\-*/^_&|~#]+)"
)


def compute_sha256(text: str) -> str:
    """Compute standard SHA-256 hex digest of a UTF-8 string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def compute_location_sha256(
    file_path: str,
    start_line: int,
    end_line: int,
    start_byte: Optional[int],
    end_byte: Optional[int],
    content_sha256: str,
) -> str:
    """Compute deterministic SHA-256 binding file path, line numbers, byte offsets, and content digest."""
    sb = start_byte if start_byte is not None else -1
    eb = end_byte if end_byte is not None else -1
    return compute_sha256(f"{file_path}:{start_line}:{end_line}:{sb}:{eb}:{content_sha256}")


def normalize_latex(latex: str) -> str:
    """Normalize LaTeX formula string by collapsing whitespace and normalizing delimiters."""
    s = latex.strip()
    # Strip enclosing math delimiters
    if s.startswith("$$") and s.endswith("$$"):
        s = s[2:-2].strip()
    elif s.startswith("$") and s.endswith("$") and not s.startswith("$$"):
        s = s[1:-1].strip()
    elif s.startswith(r"\[") and s.endswith(r"\]"):
        s = s[2:-2].strip()
    elif s.startswith(r"\(") and s.endswith(r"\)"):
        s = s[2:-2].strip()
    
    # Normalize multiple whitespace to single space
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_text(text: str) -> str:
    """Normalize prose text for stable content hashing."""
    s = re.sub(r"\s+", " ", text.strip())
    return s


def extract_math_symbols(latex: str) -> List[str]:
    """Extract distinct mathematical operator and symbol tokens from LaTeX."""
    tokens = set()
    for match in RE_MATH_SYMBOLS.finditer(latex):
        token = match.group(0).strip()
        if len(token) > 0 and token not in ("{", "}", "(", ")", "[", "]", ","):
            tokens.add(token)
    return sorted(tokens)


def derive_formula_uuid(normalized_latex: str, formula_type: FormulaType, context_index: int) -> uuid.UUID:
    """Generate deterministic UUIDv5 for a mathematical formula."""
    key = f"formula:{formula_type.value}:{context_index}:{normalized_latex}"
    return uuid.uuid5(COMPOSITION_NAMESPACE, key)


def derive_claim_uuid(label: str, normalized_statement: str) -> uuid.UUID:
    """Generate deterministic UUIDv5 for a formal claim."""
    key = f"claim:{label.lower().strip()}:{normalized_statement}"
    return uuid.uuid5(COMPOSITION_NAMESPACE, key)


def derive_line_uuid(line_num: int, line_sha256: str) -> uuid.UUID:
    """Generate deterministic UUIDv5 for a prose line."""
    key = f"line:{line_num}:{line_sha256}"
    return uuid.uuid5(COMPOSITION_NAMESPACE, key)


class PaperCompositionExtractor:
    """Exhaustive parser and alignment engine across MD, TeX, and PDF."""

    def __init__(self, paper_dir: Path):
        self.paper_dir = paper_dir.resolve()

        # Dynamically discover primary markdown manuscript file
        md_candidates = [
            f for f in self.paper_dir.glob("*.md")
            if not f.name.startswith("README")
            and not f.name.endswith("_change_log.md")
            and not f.name.endswith("_claim_ledger.md")
        ]
        if not md_candidates:
            raise FileNotFoundError(f"No primary markdown manuscript found in {self.paper_dir}")

        if len(md_candidates) == 1:
            self.md_path = md_candidates[0]
        else:
            matching = [f for f in md_candidates if f.stem in self.paper_dir.name or self.paper_dir.name.endswith(f.stem)]
            self.md_path = matching[0] if matching else max(md_candidates, key=lambda f: f.stat().st_size)

        stem = self.md_path.stem
        self.tex_path = self.paper_dir / f"{stem}.tex"
        self.pdf_path = self.paper_dir / f"{stem}.pdf"

        yaml_ledger = self.paper_dir / f"{stem}_claim_ledger.yaml"
        md_ledger = self.paper_dir / f"{stem}_claim_ledger.md"
        if yaml_ledger.exists():
            self.claim_ledger_path = yaml_ledger
        elif md_ledger.exists():
            self.claim_ledger_path = md_ledger
        else:
            candidates = (
                list(self.paper_dir.glob("*_claim_ledger.yaml"))
                or list(self.paper_dir.glob("*_claim_ledger.md"))
                or list(self.paper_dir.glob("claim_ledger.yaml"))
                or list(self.paper_dir.glob("claim_ledger.md"))
            )
            if not candidates and (self.paper_dir / "papers").is_dir():
                candidates = (
                    list((self.paper_dir / "papers").glob("*_claim_ledger.yaml"))
                    or list((self.paper_dir / "papers").glob("*_claim_ledger.md"))
                )
            self.claim_ledger_path = candidates[0] if candidates else yaml_ledger

        self.lean_dir = self.paper_dir / "lean4"
        self.code_dir = self.paper_dir / "code"

        if not self.md_path.exists():
            raise FileNotFoundError(f"Markdown manuscript not found at {self.md_path}")

        self._last_dialect_warnings: List[str] = []

    def extract_from_markdown(self) -> Tuple[List[MathFormulaEntry], List[ProseClaimEntry], List[ProseLineEntry], List[str]]:
        """Extract all math formulas, formal claims, and hashed prose lines from Markdown."""
        md_text = self.md_path.read_text(encoding="utf-8")
        raw_lines_keepends = md_text.splitlines(keepends=True)
        lines = md_text.splitlines()

        # Precompute 0-indexed UTF-8 start and end byte offsets for each 1-indexed line
        line_start_bytes: List[int] = []
        line_end_bytes: List[int] = []
        running_bytes = 0
        for idx, raw_l in enumerate(raw_lines_keepends):
            line_start_bytes.append(running_bytes)
            clean_l = lines[idx] if idx < len(lines) else raw_l.rstrip("\r\n")
            line_end_bytes.append(running_bytes + len(clean_l.encode("utf-8")))
            running_bytes += len(raw_l.encode("utf-8"))
        if not line_start_bytes:
            line_start_bytes = [0]
            line_end_bytes = [0]

        formulas: List[MathFormulaEntry] = []
        claims: List[ProseClaimEntry] = []
        prose_lines: List[ProseLineEntry] = []
        hygiene_warnings: List[str] = []
        dialect_warnings: List[str] = []

        current_section = ""
        in_display_math = False
        display_math_delim = ""
        display_math_buffer: List[str] = []
        display_math_start = 0
        in_code_block = False
        in_frontmatter = False

        # Pattern for formal claim headers:
        # 1. Blockquote or bold: > **[STATUS] Theorem 5.1 (Title).** Statement
        # 2. Direct bold: **Proposition E.6 (Title).** Statement
        # 3. Markdown heading: ### Theorem 5.1 (Title)
        re_claim_header = re.compile(
            r"^(?:>\s*)?(?:(#{2,4})\s+)?\*\*(?:\[([^\]]+)\]\s*)?(Theorem|Proposition|Lemma|Corollary|Definition|Remark|Conjecture|Axiom)\s+([A-Za-z0-9.\-]+)(?:\s*\((.*?)\))?\.?\*\*\s*(.*)",
            re.IGNORECASE
        )
        re_claim_heading = re.compile(
            r"^(#{2,4})\s+(?:[0-9.]+\s+)?(Theorem|Proposition|Lemma|Corollary|Definition|Remark|Conjecture|Axiom)\s+([A-Za-z0-9.\-]+)(?:\s*\((.*?)\))?\.?\s*(.*)",
            re.IGNORECASE
        )
        re_rel_md_link = re.compile(r"\]\((?!https?:|mailto:|#)([^)]+\.md(?:#[^)]*)?)\)")

        in_claim = False
        claim_start_line = 0
        claim_type = ClaimType.THEOREM
        claim_label = ""
        claim_title = ""
        claim_text_buffer: List[str] = []

        in_references = False
        formula_counter = 0

        def _make_md_anchor(
            start_ln: int,
            end_ln: int,
            env: str,
            content_sha: str,
            start_ch: Optional[int] = None,
            end_ch: Optional[int] = None,
        ) -> LocationAnchor:
            sb = line_start_bytes[start_ln - 1]
            eb = line_end_bytes[end_ln - 1]
            if start_ch is not None and start_ln == end_ln:
                line_str = lines[start_ln - 1]
                sb = line_start_bytes[start_ln - 1] + len(line_str[:start_ch].encode("utf-8"))
                eb = line_start_bytes[start_ln - 1] + len(line_str[: (end_ch or len(line_str))].encode("utf-8"))
            loc_sha = compute_location_sha256(self.md_path.name, start_ln, end_ln, sb, eb, content_sha)
            return LocationAnchor(
                file_type="md",
                file_path=self.md_path.name,
                start_line=start_ln,
                end_line=end_ln,
                start_char=start_ch,
                end_char=end_ch,
                start_byte_offset=sb,
                end_byte_offset=eb,
                location_sha256=loc_sha,
                environment=env,
            )

        for line_idx, line in enumerate(lines, start=1):
            line_hash = compute_sha256(line)
            prose_lines.append(ProseLineEntry(
                uuid=derive_line_uuid(line_idx, line_hash),
                line_number_md=line_idx,
                section_header=current_section,
                raw_line=line,
                sha256=line_hash,
                is_claim_boundary=False,
            ))

            stripped = line.strip()
            if line_idx == 1 and stripped == "---":
                in_frontmatter = True
                continue
            elif in_frontmatter:
                if stripped in ("---", "..."):
                    in_frontmatter = False
                continue

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            # Check section header
            if line.startswith("#"):
                current_section = line.strip("# ").strip()
                if re.search(r"\b(references|bibliography)\b", current_section, re.IGNORECASE):
                    in_references = True
                elif in_references and re.match(r"^#{1,2}\s+", line):
                    in_references = False

            if re.search(r"\\begin\{(thebibliography)\}", line, re.IGNORECASE):
                in_references = True
            elif re.search(r"\\end\{(thebibliography)\}", line, re.IGNORECASE):
                in_references = False

            # Claim hygiene & dialect check (exempt references / bibliography)
            if not in_references:
                for match in RE_FORBIDDEN.finditer(line):
                    hygiene_warnings.append(
                        f"Line {line_idx} contains forbidden word '{match.group(0)}' in: {line.strip()[:100]}"
                    )
                for pat_name, pat_re in INHOUSE_AND_OVERGUARDED_PATTERNS:
                    for m_pat in pat_re.finditer(line):
                        dialect_warnings.append(
                            f"{self.md_path.name}:{line_idx} contains {pat_name} ('{m_pat.group(0)}') in: {line.strip()[:100]}"
                        )
                for m_link in re_rel_md_link.finditer(line):
                    dialect_warnings.append(
                        f"{self.md_path.name}:{line_idx} contains relative .md link '{m_link.group(1)}' that breaks in standalone PDF"
                    )

            unquoted = re.sub(r"^(?:>\s*)+", "", line).strip()

            # Check for multi-line display math blocks $$ ... $$ or \[ ... \]
            if in_display_math:
                if (display_math_delim == "$$" and unquoted == "$$") or (display_math_delim == r"\[" and unquoted == r"\]"):
                    raw_latex = "\n".join(display_math_buffer)
                    norm_latex = normalize_latex(raw_latex)
                    formula_counter += 1
                    f_uuid = derive_formula_uuid(norm_latex, FormulaType.DISPLAY, formula_counter)
                    sha_raw = compute_sha256(raw_latex)
                    sha_norm = compute_sha256(norm_latex)
                    env_name = "display_dollar" if display_math_delim == "$$" else "display_bracket"
                    formulas.append(MathFormulaEntry(
                        uuid=f_uuid,
                        formula_type=FormulaType.DISPLAY,
                        raw_latex=raw_latex,
                        normalized_latex=norm_latex,
                        sha256_raw=sha_raw,
                        sha256_normalized=sha_norm,
                        md_location=_make_md_anchor(display_math_start, line_idx, env_name, sha_norm),
                        ast_symbols=extract_math_symbols(norm_latex),
                        surrounding_prose_context=lines[display_math_start - 2] if display_math_start > 1 else "",
                    ))
                    in_display_math = False
                    display_math_delim = ""
                    display_math_buffer = []
                else:
                    display_math_buffer.append(re.sub(r"^(?:>\s*)+", "", line))
                continue
            elif unquoted in ("$$", r"\["):
                in_display_math = True
                display_math_delim = unquoted
                display_math_start = line_idx
                display_math_buffer = []
                continue
            elif (unquoted.startswith("$$") and unquoted.endswith("$$") and len(unquoted) > 4) or (
                unquoted.startswith(r"\[") and unquoted.endswith(r"\]") and len(unquoted) > 4
            ):
                # Single-line display math
                is_dollar = unquoted.startswith("$$")
                raw_latex = unquoted[2:-2].strip()
                norm_latex = normalize_latex(raw_latex)
                formula_counter += 1
                f_uuid = derive_formula_uuid(norm_latex, FormulaType.DISPLAY, formula_counter)
                sha_raw = compute_sha256(raw_latex)
                sha_norm = compute_sha256(norm_latex)
                env_name = "display_dollar_single" if is_dollar else "display_bracket_single"
                formulas.append(MathFormulaEntry(
                    uuid=f_uuid,
                    formula_type=FormulaType.DISPLAY,
                    raw_latex=raw_latex,
                    normalized_latex=norm_latex,
                    sha256_raw=sha_raw,
                    sha256_normalized=sha_norm,
                    md_location=_make_md_anchor(line_idx, line_idx, env_name, sha_norm, 0, len(line)),
                    ast_symbols=extract_math_symbols(norm_latex),
                    surrounding_prose_context=line,
                ))
                continue

            # Check for formal claim headers (bold/blockquote or heading)
            m_claim = re_claim_header.match(stripped)
            m_heading = re_claim_heading.match(stripped) if not m_claim else None

            if m_claim or m_heading:
                # Flush previous claim if active
                if in_claim and claim_text_buffer:
                    full_stmt = "\n".join(claim_text_buffer).strip()
                    norm_stmt = normalize_text(full_stmt)
                    c_uuid = derive_claim_uuid(claim_label, norm_stmt)
                    sha_stmt = compute_sha256(full_stmt)
                    claims.append(ProseClaimEntry(
                        uuid=c_uuid,
                        claim_type=claim_type,
                        label=claim_label,
                        title=claim_title if claim_title else None,
                        statement_text=full_stmt,
                        normalized_text=norm_stmt,
                        sha256_statement=sha_stmt,
                        md_location=_make_md_anchor(claim_start_line, line_idx - 1, claim_type.value, sha_stmt),
                        claim_hygiene_flags=[] if in_references else [
                            w for w in FORBIDDEN_WORDS if re.search(r"\b" + re.escape(w) + r"\b", full_stmt, re.I)
                        ],
                    ))
                    claim_text_buffer = []

                in_claim = True
                claim_start_line = line_idx

                if m_claim:
                    raw_type = m_claim.group(3).lower()
                    claim_type = ClaimType(raw_type) if raw_type in [ct.value for ct in ClaimType] else ClaimType.THEOREM
                    claim_num = m_claim.group(4)
                    claim_label = f"{m_claim.group(3)} {claim_num}"
                    claim_title = m_claim.group(5) or ""
                    rest = m_claim.group(6).strip()
                else:
                    raw_type = m_heading.group(2).lower()
                    claim_type = ClaimType(raw_type) if raw_type in [ct.value for ct in ClaimType] else ClaimType.THEOREM
                    claim_num = m_heading.group(3)
                    claim_label = f"{m_heading.group(2)} {claim_num}"
                    claim_title = m_heading.group(4) or ""
                    rest = m_heading.group(5).strip()

                if rest:
                    claim_text_buffer.append(rest)
                continue
            elif in_claim:
                # Termination conditions for claim statement:
                # 1. Next header (##)
                # 2. Proof block (**Proof** / *Proof.*)
                if (
                    line.startswith("#")
                    or stripped.startswith("**Proof")
                    or stripped.startswith("*Proof")
                    or stripped.startswith("Proof:")
                    or stripped.startswith("Proof.")
                ):
                    full_stmt = "\n".join(claim_text_buffer).strip()
                    norm_stmt = normalize_text(full_stmt)
                    c_uuid = derive_claim_uuid(claim_label, norm_stmt)
                    sha_stmt = compute_sha256(full_stmt)
                    claims.append(ProseClaimEntry(
                        uuid=c_uuid,
                        claim_type=claim_type,
                        label=claim_label,
                        title=claim_title if claim_title else None,
                        statement_text=full_stmt,
                        normalized_text=norm_stmt,
                        sha256_statement=sha_stmt,
                        md_location=_make_md_anchor(claim_start_line, line_idx - 1, claim_type.value, sha_stmt),
                        claim_hygiene_flags=[] if in_references else [
                            w for w in FORBIDDEN_WORDS if re.search(r"\b" + re.escape(w) + r"\b", full_stmt, re.I)
                        ],
                    ))
                    in_claim = False
                    claim_text_buffer = []
                else:
                    claim_text_buffer.append(line.lstrip("> "))

            # Extract inline display math \[...\] or $$...$$ embedded within a prose/table line
            re_inline_disp = re.compile(r"(?:\\\[(.*?)\\\]|\$\$(.+?)\$\$)")
            for m_id in re_inline_disp.finditer(line):
                raw_id = (m_id.group(1) if m_id.group(1) is not None else m_id.group(2)).strip()
                if raw_id:
                    norm_id = normalize_latex(raw_id)
                    formula_counter += 1
                    f_uuid = derive_formula_uuid(norm_id, FormulaType.DISPLAY, formula_counter)
                    sha_raw = compute_sha256(raw_id)
                    sha_norm = compute_sha256(norm_id)
                    formulas.append(MathFormulaEntry(
                        uuid=f_uuid,
                        formula_type=FormulaType.DISPLAY,
                        raw_latex=raw_id,
                        normalized_latex=norm_id,
                        sha256_raw=sha_raw,
                        sha256_normalized=sha_norm,
                        md_location=_make_md_anchor(line_idx, line_idx, "display_inline", sha_norm, m_id.start(), m_id.end()),
                        ast_symbols=extract_math_symbols(norm_id),
                        surrounding_prose_context=line.strip(),
                    ))

            # Extract inline math $...$ and \(...\) outside of display math
            re_inline = re.compile(r"(?:(?<!\\)\$(?!\$)(.+?)(?<!\\)\$|\\\((.+?)\\\))")
            for m_in in re_inline.finditer(line):
                raw_in = (m_in.group(1) if m_in.group(1) is not None else m_in.group(2)).strip()
                env_in = "inline_dollar" if m_in.group(1) is not None else "inline_paren"
                if raw_in and not raw_in.isdigit():
                    norm_in = normalize_latex(raw_in)
                    formula_counter += 1
                    f_uuid = derive_formula_uuid(norm_in, FormulaType.INLINE, formula_counter)
                    sha_raw = compute_sha256(raw_in)
                    sha_norm = compute_sha256(norm_in)
                    formulas.append(MathFormulaEntry(
                        uuid=f_uuid,
                        formula_type=FormulaType.INLINE,
                        raw_latex=raw_in,
                        normalized_latex=norm_in,
                        sha256_raw=sha_raw,
                        sha256_normalized=sha_norm,
                        md_location=_make_md_anchor(line_idx, line_idx, env_in, sha_norm, m_in.start(), m_in.end()),
                        ast_symbols=extract_math_symbols(norm_in),
                        surrounding_prose_context=line.strip(),
                    ))

        # Flush final claim if still open
        if in_claim and claim_text_buffer:
            full_stmt = "\n".join(claim_text_buffer).strip()
            norm_stmt = normalize_text(full_stmt)
            c_uuid = derive_claim_uuid(claim_label, norm_stmt)
            sha_stmt = compute_sha256(full_stmt)
            claims.append(ProseClaimEntry(
                uuid=c_uuid,
                claim_type=claim_type,
                label=claim_label,
                title=claim_title if claim_title else None,
                statement_text=full_stmt,
                normalized_text=norm_stmt,
                sha256_statement=sha_stmt,
                md_location=_make_md_anchor(claim_start_line, max(claim_start_line, len(lines)), claim_type.value, sha_stmt),
                claim_hygiene_flags=[] if in_references else [
                    w for w in FORBIDDEN_WORDS if re.search(r"\b" + re.escape(w) + r"\b", full_stmt, re.I)
                ],
            ))

        self._last_dialect_warnings = dialect_warnings
        return formulas, claims, prose_lines, hygiene_warnings

    def extract_from_tex(self) -> Dict[str, Dict[str, Any]]:
        """Extract display and inline math environments from LaTeX source with line and byte offsets."""
        if not self.tex_path.exists():
            return {}

        tex_content = self.tex_path.read_text(encoding="utf-8")
        tex_entries: Dict[str, Dict[str, Any]] = {}

        def _record_tex_entry(key: str, env_name: str, body: str, m_start: int, m_end: int) -> None:
            norm = normalize_latex(body)
            if not norm:
                return
            start_line = tex_content[:m_start].count("\n") + 1
            end_line = tex_content[:m_end].count("\n") + 1
            sb = len(tex_content[:m_start].encode("utf-8"))
            eb = len(tex_content[:m_end].encode("utf-8"))
            sha = compute_sha256(norm)
            loc_sha = compute_location_sha256(self.tex_path.name, start_line, end_line, sb, eb, sha)
            entry = {
                "environment": env_name,
                "raw": body,
                "start_line": start_line,
                "end_line": end_line,
                "start_byte_offset": sb,
                "end_byte_offset": eb,
                "location_sha256": loc_sha,
                "sha256": sha,
            }
            if key not in tex_entries:
                tex_entries[key] = entry

        # 1. \begin{equation|align|gather}*? ... \end{...}
        re_tex_env = re.compile(r"\\begin\{(equation|align|gather)\*?\}(.*?)\\end\{\1\*?\}", re.DOTALL)
        for m in re_tex_env.finditer(tex_content):
            body = m.group(2).strip()
            norm = normalize_latex(body)
            _record_tex_entry(norm, m.group(1), body, m.start(), m.end())

        # 2. \[ ... \] (use (?<!\\) so LaTeX linebreaks \\[4pt] are not mistaken for \[)
        re_tex_bracket = re.compile(r"(?<!\\)\\\[(.*?)(?<!\\)\\\]", re.DOTALL)
        for m in re_tex_bracket.finditer(tex_content):
            body = m.group(1).strip()
            norm = normalize_latex(body)
            _record_tex_entry(norm, "display_bracket", body, m.start(), m.end())

        # 3. $$ ... $$
        re_tex_dollar_disp = re.compile(r"(?<!\\)\$\$(.*?)(?<!\\)\$\$", re.DOTALL)
        for m in re_tex_dollar_disp.finditer(tex_content):
            body = m.group(1).strip()
            norm = normalize_latex(body)
            _record_tex_entry(norm, "display_dollar", body, m.start(), m.end())

        # 4. Inline math \( ... \) and $ ... $
        re_tex_inline = re.compile(r"(?:(?<!\\)\\\((.+?)(?<!\\)\\\)|(?<!\\)\$(?!\$)([^$\n]+?)(?<!\\)\$)")
        for m in re_tex_inline.finditer(tex_content):
            body = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
            env_in = "inline_paren" if m.group(1) is not None else "inline_dollar"
            norm = normalize_latex(body)
            _record_tex_entry(f"inline:{norm}", env_in, body, m.start(), m.end())

        return tex_entries

    def extract_from_pdf(self) -> Dict[int, str]:
        """Extract text from PDF page by page."""
        if not self.pdf_path.exists():
            return {}

        pages: Dict[int, str] = {}

        if HAVE_PYMUPDF:
            doc = fitz.open(str(self.pdf_path))
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pages[page_num + 1] = page.get_text()
            doc.close()
        elif HAVE_PYPDF:
            reader = pypdf.PdfReader(str(self.pdf_path))
            for page_num, page in enumerate(reader.pages, start=1):
                pages[page_num] = page.extract_text() or ""

        return pages

    def link_code_and_proofs(
        self, formulas: List[MathFormulaEntry], claims: List[ProseClaimEntry]
    ) -> Tuple[List[MathFormulaEntry], List[ProseClaimEntry], float, float]:
        """Link formulas and claims to Python code implementations and Lean 4 proofs,
        populating claim ledger IDs, referenced formula UUIDs, and code/proof bindings."""
        # Check claim ledger for registered mappings
        ledger_claims: List[Dict[str, Any]] = []
        if self.claim_ledger_path.exists():
            try:
                ledger_data = yaml.safe_load(self.claim_ledger_path.read_text(encoding="utf-8"))
                ledger_claims = ledger_data.get("claims", [])
            except Exception:
                pass

        # Scan Lean 4 files
        lean_declarations: Set[str] = set()
        if self.lean_dir.exists():
            for f in self.lean_dir.glob("*.lean"):
                try:
                    text = f.read_text(encoding="utf-8")
                    for m in re.finditer(r"\b(theorem|def|lemma)\s+([a-zA-Z0-9_']+)", text):
                        lean_declarations.add(f"lean4/{f.name}:{m.group(2)}")
                except Exception:
                    pass

        # Scan Python code files
        code_functions: Set[str] = set()
        if self.code_dir.exists():
            for f in self.code_dir.glob("*.py"):
                try:
                    text = f.read_text(encoding="utf-8")
                    for m in re.finditer(r"def\s+([a-zA-Z0-9_]+)\(", text):
                        code_functions.add(f"code/{f.name}:{m.group(1)}")
                except Exception:
                    pass

        # Helper to match claim to ledger
        def match_ledger(claim: ProseClaimEntry) -> Optional[Dict[str, Any]]:
            lbl = claim.label.strip()
            parts = lbl.split()
            kind = parts[0] if len(parts) > 0 else ""
            num = parts[1] if len(parts) > 1 else ""
            for lc in ledger_claims:
                heading = (lc.get("paper_pointer") or {}).get("heading", "")
                title = lc.get("title", "")
                slug = lc.get("slug", "")
                if re.search(r"\b" + re.escape(lbl) + r"\b", heading, re.I) or re.search(r"\b" + re.escape(lbl) + r"\b", title, re.I):
                    return lc
            if num:
                for lc in ledger_claims:
                    title = lc.get("title", "")
                    slug = lc.get("slug", "")
                    if re.search(r"\b" + re.escape(num) + r"\b", title):
                        return lc
                    m_range = re.search(r"([A-Za-z0-9.]+)\s*--\s*([A-Za-z0-9.]+)", title)
                    if m_range:
                        start_r, end_r = m_range.group(1), m_range.group(2)
                        if start_r.startswith("E.") and end_r.startswith("E.") and num.startswith("E."):
                            try:
                                n_val = int(num.split(".")[1])
                                s_val = int(start_r.split(".")[1])
                                e_val = int(end_r.split(".")[1])
                                if s_val <= n_val <= e_val:
                                    return lc
                            except Exception:
                                pass
                    if "axiom" in kind.lower() and (re.search(r"\b" + re.escape(num) + r"\b", title, re.I) or re.search(r"\b" + re.escape(num) + r"\b", slug, re.I)):
                        return lc
            return None

        # Build updated claims with referenced_formula_uuids and claim_ledger_id
        updated_claims: List[ProseClaimEntry] = []
        formula_to_claim_map: Dict[uuid.UUID, ProseClaimEntry] = {}

        for claim in claims:
            encompassed_f = [
                f for f in formulas
                if claim.md_location and f.md_location and claim.md_location.start_line <= f.md_location.start_line <= claim.md_location.end_line
            ]
            ref_uuids = [f.uuid for f in encompassed_f]

            lc = match_ledger(claim)
            ledger_id = (lc.get("claim_id") or lc.get("id")) if lc else None

            c_code_bindings: List[str] = []
            c_lean_bindings: List[str] = []

            if lc:
                for ev in lc.get("evidence", []):
                    loc = ev.get("file_location") or ev.get("module_path")
                    if loc:
                        if "lean" in loc or loc.endswith(".lean"):
                            if loc not in c_lean_bindings:
                                c_lean_bindings.append(loc)
                        else:
                            if loc not in c_code_bindings:
                                c_code_bindings.append(loc)
                lean_info = lc.get("lean4")
                if isinstance(lean_info, dict):
                    mod = lean_info.get("module")
                    if mod:
                        loc = f"lean4/{mod}.lean"
                        if loc not in c_lean_bindings:
                            c_lean_bindings.append(loc)
                code_ev = lc.get("code_evidence")
                if isinstance(code_ev, dict):
                    for test_ref in code_ev.get("tests", []):
                        if isinstance(test_ref, str) and test_ref:
                            clean_ref = test_ref.split("::")[0]
                            if clean_ref not in c_code_bindings:
                                c_code_bindings.append(clean_ref)

            label_clean = claim.label.lower().replace(" ", "").replace(".", "_")
            for lean_decl in lean_declarations:
                if label_clean and label_clean in lean_decl.lower() and lean_decl not in c_lean_bindings:
                    c_lean_bindings.append(lean_decl)

            up_claim = claim.model_copy(update={
                "referenced_formula_uuids": ref_uuids,
                "claim_ledger_id": ledger_id,
                "code_bindings": c_code_bindings,
                "lean_bindings": c_lean_bindings,
            })
            updated_claims.append(up_claim)

            for f in encompassed_f:
                formula_to_claim_map[f.uuid] = up_claim

        # Update formulas with bindings inherited from the enclosing claim ledger evidence.
        updated_formulas: List[MathFormulaEntry] = []
        for formula in formulas:
            f_code = list(formula.code_bindings)
            f_lean = list(formula.lean_bindings)

            parent_claim = formula_to_claim_map.get(formula.uuid)
            if parent_claim:
                for cb in parent_claim.code_bindings:
                    if cb not in f_code:
                        f_code.append(cb)
                for lb in parent_claim.lean_bindings:
                    if lb not in f_lean:
                        f_lean.append(lb)

            up_formula = formula.model_copy(update={
                "code_bindings": f_code,
                "lean_bindings": f_lean,
            })
            updated_formulas.append(up_formula)

        code_cov = round(len([f for f in updated_formulas if f.code_bindings]) / max(1, len(updated_formulas)), 3)
        lean_cov = round(len([c for c in updated_claims if c.lean_bindings]) / max(1, len(updated_claims)), 3)
        return updated_formulas, updated_claims, code_cov, lean_cov

    def cross_check_formats(
        self,
        formulas: List[MathFormulaEntry],
        claims: List[ProseClaimEntry],
        tex_entries: Dict[str, Dict[str, Any]],
        pdf_pages: Dict[int, str],
    ) -> List[FormatCrossCheck]:
        """Cross-check formulas and claims across Markdown, TeX, and PDF."""
        cross_checks: List[FormatCrossCheck] = []

        for formula in formulas:
            if formula.formula_type != FormulaType.DISPLAY:
                continue
            norm = formula.normalized_latex
            tex_match = tex_entries.get(norm)
            tex_hash = tex_match["sha256"] if tex_match else None
            exact = bool(tex_hash) and tex_hash == formula.sha256_normalized
            pdf_found = bool(norm) and any(norm in page_text for page_text in pdf_pages.values())
            cross_checks.append(FormatCrossCheck(
                item_uuid=formula.uuid,
                item_type="formula",
                md_sha256=formula.sha256_normalized,
                tex_sha256=tex_hash,
                pdf_matched=pdf_found,
                status=AlignmentStatus.EXACT_MATCH if exact else AlignmentStatus.UNMATCHED,
                drift_notes=None if exact else "TeX normalized hash does not equal the Markdown formula hash",
            ))

        for claim in claims:
            pdf_found = bool(claim.label) and any(claim.label in page_text for page_text in pdf_pages.values())
            cross_checks.append(FormatCrossCheck(
                item_uuid=claim.uuid,
                item_type="claim",
                md_sha256=claim.sha256_statement,
                tex_sha256=None,
                pdf_matched=pdf_found,
                status=AlignmentStatus.UNMATCHED,
                drift_notes=(
                    "PDF text contains the claim label; the statement was not hashed against TeX or PDF"
                    if pdf_found else
                    "Claim statement was not hashed against TeX or PDF"
                ),
            ))

        return cross_checks

    def attach_cross_format_locations(
        self,
        formulas: List[MathFormulaEntry],
        claims: List[ProseClaimEntry],
        tex_entries: Dict[str, Dict[str, Any]],
        pdf_pages: Dict[int, str],
    ) -> Tuple[List[MathFormulaEntry], List[ProseClaimEntry]]:
        """Attach tex_location and pdf_location anchors with byte/char offsets and location_sha256."""
        updated_formulas: List[MathFormulaEntry] = []
        for formula in formulas:
            norm = formula.normalized_latex
            tex_key = norm if formula.formula_type == FormulaType.DISPLAY else f"inline:{norm}"
            tex_match = tex_entries.get(tex_key) or tex_entries.get(norm)
            tex_loc: Optional[LocationAnchor] = None
            if tex_match:
                tex_loc = LocationAnchor(
                    file_type="tex",
                    file_path=self.tex_path.name,
                    start_line=tex_match["start_line"],
                    end_line=tex_match["end_line"],
                    start_byte_offset=tex_match.get("start_byte_offset"),
                    end_byte_offset=tex_match.get("end_byte_offset"),
                    location_sha256=tex_match.get("location_sha256"),
                    environment=tex_match.get("environment"),
                )

            pdf_loc: Optional[PdfLocationAnchor] = None
            if norm:
                for page_num, page_text in pdf_pages.items():
                    idx = page_text.find(norm)
                    if idx >= 0:
                        ctx = page_text[max(0, idx - 40) : idx + len(norm) + 40].replace("\n", " ").strip()
                        pdf_loc = PdfLocationAnchor(
                            page_number=page_num,
                            char_offset=idx,
                            location_sha256=compute_sha256(f"{page_num}:{idx}:{norm}"),
                            matched_snippet=norm,
                            surrounding_context=ctx,
                        )
                        break

            updated_formulas.append(
                formula.model_copy(update={"tex_location": tex_loc, "pdf_location": pdf_loc})
            )

        updated_claims: List[ProseClaimEntry] = []
        for claim in claims:
            pdf_loc = None
            if claim.label:
                for page_num, page_text in pdf_pages.items():
                    idx = page_text.find(claim.label)
                    if idx >= 0:
                        ctx = page_text[max(0, idx - 40) : idx + len(claim.label) + 80].replace("\n", " ").strip()
                        pdf_loc = PdfLocationAnchor(
                            page_number=page_num,
                            char_offset=idx,
                            location_sha256=compute_sha256(f"{page_num}:{idx}:{claim.label}"),
                            matched_snippet=claim.label,
                            surrounding_context=ctx,
                        )
                        break
            updated_claims.append(claim.model_copy(update={"pdf_location": pdf_loc}))

        return updated_formulas, updated_claims

    def audit_dialect_and_identity(
        self, pdf_pages: Dict[int, str]
    ) -> Tuple[List[str], Dict[str, Any], str, str]:
        """Audit in-house dialect warnings across package surfaces and verify author/date/version parity."""
        dialect_warnings = list(self._last_dialect_warnings)

        # Scan README.md, docs/descriptions.md, *_claim_ledger.md, and *_change_log.md for in-house jargon / courtroom boilerplate
        extra_md_files = [
            self.paper_dir / "README.md",
            self.paper_dir / "docs" / "descriptions.md",
            *sorted(self.paper_dir.glob("*_claim_ledger.md")),
            *sorted(self.paper_dir.glob("*_change_log.md")),
        ]
        for extra_f in extra_md_files:
            if extra_f.is_file():
                rel_name = extra_f.relative_to(self.paper_dir).as_posix()
                for ln_idx, ln in enumerate(extra_f.read_text(encoding="utf-8").splitlines(), start=1):
                    for pat_name, pat_re in INHOUSE_AND_OVERGUARDED_PATTERNS:
                        for m_pat in pat_re.finditer(ln):
                            dialect_warnings.append(
                                f"{rel_name}:{ln_idx} contains {pat_name} ('{m_pat.group(0)}') in: {ln.strip()[:100]}"
                            )

        zenodo_path = self.paper_dir / "zenodo_metadata.json"
        zenodo_data: Dict[str, Any] = {}
        if zenodo_path.is_file():
            raw_z = zenodo_path.read_text(encoding="utf-8")
            try:
                zenodo_data = json.loads(raw_z)
            except Exception:
                pass
            for ln_idx, ln in enumerate(raw_z.splitlines(), start=1):
                for pat_name, pat_re in INHOUSE_AND_OVERGUARDED_PATTERNS:
                    for m_pat in pat_re.finditer(ln):
                        dialect_warnings.append(
                            f"zenodo_metadata.json:{ln_idx} contains {pat_name} ('{m_pat.group(0)}') in: {ln.strip()[:100]}"
                        )

        # Extract title, version, date, and author from Markdown
        md_lines = self.md_path.read_text(encoding="utf-8").splitlines()[:60]
        paper_title = self.md_path.stem.replace("_", " ").title()
        md_version: Optional[str] = None
        md_date: Optional[str] = None
        md_author: Optional[str] = None

        in_fm = False
        for idx, line in enumerate(md_lines):
            s = line.strip()
            if idx == 0 and s == "---":
                in_fm = True
                continue
            if in_fm:
                if s in ("---", "..."):
                    in_fm = False
                    continue
                if s.lower().startswith("title:"):
                    val = s.split(":", 1)[1].strip().strip("\"'")
                    if val and val not in ("|", ">"):
                        paper_title = val
                elif s.lower().startswith("version:"):
                    val = s.split(":", 1)[1].strip().strip("\"'")
                    if val and val not in ("|", ">"):
                        md_version = val
                elif s.lower().startswith("date:"):
                    val = s.split(":", 1)[1].strip().strip("\"'")
                    if val and val not in ("|", ">"):
                        m_dt = re.search(r"(\d{4}-\d{2}-\d{2})", val)
                        md_date = m_dt.group(1) if m_dt else val
                elif s.lower().startswith("author:"):
                    val = s.split(":", 1)[1].strip().strip("\"'")
                    if val and val not in ("|", ">"):
                        md_author = val
                else:
                    if not md_date:
                        m_dt = re.search(r"(\d{4}-\d{2}-\d{2})", s)
                        if m_dt:
                            md_date = m_dt.group(1)
                    if not md_version:
                        m_vr = re.search(r"[vV]ersion[:\s]+([vV]?[0-9]+\.[0-9]+(?:\.[0-9]+)?)", s)
                        if m_vr:
                            md_version = m_vr.group(1)
                continue

            if line.startswith("# ") and paper_title == self.md_path.stem.replace("_", " ").title():
                paper_title = line[2:].strip()

            m_ver = re.search(r"(?:\*\*Version:?\*\*|\|\s*\*\*Version\*\*\s*\|)\s*([vV]?[0-9]+\.[0-9]+(?:\.[0-9]+)?(?:\s*[A-Za-z\-]+)?)", line)
            if m_ver and not md_version:
                md_version = m_ver.group(1).strip()

            m_date = re.search(r"(?:\*\*Date:?\*\*|\|\s*\*\*Date\*\*\s*\|)\s*(\d{4}-\d{2}-\d{2})", line)
            if m_date and not md_date:
                md_date = m_date.group(1).strip()

            m_auth = re.search(r"(?:\*\*Author:?\*\*|\|\s*\*\*Author\*\*\s*\|)\s*([^|\n]+)", line)
            if m_auth and not md_author:
                md_author = m_auth.group(1).strip().strip("* ")

        def _norm_ver(v: Optional[str]) -> Optional[str]:
            if not v:
                return None
            return v.strip().lstrip("vV").split()[0].strip()

        zenodo_version = str(zenodo_data.get("version")).strip() if zenodo_data.get("version") else None
        zenodo_date = str(zenodo_data.get("publication_date")).strip() if zenodo_data.get("publication_date") else None
        creators = zenodo_data.get("creators") or []
        zenodo_author = creators[0].get("name") if creators and isinstance(creators[0], dict) else None

        pdf_page1 = pdf_pages.get(1, "")
        pdf_has_author = ("Carroll" in pdf_page1) if pdf_page1 else None
        pdf_has_version = (_norm_ver(md_version) in pdf_page1) if (pdf_page1 and md_version) else None
        pdf_has_date = (md_date in pdf_page1) if (pdf_page1 and md_date) else None

        mismatches: List[str] = []
        if md_version and zenodo_version and _norm_ver(md_version) != _norm_ver(zenodo_version):
            mismatches.append(f"Version mismatch: MD='{md_version}' vs zenodo_metadata.json='{zenodo_version}'")
        if md_date and zenodo_date and md_date != zenodo_date:
            mismatches.append(f"Date mismatch: MD='{md_date}' vs zenodo_metadata.json='{zenodo_date}'")
        if zenodo_author and "Carroll" not in zenodo_author:
            mismatches.append(f"Author mismatch in zenodo_metadata.json: '{zenodo_author}'")
        if md_author and "Carroll" not in md_author:
            mismatches.append(f"Author mismatch in MD: '{md_author}'")
        if pdf_page1 and md_version and not pdf_has_version:
            mismatches.append(f"PDF page 1 does not contain manuscript version '{_norm_ver(md_version)}'")
        if pdf_page1 and md_date and not pdf_has_date:
            mismatches.append(f"PDF page 1 does not contain manuscript date '{md_date}'")

        identity_checks: Dict[str, Any] = {
            "md_author": md_author,
            "md_version": md_version,
            "md_date": md_date,
            "zenodo_author": zenodo_author,
            "zenodo_version": zenodo_version,
            "zenodo_date": zenodo_date,
            "pdf_page1_has_author": pdf_has_author,
            "pdf_page1_has_version": pdf_has_version,
            "pdf_page1_has_date": pdf_has_date,
            "consistent": len(mismatches) == 0,
            "mismatches": mismatches,
        }

        manuscript_version = md_version or zenodo_version or "1.0.0"
        return dialect_warnings, identity_checks, paper_title, manuscript_version

    def build_manifest(self) -> PaperCompositionManifest:
        """Execute complete extraction and build the typed PaperCompositionManifest."""
        formulas, claims, prose_lines, hygiene_warnings = self.extract_from_markdown()
        tex_entries = self.extract_from_tex()
        pdf_pages = self.extract_from_pdf()

        formulas, claims, code_cov, lean_cov = self.link_code_and_proofs(formulas, claims)
        formulas, claims = self.attach_cross_format_locations(formulas, claims, tex_entries, pdf_pages)
        cross_checks = self.cross_check_formats(formulas, claims, tex_entries, pdf_pages)
        dialect_warnings, identity_checks, paper_title, manuscript_version = self.audit_dialect_and_identity(pdf_pages)

        # Index dictionaries by UUID string
        formulas_dict = {str(f.uuid): f for f in formulas}
        claims_dict = {str(c.uuid): c for c in claims}

        # Determine paper ID dynamically
        paper_id = self.paper_dir.name
        if "witnessed_difference_programme" in self.paper_dir.name:
            paper_id = "WDP-000"
        elif "projection_obstruction" in self.paper_dir.name:
            paper_id = "PO-000"
        elif "zero_container_relational" in self.paper_dir.name:
            paper_id = "PO-035"

        manifest = PaperCompositionManifest(
            manifest_version="1.1.0",
            paper_id=paper_id,
            paper_title=paper_title,
            manuscript_version=manuscript_version,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            total_formulas_extracted=len(formulas),
            total_claims_extracted=len(claims),
            total_lines_hashed=len(prose_lines),
            formulas=formulas_dict,
            claims=claims_dict,
            cross_format_checks=cross_checks,
            code_binding_coverage=code_cov,
            lean_binding_coverage=lean_cov,
            hygiene_clean_status=len(hygiene_warnings) == 0,
            hygiene_warnings=hygiene_warnings,
            dialect_warnings=dialect_warnings,
            identity_checks=identity_checks,
        )

        return manifest


def _binding_zip_path(binding: str) -> str:
    """File path named by a binding. A `path:declaration` binding contributes `path`."""
    return binding.split(":", 1)[0].replace("\\", "/").lstrip("./")


def _zip_contains(namelist: List[str], required: str) -> bool:
    suffix = "/" + required
    return any(name.replace("\\", "/") in (required, ) or name.replace("\\", "/").endswith(suffix) for name in namelist)


def verify_zip_against_manifest(
    zip_path: Path,
    manifest: PaperCompositionManifest,
    receipt_path: Optional[Path] = None,
    checksum_manifest_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """PASS only when every manifest code or lean binding and checksum manifest entry is in the zip.

    Records the SHA-256 of the zip bytes. A manifest with no bindings fails.
    An unrelated Python file does not satisfy a missing bound path.
    """
    if not zip_path.is_file():
        raise FileNotFoundError(f"Release zip not found: {zip_path}")

    required: List[str] = []
    for entry in list(manifest.formulas.values()) + list(manifest.claims.values()):
        for binding in list(entry.code_bindings) + list(entry.lean_bindings):
            path = _binding_zip_path(binding)
            if path and path not in required:
                required.append(path)

    # Cross-check against SHA256SUMS or MANIFEST.sha256 if available
    manifest_source = checksum_manifest_path
    if manifest_source is None:
        cand1 = zip_path.parent / "SHA256SUMS"
        cand2 = zip_path.parent / "MANIFEST.sha256"
        if cand1.is_file():
            manifest_source = cand1
        elif cand2.is_file():
            manifest_source = cand2

    manifest_files: List[str] = []
    if manifest_source and manifest_source.is_file():
        for line in manifest_source.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                rel = parts[1].strip().lstrip("*")
                manifest_files.append(rel)
                if rel not in required:
                    required.append(rel)

    # Check that docs/descriptions.md is bundled if present on disk
    desc_path = zip_path.parent / "docs" / "descriptions.md"
    if desc_path.is_file() and "docs/descriptions.md" not in required:
        required.append("docs/descriptions.md")

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()

    present = [path for path in required if _zip_contains(namelist, path)]
    missing = [path for path in required if path not in present]
    receipt: Dict[str, Any] = {
        "paper_id": manifest.paper_id,
        "manuscript_version": manifest.manuscript_version,
        "zip_path": str(zip_path),
        "zip_sha256": hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "total_zip_files": len(namelist),
        "required_paths": required,
        "matched_python_modules": [path for path in present if path.endswith(".py")],
        "matched_lean_modules": [path for path in present if path.endswith(".lean")],
        "missing_paths": missing,
        "status": "FAIL",
    }
    if manifest_files:
        receipt["checksum_manifest_file"] = str(manifest_source)
        receipt["manifest_files_count"] = len(manifest_files)
    if not required:
        receipt["error"] = "Manifest has no code or lean bindings to verify."
    elif missing:
        receipt["error"] = "Release zip is missing bound or manifest paths: " + ", ".join(missing)
    else:
        receipt["status"] = "PASS"

    if receipt_path is not None:
        receipt_path = Path(receipt_path).resolve()
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deep paper composition hasher: types, extracts, and hashes formulas and prose across MD, TeX, and PDF."
    )
    parser.add_argument("paper_dir", type=Path, help="Directory containing the paper package")
    parser.add_argument("--output-yaml", "--output", dest="output_yaml", type=Path, default=None, help="Output path for YAML manifest")
    parser.add_argument("--output-json", type=Path, default=None, help="Output path for JSON manifest")
    parser.add_argument("--verify-zip", type=Path, default=None, help="Path to release zip to verify")
    parser.add_argument("--checksum-manifest", type=Path, default=None, help="Path to SHA256SUMS or MANIFEST.sha256 to cross-check against zip")
    parser.add_argument("--receipt-path", type=Path, default=None, help="Output path for verification receipt (defaults to paper_dir/paper_composition_receipt.json when verifying)")
    parser.add_argument("--strict", action="store_true", help="Fail with non-zero exit code if hygiene/dialect warnings or identity mismatches exist")

    args = parser.parse_args()

    try:
        extractor = PaperCompositionExtractor(args.paper_dir)
        manifest = extractor.build_manifest()

        print(f"=== Deep Paper Composition Hasher ===")
        print(f"Paper: {manifest.paper_id} ({manifest.manuscript_version})")
        print(f"Total Formulas Typed & Hashed: {manifest.total_formulas_extracted}")
        print(f"Total Formal Claims Typed & Hashed: {manifest.total_claims_extracted}")
        print(f"Total Prose Lines Hashed: {manifest.total_lines_hashed}")
        print(f"Cross-Format Checks: {len(manifest.cross_format_checks)}")
        print(f"Claim Hygiene Status: {'CLEAN' if manifest.hygiene_clean_status else 'WARNINGS DETECTED'}")
        print(f"Dialect & Guarded Boilerplate Status: {'CLEAN' if not manifest.dialect_warnings else f'{len(manifest.dialect_warnings)} WARNINGS'}")
        print(f"Identity Parity Status: {'CONSISTENT' if manifest.identity_checks.get('consistent', True) else 'MISMATCH DETECTED'}")

        if args.output_yaml:
            out_yaml = args.output_yaml.resolve()
            out_yaml.parent.mkdir(parents=True, exist_ok=True)
            # Dump as clean YAML
            data = json.loads(manifest.model_dump_json())
            with open(out_yaml, "w", encoding="utf-8") as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            print(f"Wrote YAML manifest: {out_yaml} ({out_yaml.stat().st_size:,} bytes)")

        if args.output_json:
            out_json = args.output_json.resolve()
            out_json.parent.mkdir(parents=True, exist_ok=True)
            with open(out_json, "w", encoding="utf-8") as f:
                f.write(manifest.model_dump_json(indent=2))
            print(f"Wrote JSON manifest: {out_json} ({out_json.stat().st_size:,} bytes)")

        if args.verify_zip:
            out_receipt = args.receipt_path or (args.paper_dir / "paper_composition_receipt.json")
            zip_receipt = verify_zip_against_manifest(
                args.verify_zip,
                manifest,
                receipt_path=out_receipt,
                checksum_manifest_path=args.checksum_manifest,
            )
            print(f"Release Zip Verification: {zip_receipt['status']} ({len(zip_receipt['matched_python_modules'])} python, {len(zip_receipt['matched_lean_modules'])} lean files)")
            print(f"Wrote verification receipt: {out_receipt} ({out_receipt.stat().st_size:,} bytes)")
            if zip_receipt["status"] != "PASS":
                return 1

        if args.strict:
            failed_strict = False
            if not manifest.hygiene_clean_status:
                failed_strict = True
                print(f"FAILED (strict mode): {len(manifest.hygiene_warnings)} claim hygiene warnings exist.")
                for w in manifest.hygiene_warnings[:10]:
                    print(f"  - {w}")
            if manifest.dialect_warnings:
                failed_strict = True
                print(f"FAILED (strict mode): {len(manifest.dialect_warnings)} dialect/guarded boilerplate warnings exist.")
                for w in manifest.dialect_warnings[:10]:
                    print(f"  - {w}")
            if not manifest.identity_checks.get("consistent", True):
                failed_strict = True
                mismatches = manifest.identity_checks.get("mismatches", [])
                print(f"FAILED (strict mode): {len(mismatches)} identity parity mismatches exist.")
                for m in mismatches:
                    print(f"  - {m}")
            if failed_strict:
                return 1

        print("PASS: Compositional extraction and hashing complete.")
        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

