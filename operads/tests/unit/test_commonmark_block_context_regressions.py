"""Deciding counterexamples found during the container/HTML peer review."""

import pytest

from operads.domain.value_objects import SkillId
from operads.infrastructure.parser.markdown_parser_adapter import LosslessMarkdownParserAdapter


FENCE = "~~~oewas.operation.v3\noperation_id: visible\ninputs: []\n~~~"


def ids(source):
    result = LosslessMarkdownParserAdapter().parse_document(SkillId("review"), "review.md", source.encode())
    assert result.is_ok, result
    return [str(op.operation_id) for op in result.unwrap().operations]


@pytest.mark.parametrize("initial,marker", [("1.", "2."), ("1)", "2)"), ("1.", "123."), ("1.", "2)")])
def test_ordered_sibling_is_not_a_lazy_paragraph_continuation(initial, marker):
    indent = " " * (len(marker) + 1)
    assert ids(initial + " paragraph\n" + marker + " " + FENCE.replace("\n", "\n" + indent)) == ["visible"]


@pytest.mark.parametrize("tag", ["pre", "SCRIPT", "style", "textarea"])
def test_raw_self_closing_open_tag_cannot_start_type_seven(tag):
    assert ids("<" + tag + "/>\n" + FENCE) == ["visible"]


@pytest.mark.parametrize("tag", ["ſcript", "dıv"])
def test_non_ascii_case_folding_cannot_create_html_block_tags(tag):
    assert ids("<" + tag + ">\n" + FENCE) == ["visible"]


def test_non_ascii_attribute_value_is_a_valid_complete_html_tag():
    assert ids("<custom data-x=\u00a0>\n" + FENCE) == []


def test_non_ascii_end_tag_cannot_terminate_a_raw_html_block():
    assert ids("<script>\n</ſtyle>\n" + FENCE) == []


def test_new_non_one_ordered_list_still_cannot_interrupt_an_unrelated_paragraph():
    # The standalone ~~~ opens an ordinary fence; the later declaration stays literal.
    assert ids("paragraph\n2. ~~~oewas.operation.v3\n   operation_id: hidden\n   ~~~\n\n" + FENCE) == []


def test_quote_container_exit_cannot_be_mistaken_for_an_ordered_sibling():
    assert ids("> 1. paragraph\n2. ordinary text\n\n" + FENCE) == ["visible"]
