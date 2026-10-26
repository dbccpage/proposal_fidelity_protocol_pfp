"""Bundle-reader port and filesystem-adapter tests for StructureBench."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import TracebackType
from typing import BinaryIO

import pytest

from omega_engine_operads.structurebench import StructureBenchEvaluator
from omega_engine_operads.structurebench.path_bundle_reader import (
    PathBundleReader,
)
from omega_engine_operads.structurebench.ports import BundleReader
from omega_engine_operads.tests.unit import (
    test_structurebench_no_vacuous_decisions as fixtures,
)


@dataclass
class MemoryBundleReader:
    artifacts: dict[str, bytes]
    reads: list[str] = field(default_factory=list)

    def is_bundle(self) -> bool:
        return True

    def read(self, name: str) -> bytes | None:
        self.reads.append(name)
        return self.artifacts.get(name)


def test_evaluator_accepts_an_in_memory_bundle_reader(tmp_path: Path) -> None:
    disk_bundle = fixtures._write_bundle(tmp_path / "fixture")
    artifacts = {path.name: path.read_bytes() for path in disk_bundle.iterdir()}
    reader: BundleReader = MemoryBundleReader(artifacts)

    report = StructureBenchEvaluator(bundle_reader=reader).evaluate()

    assert report.is_clean(), report.render()
    assert "receipt.json" in reader.reads
    assert "dda_actions.jsonl" in reader.reads
    assert len(reader.reads) == len(set(reader.reads)), "artifacts must be evaluated from one snapshot"


@pytest.mark.parametrize(
    "hostile_name",
    ("../secret.txt", "subdir/artifact.json", r"subdir\artifact.json", r"C:\secret.txt"),
)
def test_path_reader_refuses_paths_outside_its_bundle(tmp_path: Path, hostile_name: str) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    assert PathBundleReader(bundle).read(hostile_name) is None


def test_path_reader_refuses_symlink_artifacts(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_bytes(b"outside")
    link = bundle / "receipt.json"
    try:
        link.symlink_to(secret)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    assert PathBundleReader(bundle).read("receipt.json") is None


def test_path_reader_refuses_file_swapped_between_check_and_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class TrackingStream:
        def __init__(self, stream: BinaryIO) -> None:
            self.stream = stream
            self.read_calls = 0

        def fileno(self) -> int:
            return self.stream.fileno()

        def read(self) -> bytes:
            self.read_calls += 1
            return self.stream.read()

        def __enter__(self) -> TrackingStream:
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
        ) -> None:
            self.stream.close()

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    artifact = bundle / "receipt.json"
    artifact.write_bytes(b"expected")
    secret = tmp_path / "secret.txt"
    secret.write_bytes(b"outside")
    original_open = Path.open
    secret_stream: TrackingStream | None = None

    def swapped_open(path: Path, *args: object, **kwargs: object) -> TrackingStream:
        nonlocal secret_stream
        assert path == artifact
        secret_stream = TrackingStream(original_open(secret, *args, **kwargs))
        return secret_stream

    monkeypatch.setattr(Path, "open", swapped_open)

    assert PathBundleReader(bundle).read("receipt.json") is None
    assert secret_stream is not None
    assert secret_stream.read_calls == 0
