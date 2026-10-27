"""Route existing EIS persistence at composition, preserving admitted catalog priority."""
from pathlib import Path

from eis.domain.pharmacy_catalog import PharmacyCatalogRepository
from eis.domain.pharmacy_seeder import PharmacySeeder
from eis.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from operating_system.adapters.intelligence_custody.ic_routing import intelligence_path


def routed_catalog_path(repo_root: Path) -> Path:
    agents = repo_root / "eis/antibodies/pharmacy_catalog.json"
    if agents.is_file():
        return agents
    intelligence = intelligence_path(repo_root, "_intelligence/antibodies/pharmacy_catalog.json")
    return intelligence if intelligence.is_file() else agents


def build_routed_pharmacy_seeder(repo_root: Path) -> PharmacySeeder:
    repository = PharmacyCatalogRepository(
        repo_root, catalog_file=routed_catalog_path(repo_root),
        telemetry_dir=intelligence_path(repo_root, "_intelligence/archive/telemetry/antibodies"),
        byte_writer=filesystem_byte_writer,
        byte_source=filesystem_catalog_bytes,
    )
    return PharmacySeeder(repository=repository)
