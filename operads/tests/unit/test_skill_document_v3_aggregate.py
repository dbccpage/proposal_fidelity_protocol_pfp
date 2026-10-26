"""Unit tests for OEWAS V3 SkillDocumentV3 and OperationV3 entities."""

import unittest
from datetime import datetime, timezone

from omega_engine_operads.domain.entities import (
    CapabilitySliceV3,
    DocumentLeafNode,
    EstateCatalogV3,
    OperationV3,
    PortSpecV3,
    SkillDocumentV3,
)
from omega_engine_operads.domain.value_objects import (
    AdmissionFacet,
    AuthorityEffect,
    ColourId,
    ContentDigest,
    DeclarationFacet,
    DocumentId,
    EstateRef,
    ExecutorBindingFacet,
    InstructionOperand,
    OperandId,
    OperationId,
    SchemaBindingFacet,
    SchemaRef,
    SkillId,
    SkillLifecycleV3,
    SourceByteSpan,
    ValidationFacet,
)


class DomainEntityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dummy_digest = ContentDigest.sha256("f" * 64)
        self.span = SourceByteSpan(0, 50, 1, 0, 3, 10)
        self.lifecycle = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.BOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
            schema_digest=self.dummy_digest,
            executor_digest=self.dummy_digest,
        )
        self.port_in = PortSpecV3(
            name="input_code",
            colour_id=ColourId("Code"),
            schema_ref=SchemaRef("schema:code:v1"),
            schema_digest=self.dummy_digest,
            validator_ref="validator:code",
            validator_digest=self.dummy_digest,
        )
        self.port_out = PortSpecV3(
            name="output_audit",
            colour_id=ColourId("Audit"),
            schema_ref=SchemaRef("schema:audit:v1"),
            schema_digest=self.dummy_digest,
            validator_ref="validator:audit",
            validator_digest=self.dummy_digest,
        )

    def test_operation_effect_ceiling_guard(self) -> None:
        # Legal: effect <= ceiling
        op = OperationV3(
            operation_id=OperationId("audit_code"),
            inputs=(self.port_in,),
            output=self.port_out,
            operand_refs=(OperandId("clause_1"),),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        self.assertEqual(op.operation_id, OperationId("audit_code"))

        # Illegal: effect > ceiling
        with self.assertRaises(ValueError):
            OperationV3(
                operation_id=OperationId("illegal_op"),
                inputs=(self.port_in,),
                output=self.port_out,
                operand_refs=(OperandId("clause_1"),),
                lifecycle=self.lifecycle,
                residual_status="unknown",
                authority_effect=AuthorityEffect.STATE_TRANSITION,
                authority_ceiling=AuthorityEffect.NONE,
            )

    def test_skill_document_aggregate_and_catalog(self) -> None:
        op = OperationV3(
            operation_id=OperationId("audit_code"),
            inputs=(self.port_in,),
            output=self.port_out,
            operand_refs=(OperandId("clause_1"),),
            lifecycle=self.lifecycle,
            residual_status="verified",
            authority_effect=AuthorityEffect.NONE,
            authority_ceiling=AuthorityEffect.NONE,
        )
        operand = InstructionOperand(
            operand_id=OperandId("clause_1"),
            kind="instruction",
            instruction_body="verify clean architecture boundaries",
            span=self.span,
        )
        leaf = DocumentLeafNode(
            kind="prose",
            span=self.span,
            content="Audit instructions",
        )
        doc = SkillDocumentV3(
            document_id=DocumentId("doc-audit"),
            skill_id=SkillId("code-auditor"),
            source_relative_path="skills/code-auditor/SKILL.md",
            raw_digest=self.dummy_digest,
            semantic_digest=self.dummy_digest,
            leaf_nodes=(leaf,),
            operands=(operand,),
            operations=(op,),
            compositions=(),
            proven_root_operation_id=OperationId("audit_code"),
        )
        self.assertEqual(doc.get_operation(OperationId("audit_code")), op)

        catalog = EstateCatalogV3(
            catalog_id="catalog-001",
            estate_ref=EstateRef("canonical"),
            epoch=1,
            compiled_at=datetime.now(timezone.utc),
            skills={SkillId("code-auditor"): doc},
            operations={OperationId("audit_code"): op},
            capability_slices={"audit": CapabilitySliceV3("audit", "Auditing", (OperationId("audit_code"),))},
            aliases={},
            catalog_digest=self.dummy_digest,
        )
        self.assertEqual(catalog.total_skills, 1)
        self.assertEqual(catalog.total_operations, 1)
