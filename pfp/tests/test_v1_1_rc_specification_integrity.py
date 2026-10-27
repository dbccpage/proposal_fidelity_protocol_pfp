"""Isolated artifact-custody controls; no pilot, model, or engine is executed."""

from __future__ import annotations

import gzip
import hashlib
import json
import platform
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from pfp.scripts import verify_v1_1_rc_specification as integrity


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _manifest_row(root: Path, path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(root).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _refresh_manifest(root: Path) -> dict:
    evidence = root / integrity.EVIDENCE_DIRECTORY
    artifacts = [root / integrity.MONOGRAPH, evidence / "census.json", evidence / "records.json.gz"]
    manifest = {
        "base_commit": "a" * 40,
        "sources": sorted(
            (
                _manifest_row(root, path)
                for path in [root / "source.txt", *sorted((root / "tests").glob("test_*.py"))]
            ),
            key=lambda row: row["path"].encode("utf-8"),
        ),
        "artifacts": sorted(
            (_manifest_row(root, path) for path in artifacts),
            key=lambda row: row["path"].encode("utf-8"),
        ),
    }
    _write_json(root / integrity.DEFAULT_MANIFEST, manifest)
    return manifest


@pytest.fixture
def audit_tree(tmp_path: Path) -> Path:
    (tmp_path / "source.txt").write_text("immutable source\n", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    for i in range(308):
        (tmp_path / "tests" / f"test_{i:03}.py").write_text(
            "# Unexecuted isolated fixture module.\n"
        )
    monograph = tmp_path / integrity.MONOGRAPH
    monograph.parent.mkdir(parents=True)
    monograph.write_text("# Isolated audit fixture\n", encoding="utf-8")
    census = {
        "base_commit": "a" * 40,
        "audit_mode": "static_source_and_record_audit",
        "curriculum": [{"id": f"{i:03}"} for i in range(13)],
        "pilots": [
            {
                "id": i,
                "materialization": "present",
                "evidence_status": "recorded",
                "executed_now": False,
                "empirical_verified": False,
            }
            for i in range(1, 76)
        ],
        "antibodies": [{"id": f"AB-{i:03}"} for i in range(1, 20)],
        "adversary_modules": [
            {"path": f"tests/test_{i:03}.py", "provenance": "source_only", "executed_now": False}
            for i in range(308)
        ],
    }
    _write_json(tmp_path / integrity.DEFAULT_CENSUS, census)
    compressed = tmp_path / integrity.EVIDENCE_DIRECTORY / "records.json.gz"
    payload = {
        "schema_version": integrity.GZIP_SCHEMA,
        "base_commit": "a" * 40,
        "audit_mode": "static_source_and_record_audit",
        "records": [{"status": "recorded"}],
    }
    compressed.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8"), mtime=0))
    _refresh_manifest(tmp_path)
    return tmp_path


def _change_census(root: Path, change) -> None:
    path = root / integrity.DEFAULT_CENSUS
    census = json.loads(path.read_text())
    change(census)
    _write_json(path, census)
    _refresh_manifest(root)


def test_valid_fixture_has_exact_coverage_and_narrow_receipt(audit_tree):
    receipt = integrity.verify(audit_tree)
    assert receipt["status"] == "PASS"
    assert receipt["census_counts"] == {
        "curriculum": 13,
        "pilots": 75,
        "antibodies": 19,
        "adversary_modules": 308,
    }
    assert receipt["gzip_json_files_checked"] == 1
    assert "no mathematical or runtime certification" in receipt["scope"]


def test_changed_source_bytes_are_refused(audit_tree):
    (audit_tree / "source.txt").write_text("tampered\n")
    with pytest.raises(integrity.IntegrityError, match="SHA-256 mismatch"):
        integrity.verify(audit_tree)


def test_missing_declared_file_is_refused(audit_tree):
    (audit_tree / "source.txt").unlink()
    with pytest.raises(integrity.IntegrityError, match="missing manifest file"):
        integrity.verify(audit_tree)


def test_duplicate_manifest_path_is_refused(audit_tree):
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["sources"].append(manifest["sources"][0])
    _write_json(path, manifest)
    with pytest.raises(integrity.IntegrityError, match="duplicate manifest path"):
        integrity.verify(audit_tree)


def test_unsorted_artifact_paths_are_refused(audit_tree):
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["artifacts"].reverse()
    _write_json(path, manifest)
    with pytest.raises(integrity.IntegrityError, match="sorted in UTF-8 order"):
        integrity.verify(audit_tree)


@pytest.mark.parametrize("category", ["curriculum", "pilots", "antibodies", "adversary_modules"])
def test_missing_required_census_member_is_refused(audit_tree, category):
    _change_census(audit_tree, lambda census: census[category].pop())
    with pytest.raises(integrity.IntegrityError, match="exact required set|exactly 308"):
        integrity.verify(audit_tree)


def test_duplicate_pilot_id_is_refused_even_with_correct_row_count(audit_tree):
    _change_census(audit_tree, lambda census: census["pilots"][1].update(id=1))
    with pytest.raises(integrity.IntegrityError, match="duplicate census pilots id"):
        integrity.verify(audit_tree)


def test_boolean_id_cannot_impersonate_pilot_one(audit_tree):
    _change_census(audit_tree, lambda census: census["pilots"][0].update(id=True))
    with pytest.raises(integrity.IntegrityError, match="id must be an integer"):
        integrity.verify(audit_tree)


def test_absent_pilot_cannot_be_claimed_empirically_verified(audit_tree):
    _change_census(
        audit_tree,
        lambda census: census["pilots"][0].update(
            materialization="absent", evidence_status="absent", empirical_verified=True
        ),
    )
    with pytest.raises(
        integrity.IntegrityError, match="cannot be empirically verified or executed"
    ):
        integrity.verify(audit_tree)


def test_source_only_module_cannot_be_claimed_executed(audit_tree):
    _change_census(audit_tree, lambda census: census["adversary_modules"][0].update(executed_now=True))
    with pytest.raises(integrity.IntegrityError, match="cannot be labelled executed now"):
        integrity.verify(audit_tree)


def test_corrupt_gzip_is_refused_even_when_its_hash_is_resealed(audit_tree):
    path = audit_tree / integrity.EVIDENCE_DIRECTORY / "records.json.gz"
    path.write_bytes(b"not a gzip stream")
    _refresh_manifest(audit_tree)
    with pytest.raises(integrity.IntegrityError, match="cannot decode gzip JSON"):
        integrity.verify(audit_tree)


def test_gzip_metadata_must_bind_same_base_commit(audit_tree):
    path = audit_tree / integrity.EVIDENCE_DIRECTORY / "records.json.gz"
    value = json.loads(gzip.decompress(path.read_bytes()))
    value["base_commit"] = "b" * 40
    path.write_bytes(gzip.compress(json.dumps(value).encode(), mtime=0))
    _refresh_manifest(audit_tree)
    with pytest.raises(integrity.IntegrityError, match="base_commit mismatch"):
        integrity.verify(audit_tree)


def test_repository_escape_is_refused(audit_tree):
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["sources"][0]["path"] = "../outside.txt"
    _write_json(path, manifest)
    with pytest.raises(integrity.IntegrityError, match="repository-relative"):
        integrity.verify(audit_tree)


def test_census_module_must_be_covered_by_manifest(audit_tree):
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["sources"] = [row for row in manifest["sources"] if row["path"] != "tests/test_000.py"]
    _write_json(path, manifest)
    with pytest.raises(
        integrity.IntegrityError, match="Adversary module omitted from source_manifest"
    ):
        integrity.verify(audit_tree)


def test_execution_receipt_cannot_be_hashed_by_its_own_manifest(audit_tree):
    receipt = audit_tree / integrity.EVIDENCE_DIRECTORY / "execution_receipt.json"
    _write_json(receipt, {"status": "PASS"})
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["artifacts"].append(_manifest_row(audit_tree, receipt))
    manifest["artifacts"].sort(key=lambda row: row["path"].encode("utf-8"))
    _write_json(path, manifest)
    with pytest.raises(integrity.IntegrityError, match="execution receipt must be excluded"):
        integrity.verify(audit_tree)


@pytest.mark.parametrize("tampered", [False, True])
def test_cli_verdict_records_actual_command_version_exit_code_and_scope(audit_tree, tampered):
    if tampered:
        (audit_tree / "source.txt").write_text("changed after the manifest\n")
    command = [
        sys.executable,
        str(Path(integrity.__file__).resolve()),
        "--repository-root",
        str(audit_tree),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    receipt = json.loads(completed.stdout)
    assert completed.returncode == int(tampered)
    assert receipt["status"] == ("FAIL" if tampered else "PASS")
    assert receipt["exit_code"] == completed.returncode
    assert receipt["argv"] == command
    assert receipt["command"] == shlex.join(command)
    assert receipt["tool_version"] == f"Python {platform.python_version()}; {receipt['schema']}"
    assert receipt["invocation_kind"] == "process"
    assert receipt["tested_scope"]["repository_root"] == str(audit_tree)
    assert receipt["tested_scope"]["manifest"] == str(audit_tree / integrity.DEFAULT_MANIFEST)
    assert "pilot execution" in receipt["tested_scope"]["excluded"]


def _declare_output(root: Path, *, included: bool = True) -> Path:
    output = root / integrity.EVIDENCE_DIRECTORY / "test_output.txt"
    output.write_text("recorded isolated test output\n", encoding="utf-8")
    row = _manifest_row(root, output)
    _write_json(
        root / integrity.EVIDENCE_DIRECTORY / "execution_receipt.json",
        {"check": {"output_artifact": row["path"], "output_sha256": row["sha256"]}},
    )
    if included:
        path = root / integrity.DEFAULT_MANIFEST
        manifest = json.loads(path.read_text())
        manifest["artifacts"].append(row)
        manifest["artifacts"].sort(key=lambda item: item["path"].encode("utf-8"))
        _write_json(path, manifest)
    return output


def test_execution_output_must_be_published_in_manifest(audit_tree):
    _declare_output(audit_tree, included=False)
    with pytest.raises(integrity.IntegrityError, match="execution output omitted"):
        integrity.verify(audit_tree)


def test_published_execution_output_is_checked(audit_tree):
    _declare_output(audit_tree)
    assert integrity.verify(audit_tree)["execution_output_artifacts_checked"] == 1


def test_execution_receipt_cannot_substitute_output_digest(audit_tree):
    _declare_output(audit_tree)
    path = audit_tree / integrity.EVIDENCE_DIRECTORY / "execution_receipt.json"
    receipt = json.loads(path.read_text())
    receipt["check"]["output_sha256"] = "f" * 64
    _write_json(path, receipt)
    with pytest.raises(integrity.IntegrityError, match="execution output digest mismatch"):
        integrity.verify(audit_tree)


def test_missing_published_execution_output_is_refused(audit_tree):
    _declare_output(audit_tree).unlink()
    with pytest.raises(integrity.IntegrityError, match="missing manifest file"):
        integrity.verify(audit_tree)


def _pin_fixture_sources(root: Path) -> str:
    hooks = root / "empty-hooks"
    hooks.mkdir()
    command = [
        "git",
        "-c",
        "core.autocrlf=false",
        "-c",
        f"core.hooksPath={hooks}",
        "-c",
        "commit.gpgsign=false",
        "-c",
        "user.name=Isolated audit test",
        "-c",
        "user.email=audit-test@example.invalid",
    ]
    subprocess.run([*command, "init", "-q"], cwd=root, check=True, capture_output=True)
    subprocess.run(
        [*command, "add", "--", "source.txt", "tests"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [*command, "commit", "-qm", "Pin isolated audit sources"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    path = root / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["base_commit"] = revision
    census_path = root / integrity.DEFAULT_CENSUS
    census = json.loads(census_path.read_text())
    census["base_commit"] = revision
    _write_json(census_path, census)
    compressed = root / integrity.EVIDENCE_DIRECTORY / "records.json.gz"
    payload = json.loads(gzip.decompress(compressed.read_bytes()))
    payload["base_commit"] = revision
    compressed.write_bytes(gzip.compress(json.dumps(payload).encode(), mtime=0))
    for row in manifest["artifacts"]:
        row["sha256"] = hashlib.sha256((root / row["path"]).read_bytes()).hexdigest()
    _write_json(path, manifest)
    return revision


@pytest.mark.parametrize("deleted", [False, True])
def test_pinned_audit_survives_later_source_changes_without_claiming_current_bytes(
    audit_tree, deleted
):
    revision = _pin_fixture_sources(audit_tree)
    source = audit_tree / "source.txt"
    if deleted:
        source.unlink()
    else:
        source.write_text("newer source outside the frozen audit\n")
    with pytest.raises(integrity.IntegrityError):
        integrity.verify(audit_tree)
    receipt = integrity.verify(audit_tree, pinned_sources=True)
    assert receipt["base_commit"] == revision
    assert receipt["source_binding"] == "pinned_git_revision"
    assert receipt["working_tree_sources_verified"] is False
    result = subprocess.run(
        [
            sys.executable,
            str(Path(integrity.__file__).resolve()),
            "--repository-root",
            str(audit_tree),
            "--pinned-sources",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["source_binding"] == "pinned_git_revision"


def test_pinned_audit_refuses_forged_hash_even_when_current_file_matches(audit_tree):
    _pin_fixture_sources(audit_tree)
    (audit_tree / "source.txt").write_text("forged replacement\n")
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    for row in manifest["sources"]:
        row["sha256"] = hashlib.sha256((audit_tree / row["path"]).read_bytes()).hexdigest()
    _write_json(path, manifest)
    with pytest.raises(integrity.IntegrityError, match="SHA-256 mismatch"):
        integrity.verify(audit_tree, pinned_sources=True)


def test_missing_pinned_revision_never_falls_back_to_current_files(audit_tree):
    _pin_fixture_sources(audit_tree)
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["base_commit"] = "0" * 40
    _write_json(path, manifest)
    with pytest.raises(integrity.IntegrityError, match="missing pinned Git source"):
        integrity.verify(audit_tree, pinned_sources=True)


def test_pinned_mode_without_git_repository_returns_typed_refusal(audit_tree):
    with pytest.raises(integrity.IntegrityError, match="pinned Git source"):
        integrity.verify(audit_tree, pinned_sources=True)


def test_manifest_control_character_cannot_inject_git_batch_request(audit_tree):
    path = audit_tree / integrity.DEFAULT_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["sources"][0]["path"] = "source.txt\nHEAD:other.txt"
    _write_json(path, manifest)
    with pytest.raises(integrity.IntegrityError, match="noncanonical manifest path"):
        integrity.verify(audit_tree)


@pytest.mark.parametrize("category", ["pilots", "adversary_modules"])
def test_static_audit_cannot_launder_execution_by_changing_both_flags(audit_tree, category):
    change = {"executed_now": True}
    change["evidence_status" if category == "pilots" else "provenance"] = "executed_now"
    _change_census(audit_tree, lambda census: census[category][0].update(change))
    with pytest.raises(integrity.IntegrityError, match="static audit cannot claim"):
        integrity.verify(audit_tree)


def test_census_cannot_bind_another_source_revision(audit_tree):
    _change_census(audit_tree, lambda census: census.update(base_commit="b" * 40))
    with pytest.raises(integrity.IntegrityError, match="census base_commit mismatch"):
        integrity.verify(audit_tree)


def test_census_cannot_change_the_frozen_audit_mode(audit_tree):
    _change_census(audit_tree, lambda census: census.update(audit_mode="live_execution"))
    with pytest.raises(integrity.IntegrityError, match="census audit_mode"):
        integrity.verify(audit_tree)
