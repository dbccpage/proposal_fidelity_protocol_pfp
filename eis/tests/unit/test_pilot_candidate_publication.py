"""Harvesting publishes candidates, never an admission or duplicate sighting."""

import json
import hashlib
import subprocess
from pathlib import Path
import pytest

from omega_engine_epistemic_immune_system.domain.pharmacy_catalog import PharmacyCatalogRepository
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
    release_publication_marker,
)
from omega_engine_epistemic_immune_system.domain.pharmacy_models import Antibody


def candidate():
    return Antibody.farm(
        antibody_id="ab_example", failure_class="scope", target_pattern="bad",
        constraint_type="ProjectOut", operatorizability="repairable", action="repair",
        severity="P1", description="finite check", negative_fixture="bad", positive_fixture="good",
    ).to_dict()


def test_candidate_publication_deduplicates_observation_and_keeps_projection(tmp_path):
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    record = candidate()
    release_publication_marker(repo.publish_candidates([record], observation_id="observed:fixture:1").marker_path)
    before = repo.catalog_file.read_bytes()
    release_publication_marker(repo.publish_candidates([record], observation_id="observed:fixture:1").marker_path)
    assert repo.catalog_file.read_bytes() == before
    release_publication_marker(repo.publish_candidates([record], observation_id="observed:fixture:2").marker_path)
    entry = repo.load_catalog()["antibodies"][record["antibody_id"]]
    assert entry["times_seen"] == 2
    assert entry["pharmacy_status"] == "candidate"
    assert json.loads(repo.get_antibody_path(record["antibody_id"]).read_bytes()) == entry


@pytest.mark.parametrize("status", ["admitted", "rejected", "retired"])
def test_harvest_preserves_judged_record_and_historical_projection(tmp_path, status):
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    record = candidate()
    judged = dict(record, pharmacy_status=status)
    repo.update_catalog([Antibody(**judged)], run_id="prior", task_id="prior")
    before = repo.catalog_file.read_bytes()
    release_publication_marker(repo.publish_candidates([record], observation_id="observed:fixture:1").marker_path)
    assert repo.catalog_file.read_bytes() == before
    assert repo.load_catalog()["antibodies"][record["antibody_id"]] == judged


def test_cannot_publish_non_candidate(tmp_path):
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    with pytest.raises(ValueError, match="PHARMACY_CANDIDATE_REQUIRED"):
        release_publication_marker(repo.publish_candidates([dict(candidate(), pharmacy_status="admitted")], observation_id="a").marker_path)


def test_projection_drift_is_visible_and_repair_uses_catalog(tmp_path):
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    release_publication_marker(repo.publish_candidates([candidate()], observation_id="a").marker_path)
    projection = repo.get_antibody_path("ab_example")
    projection.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="PHARMACY_PROJECTION_DRIFT"):
        repo.load_catalog()
    release_publication_marker(repo.repair_projections())
    assert json.loads(projection.read_bytes()) == repo.load_catalog()["antibodies"]["ab_example"]


def test_interruption_does_not_hide_as_success_or_empty_catalog(tmp_path):
    class Interrupted(PharmacyCatalogRepository):
        def _atomic_write(self, path, payload):
            if path == self.catalog_file:
                raise OSError("simulated interrupted publication")
            super()._atomic_write(path, payload)

    repo = Interrupted(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    with pytest.raises(OSError, match="interrupted"):
        release_publication_marker(repo.publish_candidates([candidate()], observation_id="a").marker_path)
    with pytest.raises(ValueError, match="PHARMACY_PUBLICATION_INTERRUPTED"):
        repo.load_catalog()
    # A missing catalog cannot be reconstructed from uncommitted projections.
    with pytest.raises(ValueError, match="PHARMACY_AUTHORITATIVE_CATALOG_MISSING"):
        release_publication_marker(repo.repair_projections())


def test_corrupt_catalog_cannot_be_repaired_into_empty_success(tmp_path):
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    repo.catalog_file.parent.mkdir(parents=True, exist_ok=True)
    repo.catalog_file.write_text("{", encoding="utf-8")
    with pytest.raises(ValueError, match="Corrupt or unreadable"):
        release_publication_marker(repo.publish_candidates([candidate()], observation_id="a").marker_path)
    with pytest.raises(ValueError, match="Corrupt or unreadable"):
        release_publication_marker(repo.repair_projections())


def test_selected_definitions_have_actual_controls_and_exact_historical_sources():
    from scripts.harvest_pilot_immunology import DEFAULT_DEFINITIONS, load_candidates
    root = Path(__file__).resolve().parents[3]
    packet, records = load_candidates(root / DEFAULT_DEFINITIONS)
    assert len(records) == 2
    assert packet["admission_scope"] == "prompt://mathematics/hadamard/pilot035/answer/tao-cross-ratios-v1"
    for record in records:
        historical = record["historical_source"]
        historical_bytes = subprocess.check_output(
            ["git", "show", f"{historical['repository_revision']}:{historical['path']}"],
            cwd=root,
        )
        assert hashlib.sha256(historical_bytes).hexdigest() == historical["sha256"]
        assert record["scope"]["prompt_fields"] == ["claims"]
        assert record["pharmacy_status"] == "candidate"
        assert record["admission"] is None


def test_script_repetition_and_reformat_are_not_new_observations(tmp_path):
    from scripts.harvest_pilot_immunology import DEFAULT_DEFINITIONS, harvest_and_publish
    root = Path(__file__).resolve().parents[3]
    definitions = tmp_path / "definitions.json"
    packet = json.loads((root / DEFAULT_DEFINITIONS).read_bytes())
    definitions.write_text(json.dumps(packet), encoding="utf-8")
    request = tmp_path / "request.json"
    first = harvest_and_publish(tmp_path, definitions_file=definitions, request_path=request)
    assert len(first["changed_ids"]) == 2
    definitions.write_text(json.dumps(packet, indent=3), encoding="utf-8")
    second = harvest_and_publish(tmp_path, definitions_file=definitions, request_path=request)
    assert second["changed_ids"] == []
    catalog = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes).load_catalog()
    for entry in catalog["antibodies"].values():
        assert entry["times_seen"] == 1
        assert entry["rule_sha256"]
        assert entry["scope"]["domain"] == "mathematics"
        assert entry["guidance_text"]
        assert entry["pharmacy_status"] == "candidate"
    for item in json.loads(request.read_bytes())["requests"]:
        assert item["human_decision"] is None
        assert item["request"]["status"] == "CANDIDATE"
        assert "sha256:" + hashlib.sha256(item["rule_bytes_utf8"].encode()).hexdigest() == item["request"]["candidate_digest"]


