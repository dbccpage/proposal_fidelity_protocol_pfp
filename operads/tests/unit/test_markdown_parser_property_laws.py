"""Examiner Class 1: Lossless Markdown Parser Property and Conservation Laws.

Theoretical Minimum:
1. INVARIANT: For any markdown document, parsed leaf node byte spans must form a strict partition of the
   input byte buffer: span[0].start == 0, span[i+1].start == span[i].end, span[-1].end == len(bytes),
   and b"".join(bytes[s.start:s.end]) == bytes.
2. BREAK: Parser skips whitespace between blocks, miscalculates multi-byte UTF-8 byte spans, or omits trailing prose.
3. WITNESS: Reconstructed bytes != input bytes or span continuity fails.
4. MUTATION: In markdown_parser_adapter.py, delete the trailing prose node append at line 143.
"""

from __future__ import annotations

import unittest

from operads.domain.value_objects import SkillId
from operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)


class TestMarkdownParserPropertyLaws(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = LosslessMarkdownParserAdapter()
        self.skill_id = SkillId("skill:prop_test")

    def test_property_gap_free_partition_over_generated_corpus(self) -> None:
        """Class 1: Asserts gap-free byte partition across 10 varied document templates."""
        templates = [
            # Template 1: Pure prose without fences
            b"# Heading 1\nSome introductory text.\n\nParagraph 2 with unicode \xe2\x9a\x9b\xef\xb8\x8f.\n",
            # Template 2: Single fence at beginning
            b"```oewas.operand.v3\noperand_id: op_1\nkind: goal\nbody: test\ndependencies: []\nemitted_observations: []\n```\nTrailing text.\n",
            # Template 3: Single fence at end
            b"Leading documentation before the fence.\n\n```oewas.operand.v3\noperand_id: op_2\nkind: goal\nbody: test2\ndependencies: []\nemitted_observations: []\n```",
            # Template 4: Multiple interleaved fences with blank lines
            b"P1\n\n```oewas.operand.v3\noperand_id: op_3\nkind: goal\nbody: b3\ndependencies: []\nemitted_observations: []\n```\n\nIntermediate P2\n\n```oewas.operand.v3\noperand_id: op_4\nkind: goal\nbody: b4\ndependencies: []\nemitted_observations: []\n```\n\nFinal P3\n",
            # Template 5: Non-OEWAS foreign code fences
            b"# Intro\n```python\ndef foo():\n    return 42\n```\nMiddle\n```bash\necho hello\n```\nEnd\n",
            # Template 6: Empty document
            b"",
            # Template 7: Only newlines
            b"\n\n\n\n",
            # Template 8: Heavy multi-byte UTF-8 prose with math symbols
            "# \u03a9-Engine \u2207\xb2\u03c8 \u2297 \u03a6\u2081\nSome complex math prose: \u2200 x \u2208 X, \u2203 y \u2208 Y.\n```oewas.operand.v3\noperand_id: op_math\nkind: instruction\nbody: solve\ndependencies: []\nemitted_observations: []\n```\nDone \U0001f389\n".encode("utf-8"),
        ]

        for idx, raw_bytes in enumerate(templates):
            res = self.parser.parse_document(
                skill_id=self.skill_id,
                relative_path=f"skills/template_{idx}/SKILL.md",
                content=raw_bytes,
            )
            self.assertTrue(res.is_ok, f"Template {idx} failed to parse: {res.unwrap_err() if res.is_err else ''}")
            doc = res.unwrap()

            if not raw_bytes:
                self.assertEqual(len(doc.leaf_nodes), 0)
                continue

            # Invariant 1: Gap-Free Contiguity
            current_byte = 0
            for node_idx, node in enumerate(doc.leaf_nodes):
                self.assertEqual(
                    node.span.start_byte,
                    current_byte,
                    f"Template {idx} Node {node_idx} start_byte {node.span.start_byte} != expected {current_byte}",
                )
                self.assertGreaterEqual(node.span.end_byte, node.span.start_byte)
                current_byte = node.span.end_byte

            self.assertEqual(
                current_byte,
                len(raw_bytes),
                f"Template {idx} total parsed bytes {current_byte} != raw length {len(raw_bytes)}",
            )

            # Invariant 2: Algebraic Conservation of Bytes
            reconstructed = b"".join(raw_bytes[n.span.start_byte:n.span.end_byte] for n in doc.leaf_nodes)
            self.assertEqual(
                reconstructed,
                raw_bytes,
                f"Template {idx} reconstructed bytes diverged from source",
            )


if __name__ == "__main__":
    unittest.main()
