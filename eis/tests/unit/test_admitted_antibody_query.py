"""Admitted-only reads, and re-observation never demotes a human judgement.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from pathlib import Path

from omega_engine_epistemic_immune_system.domain.pharmacy_catalog import PharmacyCatalogRepository
from omega_engine_epistemic_immune_system.domain.pharmacy_seeder import PharmacySeeder
from omega_engine_epistemic_immune_system.infrastructure.pharmacy_writer import (
    filesystem_byte_writer,
    filesystem_catalog_bytes,
)
from omega_engine_epistemic_immune_system.use_cases.admitted_antibody_query import (
    admitted_antibodies,
)

DEFECT = "candidate selected without a bound checker receipt"


def _admit(repository: PharmacyCatalogRepository, antibody_id: str, status: str) -> None:
    """Stand-in for the human admission step: rewrite the recorded status."""
    catalog = repository.load_catalog()
    catalog["antibodies"][antibody_id]["pharmacy_status"] = status
    repository.catalog_file.write_text(json.dumps(catalog), encoding="utf-8")


def test_farmed_candidates_are_never_returned_as_admitted(tmp_path: Path) -> None:
    seeder = PharmacySeeder(repo_root=tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    farmed = seeder.farm_antibodies_from_defects([DEFECT], run_id="r1", task_id="t1")
    assert [antibody.pharmacy_status for antibody in farmed] == ["candidate"]
    result = admitted_antibodies(seeder.repository.load_catalog())
    assert result.admitted == ()
    assert result.malformed_ids == ()


def test_admitted_entries_are_returned_and_others_are_not(tmp_path: Path) -> None:
    seeder = PharmacySeeder(repo_root=tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    farmed = seeder.farm_antibodies_from_defects(
        [DEFECT, "float residual compared with a tolerance", "unbounded retry loop"],
        run_id="r1",
        task_id="t1",
    )
    ids = sorted(antibody.antibody_id for antibody in farmed)
    _admit(seeder.repository, ids[0], "admitted")
    _admit(seeder.repository, ids[1], "rejected")
    result = admitted_antibodies(seeder.repository.load_catalog())
    assert [antibody.antibody_id for antibody in result.admitted] == [ids[0]]
    assert result.admitted[0].pharmacy_status == "admitted"


def test_reobserving_an_admitted_antibody_does_not_demote_it(tmp_path: Path) -> None:
    seeder = PharmacySeeder(repo_root=tmp_path, byte_writer=filesystem_byte_writer, byte_source=filesystem_catalog_bytes)
    [antibody] = seeder.farm_antibodies_from_defects([DEFECT], run_id="r1", task_id="t1")
    _admit(seeder.repository, antibody.antibody_id, "admitted")
    again = seeder.farm_antibodies_from_defects([DEFECT], run_id="r2", task_id="t2")
    assert again == []
    assert seeder.preserved_judged == [antibody.antibody_id]
    catalog = seeder.repository.load_catalog()
    assert catalog["antibodies"][antibody.antibody_id]["pharmacy_status"] == "admitted"
    assert [a.antibody_id for a in admitted_antibodies(catalog).admitted] == [antibody.antibody_id]


def test_malformed_admitted_entries_are_reported_not_returned() -> None:
    catalog = {
        "antibodies": {
            "ab_x": {"antibody_id": "ab_y", "pharmacy_status": "admitted"},
            "ab_z": "not a mapping",
        }
    }
    result = admitted_antibodies(catalog)
    assert result.admitted == ()
    assert result.malformed_ids == ("ab_x",)
