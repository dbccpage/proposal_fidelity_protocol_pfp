"""Persisted composition verification uses exact typed ports; no execution authority."""

import json
from dataclasses import replace
from datetime import datetime, timezone

import pytest

from omega_engine_operads.domain.entities.catalog_v3 import EstateCatalogV3
from omega_engine_operads.domain.entities.composition_v3 import CompositionV3
from omega_engine_operads.domain.entities.operation_v3 import (
    OperationV3,
    PortSpecV3,
)
from omega_engine_operads.domain.entities.skill_document_v3 import SkillDocumentV3
from omega_engine_operads.domain.value_objects import (
    AdmissionFacet,
    ColourId,
    ContentDigest,
    DeclarationFacet,
    DocumentId,
    EstateRef,
    ExecutorBindingFacet,
    OperationId,
    SchemaBindingFacet,
    SchemaRef,
    SkillId,
    SkillLifecycleV3,
    ValidationFacet,
)
from omega_engine_operads.infrastructure.bootstrap import create_oeop_container


def _catalog(epoch, changed=None):
    expected = PortSpecV3(
        "parent-input", ColourId("Code"), SchemaRef("schema:code:v1"),
        ContentDigest.sha256("a" * 64), "validator:code:v1", ContentDigest.sha256("b" * 64),
    )
    life = SkillLifecycleV3(
        DeclarationFacet.DECLARED, SchemaBindingFacet.BOUND, ExecutorBindingFacet.BOUND,
        ValidationFacet.VALIDATED, AdmissionFacet.UNADMITTED,
        ContentDigest.sha256("c" * 64), ContentDigest.sha256("d" * 64),
    )
    root = OperationV3(OperationId("root"), (expected,), expected, (), life, "HOLD")
    output = replace(expected, name="child-output")
    if changed:
        output = replace(output, **changed)
    child = OperationV3(OperationId("child"), (), output, (), life, "HOLD")
    composition = CompositionV3(
        "bounded-composition", "substitute", root.operation_id, (child.operation_id,),
        ((0, child.operation_id),), "Code -> Code",
    )
    skill_id = SkillId("bounded")
    digest = ContentDigest.sha256("c" * 64)
    doc = SkillDocumentV3(
        DocumentId("bounded-document"), skill_id, "fixtures/bounded.md", digest, digest,
        operations=(root, child), compositions=(composition,),
    )
    return EstateCatalogV3(
        f"catalog-{epoch}", EstateRef("bounded"), epoch,
        datetime(2026, 10, 13, tzinfo=timezone.utc), {skill_id: doc},
        {root.operation_id: root, child.operation_id: child}, {}, {}, digest,
    )


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("colour_id", ColourId("State"), "COLOUR_MISMATCH"),
        ("schema_ref", SchemaRef("schema:foreign:v1"), "SCHEMA_REFERENCE_MISMATCH"),
        ("schema_digest", ContentDigest.sha256("e" * 64), "SCHEMA_DIGEST_MISMATCH"),
        ("validator_ref", "validator:foreign:v1", "VALIDATOR_REFERENCE_MISMATCH"),
        ("validator_digest", ContentDigest.sha256("f" * 64), "VALIDATOR_DIGEST_MISMATCH"),
    ],
)
def test_persisted_catalog_refuses_foreign_boundary_and_restores_after_reopen(
    tmp_path, field, value, code,
):
    path = str(tmp_path / "composition.sqlite3")
    invalid = _catalog(1, {field: value})
    container = create_oeop_container(workspace_root=tmp_path, db_path=path)
    with container.uow:
        assert container.uow.save_catalog(invalid, ()).is_ok

    container = create_oeop_container(workspace_root=tmp_path, db_path=path)
    with container.uow:
        loaded = container.api.get_catalog(invalid.catalog_id).unwrap()
        assert next(iter(loaded.skills.values())).compositions == (
            next(iter(invalid.skills.values())).compositions[0],
        )
        refused = container.api.verify_catalog(invalid.catalog_id).unwrap()
        assert refused.is_valid is False
        assert any(code in error for error in refused.errors)
        assert container.uow.save_catalog(_catalog(2), ()).is_ok

    container = create_oeop_container(workspace_root=tmp_path, db_path=path)
    with container.uow:
        recovered = container.api.verify_catalog("catalog-2").unwrap()
        assert recovered.is_valid is True
        assert recovered.errors == ()
        assert container.api.verify_catalog("catalog-1").unwrap().is_valid is False


def test_legacy_catalog_without_composition_payload_is_not_fabricated(tmp_path):
    path = str(tmp_path / "legacy.sqlite3")
    container = create_oeop_container(workspace_root=tmp_path, db_path=path)
    with container.uow:
        assert container.uow.save_catalog(_catalog(1), ()).is_ok
        row = container.uow._conn.execute(
            "SELECT payload_json FROM catalogs_v3 WHERE catalog_id='catalog-1'",
        ).fetchone()
        legacy = json.loads(row["payload_json"])
        for document in legacy["skills"].values():
            document.pop("compositions")
        raw = json.dumps(legacy)
        with container.uow._conn:
            container.uow._conn.execute(
                "UPDATE catalogs_v3 SET payload_json=? WHERE catalog_id='catalog-1'", (raw,),
            )
    container = create_oeop_container(workspace_root=tmp_path, db_path=path)
    with container.uow:
        loaded = container.api.get_catalog("catalog-1").unwrap()
        assert next(iter(loaded.skills.values())).compositions == ()
        retained = container.uow._conn.execute(
            "SELECT payload_json FROM catalogs_v3 WHERE catalog_id='catalog-1'",
        ).fetchone()["payload_json"]
        assert retained == raw
