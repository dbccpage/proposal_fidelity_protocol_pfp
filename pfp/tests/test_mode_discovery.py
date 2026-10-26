"""Tests for dynamic discovery of Symbol Game mode contracts via modes_manifest.yaml.
AuthorityEffect: None.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from omega_engine_pfp.domain.modes import ModeContract, ModesManifest
from omega_engine_pfp.entrypoints.cli.symbol_game import main
from omega_engine_pfp.infrastructure.adapters.mode_discovery import (
    discover_modes_manifest,
    find_modes_dir,
    load_all_mode_contracts,
    validate_mode_catalog_closure,
)
from omega_engine_pfp.use_cases.modes import (
    GetModeUseCase,
    ListModesUseCase,
    ValidateModesUseCase,
)

def test_dynamic_discovery_finds_modes_manifest():
    """Verify that find_modes_dir dynamically discovers the canonical top-level modes/ folder."""
    modes_dir = find_modes_dir()
    assert modes_dir.is_dir()
    assert (modes_dir / "modes_manifest.yaml").is_file()
    assert modes_dir.name == "modes"
    assert modes_dir == Path(__file__).resolve().parents[1] / "infrastructure" / "yaml" / "modes"


def test_explicit_root_does_not_fall_back_to_the_installed_catalog(tmp_path, monkeypatch):
    monkeypatch.delenv("SYMBOL_GAME_MODES_DIR", raising=False)
    with pytest.raises(FileNotFoundError):
        find_modes_dir(tmp_path)


def test_explicit_root_discovers_the_packaged_layout(tmp_path, monkeypatch):
    monkeypatch.delenv("SYMBOL_GAME_MODES_DIR", raising=False)
    directory = tmp_path / "omega_engine_pfp" / "infrastructure" / "yaml" / "modes"
    directory.mkdir(parents=True)
    (directory / "modes_manifest.yaml").write_text("modes: []\n", encoding="utf-8")
    assert find_modes_dir(tmp_path) == directory


def test_modes_manifest_contents():
    """Verify modes_manifest.yaml parsed into ModesManifest domain model."""
    manifest = discover_modes_manifest()
    assert isinstance(manifest, ModesManifest)
    assert manifest.manifest_version == "2.0.0"
    assert len(manifest.modes) == 20
    assert len(manifest.clusters) == 5

    # Check expected clusters
    expected_clusters = {
        "cluster_1_carrier_representation",
        "cluster_2_internal_steering",
        "cluster_3_group_cochain_structure",
        "cluster_4_dialectical_adversarial",
        "cluster_5_foundational_mechanization",
    }
    assert set(manifest.clusters.keys()) == expected_clusters

    # Check total modes across clusters equal 20
    all_cluster_modes = []
    for c in manifest.clusters.values():
        all_cluster_modes.extend(c.mode_ids)
    assert sorted(all_cluster_modes) == list(range(1, 21))


def test_load_all_mode_contracts_twenty_closed():
    """Verify that all 20 mode contracts are loaded with strict claim hygiene."""
    contracts = load_all_mode_contracts()
    assert len(contracts) == 20

    for mid in range(1, 21):
        assert mid in contracts
        contract = contracts[mid]
        assert isinstance(contract, ModeContract)
        assert contract.mode_id == mid
        assert len(contract.name) > 0
        assert len(contract.cluster) > 0
        assert contract.authority_effect == "None"
        assert len(contract.rules) >= 1
        assert len(contract.winning_condition) > 0
        assert isinstance(contract.failure_modes, list)
        assert isinstance(contract.verifier_contract, dict)
        assert Path(contract.file_path).is_file()


def test_catalog_closure():
    """Verify zero orphan files and zero missing contracts between manifest and disk."""
    closure = validate_mode_catalog_closure()
    assert closure["is_closed"] is True
    assert closure["total_modes_count"] == 20
    assert closure["declared_modes_count"] == 20
    assert closure["disk_files_count"] == 20
    assert len(closure["missing_on_disk"]) == 0
    assert len(closure["extra_on_disk"]) == 0


def test_env_var_override_dynamic_discovery(tmp_path: Path):
    """Verify that SYMBOL_GAME_MODES_DIR environment variable overrides default search."""
    # Create a minimal fake modes directory
    fake_manifest = tmp_path / "modes_manifest.yaml"
    fake_manifest.write_text(
        """manifest_version: "2.0.0"
