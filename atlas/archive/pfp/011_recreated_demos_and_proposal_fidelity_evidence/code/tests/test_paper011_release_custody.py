"""Boundary mutations for the locally adapted canonical template machinery."""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

PAPER = Path(__file__).resolve().parents[2]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


paths = load("paper011_paths_test", PAPER / "code/deposit_paths.py")
release = load("paper011_release_test", PAPER / "tools/rebuild_release.py")


def test_archive_payload_is_exhaustive_even_for_excluded_names(tmp_path):
    for relative in (
        "docs/source_archive/pfp_demos/evidence/receipt.log",
        "docs/source_archive/pfp_demos/.hidden/.env",
        "docs/source_archive/pfp_demos/build/MANIFEST.sha256",
        "docs/source_archive/pfp_demos/archive.zip",
        "docs/evidence/current.json",
        "build/cache.bin",
    ):
        file = tmp_path / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"retained")
    actual = {
        file.relative_to(tmp_path).as_posix()
        for file in paths.walk_files(
            tmp_path, {"evidence", "build"}, {".env", "MANIFEST.sha256"}, {".log", ".zip"}
        )
    }
    assert actual == {
        "docs/source_archive/pfp_demos/evidence/receipt.log",
        "docs/source_archive/pfp_demos/.hidden/.env",
        "docs/source_archive/pfp_demos/build/MANIFEST.sha256",
        "docs/source_archive/pfp_demos/archive.zip",
        "docs/evidence/current.json",
    }


def test_traversal_errors_are_fatal(tmp_path, monkeypatch):
    def denied_walk(root, *, followlinks, onerror):
        onerror(PermissionError("unreadable retained directory"))
        return iter(())

    monkeypatch.setattr(paths.os, "walk", denied_walk)
    with pytest.raises(PermissionError, match="unreadable"):
        paths.walk_files(tmp_path, set(), set(), set())


@pytest.mark.parametrize(
    "entries",
    [
        ["Dir/a", "dir/b"],
        ["Asset", "asset/child"],
        ["a", "a"],
        ["a/../b"],
        ["a\\b"],
        ["C:/escape"],
        ["/absolute"],
    ],
)
def test_manifest_path_mutations_refuse(tmp_path, entries):
    manifest = tmp_path / "SHA256SUMS"
    manifest.write_text("".join("0" * 64 + "  " + item + "\n" for item in entries))
    with pytest.raises(ValueError):
        paths.read_manifest(tmp_path, manifest)


def test_reparse_metadata_refuses(tmp_path, monkeypatch):
    target = tmp_path / "data"
    target.write_bytes(b"same bytes")
    original = Path.lstat

    def fake_lstat(path):
        if path == target:
            return SimpleNamespace(st_mode=0o100644, st_file_attributes=0x400)
        return original(path)

    monkeypatch.setattr(Path, "lstat", fake_lstat)
    with pytest.raises(ValueError, match="symlink or junction"):
        paths.walk_files(tmp_path, set(), set(), set())


@pytest.fixture
def package(tmp_path):
    paper = tmp_path / "fixture"
    (paper / "code").mkdir(parents=True)
    shutil.copyfile(PAPER / "code/deposit_paths.py", paper / "code/deposit_paths.py")
    (paper / "payload.txt").write_bytes(b"payload\r\n")
    (paper / "zenodo_metadata.json").write_text(json.dumps({"publication_date": "2026-10-02"}))
    release.refresh(paper)
    assert release.validate(paper) == []
    return paper


@pytest.mark.parametrize("mutation", ["payload", "extra", "prepend", "append", "directory_control"])
def test_release_boundary_mutations_refuse(package, mutation):
    archive = release.archive_path(package)
    if mutation == "payload":
        (package / "payload.txt").write_bytes(b"changed")
    elif mutation == "extra":
        (package / "extra.txt").write_bytes(b"unlisted")
    elif mutation == "prepend":
        archive.write_bytes(b"prefix" + archive.read_bytes())
    elif mutation == "append":
        archive.write_bytes(archive.read_bytes() + b"suffix")
    else:
        control = package / "SHA256SUMS"
        original = control.read_bytes()
        control.unlink()
        control.mkdir()
        (control / "same-bytes").write_bytes(original)
    assert release.validate(package)


def test_build_is_byte_identical_and_archive_retains_all_source_files(package):
    source = package / "docs/source_archive/pfp_demos/evidence/raw.json"
    source.parent.mkdir(parents=True)
    source.write_bytes(b'{"raw":"CRLF"}\r\n')
    release.refresh(package)
    first = release.archive_path(package).read_bytes()
    release.refresh(package)
    assert release.archive_path(package).read_bytes() == first
    assert release.validate(package) == []
    assert source.relative_to(package).as_posix() in (package / "MANIFEST.sha256").read_text()


def test_same_byte_symlink_control_refuses(package):
    control = package / "SHA256SUMS"
    retained = package / "retained"
    retained.write_bytes(control.read_bytes())
    control.unlink()
    try:
        os.symlink(retained, control)
    except OSError:
        pytest.skip(
            "OS does not grant unprivileged symlink creation; reparse metadata separately tested"
        )
    assert release.validate(package)
