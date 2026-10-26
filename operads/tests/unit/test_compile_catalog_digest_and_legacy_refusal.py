"""Catalog digest framing and content, and the legacy-read refusal.

Two defects in `CompileCatalogHandler`:

* The catalog digest was SHA-256 over the bare concatenation of sorted
  operation ids. Ids ``["ab", "c"]`` and ``["a", "bc"]`` concatenate to the same
  bytes, and nothing about what an operation or skill *declares* entered the
  hash, so two catalogs with the same ids and different content shared a digest.
* With no tracked skill paths the legacy reader was tried, and a failed read
  fell through with nothing read: an empty epoch was persisted as if the
  estate had no skills.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from typing import Tuple

import pytest

from omega_engine_operations.domain.rop.result import Err, Ok, Result
from omega_engine_operads.application.commands.compile_catalog import (
    CompileCatalogHandler,
    catalog_content_digest,
)
from omega_engine_operads.application.dtos.command_dtos import (
    CompileCatalogCommand,
)
from omega_engine_operads.application.ports.estate_source_port import (
    EstateSourcePort,
)
from omega_engine_operads.application.ports.legacy_catalog_reader_port import (
    LegacyCatalogReaderPort,
)
from omega_engine_operads.application.ports.skill_document_parser_port import (
    SkillDocumentParserPort,
)
from omega_engine_operads.domain.entities.operation_v3 import (
    OperationV3,
    PortSpecV3,
)
from omega_engine_operads.domain.entities.skill_document_v3 import (
    SkillDocumentV3,
)
from omega_engine_operads.domain.errors.domain_errors import (
    DomainInvariantError,
    OeopDomainError,
)
from omega_engine_operads.domain.value_objects.content_digest import (
    ContentDigest,
)
from omega_engine_operads.domain.value_objects.identifier import (
    CausationId,
    ColourId,
    CorrelationId,
    DocumentId,
    EstateRef,
    OperationId,
    SchemaRef,
    SkillId,
)
from omega_engine_operads.domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)
from omega_engine_operads.infrastructure.providers.system_clock import (
    SystemClock,
)
from omega_engine_operads.infrastructure.providers.uuid_id_generator import (
    UuidIdGenerator,
)
from omega_engine_operads.infrastructure.storage.sqlite_unit_of_work import (
    SqliteUnitOfWork,
)

ESTATE = EstateRef("fixture-estate")


def _digest(text: str) -> ContentDigest:
    return ContentDigest.sha256(hashlib.sha256(text.encode("utf-8")).hexdigest())


def _document(skill: str, op_ids: Tuple[str, ...], residual: str = "unknown", body: str = "") -> SkillDocumentV3:
    raw = _digest(f"{skill}|{body}")
    port = PortSpecV3(
        name="in",
        colour_id=ColourId("State"),
        schema_ref=SchemaRef("schema:fixture:v1"),
        schema_digest=raw,
        validator_ref="validator:fixture",
        validator_digest=raw,
    )
    lifecycle = SkillLifecycleV3(
        declaration=DeclarationFacet.DECLARED,
        schema_binding=SchemaBindingFacet.ANY_SCHEMA,
        executor_binding=ExecutorBindingFacet.UNBOUND,
        validation=ValidationFacet.UNCHECKED,
        admission=AdmissionFacet.ADMITTED,
    )
    operations = tuple(
        OperationV3(
            operation_id=OperationId(op_id),
            inputs=(port,),
            output=port,
            operand_refs=(),
            lifecycle=lifecycle,
            residual_status=residual,
        )
        for op_id in op_ids
    )
    return SkillDocumentV3(
        document_id=DocumentId(f"doc_{skill}"),
        skill_id=SkillId(skill),
        source_relative_path=f".agents/skills/{skill}/SKILL.md",
        raw_digest=raw,
        semantic_digest=raw,
        operations=operations,
    )


class _NoTrackedPaths(EstateSourcePort):
    def list_skill_paths(self, estate_ref: EstateRef) -> Result[Tuple[str, ...], OeopDomainError]:
        return Ok(())

    def read_skill_bytes(self, relative_path: str) -> Result[bytes, OeopDomainError]:
        raise AssertionError("no path is listed, so none may be read")


class _UnusedParser(SkillDocumentParserPort):
    def parse_document(self, skill_id, relative_path, content):  # type: ignore[override]
        raise AssertionError("the legacy path does not parse documents")


class _Legacy(LegacyCatalogReaderPort):
    def __init__(self, result: Result[Tuple[SkillDocumentV3, ...], OeopDomainError]) -> None:
        self._result = result

    def read_legacy_estate(self, estate_ref: EstateRef) -> Result[Tuple[SkillDocumentV3, ...], OeopDomainError]:
        return self._result


def _handler(legacy: _Legacy, uow: SqliteUnitOfWork) -> CompileCatalogHandler:
    return CompileCatalogHandler(
        estate_source=_NoTrackedPaths(),
        parser=_UnusedParser(),
        legacy_reader=legacy,
        uow=uow,
        clock=SystemClock(),
        id_gen=UuidIdGenerator(),
    )


def _command(**overrides) -> CompileCatalogCommand:
    return CompileCatalogCommand(
        estate_ref=ESTATE,
        correlation_id=CorrelationId("corr"),
        causation_id=CausationId("cause"),
        **overrides,
    )


def _compile(documents: Tuple[SkillDocumentV3, ...]) -> str:
    uow = SqliteUnitOfWork(":memory:")
    try:
        res = _handler(_Legacy(Ok(documents)), uow).handle(_command())
        assert res.is_ok, res
        return res.unwrap().catalog_digest
    finally:
        uow.close()


def _persisted(uow: SqliteUnitOfWork):
    latest = uow.get_latest_catalog(str(ESTATE))
    assert latest.is_ok
    return latest.unwrap()


# -- digest framing and content ------------------------------------------


def test_ids_that_concatenate_to_the_same_bytes_get_different_digests() -> None:
    """Counterexample: ["ab", "c"] vs ["a", "bc"] collided under bare concatenation."""
    left = _compile((_document("s", ("ab", "c")),))
    right = _compile((_document("s", ("a", "bc")),))
    assert left != right


def test_same_ids_with_different_operation_content_get_different_digests() -> None:
    """The old digest read only ids, so a changed declaration kept its digest."""
    left = _compile((_document("s", ("s:invoke",), residual="unknown"),))
    right = _compile((_document("s", ("s:invoke",), residual="closed"),))
    assert left != right


def test_same_ids_with_different_document_bytes_get_different_digests() -> None:
    left = _compile((_document("s", ("s:invoke",), body="v1"),))
    right = _compile((_document("s", ("s:invoke",), body="v2"),))
    assert left != right


def test_the_digest_is_a_function_of_content_not_of_run_identity() -> None:
    """Fresh catalog ids, clocks and databases must not move the digest."""
    documents = (_document("b", ("b:invoke",)), _document("a", ("a:invoke",)))
    assert _compile(documents) == _compile(tuple(reversed(documents)))


def test_mixed_compiled_and_markdown_documents_enter_one_public_catalog():
    compiled = _document("canonical", ("canonical.audit",))
    markdown = _document("legacy", ("legacy:audit",))

    class MixedSource(_NoTrackedPaths):
        def list_skill_paths(self, estate_ref):
            return Ok((".agents/skills/canonical/SKILL.md", ".agents/skills/legacy/SKILL.md"))

        def read_compiled_skill_document(self, path):
            return Ok(compiled if "/canonical/" in path else None)

        def read_skill_bytes(self, path):
            assert "/legacy/" in path
            return Ok(b"legacy source")

    class MarkdownParser(_UnusedParser):
        def parse_document(self, skill_id, relative_path, content):
            assert str(skill_id) == "legacy" and content == b"legacy source"
            return Ok(markdown)

    uow = SqliteUnitOfWork(":memory:")
    try:
        result = CompileCatalogHandler(MixedSource(), MarkdownParser(), _Legacy(Err(
            DomainInvariantError(code="UNUSED", message="No legacy fallback")
        )), uow, SystemClock(), UuidIdGenerator()).handle(_command())
        assert result.is_ok, result
        assert result.unwrap().total_operations == 2
        assert set(map(str, _persisted(uow).operations)) == {"canonical.audit", "legacy:audit"}
    finally:
        uow.close()


def test_catalog_content_digest_is_order_independent_and_typed() -> None:
    a = _document("a", ("a:1", "a:2"))
    skills = {a.skill_id: a}
    ops = {op.operation_id: op for op in a.operations}
    owners = {op.operation_id: a.skill_id for op in a.operations}
    reversed_ops = dict(reversed(list(ops.items())))
    first = catalog_content_digest(skills, ops, owners)
    assert first == catalog_content_digest(skills, reversed_ops, owners)
    assert type(first) is ContentDigest
    assert first.algorithm == "sha256"


def test_one_operation_declared_by_two_documents_is_refused() -> None:
    """A keyed map silently kept only the second declaration."""
    uow = SqliteUnitOfWork(":memory:")
    try:
        documents = (_document("a", ("shared",)), _document("b", ("shared",)))
        res = _handler(_Legacy(Ok(documents)), uow).handle(_command())
        assert res.is_err
        assert res.unwrap_err().code == "DUPLICATE_OPERATION_ID"
        assert _persisted(uow) is None
    finally:
        uow.close()


# -- legacy read failure and the empty estate ------------------------------


def test_a_failed_legacy_read_is_refused_and_persists_nothing() -> None:
    """Counterexample: the old handler returned Ok with epoch 1 and 0 skills."""
    uow = SqliteUnitOfWork(":memory:")
    try:
        failing = _Legacy(Err(DomainInvariantError(code="LEGACY_IO", message="disk unreadable")))
        res = _handler(failing, uow).handle(_command())
        assert res.is_err
        error = res.unwrap_err()
        assert error.code == "LEGACY_READ_FAILED"
        assert "disk unreadable" in error.message
        assert _persisted(uow) is None
    finally:
        uow.close()


def test_an_empty_estate_is_refused_unless_the_command_allows_it() -> None:
    uow = SqliteUnitOfWork(":memory:")
    try:
        handler = _handler(_Legacy(Ok(())), uow)

        refused = handler.handle(_command())
        assert refused.is_err
        assert refused.unwrap_err().code == "EMPTY_ESTATE"
        assert _persisted(uow) is None

        allowed = handler.handle(_command(allow_empty_estate=True))
        assert allowed.is_ok
        dto = allowed.unwrap()
        assert (dto.epoch, dto.total_skills, dto.total_operations) == (1, 0, 0)
        assert _persisted(uow) is not None
    finally:
        uow.close()


@pytest.mark.parametrize("truthy", [1, "yes", None])
def test_allow_empty_estate_must_be_an_exact_bool(truthy) -> None:
    with pytest.raises(TypeError):
        _command(allow_empty_estate=truthy)
