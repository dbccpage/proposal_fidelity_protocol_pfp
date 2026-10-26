"""Corruption controls over a small synthetic archive, never imported demos."""

from __future__ import annotations

import importlib.util
import json
import stat
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[1] / "source_custody.py"
_SPEC = importlib.util.spec_from_file_location("paper011_source_custody_for_tests", _MODULE_PATH)
custody = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = custody
_SPEC.loader.exec_module(custody)


@pytest.fixture
def snapshot(tmp_path: Path) -> tuple[Path, dict, str]:
    data = b"historical receipt\r\nunchanged\xff\x00"
    source = "education/demos/nested/receipt.dat"
    copy = "docs/source_archive/pfp_demos/nested/receipt.dat"
    path = tmp_path / copy
    path.parent.mkdir(parents=True)
    path.write_bytes(data)
    digest = custody.sha256(data)
    manifest = {
        "schema_version": custody.SCHEMA,
        "paper_id": "PAPER_011",
        "authority_effect": "None",
        "source_git_head": "1" * 40,
        "captured_at_utc": "2026-10-02T12:00:00+00:00",
        "inventory_policy": "ALL_GIT_TRACKED_FILES_UNDER_DECLARED_ROOTS",
        "excluded_scope": "UNTRACKED_LOCAL_STATE_ONLY",
        "source_roots": [
            {
                "source_root": "education/demos",
                "copy_root": "docs/source_archive/pfp_demos",
                "file_count": 1,
                "total_bytes": len(data),
            }
        ],
        "file_count": 1,
        "total_bytes": len(data),
        "entries": [
            {
                "source_path": source,
                "copy_path": copy,
                "captured_source_sha256": digest,
                "current_copy_sha256": digest,
                "size_bytes": len(data),
                "git_blob_oid": "2" * 40,
                "git_mode": "100644",
            }
        ],
    }
    pin = write_manifest(tmp_path, manifest)
    return tmp_path, manifest, pin


def write_manifest(paper: Path, value: dict) -> str:
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    (paper / custody.MANIFEST_PATH).write_bytes(raw)
    return custody.sha256(raw)


def test_paper011_source_custody_preserves_arbitrary_raw_bytes(snapshot) -> None:
    paper, _, pin = snapshot
    result = custody.verify_source_copies(paper, expected_manifest_sha256=pin)
    assert result["status"] == "VERIFIED_BYTE_COPIES"
    assert result["file_count"] == 1
    assert result["execution_claim"] == "NONE_ARCHIVAL_CUSTODY_ONLY"
    assert result["authority_effect"] == "None"
    assert result["source_inventory_checked"] is False


@pytest.mark.parametrize("mutation", ["corrupt", "missing", "extra", "extra_subtree", "directory"])
def test_paper011_copy_mutation_refuses(snapshot, mutation: str) -> None:
    paper, manifest, pin = snapshot
    path = paper / manifest["entries"][0]["copy_path"]
    if mutation == "corrupt":
        path.write_bytes(path.read_bytes() + b"!")
    elif mutation == "missing":
        path.unlink()
    elif mutation == "extra":
        path.with_name("unlisted.dat").write_bytes(b"extra")
    elif mutation == "extra_subtree":
        extra = paper / "docs/source_archive/unlicensed/extra.dat"
        extra.parent.mkdir()
        extra.write_bytes(b"extra")
    else:
        raw = path.read_bytes()
        path.unlink()
        path.mkdir()
        (path / "same-bytes.dat").write_bytes(raw)
    with pytest.raises(custody.CustodyError):
        custody.verify_source_copies(paper, expected_manifest_sha256=pin)


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_path", "../escape"),
        ("copy_path", "docs/source_archive/other.dat"),
        ("captured_source_sha256", "0" * 64),
        ("size_bytes", True),
        ("git_mode", "120000"),
    ],
)
def test_paper011_untrusted_manifest_refuses(snapshot, field: str, value: object) -> None:
    paper, manifest, _ = snapshot
    manifest["entries"][0][field] = value
    write_manifest(paper, manifest)
    with pytest.raises(custody.CustodyError):
        custody.verify_source_copies(paper)


