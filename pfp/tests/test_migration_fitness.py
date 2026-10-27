"""Migration coverage refuses stale or incomplete reviewed source inventories."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from pfp.infrastructure.migration_fitness import (
    DEFAULT_MAP,
    MAP_SCHEMA,
    check_file_map,
)


@pytest.fixture
def mapped_repo(tmp_path: Path):
    source = "pfp/domain/example.py"
    target = "engine/crates_rs/core_symbol_game/src/lib.rs"
    (tmp_path / source).parent.mkdir(parents=True)
    (tmp_path / source).write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / target).parent.mkdir(parents=True)
    (tmp_path / target).write_text("pub fn example() {}\n", encoding="utf-8")
    row = {
        "path": source,
        "source_sha256": hashlib.sha256((tmp_path / source).read_bytes()).hexdigest(),
        "rust_targets": [target + "::example"],
        "status": "partial",
        "action": "Keep fixture controls until compiled parity is verified.",
    }
    map_path = tmp_path / "map.json"
    document = {"schema_version": MAP_SCHEMA, "files": [row]}
    map_path.write_text(json.dumps(document), encoding="utf-8")
    return tmp_path, map_path, document, source, target


def _check(mapped_repo, *, extra_paths=()):
    root, map_path, document, source, _ = mapped_repo
    map_path.write_text(json.dumps(document), encoding="utf-8")
    return check_file_map(root, map_path, tracked_paths=(source, *extra_paths))


def test_a_complete_map_checks_original_bytes_and_existing_native_owner(mapped_repo):
    assert _check(mapped_repo) == ()


def test_new_tracked_source_cannot_disappear_from_the_migration_map(mapped_repo):
    findings = _check(mapped_repo, extra_paths=("pfp/domain/new.py",))
    assert [(value.code, value.path) for value in findings] == [
        ("UNMAPPED_SOURCE", "pfp/domain/new.py")
    ]


def test_a_changed_source_refuses_even_when_inventory_and_target_still_match(mapped_repo):
    root, _, _, source, _ = mapped_repo
    (root / source).write_text("VALUE = 2\n", encoding="utf-8")
    assert [value.code for value in _check(mapped_repo)] == ["SOURCE_CHANGED"]


@pytest.mark.parametrize(
    ("reviewed", "changed"),
    [(b"VALUE = 1\n", b"VALUE = 1\r\n"), (b"VALUE = 1\r\n", b"VALUE = 1\n")],
    ids=("lf-to-crlf", "crlf-to-lf"),
)
def test_newline_only_drift_requires_explicit_raw_byte_reconciliation(
    mapped_repo, reviewed, changed
):
    root, _, document, source, _ = mapped_repo
    row = document["files"][0]
    original_digest = hashlib.sha256(reviewed).hexdigest()
    row.update(source_sha256=original_digest, baseline_source_sha256=original_digest)
    (root / source).write_bytes(reviewed)
    assert _check(mapped_repo) == ()

    (root / source).write_bytes(changed)
    assert [value.code for value in _check(mapped_repo)] == ["SOURCE_CHANGED"]
    assert row["source_sha256"] == row["baseline_source_sha256"] == original_digest

    row["source_sha256"] = hashlib.sha256(changed).hexdigest()
    assert _check(mapped_repo) == ()
    assert row["baseline_source_sha256"] == original_digest


def test_duplicate_source_rows_do_not_count_as_complete_coverage(mapped_repo):
    _, _, document, _, _ = mapped_repo
    document["files"].append(document["files"][0].copy())
    assert [value.code for value in _check(mapped_repo)] == ["DUPLICATE_SOURCE"]


@pytest.mark.parametrize(
    "target",
    [
        "../secret.rs",
        "engine/crates_rs/absent.rs",
        "other/lib.rs",
        "core_symbol_game::graph",
    ],
)
def test_native_targets_must_name_existing_repository_owner_files(mapped_repo, target):
    _, _, document, _, _ = mapped_repo
    document["files"][0]["rust_targets"] = [target]
    assert [value.code for value in _check(mapped_repo)] == ["BAD_RUST_TARGET"]


def test_python_source_requires_a_byte_commitment(mapped_repo):
    _, _, document, _, _ = mapped_repo
    del document["files"][0]["source_sha256"]
    assert [value.code for value in _check(mapped_repo)] == ["BAD_SOURCE_DIGEST"]


def test_duplicate_json_keys_refuse_before_rows_are_interpreted(mapped_repo):
    root, map_path, _, source, _ = mapped_repo
    map_path.write_text(
        '{"schema_version":"wrong","schema_version":"other","files":[]}', encoding="utf-8"
    )
    findings = check_file_map(root, map_path, tracked_paths=(source,))
    assert [value.code for value in findings] == ["MAP_UNAVAILABLE"]
    assert "duplicate JSON key" in findings[0].detail


def test_map_size_bound_accepts_exact_limit_and_refuses_extra_bytes(mapped_repo, monkeypatch):
    from pfp.infrastructure import migration_fitness

    root, map_path, document, source, _ = mapped_repo
    raw = json.dumps(document).encode("utf-8")
    monkeypatch.setattr(migration_fitness, "MAX_MAP_BYTES", len(raw))
    map_path.write_bytes(raw)
    assert check_file_map(root, map_path, tracked_paths=(source,)) == ()
    map_path.write_bytes(raw + b" ")
    findings = check_file_map(root, map_path, tracked_paths=(source,))
    assert [item.code for item in findings] == ["MAP_UNAVAILABLE"]
    assert "exceeds inspection byte limit" in findings[0].detail


def test_a_symlink_cannot_make_an_external_file_a_native_owner(mapped_repo):
    root, _, document, _, _ = mapped_repo
    outside = root.parent / (root.name + "-external.rs")
    outside.write_text("external", encoding="utf-8")
    link = root / "engine/crates_rs/outside.rs"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("host cannot create test symlinks")
    document["files"][0]["rust_targets"] = ["engine/crates_rs/tests/outside.rs"]
    assert [value.code for value in _check(mapped_repo)] == ["BAD_RUST_TARGET"]


def test_a_native_owner_claim_requires_an_actual_target(mapped_repo):
    _, _, document, _, _ = mapped_repo
    document["files"][0].update(status="native-owner", rust_targets=[])
    assert [value.code for value in _check(mapped_repo)] == ["NATIVE_OWNER_MISSING"]


def test_even_noncode_assets_require_reviewed_bytes(mapped_repo):
    root, map_path, document, _, _ = mapped_repo
    asset = "pfp/fixtures/example.json"
    (root / asset).parent.mkdir(parents=True)
    (root / asset).write_text("{}", encoding="utf-8")
    document["files"][0]["path"] = asset
    del document["files"][0]["source_sha256"]
    map_path.write_text(json.dumps(document), encoding="utf-8")
    assert [value.code for value in check_file_map(root, map_path, tracked_paths=(asset,))] == [
        "BAD_SOURCE_DIGEST"
    ]


def test_self_referential_map_is_covered_without_an_impossible_self_digest(mapped_repo):
    root, _, document, source, _ = mapped_repo
    map_path = root / DEFAULT_MAP
    map_path.parent.mkdir(parents=True)
    document["files"].append(
        {
            "path": DEFAULT_MAP,
            "rust_targets": [],
            "status": "documentation",
            "action": "Keep reviewed source inventory current.",
        }
    )
    map_path.write_text(json.dumps(document), encoding="utf-8")
    assert check_file_map(root, map_path, tracked_paths=(source, DEFAULT_MAP)) == ()


def test_empty_inventory_cannot_report_complete_coverage(mapped_repo):
    root, map_path, _, _, _ = mapped_repo
    assert [value.code for value in check_file_map(root, map_path, tracked_paths=())] == [
        "MAP_UNAVAILABLE"
    ]


def test_current_review_map_covers_the_actual_git_index_and_source_bytes():
    root = Path(__file__).resolve().parents[2]
    findings = check_file_map(root)
    assert not findings, dict(Counter(finding.code for finding in findings))


def test_previous_review_map_remains_exactly_recoverable_with_baseline_custody():
    root = Path(__file__).resolve().parents[2]
    current = json.loads((root / DEFAULT_MAP).read_bytes())
    prior = current["current_review"]["previous_map"]
    raw = subprocess.check_output(
        ["git", "cat-file", "blob", f"{prior['revision']}:{prior['path']}"], cwd=root
    )
    assert hashlib.sha256(raw).hexdigest() == prior["sha256"]
    historical = json.loads(raw)
    assert historical["baseline_commit"] == current["baseline_commit"]
    assert historical["baseline_files_reviewed"] == current["baseline_files_reviewed"] == 4803
    old = {row["path"]: row for row in historical["files"]}
    for row in current["files"]:
        if row["path"] in old:
            assert row.get("baseline_source_sha256") == old[row["path"]].get(
                "baseline_source_sha256"
            )


def test_explicit_source_binding_reconciliation_preserves_fixed_base_rows_and_pins():
    root = Path(__file__).resolve().parents[2]

    def git_blob(revision, path):
        return subprocess.check_output(
            ["git", "cat-file", "blob", f"{revision}:{path}"], cwd=root
        )

    # This completed review concerns its immutable landing, not future edits.
    reviewed_revision = "ff6b85506e2219e43d8a1770ed04e2c84668ddc4"
    reviewed_raw = git_blob(reviewed_revision, DEFAULT_MAP)
    assert hashlib.sha256(reviewed_raw).hexdigest() == (
        "a8df694c08b69e8be9a3387d016ae441be29d941ecfb54652c277cef580e9550"
    )
    current = json.loads(reviewed_raw)
    reconciliation = current["current_review"]["source_binding_reconciliation"]
    previous_map = reconciliation["previous_map"]
    assert previous_map["revision"] == "20d9d41c684f6a88ff856b8434dfe97202a8b5fe"
    assert previous_map["path"] == DEFAULT_MAP
    assert previous_map["sha256"] == (
        "5ddb0f6e0d98b33a719e05d69d5e093372a4d426c9e01bdb932659ac7ca4ea68"
    )

    previous_raw = git_blob(previous_map["revision"], previous_map["path"])
    assert hashlib.sha256(previous_raw).hexdigest() == previous_map["sha256"]
    previous = json.loads(previous_raw)
    assert reconciliation["receipt"] == (
        "_ic/adversary/rust_map_reconciliation_20261013/reconciliation.json"
    )
    receipt_file = root / reconciliation["receipt"]
    receipt_raw = (
        receipt_file.read_bytes()
        if receipt_file.is_file()
        else git_blob(reviewed_revision, reconciliation["receipt"])
    )
    assert hashlib.sha256(receipt_raw).hexdigest() == reconciliation["receipt_sha256"]
    receipt = json.loads(receipt_raw)
    rows = {row["path"]: row for row in receipt["rows"]}
    maintenance = {row["path"]: row for row in receipt["maintenance_rows"]}
    assert len(rows) == len(receipt["rows"]) == 126
    assert len(maintenance) == len(receipt["maintenance_rows"])
    assert not rows.keys() & maintenance.keys()
    old = {row["path"]: row for row in previous["files"]}
    new = {row["path"]: row for row in current["files"]}
    assert old.keys() == new.keys()
    assert rows.keys() | maintenance.keys() <= old.keys()
    for key, value in previous.items():
        if key not in {"files", "current_review"}:
            assert current[key] == value, key
    for key, value in previous["current_review"].items():
        assert current["current_review"][key] == value, key

    classifications = Counter()
    for path, prior_row in old.items():
        record = rows.get(path, maintenance.get(path))
        if record is None:
            assert new[path] == prior_row, path
            continue
        assert record["previous_row"] == prior_row, path
        raw = git_blob(reviewed_revision, path)
        assert record["current_source_sha256"] == hashlib.sha256(raw).hexdigest(), path
        assert record["current_bytes"] == len(raw), path
        expected = prior_row.copy()
        expected["source_sha256"] = record["current_source_sha256"]
        if "bytes_reviewed" in expected:
            expected["bytes_reviewed"] = len(raw)
        if path in maintenance and "definitions" in expected:
            expected["definitions"] = [
                node.name for node in ast.parse(raw.decode("utf-8-sig")).body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            ]
        assert new[path] == expected, path
        if path in maintenance:
            continue

        base_raw = git_blob(previous_map["revision"], path)
        classification = record["classification"]
        classifications[classification] += 1
        if classification == "EXACT_CRLF_REVIEW_PROJECTION":
            assert b"\r" not in raw and raw == base_raw, path
            assert hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest() == (
                prior_row["source_sha256"]
            ), path
            continue
        assert classification in {"HISTORICAL_MIXED_EOL", "MIXED_EOL_AND_REVIEWED_PATH_FIX"}
        historical = record["historical_git"]
        historical_raw = git_blob(historical["revision"], historical["path"])
        assert hashlib.sha256(historical_raw).hexdigest() == (
            historical["sha256"]
        ) == prior_row["source_sha256"], path
        historical_oid = subprocess.check_output(
            ["git", "rev-parse", f"{historical['revision']}:{historical['path']}"], cwd=root
        ).decode().strip()
        assert historical_oid == historical["blob_oid"], path
        assert historical_raw.replace(b"\r\n", b"\n") == base_raw, path
        if classification == "MIXED_EOL_AND_REVIEWED_PATH_FIX":
            assert path == "pfp/infrastructure/tower_evidence/level_engine/resolver.py"
            assert record["normalized_pre_fix_sha256"] == hashlib.sha256(base_raw).hexdigest()
            assert raw != base_raw
        else:
            assert raw == base_raw, path
    assert classifications["EXACT_CRLF_REVIEW_PROJECTION"] == 124
    assert sum(classifications.values()) == 126


DRIVER_PROMPT_LANDING = "b512f608f0d5b7a83d2a903e7b4ad96388f0f4b6"


def _git_blob(root: Path, revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", f"{revision}:{path}"], cwd=root)


def test_native_driver_review_preserves_previous_map_and_current_source_bindings():
    """The completed driver review stays bound to its landing, not later edits."""
    root = Path(__file__).resolve().parents[2]
    current = json.loads(_git_blob(root, DRIVER_PROMPT_LANDING, DEFAULT_MAP))
    review = current["current_review"]["driver_prompt_binding"]
    prior = review["previous_map"]
    assert prior["revision"] == "cbd47922df440271052b6b84d1b9cfe6848f25f0"
    assert prior["path"] == DEFAULT_MAP
    assert prior["sha256"] == (
        "5705a1d87bf25a6409116d216b8c883ebc34a0d7c5059d4522efd72020d187d0"
    )
    previous_raw = _git_blob(root, prior["revision"], prior["path"])
    assert hashlib.sha256(previous_raw).hexdigest() == prior["sha256"]
    previous = json.loads(previous_raw)
    receipt_raw = _git_blob(root, DRIVER_PROMPT_LANDING, review["receipt"])
    assert hashlib.sha256(receipt_raw).hexdigest() == review["receipt_sha256"]
    receipt = json.loads(receipt_raw)
    assert receipt["previous_map"] == prior
    records = {row["path"]: row for row in receipt["rows"]}
    assert len(records) == len(receipt["rows"])
    assert set(records) == set(review["reviewed_paths"])
    old = {row["path"]: row for row in previous["files"]}
    new = {row["path"]: row for row in current["files"]}
    assert old.keys() == new.keys()
    for key, value in previous.items():
        if key not in {"files", "current_review"}:
            assert current[key] == value, key
    for key, value in previous["current_review"].items():
        assert current["current_review"][key] == value, key
    mutable_fields = {
        "source_sha256", "bytes_reviewed", "definitions", "status", "action", "notes", "review_depth",
    }
    for path, old_row in old.items():
        if path not in records:
            assert new[path] == old_row, path
            continue
        record = records[path]
        assert record["previous_row"] == old_row, path
        assert record["current_row"] == new[path], path
        assert old_row.keys() == new[path].keys(), path
        changes = {key for key in old_row if old_row[key] != new[path][key]}
        assert changes <= mutable_fields, path
        assert changes == set(record["changed_fields"]), path
        raw = _git_blob(root, DRIVER_PROMPT_LANDING, path)
        assert hashlib.sha256(raw).hexdigest() == new[path]["source_sha256"], path
        if "bytes_reviewed" in new[path]:
            assert len(raw) == new[path]["bytes_reviewed"], path
    manifest = json.loads(
        _git_blob(root, DRIVER_PROMPT_LANDING, "pfp/migration_manifest.json")
    )
    assert manifest["migration_complete"] is False
    assert "prompt_identity_and_turn_lifecycle_parity" in manifest["remaining"]


def test_live_map_keeps_the_landed_driver_review_record():
    root = Path(__file__).resolve().parents[2]
    landing = json.loads(_git_blob(root, DRIVER_PROMPT_LANDING, DEFAULT_MAP))
    current = json.loads((root / DEFAULT_MAP).read_bytes())
    for key, value in landing["current_review"].items():
        assert current["current_review"][key] == value, key
    assert "demo_pfp_boundary" in current["current_review"]


def test_prompt_artifact_review_preserves_prior_pins_and_scoped_current_bindings():
    root = Path(__file__).resolve().parents[2]
    current = json.loads((root / DEFAULT_MAP).read_bytes())
    review = current["current_review"]["python_prompt_artifact_parity"]
    prior = review["previous_map"]
    assert prior == {
        "revision": "0acb16d89c8ef0dfd2c8566f436ff4c970836b77",
        "path": DEFAULT_MAP,
        "sha256": "ea8830ff5364e09ec8f9c260bc1e7e6c3fd9cda8dd26f03d29a5e18272adbf09",
    }
    previous_raw = subprocess.check_output(
        ["git", "cat-file", "blob", f"{prior['revision']}:{prior['path']}"], cwd=root
    )
    assert hashlib.sha256(previous_raw).hexdigest() == prior["sha256"]
    previous = json.loads(previous_raw)
    receipt_raw = (root / review["receipt"]).read_bytes()
    assert hashlib.sha256(receipt_raw).hexdigest() == review["receipt_sha256"]
    receipt = json.loads(receipt_raw)
    assert receipt["previous_map"] == prior
    records = {row["path"]: row for row in receipt["rows"]}
    assert len(records) == len(receipt["rows"])
    assert set(records) == set(review["reviewed_paths"])
    old = {row["path"]: row for row in previous["files"]}
    new = {row["path"]: row for row in current["files"]}
    assert new.keys() - old.keys() == set(review["new_paths"])
    assert not old.keys() - new.keys()
    for key, value in previous.items():
        if key not in {"files", "current_review"}:
            assert current[key] == value, key
    for key, value in previous["current_review"].items():
        assert current["current_review"][key] == value, key
    mutable_fields = {
        "source_sha256", "bytes_reviewed", "definitions", "status", "action", "notes",
        "review_depth", "rust_targets",
    }
    for path, new_row in new.items():
        if path not in records:
            assert new_row == old[path], path
            continue
        record = records[path]
        assert record["previous_row"] == old.get(path), path
        assert record["current_row"] == new_row, path
        if path in old:
            assert old[path].keys() == new_row.keys(), path
            changes = {key for key in old[path] if old[path][key] != new_row[key]}
            assert changes <= mutable_fields, path
            assert changes == set(record["changed_fields"]), path
        raw = (root / path).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == new_row["source_sha256"], path
        if "bytes_reviewed" in new_row:
            assert len(raw) == new_row["bytes_reviewed"], path
    assert new["pfp/domain/aggregates/prompt_artifact.py"]["status"] == "partial_native"
    assert new["pfp/use_cases/prompt_artifact.py"]["status"] == "partial_native"
    manifest = json.loads((root / "pfp/migration_manifest.json").read_bytes())
    assert manifest["migration_complete"] is False
    assert "native_canonical_prompt_artifact_parity" in manifest["implemented"]
    assert "prompt_identity_and_turn_lifecycle_parity" in manifest["remaining"]



def test_current_source_metadata_cannot_retain_removed_definitions_or_old_sizes():
    root = Path(__file__).resolve().parents[2]
    current = json.loads((root / DEFAULT_MAP).read_bytes())
    for row in current["files"]:
        if "bytes_reviewed" in row:
            raw = (root / row["path"]).read_bytes()
            assert row["bytes_reviewed"] == len(raw), row["path"]
        if "definitions" in row:
            tree = ast.parse((root / row["path"]).read_text(encoding="utf-8-sig"))
            assert row["definitions"] == [
                node.name for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            ], row["path"]
