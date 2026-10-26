"""Integration coverage for the concrete StructureBench filesystem boundary."""

from pathlib import Path

from omega_engine_operads.structurebench import evaluate_bundle
from omega_engine_operads.tests.unit import (
    test_structurebench_no_vacuous_decisions as fixtures,
)


def test_path_bundle_reader_drives_the_public_evaluation_entrypoint(tmp_path: Path) -> None:
    bundle = fixtures._write_bundle(tmp_path / "bundle")

    report = evaluate_bundle(bundle)

    assert report.is_clean(), report.render()
