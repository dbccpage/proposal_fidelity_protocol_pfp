"""Custody and discrimination tests for the Symbol Game attack census."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from omega_engine_operations.use_cases.verification import (
    symbol_game_attack_surface as census,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return completed.stdout.strip()


def _write(root: Path, path: str, text: str) -> None:
    destination = root / path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8", newline="\n")


def _commit_all(root: Path) -> str:
    _git(root, "add", "--all")
    _git(
        root,
        "-c",
        "user.name=Attack Census Test",
        "-c",
        "user.email=attack-census@example.invalid",
        "commit",
        "-m",
        "fixture",
    )
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def fixture_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "--initial-branch=main")
    _git(root, "remote", "add", "origin", "https://example.invalid/census.git")

    _write(
        root,
        "omega_engine_governance/contracts/packet.json",
        '{"packet":"positive"}\n',
    )
    _write(
        root,
        "omega_engine_pfp/core.py",
        "from shared.helper import VALUE\nRESULT = VALUE\n",
    )
    _write(root, "shared/helper.py", "VALUE = 7\n")
    _write(
        root,
        "external/caller.py",
        "from omega_engine_pfp.core import RESULT\n",
    )
    _write(
        root,
        "external/dynamic.py",
        "import importlib\n"
        'MODULE = importlib.import_module("omega_engine_pfp.core")\n',
    )
    _write(root, "unrelated/leave_me_out.txt", "not connected\n")
    _write(
        root,
        "tsconfig.json",
        '{"compilerOptions":{"paths":{"@/*":["./*"]}}}\n',
    )
    _write(
        root,
        "_ooutwire/legacy-note.md",
        "Historical omega_engine/crates/symbol_game citation.\n",
    )
    _write(
        root,
        "tools/live_legacy_config.yaml",
        "crate: omega_engine/crates/symbol_game\n",
    )
    _write(
        root,
        ".github/workflows/integration.yml",
        "on:\n"
        "  pull_request:\n"
        "    paths:\n"
        '      - "omega_engine_pfp/**"\n'
        "jobs:\n"
        "  verify:\n"
        "    steps:\n"
        "      - run: python tools/workflow_gate.py\n",
    )
    _write(root, "tools/workflow_gate.py", "RESULT = 'workflow reached'\n")
    _write(
        root,
        "tools/generate_contracts.py",
        'SOURCE = "omega_engine_governance/contracts/packet.json"\n',
    )
    _write(
        root,
        "tools/contract_consumer.yaml",
        "contract: omega_engine_governance/contracts/packet.json\n",
    )

    _write(
        root,
        "omega_engine/crates_rs/Cargo.toml",
        "[workspace]\n"
        "members = [\n"
        '  "omega_symbol_game_runtime",\n'
        '  "omega_symbol_game",\n'
        '  "../../tools/workspace_only",\n'
        "]\n",
    )
    _write(
        root,
        "omega_engine/crates_rs/contract_shapes_build.rs",
        "pub fn generate_contract_shapes() {}\n",
    )
    _write(
        root,
        "omega_engine/crates_rs/shared_runtime/Cargo.toml",
        '[package]\nname = "shared_runtime"\nversion = "0.1.0"\n',
    )
    _write(
        root,
        "omega_engine/crates_rs/shared_runtime/src/lib.rs",
        "pub const SHARED: bool = true;\n",
    )
    _write(
        root,
        "omega_engine/crates_rs/omega_symbol_game_runtime/Cargo.toml",
        '[package]\nname = "omega_symbol_game_runtime"\nversion = "0.1.0"\n'
        '[dependencies]\nshared_runtime = { path = "../shared_runtime" }\n',
    )
    _write(
        root,
        "omega_engine/crates_rs/omega_symbol_game_runtime/src/lib.rs",
        "mod worker;\npub const RUNTIME: bool = worker::READY;\n",
    )
    _write(
        root,
        "omega_engine/crates_rs/omega_symbol_game_runtime/src/worker.rs",
        "pub const READY: bool = true;\n",
    )
    _write(
        root,
        "omega_engine/crates_rs/omega_symbol_game_runtime/build.rs",
        'include!("../contract_shapes_build.rs");\n',
    )
    _write(
        root,
        "omega_engine/crates_rs/omega_symbol_game/Cargo.toml",
        '[package]\nname = "omega_symbol_game"\nversion = "0.1.0"\n'
        '[dependencies]\nomega_symbol_game_runtime = '
        '{ path = "../omega_symbol_game_runtime" }\n',
    )
    _write(
        root,
        "omega_engine/crates_rs/omega_symbol_game/src/main.rs",
        "fn main() {}\n",
    )
    _write(
        root,
        "omega_engine/crates_rs/omega_symbol_game/build.rs",
        'include!("../contract_shapes_build.rs");\n',
    )
    _write(
        root,
        "tools/rust_consumer/Cargo.toml",
        '[package]\nname = "rust_consumer"\nversion = "0.1.0"\n'
        '[dependencies]\nomega_symbol_game = '
        '{ path = "../../omega_engine/crates_rs/omega_symbol_game" }\n',
    )
    _write(root, "tools/rust_consumer/src/lib.rs", "pub fn consume() {}\n")
    _write(
        root,
        "tools/workspace_only/Cargo.toml",
        '[package]\nname = "workspace_only"\nversion = "0.1.0"\n',
    )
    _write(root, "tools/workspace_only/src/lib.rs", "pub const ONLY: bool = true;\n")
    return root, _commit_all(root)


def _by_path(manifest: census.Manifest) -> dict[str, dict]:
    return {str(record["path"]): dict(record) for record in manifest.files}


def test_census_closes_over_python_and_cargo_consumers(
    fixture_repo: tuple[Path, str],
) -> None:
    root, commit = fixture_repo
    manifest = census.build_manifest(root, commit)
    records = _by_path(manifest)

    required = {
        "omega_engine_governance/contracts/packet.json",
        "omega_engine_pfp/core.py",
        "shared/helper.py",
        "external/caller.py",
        "external/dynamic.py",
        "omega_engine/crates_rs/shared_runtime/src/lib.rs",
        "omega_engine/crates_rs/omega_symbol_game_runtime/src/lib.rs",
        "omega_engine/crates_rs/omega_symbol_game/src/main.rs",
        "tools/rust_consumer/src/lib.rs",
        "omega_engine/crates_rs/contract_shapes_build.rs",
        "omega_engine/crates_rs/omega_symbol_game_runtime/src/worker.rs",
        "tools/workspace_only/src/lib.rs",
        ".github/workflows/integration.yml",
        "tools/workflow_gate.py",
        "tools/generate_contracts.py",
        "tools/contract_consumer.yaml",
        "_ooutwire/legacy-note.md",
        "tools/live_legacy_config.yaml",
    }
    assert required <= records.keys()
    assert "unrelated/leave_me_out.txt" not in records
    assert "tsconfig.json" not in records
    assert "python-import-closure" in records["shared/helper.py"][
        "inclusion_reasons"
    ]
    assert "rust-crate-dependency-closure" in records[
        "tools/rust_consumer/src/lib.rs"
    ]["inclusion_reasons"]
    runtime_build_edges = records[
        "omega_engine/crates_rs/omega_symbol_game_runtime/build.rs"
    ]["dependency_edges"]
    assert {
        "kind": "rust_include",
        "target": "omega_engine/crates_rs/contract_shapes_build.rs",
    } in runtime_build_edges
    runtime_lib_edges = records[
        "omega_engine/crates_rs/omega_symbol_game_runtime/src/lib.rs"
    ]["dependency_edges"]
    assert {
        "kind": "rust_module",
        "target": "omega_engine/crates_rs/omega_symbol_game_runtime/src/worker.rs",
    } in runtime_lib_edges
    workspace_edges = records["omega_engine/crates_rs/Cargo.toml"][
        "dependency_edges"
    ]
    assert {
        "kind": "cargo_workspace_member",
        "target": "tools/workspace_only/Cargo.toml",
    } in workspace_edges
    workflow_edges = records[".github/workflows/integration.yml"][
        "dependency_edges"
    ]
    assert {
        "kind": "workflow_path",
        "target": "tools/workflow_gate.py",
    } in workflow_edges
    assert {
        "kind": "generator_path",
        "target": "omega_engine_governance/contracts/packet.json",
    } in records["tools/generate_contracts.py"]["dependency_edges"]
    assert {
        "kind": "contract_binding",
        "target": "omega_engine_governance/contracts/packet.json",
    } in records["tools/contract_consumer.yaml"]["dependency_edges"]


def test_records_bind_exact_blob_bytes_and_not_the_worktree(
    fixture_repo: tuple[Path, str],
) -> None:
    root, commit = fixture_repo
    committed = b"VALUE = 7\n"
    (root / "shared/helper.py").write_text(
        "VALUE = 999\n", encoding="utf-8", newline="\n"
    )

    record = _by_path(census.build_manifest(root, commit))["shared/helper.py"]

    assert record["byte_count"] == len(committed)
    assert record["sha256"] == hashlib.sha256(committed).hexdigest()
    assert record["blob_oid"] == _git(root, "rev-parse", f"{commit}:shared/helper.py")


def test_output_is_canonical_and_deterministic(
    fixture_repo: tuple[Path, str],
) -> None:
    root, commit = fixture_repo
    first = census.render_manifest(census.build_manifest(root, commit))
    second = census.render_manifest(census.build_manifest(root, commit))

    assert first == second
    assert not first.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" not in first
    assert first.endswith(b"\n")


def test_legacy_references_are_not_silently_treated_as_equivalent(
    fixture_repo: tuple[Path, str],
) -> None:
    root, commit = fixture_repo
    records = _by_path(census.build_manifest(root, commit))

    assert records["_ooutwire/legacy-note.md"]["disposition"] == (
        "HISTORICAL_OR_PROVENANCE_REVIEW"
    )
    assert records["tools/live_legacy_config.yaml"]["disposition"] == (
        "LIVE_REFERENCE_REVIEW"
    )


def test_missing_baseline_and_zero_scope_are_decisive_refusals(tmp_path: Path) -> None:
    root = tmp_path / "empty-scope"
    root.mkdir()
    _git(root, "init", "--initial-branch=main")
    _write(root, "unrelated.txt", "nothing to inventory\n")
    commit = _commit_all(root)

    with pytest.raises(census.CensusError, match="baseline commit is missing"):
        census.build_manifest(root, "f" * 40)
    with pytest.raises(census.CensusError, match="found zero files"):
        census.build_manifest(root, commit)


def test_broken_dependency_edge_and_tampered_copy_are_rejected(
    fixture_repo: tuple[Path, str], tmp_path: Path
) -> None:
    root, commit = fixture_repo
    original = census.build_manifest(root, commit)
    records = [dict(record) for record in original.files]
    records = [record for record in records if record["path"] != "shared/helper.py"]
    broken = census.Manifest(original.header, tuple(records))
    with pytest.raises(census.CensusError, match="dependency target is missing"):
        census.validate_manifest(broken)

    path = tmp_path / "manifest.jsonl"
    census.write_manifest(root, commit, path)
    lines = path.read_text(encoding="utf-8").splitlines()
    row = json.loads(lines[1])
    row["sha256"] = "0" * 64
    lines[1] = json.dumps(row, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    with pytest.raises(census.CensusError, match="stale or non-canonical"):
        census.check_manifest(root, path)


def test_duplicate_hash_classification_and_attack_assignment_defects_refuse(
    fixture_repo: tuple[Path, str],
) -> None:
    root, commit = fixture_repo
    original = census.build_manifest(root, commit)

    cases = (
        (lambda rows: rows[1].__setitem__("path", rows[0]["path"]), "unique"),
        (lambda rows: rows[0].__setitem__("sha256", ""), "SHA-256"),
        (lambda rows: rows[0].__setitem__("role", ""), "role is invalid"),
        (lambda rows: rows[0].__setitem__("attack_lanes", []), "attack assignment"),
    )
    for mutate, expected in cases:
        rows = copy.deepcopy(list(original.files))
        mutate(rows)
        damaged = census.Manifest(copy.deepcopy(original.header), tuple(rows))
        with pytest.raises(census.CensusError, match=expected):
            census.validate_manifest(damaged)


def test_shipped_manifest_rebuilds_byte_for_byte_from_its_pinned_commit() -> None:
    manifest = census.check_manifest(REPO_ROOT, Path(census.DEFAULT_MANIFEST))

    assert manifest.header["authority_effect"] == "None"
    assert manifest.header["baseline_commit"] == (
        "36c62333335d56cea539b564add7b5fa5439a9fb"
    )
    assert manifest.header["baseline_tree"] == (
        "dd43700697688d73e0d9e4d000c8ec80ab16a353"
    )
    assert manifest.header["counts"]["included_files"] > 0


def test_retired_evidence_manifest_path_resolves_to_historical_custody() -> None:
    resolved = census.resolve_manifest_path(
        REPO_ROOT,
        Path(
            "omega_engine_operations/evidence/"
            "symbol_game_attack_surface_20260903.jsonl"
        ),
    )
    assert resolved == REPO_ROOT / census.DEFAULT_MANIFEST
