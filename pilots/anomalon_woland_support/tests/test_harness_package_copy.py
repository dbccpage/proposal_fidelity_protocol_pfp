"""Offline safety checks for the relocated historical package builder."""

import os
import subprocess

import pytest

from pilots.anomalon_woland_support.documentation.harness_evolution import build_review_package as package


def test_package_refuses_linked_payload_directories(tmp_path):
    source, external = tmp_path / "source", tmp_path / "external"
    source.mkdir()
    external.mkdir()
    (external / "evidence.json").write_bytes(b'{"result":"same bytes"}')
    linked = source / "receipts"
    if os.name == "nt":
        quote = lambda p: "'" + str(p).replace("'", "''") + "'"
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"New-Item -ItemType Junction -Path {quote(linked)} -Target {quote(external)} | Out-Null",
            ],
            check=True,
            capture_output=True,
        )
    else:
        linked.symlink_to(external, target_is_directory=True)
    try:
        with pytest.raises(ValueError, match="NONREGULAR_PACKAGE_PATH"):
            package.copy_tree(source, tmp_path / "output")
    finally:
        if os.name == "nt":
            linked.rmdir()
        else:
            linked.unlink()

def test_package_traversal_errors_are_fatal(tmp_path, monkeypatch):
    def unreadable(*args, **kwargs):
        kwargs["onerror"](PermissionError("retained directory unreadable"))
        return iter(())

    monkeypatch.setattr(os, "walk", unreadable)
    with pytest.raises(PermissionError, match="unreadable"):
        package.copy_tree(tmp_path, tmp_path / "destination")
