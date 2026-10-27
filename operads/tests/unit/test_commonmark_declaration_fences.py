"""Selected CommonMark 0.31.2 section 4.5 rules at the public parser boundary."""

import hashlib

import pytest

from operads.domain.value_objects import SkillId
from operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)


def parse(source):
    return LosslessMarkdownParserAdapter().parse_document(
        SkillId("fences"), "skills/fences/SKILL.md", source,
    )


def assert_exact_partition(source, document):
    offset = 0
    for leaf in document.leaf_nodes:
        assert leaf.span.start_byte == offset
        offset = leaf.span.end_byte
    assert offset == len(source)
    assert b"".join(source[n.span.start_byte:n.span.end_byte] for n in document.leaf_nodes) == source
    assert document.raw_digest == type(document.raw_digest).sha256(hashlib.sha256(source).hexdigest())


@pytest.mark.parametrize("marker", ["```", "````", "~~~", "~~~~~"])
@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("indent", ["", "   "])
def test_declaration_variants_preserve_bytes_and_semantics(marker, ending, indent):
    source = ending.join([
        "## Ω", "### Child", "## Sibling", indent + marker + " \toewas.operation.v3\t ",
        indent + "operation_id: fences:run", indent + "inputs: []",
        " " + marker + marker[0] + " \t", "tail",
    ]).encode()
    result = parse(source)
    assert result.is_ok, result
    document = result.unwrap()
    assert str(document.operations[0].operation_id) == "fences:run"
    assert_exact_partition(source, document)
    fence = next(n for n in document.leaf_nodes if n.kind == "code_fence")
    assert fence.span.start_line == 4
    assert fence.span.start_col == 0
    assert fence.span.end_line == 7
    assert source[fence.span.start_byte:fence.span.end_byte].decode().endswith(" \t")
    baseline = parse(b"```oewas.operation.v3\noperation_id: fences:run\ninputs: []\n```").unwrap()
    assert document.semantic_digest == baseline.semantic_digest


@pytest.mark.parametrize("closer", ["~~~", "```", "```` trailing", "    ````", "````\u00a0"])
def test_invalid_closer_does_not_admit_declared_operation(closer):
    result = parse(("Ω\r\n````oewas.operation.v3\r\noperation_id: fences:run\r\n" + closer).encode())
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == "UNCLOSED_OEWAS_FENCE"
    assert error.locus == "skills/fences/SKILL.md:2"


def test_invalid_closers_are_literal_content_until_valid_closer():
    source = b"````text\n```\n~~~\n```` trailing\n    ````\n````` \t\nafter"
    document = parse(source).unwrap()
    fence = document.leaf_nodes[0]
    assert fence.kind == "code_fence"
    assert fence.content == "```\n~~~\n```` trailing\n    ````"
    assert document.leaf_nodes[-1].content == "\nafter"
    assert_exact_partition(source, document)


@pytest.mark.parametrize("source,expected", [
    (b"~~~text\n```oewas.operation.v3\noperation_id: hidden\n```", "```oewas.operation.v3\noperation_id: hidden\n```"),
    (b"```", ""),
    (b"~~~text\rbody", "body"),
    (b"~~~text\nbody\n", "body\n"),
    (b"~~~text\n~~~", ""),
    (b"   ~~~text\n a\n  b\n   c\n    d\n\te\n~~~", "a\nb\nc\n d\n e"),
])
def test_ordinary_fences_shield_declarations_and_deindent_content(source, expected):
    document = parse(source).unwrap()
    assert not document.operations
    assert document.leaf_nodes[0].kind == "code_fence"
    assert document.leaf_nodes[0].content == expected
    assert_exact_partition(source, document)


@pytest.mark.parametrize("source", [
    b"``oewas.operation.v3\noperation_id: hidden",
    b"    ```oewas.operation.v3\n    operation_id: hidden",
    b"\t~~~oewas.operation.v3\noperation_id: hidden",
    b"```oewas.operation.v3`\noperation_id: hidden",
])
def test_non_openers_remain_prose(source):
    document = parse(source).unwrap()
    assert not document.operations
    assert all(n.kind == "prose" for n in document.leaf_nodes)
    assert_exact_partition(source, document)


@pytest.mark.parametrize("info,body,code", [
    ("oewas.operand.v3", "[]", "MALFORMED_OPERAND_BLOCK"),
    ("oewas.operation.v3", "inputs: [broken", "MALFORMED_OEWAS_DECLARATION"),
    ("oewas.composition.v3", "slot_bindings: nope", "MALFORMED_SLOT_BINDINGS"),
])
def test_tilde_declarations_keep_existing_typed_refusals(info, body, code):
    result = parse(("intro\r  ~~~~" + info + "\r  " + body + "\r ~~~~").encode())
    assert result.is_err
    assert result.unwrap_err().code == code
    assert result.unwrap_err().locus == "skills/fences/SKILL.md:2"
