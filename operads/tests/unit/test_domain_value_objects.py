"""Unit tests for OEWAS V3 domain value objects."""

import unittest

from operads.domain.value_objects import (
    AUTHORITY_RANK,
    AdmissionFacet,
    AuthorityEffect,
    ContentDigest,
    DeclarationFacet,
    DocumentId,
    ExecutorBindingFacet,
    OperationId,
    SchemaBindingFacet,
    SkillId,
    SkillLifecycleV3,
    SourceByteSpan,
    ValidationFacet,
)


class ValueObjectTests(unittest.TestCase):
    def test_identifiers_exact_type_equality_and_hash(self) -> None:
        s1 = SkillId("my-skill")
        s2 = SkillId("my-skill")
        o1 = OperationId("my-skill")
        d1 = DocumentId("my-skill")

        self.assertEqual(s1, s2)
        self.assertEqual(hash(s1), hash(s2))

        # Cross-class type confusion rejected
        self.assertNotEqual(s1, o1)
        self.assertNotEqual(s1, d1)
        self.assertNotEqual(o1, d1)
        self.assertNotEqual(s1, "my-skill")

    def test_content_digest_exact_type_and_validation(self) -> None:
        hex_64 = "a" * 64
        d1 = ContentDigest.sha256(hex_64)
        d2 = ContentDigest("sha256", hex_64)
        self.assertEqual(d1, d2)
        self.assertEqual(hash(d1), hash(d2))

        with self.assertRaises(ValueError):
            ContentDigest.sha256("invalid_hex")

    def test_source_byte_span_invariants(self) -> None:
        span = SourceByteSpan(0, 100, 1, 0, 5, 20)
        self.assertEqual(span.byte_length, 100)

        with self.assertRaises(ValueError):
            SourceByteSpan(100, 50, 1, 0, 5, 20)  # end < start

        with self.assertRaises(ValueError):
            SourceByteSpan(0, 100, 5, 0, 2, 20)  # end_line < start_line

    def test_skill_lifecycle_facets(self) -> None:
        valid_digest = ContentDigest.sha256("b" * 64)
        exec_digest = ContentDigest.sha256("c" * 64)

        lifecycle_complete = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.BOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
            schema_digest=valid_digest,
            executor_digest=exec_digest,
        )
        self.assertTrue(lifecycle_complete.is_executable)
        self.assertFalse(
            SkillLifecycleV3(
                declaration=DeclarationFacet.DECLARED,
                schema_binding=SchemaBindingFacet.BOUND,
                executor_binding=ExecutorBindingFacet.BOUND,
                validation=ValidationFacet.VALIDATED,
                admission=AdmissionFacet.ADMITTED,
                schema_digest=ContentDigest.sha256("0" * 64),
                executor_digest=exec_digest,
            ).is_executable
        )

        lifecycle_unbound = SkillLifecycleV3(
            declaration=DeclarationFacet.DECLARED,
            schema_binding=SchemaBindingFacet.UNBOUND,
            executor_binding=ExecutorBindingFacet.BOUND,
            validation=ValidationFacet.VALIDATED,
            admission=AdmissionFacet.ADMITTED,
        )
        self.assertFalse(lifecycle_unbound.is_executable)

    def test_authority_rank_ordering(self) -> None:
        self.assertLess(
            AUTHORITY_RANK[AuthorityEffect.NONE],
            AUTHORITY_RANK[AuthorityEffect.EVIDENCE_ONLY],
        )
        self.assertLess(
            AUTHORITY_RANK[AuthorityEffect.EVIDENCE_ONLY],
            AUTHORITY_RANK[AuthorityEffect.STATE_TRANSITION],
        )
