"""Edge-case fuzz test suite verifying AST recovery and error reporting for markdown parser."""

from __future__ import annotations

import unittest

from operads.domain.errors.domain_errors import DomainInvariantError
from operads.domain.value_objects.identifier import SkillId
from operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)


class TestMarkdownParserEdgeCaseFuzz(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = LosslessMarkdownParserAdapter()
        self.skill_id = SkillId("edge_case_skill")

    def test_unterminated_code_fence_preservation(self) -> None:
        """A declared operation needs an explicit closing fence, not silent omission."""
        raw_markdown = b"""# Header
Some introductory text.

```oewas.operation.v3
operation_id: "edge:op"
inputs: []
output: {}
This code fence is never closed by triple backticks!
"""
        res = self.parser.parse_document(self.skill_id, "skills/edge/SKILL.md", raw_markdown)
        self.assertTrue(res.is_err)
        self.assertEqual(res.unwrap_err().code, "UNCLOSED_OEWAS_FENCE")
        self.assertEqual(res.unwrap_err().locus, "skills/edge/SKILL.md:4")

    def test_malformed_yaml_syntax_returns_typed_domain_error_with_locus(self) -> None:
        """Malformed YAML syntax within an OEWAS block should return typed error with line locus."""
        bad_yaml_markdown = b"""# Header

```oewas.operation.v3
operation_id: "edge:op"
inputs: [ { unclosed dict
output: {
```
"""
        res = self.parser.parse_document(self.skill_id, "skills/bad/SKILL.md", bad_yaml_markdown)
        self.assertTrue(res.is_err)
        err = res.unwrap_err()
        self.assertIsInstance(err, DomainInvariantError)
        self.assertEqual(err.code, "MALFORMED_OEWAS_DECLARATION")
        self.assertIn("skills/bad/SKILL.md", err.locus)
        self.assertIn("3", err.locus)  # Starts at line 3

    def test_non_dictionary_yaml_returns_typed_domain_error(self) -> None:
        """Scalar or list YAML inside an OEWAS block should return typed error."""
        list_yaml_markdown = b"""# Header

```oewas.operation.v3
- "this is a list"
- "not a dictionary"
```
"""
        res = self.parser.parse_document(self.skill_id, "skills/list/SKILL.md", list_yaml_markdown)
        self.assertTrue(res.is_err)
        err = res.unwrap_err()
        self.assertIsInstance(err, DomainInvariantError)
        self.assertEqual(err.code, "MALFORMED_OPERATION_BLOCK")
        self.assertIn("must be a YAML dictionary", err.message)

    def test_invalid_enum_facet_returns_typed_domain_error(self) -> None:
        """Invalid enum values inside an OEWAS block should be caught and reported cleanly."""
        invalid_enum_markdown = b"""# Header

```oewas.operation.v3
operation_id: "edge:op"
authority_effect: "SuperUserUnrestricted"
```
"""
        res = self.parser.parse_document(self.skill_id, "skills/enum/SKILL.md", invalid_enum_markdown)
        self.assertTrue(res.is_err)
        err = res.unwrap_err()
        self.assertIsInstance(err, DomainInvariantError)
        self.assertEqual(err.code, "MALFORMED_OEWAS_DECLARATION")
        self.assertIn("SuperUserUnrestricted", err.message)

    def test_invalid_utf8_binary_payload_returns_encoding_error(self) -> None:
        """Non-UTF-8 binary bytes should return an ENCODING_ERROR domain error."""
        corrupt_bytes = b"\xff\xfe\xfa\x00\x80\x81\x82 corrupted binary"
        res = self.parser.parse_document(self.skill_id, "skills/corrupt/SKILL.md", corrupt_bytes)
        self.assertTrue(res.is_err)
        err = res.unwrap_err()
        self.assertIsInstance(err, DomainInvariantError)
        self.assertEqual(err.code, "ENCODING_ERROR")

    def test_multiple_interleaved_fences_with_mixed_languages(self) -> None:
        """Interleaved python, bash, and oewas fences should parse cleanly with accurate byte spans."""
        mixed_markdown = b"""# Multi-Fence Doc

```python
def foo():
    return 42
```

```oewas.operand.v3
operand_id: "op_input"
kind: "parameter"
body: "input param"
```

```bash
echo "hello world"
```

```oewas.operation.v3
operation_id: "edge:mixed_op"
inputs:
  - name: "in"
    colour_id: "Data"
    schema_ref: "schema:any:v1"
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: "out"
  colour_id: "Receipt"
  schema_ref: "schema:receipt:v1"
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
```
"""
        res = self.parser.parse_document(self.skill_id, "skills/mixed/SKILL.md", mixed_markdown)
        self.assertTrue(res.is_ok)
        doc = res.unwrap()
        self.assertEqual(len(doc.operands), 1)
        self.assertEqual(len(doc.operations), 1)
        self.assertEqual(len(doc.leaf_nodes), 9)  # 5 prose sections + 4 code fences
        reconstructed = b"".join(mixed_markdown[node.span.start_byte:node.span.end_byte] for node in doc.leaf_nodes)
        self.assertEqual(reconstructed, mixed_markdown)

    def test_multibyte_unicode_byte_span_accuracy(self) -> None:
        """Assert that multi-byte UTF-8 characters do not shift subsequent byte spans."""
        raw_markdown = """# Multi-Byte Math Header Φ₁ 🚀 ∇²ψ
Some text with unicode symbols: 𝒳 = 𝒴 ⊗ 𝒵 and emojis 🧠✨.

```oewas.operation.v3
operation_id: "edge:unicode_op"
inputs:
  - name: "in"
    colour_id: "Data"
    schema_ref: "schema:any:v1"
    schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
output:
  name: "out"
  colour_id: "Receipt"
  schema_ref: "schema:receipt:v1"
  schema_digest: "0000000000000000000000000000000000000000000000000000000000000000"
```

Trailing notes with greek letters α, β, γ.
""".encode("utf-8")

        res = self.parser.parse_document(self.skill_id, "skills/unicode/SKILL.md", raw_markdown)
        self.assertTrue(res.is_ok)
        doc = res.unwrap()
        self.assertEqual(len(doc.operations), 1)

        # Verify gap-free contiguous byte coverage
        current_byte = 0
        for node in doc.leaf_nodes:
            self.assertEqual(node.span.start_byte, current_byte)
            current_byte = node.span.end_byte

        self.assertEqual(current_byte, len(raw_markdown))

        # Verify 100% byte-exact reconstruction across multi-byte unicode spans
        reconstructed = b"".join(raw_markdown[node.span.start_byte:node.span.end_byte] for node in doc.leaf_nodes)
        self.assertEqual(reconstructed, raw_markdown)


if __name__ == "__main__":
    unittest.main()
