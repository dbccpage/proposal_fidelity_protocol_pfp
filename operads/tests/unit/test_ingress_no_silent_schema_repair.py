"""Public parser refusal and byte-custody controls. AuthorityEffect: None."""

from __future__ import annotations

import hashlib

import pytest

from omega_engine_operads.domain.errors.domain_errors import DomainInvariantError
from omega_engine_operads.domain.value_objects.identifier import SkillId
from omega_engine_operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
)
from omega_engine_operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)


def test_scalar_operation_inputs_are_refused_with_document_locus() -> None:
    content = (
        "# Φ ingress\n\n```oewas.operation.v3\n"
        "operation_id: ingress:audit\ninputs: Code\n```\n"
    ).encode("utf-8")

    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), ".agents/skills/ingress/SKILL.md", content
    )

    assert result.is_err, "Scalar inputs must not be silently compiled as a nullary operation"
    error = result.unwrap_err()
    assert isinstance(error, DomainInvariantError)
    assert error.code == "MALFORMED_OPERATION_INPUTS"
    assert error.locus == ".agents/skills/ingress/SKILL.md:3"


@pytest.mark.parametrize("yaml_inputs", ["null", "false", "7", "{name: code}"])
def test_present_non_list_inputs_are_not_treated_as_absent(yaml_inputs: str) -> None:
    content = (
        "```oewas.operation.v3\noperation_id: ingress:audit\n"
        f"inputs: {yaml_inputs}\n```\n"
    ).encode("utf-8")

    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), "ingress.md", content
    )

    assert result.is_err
    assert result.unwrap_err().code == "MALFORMED_OPERATION_INPUTS"
    assert result.unwrap_err().locus == "ingress.md:1"


@pytest.mark.parametrize("inputs_line", ["", "inputs: []\n"])
def test_omitted_or_empty_inputs_remain_valid(inputs_line: str) -> None:
    content = (
        "```oewas.operation.v3\noperation_id: ingress:audit\n"
        f"{inputs_line}```\n"
    ).encode("utf-8")

    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), "ingress.md", content
    )

    assert result.is_ok, result
    assert result.unwrap().operations[0].inputs == ()
    assert result.unwrap().operations[0].lifecycle.admission is AdmissionFacet.UNADMITTED


def test_valid_utf8_bytes_and_port_are_preserved_without_self_admission() -> None:
    content = (
        "# Φ ingress 🚀\n\n### Nested\n\n## Sibling\n\n"
        "```oewas.operation.v3\n"
        "operation_id: ingress:audit\n"
        "declaration: Declared\nschema_binding: Bound\nexecutor_binding: Bound\n"
        "validation: Validated\nadmission: Admitted\n"
        f"schema_digest: {'a' * 64}\nexecutor_digest: {'b' * 64}\n"
        "inputs:\n  - name: code\n    colour_id: Code\n"
        "    schema_ref: schema:code:v1\n"
        f"    schema_digest: {'c' * 64}\n"
        "output:\n  name: audit\n  colour_id: Audit\n```\n\nTrailing Ω.\n"
    ).encode("utf-8")

    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), ".agents/skills/ingress/SKILL.md", content
    )

    assert result.is_ok, result
    document = result.unwrap()
    assert document.raw_digest.hex_digest == hashlib.sha256(content).hexdigest()
    assert document.source_relative_path == ".agents/skills/ingress/SKILL.md"
    assert len(document.operations) == 1
    operation = document.operations[0]
    assert [(port.name, str(port.colour_id)) for port in operation.inputs] == [("code", "Code")]
    assert str(operation.inputs[0].schema_ref) == "schema:code:v1"
    assert operation.inputs[0].schema_digest.hex_digest == "c" * 64
    assert operation.lifecycle.admission is AdmissionFacet.UNADMITTED
    assert operation.lifecycle.schema_digest is not None
    assert operation.lifecycle.schema_digest.hex_digest == "a" * 64
    assert operation.lifecycle.executor_digest is not None
    assert operation.lifecycle.executor_digest.hex_digest == "b" * 64
    assert operation.lifecycle.is_executable is False
    previous_end = 0
    for leaf in document.leaf_nodes:
        assert leaf.span.start_byte == previous_end
        previous_end = leaf.span.end_byte
    assert previous_end == len(content)
    assert b"".join(
        content[leaf.span.start_byte:leaf.span.end_byte] for leaf in document.leaf_nodes
    ) == content