title: "Custom Mock Modes"
clusters:
  c1:
    name: "Mock Cluster"
    modes: [99]
modes:
  - id: 99
    file: "mode_99.yaml"
    name: "Mock Mode"
    cluster: "Mock Cluster"
""",
        encoding="utf-8",
    )
    fake_mode = tmp_path / "mode_99.yaml"
    fake_mode.write_text(
        """mode_id: 99
name: "Mock Mode"
cluster: "Mock Cluster"
authority_effect: "None"
core_mechanism: "Testing"
substrate: "Test Substrate"
rules: ["Test Rule"]
winning_condition: "All tests pass"
""",
        encoding="utf-8",
    )

    old_env = os.environ.get("SYMBOL_GAME_MODES_DIR")
    try:
        os.environ["SYMBOL_GAME_MODES_DIR"] = str(tmp_path)
        discovered_dir = find_modes_dir()
        assert discovered_dir == tmp_path

        manifest = discover_modes_manifest()
        assert manifest.title == "Custom Mock Modes"

        contracts = load_all_mode_contracts()
        assert 99 in contracts
        assert contracts[99].name == "Mock Mode"
    finally:
        if old_env is not None:
            os.environ["SYMBOL_GAME_MODES_DIR"] = old_env
        else:
            os.environ.pop("SYMBOL_GAME_MODES_DIR", None)


def test_use_cases_list_get_validate():
    """Verify domain use cases operate independently of CLI presentation."""
    list_uc = ListModesUseCase(discover_modes_manifest, load_all_mode_contracts)
    res = list_uc.execute()
    assert res["total_count"] == 20
    assert len(res["modes"]) == 20

    # Filter by cluster
    carrier_res = list_uc.execute(cluster_filter="Carrier")
    assert carrier_res["returned_count"] == 4
    assert len(carrier_res["modes"]) == 4

    get_uc = GetModeUseCase(load_all_mode_contracts)
    mode_2 = get_uc.execute(2)
    assert mode_2 is not None
    assert mode_2.name == "Packets & Sealed Envelopes"

    with pytest.raises(KeyError):
        get_uc.execute(999)

    val_uc = ValidateModesUseCase(validate_mode_catalog_closure)
    audit = val_uc.execute()
    assert audit["is_closed"] is True


def test_cli_runner_mode_list(capsys):
    """Verify CLI command: symbol-game mode list."""
    exit_code = main(["mode", "list"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "The Twenty Canonical Modes of The Symbol Game" in captured.out
    assert "Packets & Sealed Envelopes" in captured.out
    assert "Genesis First-Cut <arb> Marking" in captured.out


def test_use_cases_accept_an_in_memory_catalog():
    contracts = {
        mid: ModeContract(mid, name, cluster, "None", "rewrite", "symbols", "fixture")
        for mid, name, cluster in ((7, "Second", "Other"), (2, "First", "Carrier"))
    }
    manifest = ModesManifest("test", "Memory catalog", "fixture", {}, [], "memory/modes.yaml")
    load_contracts = lambda: contracts
    listing = ListModesUseCase(lambda: manifest, load_contracts)
    assert [row["mode_id"] for row in listing.execute()["modes"]] == [2, 7]
    filtered = listing.execute("carrier")
    assert (filtered["total_count"], filtered["returned_count"]) == (2, 1)
    assert filtered["modes"][0]["name"] == "First"
    assert GetModeUseCase(load_contracts).execute(7) is contracts[7]
    with pytest.raises(KeyError, match="99"):
        GetModeUseCase(load_contracts).execute(99)
    assert ValidateModesUseCase(lambda: {"is_closed": False}).execute() == {"is_closed": False}


def test_cli_runner_mode_show(capsys):
    """Verify CLI command: symbol-game mode show 2."""
    exit_code = main(["mode", "show", "2"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "MODE 2: Packets & Sealed Envelopes" in captured.out
    assert "Winning Condition:" in captured.out
    assert "Authority: None" in captured.out


def test_cli_runner_mode_validate(capsys):
    """Verify CLI command: symbol-game mode validate."""
    exit_code = main(["mode", "validate"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Closure Status  : [PASS] CLOSED" in captured.out

