"""Integration tests for the Wave 4 head-to-head parity harness.

AuthorityEffect: None.
"""

from __future__ import annotations

from pathlib import Path

from pfp_core.wave4_parity_harness import (
    compare_against_repo,
    compare_wave4_vectors,
    run_local_wave4_probe,
)


def test_wave4_local_probe_emits_expected_four_scenario_metrics(tmp_path: Path) -> None:
    report = run_local_wave4_probe(work_dir=tmp_path)
    assert report["authority_effect"] == "None"

    s1 = report["scenario_1_act3_and_wild_hold"]
    assert s1["wild_disposition"] == "HOLD_OR_REPAIR"
    assert s1["bout_refusal_code"] == "ACT3_IMMUNE_SIEVE_HOLD"
    assert s1["act4_critique_calls_when_held"] == 0
    assert s1["shared_screen_invocations"] >= 2
    assert s1["single_catalog_shared"] is True

    s2 = report["scenario_2_self_panel_gate"]
    assert s2["autoimmune_admission_refused"] is True
    assert s2["clean_panel_false_positives"] == 0
    assert s2["stranger_disposition"] == "PASS"

    s3 = report["scenario_3_relapse_vs_cure"]
    assert s3["relapsed_status"] == "RELAPSED_BURIED"
    assert s3["relapsed_tainted"] is True
    assert s3["relapsed_headstones"] == 1
    assert s3["cured_status"] == "CURED_ADOPTED"
    assert s3["cured_tainted"] is False

    s4 = report["scenario_4_12hop_attenuation"]
    assert s4["weights_1_to_10"]["1"] == "1/2"
    assert s4["weights_1_to_10"]["10"] == "1/1024"
    assert s4["active_at_hop_10"] is True
    assert s4["active_at_hop_11"] is False
    assert s4["active_at_hop_12"] is False


def test_wave4_vector_comparison_detects_match_mismatch_and_unready_target(
    tmp_path: Path,
) -> None:
    baseline = run_local_wave4_probe(work_dir=tmp_path / "base")
    matched = compare_wave4_vectors(baseline, baseline)
    assert matched["parity_status"] == "MATCH"
    assert matched["mismatches"] == []

    drifted = {
        **baseline,
        "scenario_2_self_panel_gate": {
            **baseline["scenario_2_self_panel_gate"],
            "clean_panel_false_positives": 2,
        },
    }
    mismatched = compare_wave4_vectors(baseline, drifted)
    assert mismatched["parity_status"] == "MISMATCH"
    assert any("clean_panel_false_positives" in item for item in mismatched["mismatches"])

    empty_repo = tmp_path / "unready_anomalon"
    empty_repo.mkdir()
    unready = compare_against_repo(empty_repo)
    assert unready["parity_status"] == "TARGET_NOT_READY"
