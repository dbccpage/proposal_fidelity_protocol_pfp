"""Integration tests for the Wave 4 head-to-head parity harness.

AuthorityEffect: None.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pfp_core.wave4_parity_harness import (
    compare_against_repo,
    compare_wave4_vectors,
    run_local_wave4_probe,
)


def _core_symbol_game_available() -> bool:
    """The Act III bout loads its council through the native core_symbol_game host.

    That crate is not in this repository, so CI cannot build it; these tests run
    wherever CORE_SYMBOL_GAME_HOST or a local build provides the binary.
    """
    from operating_system.adapters.rust_host.ffi import locate_host_binary

    import pfp_core  # noqa: F401  (puts ops/ on sys.path)

    return locate_host_binary(binary_name="core_symbol_game").is_ok


requires_core_symbol_game = pytest.mark.skipif(
    not _core_symbol_game_available(),
    reason="native core_symbol_game host binary not built (set CORE_SYMBOL_GAME_HOST)",
)


def _stage_target_repo_without_harness(source_root: Path, dest_root: Path) -> None:
    packages = (
        "pfp_core",
        "eis",
        "pciv",
        "pfp",
        "ops/adversary",
        "ops/operations",
        "ops/operating_system",
        "operads",
        "workflows/wf52_finite_qm_benchmark",
    )
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*wave4_parity_harness*")
    for rel in packages:
        src = source_root / rel
        if src.is_dir():
            shutil.copytree(src, dest_root / rel, ignore=ignore, dirs_exist_ok=True)
    for rel_file in (
        "ops/__init__.py",
        "pfp/domain/immune/self_panel.json",
        "code/rust/core_operad_canon/src/lib.rs",
    ):
        src_file = source_root / rel_file
        if src_file.is_file():
            dst_file = dest_root / rel_file
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)
    (dest_root / "ops" / "governance").mkdir(parents=True, exist_ok=True)


@requires_core_symbol_game
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


@requires_core_symbol_game
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

    empty_repo = tmp_path / "unready_target"
    empty_repo.mkdir()
    unready = compare_against_repo(empty_repo)
    assert unready["parity_status"] == "TARGET_NOT_READY"


@requires_core_symbol_game
def test_wave4_compare_against_repo_runs_when_target_lacks_harness_file(
    tmp_path: Path,
) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    target_repo = tmp_path / "target_checkout"
    target_repo.mkdir()
    _stage_target_repo_without_harness(repo_root, target_repo)
    assert not (target_repo / "pfp_core" / "wave4_parity_harness.py").exists()

    compared = compare_against_repo(target_repo)
    assert compared["parity_status"] == "MATCH"
    assert compared["mismatches"] == []
