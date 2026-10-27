from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Sequence


NON_PORTABLE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"file:///[a-zA-Z]:[/\\]", re.IGNORECASE),
    re.compile(r"[a-zA-Z]:\\Users\\[a-zA-Z0-9_-]+", re.IGNORECASE),
    # The lookahead was written as (?!\\.|\n), which compiles to
    # "not followed by a backslash and any character, or a newline". The scan is
    # line-by-line after splitlines(), so the newline alternative was unreachable
    # and /home/bare_metal_anchor/.config/thing still matched. A single-escaped (?!\.) is
    # what excludes a dot-directory, which is what was intended.
    re.compile(r"/Users/[a-zA-Z0-9_-]+/(?!\.)", re.IGNORECASE),
    re.compile(r"/home/[a-zA-Z0-9_-]+/(?!\.)", re.IGNORECASE),
)


class NonPortableReferenceError(Exception):
    """Raised in strict mode when non-portable path references are discovered."""
    pass


@dataclass(frozen=True, slots=True)
class LocusHit:
    line_number: int
    matched_text: str
    pattern_index: int

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, LocusHit)
        return (
            self.line_number == other.line_number
            and self.matched_text == other.matched_text
            and self.pattern_index == other.pattern_index
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "line_number": self.line_number,
            "matched_text": self.matched_text,
            "pattern_index": self.pattern_index,
        }


@dataclass(frozen=True, slots=True)
class ScanReport:
    file_path: str
    hits: tuple[LocusHit, ...]
    is_clean: bool

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, ScanReport)
        return (
            self.file_path == other.file_path
            and self.hits == other.hits
            and self.is_clean == other.is_clean
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "hits": [h.to_dict() for h in self.hits],
            "is_clean": self.is_clean,
            "hit_count": len(self.hits),
        }


def scan_text_for_portable_references(
    file_path: str,
    content: str,
    *,
    strict: bool = False,
    allow_patterns: Sequence[str] = (),
) -> ScanReport:
    """Scans file content for non-portable local filesystem references.
    
    If strict=True and hits are found, raises NonPortableReferenceError.
    """
    lines = content.splitlines()
    hits: list[LocusHit] = []

    for line_idx, line in enumerate(lines, start=1):
        if any(allowed in line for allowed in allow_patterns):
            continue
        for p_idx, pattern in enumerate(NON_PORTABLE_PATTERNS):
            # finditer, not search. One hit per pattern per line silently
            # dropped every reference after the first, so a line naming two
            # non-portable paths reported one and the remediation loci were
            # incomplete.
            for match in pattern.finditer(line):
                hits.append(
                    LocusHit(
                        line_number=line_idx,
                        matched_text=match.group(0),
                        pattern_index=p_idx,
                    )
                )

    hit_tuple = tuple(hits)
    is_clean = len(hit_tuple) == 0

    if strict and not is_clean:
        raise NonPortableReferenceError(
            f"Strict scan failed: {len(hit_tuple)} non-portable local filesystem path(s) detected in '{file_path}'"
        )

    return ScanReport(
        file_path=file_path,
        hits=hit_tuple,
        is_clean=is_clean,
    )
