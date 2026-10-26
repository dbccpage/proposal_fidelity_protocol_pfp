"""Frontmatter is metadata, not an alternative V3 declaration carrier."""

import hashlib

import pytest

from omega_engine_operads.domain.value_objects import SkillId
from omega_engine_operads.domain.value_objects.lifecycle_facets import AdmissionFacet
from omega_engine_operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)


BODY = "~~~oewas.operation.v3\noperation_id: body:real\ninputs: []\n~~~\n"
EXAMPLES = [
    "~~~oewas.operation.v3\noperation_id: header:phantom\ninputs: []\n~~~",
    "~~~oewas.operand.v3\noperand_id: header:phantom\nbody: metadata only\n~~~",
    "~~~oewas.composition.v3\ncomposition_id: header:phantom\n~~~",
    "~~~oewas.operation.v3\ninputs: [broken\n~~~",
    "~~~oewas.operation.v3\noperation_id: header:unclosed",
    "~~~python\n# An unclosed example must not hide the real body",
]


def _header(example: str) -> str:
    return "---\nname: fixture\ndescription: |\n  Ω metadata\n" + "".join(
        "  " + line + "\n" for line in example.splitlines()
    ) + "---\n"


def _parse(raw: bytes):
    return LosslessMarkdownParserAdapter().parse_document(SkillId("fixture"), "skill.md", raw)


@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"])
@pytest.mark.parametrize("example", EXAMPLES)
def test_header_examples_are_literal_and_body_retains_physical_spans(ending, example):
    raw = (_header(example) + BODY).replace("\n", ending).encode("utf-8")
    result = _parse(raw)
    assert result.is_ok, result
    document = result.unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["body:real"]
    assert not document.operands and not document.compositions
    assert document.operations[0].lifecycle.admission is AdmissionFacet.UNADMITTED
    assert not document.operations[0].lifecycle.is_executable
    assert str(document.raw_digest) == "sha256:" + hashlib.sha256(raw).hexdigest()
    assert b"".join(raw[leaf.span.start_byte:leaf.span.end_byte] for leaf in document.leaf_nodes) == raw
    assert document.leaf_nodes[0].kind == "prose"
    assert document.leaf_nodes[0].content == _header(example).replace("\n", ending)
    fence = next(leaf for leaf in document.leaf_nodes if leaf.kind == "code_fence")
    assert fence.span.start_byte == len(_header(example).replace("\n", ending).encode("utf-8"))
    assert fence.span.start_line == len(_header(example).splitlines()) + 1


def test_header_changes_raw_identity_without_changing_body_declaration_identity():
    first = _parse((_header(EXAMPLES[0]) + BODY).encode()).unwrap()
    second = _parse((_header(EXAMPLES[0].replace("phantom", "different")) + BODY).encode()).unwrap()
    plain = _parse(BODY.encode()).unwrap()
    assert first.raw_digest != second.raw_digest
    assert first.semantic_digest == second.semantic_digest == plain.semantic_digest
    assert first.operations == second.operations == plain.operations


@pytest.mark.parametrize("prefix", [
    "", "---\n", "---\nordinary Markdown\n---\n", "---\n[one, two]\n---\n",
    "---\nname: [broken\n---\n", "---\nname: one\nname: two\n---\n",
    "---\nname: fixture\n--- trailing text\n", "\n---\nname: fixture\n---\n",
])
def test_non_frontmatter_prefix_keeps_existing_markdown_behavior(prefix):
    document = _parse((prefix + BODY).encode()).unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["body:real"]


def test_malformed_real_body_declaration_still_refuses_at_original_line():
    header = _header(EXAMPLES[0])
    result = _parse((header + "~~~oewas.operation.v3\ninputs: wrong\n~~~\n").encode())
    assert result.is_err
    error = result.unwrap_err()
    assert error.code == "MALFORMED_OPERATION_INPUTS"
    assert error.locus == f"skill.md:{len(header.splitlines()) + 1}"


def test_frontmatter_claimed_admission_and_operad_metadata_cannot_create_an_operation():
    raw = b"---\nname: fixture\nadmission: Admitted\noperad_arity: 0\noperad_target_colour: Proof\n---\n"
    document = _parse(raw).unwrap()
    assert not document.operations and document.proven_root_operation_id is None
    assert document.leaf_nodes[0].content.encode() == raw
