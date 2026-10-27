"""Paper specification and monograph envelope entities.

Adheres strictly to EADC addressing and Clean Architecture purity.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

_EADC_REGEX = re.compile(r"^EA:([0-9A-Za-z_-]{3,12})\.([0-9A-Za-z_-]{3,12})\.([0-9A-Za-z_-]{3,12})$")


@dataclass(frozen=True)
class EADCAddress:
    """EADC Decimal Classification Address: EA:FFF.SSS.BBB.

    FFF = Folder / Domain Family (e.g. F005)
    SSS = Sub-family / Subject (e.g. coda, cs_q)
    BBB = Branch / Bundle / Block (e.g. 001, pub)
    """

    family: str
    subject: str
    block: str

    def __post_init__(self) -> None:
        if not self.family or not self.subject or not self.block:
            raise ValueError("EADC parts must all be non-empty strings")

    @classmethod
    def parse(cls, raw: str) -> EADCAddress:
        match = _EADC_REGEX.match(raw.strip())
        if not match:
            raise ValueError(f"Invalid EADC address '{raw}'. Must match format EA:FFF.SSS.BBB")
        return cls(family=match.group(1), subject=match.group(2), block=match.group(3))

    def as_str(self) -> str:
        return f"EA:{self.family}.{self.subject}.{self.block}"

    def __str__(self) -> str:
        return self.as_str()


@dataclass(frozen=True)
class Section:
    """A section of a research monograph."""

    id: str
    title: str
    level: int
    content: str
    subsections: Tuple[Section, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.level < 1 or self.level > 6:
            raise ValueError("Section level must be between 1 and 6")
        if not self.title.strip():
            raise ValueError("Section title cannot be empty")


@dataclass(frozen=True)
class MonographEnvelope:
    """Immutable envelope containing the monograph text and structure."""

    title: str
    abstract: str
    sections: Tuple[Section, ...]
    keywords: Tuple[str, ...]
    version: str = "1.0.0"
    license: str = "CC-BY-4.0"
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Monograph title cannot be empty")
        if not self.abstract.strip():
            raise ValueError("Monograph abstract cannot be empty")
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


@dataclass(frozen=True)
class PaperSpecification:
    """Specification and metadata contract for a research paper publication."""

    paper_id: str
    title: str
    eadc_address: EADCAddress
    authors: Tuple[str, ...]
    abstract: str
    monograph: Optional[MonographEnvelope] = None
    target_venue: str = "Zenodo"
    status: str = "DRAFT"
    metadata_fields: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.paper_id.strip():
            raise ValueError("Paper ID cannot be empty")
        if not self.authors:
            raise ValueError("At least one author is required")
        if type(self.eadc_address) is not EADCAddress:
            raise TypeError("eadc_address must be an instance of EADCAddress")
