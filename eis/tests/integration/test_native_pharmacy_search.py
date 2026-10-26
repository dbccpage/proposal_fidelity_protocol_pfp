"""Public pharmacy API against the explicitly configured current native host."""

import json
import os
import pytest

from omega_engine_epistemic_immune_system.domain.pharmacy_search import rule_content_sha256
from omega_engine_epistemic_immune_system.use_cases.pharmacy_search import PharmacySearchIndex

pytestmark = pytest.mark.skipif(
    not os.environ.get("OMEGA_SYMBOL_GAME_HOST"), reason="set OMEGA_SYMBOL_GAME_HOST to current build"
)

QUERY = dict(domain="mathematics", tags=["tao"], stage="answer", prompt_field="claims",
             scope="prompt://math/tao/035/answer/main")


def admitted(identifier="ab_selected"):
    record = dict(antibody_id=identifier, failure_class="scope", target_pattern="universal claim",
                  constraint_type="Restrain", operatorizability="repairable", action="repair",
                  severity="P1", negative_fixture="universal claim", positive_fixture="finite claim",
                  scope=dict(domain="mathematics", tags=["tao"], stages=["answer"],
                             prompt_fields=["claims"]), guidance_text="Only claim the finite result.",
                  authority_effect="None", pharmacy_status="admitted")
    digest = rule_content_sha256(record)
    record.update(rule_sha256=digest, admission=dict(decision_id="test-decision", issuer="test-operator",
                  scope=QUERY["scope"], rule_bytes_sha256="sha256:" + digest,
                  receipt_sha256="sha256:" + "a" * 64))
    return record


def test_native_scope_digest_and_signal_one():
    record = admitted()
    index = PharmacySearchIndex({"antibodies": {record["antibody_id"]: record}}, clock=lambda: 100)
    result = index.search(QUERY)
    assert [row["antibody_id"] for row in result["selected"]] == ["ab_selected"]
    assert result["selected"][0]["rule_digest"] == rule_content_sha256(record)
    assert index.search({**QUERY, "domain": "biology"})["selected"] == []
    hit = index.match(QUERY, "é universal claim")
    assert hit["hits"][0]["offset"] == 3
    assert hit["hits"][0]["offset_unit"] == "utf8_bytes"
    assert "verdict" not in hit


def test_native_file_transport_keeps_large_catalog_and_query_bound():
    record = admitted()
    catalog = {"antibodies": {record["antibody_id"]: record}, "historical_notes": "x" * 1_100_000}
    result = PharmacySearchIndex(catalog, clock=lambda: 100).search(QUERY)
    assert result["selected"][0]["antibody_id"] == "ab_selected"
    assert len(result["request_digest"]) == 64


def test_projection_drift_excludes_only_affected_rule(tmp_path):
    left, right = admitted("ab_left"), admitted("ab_right")
    path = tmp_path / "pharmacy_catalog.json"
    path.write_text(json.dumps({"antibodies": {"ab_left": left, "ab_right": right}}), encoding="utf-8")
    (tmp_path / "ab_left.json").write_text(json.dumps({**left, "times_seen": 50}), encoding="utf-8")
    result = PharmacySearchIndex(path, clock=lambda: 100).search(QUERY)
    assert [row["antibody_id"] for row in result["selected"]] == ["ab_right"]
    assert result["exclusions"] == [{"antibody_id": "ab_left", "reason": "PROJECTION_DRIFT"}]


def test_pending_publication_and_missing_managed_projection_are_visible(tmp_path):
    record = admitted()
    path = tmp_path / "pharmacy_catalog.json"
    path.write_text(json.dumps({"antibodies": {"ab_selected": record},
                               "managed_projections": {"ab_selected": "missing.json"}}), encoding="utf-8")
    index = PharmacySearchIndex(path, clock=lambda: 100)
    assert index.search(QUERY)["exclusions"] == [
        {"antibody_id": "ab_selected", "reason": "PROJECTION_UNAVAILABLE"}]
    path.with_suffix(".publication.pending.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="PHARMACY_PUBLICATION_INTERRUPTED"):
        index.search(QUERY)
