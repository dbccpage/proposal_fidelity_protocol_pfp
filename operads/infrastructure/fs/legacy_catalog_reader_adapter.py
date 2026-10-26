"""Dual-read legacy catalog reader adapter."""

from __future__ import annotations

import hashlib
import pathlib
from typing import List, Optional, Tuple

from omega_engine_operations.domain.rop.result import Ok, Result

from ...application.ports.legacy_catalog_reader_port import LegacyCatalogReaderPort
from ...domain.entities.operation_v3 import OperationV3, PortSpecV3
from ...domain.entities.skill_document_v3 import DocumentLeafNode, SkillDocumentV3
from ...domain.errors.domain_errors import OeopDomainError
from ...domain.value_objects.authority import AuthorityEffect
from ...domain.value_objects.byte_span import SourceByteSpan
from ...domain.value_objects.content_digest import ContentDigest
from ...domain.value_objects.identifier import (
    ColourId,
    DocumentId,
    EstateRef,
    OperationId,
    SchemaRef,
    SkillId,
)
from ...domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)


class LegacyCatalogReaderAdapter(LegacyCatalogReaderPort):
    def __init__(self, base_path: Optional[pathlib.Path] = None) -> None:
        self._base_path = base_path or pathlib.Path.cwd()

    def read_legacy_estate(
        self,
        estate_ref: EstateRef,
    ) -> Result[Tuple[SkillDocumentV3, ...], OeopDomainError]:
        skills_dir = self._base_path / ".agents" / "skills"
        if not skills_dir.exists():
            return Ok(())

        docs: List[SkillDocumentV3] = []
        for p in sorted(skills_dir.glob("*/SKILL.md")):
            skill_name = p.parent.name
            skill_id = SkillId(skill_name)
            raw = p.read_bytes()
            raw_digest = ContentDigest.sha256(hashlib.sha256(raw).hexdigest())

            dummy_port = PortSpecV3(
                name="in",
                colour_id=ColourId("Prompt"),
                schema_ref=SchemaRef("schema:legacy:v1"),
                schema_digest=raw_digest,
                validator_ref="validator:legacy",
                validator_digest=raw_digest,
            )
            lifecycle = SkillLifecycleV3(
                declaration=DeclarationFacet.DECLARED,
                schema_binding=SchemaBindingFacet.ANY_SCHEMA,
                executor_binding=ExecutorBindingFacet.UNBOUND,
                validation=ValidationFacet.UNCHECKED,
                admission=AdmissionFacet.UNADMITTED,
            )
            op = OperationV3(
                operation_id=OperationId(f"{skill_name}:invoke"),
                inputs=(dummy_port,),
                output=dummy_port,
                operand_refs=(),
                lifecycle=lifecycle,
                residual_status="unknown",
                authority_effect=AuthorityEffect.NONE,
                authority_ceiling=AuthorityEffect.NONE,
            )
            span = SourceByteSpan(0, len(raw), 1, 0, max(1, len(raw.splitlines())), 0)
            leaf = DocumentLeafNode(kind="prose", span=span, content=raw.decode("utf-8", errors="replace"))

            doc = SkillDocumentV3(
                document_id=DocumentId(f"doc_{skill_name}"),
                skill_id=skill_id,
                source_relative_path=p.relative_to(self._base_path).as_posix(),
                raw_digest=raw_digest,
                semantic_digest=raw_digest,
                leaf_nodes=(leaf,),
                operands=(),
                operations=(op,),
                compositions=(),
                proven_root_operation_id=OperationId(f"{skill_name}:invoke"),
            )
            docs.append(doc)

        return Ok(tuple(docs))