def test_invalid_utf8_remains_a_typed_encoding_refusal() -> None:
    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), "ingress.md", b"# ingress\n\xff\n"
    )

    assert result.is_err
    assert isinstance(result.unwrap_err(), DomainInvariantError)
    assert result.unwrap_err().code == "ENCODING_ERROR"


@pytest.mark.parametrize("yaml_body", ["Code", "null", "[Code]"])
def test_non_mapping_operation_block_remains_refused(yaml_body: str) -> None:
    content = (f"# Ω\n\n```oewas.operation.v3\n{yaml_body}\n```\n").encode("utf-8")

    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), "ingress.md", content
    )

    assert result.is_err
    assert result.unwrap_err().code == "MALFORMED_OPERATION_BLOCK"
    assert result.unwrap_err().locus == "ingress.md:3"



def test_non_mapping_operation_input_entry_is_refused_at_its_index() -> None:
    content = (
        "# Φ ingress\n\n```oewas.operation.v3\noperation_id: ingress:audit\n"
        "inputs:\n  - name: code\n    colour_id: Code\n  - State\n```\n"
    ).encode("utf-8")

    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), ".agents/skills/ingress/SKILL.md", content
    )

    assert result.is_err, "A scalar port must not be silently dropped from the declared input list"
    error = result.unwrap_err()
    assert error.code == "MALFORMED_OPERATION_INPUTS"
    assert "inputs[1]" in error.message
    assert error.locus == ".agents/skills/ingress/SKILL.md:3:inputs[1]"


@pytest.mark.parametrize("yaml_entry", ["Code", "null", "false", "7", "[]"])
def test_each_non_mapping_input_entry_is_refused(yaml_entry: str) -> None:
    content = (
        "```oewas.operation.v3\noperation_id: ingress:audit\n"
        f"inputs: [{yaml_entry}]\n```\n"
    ).encode("utf-8")

    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("ingress"), "ingress.md", content
    )

    assert result.is_err
    assert result.unwrap_err().code == "MALFORMED_OPERATION_INPUTS"
    assert "inputs[0]" in result.unwrap_err().message
    assert result.unwrap_err().locus == "ingress.md:1:inputs[0]"


@pytest.mark.parametrize(
    "kind,field",
    [
        ("operation", "operand_refs"),
        ("operation", "effects"),
        ("operation", "tool_refs"),
        ("operand", "dependencies"),
        ("operand", "emitted_observations"),
        ("composition", "child_operation_ids"),
    ],
)
@pytest.mark.parametrize("value", ["null", "false", "read_subject", "[7]", "[{name: value}]"])
def test_declared_string_lists_cannot_erase_or_coerce_contracts(kind, field, value):
    raw = (
        f"# Exact declaration\n\n```oewas.{kind}.v3\n"
        f"{field}: {value}\n```\n"
    ).encode("utf-8")
    result = LosslessMarkdownParserAdapter().parse_document(SkillId("ingress"), "ingress.md", raw)
    assert result.is_err, f"{field} must not become an empty or coerced contract"
    assert result.unwrap_err().code == "MALFORMED_OEWAS_DECLARATION"
    assert field in result.unwrap_err().message
    assert result.unwrap_err().locus == "ingress.md:3"


@pytest.mark.parametrize("value", ["null", "false", "Code", "[]"])
def test_present_non_mapping_output_is_not_replaced_by_the_default_port(value):
    raw = f"```oewas.operation.v3\noutput: {value}\n```\n".encode()
    result = LosslessMarkdownParserAdapter().parse_document(SkillId("ingress"), "ingress.md", raw)
    assert result.is_err, "A malformed output must not become the generic Data port"
    assert result.unwrap_err().code == "MALFORMED_OPERATION_OUTPUT"
    assert result.unwrap_err().locus == "ingress.md:1:output"


def test_omitted_and_empty_optional_lists_preserve_valid_defaults_and_source_bytes():
    raw = (
        "```oewas.operand.v3\noperand_id: body\nbody: Preserve the task.\n"
        "dependencies: []\nemitted_observations: []\n```\n\n"
        "```oewas.operation.v3\noperation_id: ingress:audit\n"
        "operand_refs: [body]\neffects: [read_subject]\ntool_refs: []\n```\n"
    ).encode()
    document = LosslessMarkdownParserAdapter().parse_document(SkillId("ingress"), "ingress.md", raw).unwrap()
    assert document.operations[0].effects == ("read_subject",)
    assert tuple(map(str, document.operations[0].operand_refs)) == ("body",)
    assert document.operations[0].tool_refs == ()
    assert document.operands[0].dependencies == ()
    assert document.raw_digest.hex_digest == hashlib.sha256(raw).hexdigest()
