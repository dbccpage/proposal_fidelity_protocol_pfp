"""Port for lossless parsing of skill markdown documents."""

from __future__ import annotations

from abc import ABC, abstractmethod

from operations.domain.rop.result import Result
from ...domain.entities.skill_document_v3 import SkillDocumentV3
from ...domain.errors.domain_errors import OeopDomainError
from ...domain.value_objects.identifier import SkillId


class SkillDocumentParserPort(ABC):
    @abstractmethod
    def parse_document(
        self,
        skill_id: SkillId,
        relative_path: str,
        content: bytes,
    ) -> Result[SkillDocumentV3, OeopDomainError]:
        """Parse raw markdown bytes into a lossless SkillDocumentV3 aggregate."""
        pass
