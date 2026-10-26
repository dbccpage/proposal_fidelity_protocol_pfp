"""Comprehensive boundary and fuzz test suite for OEWAS V3 domain value objects and events."""

from __future__ import annotations

from datetime import datetime, timezone
import unittest

from omega_engine_operads.domain.errors.domain_errors import (
    AuthorityCeilingExceededError,
    DomainInvariantError,
    InvalidCompositionError,
    OeopDomainError,
    SchemaMismatchError,
    UnresolvedResidualError,
)
from omega_engine_operads.domain.events.domain_events import (
    CatalogCompiledV3,
    EstateCapturedV3,
)
from omega_engine_operads.domain.value_objects.byte_span import SourceByteSpan
from omega_engine_operads.domain.value_objects.content_digest import ContentDigest
from omega_engine_operads.domain.value_objects.identifier import (
    CausationId,
    ColourId,
    CorrelationId,
    DocumentId,
    EstateRef,
    IdempotencyKey,
    OperandId,
    OperationId,
    SchemaRef,
    SkillId,
    WorkflowId,
)


class TestDomainValueObjectsBoundaryAndFuzz(unittest.TestCase):
    def test_identifiers_type_and_length_fuzz(self) -> None:
        id_classes = [
            SkillId,
            OperationId,
            DocumentId,
            OperandId,
            WorkflowId,
            ColourId,
            SchemaRef,
            CorrelationId,
            CausationId,
            IdempotencyKey,
            EstateRef,
        ]

        # 1. Non-string types rejected
        invalid_types = [123, 45.67, True, False, None, [], {}, object()]
        for cls in id_classes:
            for bad_val in invalid_types:
                with self.assertRaises(TypeError, msg=f"{cls.__name__} should reject {bad_val}"):
                    cls(bad_val)  # type: ignore

        # 2. Empty or whitespace-only strings rejected
        empty_vals = ["", "   ", "\t", "\n\r", "   \t\n  "]
        for cls in id_classes:
            for empty_val in empty_vals:
                with self.assertRaises(ValueError, msg=f"{cls.__name__} should reject '{empty_val}'"):
                    cls(empty_val)

        # 3. Giant string (> 512 chars) rejected
        giant_string = "a" * 1024
        for cls in id_classes:
            with self.assertRaises(ValueError, msg=f"{cls.__name__} should reject giant string of length 1024"):
                cls(giant_string)

        # 4. Valid identifier trimming & exact-type equality
        valid_id = SkillId("  my_skill_01  ")
        self.assertEqual(valid_id.value, "my_skill_01")
        self.assertEqual(str(valid_id), "my_skill_01")
        self.assertEqual(valid_id, SkillId("my_skill_01"))
        self.assertNotEqual(valid_id, OperationId("my_skill_01"))

    def test_byte_span_boundary_and_type_fuzz(self) -> None:
        # 1. Reject floats, bools, strings
        bad_types = [1.5, "10", True, None, []]
        for bad in bad_types:
            with self.assertRaises(TypeError):
                SourceByteSpan(start_byte=bad, end_byte=10, start_line=1, start_col=0, end_line=1, end_col=10)  # type: ignore
            with self.assertRaises(TypeError):
                SourceByteSpan(start_byte=0, end_byte=bad, start_line=1, start_col=0, end_line=1, end_col=10)  # type: ignore
            with self.assertRaises(TypeError):
                SourceByteSpan(start_byte=0, end_byte=10, start_line=bad, start_col=0, end_line=1, end_col=10)  # type: ignore

        # 2. Reject negative start byte or inverted span
        with self.assertRaises(ValueError):
            SourceByteSpan(start_byte=-1, end_byte=10, start_line=1, start_col=0, end_line=1, end_col=10)
        with self.assertRaises(ValueError):
            SourceByteSpan(start_byte=20, end_byte=10, start_line=1, start_col=0, end_line=1, end_col=10)

        # 3. Reject invalid line span (line 0 or inverted line)
        with self.assertRaises(ValueError):
            SourceByteSpan(start_byte=0, end_byte=10, start_line=0, start_col=0, end_line=1, end_col=10)
        with self.assertRaises(ValueError):
            SourceByteSpan(start_byte=0, end_byte=10, start_line=5, start_col=0, end_line=2, end_col=10)

        # 4. Reject inverted columns on same line
        with self.assertRaises(ValueError):
            SourceByteSpan(start_byte=0, end_byte=10, start_line=1, start_col=15, end_line=1, end_col=5)

        # 5. Valid span
        span = SourceByteSpan(start_byte=100, end_byte=250, start_line=5, start_col=2, end_line=12, end_col=40)
        self.assertEqual(span.byte_length, 150)

    def test_content_digest_boundary_and_fuzz(self) -> None:
        # 1. Reject non-string types
        for bad in [123, 4.56, True, None, {}]:
            with self.assertRaises(TypeError):
                ContentDigest(algorithm=bad, hex_digest="a" * 64)  # type: ignore
            with self.assertRaises(TypeError):
                ContentDigest(algorithm="sha256", hex_digest=bad)  # type: ignore

        # 2. Reject empty strings
        with self.assertRaises(ValueError):
            ContentDigest(algorithm="  ", hex_digest="a" * 64)
        with self.assertRaises(ValueError):
            ContentDigest(algorithm="sha256", hex_digest="   ")

        # 3. Reject invalid hex characters or incorrect length for sha256
        with self.assertRaises(ValueError):
            ContentDigest("sha256", "not_a_valid_hex_string")
        with self.assertRaises(ValueError):
            ContentDigest("sha256", "a" * 63)
        with self.assertRaises(ValueError):
            ContentDigest("sha256", "a" * 65)

        # 4. Valid digest
        d = ContentDigest.sha256("A" * 64)
        self.assertEqual(d.algorithm, "sha256")
        self.assertEqual(d.hex_digest, "a" * 64)
        self.assertEqual(str(d), f"sha256:{'a'*64}")

    def test_domain_event_base_interface_and_polymorphism(self) -> None:
        # 1. Base DomainEventV3 type checks
        now = datetime.now(timezone.utc)
        corr = CorrelationId("corr-123")
        cause = CausationId("cause-456")

        # Must reject invalid types on creation
        with self.assertRaises(ValueError):
            EstateCapturedV3(event_id="", occurred_at=now, correlation_id=corr, causation_id=cause)
        with self.assertRaises(TypeError):
            EstateCapturedV3(event_id="e1", occurred_at="not_a_datetime", correlation_id=corr, causation_id=cause)  # type: ignore
        with self.assertRaises(TypeError):
            EstateCapturedV3(event_id="e1", occurred_at=now, correlation_id="raw_str", causation_id=cause)  # type: ignore

        # 2. Factory method create
        evt = CatalogCompiledV3.create(
            event_id="evt_001",
            correlation_id="corr-99",
            causation_id="cause-99",
            catalog_id="cat_alpha",
            epoch=2,
            total_skills=10,
            total_operations=25,
            catalog_digest=ContentDigest.empty_sha256(),
        )
        self.assertEqual(evt.event_name, "CatalogCompiledV3")
        self.assertEqual(evt.catalog_id, "cat_alpha")
        self.assertEqual(evt.epoch, 2)

        # 3. Serialization to dict
        d = evt.to_dict()
        self.assertEqual(d["event_id"], "evt_001")
        self.assertEqual(d["event_type"], "CatalogCompiledV3")
        self.assertEqual(d["correlation_id"], "corr-99")
        self.assertEqual(d["catalog_id"], "cat_alpha")
        self.assertEqual(d["epoch"], 2)
        self.assertEqual(d["schema_version"], 1)

    def test_domain_errors_hierarchy_and_formatting(self) -> None:
        err1 = DomainInvariantError(code="INVALID_EPOCH", message="Epoch must be >= 1", locus="CatalogV3.epoch")
        self.assertEqual(str(err1), "[INVALID_EPOCH @ CatalogV3.epoch] Epoch must be >= 1")
        self.assertTrue(isinstance(err1, OeopDomainError))

        err2 = SchemaMismatchError(code="SCHEMA_MISMATCH", message="Input schema mismatch")
        self.assertEqual(str(err2), "[SCHEMA_MISMATCH] Input schema mismatch")

        err3 = UnresolvedResidualError(code="UNRESOLVED_RESIDUAL", message="Missing residual evidence")
        err4 = AuthorityCeilingExceededError(code="AUTHORITY_EXCEEDED", message="Ceiling violated")
        err5 = InvalidCompositionError(code="INVALID_TREE", message="Cycle in tree")

        for err in (err1, err2, err3, err4, err5):
            self.assertTrue(issubclass(type(err), OeopDomainError))
            self.assertTrue(issubclass(type(err), Exception))


if __name__ == "__main__":
    unittest.main()
