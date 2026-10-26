"""Live immune readers select OEEIS sources, never generated host bytes."""

from pathlib import Path

from omega_engine_epistemic_immune_system.domain.pharmacy_catalog import PharmacyCatalogRepository
from omega_engine_epistemic_immune_system.infrastructure import definitions_store
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import filesystem_catalog_bytes
from omega_engine_operations.infrastructure.intelligence_digestion.routed_pharmacy import routed_catalog_path


SOURCE = "omega_engine_epistemic_immune_system/antibodies"


def test_definitions_do_not_read_the_host_view(tmp_path, monkeypatch):
    (tmp_path / ".agents").mkdir()
    fake_module = tmp_path / "omega_engine_epistemic_immune_system/infrastructure/definitions_store.py"
    monkeypatch.setattr(definitions_store, "__file__", str(fake_module))
    monkeypatch.delenv("OEEIS_DEFINITIONS_DIR", raising=False)
    source = tmp_path / SOURCE / "definitions"
    source.mkdir(parents=True)
    (source / "demo.json").write_text("canonical", encoding="utf-8")
    host = tmp_path / ".agents/antibodies/definitions"
    host.mkdir(parents=True)
    (host / "demo.json").write_text("host edit", encoding="utf-8")
    assert definitions_store.definitions_dir() == source
    assert definitions_store.read_definition("demo.json") == "canonical"
    (source / "demo.json").unlink()
    assert definitions_store.read_definition("demo.json") is None


def test_default_pharmacy_location_ignores_an_existing_host_catalog(tmp_path):
    host = tmp_path / ".agents/antibodies/pharmacy_catalog.json"
    host.parent.mkdir(parents=True)
    host.write_text("{}", encoding="utf-8")
    expected = tmp_path / SOURCE / "pharmacy_catalog.json"
    assert PharmacyCatalogRepository.catalog_path(tmp_path) == expected
    assert PharmacyCatalogRepository.catalog_path(tmp_path, filesystem_catalog_bytes) == expected
    assert routed_catalog_path(tmp_path) == expected


def test_authored_pharmacy_precedes_runtime_candidate_catalog(tmp_path):
    canonical = tmp_path / SOURCE / "pharmacy_catalog.json"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("{}", encoding="utf-8")
    runtime = tmp_path / "_ic/cdc/antibodies/pharmacy_catalog.json"
    runtime.parent.mkdir(parents=True)
    runtime.write_text("{}", encoding="utf-8")
    assert PharmacyCatalogRepository.catalog_path(tmp_path, filesystem_catalog_bytes) == canonical
    assert routed_catalog_path(tmp_path) == canonical


def test_live_repository_definition_root_is_its_owning_package(monkeypatch):
    monkeypatch.delenv("OEEIS_DEFINITIONS_DIR", raising=False)
    root = Path(__file__).resolve().parents[3]
    assert definitions_store.definitions_dir() == root / SOURCE / "definitions"
