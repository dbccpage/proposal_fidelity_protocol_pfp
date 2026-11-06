"""Required installed dependency bytes must survive verification unchanged."""

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_path = Path(__file__).resolve().parents[1] / "runtime_environment.py"
_spec = importlib.util.spec_from_file_location("paper011_runtime_environment", _path)
runtime = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = runtime
_spec.loader.exec_module(runtime)


@pytest.fixture
def installed(tmp_path, monkeypatch):
    source = tmp_path / "solver.py"
    source.write_bytes(b"original")
    binary = tmp_path / "python.exe"
    binary.write_bytes(b"interpreter")
    distribution = SimpleNamespace(
        files=["solver.py"],
        metadata={"Name": "fixture"},
        version="1.0",
        locate_file=lambda entry: tmp_path / entry,
    )
    monkeypatch.setattr(runtime.importlib.metadata, "distribution", lambda name: distribution)
    monkeypatch.setattr(runtime.sys, "executable", str(binary))
    return source, binary, distribution


def test_declared_dependency_source_and_interpreter_drift(installed):
    source, binary, _ = installed
    profile = runtime.snapshot(["fixture"])
    assert runtime.verify(profile)["files"] == 1
    source.write_bytes(b"changed")
    with pytest.raises(ValueError, match="DEPENDENCY_DRIFT"):
        runtime.verify(profile)
    source.write_bytes(b"original")
    binary.write_bytes(b"different-interpreter")
    with pytest.raises(ValueError, match="DEPENDENCY_DRIFT"):
        runtime.verify(profile)


def test_distribution_version_and_missing_file_refuse(installed):
    source, _, distribution = installed
    profile = runtime.snapshot(["fixture"])
    distribution.version = "2.0"
    with pytest.raises(ValueError, match="DEPENDENCY_DRIFT"):
        runtime.verify(profile)
    distribution.version = "1.0"
    source.unlink()
    with pytest.raises(FileNotFoundError):
        runtime.verify(profile)


def test_added_distribution_file_refuses(installed):
    source, _, distribution = installed
    profile = runtime.snapshot(["fixture"])
    extra = source.parent / "unlisted.py"
    extra.write_bytes(b"new-input")
    distribution.files.append(extra.name)
    with pytest.raises(ValueError, match="DEPENDENCY_DRIFT"):
        runtime.verify(profile)


@pytest.mark.parametrize("names", [[], ["fixture", "fixture"]])
def test_no_empty_or_duplicate_dependency_profile(names):
    with pytest.raises(ValueError, match="DISTRIBUTION_LIST"):
        runtime.snapshot(names)
