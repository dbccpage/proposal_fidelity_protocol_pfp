"""Bibliography and literature spine reference entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Set, Tuple


@dataclass(frozen=True)
class BibEntry:
    """Canonical bibliography entry."""

    key: str
    title: str
    authors: Tuple[str, ...]
    year: int
    venue: str = ""
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    bibtex_raw: str = ""

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("BibEntry key cannot be empty")
        if not self.title.strip():
            raise ValueError("BibEntry title cannot be empty")


@dataclass(frozen=True)
class LiteratureSpineRef:
    """Reference to an authoritative literature spine catalog."""

    spine_id: str
    topic: str
    primary_keys: Tuple[str, ...] = field(default_factory=tuple)
    related_eadc: Optional[str] = None


@dataclass(frozen=True)
class CitationGraph:
    """Graph of citations within a monograph."""

    entries: Tuple[BibEntry, ...] = field(default_factory=tuple)
    in_text_citations: Tuple[str, ...] = field(default_factory=tuple)

    def uncited_entries(self) -> Set[str]:
        all_keys = {e.key for e in self.entries}
        cited = set(self.in_text_citations)
        return all_keys - cited

    def missing_entries(self) -> Set[str]:
        all_keys = {e.key for e in self.entries}
        cited = set(self.in_text_citations)
        return cited - all_keys
