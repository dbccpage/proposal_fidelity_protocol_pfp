"""Container ownership and HTML precedence at the public declaration boundary."""

import pytest

from omega_engine_operads.domain.value_objects import SkillId
from omega_engine_operads.domain.value_objects.lifecycle_facets import AdmissionFacet
from omega_engine_operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)


def declaration(name="visible"):
    return f"~~~oewas.operation.v3\noperation_id: {name}\ninputs: []\n~~~"


def parse(source):
    return LosslessMarkdownParserAdapter().parse_document(SkillId("containers"), "context.md", source)


def assert_bytes(source, document):
    offset = 0
    for node in document.leaf_nodes:
        assert node.span.start_byte == offset
        offset = node.span.end_byte
    assert offset == len(source)
    assert b"".join(source[n.span.start_byte:n.span.end_byte] for n in document.leaf_nodes) == source


@pytest.mark.parametrize("first,continuation", [
    ("> ", "> "), (">> ", ">> "), ("- ", "  "), ("12) ", "    "),
    ("> - ", ">   "), ("- > ", "  > "), ("- - ", "    "),
    ("-\t", "\t"), (">\t", ">\t"),
])
@pytest.mark.parametrize("ending", ["\n", "\r\n", "\r"])
def test_nested_container_declarations_keep_physical_spans_and_semantics(first, continuation, ending):
    lines = declaration().split("\n")
    source = ("Ω" + ending * 2 + first + (ending + continuation).join(lines) + ending + "tail").encode()
    result = parse(source)
    assert result.is_ok, result
    document = result.unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["visible"]
    assert document.operations[0].lifecycle.admission == AdmissionFacet.UNADMITTED
    assert document.semantic_digest == parse(declaration().encode()).unwrap().semantic_digest
    fence = next(n for n in document.leaf_nodes if n.kind == "code_fence")
    assert fence.span.start_byte == len(("Ω" + ending * 2).encode())
    assert fence.span.start_line == 3
    assert fence.span.end_line == 6
    assert_bytes(source, document)


def test_list_continuation_after_blank_and_different_quote_indentation():
    source = ("- item\n\n  " + declaration().replace("\n", "\n  ") +
              "\n\n > ~~~~oewas.operation.v3\n  > operation_id: second\n> ~~~~~\n").encode()
    document = parse(source).unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["visible", "second"]
    assert_bytes(source, document)


@pytest.mark.parametrize("first,body,outside", [
    ("> ", "> ", ""), ("- ", "  ", "- next\n"), ("> - ", ">   ", "> next\n"),
])
def test_outer_closer_cannot_close_a_declared_container_fence(first, body, outside):
    source = ("intro\n" + first + "~~~oewas.operation.v3\n" + body +
              "operation_id: hidden\n" + outside + "~~~\n").encode()
    result = parse(source)
    assert result.is_err
    assert result.unwrap_err().code == "UNCLOSED_OEWAS_FENCE"
    assert result.unwrap_err().locus == "context.md:2"


def test_ordinary_fence_ends_with_its_container_without_swallowing_outer_declaration():
    source = ("> ````text\n> ~~~oewas.operation.v3\n> operation_id: hidden\n> ~~~\n" +
              declaration()).encode()
    document = parse(source).unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["visible"]
    assert document.leaf_nodes[0].content.endswith("operation_id: hidden\n~~~\n")
    assert_bytes(source, document)


@pytest.mark.parametrize("start,terminator", [
    ("<pre>", "</style>"), ("<SCRIPT type='x'>", "</script>"),
    ("<style", "</style>"), ("<textarea>", "</textarea>"),
    ("<!--", "-->"), ("<?target", "?>"), ("<!DOCTYPE", ">"),
    ("<![CDATA[", "]]>"), ("<div class", ""), ("</table>", ""),
    ("<custom data-x='>'>", ""), ("</custom>", ""),
])
def test_all_seven_html_block_types_shield_fences_then_resume(start, terminator):
    source = (start + "\n" + declaration("hidden") + "\n" + terminator + "\n" + declaration()).encode()
    document = parse(source).unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["visible"]
    assert_bytes(source, document)


@pytest.mark.parametrize("line", ["<!-- -->", "<?x?>", "<!DOCTYPE x>", "<![CDATA[]]>", "<pre></pre>"])
def test_same_line_html_terminators_do_not_swallow_the_next_fence(line):
    document = parse((line + "\n" + declaration()).encode()).unwrap()
    assert len(document.operations) == 1


def test_type_six_ignores_nested_html_start_and_ends_only_at_blank_line():
    source = ("<div></div>\n<pre>\n" + declaration("hidden") + "\n\n" + declaration()).encode()
    document = parse(source).unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["visible"]
    assert_bytes(source, document)


@pytest.mark.parametrize("prefix,expect_visible", [
    ("paragraph\n<custom>\n", True), ("paragraph\n<div>\n", False),
    ("paragraph\n<!--\n", False), ("# heading\n<custom>\n", False),
    ("heading\n===\n<custom>\n", False), ("<custom attr=>\n", True),
    ("<custom>inline</custom>\n", True), ("    <div>\n", True),
    ("&lt;div>\n", True), ("[ref]: /url\n<custom>\n", False),
])
def test_html_start_requires_correct_block_and_paragraph_context(prefix, expect_visible):
    document = parse((prefix + declaration()).encode()).unwrap()
    assert bool(document.operations) == expect_visible


@pytest.mark.parametrize("first,continuation", [("- ", "  "), ("> ", "> "), ("> - ", ">   ")])
def test_html_block_ends_at_its_container_boundary(first, continuation):
    inner = "<pre>\n" + declaration("hidden")
    source = (first + inner.replace("\n", "\n" + continuation) + "\n" + declaration()).encode()
    document = parse(source).unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["visible"]
    assert_bytes(source, document)


def test_html_markers_in_code_and_indented_container_markers_stay_literal():
    source = ("````text\n<div>\n> - ~~~oewas.operation.v3\n````\n\n"
              "    > ~~~oewas.operation.v3\n    > operation_id: hidden\n    > ~~~\n" +
              declaration()).encode()
    document = parse(source).unwrap()
    assert [str(op.operation_id) for op in document.operations] == ["visible"]
    assert_bytes(source, document)
