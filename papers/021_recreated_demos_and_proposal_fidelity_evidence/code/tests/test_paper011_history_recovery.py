"""Historical source custody and actual flawed-harness behavior, from paper cwd."""

from __future__ import annotations

import copy
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

PAPER = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("paper011_history_recovery", PAPER / "code/history_recovery.py")
assert SPEC is not None and SPEC.loader is not None
H = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = H
SPEC.loader.exec_module(H)


@pytest.fixture
def recovered_copy(tmp_path):
    target = tmp_path / "paper"
    source = PAPER / "docs/history_recovery"
    shutil.copytree(source / "recovered_sources", target / "docs/history_recovery/recovered_sources")
    shutil.copyfile(source / "recovery_manifest.json", target / "docs/history_recovery/recovery_manifest.json")
    return target, target / "docs/history_recovery/recovery_manifest.json"


def test_28_exact_historical_blobs_and_original_receipt_are_bound():
    recovered = H.verify_recovery()
    report, receipt = H.report_custody(recovered)
    assert len(recovered) == 28
    assert report["total_challenges"] == 25
    assert receipt["sha256"] == H.sha(recovered["results/genesis_master_report.json"])
    assert receipt["receipt_id"] == "REC_GENESIS_SUITE_1790618314"
    assert all(H.git_blob(raw) == H.PINS[name] for name, raw in recovered.items())


def test_full_g01_g25_original_verifier_falsifiers_need_no_process(monkeypatch):
    def no_process(*args, **kwargs):
        raise AssertionError("Replay must not invoke Git, Lean, Cargo, or a provider")

    monkeypatch.setattr(H.subprocess, "run", no_process)
    result = H.replay()
    assert result["challenge_count"] == 25
    assert result["incorrect_artifact_verifications_reproduced"] == 75
    assert result["historical_claim_label_census"] == {"CHECKED": 11, "OPEN": 13, "CHOSEN_ANALOGY": 1}
    assert result["historical_checked_lean"] == {
        "claimed_checked": 11, "reported_compiled": 0, "reported_timeout": 6,
        "reported_failed_without_timeout": 2, "reported_absent": 3, "snippets_recompiled_now": 0,
    }
    assert result["all_25_positive_obligations_satisfied"] is False
    assert result["historical_raw_response_bytes_retained"] is False
    assert result["historical_lean_snippet_bytes_retained"] is False
    assert result["retained_receipt_id_matches_findings_note"] is False
    assert {row["challenge_id"] for row in result["rows"]} == {f"G{i:02}" for i in range(1, 26)}
    for row in result["rows"]:
        assert row["positive_obligation_satisfied"] is False
        assert row["mathematical_certificate_replayed"] is False
        assert row["reconstructed_prompt_declares_identity_false_by_construction"] is True
        assert row["artifact_checker_flaw_reproduced"] is True
        assert row["formal_problem"]["text"]
        assert row["output_contract"]["text"]
        assert row["capability_gate"]["text"]
    g25 = next(row for row in result["rows"] if row["challenge_id"] == "G25")
    assert g25["external_ground_truth_accesses_during_row"] == []
    assert "confirmed 0 occurrences in source" in g25["report_derived_verifier_output"]["details"][0]


def test_original_gates_preserve_correct_controls_and_expose_misses():
    result = H.replay()
    gates = {row["control"]: row for row in result["danger_gate_controls"]}
    assert gates["NEUTRAL_LANGUAGE"]["actual_output"][0] is True
    assert gates["DECLARED_IDENTITY_ASSERTION"]["actual_output"][0] is False
    assert gates["CHECKED_WITHOUT_PROOF_OR_DATA"]["actual_output"][0] is False
    assert gates["NONSENSE_DATA_ACCEPTED"]["actual_output"][0] is True
    assert gates["DIRECT_IDENTITY_MISSED"]["actual_output"][0] is True
    assert gates["QUOTED_NEGATIVE_FALSE_POSITIVE"]["actual_output"][0] is False
    assert result["json_wrapper_control"]["non_rfc8259_wrapper_accepted_by_original_parser"] is True
    for row in result["lean_lexical_controls"]:
        assert row["process_invoked"] is False
        assert row["actual_output"]["compiles"] is not True


