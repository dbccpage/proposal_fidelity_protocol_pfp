"""SkillDocumentV3 Aggregate Root."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from ..value_objects.byte_span import SourceByteSpan
from ..value_objects.content_digest import ContentDigest
from ..value_objects.identifier import DocumentId, OperationId, SkillId
from ..value_objects.operands import InstructionOperand, ResidualPackageSpan
from .composition_v3 import CompositionV3
from .operation_v3 import OperationV3


@dataclass(frozen=True, slots=True)
class DocumentLeafNode:
    kind: str  # "frontmatter", "h1", "h2", "prose", "code_fence", "blank"
    span: SourceByteSpan
    content: str
    info_string: str = ""


@dataclass(slots=True)
class SkillDocumentV3:
    document_id: DocumentId
    skill_id: SkillId
    source_relative_path: str
    raw_digest: ContentDigest
    semantic_digest: ContentDigest
    leaf_nodes: Tuple[DocumentLeafNode, ...] = ()
    operands: Tuple[InstructionOperand, ...] = ()
    operations: Tuple[OperationV3, ...] = ()
    compositions: Tuple[CompositionV3, ...] = ()
    residual_spans: Tuple[ResidualPackageSpan, ...] = ()
    proven_root_operation_id: Optional[OperationId] = None

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.document_id == other.document_id and self.raw_digest == other.raw_digest

    def __hash__(self) -> int:
        return hash((type(self), self.document_id, self.raw_digest))

    def get_operation(self, op_id: OperationId) -> Optional[OperationV3]:
        for op in self.operations:
            if op.operation_id == op_id:
                return op
        return None
