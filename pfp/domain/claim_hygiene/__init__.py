"""Claim hygiene domain package.

AuthorityEffect: None.
"""

from __future__ import annotations

from .models import (
    CitationAnchor,
    FORBIDDEN_HYPE_REPLACEMENTS,
    PaperClaim,
    strip_forbidden_hype_words,
)

__all__ = [
    "CitationAnchor",
    "FORBIDDEN_HYPE_REPLACEMENTS",
    "PaperClaim",
    "strip_forbidden_hype_words",
]
