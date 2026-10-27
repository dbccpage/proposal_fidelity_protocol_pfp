"""Pandoc & XeLaTeX Build-Hygiene Gate Rules.

AuthorityEffect: None.

Three defect classes stop, or silently damage, a Markdown -> pandoc -> XeLaTeX
build. All three occurred in one monograph rebuild on 2026-10-06:

1. ``\\( ... \\)`` math in the Markdown while the pandoc reader lacks
   ``tex_math_single_backslash``. Pandoc reads ``\\(`` as an escaped parenthesis
   and passes the inner commands (``\\mathbb``) as raw TeX outside math mode.
2. A backslash glued to a word in prose (``W\\T`` written for a set difference,
   or a Windows path). With ``raw_tex`` pandoc passes ``\\T`` through as a TeX
   command, and XeLaTeX stops on an undefined control sequence.
3. Characters the text font lacks. XeLaTeX logs ``Missing character`` and drops
   the glyph from the PDF while still exiting 0.
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import Dict, List, Optional, Tuple

from .base_rule import (
    BasePaperRule,
    PaperContext,
    RuleCategory,
    RuleFinding,
    RuleResult,
    RuleSeverity,
)

SINGLE_BACKSLASH_MATH_EXTENSION = "tex_math_single_backslash"

# The reader used by the shared kit (_kits/obstruction_paper_kit/build.sh, makefile).
CANONICAL_PANDOC_MARKDOWN_READER = (
    "markdown+tex_math_dollars+tex_math_single_backslash+raw_tex+pipe_tables"
)

# Math-mode replacements for glyphs that text fonts commonly lack. The kit
# preamble defines ``\um{#1}`` as ``\ensuremath{#1}``.
GLYPH_MATH_COMMANDS: Dict[str, str] = {
    "∖": r"\setminus",
    "∩": r"\cap",
    "∪": r"\cup",
    "ε": r"\varepsilon",
    "⁻": "^-",
    "↦": r"\mapsto",
    "∅": r"\emptyset",
    "⋯": r"\cdots",
    "⊆": r"\subseteq",
    "⊂": r"\subset",
    "₅": "_5",
}

# Text-mode commands that are legitimately written flush against a word.
PROSE_GLUED_COMMAND_ALLOWLIST = frozenset({
    "allowbreak",
    "break",
    "cite",
    "citep",
    "citet",
    "dots",
    "eqref",
    "footnote",
    "hfill",
    "index",
    "label",
    "ldots",
    "linebreak",
    "newline",
    "nobreak",
    "par",
    "qquad",
    "quad",
    "ref",
    "relax",
    "slash",
    "textsubscript",
    "textsuperscript",
    "xspace",
})

_READER_SPEC = re.compile(r"\b(markdown(?:_[a-z]+)?)((?:[+-][a-z0-9_]+)+)")
_ADJACENT_STRING_LITERALS = re.compile(r"[\"']\s+[\"']")
_SINGLE_BACKSLASH_INLINE_MATH = re.compile(r"(?<!\\)\\\((.+?)(?<!\\)\\\)")
# The colon catches drive paths (C:\Users); later path segments read as chained commands.
_GLUED_CONTROL_SEQUENCE = re.compile(r"(?<=[A-Za-z0-9:\)\]])\\([A-Za-z]+)")
_TRAILING_WORD = re.compile(r"[A-Za-z0-9]+$")
_MISSING_CHARACTER = re.compile(
    r"^Missing character: There is no (.+?) (?:\(U\+[0-9A-Fa-f]{4,6}\) )?in font (.+?)!?\s*$",
    re.MULTILINE,
)

_THEMATIC_BREAK_ASTERISKS = re.compile(r"^[ \t]*(?:\*[ \t]*){3,}\s*$")
_ASTERISK_LIST_ITEM = re.compile(r"^[ \t]*\*[ \t]+(\S.*)?$")
_MD004_SUPPRESSION_COMMENT = re.compile(
    r"<!--\s*markdownlint-(?:disable|capture)[\s\S]*?\b(?:MD004|ul-style)\b",
    re.IGNORECASE,
)

_HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
_FENCED_CODE = re.compile(r"^(`{3,}|~{3,}).*?^\1", re.DOTALL | re.MULTILINE)
_INLINE_CODE = re.compile(r"(`+)(?!`).+?(?<!`)\1")
_DISPLAY_DOLLAR_MATH = re.compile(r"\$\$.*?\$\$", re.DOTALL)

# Code regions: TeX-looking text inside them is never parsed as math.
_CODE_REGIONS: Tuple[re.Pattern[str], ...] = (_HTML_COMMENT, _FENCED_CODE, _INLINE_CODE)

# Regions where TeX syntax is intended, or that pandoc does not render as prose.
_NON_PROSE_REGIONS: Tuple[re.Pattern[str], ...] = (
    *_CODE_REGIONS,
    _DISPLAY_DOLLAR_MATH,
    re.compile(r"\\begin\{([^}]+)\}.*?\\end\{\1\}", re.DOTALL),
    re.compile(r"(?<!\\)\\\(.*?(?<!\\)\\\)", re.DOTALL),
    re.compile(r"(?<!\\)\\\[.*?(?<!\\)\\\]", re.DOTALL),
    # Inline $...$ may wrap across lines inside a paragraph, never across a blank line.
    re.compile(r"(?<![\\$])\$(?=\S)(?:[^$\n]|\n(?![ \t]*\n))+?(?<=\S)(?<!\\)\$"),
    re.compile(r"\]\([^)\s]*\)"),
    re.compile(r"<[a-z]+://[^>\s]+>"),
)

_BUILD_SCRIPT_PATH = re.compile(
    r"^(?:(?:scripts|tools)/[^/]+\.(?:py|sh|ps1)|(?:[Mm]akefile|build\.sh|build_all\.ps1))$"
)


def _blank_out(match: re.Match[str]) -> str:
    # Keep line numbers stable and break adjacency across the removed span.
    return " " + "\n" * match.group(0).count("\n")


def _blank_regions(markdown: str, patterns: Tuple[re.Pattern[str], ...]) -> str:
    text = markdown
    for pattern in patterns:
        text = pattern.sub(_blank_out, text)
    return text


def strip_non_prose(markdown: str) -> str:
    """Return the Markdown with code, math, raw TeX environments and link targets blanked."""
    return _blank_regions(markdown, _NON_PROSE_REGIONS)


def find_single_backslash_math(markdown: str) -> List[int]:
    """Line numbers of ``\\( ... \\)`` spans that contain TeX math commands."""
    text = _blank_regions(markdown, _CODE_REGIONS)
    lines: List[int] = []
    for match in _SINGLE_BACKSLASH_INLINE_MATH.finditer(text):
        inner = match.group(1)
        if re.search(r"\\[A-Za-z]|[_^]", inner):
            lines.append(text.count("\n", 0, match.start()) + 1)
    return lines


def pandoc_reader_specs(script_text: str) -> List[Tuple[str, bool]]:
    """Each Markdown reader spec in a build script, with whether single-backslash math is on.

    Adjacent string literals (Python implicit concatenation) are joined first,
    so a spec split across two literals is read whole.
    """
    joined = _ADJACENT_STRING_LITERALS.sub("", script_text)
    specs: List[Tuple[str, bool]] = []
    for match in _READER_SPEC.finditer(joined):
        enabled = False
        for sign, name in re.findall(r"([+-])([a-z0-9_]+)", match.group(2)):
            if name == SINGLE_BACKSLASH_MATH_EXTENSION:
                enabled = sign == "+"
        specs.append((match.group(0), enabled))
    return specs


def find_glued_control_sequences(markdown: str) -> List[Tuple[int, str]]:
    """``(line, command)`` for each backslash command glued to a preceding word in prose."""
    text = strip_non_prose(markdown)
    hits: List[Tuple[int, str]] = []
    for match in _GLUED_CONTROL_SEQUENCE.finditer(text):
        command = match.group(1)
        if command in PROSE_GLUED_COMMAND_ALLOWLIST:
            continue
        word = _TRAILING_WORD.search(text, max(0, match.start() - 256), match.start())
        if word is not None and word.start() > 0 and text[word.start() - 1] == "\\":
            # Chained raw TeX such as \noindent\textbf: the "word" is itself a command.
            continue
        hits.append((text.count("\n", 0, match.start()) + 1, command))
    return hits


def parse_missing_glyphs(tex_log: str) -> Dict[str, int]:
    """Glyph -> occurrence count for every ``Missing character`` line in a XeLaTeX log."""
    counts: Dict[str, int] = {}
    for match in _MISSING_CHARACTER.finditer(tex_log):
        glyph = match.group(1)
        counts[glyph] = counts.get(glyph, 0) + 1
    return dict(sorted(counts.items()))


def suggest_glyph_mapping(glyph: str) -> Optional[str]:
    """A ``\\newunicodechar`` line for a known glyph, or None."""
    command = GLYPH_MATH_COMMANDS.get(glyph)
    if command is None:
        return None
    return f"\\newunicodechar{{{glyph}}}{{\\um{{{command}}}}}"


def describe_missing_glyphs(counts: Dict[str, int]) -> str:
    """One-line summary of missing glyphs, with suggested preamble mappings where known."""
    parts = []
    for glyph, count in counts.items():
        mapping = suggest_glyph_mapping(glyph)
        hint = f" -> {mapping}" if mapping else ""
        parts.append(f"{glyph} (U+{ord(glyph[0]):04X}) x{count}{hint}")
    return "; ".join(parts)


class PandocSingleBackslashMathRule(BasePaperRule):
    """Manuscripts using ``\\( ... \\)`` math need a reader with ``tex_math_single_backslash``."""

    @property
    def rule_id(self) -> str:
        return "R_PANDOC_SINGLE_BACKSLASH_MATH"

    @property
    def name(self) -> str:
        return "Pandoc Reader Parses Single-Backslash Math"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "If the manuscript writes inline math as \\( ... \\), every package build script "
            "that declares a pandoc Markdown reader must enable +tex_math_single_backslash."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result({"checked": False, "reason": "no primary Markdown"})
        math_lines = find_single_backslash_math(ctx.read_text(md_path))
        if not math_lines:
            return self.pass_result({"checked": True, "single_backslash_math_spans": 0})

        scripts = [p for p in ctx.list_paths() if _BUILD_SCRIPT_PATH.match(p)]
        findings: List[RuleFinding] = []
        spec_count = 0
        for script in scripts:
            for spec, enabled in pandoc_reader_specs(ctx.read_text(script)):
                spec_count += 1
                if not enabled:
                    findings.append(
                        RuleFinding(
                            rule_id=self.rule_id,
                            severity=self.severity,
                            message=(
                                f"Reader '{spec}' lacks +{SINGLE_BACKSLASH_MATH_EXTENSION}, but the "
                                f"manuscript has {len(math_lines)} \\( ... \\) math span(s) "
                                f"(first at {md_path}:L{math_lines[0]})."
                            ),
                            file_path=script,
                            remediation=(
                                f"Add +{SINGLE_BACKSLASH_MATH_EXTENSION} to the reader "
                                f"(kit reader: {CANONICAL_PANDOC_MARKDOWN_READER})."
                            ),
                        )
                    )

        details = {
            "checked": spec_count > 0,
            "single_backslash_math_spans": len(math_lines),
            "reader_specs": spec_count,
        }
        if findings:
            return self.fail_result(findings, details)
        return self.pass_result(details)


class ProseBackslashControlSequenceRule(BasePaperRule):
    """Prose must not contain a backslash command glued to a word (``W\\T``, ``C:\\Users``)."""

    @property
    def rule_id(self) -> str:
        return "R_MD_PROSE_BACKSLASH"

    @property
    def name(self) -> str:
        return "No Stray TeX Control Sequences in Prose"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "Outside code, math and raw TeX environments, a backslash directly after a letter, "
            "digit, colon or closing bracket becomes an undefined TeX command under raw_tex."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        md_path = ctx.get_primary_markdown_path()
        if not md_path:
            return self.pass_result({"checked": False, "reason": "no primary Markdown"})
        hits = find_glued_control_sequences(ctx.read_text(md_path))
        findings = [
            RuleFinding(
                rule_id=self.rule_id,
                severity=self.severity,
                message=f"Backslash command '\\{command}' glued to a word in prose on line {line}",
                file_path=md_path,
                line_number=line,
                remediation=(
                    "Write a set difference as ∖ (U+2216) or $A\\setminus B$; put paths and "
                    "literal backslashes in `code spans`."
                ),
            )
            for line, command in hits
        ]
        if findings:
            return self.fail_result(findings, {"hits": len(hits)})
        return self.pass_result({"checked": True, "hits": 0})


class TexLogMissingGlyphRule(BasePaperRule):
    """A retained XeLaTeX log must report zero ``Missing character`` lines."""

    @property
    def rule_id(self) -> str:
        return "R_TEX_MISSING_GLYPHS"

    @property
    def name(self) -> str:
        return "No Missing Glyphs in the XeLaTeX Log"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "XeLaTeX drops characters the font lacks and still exits 0; a retained "
            "<stem>.log must contain no 'Missing character' lines."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        tex_path = ctx.get_primary_tex_path()
        if not tex_path:
            return self.pass_result({"checked": False, "reason": "no primary .tex"})
        log_path = tex_path[: -len(".tex")] + ".log"
        if not ctx.has_file(log_path):
            # The rebuild step and review Stage 5 scan the fresh log of their own build.
            return self.pass_result({"checked": False, "reason": f"{log_path} not retained"})
        counts = parse_missing_glyphs(ctx.read_text(log_path))
        if counts:
            return self.fail_result(
                [
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"XeLaTeX dropped {sum(counts.values())} glyph(s): {describe_missing_glyphs(counts)}",
                        file_path=log_path,
                        remediation=(
                            "Map each glyph in the preamble with \\newunicodechar (the kit uses "
                            "\\um{...} for math symbols), or choose a font that has it."
                        ),
                    )
                ],
                {"missing_glyphs": counts},
            )
        return self.pass_result({"checked": True, "missing_glyphs": {}})


def find_asterisk_list_items(text: str) -> List[Tuple[int, str]]:
    """Return 1-indexed (line_number, line_snippet) for asterisk list items violating MD004."""
    hits: List[Tuple[int, str]] = []
    in_code = False
    fence_char = ""
    in_math = False

    for idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()

        # Handle fenced code blocks
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            if not in_code:
                in_code = True
                fence_char = fence
                continue
            elif stripped.startswith(fence_char):
                in_code = False
                fence_char = ""
                continue

        if in_code:
            continue

        # Handle display math blocks
        if in_math:
            if stripped == "$$" or stripped.endswith("$$") or stripped == r"\]":
                in_math = False
            continue

        if stripped == "$$" or stripped == r"\[":
            in_math = True
            continue
        elif stripped.startswith("$$"):
            if stripped.endswith("$$") and len(stripped) > 2:
                # Single-line display math
                continue
            in_math = True
            continue

        # Skip thematic breaks (e.g. ***, * * *, ****)
        if _THEMATIC_BREAK_ASTERISKS.match(line):
            continue

        if _ASTERISK_LIST_ITEM.match(line):
            hits.append((idx, stripped))

    return hits


def find_md004_suppressions(text: str) -> List[Tuple[int, str]]:
    """Return 1-indexed (line_number, match_snippet) for markdownlint MD004 suppressions."""
    hits: List[Tuple[int, str]] = []
    for m in _MD004_SUPPRESSION_COMMENT.finditer(text):
        line_num = text.count("\n", 0, m.start()) + 1
        snippet = m.group(0).strip().replace("\n", " ")[:60]
        hits.append((line_num, snippet))
    return hits


class MarkdownUnorderedListStyleRule(BasePaperRule):
    """All Markdown documents in the paper package must use dash style ('-') for unordered lists per MD004.

    Asterisk list markers ('*') and suppressing/ignoring MD004 via comments or config files are prohibited;
    linter warnings must be fixed on disk.
    """

    @property
    def rule_id(self) -> str:
        return "R_MD_UL_STYLE_DASH"

    @property
    def name(self) -> str:
        return "Markdown Unordered Lists Must Use Dash Style (MD004)"

    @property
    def category(self) -> RuleCategory:
        return RuleCategory.LATEX_PDF

    @property
    def severity(self) -> RuleSeverity:
        return RuleSeverity.BLOCKER

    @property
    def description(self) -> str:
        return (
            "All Markdown documents in the paper package must use dash style ('-') for unordered "
            "lists per MD004; asterisk list markers ('*') and suppressing/ignoring MD004 are prohibited."
        )

    def evaluate(self, ctx: PaperContext) -> RuleResult:
        all_files = ctx.get_all_files()
        md_files = [p for p in all_files if p.endswith(".md")]
        if not md_files:
            return self.pass_result({"checked": False, "reason": "no markdown files"})

        findings: List[RuleFinding] = []
        total_asterisk_lists = 0

        for md_path in sorted(md_files):
            text = ctx.read_text(md_path)
            # Check for asterisk list items
            ast_hits = find_asterisk_list_items(text)
            total_asterisk_lists += len(ast_hits)
            for line, snippet in ast_hits:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Unordered list item uses asterisk marker violating MD004 on line {line}: '{snippet}'",
                        file_path=md_path,
                        line_number=line,
                        remediation="Change asterisk list item marker '*' to dash '-' and verify markdownlint MD004 passes.",
                    )
                )

            # Check for suppression comments
            suppressions = find_md004_suppressions(text)
            for line, snippet in suppressions:
                findings.append(
                    RuleFinding(
                        rule_id=self.rule_id,
                        severity=self.severity,
                        message=f"Markdownlint MD004/ul-style disabled or suppressed on line {line}: '{snippet}'",
                        file_path=md_path,
                        line_number=line,
                        remediation="Remove markdownlint suppression comment; fix the underlying list markers to dashes on disk.",
                    )
                )

        # Check config files for MD004 suppressions
        for cfg_name in (".markdownlint.json", ".markdownlint.jsonc", ".markdownlint.yaml", ".markdownlint.yml"):
            for path in all_files:
                if PurePosixPath(path).name == cfg_name:
                    content = ctx.read_text(path)
                    is_yaml = cfg_name.endswith((".yaml", ".yml"))
                    disabled = False
                    if not is_yaml:
                        if re.search(r'"(?:MD004|ul-style)"\s*:\s*false', content) or re.search(
                            r'"style"\s*:\s*"(?:asterisk|consistent|sublist)"', content
                        ):
                            disabled = True
                    else:
                        if re.search(r'(?:MD004|ul-style)\s*:\s*false', content) or re.search(
                            r'style\s*:\s*["\']?(?:asterisk|consistent|sublist)["\']?', content
                        ):
                            disabled = True
                    if disabled:
                        findings.append(
                            RuleFinding(
                                rule_id=self.rule_id,
                                severity=self.severity,
                                message=(
                                    f"Markdownlint MD004/ul-style disabled or configured with non-dash style in config: {path}"
                                ),
                                file_path=path,
                                remediation="Configure MD004 with style 'dash' or remove the suppression override.",
                            )
                        )

        if findings:
            return self.fail_result(
                findings,
                {
                    "markdown_files_checked": len(md_files),
                    "asterisk_list_items": total_asterisk_lists,
                    "total_defects": len(findings),
                },
            )

        return self.pass_result(
            {
                "checked": True,
                "markdown_files_checked": len(md_files),
                "asterisk_list_items": 0,
            }
        )
