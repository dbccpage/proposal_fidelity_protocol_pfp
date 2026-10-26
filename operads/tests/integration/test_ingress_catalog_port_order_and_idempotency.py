"""Real filesystem/parser/SQLite ingress controls. AuthorityEffect: None."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from omega_engine_operads.application.commands.compile_catalog import (
    CompileCatalogHandler,
    operation_content_digest,
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

SKILL_PATH = ".agents/skills/ingress/SKILL.md"
ESTATE = EstateRef("ingress-fixture")


def _write_skill(root: Path, inputs_yaml: str) -> bytes:
    content = (
        "---\nname: ingress\ndescription: Exact ingress fixture\n"
        "operad_source_colours: [Code, State]\noperad_target_colour: Audit\n"
        "operad_arity: 2\noperad_residual: unknown\n---\n\n# Φ ingress\n\n"
        "```oewas.operation.v3\noperation_id: ingress:audit\n"
        f"{inputs_yaml}"
        "output:\n  name: audit\n  colour_id: Audit\n"
        "schema_binding: Bound\nexecutor_binding: Bound\nvalidation: Validated\n"
        "admission: Admitted\n"
        f"schema_digest: {'a' * 64}\nexecutor_digest: {'b' * 64}\n```\n"
    ).encode("utf-8")
    skill = root / SKILL_PATH
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_bytes(content)
    catalog = compile_capability_catalog(root, tracked_paths=(SKILL_PATH,))
    projection = root / ".agents/skill_operads/capability_catalog.v1.json"
    projection.parent.mkdir(parents=True, exist_ok=True)
    projection.write_bytes(encode_capability_catalog(catalog))
    return content


def _ports(names: tuple[str, ...]) -> str:
    colours = {"code": "Code", "state": "State"}
    return "inputs:\n" + "".join(
        f"  - name: {name}\n    colour_id: {colours[name]}\n" for name in names
    )


def _handler(root: Path, uow: SqliteUnitOfWork) -> CompileCatalogHandler:
    return CompileCatalogHandler(
        estate_source=FsEstateSourceAdapter(root),
        parser=LosslessMarkdownParserAdapter(),
        legacy_reader=LegacyCatalogReaderAdapter(root),
        uow=uow,
        clock=SystemClock(),
        id_gen=UuidIdGenerator(),
    )


def _command(key: str, expected_version: int) -> CompileCatalogCommand:
    return CompileCatalogCommand(
        estate_ref=ESTATE,
        correlation_id=CorrelationId("corr-ingress"),
        causation_id=CausationId("cause-ingress"),
        idempotency_key=IdempotencyKey(key),
        expected_version=expected_version,
    )


def _row_counts(db_path: Path) -> tuple[int, ...]:
    with sqlite3.connect(db_path) as connection:
        return tuple(
            connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ("catalogs_v3", "events_v3", "outbox_v3", "idempotency_v3")
        )


def test_catalog_frontmatter_example_never_becomes_a_persisted_operation(tmp_path: Path) -> None:
    raw = _write_skill(tmp_path, _ports(("code", "state")))
    raw = raw.replace(
        b"description: Exact ingress fixture\n",
        b"description: |\n  ```oewas.operation.v3\n"
        b"  operation_id: metadata:phantom\n  inputs: []\n  ```\n",
    )
    (tmp_path / SKILL_PATH).write_bytes(raw)
    source_catalog = compile_capability_catalog(tmp_path, tracked_paths=(SKILL_PATH,))
    (tmp_path / ".agents/skill_operads/capability_catalog.v1.json").write_bytes(
        encode_capability_catalog(source_catalog)
    )
    with SqliteUnitOfWork(str(tmp_path / "metadata.sqlite3")) as uow:
        result = _handler(tmp_path, uow).handle(_command("metadata-body-boundary", 0))
        assert result.is_ok, result
        catalog = uow.get_catalog(result.unwrap().catalog_id).unwrap()
        assert {str(operation) for operation in catalog.operations} == {"ingress:audit"}
        document = next(iter(catalog.skills.values()))
        assert document.raw_digest.hex_digest == hashlib.sha256(raw).hexdigest()
        assert (tmp_path / SKILL_PATH).read_bytes() == raw
        assert all(op.lifecycle.admission is AdmissionFacet.UNADMITTED for op in catalog.operations.values())


@pytest.mark.parametrize(
    ("inputs_yaml", "field_locus"),
    [
        ("inputs: Code\n", ""),
        ("inputs:\n  - name: code\n    colour_id: Code\n  - State\n", ":inputs[1]"),
    ],
    ids=("non-list", "non-mapping-entry"),
)
def test_malformed_inputs_persist_nothing_and_valid_recovery_uses_real_ports(
    tmp_path: Path, inputs_yaml: str, field_locus: str
) -> None:
    content = _write_skill(tmp_path, inputs_yaml)
    db_path = tmp_path / "ingress.sqlite3"
    command = _command("refused-then-recovered", 0)

    with SqliteUnitOfWork(str(db_path)) as uow:
        handler = _handler(tmp_path, uow)
        refused = handler.handle(command)
        assert refused.is_err
        error = refused.unwrap_err()
        assert error.code == "DOCUMENT_PARSE_ERROR"
        assert error.status_code == 400
        assert "MALFORMED_OPERATION_INPUTS" in error.message
        fence_line = content[:content.index(b"```oewas.operation.v3")].count(b"\n") + 1
        assert error.locus == f"{SKILL_PATH}:{fence_line}{field_locus}"
        assert uow.get_latest_catalog(str(ESTATE)).unwrap() is None
        assert _row_counts(db_path) == (0, 0, 0, 0)

        _write_skill(tmp_path, _ports(("code", "state")))
        recovered = handler.handle(command)
        assert recovered.is_ok, recovered
        assert recovered.unwrap().epoch == 1
        persisted = uow.get_catalog(recovered.unwrap().catalog_id).unwrap()
        assert persisted is not None
        operation = next(iter(persisted.operations.values()))
        assert [port.name for port in operation.inputs] == ["code", "state"]
        assert operation.lifecycle.admission is AdmissionFacet.UNADMITTED
        assert operation.lifecycle.is_executable is False
        assert _row_counts(db_path) == (1, 2, 2, 1)


def test_port_order_changes_digest_and_changed_request_cannot_replay_prior_key(tmp_path: Path) -> None:
    _write_skill(tmp_path, _ports(("code", "state")))
    db_path = tmp_path / "ingress.sqlite3"
    first_command = _command("first-snapshot", 0)

    with SqliteUnitOfWork(str(db_path)) as uow:
        handler = _handler(tmp_path, uow)
        first = handler.handle(first_command)
        assert first.is_ok, first
        first_dto = first.unwrap()
        first_catalog = uow.get_catalog(first_dto.catalog_id).unwrap()
        assert first_catalog is not None
        first_operation = next(iter(first_catalog.operations.values()))
        assert [port.name for port in first_operation.inputs] == ["code", "state"]
        assert _row_counts(db_path) == (1, 2, 2, 1)

        _write_skill(tmp_path, _ports(("state", "code")))
        conflict = handler.handle(_command("first-snapshot", 1))
        assert conflict.is_err
        assert conflict.unwrap_err().code == "IDEMPOTENCY_CONFLICT"
        assert conflict.unwrap_err().status_code == 409
        assert _row_counts(db_path) == (1, 2, 2, 1)

        # An identical command retries its recorded snapshot; live source changes
        # do not turn it into a new request. A new key/version requests compilation.
        assert handler.handle(first_command).unwrap() == first_dto
        second_command = _command("second-snapshot", 1)
        second = handler.handle(second_command)
        assert second.is_ok, second
        second_dto = second.unwrap()
        assert second_dto.epoch == 2
        assert second_dto.catalog_id != first_dto.catalog_id
        assert second_dto.catalog_digest != first_dto.catalog_digest
        second_catalog = uow.get_catalog(second_dto.catalog_id).unwrap()
        assert second_catalog is not None
        second_operation = next(iter(second_catalog.operations.values()))
        assert [port.name for port in second_operation.inputs] == ["state", "code"]
        assert operation_content_digest(first_operation) != operation_content_digest(second_operation)
        assert second_operation.lifecycle.admission is AdmissionFacet.UNADMITTED
        assert second_operation.lifecycle.is_executable is False
        assert _row_counts(db_path) == (2, 4, 4, 2)

        assert handler.handle(second_command).unwrap() == second_dto
        assert uow.get_latest_catalog(str(ESTATE)).unwrap().epoch == 2
        assert _row_counts(db_path) == (2, 4, 4, 2)


@pytest.mark.parametrize(
    "declaration,code",
    [
        ("effects: read_subject\n", "MALFORMED_OEWAS_DECLARATION"),
        ("tool_refs: [7]\n", "MALFORMED_OEWAS_DECLARATION"),
        ("operand_refs: false\n", "MALFORMED_OEWAS_DECLARATION"),
        ("output: Code\n", "MALFORMED_OPERATION_OUTPUT"),
    ],
)
def test_malformed_contract_fields_persist_nothing_then_recover(tmp_path, declaration, code):
    raw = _write_skill(tmp_path, _ports(("code", "state")))
    if declaration.startswith("output:"):
        raw = raw.replace(b"output:\n  name: audit\n  colour_id: Audit\n", declaration.encode())
    else:
        raw = raw.replace(
            b"operation_id: ingress:audit\n",
            b"operation_id: ingress:audit\n" + declaration.encode(),
        )
    (tmp_path / SKILL_PATH).write_bytes(raw)
    source_catalog = compile_capability_catalog(tmp_path, tracked_paths=(SKILL_PATH,))
    (tmp_path / ".agents/skill_operads/capability_catalog.v1.json").write_bytes(
        encode_capability_catalog(source_catalog)
    )
    database = tmp_path / "contract-fields.sqlite3"
    with SqliteUnitOfWork(str(database)) as uow:
        handler = _handler(tmp_path, uow)
        command = _command("malformed-contract-then-recovery", 0)
        refused = handler.handle(command)
        assert refused.is_err
        assert refused.unwrap_err().code == "DOCUMENT_PARSE_ERROR"
        assert code in refused.unwrap_err().message
        assert _row_counts(database) == (0, 0, 0, 0)
        assert (tmp_path / SKILL_PATH).read_bytes() == raw
        _write_skill(tmp_path, _ports(("code", "state")))
        assert handler.handle(command).is_ok
        assert _row_counts(database) == (1, 2, 2, 1)
