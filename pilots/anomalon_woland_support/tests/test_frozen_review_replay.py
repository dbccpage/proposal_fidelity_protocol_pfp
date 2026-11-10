"""Extraction and offline-execution controls for the historical review handoff."""

import json
import os
import stat
import subprocess
import sys
import zipfile
from types import SimpleNamespace

import pytest

from pilots.anomalon_woland_support.documentation.harness_evolution import replay_review_archive as replay


def archive_at(tmp_path, members):
    archive = tmp_path / "fixture.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for name, mode in members:
            item = zipfile.ZipInfo(name)
            # ZipInfo normalizes Windows separators during construction; retain
            # the hostile wire spelling so the extraction boundary sees it.
            item.filename = name
            item.external_attr = mode << 16
            output.writestr(item, b"retained bytes")
    return archive


@pytest.mark.parametrize("name", [
    "../escape", "/absolute", "foreign/file", "pfp_harness_author_review/../escape",
    "pfp_harness_author_review/a\\b", "pfp_harness_author_review/x:stream",
    "pfp_harness_author_review/CON.txt", "pfp_harness_author_review/trailing.",
])
def test_unsafe_members_are_refused_before_any_extraction(tmp_path, name):
    archive = archive_at(tmp_path, [(name, stat.S_IFREG | 0o644)])
    target = tmp_path / "output"
    with pytest.raises(ValueError, match="UNSAFE_ARCHIVE_MEMBER"):
        replay.extract(archive, target, replay.sha(archive))
    assert not target.exists()


@pytest.mark.parametrize("members,reason", [
    ([(replay.PACKAGE + "/link", stat.S_IFLNK | 0o777)], "NONREGULAR"),
    ([(replay.PACKAGE + "/A", stat.S_IFREG), (replay.PACKAGE + "/a", stat.S_IFREG)], "DUPLICATE"),
])
def test_link_and_case_collisions_fail_closed(tmp_path, members, reason):
    archive = archive_at(tmp_path, members)
    with pytest.raises(ValueError, match=reason):
        replay.extract(archive, tmp_path / "output", replay.sha(archive))
    assert not (tmp_path / "output").exists()


def test_digest_is_checked_and_existing_work_is_preserved(tmp_path):
    archive = archive_at(tmp_path, [(replay.PACKAGE + "/payload", stat.S_IFREG | 0o644)])
    target = tmp_path / "output"
    with pytest.raises(ValueError, match="DIGEST_MISMATCH"):
        replay.extract(archive, target, "0" * 64)
    assert not target.exists()
    package = replay.extract(archive, target, replay.sha(archive))
    (package / "payload").write_text("user changes")
    with pytest.raises(ValueError, match="DESTINATION_EXISTS"):
        replay.extract(archive, target, replay.sha(archive))
    assert (package / "payload").read_text() == "user changes"


@pytest.mark.parametrize("probe", [
    "import socket; socket.socket()",
    "import subprocess, sys; subprocess.run([sys.executable, '-c', 'pass'], check=True)",
])
def test_replay_child_refuses_network_and_process_execution(tmp_path, probe):
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools/rebuild_release.py").write_text(probe)
    result = subprocess.run(
        [sys.executable, "-I", "-S", "-B", "-c", replay.CHILD, str(tmp_path), "[]"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "OFFLINE_REPLAY_EXTERNAL_EXECUTION_REFUSED" in result.stderr


def test_extraction_uses_authenticated_bytes_after_path_replacement(tmp_path, monkeypatch):
    archive = archive_at(tmp_path, [(replay.PACKAGE + "/payload", stat.S_IFREG | 0o644)])
    expected = replay.sha(archive)
    original_zip = zipfile.ZipFile

    def swap_path(source, *args, **kwargs):
        with original_zip(archive, "w") as replacement:
            replacement.writestr(replay.PACKAGE + "/payload", b"substituted code")
        return original_zip(source, *args, **kwargs)

    monkeypatch.setattr(replay.zipfile, "ZipFile", swap_path)
    package = replay.extract(archive, tmp_path / "output", expected)
    assert (package / "payload").read_bytes() == b"retained bytes"


def test_same_byte_archive_under_linked_parent_is_refused(tmp_path):
    real = tmp_path / "real"
    real.mkdir()
    archive = archive_at(real, [(replay.PACKAGE + "/payload", stat.S_IFREG | 0o644)])
    alias = tmp_path / "alias"
    if os.name == "nt":
        def quote(path):
            return "'" + str(path).replace("'", "''") + "'"
        subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command",
             f"New-Item -ItemType Junction -Path {quote(alias)} -Target {quote(real)} | Out-Null"],
            check=True, capture_output=True,
        )
    else:
        alias.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="NONREGULAR_ARCHIVE_PATH"):
        replay.extract(alias / archive.name, tmp_path / "output", replay.sha(archive))
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("mode,reason", [
    ("timeout", "REPLAY_TIMEOUT"), ("start", "REPLAY_START_FAILED"),
    ("missing", "REPLAY_REPORT_INVALID"), ("malformed", "REPLAY_REPORT_INVALID"),
    ("bool", "REPLAY_REPORT_INVALID"), ("paid", "REPLAY_REPORT_INVALID"),
    ("valid", None),
])
def test_interrupted_or_invalid_replay_has_failure_receipt(tmp_path, monkeypatch, mode, reason):
    output = tmp_path / "output"
    package = output / replay.PACKAGE
    archive = tmp_path / "fixture.zip"
    archive.write_bytes(b"fixture")
    monkeypatch.setattr(replay, "ARCHIVE", archive)
    monkeypatch.setattr(sys, "argv", ["replay", "--output", str(output)])
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-secret-must-not-reach-child")

    def fixture_extract(*args):
        package.mkdir(parents=True)
        return package

    def execute(*args, **kwargs):
        assert "ANTHROPIC_API_KEY" not in kwargs["env"]
        assert kwargs["env"]["OMEGA_CREDENTIAL_DISCOVERY"] == "off"
        if mode == "timeout":
            raise subprocess.TimeoutExpired("fixture", 300, output=b"partial output", stderr=b"partial error")
        if mode == "start":
            raise OSError("fixture failure")
        if mode != "missing":
            report = package / "repository/omega_engine_woland/documentation/harness_evolution/campaign/report.json"
            report.parent.mkdir(parents=True)
            body = {"status": "NOT_RUN", "independent_provider_calls": 0,
                    "assigned_trials": 0, "spent_microusd": 0, "held_microusd": 0}
            if mode == "bool":
                body["assigned_trials"] = False
            if mode == "paid":
                body["spent_microusd"] = 1
            report.write_text("invalid" if mode == "malformed" else json.dumps(body))
        return SimpleNamespace(returncode=0, stdout="completed", stderr="")

    monkeypatch.setattr(replay, "extract", fixture_extract)
    monkeypatch.setattr(replay.subprocess, "run", execute)
    assert replay.main() == (0 if reason is None else 1)
    receipt = json.loads((output / "replay_receipt.json").read_text())
    assert receipt["failure"] == reason
    assert receipt["status"] == ("PASS" if reason is None else "FAIL")
    if mode == "timeout":
        assert (output / "replay.stdout.txt").read_text() == "partial output"
        assert (output / "replay.stderr.txt").read_text() == "partial error"
