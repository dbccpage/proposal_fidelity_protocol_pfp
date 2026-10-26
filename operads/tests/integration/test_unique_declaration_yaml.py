"""Real declaration/compiler/SQLite controls. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from omega_engine_operads.application.commands.compile_catalog import (
    CompileCatalogHandler,
)
from omega_engine_operads.application.dtos.command_dtos import CompileCatalogCommand
from omega_engine_operads.domain.capability_catalog_v1 import (
    encode_capability_catalog,
)
from omega_engine_operads.domain.value_objects.identifier import (
    CausationId,
    CorrelationId,
    EstateRef,
    IdempotencyKey,
    SkillId,
)
from omega_engine_operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
)
from omega_engine_operads.infrastructure.capability_catalog_compiler import (
    compile_capability_catalog,
)
from omega_engine_operads.infrastructure.fs.fs_estate_source_adapter import (
    FsEstateSourceAdapter,
)
from omega_engine_operads.infrastructure.fs.legacy_catalog_reader_adapter import (
    LegacyCatalogReaderAdapter,
)
from omega_engine_operads.infrastructure.parser.markdown_parser_adapter import (
    LosslessMarkdownParserAdapter,
)
from omega_engine_operads.infrastructure.providers.system_clock import SystemClock
from omega_engine_operads.infrastructure.providers.uuid_id_generator import (
    UuidIdGenerator,
)
from omega_engine_operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)

SKILL_PATH = ".agents/skills/unique-yaml/SKILL.md"
ESTATE = EstateRef("unique-yaml")


def _write(root: Path, declaration: str) -> bytes:
    content = (
        "---\nname: unique-yaml\ndescription: YAML custody fixture\n"
        "operad_source_colours: [Code, State]\noperad_target_colour: Audit\n"
        "operad_arity: 2\noperad_residual: unknown\n---\n\n# Φ fixture\n\n"
        + declaration
    ).encode("utf-8")
    skill = root / SKILL_PATH
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_bytes(content)
    catalog = compile_capability_catalog(root, tracked_paths=(SKILL_PATH,))
    projection = root / ".agents/skill_operads/capability_catalog.v1.json"
    projection.parent.mkdir(parents=True, exist_ok=True)
    projection.write_bytes(encode_capability_catalog(catalog))
    return content


def _declaration(body: str, kind: str = "operation") -> str:
    return f"```oewas.{kind}.v3\n{body}\n```\n"


def _command() -> CompileCatalogCommand:
    return CompileCatalogCommand(
        estate_ref=ESTATE, correlation_id=CorrelationId("corr"),
        causation_id=CausationId("cause"), idempotency_key=IdempotencyKey("retry"),
        expected_version=0,
    )


def _counts(db: Path) -> tuple[int, ...]:
    with sqlite3.connect(db) as connection:
        return tuple(connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                     for name in ("catalogs_v3", "events_v3", "outbox_v3", "idempotency_v3"))


def test_duplicate_inputs_refuse_before_compiler_persistence_and_recover(tmp_path: Path) -> None:
    content = _write(tmp_path, _declaration("operation_id: unique:audit\ninputs: Code\ninputs: []"))
    db = tmp_path / "catalog.sqlite3"
    with SqliteUnitOfWork(str(db)) as uow:
        handler = CompileCatalogHandler(
            FsEstateSourceAdapter(tmp_path), LosslessMarkdownParserAdapter(),
            LegacyCatalogReaderAdapter(tmp_path), uow, SystemClock(), UuidIdGenerator(),
        )
        refused = handler.handle(_command())
        assert refused.is_err, "Repeated inputs must not silently select a nullary operation"
        error = refused.unwrap_err()
        assert (error.code, error.status_code) == ("DOCUMENT_PARSE_ERROR", 400)
        assert "MALFORMED_OEWAS_DECLARATION" in error.message
        line = content[:content.index(b"```oewas.operation.v3")].count(b"\n") + 1
        assert error.locus == f"{SKILL_PATH}:{line}"
        assert _counts(db) == (0, 0, 0, 0)
        assert uow.get_latest_catalog(str(ESTATE)).unwrap() is None

        _write(tmp_path, _declaration(
            "operation_id: unique:audit\ninputs:\n  - {name: code, colour_id: Code}\n"
            "  - {name: state, colour_id: State}\noutput: {colour_id: Audit}"
        ))
        recovered = handler.handle(_command())
        assert recovered.is_ok, recovered
        assert recovered.unwrap().epoch == 1
        catalog = uow.get_catalog(recovered.unwrap().catalog_id).unwrap()
        operation = next(iter(catalog.operations.values()))
        assert [p.colour_id.value for p in operation.inputs] == ["Code", "State"]
        assert operation.lifecycle.admission is AdmissionFacet.UNADMITTED
        assert not operation.lifecycle.is_executable
        assert _counts(db) == (1, 2, 2, 1)
        assert handler.handle(_command()).unwrap() == recovered.unwrap()
        assert _counts(db) == (1, 2, 2, 1)



@pytest.mark.parametrize(("kind", "body"), [
    ("operation", "operation_id: first\noperation_id: second"),
    ("operation", 'operation_id: first\n"operation_\\u0069d": second'),
    ("operation", "operation_id: unique\ninputs: [{colour_id: Code, colour_id: State}]"),
    ("operation", 'operation_id: unique\ninputs: [{colour_id: Code, "colour_\\u0069d": State}]'),
    ("operation", "operation_id: unique\noutput: {colour_id: Code, colour_id: Audit}"),
    ("operation", "operation_id: unique\nmetadata: {k: 1, k: 1}"),
    ("operation", "{operation_id: first, operation_id: second}"),
    ("operation", "operation_id: unique\nport: &p {colour_id: Code, colour_id: State}\ninputs: [{<<: *p}]"),
    ("operation", 'operation_id: unique\nport: &p {colour_id: Code, "colour_\\u0069d": State}\ninputs: [{<<: *p}]'),
    ("operation", "operation_id: unique\ninputs: [{<<: {colour_id: Code}, <<: {name: code}}]"),
    ("operation", "operation_id: unique\nmetadata: {true: first, 1: second}"),
    ("operation", "? &key operation_id\n: first\n? *key\n: second"),
    ("operand", "operand_id: unique\nbody: first\nbody: second"),
    ("operand", 'operand_id: unique\nbody: first\n"b\\u006fdy": second'),
    ("composition", "composition_id: unique\nroot_operation_id: first\nroot_operation_id: second"),
    ("composition", 'composition_id: unique\nroot_operation_id: first\n"root_operation_\\u0069d": second'),
])
def test_repeated_source_keys_in_recognized_fences_are_typed_refusals(kind, body):
    result = LosslessMarkdownParserAdapter().parse_document(
        SkillId("unique"), "fixture/SKILL.md", _declaration(body, kind).encode()
    )
    assert result.is_err, (kind, body)
    error = result.unwrap_err()
    assert error.code == "MALFORMED_OEWAS_DECLARATION"
    assert error.locus == "fixture/SKILL.md:1"
    assert "duplicate source key" in error.message


@pytest.mark.parametrize(("body", "expected"), [
    ("operation_id: unique\ninputs: [{colour_id: Code}, {colour_id: State}]", ["Code", "State"]),
    ("operation_id: unique\ninputs: []", []),
    ("operation_id: unique", []),
    ('operation_id: unique\ninputs: [{"colour_\\u0069d": Code}]', ["Code"]),
    ("operation_id: unique\ndefaults: &p {colour_id: Code}\ninputs: [{<<: *p, name: code}]", ["Code"]),
    ("operation_id: unique\ndefaults: &p {colour_id: Code}\ninputs: [{<<: *p, colour_id: State}]", ["State"]),
    ("operation_id: unique\nfirst: &p {colour_id: Code}\nsecond: &q {colour_id: State}\ninputs: [{<<: [*p, *q]}]", ["Code"]),
    ("operation_id: unique\nfirst: &p {colour_id: Code}\nsecond: &q {name: code}\ninputs: [{<<: [*p, *q]}]", ["Code"]),
    ("operation_id: unique\nbase: &b {colour_id: Code}\ncombined: &p {<<: *b, colour_id: State}\ninputs: [*p, *p]", ["State", "State"]),
    ('operation_id: unique\ndefaults: &p {colour_id: Code}\ninputs: [{<<: *p, "<<": ordinary metadata}]', ["Code"]),
    ('operation_id: unique\n"<<": ordinary metadata\ninputs: [{colour_id: Code}]', ["Code"]),
    ("operation_id: unique\n= : ordinary metadata\ninputs: [{colour_id: Code}]", ["Code"]),
    ("operation_id: unique\n1: integer metadata\ninputs: [{colour_id: Code}]", ["Code"]),
])
def test_defined_yaml_merge_alias_and_key_compatibility(body, expected):
    raw = ("# Φ prose\n\n" + _declaration(body)).encode()
    result = LosslessMarkdownParserAdapter().parse_document(SkillId("unique"), "fixture/SKILL.md", raw)
    assert result.is_ok, result
    document = result.unwrap()
    operation = document.operations[0]
    assert [p.colour_id.value for p in operation.inputs] == expected
    assert operation.lifecycle.admission is AdmissionFacet.UNADMITTED
    assert not operation.lifecycle.is_executable
    assert document.raw_digest.hex_digest == hashlib.sha256(raw).hexdigest()
    for leaf in document.leaf_nodes:
        bounded = raw[leaf.span.start_byte:leaf.span.end_byte].decode()
        assert leaf.content in bounded


def test_foreign_fence_remains_byte_preserved_without_semantic_yaml_loading():
    raw = b"```yaml\noperation_id: first\noperation_id: second\n```\n"
    result = LosslessMarkdownParserAdapter().parse_document(SkillId("unique"), "fixture/SKILL.md", raw)
    assert result.is_ok
    document = result.unwrap()
    assert not document.operations
    assert document.leaf_nodes[0].content == "operation_id: first\noperation_id: second"


def test_loader_does_not_modify_global_safe_loader_and_has_no_cross_document_cache():
    import yaml

    assert yaml.safe_load("operation_id: first\noperation_id: second") == {"operation_id": "second"}
    parser = LosslessMarkdownParserAdapter()
    for _ in range(3):
        raw = _declaration("operation_id: unique\ninputs: [{colour_id: Code}]").encode()
        assert parser.parse_document(SkillId("unique"), "fixture/SKILL.md", raw).is_ok
