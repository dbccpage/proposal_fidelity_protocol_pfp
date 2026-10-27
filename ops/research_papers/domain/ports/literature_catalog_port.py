"""Protocol for Literature Catalog and Bibliography Resolution."""

from __future__ import annotations

from typing import Optional, Protocol

from ..models.bibliography import BibEntry


class LiteratureCatalogPort(Protocol):
    """Protocol for resolving literature citations and spine references."""

    def lookup_bib_entry(self, key: str) -> Optional[BibEntry]:
        """Looks up a BibEntry by key from the catalog."""
        ...

    def resolve_doi(self, doi: str) -> Optional[BibEntry]:
        """Resolves a DOI to a validated BibEntry."""
        ...

    def resolve_arxiv(self, arxiv_id: str) -> Optional[BibEntry]:
        """Resolves an arXiv ID to a validated BibEntry."""
        ...

    def validate_spine_reference(self, spine_id: str, eadc_family: str) -> bool:
        """Validates that spine_id is recognized and aligned with the declared EADC family."""
        ...