def test_raw_source_mutation_blocks_replay(recovered_copy):
    paper, manifest = recovered_copy
    first = sorted(H.PINS)[0]
    raw_path = paper / (H.RECOVERED_PREFIX + first)
    raw_path.write_bytes(raw_path.read_bytes() + b"\n")
    with pytest.raises(H.RecoveryError, match="RECOVERED_BYTES_MISMATCH"):
        H.replay(manifest, paper)


def test_rehashed_manifest_cannot_authorize_substituted_blob(recovered_copy):
    paper, manifest = recovered_copy
    data = json.loads(manifest.read_bytes())
    entry = data["entries"][0]
    path = paper / entry["recovered_relative_path"]
    altered = path.read_bytes() + b"changed\n"
    path.write_bytes(altered)
    entry.update({"sha256": H.sha(altered), "git_blob": H.git_blob(altered), "byte_count": len(altered)})
    manifest.write_bytes(H.canonical(data))
    with pytest.raises(H.RecoveryError, match="RECOVERY_BLOB_OR_PATH_IDENTITY_MISMATCH"):
        H.replay(manifest, paper)


def test_duplicate_and_omitted_sources_fail_census(recovered_copy):
    paper, manifest = recovered_copy
    data = json.loads(manifest.read_bytes())
    data["entries"][1] = copy.deepcopy(data["entries"][0])
    manifest.write_bytes(H.canonical(data))
    with pytest.raises(H.RecoveryError, match="RECOVERY_BLOB_OR_PATH_IDENTITY_MISMATCH"):
        H.verify_recovery(manifest, paper)


def test_source_path_or_commit_substitution_fails(recovered_copy):
    paper, manifest = recovered_copy
    data = json.loads(manifest.read_bytes())
    data["source_commit"] = "0" * 40
    manifest.write_bytes(H.canonical(data))
    with pytest.raises(H.RecoveryError, match="RECOVERY_IDENTITY_MISMATCH"):
        H.verify_recovery(manifest, paper)


def test_corrupt_report_cannot_replay_original_receipt():
    recovered = H.verify_recovery()
    recovered["results/genesis_master_report.json"] += b"\n"
    with pytest.raises(H.RecoveryError, match="RECEIPT_REPORT_DIGEST_MISMATCH"):
        H.report_custody(recovered)


def test_missing_or_duplicate_g_id_not_accepted_even_if_report_self_rehashed():
    recovered = H.verify_recovery()
    report = json.loads(recovered["results/genesis_master_report.json"])
    report["results"][1]["challenge_id"] = "G01"
    changed = H.canonical(report)
    receipt = json.loads(recovered["results/genesis_receipt.json"])
    receipt["sha256"] = H.sha(changed)
    recovered.update({"results/genesis_master_report.json": changed,
                      "results/genesis_receipt.json": H.canonical(receipt)})
    with pytest.raises(H.RecoveryError, match="HISTORICAL_CHALLENGE_CENSUS_MISMATCH"):
        H.report_custody(recovered)


@pytest.mark.parametrize("path", ["../outside", "/absolute", "C:/absolute", "docs\\escape"])
def test_recovery_path_cannot_escape_paper(path, tmp_path):
    with pytest.raises(H.RecoveryError, match="UNSAFE_RECOVERED_PATH"):
        H.paper_path(tmp_path, path)


def test_corrupt_harness_cannot_be_executed():
    recovered = H.verify_recovery()
    with pytest.raises(H.RecoveryError, match="HARNESS_SOURCE_BLOB_MISMATCH"):
        H.preserved_harness(recovered["run_genesis_suite.py"] + b"\n")
