"""LaTeX & PDF Manuscript Gate Rules.

AuthorityEffect: None.

Enforces structural and typographic invariants on TeX sources, citations,
landscape table orientations, and compiled PDF artifacts.
"""

from __future__ import annotations

import re
from typing import List, Set

from .base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)

CITE_PATTERN = re.compile(r"\\cite(?:\[[^\]]*\])?\{([^}]+)\}")
BIBITEM_PATTERN = re.compile(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}")
TABLE_ENV_PATTERN = re.compile(r"\\begin\{tabular\}\{([^}]+)\}")


class NoMaketitleRule(BasePaperRule):
    """Enforces that LaTeX sources avoid \\maketitle, using explicit centered header blocks instead."""

    @property
    def rule_id(self) -> str:
        return "R_NO_MAKETITLE"

    @property
    def name(self) -> str:
        return "No \\maketitle Invariant (Centered Header Block)"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "LaTeX monograph must avoid \\maketitle and automatic horizontal rules, using a centered metadata block."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        tex_path = ctx.get_primary_tex_path()
        if not tex_path:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="No primary .tex source file found in package root.",
                )
            ])

        content = ctx.read_text(tex_path)
        findings: List[RuleFinding] = []

        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            code_part = re.sub(r"(?<!\\)%.*$", "", stripped).strip()
            if "\\maketitle" in code_part:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Illegal \\maketitle invocation on line {line_no}",
                        file_path=tex_path,
                        line_number=line_no,
                        remediation="Replace \\maketitle with an explicit \\begin{center} ... \\end{center} header block.",
                    )
                )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class NoTableOfContentsRule(BasePaperRule):
    """Enforces that LaTeX sources avoid automatic \\tableofcontents to prevent empty TOC pages."""

    @property
    def rule_id(self) -> str:
        return "R_NO_TOC"

    @property
    def name(self) -> str:
        return "No \\tableofcontents Invariant"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "LaTeX monograph must avoid \\tableofcontents to prevent blank/unpopulated TOC page insertions."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        tex_path = ctx.get_primary_tex_path()
        if not tex_path:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="No primary .tex source file found in package root.",
                )
            ])

        content = ctx.read_text(tex_path)
        findings: List[RuleFinding] = []

        for line_no, line in enumerate(content.splitlines(), start=1):
            stripped = line.strip()
            code_part = re.sub(r"(?<!\\)%.*$", "", stripped).strip()
            if "\\tableofcontents" in code_part:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Illegal \\tableofcontents invocation on line {line_no}",
                        file_path=tex_path,
                        line_number=line_no,
                        remediation="Remove \\tableofcontents; use clean section hierarchy directly.",
                    )
                )

        if findings:
            return self.fail_result(findings)
        return self.pass_result()


class CitationBijectionRule(BasePaperRule):
    """Enforces that every citation key in the LaTeX source maps to an explicit bibliography entry."""

    @property
    def rule_id(self) -> str:
        return "R_CITATION_BIJECTION"

    @property
    def name(self) -> str:
        return "Citation-Bibliography Bijection"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Every \\cite{key} in LaTeX monograph must resolve to an explicit \\bibitem{key}."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        tex_path = ctx.get_primary_tex_path()
        if not tex_path:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="No primary .tex source file found in package root.",
                )
            ])

        content = ctx.read_text(tex_path)
        cited_keys: Set[str] = set()
        bib_keys: Set[str] = set()

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("%"):
                continue
            for match in CITE_PATTERN.finditer(stripped):
                for k in match.group(1).split(","):
                    k = k.strip()
                    if k:
                        cited_keys.add(k)
            for match in BIBITEM_PATTERN.finditer(stripped):
                k = match.group(1).strip()
                if k:
                    bib_keys.add(k)

        findings: List[RuleFinding] = []
        for ck in sorted(list(cited_keys)):
            if ck not in bib_keys:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Citation key '{ck}' has no matching \\bibitem in bibliography.",
                        file_path=tex_path,
                        remediation=f"Add \\bibitem{{{ck}}} to the bibliography or correct the citation key.",
                    )
                )

        if findings:
            return self.fail_result(findings, {"cited_count": len(cited_keys), "bib_count": len(bib_keys)})
        return self.pass_result({"cited_count": len(cited_keys), "bib_count": len(bib_keys)})


