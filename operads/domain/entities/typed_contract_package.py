"""A compiled, declaration-only package over existing OEWAS domain types."""

from __future__ import annotations

from dataclasses import dataclass

from ..anti_skills.anti_skill_v2 import AntiSkillFixtureBankV1, AntiSkillSpecV2
from ..capability_catalog_v1 import CapabilityCatalogV1
from ..prompt_hierarchy.models import PromptTreeNode
from .operation_v3 import OperationV3
from .skill_document_v3 import SkillDocumentV3


@dataclass(frozen=True, slots=True)
class CompiledTypedPackageV1:
    contracts_digest: str
    catalog: CapabilityCatalogV1
    operations: tuple[OperationV3, ...]
    documents: tuple[SkillDocumentV3, ...]
    anti_spec: AntiSkillSpecV2
    fixture_bank: AntiSkillFixtureBankV1
    packages: tuple[tuple[str, bytes], ...]
    prompt_attachments: tuple[PromptTreeNode, ...] = ()
    guidance_documents: tuple[SkillDocumentV3, ...] = ()

    @property
    def all_documents(self) -> tuple[SkillDocumentV3, ...]:
        """All selectable instructions; ``documents`` preserves the original audit pair."""
        return self.documents + self.guidance_documents
