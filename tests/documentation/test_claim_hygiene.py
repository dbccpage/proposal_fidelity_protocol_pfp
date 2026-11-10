"""E2E Test: Claim Hygiene & Authority Posture Verification.

AuthorityEffect: None.

Audits every markdown document in documentation/ to ensure:
1. Every file explicitly declares 'AuthorityEffect: None' or equivalent neutral authority posture.
2. Zero unhedged occurrences of forbidden promotional / hype words:
   'proves', 'guarantees', 'mathematically verifies', 'fundamentally', 'true intelligence',
   'impossible', 'universal', 'flawless', 'perfectly', 'clearly', 'obviously', 'simply',
   'merely', 'weaponized'.
3. Any mention of guarantees is qualified ('guarantees under declared assumptions'),
   and any discussion of forbidden claims occurs in negative context ('What the code does NOT support').
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Tuple

import pytest

REPO_ROOT: Path = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tests.documentation.conftest import FORBIDDEN_HYPE_WORDS


class Finding(NamedTuple):
    file_path: str
    line_number: int
    word: str
    line_snippet: str


def check_authority_effect_present(text: str) -> bool:
    """Return True if the text declares AuthorityEffect: None or equivalent neutral posture."""
    pattern = r"(?:\*{0,2})AuthorityEffect(?:\*{0,2})\s*[:=]\s*(?:\*{0,2})None(?:\*{0,2})"
    return bool(re.search(pattern, text, re.IGNORECASE))


def is_justified_occurrence(word: str, line: str) -> bool:
    """Determine whether an occurrence of a forbidden word is explicitly justified or negated.

    Under Claim Hygiene rules:
    - 'guarantees' is permitted as 'guarantees under [the ]declared assumptions'.
    - Words occurring in explicit negative-scope summaries (e.g., 'does not demonstrate that ... proves',
      'does not claim universal', 'not a universal mathematical proof') represent proper bounding.
    - Mentions inside explicit claim hygiene rule citations or code references are permitted.
    """
    line_lower = line.lower().strip()

    # Replacement default: 'guarantees' -> 'guarantees under declared assumptions'
    if word == "guarantees":
        if re.search(r"guarantees\s+under\s+(?:the\s+)?declared\s+assumptions", line_lower):
            return True

    # Mathematical topology term 'simply connected'
    if word == "simply" and "simply connected" in line_lower:
        return True

    # Claim bounding: 'universal claims' designated as candidate/unverified
    if word == "universal" and ("universal claims" in line_lower or "universal certification" in line_lower):
        return True

    # Explicit negation contexts (What the code does NOT support)
    negation_patterns = [
        r"does\s+not\s+(?:demonstrate|claim|constitute|show|imply|mean|prove)",
        r"not\s+a\s+universal",
        r"not\s+claim\s+universal",
        r"refus(?:ing|es|ed)\s+universal",
        r"absence\s+of\s+.*?\s+does\s+not",
        r"neither\s+.*?\s+nor",
        r"never\s+guarantees",
    ]
    for pat in negation_patterns:
        if re.search(pat, line_lower):
            return True

    # Meta-discussions of claim hygiene rules or quotes of forbidden words
    if "forbidden" in line_lower or "claim hygiene" in line_lower or "replacement default" in line_lower:
        return True

    return False


def scan_file_for_forbidden_words(file_path: Path) -> List[Finding]:
    """Scan a markdown file for unhedged occurrences of the 14 forbidden hype words."""
    findings: List[Finding] = []
    text = file_path.read_text(encoding="utf-8", errors="replace")

    in_code_block = False
    for line_idx, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # Toggle fenced code blocks ``` ... ```
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        for word in FORBIDDEN_HYPE_WORDS:
            # Word boundary regex, case-insensitive
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, line, re.IGNORECASE):
                if not is_justified_occurrence(word, line):
                    findings.append(
                        Finding(
                            file_path=str(file_path),
                            line_number=line_idx,
                            word=word,
                            line_snippet=line.strip()[:120],
                        )
                    )

    return findings


class TestClaimHygiene:
    """Audits documentation files for strict Claim Hygiene compliance."""

    def test_forbidden_words_catalog_completeness(self) -> None:
        """Verify the forbidden hype word catalog contains all 14 mandatory terms."""
        expected = {
            "proves",
            "guarantees",
            "mathematically verifies",
            "fundamentally",
            "true intelligence",
            "impossible",
            "universal",
            "flawless",
            "perfectly",
            "clearly",
            "obviously",
            "simply",
            "merely",
            "weaponized",
        }
        assert FORBIDDEN_HYPE_WORDS == expected, (
            f"Catalog mismatch: missing {expected - FORBIDDEN_HYPE_WORDS}, "
            f"extra {FORBIDDEN_HYPE_WORDS - expected}"
        )

    def test_all_documentation_files_declare_authority_effect_none(
        self, all_doc_files: List[Path]
    ) -> None:
        """Verify that every .md file in documentation/ explicitly declares AuthorityEffect: None."""
        assert len(all_doc_files) > 0, "No documentation files found to evaluate"
        missing_authority: List[str] = []

        for fpath in all_doc_files:
            text = fpath.read_text(encoding="utf-8", errors="replace")
            if not check_authority_effect_present(text):
                missing_authority.append(str(fpath))

        assert not missing_authority, (
            f"The following {len(missing_authority)} files are missing 'AuthorityEffect: None':\n"
            + "\n".join(f" - {f}" for f in missing_authority)
        )

    def test_all_documentation_files_free_of_unhedged_forbidden_words(
        self, all_doc_files: List[Path]
    ) -> None:
        """Verify zero unhedged occurrences of forbidden words across all documentation files."""
        assert len(all_doc_files) > 0, "No documentation files found to evaluate"
        all_findings: List[Finding] = []

        for fpath in all_doc_files:
            findings = scan_file_for_forbidden_words(fpath)
            all_findings.extend(findings)

        if all_findings:
            report_lines = [
                f" - {f.file_path}:{f.line_number} [{f.word}]: \"{f.line_snippet}\""
                for f in all_findings
            ]
            pytest.fail(
                f"Discovered {len(all_findings)} unhedged forbidden hype word violations:\n"
                + "\n".join(report_lines)
            )

    def test_adversarial_forbidden_word_detection(self) -> None:
        """Adversarial check: ensure the scanner flags all 14 forbidden words in synthetic prose."""
        synthetic_prose = """
        This algorithm fundamentally proves universal intelligence and guarantees
        flawless performance. It mathematically verifies that errors are impossible.
        The model achieves true intelligence, perfectly solving tasks that were clearly,
        obviously, simply, merely beyond reach, while avoiding weaponized failure modes.
        """
        detected: List[str] = []
        for word in FORBIDDEN_HYPE_WORDS:
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, synthetic_prose, re.IGNORECASE):
                detected.append(word)

        assert set(detected) == FORBIDDEN_HYPE_WORDS, (
            f"Adversarial detector failed to flag: {FORBIDDEN_HYPE_WORDS - set(detected)}"
        )

    def test_adversarial_missing_authority_effect_rejection(self) -> None:
        """Adversarial check: ensure documents without AuthorityEffect: None are rejected."""
        unadorned_doc = """
        # My Great Proposal
        Author: Someone
        This document proposes an architectural enhancement without declaring authority.
        """
        assert not check_authority_effect_present(unadorned_doc), (
            "Should have rejected document lacking AuthorityEffect: None"
        )