class LandscapeTableRule(BasePaperRule):
    """Enforces that wide comparative audit tables (>=6 columns) use pdflscape orientation."""

    @property
    def rule_id(self) -> str:
        return "R_LANDSCAPE_TABLES"

    @property
    def name(self) -> str:
        return "Landscape Table Width Discipline"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.MAJOR

    @property
    def description(self) -> str:
        return "Wide comparative tables with >= 6 columns must be typeset in landscape orientation."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        tex_path = ctx.get_primary_tex_path()
        if not tex_path:
            return self.pass_result()

        content = ctx.read_text(tex_path)
        has_pdflscape = "pdflscape" in content
        in_landscape = False
        findings: List[RuleFinding] = []

        for line_no, line in enumerate(content.splitlines(), start=1):
            if "\\begin{landscape}" in line:
                in_landscape = True
            elif "\\end{landscape}" in line:
                in_landscape = False

            match = TABLE_ENV_PATTERN.search(line)
            if match and not in_landscape:
                col_spec = match.group(1).replace("|", "").replace(" ", "").replace("@{}", "")
                col_count = len([c for c in col_spec if c in "lcrpmbX"])
                if col_count >= 6:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=f"Wide table with {col_count} columns typeset in portrait mode on line {line_no}",
                            file_path=tex_path,
                            line_number=line_no,
                            remediation="Wrap table in \\begin{landscape} ... \\end{landscape} using \\usepackage{pdflscape}.",
                        )
                    )

        if findings:
            return self.fail_result(findings, {"has_pdflscape": has_pdflscape})
        return self.pass_result({"has_pdflscape": has_pdflscape})


class PdfExistsAndRenderableRule(BasePaperRule):
    """Enforces that a compiled PDF exists, is non-empty, and possesses a valid PDF signature."""

    @property
    def rule_id(self) -> str:
        return "R_PDF_RENDERABLE"

    @property
    def name(self) -> str:
        return "Rendered PDF Manuscript Integrity"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return "Deposited PDF monograph must exist, be non-empty, and contain a valid %PDF header."

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        pdf_path = ctx.get_primary_pdf_path()
        if not pdf_path:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message="[TEX_PDF_HASH_DESYNCHRONIZATION] No primary .pdf compiled monograph found in package root or docs/.",
                    remediation="Compile LaTeX source via xelatex to produce the publication PDF.",
                )
            ])

        pdf_bytes = ctx.read_bytes(pdf_path)
        if len(pdf_bytes) == 0:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"[TEX_PDF_HASH_DESYNCHRONIZATION] PDF file '{pdf_path}' is 0 bytes (empty).",
                    file_path=pdf_path,
                )
            ])

        if not pdf_bytes.startswith(b"%PDF-"):
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"[TEX_PDF_HASH_DESYNCHRONIZATION] PDF file '{pdf_path}' lacks valid %PDF header signature.",
                    file_path=pdf_path,
                )
            ])

        if ctx.package_dir is not None and len(pdf_bytes) < 1024:
            return self.fail_result([
                RuleFinding(
                    rule_id=self.rule_id,
                    severity=self.severity,
                    message=f"[TEX_PDF_HASH_DESYNCHRONIZATION] PDF file '{pdf_path}' is corrupted or empty (< 1KB; {len(pdf_bytes)} bytes).",
                    file_path=pdf_path,
                    remediation="Recompile LaTeX source to ensure a complete, non-truncated PDF.",
                )
            ])

        return self.pass_result({"pdf_path": pdf_path, "bytes": len(pdf_bytes)})
