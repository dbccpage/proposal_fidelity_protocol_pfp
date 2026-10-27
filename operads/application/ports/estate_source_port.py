"""Port for reading skill source documents from an estate."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from operations.domain.rop.result import Ok, Result
from ...domain.entities.skill_document_v3 import SkillDocumentV3
from ...domain.errors.domain_errors import OeopDomainError
from ...domain.value_objects.identifier import EstateRef


class EstateSourcePort(ABC):
    def read_compiled_skill_document(
        self, relative_path: str
    ) -> Result[SkillDocumentV3 | None, OeopDomainError]:
        """Return an already typed source, or None for the Markdown parser."""
        return Ok(None)

    @abstractmethod
    def list_skill_paths(self, estate_ref: EstateRef) -> Result[Tuple[str, ...], OeopDomainError]:
        """List all relative skill document paths (e.g. skills/my-skill/SKILL.md)."""
        pass

    @abstractmethod
    def read_skill_bytes(self, relative_path: str) -> Result[bytes, OeopDomainError]:
        """Read raw bytes of a skill markdown document."""
        pass
