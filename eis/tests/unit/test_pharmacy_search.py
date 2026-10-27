"""Snapshot and identity boundary checks for admitted guidance lookup."""

import pytest

from eis.domain.pharmacy_search import (
    PharmacyQuery,
    rule_content_sha256,
)
from eis.use_cases.pharmacy_search import PharmacySearchIndex
from eis.domain.pharmacy_catalog import PharmacyCatalogRepository
from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
    release_publication_marker,
)


def test_rule_identity_ignores_observation_and_binds_guidance():
    record = dict(failure_class="scope", target_pattern="claims", constraint_type="Restrain",
                  operatorizability="repairable", action="repair", severity="P1",
                  negative_fixture="harm", positive_fixture="benign",
                  scope={"domain": "mathematics", "tags": ["tao"], "stages": ["answer"],
                         "prompt_fields": ["claims"]}, guidance_text="State finite scope.")
    observed = {**record, "times_seen": 100, "source_run_id": "new-run"}
    assert rule_content_sha256(record) == rule_content_sha256(observed)
    assert rule_content_sha256(record) != rule_content_sha256({**record, "guidance_text": "other"})


def test_index_reloads_changed_catalog_and_refuses_corruption(tmp_path):
    path = tmp_path / "pharmacy_catalog.json"
    path.write_text('{"antibodies":{}}', encoding="utf-8")
    index = PharmacySearchIndex(path)
    first = index.catalog_digest
    path.write_text('{"antibodies":{},"revision":2}', encoding="utf-8")
    assert index.catalog_digest != first
    path.write_text('{broken', encoding="utf-8")
    with pytest.raises(ValueError, match="PHARMACY_CATALOG_INVALID"):
        _ = index.catalog_digest


def test_catalog_snapshot_is_not_mutated_by_caller():
    catalog = {"antibodies": {}}
    index = PharmacySearchIndex(catalog)
    first = index.catalog_digest
    catalog["antibodies"]["injected"] = {}
    assert index.catalog_digest == first


def test_duplicate_catalog_keys_refused(tmp_path):
    path = tmp_path / "catalog.json"
    path.write_text('{"antibodies":{},"antibodies":{}}', encoding="utf-8")
    with pytest.raises(ValueError, match="PHARMACY_CATALOG_INVALID"):
        PharmacySearchIndex(path)


def test_query_defaults_do_not_make_scope_optional():
    query = PharmacyQuery(domain="mathematics", tags=("tao",), stage="answer",
                          prompt_field="claims", scope="prompt://math/tao/035/answer/main")
    assert query.limit == 3


def test_managed_unicode_projection_uses_existing_publisher_bytes(tmp_path):
    record = dict(antibody_id="ab_unicode", failure_class="scope", target_pattern="claims",
                  constraint_type="Restrain", operatorizability="repairable", action="repair",
                  severity="P1", negative_fixture="harm", positive_fixture="benign",
                  scope={"domain": "mathematics", "tags": ["tao"], "stages": ["answer"],
                         "prompt_fields": ["claims"]}, guidance_text="Keep λ and Ω finite.",
                  pharmacy_status="candidate", authority_effect="None")
    record["rule_sha256"] = record["evidence_sha256"] = rule_content_sha256(record)
    repository = PharmacyCatalogRepository(
        tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes,
    )
    release_publication_marker(
        repository.publish_candidates([record], observation_id="unicode-fixture").marker_path
    )
    index = PharmacySearchIndex(repository.catalog_file, repo_root=tmp_path)
    assert index._projection_exclusions() == {}
    projection = repository.get_antibody_path("ab_unicode", status="candidate")
    projection.write_bytes(projection.read_bytes() + b" ")
    assert index._projection_exclusions() == {"ab_unicode": "PROJECTION_DRIFT"}
