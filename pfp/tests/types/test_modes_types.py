"""Tests for modes/mode_catalog.py: typing, negative controls, YAML parity.

AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

from pfp.infrastructure.contract_loading import load_mode_catalog
from pydantic import ValidationError

from pfp.domain.stages import mode_catalog as mc

HERE = Path(__file__).resolve()
MODES = HERE.parents[2] / "infrastructure" / "yaml" / "modes"


def _raw() -> dict:
    return yaml.safe_load((MODES / "mode_catalog.yaml").read_text(encoding="utf-8"))


def test_yaml_validates_and_matches_contract_files() -> None:
    catalog = load_mode_catalog(MODES, MODES / "mode_catalog.yaml")
    assert len(catalog.entries) == 20


def test_yaml_cluster_membership_matches_model_constant() -> None:
    catalog = mc.ModeCatalog.model_validate(_raw(), strict=False)
    for cluster, members in mc.CLUSTER_MEMBERS.items():
        got = tuple(sorted(e.mode_id for e in catalog.entries if e.cluster == cluster))
        assert got == members


def test_yaml_agrees_with_modes_manifest() -> None:
    manifest = yaml.safe_load((MODES / "modes_manifest.yaml").read_text(encoding="utf-8"))
    refs = [mc.ManifestModeRef.model_validate(m, strict=False) for m in manifest["modes"]]
    catalog = mc.ModeCatalog.model_validate(_raw(), strict=False)
    by_id = {e.mode_id: e for e in catalog.entries}
    for ref in refs:
        assert by_id[ref.id].contract_path == ref.file
        assert by_id[ref.id].cluster == ref.cluster


def test_readme_links_new_files() -> None:
    text = (MODES / "README.md").read_text(encoding="utf-8")
    assert "(mode_catalog.py)" in text and "(mode_catalog.yaml)" in text


def test_negative_missing_mode_rejected() -> None:
    raw = _raw()
    raw["entries"] = raw["entries"][:-1]
    with pytest.raises(ValidationError):
        mc.ModeCatalog.model_validate(raw, strict=False)


def test_negative_duplicate_mode_rejected() -> None:
    raw = _raw()
    raw["entries"][19] = dict(raw["entries"][18])
    with pytest.raises(ValidationError):
        mc.ModeCatalog.model_validate(raw, strict=False)


def test_negative_wrong_cluster_rejected() -> None:
    entry = dict(_raw()["entries"][0])
    entry["cluster"] = "Cluster II: Internal Steering"
    with pytest.raises(ValidationError):
        mc.ModeCatalogEntry.model_validate(entry, strict=False)


def test_negative_path_prefix_mismatch_rejected() -> None:
    entry = dict(_raw()["entries"][0])
    entry["contract_path"] = "mode_02_packets_and_sealed_envelopes/contract.yaml"
    with pytest.raises(ValidationError):
        mc.ModeCatalogEntry.model_validate(entry, strict=False)


def test_negative_bool_mode_id_rejected() -> None:
    entry = dict(_raw()["entries"][0])
    entry["mode_id"] = True
    with pytest.raises(ValidationError):
        mc.ModeCatalogEntry.model_validate(entry, strict=False)


def test_negative_authority_effect_and_extra_field_rejected() -> None:
    entry = dict(_raw()["entries"][0])
    with pytest.raises(ValidationError):
        mc.ModeCatalogEntry.model_validate({**entry, "authority_effect": "Grant"}, strict=False)
    with pytest.raises(ValidationError):
        mc.ModeCatalogEntry.model_validate({**entry, "surplus": 1}, strict=False)


def test_negative_contract_disagreement_detected(tmp_path: Path) -> None:
    raw = _raw()
    raw["entries"][0]["cluster"] = "Cluster V: Foundational Mechanization"
    # mode 1 is not in cluster V, so the model itself refuses before file comparison
    with pytest.raises(ValidationError):
        mc.ModeCatalog.model_validate(raw, strict=False)


def test_frozen() -> None:
    catalog = mc.ModeCatalog.model_validate(_raw(), strict=False)
    with pytest.raises(ValidationError):
        catalog.entries[0].name = "x"