def test_paper011_manifest_external_pin_prevents_replacement(snapshot) -> None:
    paper, manifest, pin = snapshot
    manifest["source_git_head"] = "3" * 40
    write_manifest(paper, manifest)
    with pytest.raises(custody.CustodyError, match="manifest pin mismatch"):
        custody.verify_source_copies(paper, expected_manifest_sha256=pin)


def test_paper011_duplicate_json_keys_refuse(snapshot) -> None:
    paper, _, _ = snapshot
    (paper / custody.MANIFEST_PATH).write_bytes(b'{"schema_version":"one","schema_version":"two"}')
    with pytest.raises(custody.CustodyError, match="duplicate manifest key"):
        custody.verify_source_copies(paper)


def test_paper011_manifest_bijection_refuses_duplicate(snapshot) -> None:
    paper, manifest, _ = snapshot
    manifest["entries"].append(dict(manifest["entries"][0]))
    write_manifest(paper, manifest)
    with pytest.raises(custody.CustodyError, match="bijective"):
        custody.verify_source_copies(paper)


def test_paper011_read_failure_is_fatal(snapshot, monkeypatch) -> None:
    paper, _, _ = snapshot
    original = Path.iterdir

    def refuse_archive(path: Path):
        if path == paper / "docs/source_archive":
            raise PermissionError("injected unreadable archive")
        return original(path)

    monkeypatch.setattr(Path, "iterdir", refuse_archive)
    with pytest.raises(custody.CustodyError, match="traversal failed"):
        custody.verify_source_copies(paper)


def test_paper011_reparse_metadata_refuses_even_same_bytes(snapshot, monkeypatch) -> None:
    paper, manifest, _ = snapshot
    target = paper / manifest["entries"][0]["copy_path"]
    original = Path.lstat

    def redirected_metadata(path: Path):
        info = original(path)
        if path == target:
            return SimpleNamespace(st_mode=stat.S_IFREG, st_file_attributes=0x400)
        return info

    monkeypatch.setattr(Path, "lstat", redirected_metadata)
    with pytest.raises(custody.CustodyError, match="redirected entry"):
        custody.verify_source_copies(paper)


def test_paper011_pinned_git_inventory_must_be_complete(snapshot, monkeypatch) -> None:
    paper, _, _ = snapshot
    monkeypatch.setattr(custody, "tracked_sources", lambda *args: {})
    with pytest.raises(custody.CustodyError, match="pinned source Git inventory"):
        custody.verify_source_copies(paper, source_repo=paper)


def test_paper011_redirected_root_ancestor_refuses(snapshot, monkeypatch) -> None:
    paper, _, _ = snapshot
    original = Path.lstat

    def redirected_ancestor(path: Path):
        if path == paper.parent:
            return SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=0x400)
        return original(path)

    monkeypatch.setattr(Path, "lstat", redirected_ancestor)
    with pytest.raises(custody.CustodyError, match="redirected entry"):
        custody.verify_source_copies(paper)


def test_paper011_mutation_by_source_subprocess_is_caught(snapshot, monkeypatch) -> None:
    paper, manifest, _ = snapshot
    entry = manifest["entries"][0]

    def modified_git(*args):
        (paper / entry["copy_path"]).write_bytes(b"changed by source subprocess")
        return {entry["source_path"]: (entry["git_mode"], entry["git_blob_oid"])}

    monkeypatch.setattr(custody, "tracked_sources", modified_git)
    with pytest.raises(custody.CustodyError, match="copy bytes changed"):
        custody.verify_source_copies(paper, source_repo=paper)


def test_paper011_changed_original_source_refuses(snapshot, monkeypatch) -> None:
    paper, manifest, _ = snapshot
    source_repo = paper / "source-repo"
    entry = manifest["entries"][0]
    source = source_repo / entry["source_path"]
    source.parent.mkdir(parents=True)
    source.write_bytes(b"source changed after capture")
    monkeypatch.setattr(
        custody,
        "tracked_sources",
        lambda *args: {entry["source_path"]: (entry["git_mode"], entry["git_blob_oid"])},
    )
    with pytest.raises(custody.CustodyError, match="source bytes changed"):
        custody.verify_source_copies(paper, source_repo=source_repo)
