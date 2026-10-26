"""Pure domain models for Claim Hygiene & Literature Anchoring (Prompt 12).

AuthorityEffect: None.
ZERO-FLOAT Law: Pure discrete strings and digests.
Clean Architecture: Zero outward dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Optional, Sequence, Tuple

FORBIDDEN_HYPE_REPLACEMENTS: Tuple[Tuple[str, str], ...] = (
    ("proves", "shows in this model"),
    ("guarantees", "guarantees under the declared assumptions"),
    ("fundamentally", "specifically"),
    ("true intelligence", "bounded toy evaluator"),
    ("impossible", "refutable in this formal setting"),
    ("universal", "scoped"),
    ("flawless", "checked"),
    ("perfectly", "consistently"),
    ("clearly", "by inspection"),
    ("obviously", "directly"),
    ("simply", "directly"),
    ("merely", "only"),
    ("weaponized", "targeted"),
)


def strip_forbidden_hype_words(text: str) -> Tuple[str, Tuple[Tuple[str, str], ...]]:
    """Strips forbidden hype verbs and replaces them with bounded, defensible phrasing."""
    sanitized = text
    applied: list[Tuple[str, str]] = []

    for pattern, replacement in FORBIDDEN_HYPE_REPLACEMENTS:
        regex = re.compile(rf"\b{re.escape(pattern)}\b", re.IGNORECASE)
        if regex.search(sanitized):
            sanitized = regex.sub(replacement, sanitized)
            applied.append((pattern, replacement))

    return sanitized, tuple(applied)


@dataclass(frozen=True)
class PaperClaim:
    """Manuscript claim with sanitized claim language and formal proof/test anchors."""

    claim_id: str
    raw_statement: str
    sanitized_statement: str
    replacements_applied: Tuple[Tuple[str, str], ...]
    attested_test_path: Optional[str]
    lean_proof_id: Optional[str]
    authority_effect: str = "None"

    @classmethod
    def create(
        cls,
        claim_id: str,
        raw_statement: str,
        attested_test_path: Optional[str] = None,
        lean_proof_id: Optional[str] = None,
    ) -> PaperClaim:
        sanitized, applied = strip_forbidden_hype_words(raw_statement)
        return cls(
            claim_id=claim_id,
            raw_statement=raw_statement,
            sanitized_statement=sanitized,
            replacements_applied=applied,
            attested_test_path=attested_test_path,
            lean_proof_id=lean_proof_id,
            authority_effect="None",
        )

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.claim_id,
            self.raw_statement,
            self.sanitized_statement,
            self.replacements_applied,
            self.attested_test_path,
            self.lean_proof_id,
            self.authority_effect,
        ) == (
            other.claim_id,
            other.raw_statement,
            other.sanitized_statement,
            other.replacements_applied,
            other.attested_test_path,
            other.lean_proof_id,
            other.authority_effect,
        )


@dataclass(frozen=True)
class CitationAnchor:
    """Cryptographic literature citation anchor bound to exact byte-range SHA-256."""

    citation_id: str
    doi_or_arxiv: str
    source_title: str
    byte_range_sha256: str
    is_verified: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.citation_id,
            self.doi_or_arxiv,
            self.source_title,
            self.byte_range_sha256,
            self.is_verified,
        ) == (
            other.citation_id,
            other.doi_or_arxiv,
            other.source_title,
            other.byte_range_sha256,
            other.is_verified,
        )