def test_bad_control_or_changed_rule_is_refused_before_publication(tmp_path):
    from scripts.harvest_pilot_immunology import DEFAULT_DEFINITIONS, harvest_and_publish
    from omega_engine_epistemic_immune_system.domain.pharmacy_search import rule_content_sha256
    root = Path(__file__).resolve().parents[3]
    definitions = tmp_path / "definitions.json"
    packet = json.loads((root / DEFAULT_DEFINITIONS).read_bytes())
    packet["candidates"][0]["guidance_text"] = "changed without new digest"
    definitions.write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(ValueError, match="PILOT_RULE_DIGEST_MISMATCH"):
        harvest_and_publish(tmp_path, definitions_file=definitions)
    record = packet["candidates"][0]
    record["rule_sha256"] = rule_content_sha256(record)
    record["antibody_id"] = "ab_changed_" + record["rule_sha256"][:12]
    record["controls"]["must_not_match"].append(record["negative_fixture"])
    definitions.write_text(json.dumps(packet), encoding="utf-8")
    with pytest.raises(ValueError, match="PILOT_FIXTURE_POLARITY_MISMATCH"):
        harvest_and_publish(tmp_path, definitions_file=definitions)
    assert not (tmp_path / ".agents/antibodies/pharmacy_catalog.json").exists()


def test_refused_admission_cannot_change_catalog(tmp_path):
    from scripts.harvest_pilot_immunology import DEFAULT_DEFINITIONS, harvest_and_publish
    from omega_engine_epistemic_immune_system.domain.external_admission import HumanAntiSkillAdmissionDecisionV1

    class RefusingGate:
        def apply_admission(self, decision, target_rule_bytes):
            return {"status": "REFUSED", "reason": "MISSING_ISSUER"}

    root = Path(__file__).resolve().parents[3]
    harvest_and_publish(tmp_path, definitions_file=root / DEFAULT_DEFINITIONS)
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    record = next(iter(repo.load_catalog()["antibodies"].values()))
    before = repo.catalog_file.read_bytes()
    decision = HumanAntiSkillAdmissionDecisionV1("decision", "", "sha256:" + record["rule_sha256"], "pilot035", "sha256:" + "0" * 64)
    with pytest.raises(ValueError, match="PHARMACY_ADMISSION_REFUSED:MISSING_ISSUER"):
        repo.publish_admission(record["antibody_id"], decision, applier=RefusingGate())
    assert repo.catalog_file.read_bytes() == before


def test_interrupted_existing_catalog_recovers_old_committed_record(tmp_path):
    repo = PharmacyCatalogRepository(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    release_publication_marker(repo.publish_candidates([candidate()], observation_id="first").marker_path)

    class Interrupted(PharmacyCatalogRepository):
        def _atomic_write(self, path, payload):
            if path == self.catalog_file:
                raise OSError("interrupted")
            super()._atomic_write(path, payload)

    interrupted = Interrupted(tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    with pytest.raises(OSError, match="interrupted"):
        interrupted.publish_candidates([candidate()], observation_id="second")
    with pytest.raises(ValueError, match="PHARMACY_PUBLICATION_INTERRUPTED"):
        repo.load_catalog()
    release_publication_marker(repo.repair_projections())
    assert repo.load_catalog()["antibodies"]["ab_example"]["times_seen"] == 1
