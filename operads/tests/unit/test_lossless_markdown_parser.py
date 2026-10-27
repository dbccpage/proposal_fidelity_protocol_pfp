"""Unit tests for lossless CommonMark parser adapter."""

import unittest

from operads.domain.value_objects import (
    AuthorityEffect,
    OperandId,
    OperationId,
    SkillId,
)
from operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    ValidationFacet,
)
from operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)

SAMPLE_MARKDOWN = b"""# Skill: My Skill

This is documentation prose.

```oewas.operand.v3
operand_id: op_auth_1
kind: instruction
body: enforce clean architecture
dependencies: []
emitted_observations:
  - obs_clean_arch
```

More intermediate documentation prose.

```oewas.operation.v3
operation_id: my_skill:audit
declaration: Declared
schema_binding: Bound
executor_binding: Bound
validation: Validated
admission: Admitted
authority_effect: None
authority_ceiling: None
residual_status: verified
inputs:
  - name: code_in
    colour_id: Code
    schema_ref: schema:code:v1
    schema_digest: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
output:
  name: audit_out
  colour_id: Audit
  schema_ref: schema:audit:v1
  schema_digest: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
operand_refs:
  - op_auth_1
```

```oewas.composition.v3
composition_id: comp_1
term_kind: primitive
root_operation_id: my_skill:audit
child_operation_ids: []
slot_bindings: []
expected_boundary: Code -> Audit
```

Final trailing prose.
"""


class LosslessMarkdownParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = LosslessMarkdownParserAdapter()

    def test_parse_sample_document_extracts_leaves_operands_and_operations(self) -> None:
        res = self.parser.parse_document(
            skill_id=SkillId("my_skill"),
            relative_path="skills/my_skill/SKILL.md",
            content=SAMPLE_MARKDOWN,
        )
        self.assertTrue(res.is_ok)
        doc = res.unwrap()

        self.assertEqual(doc.skill_id, SkillId("my_skill"))
        self.assertEqual(len(doc.leaf_nodes), 7)  # prose, fence, prose, fence, prose(blank), fence, prose
        self.assertEqual(len(doc.operands), 1)
        self.assertEqual(doc.operands[0].operand_id, OperandId("op_auth_1"))
        self.assertEqual(doc.operands[0].instruction_body, "enforce clean architecture")

        self.assertEqual(len(doc.operations), 1)
        op = doc.operations[0]
        self.assertEqual(op.operation_id, OperationId("my_skill:audit"))
        self.assertEqual(op.authority_effect, AuthorityEffect.NONE)
        self.assertEqual(len(op.inputs), 1)
        self.assertEqual(op.inputs[0].name, "code_in")
        self.assertEqual(op.lifecycle.admission, AdmissionFacet.UNADMITTED)
        self.assertFalse(op.lifecycle.is_executable)

        self.assertEqual(len(doc.compositions), 1)
        comp = doc.compositions[0]
        self.assertEqual(comp.composition_id, "comp_1")
        self.assertEqual(comp.term_kind, "primitive")

    def test_reconstruct_exact_bytes_from_spans(self) -> None:
        res = self.parser.parse_document(
            skill_id=SkillId("my_skill"),
            relative_path="skills/my_skill/SKILL.md",
            content=SAMPLE_MARKDOWN,
        )
        self.assertTrue(res.is_ok)
        doc = res.unwrap()

        # Verify gap-free byte coverage
        current_byte = 0
        for leaf in doc.leaf_nodes:
            self.assertEqual(leaf.span.start_byte, current_byte)
            current_byte = leaf.span.end_byte
        self.assertEqual(current_byte, len(SAMPLE_MARKDOWN))

    def test_omitted_bindings_fail_closed(self) -> None:
        content = b"""```oewas.operation.v3
operation_id: minimal:audit
output:
  name: result
  colour_id: Audit
```"""
        result = self.parser.parse_document(SkillId("minimal"), "minimal.md", content)
        self.assertTrue(result.is_ok)
        lifecycle = result.unwrap().operations[0].lifecycle
        self.assertEqual(lifecycle.schema_binding, SchemaBindingFacet.UNBOUND)
        self.assertEqual(lifecycle.executor_binding, ExecutorBindingFacet.UNBOUND)
        self.assertEqual(lifecycle.validation, ValidationFacet.UNCHECKED)
        self.assertEqual(lifecycle.admission, AdmissionFacet.UNADMITTED)
        self.assertIsNone(lifecycle.schema_digest)
        self.assertIsNone(lifecycle.executor_digest)
        self.assertFalse(lifecycle.is_executable)

    def test_semantic_digest_covers_operation_contract(self) -> None:
        original = self.parser.parse_document(SkillId("my_skill"), "skill.md", SAMPLE_MARKDOWN)
        changed = self.parser.parse_document(
            SkillId("my_skill"), "skill.md",
            SAMPLE_MARKDOWN.replace(b"colour_id: Audit", b"colour_id: Receipt"),
        )
        self.assertTrue(original.is_ok)
        self.assertTrue(changed.is_ok)
        self.assertNotEqual(original.unwrap().semantic_digest, changed.unwrap().semantic_digest)

    def test_slot_bindings_keep_integer_indices(self) -> None:
        source = SAMPLE_MARKDOWN.replace(
            b"slot_bindings: []", b"slot_bindings:\n  - [0, my_skill:audit]"
        )
        parsed = self.parser.parse_document(SkillId("my_skill"), "skill.md", source)
        self.assertTrue(parsed.is_ok)
        self.assertEqual(parsed.unwrap().compositions[0].slot_bindings[0][0], 0)
